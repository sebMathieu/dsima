#!/usr/bin/env python3

import asyncio # pip install asyncio (or pip3)
import websockets # pip install websockets (or pip3)
import sys,socket, threading

from server.clienthandler import clientHandler,IPGetterProtocol
from server.log import log
from server.isinterface import compute as simulationCompute

## Server location.
host='localhost'
## Server port.
port=8000

## Display the help of the server.
def displayHelp():
	print("python server.py [host port]\n\tStart a local server at address ws://%s:%s/." % (host, port))
	print("python server.py -d\n\tStart a server at address ws://%s:%s/." % (socket.gethostbyname(socket.gethostname()), port))

if __name__ == '__main__':
	# Parse command line arguments
	if len(sys.argv)==1:
		pass
	elif len(sys.argv)==2 and sys.argv[1]=="-d":
		host=socket.gethostbyname(socket.gethostname())
	elif len(sys.argv)==3:
		host=sys.argv[1]
		port=int(sys.argv[2])
	else:
		displayHelp()
		exit(1)

	# Start the computation thread
	threading.Thread(target=simulationCompute).start()

	# Start the server
	log("Server started on ws://%s:%s/" % (host, port))
	start_server = websockets.serve(clientHandler, host, port, klass=IPGetterProtocol)
	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()
	