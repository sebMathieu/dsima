##@package agent
#@author Sebastien MATHIEU

from abc import ABCMeta, abstractmethod

## Abstract class of an agent.
class Agent(object):
    __metaclass__ = ABCMeta
    
    ## Total number of agents.
    _agentsNumber=0
    
    ## Default constructor.
    def __init__(self):
        self._id=Agent._agentsNumber
        Agent._agentsNumber+=1
    
    ## Get the agent's id.
    def id(self):
        return self._id;

    ## Initialize the agent and create its set of personal data.
    # @param data Data. 
    @abstractmethod
    def initialize(self, data):
        pass
    
    ## Perform the action of the agent.
    # The data are modified by the actions of the agent.
    # @param data Data needed for the action. 
    # @param layer Current layer.
    @abstractmethod 
    def act(self, data, layer):
        pass
    
    def __repr__(self):
        return "A#"+str(self._id)
    
    def __str__(self):
        return "Agent #"+str(self._id)
    
    ## @var _id
    # Unique identifier of the agent.
    