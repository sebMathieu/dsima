##@package main
#@author Sebastien MATHIEU

import sys, getopt

#import src.tools as tools

## Entry point of the program.
def main(argv):	
    # Default parameters
	if len(argv) < 1 :
		displayHelp()
		sys.exit(2)
	instanceFile=argv[0]
	outputDirectory=None
	if len(argv) >= 2:
		outputDirectory=argv[1]
	
	# Parse instance parameters
	from src.instanceparamaters import InstanceParameters
	instanceParameters=InstanceParameters(instanceFile)
	
	# Read annual data
	from src.timedata import TimeData
	annualData=TimeData('annualdata')
	
	# Create the instance
	from src.instance import Instance
	instance=Instance(instanceParameters, annualData,outputDirectory)
	
## Display help of the program.
def displayHelp():
	text="Usage :\n\tpython main.py instanceParameters.xml [outputDirectory]"
	print(text);

# Starting point from python #   
if __name__ == "__main__":
    main(sys.argv[1:])
	
	