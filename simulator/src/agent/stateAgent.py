##@package stateAgent
#@author Sebastien MATHIEU

from abc import ABCMeta, abstractmethod
from .agent import Agent

## Abstract class of a state agent.
# A state agent is an agent with a list of numeric state variables which may be checked for convergence.
class StateAgent(Agent):
    __metaclass__ = ABCMeta
    
    def __init__(self,name=""):
        self.rename(name)
    
    ## Create the set of personal data of the state agent.
    # In particular it creates its personal dictionary of variables referenced by its name (@see Data.personal).
    # One of its personal variables is 'statusVariables' which is a list of identifier of personal variables to check for convergence.
    # These state variables must take the form of a list of floats.
    # @param data Data. 
    @abstractmethod
    def initialize(self, data):
        data.personal[self.name]={}
        data.personal[self.name]['statusVariables']=[]
    
    ## Perform the action of the agent.
    # The data are modified by the actions of the agent.
    # @param data Data needed for the action. 
    # @param layer Current layer. 
    @abstractmethod
    def act(self, data, layer):
        pass
    
    ## Rename the agent.
    # @param name New name.
    # If an empty name is given the new name is "Agent #id".
    def rename(self,name=""):
        if name=="":
            self.name="Agent #"+str(self._id)
        else:
            self.name=name
    
    def __str__(self):
        return self.name
    
    ## @var name
    # Actor name.
