import json
import urllib.request
import re


def ytinfo(self, e, urlposted=False):
    if urlposted:
        yt = e.input
        if "youtube.com" not in yt and "youtu.be" not in yt:
            return
        yt = re.search("(v=|/)([\w-]+)(&.+|#t=.+|\?t=.+)?$", yt).group(2)
    else:
        yt = self.tools['google_url']('site:youtube.com {}'.format(e.input), 'watch%3Fv%3D')
        yt = yt[yt.find("%3Fv%3D") + 7:]

    url = "http://gdata.youtube.com/feeds/api/videos/{}?v=2&alt=jsonc".format(yt)

    request = urllib.request.urlopen(url)
    ytjson = json.loads(request.read().decode())
    ytjson = ytjson['data']
    mins = ytjson['duration'] // 60
    if mins:
        mins = "{}m ".format(str(mins))
    else:
        mins = ""
    secs = ytjson['duration'] % 60
    if secs:
        secs = "{}s ".format(str(secs))
    else:
        secs = ""
    duration = "{}{}".format(mins, secs)
    
    try:
        rating = "{0:.1f}/10".format((int(ytjson['likeCount']) / ytjson['ratingCount']) * 10)
    except KeyError:
        rating = "NA"
    
    ytlink = ""
    if not urlposted:
        ytlink = " - http://youtu.be/" + yt

    content = ""
    try:
        if ytjson['contentRating']:
            content = " - 4NSFW"
    except KeyError:
        pass

    e.output = "Youtube: {} [{}] :: length: {}- rated: {} - {} views - {} on {}{}{}".format(ytjson['title'],
                                                                                            ytjson['category'],
                                                                                            duration,
                                                                                            rating,
                                                                                            ytjson['viewCount'],
                                                                                            ytjson['uploader'],
                                                                                            ytjson['uploaded'][:10],
                                                                                            ytlink, content)
    return e
ytinfo.command = "!yt"
ytinfo.helptext = """
Usage: !yt <vide title>
Example: !yt cad video
Looks up a given youtube video, and provides information and a link"""
