##@package Example
# Example of agent-based system based on a supply and a demand curve
#@author Sebastien MATHIEU

from .agent import Agent
from .abstractSystem import AbstractSystem
from .layer import Layer
from .data import Data

import math

## Supply with the target supply function \f$\pi = 0.1 q^2 +2\f$
class Supply(Agent):
    def initialize(self, data):
        data.general['pi']=10.0 # Set a starting price
        
    def act(self, data, layer):
        # Compute the target price from the supply function
        targetPrice=0.1*(data.general['q']**2)+2 
        # Take the mean between the last price and the target price.
        data.general['pi']=(data.general['pi']+targetPrice)/2
        print("\tSupply propose the price " + str(data.general['pi'])

## Demand with the inverse demand function \f$\pi = 40 - 0.05 q^2\f$
class Demand(Agent):
    def initialize(self, data):
        data.general['q']=0 # Initial quantity bought
        
    def act(self, data, layer):
        pi=data.general['pi']
        if pi > 40.0: # Price to high, no demand
            data.general['q']=0
        else: # Demand function
            data.general['q']=math.sqrt((40.0-data.general['pi'])/0.05)
        print("\tDemand buy the quantity " + str(data.general['q']))

## Agent based system definition
class System(AbstractSystem):
    def __init__(self):
        AbstractSystem.__init__(self)
        self._lastPrice=None
        self.generate()
        
    ## Generate the example system.
    def generate(self):
        # Create actors
        supply=Supply()
        demand=Demand()
        
        # Create two layers with one actor in each.
        layerSupply=Layer([supply])
        layerDemand=Layer([demand])
        
        # Add the layers to the layer list
        self.layerList.append(layerDemand) # First the system call the demand side
        self.layerList.append(layerSupply) # After the system call the supply side
        
    def hasConverged(self):
        oldPrice=self._lastPrice
        self._lastPrice=self.data.general['pi']
        if oldPrice == None:
            return None
        elif abs(oldPrice - self._lastPrice) < 0.001: # Convergence if the price does not change.
            return "System has converged."
        else:
            return None
            
# Starting point from python #   
if __name__ == "__main__":
    system=System()
    print("Staring the agent-based simulation...")
    convergence=system.run()
    print("\nNumber of iterations : "+str(system.iterations))
    print(convergence)
    