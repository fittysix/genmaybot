
def get_metacritic(self, e):
    url = self.tools['google_url']("site:metacritic.com " + e.input, "www.metacritic.com/")
    page = self.tools["load_html_from_URL"](url)
    titleDiv = page.findAll('div', attrs={"class": "product_title"})[0]
    try:
        title = titleDiv.a.span.string.strip()
    except: #tv shows have an extra span
        title = ""
        for string in titleDiv.a.stripped_strings:
            title = title + string
    titleUrl = titleDiv.a['href']
    if titleUrl.find("game/") > 0:
        category = 'Game - '
        category += titleDiv.findAll('span', attrs={"class": "platform"})[0].a.span.string.strip()
    elif titleUrl.find("movie/") > 0:
        category = "Movie"
    elif titleUrl.find("tv/") > 0:
        category = "TV"
    elif titleUrl.find("music/") > 0:
        category = "Music"
        # band name is here, append it to title
        title += " " + titleDiv.findAll('span', attrs={"class": "band_name"})[0].string

    if category:
        category = "(%s) " % category

    # declare these to avoid null reference
    metaScore = ""
    userScore = ""

    metaScoreDiv = page.findAll('div', attrs={"class": "metascore_wrap highlight_metascore"})[0]
    metaScore = metaScoreDiv.findAll('span', attrs={"itemprop": "ratingValue"})[0].string
    metaDesc = metaScoreDiv.findAll('span', attrs={"class": "desc"})[0].string.strip()
    metaNum = metaScoreDiv.findAll('span', attrs={"itemprop": "reviewCount"})[0].string.strip()

    userScoreDiv = page.findAll('div', attrs={"class": "userscore_wrap feature_userscore"})[0]
    userScore = userScoreDiv.a.div.string
    userDesc = userScoreDiv.findAll('span', attrs={"class": "desc"})[0].string
    userNum = userScoreDiv.find('span', attrs={"class": "count"}).a.string

    if metaScore:
        metaScore = "Metascore: " + metaScore
        metaScore += " out of 100 - %s (%s Reviews)" % (metaDesc.strip(), metaNum.strip())
        metaScore = "%s | " % metaScore
    if userScore:
        userScore = "User Score: " + userScore
        userScore += " out of 10 - %s (%s)" % (userDesc.strip(), userNum.strip())

    if metaScore or userScore:
        e.output = "%s %s| %s%s" % (title, category, metaScore, userScore)
    return e

get_metacritic.command = "!mc"

