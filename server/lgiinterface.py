##@package lgiinterface
# Interface to list the generated instances.
#@author Sebastien MATHIEU

import os
import xml.etree.ElementTree as ElementTree
import asyncio,websockets

# Interact with the user to interact with the instance generator module.
# @param client Client we are interacting with.
@asyncio.coroutine
def interact(client):
	instances=[]

	# Create instances directory if it does not exist
	if not os.path.isdir(client.instancesFolder):
		os.makedirs(client.instancesFolder)

	# List instances in directory
	for dir in os.listdir(client.instancesFolder):
		xmlFile="%s/%s/%s.xml"%(client.instancesFolder,dir,dir)
		if not os.path.isdir("%s/%s"%(client.instancesFolder,dir)) or not os.path.isfile("%s/%s/%s.xml"%(client.instancesFolder,dir,dir)):
			continue
		
		root=ElementTree.parse(xmlFile).getroot()
		hash=root.find('hash').text
		title=root.find('title').text
		if hash == dir:
			if title == None:
				title=""
			instances.append("%s;%s"%(hash,title))
			
	yield from client.socket.send("\n".join(instances))
