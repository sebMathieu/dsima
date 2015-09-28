##@package forecast
#@author Sebastien MATHIEU

## Skeleton of a forecast.
# This forecast takes as state the last measurement.
class Forecast(object):
    # Constructor
    # @param x0 Initial state.
    def __init__(self, x0=[0]):
    	self.initialize(x0)
        
	# Initialize the forecast.
	# @param x0 Initial state.
    def initialize(self, x0=[0]):
        self.x=x0

	# Provide the last measurement to predict the next state.
	# @param x Measured state.
    def measure(self, x):
        self.x=x
        
    ## @var x
    # Predicted state. 
