import urllib.request, urllib.error, urllib.parse

def get_fml(self, e):
    #queries a random fmylife.com passage
    fmlxml = urllib.request.urlopen("http://api.betacie.com/view/random?key=%s&language=en" % self.botconfig["APIkeys"]["fmlAPIkey"]).read().decode('utf-8')
    start = fmlxml.find("<text>") + 6
    end = fmlxml.find("</text>")

    fml = fmlxml[start:end]

    start = fmlxml.find("<agree>") + 7
    end = fmlxml.find("</agree>")

    iAgree = int(fmlxml[start:end])

    start = fmlxml.find("<deserved>") + 10
    end = fmlxml.find("</deserved>")

    iDeserved = int(fmlxml[start:end])

    # Use percentages for more meaningful schadenfreude stats
    total = iAgree+iDeserved
    iAgree = round(iAgree/(total)*100,1)
    iDeserved = round(iDeserved/(total)*100,1)

    sAgree = " [FYL: " + str(iAgree) + "%"
    sDeserved = " Deserved it: " + str(iDeserved) + "%]"

    # Put together the whole line for output
    fml = fml + sAgree + sDeserved

    fml = fml.replace('&quot;', '"')
    fml = fml.replace('&amp;quot;', '"')
    fml = fml.replace('&amp;', "&")
    e.output = self.tools['decode_htmlentities'](fml)

    return e

get_fml.command = "!fml"
get_fml.helptext = "Usage: !fml\nShows a random entry from fmylife.com"

