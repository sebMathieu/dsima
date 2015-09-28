##@package isinterface
# Instance simulator interface.
#@author Sebastien MATHIEU

import time, datetime, re, sys, threading, queue, subprocess,traceback,os
import asyncio,websockets
import xml.etree.ElementTree as ElementTree

from .job import Job
from .log import log

# Static parameters
## Maximum number of iterations of a simulation.
MAX_ITERATIONS=10
## Numerical tolerance on the convergence.
CONVERGENCE_TOLERANCE=0.005
## Maximum threads.
MAX_THREADS=8

## Jobs to perform
jobs=queue.Queue()
## Computing status
computingLock=threading.Lock()
## List of available threads where each element is a number.
availableThreads=queue.Queue()
## Errors list where each error is a dictionary.
errors=[]
## Lock to print.
printLock=threading.Lock()
## Lock to add an error to the errors list.
errorsLock=threading.Lock()
## Running processes. The key is the thread id and the value is the process.
processList={}
## Simulator path
simulatorPath='./simulator'
# Progression
progression=0

# Computation routine
def compute():
	global processList

	while True:
		# Get a job
		job=jobs.get()

		with computingLock:
			# Computation process
			jobThread=threading.Thread(target=computationThread,args=[job])
			jobThread.start()
			jobThread.join()

		# Communicate that the task is finished
		jobs.task_done()


## Simulate an instance
# @param threadId Id of the thread using this function.
# @param instanceDirectory Directory containing the instances to simulate (hash included).
# @param hash Hash of the instance.
# @param d Day to simulate.
def simulateInstance(threadId,instanceDirectory,hash,d):
	instanceDayDirectory="%s/%s"%(instanceDirectory,d)
	resultFile='%s/result-%s-d%s.zip'%(instanceDayDirectory,hash,d)
	if not os.path.isfile(resultFile):
		# Launch the simulation
		cmd=['python3', 'main.py', 
			 '--maxiterations',str(MAX_ITERATIONS),
			 '-f','operationFolder-%s'%threadId,
			 '-o','../%s'%resultFile,
			 '-t',str(CONVERGENCE_TOLERANCE),
			 '../%s'%instanceDayDirectory]
		process = subprocess.Popen(cmd, cwd=simulatorPath, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		processList[threadId]=process
		returnCode=process.wait()
		processList[threadId]=None
		
		stdout, stderr = process.communicate()
		if stdout is None:
			stdout=""
		else:
			stdout=stdout.decode('latin-1').encode('ascii','ignore').decode('latin-1').strip()

		if stderr is None:
			stderr=""
		else:
			stderr=stderr.decode('latin-1').encode('ascii','ignore').decode('latin-1').strip()
		
			
		# Check if the instance solved correctly
		if returnCode != 0:
			cmd=" ".join(cmd)
			with errorsLock:
				errors.append({'day':d,'cmd':cmd,'returncode':returnCode,'stdout':stdout,'stderr':stderr})
				
				# Write the error to an error file
				with open('%s/error-%s-d%s.log'%(instanceDayDirectory,hash,d),'w') as errorFile:
					errorFile.write(cmd)
					errorFile.write("\n\n")
					errorFile.write(stdout)
					errorFile.write("\n\n")
					errorFile.write(stderr)
				
			with printLock:
				log("\terror with\n\t\t%s"%cmd)

	# Add itself to the available thread list
	availableThreads.task_done()
	availableThreads.put(threadId)
	
## Computation thread of the instance generator.
# @param job Job to be done.
def computationThread(job):	
	global progression
	progression=0

	# Clear
	global processList
	processList={}
	global errors
	with errorsLock:
		errors=[]

	try:
		job.result="0 0";
		job.status=Job.RUNNING
		
		# Get the instance directory
		hash=job.args[1]
		instancesFolder=job.args[0]
		instanceDirectory='%s/%s'%(instancesFolder,hash)
		if not os.path.exists(instanceDirectory):
			raise Exception("Instance \"%s\" not found."%hash)

		log("Instance %s launched" % hash)
	
		# Get the days
		xmlFilePath="%s/%s.xml"%(instanceDirectory,hash)
		tree=ElementTree.parse(xmlFilePath)
		root=tree.getroot()
		tag=root.find('days')
		days=list(range(int(tag.find('start').text), int(tag.find('end').text)))
	
		# Remove the error file if any exists
		errorFile='%s/errors.xml'% instanceDirectory
		if os.path.isfile(errorFile):
			os.remove(errorFile)
			
		# Ensure lock file are removed
		toRemove=[]
		for f in os.listdir(simulatorPath):
			if f.endswith(".lock"):
				toRemove.append('%s/%s'%(simulatorPath,f));
		for f in toRemove:
			log("\tRemove %s"%f)
			os.remove(f)
		
		# Prepare the list of available threads
		with availableThreads.mutex:
			availableThreads.queue.clear()

		for i in range(MAX_THREADS):
			availableThreads.put(i)

		# Simulate
		completedInstancesNumber=-MAX_THREADS
		totalInstances=len(days)
		for d in days:
			if job.status==Job.ABORTED: # TODO abort also the running processes
				break;
				
			# Wait for an available thread and start it
			threadNumber=availableThreads.get()
			thread=threading.Thread(target=simulateInstance,args=[threadNumber,instanceDirectory,hash,d])
			thread.daemon=True
			thread.start()
		
			# Progression
			completedInstancesNumber+=1
			if completedInstancesNumber>0:
				progression=completedInstancesNumber/totalInstances
				job.result="%s"%progression
				with printLock:
					log("\t%s progression: %.2f%%"%(hash, progression*100.0))
				
		# Wait for the last thread
		for i in range(MAX_THREADS):
			if job.status==Job.ABORTED:
				break

			# Wait for an available thread and remove it from the pile
			availableThreads.get()

			# Add to instances
			completedInstancesNumber+=1
			if completedInstancesNumber>0:
				progression=completedInstancesNumber/totalInstances
				job.result="%s"%progression
				with printLock:
					log("\t%s progression: %.2f%%"%(hash,progression*100.0))

		log('%s completed with %s error(s).'%(hash,len(errors)))

		# Generate the global results
		if len(errors) == 0:
			cmd=['python3','scripts/globalResults.py',hash]
			process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			returnCode=process.wait()
			
			# Check for error in the global results generation
			if returnCode != 0:
				# Obtain outputs
				stdout, stderr = process.communicate()
				if stdout is None:
					stdout=""
				else:
					stdout=stdout.decode('latin-1').encode('ascii','ignore').decode('latin-1').strip()

				if stderr is None:
					stderr=""
				else:
					stderr=stderr.decode('latin-1').encode('ascii','ignore').decode('latin-1').strip()

				# Write error
				errors.append({'cmd':cmd,'returncode':returnCode,'stdout':stdout,'stderr':stderr})
				if stderr != "":
					raise Exception(stderr.decode('latin-1').strip())
				elif stdout != "":
					raise Exception(stdout.decode('latin-1').strip())
				else:
					raise Exception('Error code %s with command "%s"'%(returnCode," ".join(cmd)))

		# Get the status tag of the xml document
		statusTag=root.find('status')
		if statusTag is None:
			statusTag=ElementTree.Element('status')
			root.append(statusTag)
			
		# Change the status and manage errors
		if len(errors) > 0:
			job.result="%s/%s"%(len(errors),totalInstances)
			statusTag.text="error instance simulation %s"%job.result
			job.status=Job.ERROR
			
			# Write errors in errors.csv
			with open(errorFile, 'w') as file:
				file.write('<?xml version="1.0" encoding="ISO-8859-1" ?>\n<xml>')
				for e in errors:
					file.write('<error>\n')
					for k,v in e.items():
						file.write('\t<%s>%s</%s>\n'%(k,v if v is not None else "",k))
					file.write('</error>\n')
				file.write('</xml>\n')	
		else:
			statusTag.text="simulated"
			job.status=Job.COMPLETED
		
		if job.status==Job.ABORTED:
			statusTag.text="aborted"
		tree.write(xmlFilePath)

	except Exception as e:
		job.status=Job.ERROR
		job.result=e
		log(traceback.format_exc())
	finally:
		#TODO Clean the mess if aborted
		job.finished.release()

# Terminate the processes launched by the computation threads.
def terminateProcesses():
	for p in processList.values():
		if p is not None:
			# Try to terminate
			pid = p.pid
			p.terminate()
			
			# Force kill if needed.
			try:
				os.kill(pid, 0)
				p.kill()
			except OSError:
				pass # Terminated correctly
	
## Interact with the user and with the instance simulator module.
# @param client Client we are interacting with.
# @param message Client's message.
@asyncio.coroutine
def interact(client,message):
	hash=re.compile('"(\w\w\w\w\w\w\w\w)"').search(message).groups()[0]

	# Add the simulating status
	instanceDirectory='%s/%s'%(client.instancesFolder,hash)
	if not os.path.exists(instanceDirectory):
		raise Exception("Instance \"%s\" not found."%hash)
	xmlFilePath="%s/%s.xml"%(instanceDirectory,hash)
	tree=ElementTree.parse(xmlFilePath)
	root=tree.getroot()
	statusTag=root.find('status')
	if statusTag is None:
		statusTag=ElementTree.Element('status')
		root.append(statusTag)
	statusTag.text="simulating"
	tree.write(xmlFilePath)
	
	# Agree the transaction
	yield from client.socket.send("ok waiting")

	# Start the instance simulation thread
	job=Job([client.instancesFolder,hash])
	job.result=jobs.qsize() # Initial position
	jobs.put(job)
	client.log("Instance simulation "+hash+" added to the jobs.")
	
	# Polling of the client until the job is complete
	#TODO For now, the client may disconnect without closing the socket and let the server run alone...
	message=""
	runDisconnected=False
	while not runDisconnected or message is not None:
		message = yield from client.socket.recv()
		if message is None or message.strip().lower()=="terminate":
			# Kill thread if running
			if not runDisconnected and (job.status==Job.RUNNING or job.status==Job.WAITING):
				client.log("Terminate request")
				job.status=Job.ABORTED
				terminateProcesses()
		elif message.strip().lower()=="run disconnected":
			runDisconnected=True;
			client.log("Run disconnected")
			yield from client.socket.send("ok run disconnected")
		elif message.strip().lower() == "ready?":
			# Check status
			if job.finished.locked():
				if job.status==Job.RUNNING:
					yield from client.socket.send("OK running %s"%job.result)
				else:
					yield from client.socket.send("OK waiting")
			else:
				if job.status==Job.COMPLETED:
					yield from client.socket.send("OK instance simulated")
				else:
					yield from client.socket.send("ERROR instance simulation %s"%job.result)
				break
		else:
			yield from client.handleMessage(message)

	if runDisconnected:
		yield from job.finished.acquire() # Wait for the job to finish

## Send a message with the computing status.
@asyncio.coroutine
def isComputing(client,message):
	if computingLock.locked() :
		yield from client.socket.send('is computing simulation with progression %s and %s jobs'%(progression,jobs.qsize())) # TODO pile size
	else:
		yield from client.socket.send('is waiting for simulation')

