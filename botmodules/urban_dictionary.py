import urllib.parse


def get_urbandictionary(self, e):
    searchterm = e.input
    url = "http://www.urbandictionary.com/define.php?term=%s" % urllib.parse.quote(searchterm)

    if searchterm == "wotd":
        e.output = get_urbandictionary_wotd(self)
        return e

    if searchterm == "":
        url = "http://www.urbandictionary.com/random.php"

    page, url = self.tools["load_html_from_URL"](url, returnurl=True)

    first_definition = ""

    if page.find(id='not_defined_yet') is not None:
        return None

    first_word = page.findAll('div', attrs={"class": "word"})[0].a.string

    first_word = first_word.replace("\n", "")

    for content in page.findAll('div', attrs={"class": "meaning"})[0].contents:
        if content.string is not None:
            first_definition += content.string

    #first_definition = first_definition.encode("utf-8", 'ignore')
#    first_definition = tools.decode_htmlentities(first_definition)
#    first_word = tools.decode_htmlentities(first_word)

    first_definition = first_definition.replace("\n", " ")
    first_definition = first_definition.replace("\r", " ")
    first_definition = first_definition[0:392]

    first_definition = ((first_word + ": " + first_definition) + " [ %s ]" % self.tools['shorten_url'](url))
    #print first_definition
    e.output = first_definition
    return e

get_urbandictionary.command = "!ud"
get_urbandictionary.helptext = """Usage: !ud <word or phrase>
Example: !ud hella
Shows urbandictionary definition of a word or phrase.
!ud alone returns a random entry
!ud wotd returns the current word of the day"""


def get_urbandictionary_wotd(self):

    url = "http://www.urbandictionary.com"
    page = self.tools["load_html_from_URL"](url)
    first_definition = ""

    first_word = page.findAll('div', attrs={"class": "word"})[0].contents[1].contents[0].string
    first_word = first_word.encode("utf-8", 'ignore')

    for content in page.findAll('div', attrs={"class": "meaning"})[0].contents:
        if content.string is not None:
            first_definition += content.string

#    first_definition = tools.decode_htmlentities(first_definition)
    first_definition = first_definition.replace("\n", " ")

    wotd = (first_word.decode('utf-8') + ": " + first_definition + " [ %s ]" % self.tools['shorten_url'](url))

    return wotd
