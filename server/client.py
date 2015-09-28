##@package client
#@author Sebastien MATHIEU

import asyncio,websockets
import traceback

from .iginterface import interact as IGInteract
from .lgiinterface import interact as LGIInteract
from .giinterface import interact as GIInteract
from .ggrinterface import interact as GGRInteract
from .gdrinterface import interact as GDRInteract
from .diinterface import interact as DIInteract
from .isinterface import interact as ISInteract
from .rinterface import interact as RInteract
from .isinterface import isComputing as isComputing
from .log import log

## Manages all the interaction with the client.
class Client:
	def __init__(self,websocket):
		self.socket=websocket
		self.ip=websocket.remoteIP
	
	## Log an action
	def log(self,message):
		log("%s : %s"%(self.ip,message))

	## Interact with the client.
	@asyncio.coroutine
	def interact(self):
		self.log("connected")

		while True:
			message = yield from self.socket.recv()
			if message is None:
				break
			else:
				yield from self.handleMessage(message)

		self.log("disconnected")

	@asyncio.coroutine
	def handleMessage(self,message):
		try:
			if message is None:
				return
			message=message.strip().lower()
			if message == "instance generation request":
				self.log(message)
				yield from IGInteract(self)
			elif message == "list generated instances":
				self.log(message)
				yield from LGIInteract(self)
			elif message.startswith("get instance"):
				self.log(message)
				yield from GIInteract(self, message)
			elif message.startswith("delete instance"):
				self.log(message)
				yield from DIInteract(self, message)
			elif message.startswith("reset instance"):
				self.log(message)
				yield from RInteract(self,message)
			elif message.startswith("instance simulation request"):
				self.log(message)
				yield from ISInteract(self, message)
			elif message.startswith("is computing simulation"):
				yield from isComputing(self,message)
			elif message.startswith("get daily result"):
				self.log(message)
				yield from GDRInteract(self, message)
			elif message.startswith("get global results"):
				self.log(message)
				yield from GGRInteract(self, message)
			else:
				raise Exception("Unknown request \"%s\""%message)
		except Exception:
			self.log("Unexpected error: %s"%traceback.format_exc())
			if self.socket.open:
				yield from self.socket.send("ERROR %s"%traceback.format_exc())


	## @var instancesFolder
	# Folder with the instances of the client.
	instancesFolder="instances"
	## @var socket
	# Websocket interface to the client.
	## @var ip
	# IP of the client.
	