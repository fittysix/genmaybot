# -*- coding: utf-8 *-*
import re
import random
import time
import threading
import sqlite3


def wotd_trigger(self, e):
    #reset the wotd if it hasn't beeen found in over 24 hours
    if (time.time() - wotd_trigger.wotd_found_timestamp) > (3600 * 24):
        wotd_trigger.wotd = common_words[random.randint(0, len(common_words) - 1)]
        wotd_trigger.wotd_setter = ""
        wotd_trigger.wotd_finder = ""
        wotd_trigger.found = 0
        wotd_trigger.wotd_found_timestamp = time.time()
    if re.search(wotd_trigger.wotd, e.input, re.I) and re.search(" ", e.input) and e.source != e.nick and e.nick != "Whatsisname":
        do_wotd(self, e)
    else:
        return
wotd_trigger.lineparser = False
wotd_trigger.wotd = "cat"
wotd_trigger.wotd_found_timestamp = 0
wotd_trigger.wotd_setter = ""
wotd_trigger.wotd_finder = ""
wotd_trigger.found = 0


def __init__(self):
    conn = sqlite3.connect("wotd.sqlite")
    c = conn.cursor()
    result = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wotd_settings';").fetchone()
    if not result:
        c.execute('''CREATE TABLE 'wotd_settings' ("wotd" TEXT, "setter" TEXT, "finder" TEXT, "found" int, "timestamp" int);''')
        c.execute('''CREATE TABLE 'wotd_bans' ("nick" TEXT, "hostmask" TEXT, "channel" TEXT, "ban_time" int);''')
        wotd_trigger.wotd_found_timestamp = time.time()
        update_wotd_settings(c)
    else:
        wotd, setter, finder, found, timestamp = c.execute("SELECT * FROM wotd_settings where rowid=1").fetchone()
        wotd_trigger.wotd = wotd
        wotd_trigger.wotd_setter = setter
        wotd_trigger.wotd_finder = finder
        wotd_trigger.found = found
        wotd_trigger.wotd_found_timestamp = timestamp
    conn.commit()

    #Check if there are any active bans when we loaded - if so try to unban them in case the bot was killed while they were banned
    for ban in c.execute("SELECT * FROM wotd_bans;"):
        if time.time() - ban[3] < 60:
            unbantime = int(60 - (time.time() - ban[3]))
            threading.Timer(unbantime, unban_user, [self, ban[0], ban[1], ban[2]]).start()
        else:
            unban_user(self, ban[0], ban[1], ban[2])

    conn.close()


def update_wotd_settings(c):
    c.execute("DELETE FROM 'wotd_settings' WHERE rowid=1")
    c.execute("INSERT INTO 'wotd_settings' VALUES (?, ?, ?, ?, ?)", (wotd_trigger.wotd, wotd_trigger.wotd_setter,
                                                                     wotd_trigger.wotd_finder, wotd_trigger.found,
                                                                     wotd_trigger.wotd_found_timestamp))


def new_wotd(self, e):
    if e.hostmask == wotd_trigger.wotd_finder:
        newwotd = e.input.strip()
        if len(newwotd.split()) != 1:
            e.output = "The command usage is: !newwotd <word>"
        elif len(newwotd) < 3:
            e.output = "The word must be at least 3 letters long."
        elif newwotd in common_words:
            e.output = "Please use a different, less common word."
        else:  # Word is successfully set
            wotd_trigger.wotd = newwotd
            wotd_trigger.wotd_setter = e.nick
            wotd_trigger.found = 0
            e.output = "The word has been set to: {}\nYou can set it again with !newwotd <word> until someone finds it\nIf the word is not found in 24 hours it will be reset".format(newwotd)

            conn = sqlite3.connect("wotd.sqlite")
            c = conn.cursor()
            update_wotd_settings(c)
            conn.commit()
            conn.close()
    else:
        if wotd_trigger.wotd_finder:
            e.output = "Someone else already found the word, sorry."
        else:
            e.output = "You have to find the word of the day if you want to change it."

    return e
new_wotd.command = "!newwotd"
new_wotd.privateonly = True
new_wotd.helptext = "Use this command in a PM to the bot to set a new word of the day when you find it."


common_words = ["the", "people", "would", "really", "think", "right", "there", "about", "were", "when", "your", "can",
                "which", "each", "other", "them", "then", "into", "him", "write", "more", "their", "make", "word", "some",
                "many", "time", "look", "see", "who", "may", "down", "get", "day", "come", "part", "like", "now", "these",
                "other", "said", "could", "she"]


def do_wotd(self, e):
    #If the word was found over 10 minutes ago but a new one wasn't set, allow the new person who got it to set it.
    if time.time() - wotd_trigger.wotd_found_timestamp > 600 and wotd_trigger.found:
        wotd_trigger.found = 0
    if not wotd_trigger.found:
        wotd_trigger.wotd_finder = e.hostmask
        wotd_trigger.wotd_found_timestamp = time.time()
        wotd_trigger.found = 1
        self.irccontext.privmsg(e.nick, "You can set a new word of the day with the command !newwotd <word>  You have 10 minutes to change the word")
    ban_user(self, e)
    conn = sqlite3.connect("wotd.sqlite")
    c = conn.cursor()
    c.execute("INSERT INTO 'wotd_bans' VALUES (?, ?, ?, ?)", (e.nick, e.hostmask, e.source, time.time()))
    update_wotd_settings(c)
    conn.commit()
    conn.close()


def ban_user(self, e):
    self.irccontext.privmsg("Angstserv", "deprotect {} {}".format(e.source, e.nick))
    self.irccontext.privmsg("Angstserv", "ACCESS {} add {} -1".format(e.source, e.nick))
    time.sleep(1)
    self.irccontext.mode(e.source, '+b {}'.format(e.hostmask))
    self.irccontext.kick(e.source, e.nick, "Congratulations! You found the word of the day, courtesy of {}!".format(wotd_trigger.wotd_setter or self.irccontext.get_nickname()))
    threading.Timer(60, unban_user, [self, e.nick, e.hostmask, e.source]).start()

def unban_user(self, nick, hostmask, channel):
    self.irccontext.mode(channel, '-b {}'.format(hostmask))
    self.irccontext.privmsg("Angstserv", "ACCESS {} add {} 5".format(channel, nick))
    self.irccontext.invite(nick, channel)

    conn = sqlite3.connect("wotd.sqlite")
    c = conn.cursor()
    c.execute("DELETE FROM 'wotd_bans' WHERE nick = ? and channel = ?", (nick, channel))
    conn.commit()
    conn.close()
