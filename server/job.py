## @package job
#@author Sebastien MATHIEU

import asyncio

## Command line job.
class Job:
	## Waiting status.
	WAITING=2
	## Job completed status.
	COMPLETED=0
	## Error status.
	ERROR=-1
	## Running status.
	RUNNING=1
	## Aborted status.
	ABORTED=-2

	## Constructor.
	# @param args List of arguments.
	def __init__(self,args):
		self.args=args
		self.finished=asyncio.Semaphore(value=0)
		self.result=None
		self.process=None
		self.status=2
		
	## @var args
	# List of arguments.
	## @var finished
	# Semaphore to check if the job is completed.
	## @var result
	# Stdout output of the job.
	## @var process
	# Process corresponding to the job.
	## @var status
	# Execution status of the job.
	
	
	