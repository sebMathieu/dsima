#@package cplexsolver
#Class to solve a model using CPLEX, SCIP and ZIMPL.
#@version 1.0

import re, os

from .solver import Solver

class CplexSolver(Solver):
	## Constructor.
	# @param cplexBin Path to the CPLEX binary.
	# @param scipBin Path to the SCIP binary.
	# @param lp Binary equal to True if the solver writes the LP problem file.
	# @param timeLimit Time limit in seconds
	# @param maxTrials Maximum calling trials of the solver.
	def __init__(self,cplexBin='cplex',scipBin='../scip',lp=False,timeLimit=5*60,maxTrials=2):
		self._sol={}
		self.lp=lp
		self._cplex=cplexBin
		self._scip=scipBin
		self.timeLimit=timeLimit
		self.maxTrials=max(1,maxTrials)

	def solve(self,model,solution,cwd=""):
		Solver.solve(self,model,solution)

		# Create the cmd to write the lp
		scipCmd=self._scip
		scipCmd+=' -c "read %s"'%model

		lpFile=solution+".lp"
		lpPath='%s/%s'%(cwd,lpFile)
		scipCmd+=' -c "write problem %s"' % lpFile
		if os.path.exists(lpPath):
			os.remove(lpPath)

		scipCmd+=' -c "q"'

		# Call scip and generate the lp
		self.debugInfo="\tCommand: %s\n"%scipCmd
		retCode=-1
		trial=0
		while retCode!=0 and trial<self.maxTrials:
			retCode=Solver.silentCall(self,scipCmd,cwd)
			trial+=1

		# Check return
		if retCode != 0:
			raise Exception('Error calling SCIP with the model "' + model + '".\n\tCommand : '+ scipCmd)
		if not os.path.isfile(lpPath):
			raise Exception('Error when generating "' + lpFile + '"".\n\tCommand : '+ scipCmd)

		# Solve the lp using cplex
		solutionFile='%s/%s'%(cwd,solution)
		cplexCmd = '%s -c "set logfile *"' % self._cplex
		if self.timeLimit > 0:
			cplexCmd+=' -c "set timelimit %s"' % self.timeLimit

		# Feasibility first
		cplexCmd += ' -c "set lpmethod 1"'
		#cplexCmd += ' -c "set mip tolerances mipgap 0.1"' # Relax tolerance

		cplexCmd += ' "read %s" "opt" "write %s" "y" "quit"' % (lpFile, solution)

		if os.path.exists(solutionFile):
			os.remove(solutionFile)

		self.debugInfo="\tCommand: %s\n"%cplexCmd
		retCode=-1
		trial=0
		while retCode!=0 and trial<self.maxTrials:
			retCode=Solver.silentCall(self,cplexCmd,cwd)
			trial+=1

		# Check return
		if retCode != 0:
			raise Exception('Error calling CPLEX with the model \"'+ lpFile + '\".\n\tCommand : '+cplexCmd)
		if not os.path.isfile(solutionFile):
			raise Exception('Error when generating the solution file with the model \"'+ lpFile + '\".\n\tCommand : '+cplexCmd)

		# Parse the solution
		self._sol=self._parseSolution(solutionFile)

	def isFeasible(self):
		return self._sol['#$!feasible']

	def isOptimal(self):
		optimal=(self._sol['#$!status'].find("optimal") >=0)
		if not optimal:
			self.debugInfo+="\tSolution status: %s\n"%self._sol['#$!status']
		return optimal

	def objectiveValue(self):
		return self._sol['#$!obj']

	def variableValue(self,variableName='x'):
		v=0.0
		try:
			v=float(self._sol[variableName])
		finally:
			return v

	## Parse the solution file.
	#@param filePath Path to the solution file.
	def _parseSolution(self,filePath):
		dict={}
		dict['#$!feasible'] = False
		dict['#$!obj'] = 0.0
		dict['#$!status'] = 'not parsed'

		with open(filePath, 'r') as file:
			feasibleRegex = re.compile('^\s+primalFeasible="(\d)"')
			statusRegex = re.compile('^\s+solutionStatusString="(.+)"')
			varRegex = re.compile('^\s+<variable name="(.+?)" .+? value="(.+?)"')
			objRegex = re.compile('^\s+objectiveValue="(.+)"')
			for line in file:
				matchVar=varRegex.match(line)
				if matchVar:
					dict[matchVar.group(1)]=matchVar.group(2)
				elif objRegex.match(line):
					dict['#$!obj']=float(objRegex.match(line).group(1))
				elif feasibleRegex.match(line):
					dict['#$!feasible'] = feasibleRegex.match(line).group(1) == "1"
				elif statusRegex.match(line):
					dict['#$!status'] = statusRegex.match(line).group(1)
		return dict

	## @var _sol
	# Solution xml tree.
	## @var lp
	# Boolean, True if the solver writes the LP problem file.
	## @var _cplex
	# Path to the CPLEX binary.
	## @var _scip
	# Path to the SCIP binary.
	## @var timeLimit
	# Time limit in seconds.
	## @var maxTrials
	# Maximum calling trials of the solver.
