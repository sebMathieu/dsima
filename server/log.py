##@package log
#@author Sebastien MATHIEU

import threading
from datetime import datetime

## Log file path.
LOG_FILE="log-server.log"
## Semaphore to lock the logging.
logLock=threading.Lock()

##Write a content to the log file in a thread-safe manner.
#@param content Content to write.
def log(content):
	timestamp = datetime.now()
	content="(%s) %s" %(timestamp.strftime('%H:%M:%S - %d/%m/%y'), content)

	with logLock:
		print(content)
		with open(LOG_FILE, "a") as f:
			f.write(str(content)+'\n')
