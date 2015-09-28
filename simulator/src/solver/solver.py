##@package solver
#@author Sebastien MATHIEU

import subprocess, os

## Skeleton of a solver interface.
class Solver(object):
	def __init__(self):
		self.lastModel=""
		self.lastSolution=""
		self.debugInfo=""

	## Solve a problem
	# @param model Model file.
	# @param solution Target solution file.
	def solve(self,model,solution):
		self.lastModel=model
		self.lastSolution=solution

	## Raise an exception if method isOptimal returns false.
	def checkOptimal(self):
		if (not self.isOptimal()):
			raise Exception("Problem not solved to optimality:\n\tModel: %s\n\tSolution file: %s\n%s\n" % (self.lastModel,self.lastSolution,self.debugInfo))
	
	## Raise an exception if method isFeasible returns false.
	def checkFeasible(self):
		if (not self.isFeasible()):
			raise Exception("Solution is not feasible:\n\tModel: %s\n\tSolution file: %s\n%s\n" % (self.lastModel,self.lastSolution,self.debugInfo))
	
	## Return true if the solution is optimal.
	#@return True if the solution is optimal.
	def isFeasible(self):
		return self.isOptimal()
	
	## Return true if the solution is optimal.
	#@return True if the solution is optimal.
	def isOptimal(self):
		return False
		
	##Get the objective value.
	#@return Objective value. 
	def objectiveValue(self):
		return 0.0

	##Get the value of a variable.
	#@param variableName Name of the variable.
	#@return Value, 0 if not found.
	def variableValue(self,variableName='x'):
		return 0.0

	##Get a vector of variable values.
	#@param maxIndex Maximum index.
	#@param variablePrefix Prefix of the variables to get. For instance : 'x#' becomes 'x#0','x#1',...
	#@param minIndex Minimum index.
	#@param variableSuffix Suffix of the variables to get. Appended after the index number.
	#@return Vector of values.
	def variableVectorValue(self,maxIndex,variablePrefix='x#',minIndex=0,variableSuffix=''):
		l=[0.0]*(maxIndex-minIndex+1)
		for i in range(minIndex,maxIndex+1):
			l[i-minIndex]=self.variableValue(variablePrefix+str(i)+variableSuffix)
		return l	
	
	##Call a commend without display.
	#@param command Command to execute
	#@param cwd Working directory.
	#@return The return status of the command. 
	def silentCall(self,command,cwd=""):
		retCode=-1
		with open(os.devnull, "w") as f:
			retCode=subprocess.call(command, stdout = f, shell=True, cwd=cwd)
			#retCode=subprocess.call(command, shell=True, cwd=cwd)
		return retCode

	## @var lastModel
	# Last model used by the solve method.
	## @var lastSolution
	# Last solution obtained by the solve method.
	## @var debugInfo
	# Additional debug informations to display.
	