##@package data
#@author Sebastien MATHIEU

## Class handling the data of the system.
class Data:
    
    ## Default constructor.
    def __init__(self):
        self.general={}
        self.personal={}
        
    ## @var general
    # Dictionary "variable name - value".
    
    ## @var personal
    # Dictionary where the key is the id of the user and the value a dictionary of variables.
    # @see Data.general
    