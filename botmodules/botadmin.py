import time, sys, traceback
import threading

#test commit
def manual_spamban(line, nick, self, c):
    if len(line.split(" ")) == 3:
        user = line.split(" ")[1]
        bantime = line.split(" ")[2]
        self.spam[user] = {}
        self.spam[user]['count'] = 2
        self.spam[user]['last'] = time.time()
        self.spam[user]['first'] = time.time()
        self.spam[user]['limit'] = bantime
manual_spamban.admincommand = "spamban"

def kill_bot(line, nick, self, c):
    print("got die command from " + nick)
    message = ""
    if line[4:]:
        message = line[4:]
    c.disconnect(message)
    self.t.cancel()
    sys.exit(0)
kill_bot.admincommand = "die"

def nick(line, nick, self, c):
    print(line)
    print(line[5:])
    c.nick(line[5:])
nick.admincommand = "nick"

def clear_bans(line, nick, self, c):
    print(nick + " cleared bans")
    self.spam ={}
    return "All bans cleared"
clear_bans.admincommand = "clearbans"

def reload_modules(line, nick, self, c):
    return self.loadmodules()
reload_modules.admincommand = "reload"


def reload_config(line, nick, self, c):
    return self.load_config()
reload_config.admincommand = "reconfig"


def enable_command(line, nick, self, c):
    if len(line.split(" ")) == 2:
        command = line.split(" ")[1]
        if command in self.commandaccesslist:
            del self.commandaccesslist[command]
            return command + " Enabled"
        else:
            return command + " not disabled"
enable_command.admincommand = "enable"

def disable_command(line, nick, self, c):
    if len(line.split(" ")) == 2:
        command = line.split(" ")[1]
        self.commandaccesslist[command] = "Disabled"
        return command + " Disabled"
disable_command.admincommand = "disable"

def disable_alert(line,nick,self,c):
	if len(line.split(" ")) == 2:
		disable_alert = line.split(" ")[1]
		for alert in self.botalerts:
			if alert.__name__ == disable_alert:
				alert.alert = False
				return disable_alert + " disabled"
disable_alert.admincommand = "disable_alert"

def enable_alert(line,nick,self,c):
	if len(line.split(" ")) == 2:
		enable_alert = line.split(" ")[1]
		for alert in self.botalerts:
			if alert.__name__ == enable_alert:
				alert.alert = True
				return disable_alert + " enabled"
enable_alert.admincommand = "enable_alert"


def cooldown_command(line, nick, self, c):
    if len(line.split(" ")) == 3:
        command = line.split(" ")[1]
        cooldown = line.split(" ")[2]
        if cooldown.isdigit():
            cooldown = int(cooldown)
            if cooldown == 0:
                if command in self.commandaccesslist:
                    del self.commandaccesslist[command]
                return command + " cooldown disabled"
            else:
                self.commandaccesslist[command] = cooldown
                self.commandcooldownlast[command] = time.time() - cooldown
                return command + " cooldown set to " + str(cooldown) + " seconds (set to 0 to disable)"
        else:
            return "bad format: 'cooldown !wiki 30' (30 second cooldown on !wiki)"
    else:
        return "not enough perameters: cooldown !command ##"
cooldown_command.admincommand = "cooldown"

def command_status(line, nick, self, c):
    if len(line.split(" ")) == 2:
        command = line.split(" ")[1]
        if command in self.commandaccesslist:
            return command + " " + str(self.commandaccesslist[command]) + " (Seconds cooldown if it's a number)"
        else:
            return command + " Enabled"
    elif len(line.split(" ")) == 1:
        return str(list(self.commandaccesslist.items()))

command_status.admincommand = "status"

def join_chan(line, nick, self, c):
    if len(line.split(" ")) == 2:
        chan = line.split(" ")[1]
        if chan[0:1] != "#":
            return "not a valid channel name"
        if chan in self.channels:
            return "Already in " + chan
        else:
            c.join(chan)
            return "Joined " + chan
join_chan.admincommand = "join"

def part_chan(line, nick, self, c):
    if len(line.split(" ")) >= 2:
        chan = line.split(" ")[1]
        message = ""
        if len(line.split(" ")) > 2:
            message = " ".join(line.split(" ")[2:])
        if chan[0:1] != "#":
            return "not a valid channel name: Part #chan part message here"
        if chan in self.channels:
            c.part(chan, message)
            return "Left " + chan
        else:
            return "Not in " + chan
part_chan.admincommand = "part"

def say_cmd(line, nick, self, c):
	if len(line.split(" ")) > 2:
		chan = line.split(" ")[1]
		words = " ".join(line.split(" ")[2:])
		c.privmsg(chan, words)
		return "Said %s to %s" % (words, chan)
	else:
		return "Correct syntax: say [#channel/nickname] I hate you!"
say_cmd.admincommand="say"

def show_channels(line, nck, self, c):
    return ", ".join(self.channels)
show_channels.admincommand = "channels"

def quake_filter(line, nick, self, c):
    for alert in self.botalerts:
        if alert.__name__ == "quake_alert":
            if len(line.split(" ")) >= 2:
                try:
                     alert.filter = " ".join(line.split(" ")[1:])
                     return "Earthquake alerts containing '%s' will not be shown." % " ".join(line.split(" ")[1:])
                except:
                    traceback.print_exc()
                    return "Quake module doesn't seem to be loaded."
            else:
                return "Correct syntax: quake-filter [title string]   For example: quake-filter Honshu -> this will disable any quake alerts containing the word Honshu"
quake_filter.admincommand = "quake-filter"


def debug_listthreads(line, nick, self, c):
    print(threading.enumerate())
    return "A list of threads has been printed in the event log"
debug_listthreads.admincommand = "listthreads"
