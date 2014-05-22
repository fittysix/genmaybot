from botmodules.chatterbotapi import ChatterBotFactory, ChatterBotType
import re


def chatter(self, e):
    botnick = e.botnick.lower()

    if e.input.lower().find(botnick) != -1:
        if e.input[0:len(botnick)].lower() == botnick:
            e.input = e.input[len(botnick):].strip()
        e.input = re.sub("(?i)%s" % botnick, "cleverbot", e.input)
        factory = ChatterBotFactory()

        bot1 = factory.create(ChatterBotType.CLEVERBOT)
        bot1session = bot1.create_session()

        e.output = bot1session.think(e.input)
        e.output = self.tools['decode_htmlentities'](re.sub("(?i)cleverbot", botnick, e.output))
        return e
    else:
        return None

chatter.lineparser = True


