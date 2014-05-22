# Coded by Bobng/Nigg/Lobe/etc
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import _thread
import json as sjson
import http.cookiejar
import time
import traceback
user_agent = "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3"


class EventHandler:
    def fire(self,event,chat,var):
        ''' Callback class. Var is info relating to the event '''
        if hasattr(self,event):
            getattr(self,event)(chat,var)

class OmegleChat:
    def __init__(self,_id=None,debug=True):
        self.url = "http://omegle.com/"
        self.id = _id
        self.failed = False
        self.connected = False
        self.in_chat = False
        self.handlers = []
        self.terminated = False

        self.debug = debug
        
        jar = http.cookiejar.CookieJar()
        processor = urllib.request.HTTPCookieProcessor(jar)
        self.connector = urllib.request.build_opener(processor)#,urllib2.HTTPHandler(debuglevel=1))
        self.connector.addheaders = [
            ('User-agent',user_agent)
            ]

    def pausedChat(self,chat,message,pause):
        ''' Make it look like the bot is typing something '''
        self.typing()
        time.sleep(pause)
        self.stoppedTyping()
        self.say(message)

    def get_events(self,json=False):
        ''' Poll the /events/ page and process the response '''
        #requester = urllib2.Request(self.url+'events',headers={'id':self.id}
        data = urllib.parse.urlencode({'id':self.id}).encode()
        try:
            events = self.connector.open(self.url+'events',data, 120).read().decode()
        except:
            ''' An exception here means the connection timed out so we can pretend they disconnected '''
            print("omegle timeout")
            events = "[['strangerDisconnected']]"
        if json:
            return sjson.loads(events)
        else:
            return events

    def connect_events(self, event_handler):
        ''' Add an event handler '''
        self.handlers.append(event_handler)

    def fire(self,event,var):
        for handler in self.handlers:
            handler.fire(event,self,var)

    def terminate(self):
        ''' Terminate the thread. Don't call directly, use .disconnect() instead '''
        self.terminated = True

    def open_page(self,page,data={}):
     try:
        if self.terminated:
            return
        
        if not 'id' in data:
            data['id'] = self.id
        r = self.connector.open(self.url+page,urllib.parse.urlencode(data).encode()).read().decode()
        if not r == "win":
            # Maybe make it except here?
            if self.debug: print('Page %s returned %s'%(page,r))
        return r
     except:
        traceback.print_exc()

    def say(self,message):
        ''' Send a message from the chat '''
        if self.debug: print('Saying message: %s'%message)
        self.open_page('send',{'msg':message})

    def disconnect(self):
        ''' Close the chat '''
        self.open_page('disconnect',{})
        self.terminate()

    def typing(self):
        ''' Tell the stranger we are typing '''
        self.open_page('typing')

    def stoppedTyping(self):
        ''' Tell the stranger we are no longer typing '''
        self.open_page('stoppedtyping')

    def connect(self,threaded=True):
        ''' Start a chat session'''
        if not self.id:
            data = urllib.parse.urlencode({}).encode()
            self.id = self.connector.open(self.url+'start',data).read().decode().strip('"')
            print(self.id)
        self.connected = True
        if threaded:
            _thread.start_new_thread(self.reactor,())
        else:
            self.reactor()

    def waitForTerminate(self):
        ''' This only returns when .disconnect() or .terminate() is called '''
        while not self.terminated:
            time.sleep(0.1)
            pass
        return

    def reactor(self):
      try:
        while True:
            if self.terminated:
                if self.debug: print("Thread terminating")
                return

            events = self.get_events(json=True)
            if not events:
                print("maybe")
                continue
            if self.debug: print(events)
            for event in events:
                if len(event) > 1:
                    self.fire(event[0],event[1:])
                else:
                    self.fire(event[0],None)
      except:
        traceback.print_exc()
if __name__=='__main__':

    class MyEventHandler(EventHandler):
        def connected(self,chat,var):
            print("Connected")
            chat.in_chat = True
            chat.say("Hello!")

        def gotMessage(self,chat,message):
            message = message[0]
            print("Message recieved: "+message)          

        def typing(self,chat,var):
            print("Stranger is typing...")

        def stoppedTyping(self,chat,var):
            print("Stranger stopped typing!")

        def strangerDisconnected(self,chat,var):
            print("Stranger disconnected - Terminating")
            chat.terminate()
            
    for i in range(2):
        print("Starting chat %s"%i)
        a = OmegleChat()
        a.connect_events(MyEventHandler())
        a.connect(True)
        a.waitForTerminate()
    input()
