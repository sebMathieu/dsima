##@package iginterface
# Instance generator interface.
#@author Sebastien MATHIEU

import time, sys, threading, queue, subprocess,traceback,os
import asyncio,websockets
import xml.etree.ElementTree as ElementTree

from .job import Job
from .log import log

## Computation thread of the instance generator.
def computationThread(job):	
	try:
		job.status=Job.RUNNING
		
		xmlContent=job.args[1]
		instancesFolder=job.args[0]
		
		# Get the hash
		root=ElementTree.fromstring(xmlContent)
		tree=ElementTree.ElementTree(root)
		hash=root.find('hash').text
		directory='%s/%s'%(instancesFolder,hash)
		if not os.path.exists(directory):
			os.makedirs(directory)
		
		# Write the xml file
		xmlDataFile='%s/%s.xml'%(directory,hash)
		tree.write(xmlDataFile)
		
		# Launch the generation
		cmd=['python3', 'main.py', '../%s/%s/%s.xml'%(instancesFolder,hash,hash), '../%s'%instancesFolder]
		job.process = subprocess.Popen(cmd, cwd='instanceGenerator', stdout=subprocess.PIPE, stderr=subprocess.PIPE) # TODO remove pipes
		log("Instance generation of %s with the cmd \"%s\" started"%(hash," ".join(cmd)))
		returnCode=job.process.wait()
		log("Instance generation process of %s finished"%hash)
		if job.status != Job.ERROR:
			# Get the process outputs
			stdout, stderr = job.process.communicate()
			stderr=stderr.decode('latin-1').strip()
			stdout=stdout.decode('latin-1').strip() # Clean text answer
			if stderr != "":
				log("Stderr:\n%s"%stderr)
			
			# Get the status tag of the xml document
			statusTag=root.find('status')
			if statusTag is None:
				statusTag=ElementTree.Element('status')
				root.append(statusTag)
			
			# Notifies the completion of the job
			if returnCode == 0:
				job.result=stdout
				job.status=Job.COMPLETED
				statusTag.text="generated"
			else:
				job.result=stderr
				job.status=Job.ERROR
				statusTag.text="error instance generation"
			tree.write(xmlDataFile)
		else:
			job.result=Exception("Job killed !")
			
	except Exception as e:
		job.status=Job.ERROR
		job.result=e
		log(traceback.format_exc())
	finally:
		#TODO Clean the mess if aborted
		job.finished.release()
	
## Interact with the user and with the instance generator module.
# @param client Client we are interacting with.
@asyncio.coroutine
def interact(client):
	# Agree to receive the instance parameters and waits
	yield from client.socket.send("OK instance generation request")
	xmlParameters=yield from client.socket.recv()	
	if xmlParameters is None:
		return
	yield from client.socket.send("OK instance received")
	client.log("\n"+xmlParameters)

	# Start the instance generation thread
	job=Job([client.instancesFolder,xmlParameters])
	thread=threading.Thread(target=computationThread,args=[job])
	thread.daemon=True
	thread.start()
	
	# Get the hash
	root=ElementTree.fromstring(xmlParameters)	
	hash=root.find('hash').text
		
	# Polling of the client until the job is complete
	while True:
		message = yield from client.socket.recv()
		if message is None or message.strip().lower()=="terminate":
			# Kill thread if running
			if job.status==Job.RUNNING or job.status==Job.WAITING:
				client.log("Terminate request \"%s\""%hash)
				job.status=Job.ABORTED
				if job.process is not None:
					job.process.terminate()
			break
		elif message.strip().lower() == "ready?":
			# Check status
			if job.finished.locked():
				if job.status==Job.RUNNING:
					yield from client.socket.send("OK running \"%s\""%hash)
				else:
					yield from client.socket.send("OK waiting \"%s\""%hash)
			else:
				if job.status==Job.COMPLETED:
					yield from client.socket.send("OK instance generated \"%s\""%hash)
				else:
					raise Exception(job.result)
				break
		else:
			yield from client.handleMessage(message)
	