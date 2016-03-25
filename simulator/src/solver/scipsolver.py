#@package scipsolver
#Class to solve a model using SCIP and ZIMPL.
#@version 1.0

import re, os

from .solver import Solver

class ScipSolver(Solver):
    ## Constructor.
    # @param scipBin Path to the SCIP binary.
    # @param lp Binary equal to True if the solver writes the LP problem file.
    # @param timeLimit Time limit in seconds
    # @param maxTrials Maximum calling trials of the solver.
    def __init__(self,scipBin='../scip',lp=False,timeLimit=5*60,maxTrials=2):
        self._sol={}
        self.lp=lp
        self._scip=scipBin
        self.timeLimit=timeLimit
        self.maxTrials=max(1,maxTrials)
        self.noPresolve=False

    def solve(self,model,solution,cwd=""):
        Solver.solve(self,model,solution)

        # Create the cmd to solve the problem
        scipCmd = self._scip
        if self.timeLimit > 0:
            scipCmd += ' -c "set limits time %s"'%self.timeLimit
        if self.noPresolve:
            scipCmd += ' -c "set presolving maxrounds 0"'
        scipCmd+=' -c "read %s"'%model

        if self.lp:
            lpFile=solution+".lp"
            scipCmd+=' -c "write problem %s"' % lpFile
            if os.path.exists('%s/%s'%(cwd,lpFile)):
                os.remove('%s/%s'%(cwd,lpFile))
        scipCmd+=' -c "opt" -c "write solution %s" -c "q"'%solution

        # Call the solver
        solutionFile='%s/%s'%(cwd,solution)
        if os.path.exists(solutionFile):
            os.remove(solutionFile)
        self.debugInfo="\tCommand: %s\n"%scipCmd

        retCode=-1
        trial=0
        while retCode!=0 and trial<self.maxTrials:
            retCode=Solver.silentCall(self,scipCmd,cwd)
            trial+=1

        # Check return
        if retCode != 0:
            raise Exception('Error calling SCIP with the model \"'+ model + '\".\n\tCommand : '+ scipCmd)
        if not os.path.isfile('%s/%s'%(cwd,solution)):
            raise Exception('Error when generating \"'+solution+'"\".\n\tCommand : '+ scipCmd)

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
        dict['#$!feasible']=False

        with open(filePath, 'r') as file:
            varRegex = re.compile('^(\S+)\s+(\S+)\s+\(.+\)')
            statusRegex = re.compile('^solution status:\s+(\S+)\s+')
            objRegex = re.compile('^objective value:\s+(\S+)\s+')
            for line in file:
                matchVar=varRegex.match(line)
                if matchVar:
                    dict[matchVar.group(1)]=matchVar.group(2)
                elif statusRegex.match(line):
                    dict['#$!status']=statusRegex.match(line).group(1)
                elif objRegex.match(line):
                    dict['#$!obj']=float(objRegex.match(line).group(1))
                    dict['#$!feasible']=True
        return dict

    ## @var _sol
    # Solution dictionary.
    ## @var lp
    # Boolean, True if the solver writes the LP problem file.
    ## @var _scip
    # Path to the SCIP binary.
    ## @var timeLimit
    # Time limit in seconds.
    ## @var maxTrials
    # Maximum calling trials of the solver.
    ## @var noPresolve
    # Boolean, True if deactivate the presolve.
