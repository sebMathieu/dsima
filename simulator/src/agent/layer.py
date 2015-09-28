##@package layer
#@author Sebastien MATHIEU

## Layer of the system.
# List the agents belonging to one layer.
class Layer:
      ## Total number of layers.
    _layersNumber=0
    
    ## Default constructor.
    # @param agentList Initial list of agents in the layer.
    # @param name Name of the layer.
    def __init__(self, agentList=[], name=""):
        self._agentList=agentList
        self._id=Layer._layersNumber
        Layer._layersNumber+=1
        self.rename(name)
    
    ## Perform the action of all agents in the layer.
    # The data are modified by the actions of the agent.
    # @param data Data needed for the action. 
    def act(self, data):
        for a in self._agentList:
            a.act(data,self)        
    
    ## Add an agent to the agent list.
    # @param agent Agent to add. 
    def addAgent(self,agent):
        if agent not in agentList:
            agentList.append(agent)        
    
    ## Get the list of agents in the layer.
    # @return List of agents
    def agentList(self):
        return self._agentList
    
    ## Get the layer's id.
    def id(self):
        return self._id
    
    ## Remove an agent from the agent list.
    # @param agent Agent to add. 
    def removeAgent(self,agent):
        agentList.remove(agent)
        
    ## Rename the layer.
    # @param name New name.
    # If an empty name is given the new name is "Layer #id".
    def rename(self,name=""):
        if name=="":
            self.name="Layer #"+str(self._id)
        else:
            self.name=name
    
    def __str__(self):
        return self.name
    
    
    # @var _agentList
    # List of agents in this layer. 
    ## @var _id
    # Unique identifier of the layer.
    ## @var name
    # Layer name.
    