##@package main
#@author Sebastien MATHIEU

import sys, getopt, os, shutil

import src.options as options
import src.tools as tools

## Entry point of the program.
def main(argv):
	from src.system import System
	
    # Read instance folder
	if len(argv) < 1 :
		displayHelp()
		sys.exit(2)
	folderPath=argv[-1] if argv[-1].endswith(("/","\\")) else argv[-1]+"/"
	if not os.path.exists(folderPath):
		raise Exception('Folder \"%s\" does not exists.' % folderPath)
	outputSolutionFile="data.xml"
    
	# Parse options
	maximumIterations=20
	convergenceTolerance=None
	try:
	   	opts, args = getopt.getopt(argv[0:-1],"dm:o:t:f:",["im=","gamma=","maxiterations=",'operationfolder=']) 
	except getopt.GetoptError as err:
		tools.log(err)
		displayHelp()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-o"):
			outputSolutionFile=arg
		elif opt in ("-d"):
			options.DEBUG=True
		elif opt in ("--gamma"):
			options.DSO_IMBALANCE_PRICE_RATIO=float(arg)
		elif opt in ("--maxiterations"):
			maximumIterations=max(1,int(arg))
		elif opt in ("-t"):
			convergenceTolerance=float(arg)
		elif opt in("-f","--operationfolder"):
			options.FOLDER=arg
	
	# Log file
	options.log=outputSolutionFile+".log"
	
    # Create and launch system
	lockFile='lock.lock'
	if options.COPY:
		# If copy mode, the lock file is specific to the operation folder.
		lockFile='%s.lock'%(options.FOLDER)
	with tools.fileLock(lockFile):
		tools.cleanLog(options.LOG)
		system=System(dataFolder=folderPath,maximumIterations=maximumIterations,outputSolutionFile=outputSolutionFile,convergenceTolerance=convergenceTolerance)
		tools.log(system.run(),options.LOG,options.PRINT_TO_SCREEN)		
	
## Display help of the program.
def displayHelp():
	text="Usage :\n\tpython main.py [options] dataFolder\n\n"
	text+="Options:\n"
	text+="\t-d\t\t\tDebug mode.\n"
	text+="\t-o X\t\t\tSet X.xml as output file.\n" #TODO If explicitely .xml or .xml.zip 
	text+="\t--maxiterations X\tSet X as the maximum number of iterations.\n"
	text+="\t-t X\t\t\tSet the numerical tolerance for the convergence to X.\n"
	text+="\t-f X\t\t\tSet X as the operation folder" 
	tools.log(text,options.LOG,options.PRINT_TO_SCREEN)
	
# Starting point from python #   
if __name__ == "__main__":
    main(sys.argv[1:])
	
	