def do_kick(self, e):
    self.irccontext.kick("#auzland", e.nick, "thank you for participating in this test (by %s)" % e.nick)
do_kick.command = "!kick"
