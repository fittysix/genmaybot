import json
import urllib.request
import urllib.parse
import re
import gzip


def get_rt(self, e):
    url = self.tools['google_url']("site:imdb.com inurl:com/title " + e.input, "imdb.com/title/tt\\d{7}/")
    imdbid = re.search("tt\\d{7}", url).group(0)[2:]

    url = "http://api.rottentomatoes.com/api/public/v1.0/movie_alias.json?id={}&type=imdb&apikey={}"
    url = url.format(imdbid, self.botconfig["APIkeys"]["rtAPIkey"])

    movie = loadjson(url)
    if 'error' in movie:
        # our IMDB serach didn't work, so lets try rt's normally-useless search
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies.json?q={}&page_limit=1&page=1&apikey={}"
        url = url.format(urllib.parse.quote(e.input), self.botconfig["APIkeys"]["rtAPIkey"])
        results = loadjson(url)
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies/{}.json?apikey={}"
        url = url.format(results['movies'][0]['id'], self.botconfig["APIkeys"]["rtAPIkey"])
        movie = loadjson(url)

    concensus = ""
    if 'critics_consensus' in movie:
        concensus = "- " + movie['critics_consensus']
    url = self.tools['shorten_url'](movie['links']['alternate'])
    e.output = "%s (%s) - Critics: %s - Users: %s %s [ %s ]" % (movie['title'],
                                                                str(movie['year']),
                                                                str(movie['ratings']['critics_score']),
                                                                str(movie['ratings']['audience_score']),
                                                                concensus,
                                                                url)
    return e
get_rt.command = "!rt"


def loadjson(url):
    response = urllib.request.urlopen(url).read()
    try:
        #RT likes to randomly give us gzipped data even though we never requested it
        response = gzip.decompress(response)
    except:
        pass
    response = response.decode("utf-8")
    return json.loads(response)
