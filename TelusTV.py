from concurrent.futures import ThreadPoolExecutor, as_completed
from requests import head, get
from flask import Flask, make_response, request
from waitress import serve
from random import choice
from redis import Redis
from json import loads, dumps
from base64 import b64encode, b64decode
from os import environ

#import logging
#logger = logging.getLogger("waitress")
#logger.setLevel(logging.INFO)

class TelusTV:
	def __init__(self, max_streamer = 5):
		# If some other value than False, client User-Agent header must exist and be string | CAN CUSTOMIZE (Default=False / Your custom value)
		self.allowedUserAgent = False

		# If some other value than False, client CDN-LOOP header must exist and be string | CAN CUSTOMIZE (Default=False / Your custom value)
		self.cdnLoop = False

		# You can customize the Server header | CAN CUSTOMIZE (Default=TelusTV+ / Your custom value)
		self.serverHeader = "TelusTV+"

		# Send these headers with requests | CAN CUSTOMIZE (I'd reccommend doing `tv.requestHeaders["Header-Key"] = "Header-Value"` for appending headers)
		self.requestHeaders = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
		}

		# Use proxy with requests | SET BY CALLING set_proxy("protocol://your.proxy:port")
		self.__proxies = {
			"http": False,
			"https": False
		}

		# Proxy segments through here or just let the client get the segments through the source directly | CAN CUSTOMIZE (Default=True / False)
		self.proxySegments = True

		# Cache segment urls here if self.proxySegments = True
		self.__segmentURLs = {}

		# Setup flask
		self.__app = self.__setup_flask()

		# Setup Redis client for caching
		self.__redisClient = Redis(host=environ["REDIS_HOST"], port=6379, db=0)

		# Set encoding | CAN CUSTOMIZE (Default=UTF-8 / Any other encoding format)
		self.encoding = "UTF-8"

		# Cache manifest for x seconds | CAN CUSTOMIZE (Default=5 seconds / Your int value)
		self.manifestCacheSeconds = 5

		# Cache segments for x seconds | CAN CUSTOMIZE (Default=60 seconds / Your int value)
		self.segmentCacheSeconds = 60

		# Set base url and links
		self.__baseURL, self.__links = self.__get_links(max_streamer)

	# Set proxy
	def set_proxy(self, proxy):
		self.__proxies["http"] = proxy
		self.__proxies["https"] = proxy

	# Setup flask server and add manifest & segment endpoints (__get_channel_manifest & __get_channel_segment)
	def __setup_flask(self):
		app = Flask(__name__)

		allowed_methods = ["GET"]

		# /access_url_id.mpd (manifest endpoint)
		app.add_url_rule("/<int:access_url_id>.mpd", view_func=self.__get_channel_manifest, methods=allowed_methods)

		# /SEGMENT/access_url_id/SegmentPath... (segment endpoint)
		app.add_url_rule("/SEGMENT/<int:access_url_id>/<path:segment>", view_func=self.__get_channel_segment, methods=allowed_methods)

		return app

	'''
	On script start, randomly set and return:
		1) base url can be:
			- `stb` (TV Boxes)
			- `reach` (TelusTV+ APP)
			- `web` (https://telustvplus.com)

		2) links can be:
			- `lott[None, 2-5]` (Live)
			- `ndvr[None, 2-5]` (DVR)

	Sources:
		1) Channel URLs and Widevine stuff...
			a. To get all available devices: https://telus.prod.g.telustvplus.com/TELUS/T7.1/R/ENG/CHROME_FIREFOX_HTML5/OPTIK/TRAY/EXTCOLLECTION/9393
				- "availableAlso":["ANDROID","CHROME_HTML5","OTTSTB","TVOS","IOS","ANDROID_WV1","ANDROID_WV3","ANDROID_TV_BYOD","ANDROID_TV_STB","CHROME_FIREFOX_HTML5","SAFARI_HTML5","EDGE_HTML5"]

			b. To get all channels: https://telus.prod.g.telustvplus.com/TELUS/T7.1/A/ENG/CHROME_FIREFOX_HTML5/OPTIK/TRAY/LIVECHANNELS?orderBy=orderId&sortOrder=asc
			Note: Channel URLs also shown here

			c. To get token for https://multidrm.core.verimatrixcloud.net/widevine authorization header:
				Note: ANDROID_WV1 & ANDROID_WV3 require longitude/latitude coordinates

				- https://telus.prod.g.telustvplus.com/TELUS/T7.1/R/ENG/{a.availableAlso[x]}/OPTIK/CONTENT/VIDEOURL/LIVE/{b.channel_id}/10
				OR:
				- https://telus.prod.g.telustvplus.com/TELUS/T7.1/R/ENG/{a.availableAlso[x]}/OPTIK/CONTENT/VIDEOURL/LIVE/{b.channel_id}/10?longitude=xxx&latitude=yyy

				Response:
				{
					"resultCode": "OK",
					"message": "",
					"errorDescription": "200-10000",
					"resultObj": {
						"src": "https://xxxx-yyy-opus.cdn.avp.telus.net/{access_url_id}/vxfmt=dp/manifest.mpd?device_profile=dashvmx",
						"token": "eyJ...",
						"isOutOfHome": false
					},
					"systemTime": xxx
				}
				
				NOTE FOR TELUS: Expire access to endpoint with same Cookie after use, rather than a few hours... Or I think: change cookie["avs_cookie"]["EXP"] from 4 hours to 1-5 minutes. Also... Maybe... HIRE ME???

		2) Subdomains: https://securitytrails.com/list/apex_domain/cdn.avp.telus.net
			a. Live:
				- lott2-stb-opus.cdn.avp.telus.net
				- lott4-web-opus.cdn.avp.telus.net
				- lott5-reach-opus.cdn.avp.telus.net
			b. DVR:
				- ndvr3-reach-opus.cdn.avp.telus.net
			c. VOD:
				- vod-bcvp-stb-opus.cdn.avp.telus.net
	'''
	def __get_links(self, max_streamer):
		base_urls = [
			"stb",
			"reach",
			"web"
		]
		base_url = f"-{choice(base_urls)}-opus.cdn.avp.telus.net"

		streamer_range = range(1, max_streamer + 1)
		live_or_dvr = choice(["lott", "ndvr"])
		links = [f"{live_or_dvr}{i if i > 1 else ''}" for i in streamer_range]

		return base_url, links

	# When forwarding headers from telus servers, remove Content-Length & Server headers
	def __fix_headers(self, headers):
		headers_to_remove = [
			"Content-Length",
			"Server"
		]

		for header_key in headers_to_remove:
			headers.pop(header_key, None)

		return headers

	# Return manifest and response headers when found which server a channel is running on
	def __test_link(self, link, channel):
		url_base = f"https://{link}{self.__baseURL}/{channel}/vxfmt=dp/%s"
		link_base = "manifest.mpd?device_profile=dashvmx"

		redirect_url = url_base % link_base
		redirect_request = head(redirect_url, headers=self.requestHeaders, verify=True, proxies=self.__proxies)
		response_headers = redirect_request.headers

		if "Location" not in response_headers:
			return None, False

		streamer = response_headers["Location"]
		streamer_request = head(streamer, headers=self.requestHeaders, verify=True, proxies=self.__proxies)

		if streamer_request.status_code == 200:
			fix_url = f"SEGMENT/{channel}/" if self.proxySegments else streamer.replace(link_base, '')
			self.__segmentURLs[channel] = streamer.replace(link_base, '') if self.proxySegments else self.__segmentURLs.get(channel)

			get_manifest = get(streamer, headers=self.requestHeaders, verify=True, proxies=self.__proxies)
			manifest_headers = self.__fix_headers(get_manifest.headers)

			manifest = get_manifest.text.replace("media=\"", f"media=\"{fix_url}")
			manifest = manifest.replace("initialization=\"", f"initialization=\"{fix_url}")

			return manifest_headers, manifest
		else:
			return None, False

	'''
	Calls __test_link to check through:
		1. xxxx-yyy-opus.cdn.avp.telus.net
		2. xxxx2-yyy-opus.cdn.avp.telus.net
		3. xxxx3-yyy-opus.cdn.avp.telus.net
		4. xxxx4-yyy-opus.cdn.avp.telus.net
		5. xxxx5-yyy-opus.cdn.avp.telus.net

	And returns manifest and response headers if link is valid and channel found
	'''
	def __find_server(self, channel):
		resp = {
			"Headers": {},
			"Content": False
		}

		with ThreadPoolExecutor() as executor:
			future_to_link = {executor.submit(self.__test_link, link, channel): link for link in self.__links}

			for future in as_completed(future_to_link):
				link = future_to_link[future]
				try:
					future_result = future.result()
					if future_result and future_result[1]:
						resp["Headers"], resp["Content"] = future_result
				except Exception as exc:
					resp["Content"] = f"Generated an exception: {exc}"

		if resp["Content"]:
			return resp
		else:
			return False

	# Create Flask response with response headers
	def __return(self, content, status_code, headers = {}):
		resp = make_response(content, status_code) if status_code else make_response(content)

		if headers:
			for header, value in headers.items():
				resp.headers[header] = value

		return resp

	# Checks for valid request from client
	def __check_client_request(self):
		req_headers = request.headers

		if self.cdnLoop and req_headers.get("CDN-LOOP", '') != self.cdnLoop:
			return self.__return("Not Allowed", 403)

		if self.allowedUserAgent and self.allowedUserAgent not in req_headers.get("User-Agent", ''):
			return self.__return("Not Allowed", 403)

		return False

	# Set cache for manifest or segment
	def __set_redis_cache(self, redis_key, cache_time, content, status_code, headers):
		headers["X-Redis-Cache"] = "MISS"
		headers["X-Redis-Cache-TTL"] = '0'

		# Determine if content is text (str) or binary (bytes)
		if isinstance(content, str):
			content_bytes = content.encode(self.encoding)
			is_text = True
		else:
			# Content is already bytes
			content_bytes = content
			is_text = False

		# Base64 encode the bytes
		enc_content = b64encode(content_bytes).decode(self.encoding)

		response_data = {
			"content": enc_content,
			"is_text": is_text,
			"status_code": status_code,
			"headers": dict(headers)
		}

		self.__redisClient.setex(redis_key, cache_time, dumps(response_data))

	# Get cache for manifest or segment if exists
	def __get_redis_cache(self, redis_key):
		cached_content = self.__redisClient.get(redis_key)
		if cached_content:
			cached_data = loads(cached_content)

			# Base64 decode to get bytes
			content_bytes = b64decode(cached_data["content"])

			# Check the flag to see if original content was text or binary
			if cached_data.get("is_text"):
				# Decode bytes back to string
				content = content_bytes.decode(self.encoding)
			else:
				# Keep content as bytes
				content = content_bytes

			headers = cached_data["headers"]

			ttl = self.__redisClient.ttl(redis_key)
			headers["X-Redis-Cache"] = "HIT" if ttl > 0 else "EXPIRED"
			headers["X-Redis-Cache-TTL"] = str(ttl) if ttl > 0 else '0'

			return self.__return(content, cached_data["status_code"], headers)
		else:
			return False

	# Call __find_server and return modified manifest with headers if channel found
	def __get_channel_manifest(self, access_url_id):
		check_client_request = self.__check_client_request()
		if check_client_request:
			return check_client_request

		# Set cache key
		redis_key = f"manifest:{access_url_id}"

		# Try to fetch from Redis
		check_cache = self.__get_redis_cache(redis_key)
		if check_cache:
			return check_cache

		output = self.__find_server(access_url_id)
		if output:
			# Cache the response in Redis
			self.__set_redis_cache(redis_key, self.manifestCacheSeconds, output["Content"], False, output["Headers"])

			return self.__return(output["Content"], False, output["Headers"])
		else:
			return self.__return(f"Unable to find channel id: {access_url_id}", 404)

	# Gets the segment if self.proxySegments = True
	def __get_channel_segment(self, access_url_id, segment):
		check_client_request = self.__check_client_request()
		if check_client_request:
			return check_client_request

		if not self.proxySegments:
			return self.__return(f"Segment proxy is disabled", 403)

		# Redis key for caching segment data
		redis_key = f"segment:{access_url_id}:{segment}"

		# Try to fetch from Redis
		check_cache = self.__get_redis_cache(redis_key)
		if check_cache:
			return check_cache

		if self.__segmentURLs.get(access_url_id) is None:
			return self.__return(f"Segment URL not found for channel id: {access_url_id}", 500)

		query_string = request.query_string.decode(self.encoding)
		full_segment = f"{self.__segmentURLs[access_url_id]}{segment}?{query_string}" if query_string else segment

		get_segment = get(full_segment, headers=self.requestHeaders, verify=True, proxies=self.__proxies)

		if get_segment.status_code != 200:
			return self.__return(f"Segment not found for channel id: {access_url_id}", 404)

		headers = self.__fix_headers(get_segment.headers)

		content = get_segment.content

		# Cache the response in Redis
		self.__set_redis_cache(redis_key, self.segmentCacheSeconds, content, False, headers)

		return self.__return(content, False, headers)

	# Start the Web Server using waitress
	def start_web_app(self, port = 80):
		# Waitress
		serve(self.__app, host="0.0.0.0", port=port, ident=self.serverHeader)

		# Flask (For debugging)
		#self.__app.run(debug=True, host="0.0.0.0", port=port)
