import urllib.request, urllib.error, urllib.parse
import xml.dom.minidom


def get_woot(self, e):
    #display the current woot.com sale
    woot = e.input or "woot"
    url = "http://api.woot.com/1/sales/current.rss/" + woot
    dom = xml.dom.minidom.parse(urllib.request.urlopen(url))

    product = dom.getElementsByTagName("woot:product")[0].childNodes[0].data
    product = self.tools['decode_htmlentities'](product)

    price = dom.getElementsByTagName("woot:price")[0].childNodes[0].data
    link = dom.getElementsByTagName("link")[1].childNodes[0].data

    e.output = product + " [" + price + "] " + link
    return e

get_woot.command = "!woot"
get_woot.helptext = "Usage: !woot\nShows today's deal from woot.com"
