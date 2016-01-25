from calvin.actor.actor import Actor, ActionResult, manage, condition, guard

class WebsocketActor(Actor):
    """
    Receives data from Websockets
    Outputs:
        message: String
    """
    @manage(['port'])
    def init(self, port = 9000):
        self.use("calvinsys.network.websockethandler", shorthand='websocket')
        self.port = port
        self['websocket'].start("localhost", port)
    
    @condition(action_output=['message'])
    @guard(lambda self: len(self['websocket'].unread_messages) != 0)
    def message_received(self):
        messages="\n".join(self['websocket'].unread_messages)
        self['websocket'].unread_messages=[]
        return ActionResult(production=("\n".join(messages),))

    action_priority = (message_received,)