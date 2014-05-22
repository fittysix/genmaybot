import re


def get_imdb(self, e, urlposted=False):
    #reads title, rating, and movie description of movie titles
    searchterm = e.input
    if urlposted:
        url = searchterm
    else:
        url = self.tools['google_url']("site:imdb.com inurl:com/title " + searchterm, "imdb.com/title/tt\\d{7}/")

    if not url:
        pass
    elif url.find("imdb.com/title/tt") != -1:
        movietitle = ""
        rating = ""
        summary = ""
        imdbid = re.search("tt\\d{7}", url)
        imdburl = ('http://www.imdb.com/title/' + imdbid.group(0) + '/')
        page = self.tools["load_html_from_URL"](imdburl)

        movietitle = page.html.head.title.string.replace(" - IMDb", "")
        movietitle = movietitle.replace("IMDb - ", "")
        movietitle = "Title: " + movietitle

        if page.find(id="overview-top") != None:
            page = page.find(id="overview-top").extract()

            if page.find("div", "star-box-giga-star") != None:
                rating = self.tools['remove_html_tags'](str(page.find("div", "star-box-giga-star").text))
                rating = " - Rating: " + rating.replace("\n", "")  # remove newlines since BS4 adds them in there

            try:

                summary = str(page.find('p', itemprop='description'))

                summary = re.sub(r'\<a.*\/a\>', '', summary)
                summary = self.tools['remove_html_tags'](summary)
                summary = summary.replace('&raquo;', "")
                summary = summary.replace("\n", "")
                summary = " - " + summary
            except:
                pass

        title = movietitle + rating + summary
        if not urlposted:
            title = title + " [ %s ]" % url

        e.output = title

        return e
get_imdb.command = "!imdb"
get_imdb.helptext = "Usage: !imdb <movie title>\nExample: !imdb the matrix\nLooks up a given movie title on IMDB and shows the movie rating and a synopsis"
