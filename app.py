from TelusTV import TelusTV

# Call the TelusTV class and start web server
def main():
	port = 80 # Web server port
	streamer_range = 5 # 5 being max, xxxx[None, 2-5] for streaming server range

	tv = TelusTV(streamer_range)

	'''
	OPTIONS:

	tv.allowedUserAgent = "Mozilla" # Client User-Agent header must contain this value
	tv.cdnLoop = "cloudflare" # Say that you have this server behind a CDN like cloudflare and don't want to allow direct server access
	tv.serverHeader = "OogaBooga" # Change the Server header to whatever you'd like
	tv.requestHeaders["Header-Key"] = "Header-Value" # Send your own header to source
	tv.set_proxy("protocol://your.proxy:port") # Could use: https://github.com/Mon-ius/Docker-Warp-Socks
	tv.proxySegments = False # By default, segment proxy is enabled
	tv.encoding = "UTF-8" # Don't change unless you are having issues
	tv.manifestCacheSeconds = 10 # Cache manifest for X seconds
	tv.segmentCacheSeconds = 120 # Cache segments for X seconds
	'''

	tv.start_web_app(port)

if __name__ == "__main__":
	main()