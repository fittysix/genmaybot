import re


def advocate_beer(self, e):
    query = e.input
    #get the name, rating and style of a beer from beeradvocate.com
    url = self.tools['google_url']("site:beeradvocate.com " + query, "/beer/profile/[0-9]*?/[0-9]+")
    #url = "http://beeradvocate.com/beer/profile/306/1212/"

    beerpage = self.tools["load_html_from_URL"](url)

    beertitle = beerpage.head.title.string
    beertitle = beertitle[0:beertitle.find("|") - 1]

    grade = beerpage.find("span", {"class": "BAscore_big"}).string
    grade_wording = beerpage.find("a", href="/help/?topic=ratings").b.string
    num_reviews = beerpage.find(text=re.compile("[0-9]+ Ratings"))
    style = beerpage.find("a", href=re.compile("/beer/style/[0-9]+/")).b.string
    abv = beerpage.find("a", href=re.compile("/beer/style/[0-9]+/")).next_sibling.replace("|", "").strip()

    e.output = "Beer: %s - Grade: %s [%s, %s] Style: %s ABV: %s [ %s ]" % (beertitle, 
                                                                           grade,
                                                                           grade_wording,
                                                                           num_reviews,
                                                                           style,
                                                                           abv,
                                                                           self.tools['shorten_url'](url))
    return e
advocate_beer.command = "!beer"
advocate_beer.helptext = """\
Usage: !beer <beer name>
Example: !beer pliny the elder
Finds a given beer on beeradvocate.com and returns user ratings and beer info"""
