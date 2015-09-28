##@package interactionmodel
#@author Sebastien MATHIEU

import csv
from . import options

## Contains the options of the interaction model.
class InteractionModel:
	## Constructor.
	# @param filePath Optional path to the file with the parameters of the interaction model.
	def __init__(self, filePath=None):
		# Set default values
		self.DSOIsFSU=True
		self.DSOFlexCost="imbalance"
		self.productionFlexObligations=0.0
		self.consumptionFlexObligations=0.0
		self.DSOImbalancePriceRatio=100.0
		self.accessRestriction="none"
		self.accessBoundsComputation=None
		self.relativeDeviation=0.1

		if filePath is not None:
			self.load(filePath)
	
	## Load the parameters from a file.
	# @param filePath Path to the file with the parameters of the interaction model.
	def load(self,filePath):		
		# Read the file
		with open(filePath, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			for line in csvReader:
				# Remove comments
				if line[0].startswith(options.COMMENT_CHAR):
					continue
				
				# Check two arguments
				if len(line) != 2:
					raise Exception('Error parsing file "%s". Require 2 arguments and got "%s".'%(filePath,line))

				# retro-compatibility fix
				if line[0] == "prequalificationTimeWindow":
					line[0]="accessBoundsComputation"
				elif line[0] == "DSOAltCosts":
					if line[1].lower() in ["false","0","no"]:
						self.DSOFlexCost='normal'
					else:
						self.DSOFlexCost='full'
					continue
				elif line[0] == "nullAltCosts":
					if line[1].lower in ["true","1","yes"]:
						self.DSOFlexCost='imbalance'
					continue

				# Check existence, raise an error if the parameter does not exist.
				a=getattr(self, line[0])
				
				# Set the value
				v=line[1]
				if type(a) is float:
					v=float(v)
				elif type(a) is bool:
					v= v.lower() in ["true","1","yes"] 
				setattr(self, line[0], v)

	## @var DSOFlexCost
	#  Sets the cost at which the DSO buys flexibility. The implemented modes are:
	#  		- "imbalance": Only the imbalance is compensated
	#		- "normal":  Costs that consider that the energy has already been sold.
	# 					For instance for a 1MWh downward modulation of a producer getting green certificate, the marginal costs are -65 and the energy is sold at 40.
	# 					In this case the DSO buys the service at -25.
	#		- "full": Full reservation and activation costs.
	## @var DSOIsFSU
	# Boolean equal to true if the DSO is a FSU.
	## @var productionFlexObligations
	# Production flexibility obligations ratio.
	## @var consumptionFlexObligations
	#  Consumption flexibility obligations ratio.
	## @var DSOImbalancePriceRatio
	# Ratio of the imbalance price that is paid by the DSO in percent. Default value is 100, meaning the DSO paies for imbalance like every other actor.
	## @var accessRestriction
	# Type of access restriction of the grid user following the access agreement step of the DSO. Choices: "none","conservative","flexible".
	## @var accessBoundsComputation
	# Access bounds computation type. The value None corresponds to the default behavior which is "horizon".
	# Implemented modes:
	#	- "horizon" : Access bounds computation based on the maximum values observed by the grid user on the time horizon of the simulation.
	#	- "installed" : Access bounds computation based on the installed capacities.
	#	- "dynamic" : Bounds on the installed capacity and quarter-based restrictions from the DSO.
	# This option is implemented by the grid users themself in the way they announce their capacity needs [k,K].
	## @var relativeDeviation
	# Relative deviation from the submitted baselines allowed by the DSO and used to compute the dynamic ranges.
