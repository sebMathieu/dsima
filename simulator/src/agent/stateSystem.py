##@package stateSystem
#@author Sebastien MATHIEU

from abc import ABCMeta, abstractmethod
import copy

from .data import Data
from .abstractSystem import AbstractSystem

## Abstract agent-based state system.
# A state system is a system where the convergence is based on status variables.
# The system check global status variable referenced in a list of variable reference in data.general['statusVariables'].
# The personal status variable of StateAgent are also checked.
class StateSystem(AbstractSystem):
    __metaclass__ = ABCMeta
    
    def __init__(self,maximumIterations=1000, accuracy=0.0001):
        AbstractSystem.__init__(self,maximumIterations)
        self.history=[]
        self.eps=accuracy
        self._maxDifference=accuracy
        self.data.general['statusVariables']=[]
    
    def run(self):
        self.history=[]
        return AbstractSystem.run(self)
    
    ## Get the maximum deviation between two list of values.
    # @param v1 List of values.
    # @param v2 List of values.
    # @return Float.
    @staticmethod
    def maxDelta(v1, v2):
        return max(map(lambda x,y:abs(x-y),v1,v2))

    ## Define if the system has converged based on the status variables.
    # @return None if the system has not converged. 
    def hasConverged(self):
        self.history.append(copy.deepcopy(self.data))
        if len(self.history) >= 2:
            self._maxDifference=0 # Maximum difference
            
            # Check the global status variables
            globalStatusVariables=self.history[-1].general['statusVariables']
            for var in globalStatusVariables:
                self._maxDifference=max(self._maxDifference, StateSystem.maxDelta(self.history[-1].general[var],self.history[-2].general[var]))
                
            # Check the state variables x of each actors
            personal1=self.history[-1].personal
            personal2=self.history[-2].personal
            for actor, dico1 in personal1.items():
                dico2=personal2[actor]
                personalStatusVariables=dico1['statusVariables']
                for v in personalStatusVariables:
                    self._maxDifference=max(self._maxDifference, StateSystem.maxDelta(dico1[v],dico2[v]))
            
            # Check the maximum difference
            if self._maxDifference > self.eps:
                return AbstractSystem.hasConverged(self)
            else :
                return "System converged after %s iterations !" % self.iterations
        
        return AbstractSystem.hasConverged(self)
    
    ## @var eps
    # Numerical accuracy.
    ## @var history
    # History of the data.
    ## @var _maxDifference
    # Maximum difference between the two last iterations
    