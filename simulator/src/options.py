##@package options
#@author Sebastien MATHIEU
# List and define the option variables.

## Char to define a comment in the csv file.
COMMENT_CHAR='#'
## Log file.
LOG=None
## Print to screen.
PRINT_TO_SCREEN=True
## Debug mode.
DEBUG=False
## Copy agent parameter files instead of moving them. 
# Setting it to true may be hazardous in case of multiple calls of the simulator.
COPY=True 
## Operation folder.
FOLDER='operationFolder'
## Accuracy parameter.
EPS=0.00001
## Arbitrary big number
INF=10000
## Optimal power flow method:
#  - "networkFlow" or None: Traditional network flow with active powers.
#  - "linearOpf" : Linear approximation of the optimal power flow problems.
OPF_METHOD=None
## Solver name. By default uses scip. Alternative: cplex.
SOLVER = 'scip'
