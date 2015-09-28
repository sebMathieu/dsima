##@package abstractSystem
#@author Sebastien MATHIEU

from abc import ABCMeta, abstractmethod

from .data import Data

## Abstract agent-based system
class AbstractSystem(object):
    __metaclass__ = ABCMeta
    
    ## Constructor.
    # @param maximumIterations New maximum number of iterations. 
    def __init__(self,maximumIterations=1000):
        self.iterations=0
        self.data=Data()
        self.layerList=[]
        self.setMaximumIterations(maximumIterations)
    
    ## Internal method which inialize the agents of the system.
    def initializeAgents(self):
        # Get the list of all agents from the list of layers
        agentSet=set()
        for l in self.layerList:
            agentSet=agentSet|set(l.agentList())
        
        # Initialize all agents
        for a in agentSet:
            a.initialize(self.data)
                
    ## Set the maximum number of iterations.
    # @param maximumIterations New maximum number of iterations. 
    def setMaximumIterations(self, maximumIterations):
        self._maxIterations=maximumIterations
    
    ## Run the system.
    # @return Information of the system convergence. 
    def run(self):
        # Initialize
        self.iterations=0
        self.initializeAgents()
        
        # Loop
        while True:
            # Act on every layer
            for l in self.layerList:
                l.act(self.data)
            
            # Check convergence
            convergenceStatus=self.hasConverged()
            if convergenceStatus != None:
                return convergenceStatus
            
            # Check maximum iterations
            self.iterations+=1
            if self.iterations >= self._maxIterations:
                return "Maximum number of iterations reached ("+str(self.iterations)+")."
    
    ## Define if the system has converged based on the data gathered at the end of the last layer.
    # @return None if the system has not converged. 
    @abstractmethod
    def hasConverged(self):
        return None
            
    ## @var data
    # Data structure.
    ## @var iterations
    # Current number of iterations.
    ## @var layerList
    # Ordered list of layers of the system.
    ## @var _maxIterations
    # Maximum number of iterations.
    