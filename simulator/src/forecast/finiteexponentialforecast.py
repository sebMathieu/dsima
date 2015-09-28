##@package finiteexponentialforecast
#@author Sebastien MATHIEU

from .forecast import Forecast
from collections import deque

## Forecast by taking the exponential mean of the N last measurements.
class FiniteExponentialForecast(Forecast):
    
    ## Constructor.
    # @param x0 Initial state.
    # @param N Filtering window size.
    # @param discountFactor Discount factor.
    def __init__(self, x0=[0], N=5, discountFactor=0):
        Forecast.__init__(self,x0)
        self._N=N
        self._history=deque()
        self._history.appendleft(x0)
        self._discountFactor=discountFactor
        
    def measure(self, x):
        # Update history
        if len(self._history) == self._N:
            self._history.pop()
        self._history.appendleft(x)
            
        # Forecast
        M=len(x)
        self.x=[0]*M
        discount=1.0
        totalDiscount=0.0
        for e in self._history:
            for i in range(M):
                self.x[i]+=discount*e[i]
            totalDiscount+=discount
            discount*=self._discountFactor
        self.x=list(map(lambda x:x/totalDiscount,self.x))
    
    ## @var _history
    # History of the system.
    ## @var _N
    # Filtering window.
    ## @var _discountFactor
    # Discount factor.
    