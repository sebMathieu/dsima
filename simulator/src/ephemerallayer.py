##@package ephemerallayer
#@author Sebastien MATHIEU

from .agent.layer import Layer

## Layer of the system that is acting only on a limited number of iterations.
class EphemeralLayer(Layer):

	## Default constructor.
	# @param agentList Initial list of agents in the layer.
	# @param name Name of the layer.
	# @param itLimit Number of iterations that the layer acts.
	def __init__(self, agentList=[], name="", itLimit=1):
		Layer.__init__(self,agentList,name)
		self.iterationLimit=itLimit
		self._it=0

	## Perform the action of all agents in the layer.
	# The data are modified by the actions of the agent.
	# @param data Data needed for the action. 
	def act(self, data):
		if self._it < self.iterationLimit:
			for a in self._agentList:
				a.act(data,self)   
			self._it+=1
			
	##@var iterationLimit
	# Number of iterations that the layer acts.
	##@var _it
	# Number of iterations performed.
	