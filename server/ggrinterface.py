##@package ggrinterface
# Interface to get the global results of an instance.
#@author Sebastien MATHIEU

import asyncio,websockets
import re,os
import zipfile

## Send the paramaters file of an instance to the client.
# @param client Client we are interacting with.
# @param message Message sent.
@asyncio.coroutine
def interact(client,message):
	hash=re.compile('"(\w\w\w\w\w\w\w\w)"').search(message).groups()[0]
	with open("%s/%s/globalResults-%s.xml"%(client.instancesFolder,hash,hash), 'rb') as file:
		yield from client.socket.send(file.read())
		
		
	