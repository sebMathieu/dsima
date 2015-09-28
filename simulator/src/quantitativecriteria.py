##@package quantitativecriteria
#@author Sebastien MATHIEU

from .agent.stateAgent import StateAgent
from . import tools,options

from .dso import DSO
from .tso import TSO
from .retailer import Retailer
from .producer import Producer

## Agent which evaluates quantitatively the state of the system.
class QuantitativeCriteria(StateAgent):
    
    ## Constructor
    # @param name Name. @see rename()
    def __init__(self,name="Quantitative criteria"): 
        StateAgent.__init__(self,name)   
        self._users=[]
    
    ## Clear the criteria base.
    def clear(self,data):
        self._users=[]
        data.personal[self.name]['welfare']=[0.0]
        data.personal[self.name]['dsosCosts']=[0.0]
        data.personal[self.name]['sheddingCosts']=[0.0]
        data.personal[self.name]['tsosCosts']=[0.0]
        data.personal[self.name]['producersCosts']=[0.0]
        data.personal[self.name]['retailersCosts']=[0.0]
        
    def initialize(self, data):
        StateAgent.initialize(self,data)
        data.personal[self.name]['welfare']=[0.0]
        data.personal[self.name]['dsosCosts']=[0.0]
        data.personal[self.name]['sheddingCosts']=[0.0]
        data.personal[self.name]['tsosCosts']=[0.0]
        data.personal[self.name]['producersCosts']=[0.0]
        data.personal[self.name]['retailersCosts']=[0.0]
        data.personal[self.name]['statusVariables'].extend(('welfare','dsosCosts','sheddingCosts','tsosCosts','producersCosts','retailersCosts'))
    
    ## Register a user for the quantification.
    # @param name User's name.
    # These users should own the following personal variables:
    #   - costs
    def registerUser(self,name):
        self._users.append(name)
        
    def act(self,data,layer):
        data.personal[self.name]['welfare']=[0.0]
        data.personal[self.name]['dsosCosts']=[0.0]
        data.personal[self.name]['sheddingCosts']=[0.0]
        data.personal[self.name]['tsosCosts']=[0.0]
        data.personal[self.name]['producersCosts']=[0.0]
        data.personal[self.name]['retailersCosts']=[0.0]
        for u in self._users:
            data.personal[self.name]['welfare'][0]-=data.personal[u.name]['costs'][0]
            if isinstance(u, DSO):
                data.personal[self.name]['dsosCosts'][0]+=data.personal[u.name]['costs'][0]
                data.personal[self.name]['sheddingCosts'][0]+=data.personal[u.name]['Shedding costs']
            elif isinstance(u, TSO):
                data.personal[self.name]['tsosCosts'][0]+=data.personal[u.name]['costs'][0]
            elif isinstance(u, Producer):
                data.personal[self.name]['producersCosts'][0]+=data.personal[u.name]['costs'][0]
            elif isinstance(u, Retailer):
                data.personal[self.name]['retailersCosts'][0]+=data.personal[u.name]['costs'][0]
        data.personal[self.name]['welfare'][0]-=data.personal[self.name]['sheddingCosts'][0]

        if options.DEBUG:
            tools.log("\tWelfare : %s." % (data.personal[self.name]['welfare']), options.LOG, options.PRINT_TO_SCREEN)
            tools.log("\tDSOs costs : %s." % (data.personal[self.name]['dsosCosts']), options.LOG, options.PRINT_TO_SCREEN)
            tools.log("\tTSOs costs : %s." % (data.personal[self.name]['tsosCosts']), options.LOG, options.PRINT_TO_SCREEN)
            tools.log("\tProducers costs : %s." % (data.personal[self.name]['producersCosts']), options.LOG, options.PRINT_TO_SCREEN)
            tools.log("\tRetailers costs : %s." % (data.personal[self.name]['retailersCosts']), options.LOG, options.PRINT_TO_SCREEN)
    
    ## @var _users
    # List of users to monitor to compute the welfare.
    # These users should own the following personal variables:
    #   - costs
    