#! /usr/bin/env python
#
#To run this bot use the following command:
#
#  python genmaybot.py irc.0id.net "#chan" Nickname
#

#? look in to !seen functionality 
###? Investigate flight tracker info
#random descision maker?

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import time, urllib2, json, urllib, asyncore, locale
from htmlentitydefs import name2codepoint as n2cp
import xml.dom.minidom, threading
import sys, os, hashlib, socket, re, datetime, ConfigParser
from BeautifulSoup import BeautifulSoup

try:
    import MySQLdb
except ImportError:
    pass

socket.setdefaulttimeout(5)

spam ={}

class TestBot(SingleServerIRCBot):
    
  
    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.doingcommand = False
        self.lastspamtime = time.time() - 60
        self.lastquakecheck = ""
        self.commandaccesslist = {}
        self.commandcooldownlast = {}
        self.lastcalcresult = ""
        
        config = ConfigParser.ConfigParser()
        config.readfp(open('genmaybot.cfg'))
        
        self.wolframAPIkey = config.get("APIkeys","wolframAPIkey")
        self.fmlAPIkey = config.get("APIkeys","fmlAPIkey")
        self.identpassword = config.get("irc","identpassword")
        self.sqlpassword = config.get("mysql","sqlpassword")
        self.sqlusername = config.get("mysql","sqlusername")
        self.sqlmode = config.get("mysql","mysqlmode")
        self.botadmins = config.get("irc","botadmins").split(",")
        
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")
    
    def on_kick(self, c, e):
        if e.arguments()[0][0:6] == c.get_nickname():
           c.join(self.channel)

    def on_welcome(self, c, e):
        c.privmsg("NickServ", "identify " + self.identpassword)
        c.join(self.channel)       
        self.quake_alert(c) 

#    def on_join(self,c,e):
#        if e.source().split('!')[0][0:6] == "Python":
#            print "saw python"
#            sys.exit(0)        
            
    def on_invite(self, c, e):
        c.join(e.arguments()[0])

    def on_privmsg(self, c, e):
        #print "PRIVMSG: " + e.arguments()[0]
        #print "Target: " + e.target()
        #print "Source: " + e.source()
        
        from_nick = e.source().split("!")[0]
        line = e.arguments()[0].strip()
        
        if line == "die" or \
           line == "clearbans" or\
           line[0:6] == "enable" or\
           line[0:7] == "disable" or\
           line[0:8] == "cooldown" or\
           line[0:6] == "status":
                self.admincommand = line
                c.who(from_nick) 
        
        say = ""
        if line[0:1] == "!":
            say = self.bangcommand(e.arguments()[0])
        if say:
            c.privmsg(from_nick, say[0:600]) 
        
        if line == "ban jeffers":
          print from_nick
          c.privmsg(from_nick, "NO U! " + from_nick)
          c.privmsg(self.channel, "!ban jeffers")
    
    def on_whoreply(self, c,e):
        global spam
        nick = e.arguments()[4]
        line = self.admincommand
        self.admincommand = ""
        if e.arguments()[5].find("r") != -1 and line != "" and self.isbotadmin(nick):       
            if line == "die":
                print "got die command from " + nick 
                sys.exit(0)
            elif line == "clearbans":
                print nick + "cleared bans"
                spam ={}
                c.privmsg(nick, "All bans cleared")
            elif line[0:6] == "enable":
                if len(line.split(" ")) == 2:
                    command = line.split(" ")[1]
                    if command in self.commandaccesslist:
                        del self.commandaccesslist[command]
                        c.privmsg(nick, command + " enabled")
                    else:
                        c.privmsg(nick, command + " not disabled")
            elif line[0:7] == "disable":
                if len(line.split(" ")) == 2:
                    command = line.split(" ")[1]
                    self.commandaccesslist[command] = "Disable"
                    c.privmsg(nick, command + " disabled")
            elif line[0:8] == "cooldown":
                if len(line.split(" ")) == 3:
                    command = line.split(" ")[1]
                    cooldown = line.split(" ")[2]
                    if cooldown.isdigit():
                        cooldown = int(cooldown)
                        if cooldown == 0:
                            del self.commandaccesslist[command]
                            c.privmsg(nick, command + " cooldown disabled")
                        else:
                            self.commandaccesslist[command] = cooldown
                            self.commandcooldownlast[command] = time.time() - cooldown   
                            c.privmsg(nick, command + " cooldown set to " + str(cooldown) + " seconds (set to 0 to disable)")
                    else:
                        c.privmsg(nick, "bad format: 'cooldown !wiki 30' (30 second cooldown on !wiki)")
                else:
                    c.privmsg(nick, "not enough args")
            elif line[0:6] == "status":
                if len(line.split(" ")) == 2:
                    command = line.split(" ")[1]
                    if command in self.commandaccesslist:
                        c.privmsg(nick, command + " " + str(self.commandaccesslist[command]) + " (Seconds cooldown if it's a number)")
                    else:
                        c.privmsg(nick, command + " Enabled")
                
        else:
            print "attempted admin command: " + line + " from " + nick
                      
    def on_pubmsg(self, c, e):
        if self.doingcommand:
            return
        self.doingcommand = True
       
        from_nick = e.source().split("!")[0]
        
        try:
          say = ""  
            
          url = re.search("(?P<url>https?://[^\s]+)", e.arguments()[0])
          if url:
            say = self.url_posted(url.group(1))
          elif e.arguments()[0][0:1] == "!":
            say = self.bangcommand(e.arguments()[0])
                
          if say:
              if not self.isspam(from_nick) or self.isbotadmin(from_nick):
                  say = say.replace("join", "join")
                  say = say.replace("come", "come") 
                  c.privmsg(e.target(), say[0:600])     
        except Exception as inst: 
          print e.arguments()[0] + " : " + str(inst)
          pass

        self.doingcommand = False
        return

    def bangcommand(self, line):
        command = line.split(" ")[0]
        args = line[len(command)+1:].strip()
        
        bangcommands = {
                    "!w"        : self.get_weather,
                    "!c"        : self.google_convert,
                    "!q"        : self.get_quake,
                    "!fml"      : self.get_fml,
                    "!beer"     : self.advocate_beer,
                    "!woot"     : self.get_woot,
                    "!lastlink" : self.last_link,
                    "!wolfram"  : self.get_wolfram,
                    "!wiki"     : self.get_wiki,
                    "!imdb"     : self.get_imdb,
                    "!sunrise"  : self.google_sunrise,
                    "!sunset"   : self.google_sunset,
                    "!stock"    : self.get_stock_quote,
                    "!wu"       : self.get_weather2,
                    }
        
        say = ""
        if command in bangcommands and self.commandaccess(command):
            say = bangcommands[command](args)
                
        return say

    def quake_alert(self, context):
      try:
        request = urllib2.urlopen("http://earthquake.usgs.gov/earthquakes/catalogs/1day-M2.5.xml")
        dom = xml.dom.minidom.parse(request)
        latest_quakenode = dom.getElementsByTagName('entry')[0]
        updated = latest_quakenode.getElementsByTagName('updated')[0].childNodes[0].data
        qtitle = latest_quakenode.getElementsByTagName('title')[0].childNodes[0].data
        updated = datetime.datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
        request.close()
        if not self.lastquakecheck:
            self.lastquakecheck = updated
        if updated > self.lastquakecheck :
            self.lastquakecheck = updated	 
            for channel in self.channels:  
                context.privmsg(channel, "Latest Earthquake: " + qtitle)
      except Exception as inst: 
          print inst
          pass
      
      t=threading.Timer(60,self.quake_alert, [context])
      t.start()
    
    def isbotadmin(self, nick):
        return nick in self.botadmins
   
    def commandaccess(self, command):
        if command in self.commandaccesslist:
            if type(self.commandaccesslist[command]) == int:
                if time.time() - self.commandcooldownlast[command] < self.commandaccesslist[command]:
                    return False
                else:
                    self.commandcooldownlast[command] = time.time()
                    return True
            elif self.commandaccesslist[command] == "Disable":
                return False
        else: #if there's no entry it's assumed to be enabled
            return True
                
    def isspam(self, user):
      global spam

      if not (spam.has_key(user)):
        spam[user] = {}
        spam[user]['count'] = 0
        spam[user]['last'] = 0
        spam[user]['first'] = 0
        spam[user]['limit'] = 15
      
      spam[user]['count'] +=1
      spam[user]['last'] = time.time()
      
      if spam[user]['count'] == 1:
        spam[user]['first'] = time.time()
      
      if spam[user]['count'] > 1:
        spam[user]['limit'] = (spam[user]['count'] - 1) * 15

        if not ((spam[user]['last'] - spam[user]['first']) > spam[user]['limit']):
          bantime = spam[user]['limit'] + 15
          print "%s : %s band %s seconds" % (time.strftime("%d %b %Y %H:%M:%S", time.localtime()), user, bantime)
          return True
        else:
          spam[user]['first'] = 0
          spam[user]['count'] = 0
          spam[user]['limit'] = 15
          return False

    def get_wolfram(self, input):
        socket.setdefaulttimeout(30)
        url = "http://api.wolframalpha.com/v2/query?appid=%s&format=plaintext&input=%s" % (self.wolframAPIkey, urllib.quote(input))
        dom = xml.dom.minidom.parse(urllib2.urlopen(url))
        socket.setdefaulttimeout(10)

        if (dom.getElementsByTagName("queryresult")[0].getAttribute("success") == "false"):
            try:
                related = dom.getElementsByTagName("relatedexample")[0].getAttribute("input")
                self.get_wolfram(related)
            except:
                pass
        else:
            try:
                query = dom.getElementsByTagName("plaintext")[0].childNodes[0].data
                result = dom.getElementsByTagName("plaintext")[1].childNodes[0].data
                output = query.replace("\n", " || ") + ": " + result.replace("\n", " || ")
                
                return output.encode("utf-8")
            except:
                pass

    def get_quake(self, nothing):
      try:       
        request = urllib2.urlopen("http://earthquake.usgs.gov/earthquakes/catalogs/1day-M2.5.xml")
        dom = xml.dom.minidom.parse(request)

        latest_quakenode = dom.getElementsByTagName('entry')[0]
        qid = latest_quakenode.getElementsByTagName('id')[0].childNodes[0].data
        qtitle = latest_quakenode.getElementsByTagName('title')[0].childNodes[0].data
        request.close()
        
        return "Latest Earthquake: " + qtitle  
      except:
        pass

    def get_woot(self, nothing):
      try:
          url = "http://www.woot.com/salerss.aspx"
          req = urllib2.Request(url)
          resp = urllib2.urlopen(req).read()
      
          product = re.search('\<woot:product quantity=\"[0-9]*?\"\>(.*?)\<\/woot:product\>',resp).group(1)
          product = decode_htmlentities(product)
      
          price = re.search("<woot:price>(.*?)<\/woot:price>", resp).group(1)
      
          return product + " [" + price + "]"
      except:
          pass
        
    def google_convert(self, term):
        term = term.replace("ANS", self.lastcalcresult)
        url = "http://www.google.com/ig/calculator?q=%s" % urllib.quote(term)
        result = ""
        try:
            response = urllib2.urlopen(url).read() 
            response = response.replace("\xa0"," ").decode('unicode-escape')
            response = re.sub("([a-z]+):", '"\\1" :', response)
            response = response.replace("<sup>","^(")
            response = response.replace("</sup>",")")
            response = response.replace("&#215;","x")
            response = json.loads(response)
            if not response['error']:
                result = "%s = %s" % (response['lhs'],response['rhs'])
                self.lastcalcresult = response['rhs']
        except Exception as inst: 
            print "!c " + term + " : " + str(inst)
            pass
        
        return result
    
    def google_sunrise(self, term):
        url = "http://www.google.com/search?hl=en&client=opera&hs=6At&rls=en&q=sunrise+in+%s&aq=f&aqi=g1&aql=&oq=&gs_rfai=" % term
        request = urllib2.Request(url, None, {})
        request.add_header('User-Agent', "Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.10")
        request.add_header('Range', "bytes=0-40960")
        response = urllib2.urlopen(request).read()

        m = re.search('(sunrise-40.gif.*?\<b\>)(.*?)(\<\/b\> )(.*?)( -\s*\<b\>)(.*?)(\<\/b\> in\s*)(.*?)(\s*?\<tr\>.*?top\"\>)(.*?)(\<\/table\>)', response)
        
        #print self.remove_html_tags(m.group(2))
        
        try:
          settime = m.group(2)
          setday = m.group(4)
          setday = re.sub("\s+"," ",setday)
          setword = m.group(6)
          setcity = m.group(8)
          settimeword = m.group(10)
          
          result = "Sunrise in %s: %s %s (%s)" % (setcity,settime,setday,settimeword)
       
          #print result
        except Exception as inst:
          print inst
          pass
          return
        result = result.replace("<sup>","^")
        result = result.replace("&#215;","x")
        return self.remove_html_tags(result)
        
    def google_sunset(self, term):
        url = "http://www.google.com/search?hl=en&client=opera&hs=6At&rls=en&q=sunset+in+%s&aq=f&aqi=g1&aql=&oq=&gs_rfai=" % term
        request = urllib2.Request(url, None, {})
        request.add_header('User-Agent', "Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.10")
        request.add_header('Range', "bytes=0-40960")
        response = urllib2.urlopen(request).read()

        m = re.search('(sunset-40.gif.*?\<b\>)(.*?)(\<\/b\> )(.*?)( - \<b\>)(.*?)(\<\/b\> in\s*)(.*?)(\s*?\<tr\>.*?top\"\>)(.*?)(\<\/table\>)', response)
        
        #print self.remove_html_tags(m.group(2))
        
        try:
          settime = m.group(2)
          setday = m.group(4)
          setday = re.sub("\s+"," ",setday)
          setword = m.group(6)
          setcity = m.group(8)
          settimeword = m.group(10)
          
          result = "Sunset in %s: %s %s (%s)" % (setcity,settime,setday,settimeword)
       
          #print result
        except:
          pass
          return
        result = result.replace("<sup>","^")
        result = result.replace("&#215;","x")
        return self.remove_html_tags(result)

    def advocate_beer(self, query):
        url = self.google_url("site:beeradvocate.com " + query, "/beer/profile/[0-9]*/")
        #url = "http://beeradvocate.com/beer/profile/306/1212/"
        socket.setdefaulttimeout(30)
        try:
          beerpage = urllib2.urlopen(url).read()#.decode("ISO-8859-1")
        except:
          return
        socket.setdefaulttimeout(10)
        
        titlestart = beerpage.find("<title>") + 7
        titleend = beerpage.find(" - ", titlestart)
        beertitle = beerpage[titlestart:titleend]
 
        score_start_tag = '<span class="BAscore_big">'
        score_end_tag = 'Reviews</td>'

        start = beerpage.find(score_start_tag) + len(score_start_tag)
        score_line = beerpage[start:start+50]

        find_start_tag = "</span>\n<br>"
        find_end_tag = "<br>"

        #print score_line

        grade = score_line[0:score_line.find(find_start_tag)]

        #print "\n" + grade
        grade_wording = score_line[score_line.find(find_start_tag)+len(find_start_tag):score_line.rfind(find_end_tag)]
        #print grade_wording


        find_start_tag = find_end_tag
        find_end_tag = "</td>"

        num_reviews = score_line[score_line.rfind(find_start_tag)+len(find_start_tag):score_line.find(find_end_tag)]

        #print num_reviews

        find_start_tag = "Style | ABV"
        style_line = beerpage[beerpage.find(find_start_tag):beerpage.find(find_start_tag)+120]

        find_start_tag = "><b>"
        find_end_tag = "</b></a> | &nbsp;"

        style = style_line[style_line.find(find_start_tag)+len(find_start_tag):style_line.find(find_end_tag)]

        find_start_tag = find_end_tag
        find_end_tag = "% <a href"

        abv = style_line[style_line.find(find_start_tag)+len(find_start_tag):style_line.find(find_end_tag)+1]
        response_string = "Beer: %s - Grade: %s [%s, %s] Style: %s ABV: %s [ %s ]" % (beertitle, grade, grade_wording, num_reviews, style, abv, self.shorten_url(url))
        
        return response_string
        
    def remove_html_tags(self,data):
      p = re.compile(r'<.*?>')
      return p.sub('', data)
   
    def google_url(self, searchterm, regexstring):
        try:
          url = ('http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=' + urllib.quote(searchterm))
          request = urllib2.Request(url, None, {'Referer': 'http://irc.00id.net'})
          response = urllib2.urlopen(request)

          results_json = json.load(response)
          results = results_json['responseData']['results']
        
          for result in results:
              m = re.search(regexstring,result['url'])   
              if (m):
                 url = result['url']
                 url = url.replace('%25','%')
                 return url
          return
        except:
          return

    def shorten_url(self, url):
      try:
        values =  json.dumps({'longUrl' : url})
        headers = {'Content-Type' : 'application/json'}
        requestUrl = "https://www.googleapis.com/urlshortener/v1/url"
        req = urllib2.Request (requestUrl, values, headers)
        response = urllib2.urlopen (req)
        results = json.load(response)
        shorturl = results['id']
        return shorturl
      except:
        return ""
    
    
    def get_weather2(self, zip):
        url = "http://api.wunderground.com/auto/wui/geo/WXCurrentObXML/index.xml?query=" + urllib.quote(zip)
        dom = xml.dom.minidom.parse(urllib2.urlopen(url))
        city = dom.getElementsByTagName('display_location')[0].getElementsByTagName('full')[0].childNodes[0].data
        if city != ", ":
            temp_f = dom.getElementsByTagName('temp_f')[0].childNodes[0].data
            temp_c = dom.getElementsByTagName('temp_c')[0].childNodes[0].data
            try:
                condition = dom.getElementsByTagName('weather')[0].childNodes[0].data
            except:
                condition = ""
            try:
                humidity = dom.getElementsByTagName('relative_humidity')[0].childNodes[0].data
            except:
                humidity = ""
            try:
                wind = dom.getElementsByTagName('wind_string')[0].childNodes[0].data
            except:
                humidity = ""
            
            degree_symbol = unichr(176)
            chanmsg = "%s / %s / %s%sF %s%sC / Humidity: %s / Wind: %s" % (city, condition, temp_f,degree_symbol, temp_c, degree_symbol, humidity, wind)
            chanmsg = chanmsg.encode('utf-8')
            return chanmsg

    def get_weather(self, zip):

     
       url = "http://www.google.com/ig/api?weather=" + urllib.quote(zip)
       dom = xml.dom.minidom.parse(urllib2.urlopen(url))
       
       city = dom.getElementsByTagName('city')[0].getAttribute('data')
       temp_f = dom.getElementsByTagName('current_conditions')[0].getElementsByTagName('temp_f')[0].getAttribute('data')
       temp_c = dom.getElementsByTagName('current_conditions')[0].getElementsByTagName('temp_c')[0].getAttribute('data')
       try:
        humidity = dom.getElementsByTagName('current_conditions')[0].getElementsByTagName('humidity')[0].getAttribute('data')
       except:
        humidity = ""
       
       try: 
        wind = dom.getElementsByTagName('current_conditions')[0].getElementsByTagName('wind_condition')[0].getAttribute('data')
       except:
        wind = "" 
        
       try:
        condition = dom.getElementsByTagName('current_conditions')[0].getElementsByTagName('condition')[0].getAttribute('data')
       except:
        condition = "" 
       
       degree_symbol = unichr(176)
       
       chanmsg = "%s / %s / %s%sF %s%sC / %s / %s" % (city, condition, temp_f,degree_symbol, temp_c, degree_symbol, humidity, wind)
       chanmsg = chanmsg.encode('utf-8')
       
       return chanmsg
      
    def get_wiki(self, searchterm, urlposted=False):
      title = ""
      
      if urlposted:
          url = searchterm
      else:
          url = self.google_url("site:wikipedia.org " + searchterm,"wikipedia.org/wiki")
          
      if not url:
          pass
      elif url.find("wikipedia.org/wiki/") != -1:

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

          title = self.remove_html_tags(re.search('(?s)\<p\>(.*?)\<\/p\>',page).group(1))
          title = title.encode("utf-8", 'ignore')
          title = title.replace("<","");
          rembracket = re.compile(r'\[.*?\]')
          title = rembracket.sub('',title)
          #title = re.sub("\&.*?\;", " ", title)
          title = title.replace("\n", " ")
          
          title = decode_htmlentities(title.decode("utf-8", 'ignore')).encode("utf-8", 'ignore')

          title = title[0:420]
          if title.rfind(".")!=-1:
            title = title[0:title.rfind(".")+1]
            
          if not urlposted:
            title = (title.decode('utf-8') + " [ %s ]" % self.shorten_url(url)).encode('utf-8', 'ignore')
        except Exception as inst: 
          print "!wiki " + searchterm + " : " + str(inst)
          title = self.remove_html_tags(re.search('\<p\>(.*?\.) ',page).group(1))

      return title 
  
    def get_stock_quote(self, stock):
    # For the f argument in the url here are the values:
    #     code   description                
    #                                       
    #     l1     price                      
    #     c1     change                     
    #     v      volume                     
    #     a2     avg_daily_volume           
    #     x      stock_exchange             
    #     j1     market_cap                 
    #     b4     book_value                 
    #     j4     ebitda                     
    #     d      dividend_per_share         
    #     y      dividend_yield             
    #     e      earnings_per_share         
    #     k      52_week_high               
    #     j      52_week_low                
    #     m3     50day_moving_avg           
    #     m4     200day_moving_avg          
    #     r      price_earnings_ratio       
    #     r5     price_earnings_growth_ratio
    #     p5     price_sales_ratio          
    #     p6     price_book_ratio           
    #     s7     short_ratio  
    
      opener = urllib2.build_opener()
      opener.addheaders = [('User-Agent',"Opera/9.10 (YourMom 8.0)")]
      pagetmp = opener.open("http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=nl1c1va2j1" % stock)
      quote = pagetmp.read(1024)
      opener.close()
    
      name,price,change,volume,avg_volume,mkt_cap = quote.split(",")
      if price != "0.00": #assume no price = no result
         name = name.replace('"','')
      
         if change != "N/A":
             change = change + ' ({0:.2%})'.format((float(change)/(float(price) - float(change))))
         if volume != "N/A":
             volume = '{0:n}'.format(int(volume))
             avg_volume = '{0:n}'.format(int(avg_volume))
         
         return "[%s] %s    %s %s | Cap: %s | Volume (Avg): %s (%s)" % (stock,name.strip(),price,change,mkt_cap.strip(),volume,avg_volume)

    def get_imdb(self, searchterm, urlposted=False):
        title = ""
        movietitle = ""
        rating = ""
        summary = ""
        
        if urlposted:
            url = searchterm
        else:
            url = self.google_url("site:imdb.com/title " + searchterm,"imdb.com/title/tt\\d{7}/")
      
        if not url:
          pass
        elif url.find("imdb.com/title/tt") != -1:
          try:
            imdbid = re.search("tt\\d{7}", url)
            imdburl = ('http://www.imdb.com/title/' + imdbid.group(0) + '/')
            opener = urllib2.build_opener()
            opener.addheaders = [('User-Agent',"Opera/9.10 (YourMom 8.0)"),
                                 ('Range', "bytes=0-40960")]
            pagetmp = opener.open(imdburl)
            page = BeautifulSoup(pagetmp.read(40960))
            opener.close()
            
            movietitle = decode_htmlentities(self.remove_html_tags(str(page.find('title'))).replace(" - IMDb", ""))
            movietitle = "Title: " + movietitle

            
            if page.find(id="overview-top") != None:
                page = page.find(id="overview-top").extract()
                
                if page.find(id="star-bar-user-rate") != None:
                    rating = self.remove_html_tags(str(page.find(id="star-bar-user-rate").b))
                    rating = " - Rating: " + rating
                
                if len(page.findAll('p')) == 2:

                    summary = str(page.findAll('p')[1])
            
                    removelink = re.compile(r'\<a.*\/a\>')
                    summary = removelink.sub('',summary)
                    summary = self.remove_html_tags(summary)
                    summary = summary.replace('&raquo;', "")
                    summary = decode_htmlentities(summary.decode("utf-8", 'ignore'))
                    summary = re.sub("\&.*?\;", " ", summary)
                    summary = summary.replace("\n", " ")
                    summary = " - " + summary
                    
            title = movietitle + rating + summary       
            if not urlposted:
                title = title + " [ %s ]" % url
          except Exception as inst: 
            print "!imdb " + searchterm + ": " + str(inst)
            
#        IMDBAPI CODE
#        -not in use because it's unreliable
#           try:
#              imdbid = re.search("tt\\d{7}", url)
#              imdburl = ('http://www.imdbapi.com/?i=&t=' + imdbid.group(0))
#              request = urllib2.Request(imdburl, None, {'Referer': ''})
#              response = urllib2.urlopen(request)
#              results = json.load(response)
#              title = "Title: " + results['Title'] + " (" + results['Year'] + ") - Rating: " + results['Rating'] + " - " + results['Plot']
#              response.close()
#              title = title.encode('utf-8')
#
#           except:
#              pass
         
        return title.encode('utf-8', 'ignore')
    
    def get_title(self, url):
        title = ""
        try:
            opener = urllib2.build_opener()
            readlength = 10240
            if url.find("amazon.") != -1: 
                readlength = 100096 #because amazon is coded like shit
                
            opener.addheaders = [('User-Agent',"Opera/9.10 (YourMom 8.0)"),    
                                 ('Range',"bytes=0-" + str(readlength))]

            pagetmp = opener.open(url)
            

                
            page = pagetmp.read(readlength)
            opener.close()

            start = page.find("<title>") + 7
        
            if start < 7:
                start = page.find("<TITLE>") + 7
        
            if start < 7:
                return title
        
            end = page.find("</title>") 
        
            if end == -1:
                end = page.find("</TITLE>")
          
            if end == -1:
                return title
        
            titletmp = page[start:end]
            title = "Title: " + titletmp.strip()[0:180]
        except:
            pass
            
        return title
    
    def url_posted(self, url):

      try:

        repost=""
        days = ""        
        
        if self.sqlmode > 0:
            urlhash = hashlib.sha224(url).hexdigest()
    
            conn = MySQLdb.connect (host = "localhost",
                                      user = self.sqlusername,
                                      passwd = self.sqlpassword,
                                      db = "irc_links")   
            cursor = conn.cursor()
            query = "SELECT reposted, timestamp FROM links WHERE hash='%s'" % urlhash
            result = cursor.execute(query)
            
            if result !=0:
                result = cursor.fetchone()
                
                repost="LOL REPOST %s " % (result[0] + 1)
            
                orig = result[1]
                now = datetime.datetime.now()
                delta = now - orig
                         
                plural = ""
                if delta.days > 0:
                  if delta.days > 1:
                    plural = "s"
                  days = " (posted %s day%s ago)" % (str(delta.days), plural)
                else:
                  hrs = int(round(delta.seconds/3600.0,0))
                  if hrs == 0:
                    mins = delta.seconds/60
                    if mins > 1:
                      plural = "s"
                    days = " (posted %s minute%s ago)" % (str(mins), plural)
                    if mins == 0:
                        repost=""
                        days=""
                  else:
                    if hrs > 1:
                      plural = "s"
                    days = " (posted %s hour%s ago)" % (str(hrs), plural)
                
        
        
        title = ""        
        wiki = self.get_wiki(url, True)
        imdb = self.get_imdb(url, True)
        if wiki:
            title = wiki
        elif imdb:
            title = imdb
        else:
            if url.find("imgur.com") != -1:
              imgurid =  url[url.rfind('/')+1:url.rfind('/')+6]
              url = "http://imgur.com/" + imgurid
            title = self.get_title(url)
            if title.find("imgur: the simple") != -1:
              title = ""

        title = title.replace("\n", " ")
        pattern = re.compile('whatsisname', re.IGNORECASE)
        title = pattern.sub('', title)      
        title = decode_htmlentities(title.decode("utf-8", 'ignore')).encode("utf-8", 'ignore')

        titler = "%s%s%s" % (repost, title, days)
        
        if self.sqlmode == 2:
            title = MySQLdb.escape_string(title)
            url = MySQLdb.escape_string(url)
            query = "INSERT INTO links (url, title, hash) VALUES ('%s','%s','%s') ON DUPLICATE KEY UPDATE reposted=reposted+1,title='%s'" % (url, title, urlhash, title)       
            cursor.execute(query)
        if self.sqlmode > 0:
            conn.close()
        
        return titler

      
      except Exception as inst: 
        print url + ": " + str(inst)
        pass
      return
      
    def last_link(self, nothing):
     if self.sqlmode > 0:
          conn = MySQLdb.connect (host = "localhost",
                                    user = self.sqlusername,
                                    passwd = self.sqlpassword,
                                    db = "irc_links")
                                    
          cursor = conn.cursor()
          if (cursor.execute("SELECT url FROM links ORDER BY id DESC LIMIT 1")):
            result = cursor.fetchone()
            url = result[0]
    
          conn.close()
          return "Title: " + self.get_title(url) + " [ " + url + " ]"
     else:
        return ""
        
    def get_fml(self, nothing):
        
      try:
        fmlxml = urllib2.urlopen("http://api.betacie.com/view/random?key=%s&language=en" % self.fmlAPIkey).read()
        start = fmlxml.find("<text>") + 6
        end = fmlxml.find("</text>")
        
        fml = fmlxml[start:end]
        
        start = fmlxml.find("<agree>") + 7
        end = fmlxml.find("</agree>")
        
        fml = fml + " [FYL: " + str(fmlxml[start:end])
        
        start = fmlxml.find("<deserved>") + 10
        end = fmlxml.find("</deserved>")   
        
        fml = fml + " Deserved it: " + str(fmlxml[start:end]) + "]"
        
        
        fml = fml.replace('&quot;', '"')
        fml = fml.replace('&amp;quot;', '"')
        fml = fml.replace('&amp;', "&")
        fml = decode_htmlentities(fml)
        
        return fml
      except:
        pass
        return

def decode_htmlentities(string):
    entity_re = re.compile("&(#?)(x?)(\w+);")
    return entity_re.subn(substitute_entity, string)[0]

def substitute_entity(match):
  try:
    ent = match.group(3)
    
    if match.group(1) == "#":
        if match.group(2) == '':
            return unichr(int(ent))
        elif match.group(2) == 'x':
            return unichr(int('0x'+ent, 16))
    else:
        cp = n2cp.get(ent)

        if cp:
            return unichr(cp)
        else:
            return match.group()
  except:
      return ""
                      
def main():
    #print sys.argv
    if len(sys.argv) != 4:
        print "Usage: testbot <server[:port]> <channel> <nickname>"
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print "Error: Erroneous port."
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = TestBot(channel, nickname, server, port)
    bot.start()

if __name__ == "__main__":
    main()
    
    
