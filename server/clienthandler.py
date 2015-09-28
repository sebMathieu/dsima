##@package clienthandler
#@author Sebastien MATHIEU

import asyncio,websockets
from .client import Client

## Subclass of the protocol to obtain the ip adress of the client
class IPGetterProtocol(websockets.WebSocketServerProtocol):
    def connection_made(self, transport):
        super().connection_made(transport)
        self.remoteIP = transport.get_extra_info('peername')[0]

# Client handler routine
@asyncio.coroutine
def clientHandler(websocket, path):
	client=Client(websocket)
	yield from client.interact()
