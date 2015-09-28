##@package gdrinterface
# Interface to get a daily result.
#@author Sebastien MATHIEU

import asyncio,websockets
import re,os
import zipfile

## Send the daily result file of an instance to the client.
# @param client Client we are interacting with.
# @param message Message sent.
@asyncio.coroutine
def interact(client,message):
	captured=re.compile('"(\w\w\w\w\w\w\w\w)"\s+"(\d+)"').search(message)
	hash=captured.group(1)
	day=captured.group(2)
	
	with open("%s/%s/%s/result-%s-d%s.zip"%(client.instancesFolder,hash,day,hash,day), 'rb') as file:
		yield from client.socket.send(file.read())
	