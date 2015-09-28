## @package tools
# Bunch of tool functions.
#@author Sebastien MATHIEU
#@version 2.0

#TODO clean with only necessary functions.

import csv, glob
import subprocess, os, errno, sys, shutil
from contextlib import contextmanager

## Locking mechanism.
# Usage: with fileLock('lockFile.lock'):
# Source : http://amix.dk/blog/post/19531
@contextmanager
def fileLock(lockFile):
    if os.path.exists(lockFile):
        print('Only one script can run at once. '\
              'Script is locked with %s' % lockFile)
        sys.exit(-1)
    else:
        open(lockFile, 'w').write("1")
        try:
            yield
        finally:
            os.remove(lockFile)
			
##Write a content to the log file.
#@param content Content to write.
#@param filePath Path to the log file. 
#@param alsoPrint Boolean equals to true if print on the screen is desired.
def log(content,filePath="log.log", alsoPrint=True):
	if alsoPrint:
		print(content)
	if filePath==None or filePath=="":
		return
	if not os.path.exists(os.path.dirname(os.path.abspath(filePath))):
		os.makedirs(os.path.dirname(os.path.abspath(filePath)))
	with open(filePath, "a") as f:
		f.write(str(content)+'\n')

##Clean the log file.
#@param filePath Path to the log file. 
def cleanLog(filePath="log.log"):
	if filePath==None or filePath=="":
		return
	if not os.path.isfile(filePath):
		return
	f = open(filePath,'w')
	f.close()

##Read a list of floats in a CSV file.
#@param fileName Name of the file to read.
#@return List of doubles.  
def readCSVFloatList(fileName):
	with open(fileName, 'rb') as csvfile:
		csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
		row=csvReader.next()
		row=map(float,row)
		return row
	return []
	
##Write a list of floats in a file.
#@param fileName Name of the file to read.
#@param floatList List of floats. 
def writeFloatList(fileName, floatList):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',',quotechar='\"', quoting=csv.QUOTE_MINIMAL)
		csvWriter.writerow(floatList)
		
##Write a list of floats in a file.
#@param fileName Name of the file to read.
#@param floatMatrix List of list floats. 
def writeFloatMatrix(fileName, floatMatrix):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',',quotechar='\"', quoting=csv.QUOTE_MINIMAL)
		for fl in floatMatrix:
			csvWriter.writerow(fl)
		
##Call a commend without display.
#@param command Command to execute
#@return The return status of the command. 
def silentCall(command):
	retCode=-1
	with open(os.devnull, "w") as f:
		retCode=subprocess.call(command, stdout = f, shell=True)
		#retCode=subprocess.call(command, shell=True)
	return retCode

##Clear a folder of all files with a given extension.
#@param path Folder path.
#@param ext Extension or list of extension with the dot.
def clearFolder(path, ext=""):
	if not os.path.isdir(path):
		return
		
	# Get the list of files to remove
	fileList=[]
	if type(ext) == type(list()):
		for e in ext:
			fileList=filelist+glob.glob(path+'/*.'+e)
	if ext=="":
		fileList=glob.glob(path+'/*')
	else:
		fileList=glob.glob(path+'/*.'+ext)
	
	# Remove the files
	for f in fileList:
		os.remove(f)

##	Copy a file and check if the copy succeeded.
# @param src Source.
# @param dst Destination.
# @param maxChecks Maximum checks and trials.	
def safeCopy(src,dst,maxChecks=3):
	# Remove file if destination already exists
	if os.path.isfile(dst):
		os.remove(dst)
	
	# Copy
	shutil.copy2(src,dst)
	for i in range(maxChecks):
		if os.path.isfile(dst):
			return
		else:
			shutil.copy2(src,dst)
	
	# Maximum checks reached, raise error.
	raise Exception("Unable to copy %s to %s." % (src,dst))
