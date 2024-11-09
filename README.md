# Telus TV+ Proxy
<i>Proxy all Telus TV+ channels from one host url (DRM KEYS NOT INCLUDED NOR WILL BE)</i>

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

You can define wether you would like to proxy the segments or just connect to the source directly.

`app.py` includes a few other features, take a look at it before building the application.

NOTE: This app utilizes Redis for caching. By default, the MPEG-DASH manifest is cached for 5 seconds, segments are cached for 60 seconds.

##

Most ISPs don't know how to properly implement content protection. It doesn't help that Widevine can be easily decrypted, so that's why we here now.

Some good practices for content protection are to:
1. Utilize Geo blocking
2. Require user token authentication, take notes from Bell's Fibe TV (https://www.bell.ca/Fibe-TV)
3. Implement dynamic stream links with expiry, take notes from River TV (https://www.rivertv.ca)
4. Rotate content (drm) keys regularly, take notes from Sling TV (https://www.sling.com)

<small>Comcast's DRM solution is pretty good, but they should try to implement 2-4.. I had obtained drm keys from Shaw, Rogers, Cox, as well as a few other providers that use Comcast's DRM solution a few years back. Those keys still work to this day...</small>

The main focus for this project was Telus, as they don't appear to impliment any of the mentioned stuff. 

<small>Ever since Telus had the On-The-Go TV platform, I was able to obtain all of their DRM keys for tv channels. Telus TV+ is ight with the API rate limiting, but they should prob implement some content protection as I am still able to get the drm keys, despite them now using Verimatrix's DRM solution (https://www.verimatrix.com)</small>

##

<details close>
<summary>Can you contact me for some DRM keys?</summary>
<b>No, Fuck off!</b>
</details>

</br>

<details open>
<summary>License</summary>
<b>This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.</b>
</details>