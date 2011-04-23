from BeautifulSoup import BeautifulSoup
import re, urllib2, botmodules.tools as tools

def get_wiki(searchterm, nick, urlposted=False):
    #read the first paragraph of a wikipedia article

  if urlposted:
      url = searchterm
  else:
      if searchterm == "":
          url = "http://en.wikipedia.org/wiki/Special:Random"
      else:
          url = tools.google_url("site:wikipedia.org " + searchterm,"wikipedia.org/wiki")
  
  title = "" 
  
  if url and url.find("wikipedia.org/wiki/File:") != -1:
    
    file_title=get_wiki_file_description(url)
    
    if not file_title: pass
    else: return file_title
    
    
  if url and url.find("wikipedia.org/wiki/") != -1:

    try:
      opener = urllib2.build_opener()
      opener.addheaders = [('User-Agent',"Opera/9.10 (YourMom 8.0)")]
      pagetmp = opener.open(url)
      page = pagetmp.read()
      opener.close()

      if url.find('#') != -1:
        anchor = url.split('#')[1]
        page = page[page.find('id="' + anchor):]

      page = BeautifulSoup(page)
      tables = page.findAll('table')
      for table in tables:
        table.extract()
        
      page = page.findAll('p')
      if str(page[0])[0:9] == '<p><span ':
          page = unicode(page[1].extract())
      else:
          page = unicode(page[0].extract())

      title = tools.remove_html_tags(re.search('(?s)\<p\>(.*?)\<\/p\>',page).group(1))
      title = title.encode("utf-8", 'ignore')
      title = title.replace("<","");
      rembracket = re.compile(r'\[.*?\]')
      title = rembracket.sub('',title)
      #title = re.sub("\&.*?\;", " ", title)
      title = title.replace("\n", " ")
      
      title = tools.decode_htmlentities(title.decode("utf-8", 'ignore')).encode("utf-8", 'ignore')

      title = title[0:420]
      if title.rfind(".")!=-1:
        title = title[0:title.rfind(".")+1]
        
      if not urlposted:
        title = (title.decode('utf-8') + " [ %s ]" % tools.shorten_url(url)).encode('utf-8', 'ignore')
    except Exception as inst: 
      print "!wiki " + searchterm + " : " + str(inst)
      title = tools.remove_html_tags(re.search('\<p\>(.*?\.) ',str(page)).group(1))

  return title
get_wiki.command = "!wiki"
get_wiki.helptext = "Usage: !wiki <search term>\nExample: !wiki carl sagan\nShows the first couple of sentences of a wikipedia entry for the given search term"


def get_wiki_file_description(url):
  try:
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent',"Opera/9.10 (YourMom 8.0)")]
    pagetmp = opener.open(url)
    page = pagetmp.read()
    opener.close()

    page = BeautifulSoup(page)
    
    try:
      desc = page.findAll("div",attrs={"class":"description en"})[0].getText(separator=" ")
      #print "hit 1st case"
    except:
      try:
        desc = page.find("th",attrs={"id" : "fileinfotpl_desc"}).findNextSibling("td").find("p").getText(separator=" ")
       #print "hit 2nd case"
      except:
        try:
          desc = page.find("th",attrs={"id" : "fileinfotpl_desc"}).findNextSibling("td").find("div").getText(separator=" ")   
          #print "hit 3rd case"
        except:
          try:
            desc = page.find("div",attrs={"id":"shared-image-desc"}).next.getText(separator=" ")
            #print "hit 4th case"
          except:
            print "Couldn't find description for file %s" % url
            return False
      
    
    desc = desc.encode("utf-8", 'ignore')
    desc = desc.replace("English:","")
    desc = tools.decode_htmlentities(desc.decode("utf-8", 'ignore')).encode("utf-8", 'ignore')
    desc = desc[0:420]
    if desc.rfind(".")!=-1:
      desc = desc[0:desc.rfind(".")+1]
    
    #print desc  
    return desc.strip()
      
  except:
    print "Finding a file description failed miserably. The URL probably didn't even load."  
    return
    