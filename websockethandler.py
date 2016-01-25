from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor
from twisted.internet.protocol import Factory

#protokol => kapcsolatonkent peldanyositva
#buffereli a bejovo adatokat
class MyWebsocketProtocol(WebSocketServerProtocol):
    def __init__(self,*args):
        super(WebSocketServerProtocol, self).__init__(*args)
        self.buff=""
        #ez alapjan tortenik a frissites
        self.data_available=False

    def onMessage(self, payload, isBinary):
       message=payload.decode("utf8")
       print "message: "+message
       #bennemaradt a buffereles, de nincs kihasznalva
       self.buff=self.buff+payload.decode("utf8")
       self.data_available=True
       self.handler.unread_messages.append(message)
       self.factory.trigger()
    
    #uriti a buffert
    def data_get(self):
        self.data_available=False
        original=self.buff
        self.buff=""
        return original
    
    def onConnect(self, request):
        print "incoming connection"
    
    def onClose(self, wasClean, code, reason):
        print "closing connection"
        self.factory.trigger()

#kapcsolatra ez peldanyosit protokolt
#a trigger nem erinti, csak vakon atadja az actor scheduler-et
#a trigger egy fg pointer
class WebsocketProtocolFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(WebSocketServerFactory, self).__init__(*args, **kwargs)
        self._port=None #ezen fut a reaktor

    def start(self, host, port):
        print "listen"
        self._port=reactor.listenTCP(port, self)
    
    def stop(self):
        self._port.close()
    
    def buildProtocol(self, addr, *args, **kwargs):
        connection=super(WebsocketProtocolFactory, self).buildProtocol(addr, *args, **kwargs)
        connection.factory=self
        connection.trigger=self.trigger
        connection.actor_id=self.actor_id
        connection.handler=self.handler
        return connection
    
    def trigger(self):
        self._trigger(actor_ids=[self.actor_id])

#elinditja a factory-t, hogy lehessen hivasokat fogadni
#a triggert a node-bol adja at fg pointerkent
class WebsocketServer(object):
    def __init__(self, node, actor_id, handler):
        self._trigger=node.sched.trigger_loop
        self.unread_messages=[]
        self.connection_factory=WebsocketProtocolFactory()
        self.connection_factory.protocol=MyWebsocketProtocol
        #sajat adattagok innen, mert nekehezen lehet ebbol orokoltetni
        self.connection_factory.trigger=node.sched.trigger_loop
        self.connection_factory.actor_id=actor_id
        self.connection_factory.handler=handler
        
    def start(self, host, port):
        self.connection_factory.start(host, port)

    def stop(self):
        self.connection_factory.stop()

    def trigger(self, actor_ids):
        self._trigger(actor_ids=actor_ids)

    def receive(self, connection):
        return connection.data_get()

#ezt huzza be az actor a use-zal
class WebsocketHandler(object):
    def __init__(self, node, actor):
        self.node=node
        self.server=None
        self._actor=actor
        self.unread_messages=[]
        #node.sched.trigger_loop(actor_ids=[actor.id])
    
    def start(self, host, port):
        self.server=WebsocketServer(self.node, self._actor.id, self)
        self.server.start('localhost', port)

def register(node, actor):
    print "register"
    return WebsocketHandler(node, actor)
