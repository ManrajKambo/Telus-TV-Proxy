# Telus TV+ Proxy
<i>Proxy all Telus TV+ channels from one host url.</i>

What I created here just acts as a proxy to Telus TV+ streaming servers.

For my example, I'll be using the `A&E Canada HD` channel: `https://lott-web-opus.cdn.avp.telus.net/232006003096/vxfmt=dp/manifest.mpd?device_profile=dashvmx`

This channel might be on either of the following servers:
- lott-web-opus.cdn.avp.telus.net
- lott2-web-opus.cdn.avp.telus.net
- lott3-web-opus.cdn.avp.telus.net
- lott4-web-opus.cdn.avp.telus.net
- lott5-web-opus.cdn.avp.telus.net

It also may switch from one to another. There are WEB, STB, and DVR host urls but all do the same pretty much.

My application just allows there to be one host for every channel.

After building the application (`sh Build.sh`), the A&E MPEG-DASH manifest link would be: `http://your.server.ip:port/232006003096.mpd`

You can define whether you would like to proxy the segments or just connect to the source directly.

`app.py` includes a few other features, take a look at it before building the application.

NOTE: This app utilizes Redis for caching. By default, the MPEG-DASH manifest is cached for 5 seconds, segments are cached for 60 seconds.

##

Update 2 - DVR Compatibility

I added DVR Compatibility. DVR Catch Up works when playing streams in the TiviMate app (https://tivimate.com/)

M3U Playlist example:
```
#EXTM3U url-tvg="https://github.manrajkambo.ca/Telus-TV-EPG/releases/download/latest/epg.xml" x-tvg-url="https://github.manrajkambo.ca/Telus-TV-EPG/releases/download/latest/epg.xml"

#KODIPROP:inputstream.adaptive.license_type=clearkey
#KODIPROP:inputstream.adaptive.license_key={DRM-KEY-ID}:{DRM-KEY}
#EXTINF:-1 id="300" channel-id="300" channel-number="300" tvg-id="TELUS.AETVHD" tvg-name="A&E Canada [AETVHD]" tvg-logo="https://gn-images-stb-opus.cdn.avp.telus.net/assets/s55097_ld_h9_aa.png" group-title="English" catchup="default",A&E Canada [AETVHD]
http://your.server.ip:port/232006003096.mpd
```

DVR requests look like this:
/232006003096.mpd?utc=EPOCHSTART&lutc=EPOCHEND

EX: /232006003096.mpd?utc=1740607498&lutc=1740608991

NOTE: Seconds are ignored, requests are translated to the nearest minute.

##

Most ISPs don't know how to properly implement content protection. It doesn't help that Widevine can be easily decrypted, so that's why we here now.

Some good practices for content protection are to:
1. Utilize Geo blocking
2. Require user token authentication, take notes from Bell's Fibe TV (https://www.bell.ca/Fibe-TV)
3. Implement dynamic stream links with expiry, take notes from River TV (https://www.rivertv.ca)
4. Rotate content (drm) keys regularly, take notes from Sling TV (https://www.sling.com)

Comcast's DRM solution is pretty good, but they should try to implement 2-4.. I had obtained drm keys from Shaw, Rogers, Cox, as well as a few other providers that use Comcast's DRM solution a few years back. Those keys still work to this day...

The main focus for this project was Telus, as they don't appear to implement any of the mentioned stuff. 

Since Telus introduced their On-The-Go TV platform, I was able to obtain all of their DRM (Digital Rights Management) keys for various TV channels. While Telus TV+ has improved with API rate limiting, they should probably implement additional content protection measures, as I am still able to access the DRM keys despite them now using Verimatrix's DRM solution (https://www.verimatrix.com).

##

<details open>
<summary>License</summary>
<b>This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.</b>
</details>
