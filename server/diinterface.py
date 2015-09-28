##@package diinterface
# Interface to delete an instance.
#@author Sebastien MATHIEU

import asyncio,websockets
import re,os
import zipfile
import shutil

## Delete an instance.
# @param client Client we are interacting with.
# @param message Message sent.
@asyncio.coroutine
def interact(client,message):
	hash=re.compile('"(\w\w\w\w\w\w\w\w)"').search(message).groups()[0]
	
	directory="%s/%s"%(client.instancesFolder,hash)
	shutil.rmtree(directory)
	yield from client.socket.send("ok deleted \"%s\""%hash)
	