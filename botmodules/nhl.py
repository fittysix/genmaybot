import datetime, urllib.request
import xml.etree.ElementTree as ET

def get_nhl_live_games(self, e, webCall=False):
    url = "http://feeds.cdnak.neulion.com/fs/nhl/mobile/feeds/data/%s.xml" % (datetime.date.today().strftime("%Y%m%d"))
    games = ET.parse(urllib.request.urlopen(url)).getroot().getchildren()
    
    gamestext = "" 
    
    for game in games:
        gametext = ""
        try:
            awayteam = game.findtext('away-team/name')
            hometeam = game.findtext('home-team/name')
            
            state = game.findtext('game-state')
            
            if state == "LIVE":       
                progress = game.findtext('progress-time')
            elif state =="": #If the game hasn't started yet, get and show the start time
                starttime = game.findtext('eastern-start-time')
                if datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S").minute == 0:
                    starttime = datetime.datetime.strftime(datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S"), "Starts %-I %p Eastern")
                else:
                    starttime = datetime.datetime.strftime(datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S"), "Starts %-I:%M %p Eastern")
                gametext = "%s - %s (%s)" % (awayteam, hometeam, starttime)
                if gametext != "":
                    gamestext += gametext + " | " 
                continue
            else:
                progress = state

            scoreaway = game.findtext('away-team/goals')
            scorehome = game.findtext('home-team/goals')
            
            gametext = "%s %s - %s %s (%s)" % (awayteam, scoreaway, scorehome, hometeam, progress)
            if gametext != "":
                gamestext += gametext + " | " 
        except:
            pass


    gamestext = gamestext[0:-3]
    
    if webCall:
        return gamestext
    
    e.output = gamestext
    return e

get_nhl_live_games.command = "!nhl"
get_nhl_live_games.helptext = "Usage: !nhl Shows today's hockey games and current scores"
get_nhl_live_games.webExposed = True 

def get_nhl_live_streams(self, e, webCall=False):
    url = "http://feeds.cdnak.neulion.com/fs/nhl/mobile/feeds/data/%s.xml" % (datetime.date.today().strftime("%Y%m%d"))
    games = ET.parse(urllib.request.urlopen(url)).getroot().getchildren()

    streamstext = "" 
        
    for game in games:
        streamtext = ""
        gametext = ""
        try:
            awayteam = game.findtext('away-team/name')
            hometeam = game.findtext('home-team/name')
            awaystream = game.findtext('streams/sony_ced/away/live').replace("ced","4500")

            
            state = game.findtext('game-state')
            
            if state == "LIVE":       
                progress = game.findtext('progress-time')
            elif awaystream=="":
                continue
            else:
                starttime = game.findtext('eastern-start-time')
                if datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S").minute == 0:
                    progress = datetime.datetime.strftime(datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S"), "Starts %-I %p Eastern")
                else:
                    progress = datetime.datetime.strftime(datetime.datetime.strptime(starttime,"%m/%d/%Y %H:%M:%S"), "Starts %-I:%M %p Eastern")
                

            scoreaway = game.findtext('away-team/goals')
            scorehome = game.findtext('home-team/goals')
            gametext = "%s %s - %s %s (%s)" % (awayteam, scoreaway, scorehome, hometeam, progress)
            homestream = game.findtext('streams/sony_ced/home/live').replace("ced","4500")

            awayradio = game.findtext('streams/iphone/away/radio')
            homeradio = game.findtext('streams/iphone/home/radio')
            
            if webCall:
                streamtext = "<a href='%s'>%s stream</a><br /> <a href='%s'>%s stream</a><br /><a href='%s'>%s radio</a><br /><a href='%s'>%s radio</a>" % (awaystream,awayteam, homestream, hometeam, awayradio, awayteam, homeradio, hometeam)
            else:
                streamtext = "%s stream: %s\n%s stream: %s\n%s radio: %s\n%s radio: %s" % (awayteam, awaystream, hometeam, homestream, awayteam, awayradio, hometeam, homeradio)
        except:
            pass
        streamstext += "%s\n%s\n---------\n" % (gametext, streamtext)    
        streamstext = streamstext[0:-10]
    
    if streamstext.find("http") == -1:
        streamstext = "There are no games being played. Check today's games with !nhl"

    if webCall:
        return streamstext.replace("\n","<br />")

    e.source = e.nick
    e.notice = True
    e.output = streamstext
    return e    
        
get_nhl_live_streams.command = "!nhl-vid"
get_nhl_live_streams.helptext = "Usage: !nhl-vid Shows today's hockey game live video and audio stream URLs"            
get_nhl_live_streams.webExposed = True            
            