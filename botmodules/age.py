# 9/11/2012 Nevar Forget
import time
def age(self, e):
    self.irccontext.privmsg("Angstserv", "deprotect {} {}".format(e.source, e.nick))
    time.sleep(1)
    self.irccontext.mode(e.source, '+b {}'.format(e.hostmask))
    self.irccontext.kick(e.source, e.nick, "Congratulations! You found the word of the day, courtesy of !age!")
age.command = "!age"