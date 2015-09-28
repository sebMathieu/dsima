##@package rinterface
# Interface to reset an instance.
#@author Sebastien MATHIEU

import asyncio,websockets
import re,os,shutil
import xml.etree.ElementTree as ElementTree

## Reset an instance by deleting the files.
# @param client Client we are interacting with.
# @param message Message sent.
@asyncio.coroutine
def interact(client,message):
	hash=re.compile('"(\w\w\w\w\w\w\w\w)"').search(message).groups()[0]

	# Update xml status
	instanceDirectory='%s/%s'%(client.instancesFolder,hash)
	xmlFilePath="%s/%s.xml"%(instanceDirectory,hash)
	tree=ElementTree.parse(xmlFilePath)
	root=tree.getroot()

	# Get the status tag of the xml document
	statusTag=root.find('status')
	if statusTag is None:
		statusTag=ElementTree.Element('status')
		root.append(statusTag)

	statusTag.text="reset simulation"
	tree.write(xmlFilePath)

	# Clear the files day by day
	tag=root.find('days')
	days=list(range(int(tag.find('start').text), int(tag.find('end').text))) # List of days
	for d in days:
		try:
			os.remove('%s/%s/result-%s-d%s.zip'%(instanceDirectory,d,hash,d))
		except OSError:
			pass

	# Clear general files
	try:
		os.remove('%s/errors.xml'%instanceDirectory)
		os.remove('%s/globalResults-%s.xml'%(instanceDirectory,hash))
	except OSError:
		pass

	# Notifies the client
	yield from client.socket.send("ok reset \"%s\""%hash)