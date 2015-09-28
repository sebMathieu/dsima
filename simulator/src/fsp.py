##@package fsp
#@author Sebastien MATHIEU

from .forecast.finiteexponentialforecast import FiniteExponentialForecast
from . import options,tools,xmlsolution

## Flexibility services provider
# Needed to inherit from a state agent and have the following properties:
#	- name
#	- 'costs' personal data
#	-  nodes, a list of nodes to consider
# The method initialize should be called in the state agent initialization phase.
class FSP:
	## Name of the data file with the flexibility prices indicators.
	flexIndicatorsDataFile='flexIndicators.dat'
	## Name of the data file with the flexibility bids.
	flexDataFile='flexBids.dat'
	# Name of the data file with accepted flexibility.
	flexToActivatedDataFile='flexToActivate.dat'
	## Name of the data file with the flexibility obligations ratios.
	flexObligationsDataFile='flexObligations.dat'

	# Initialization procedure of the internal data.
	# @param data Global data set.
	def initialize(self, data):
		T=data.general['T']
		
		self.flexPricesIndicatorsP={}
		self.flexPricesIndicatorsM={}
		self.fP={}
		self.fM={}
		data.personal[self.name]['alpha']={} # Downward flexibility obligations ratio.
		data.personal[self.name]['beta']={} # Upward flexibility obligations ratio.
		data.personal[self.name]['bsp']={} # Is a balance service provider for each node and each period
		for n in self.nodes:
			data.personal[self.name]['alpha'][n]=[0.0]*T
			data.personal[self.name]['beta'][n]=[0.0]*T
			data.personal[self.name]['bsp'][n]=[0.0]*T
		
		# Flexible needs forecast
		self.flexNeedsForecast=FiniteExponentialForecast([0.0]*(2*len(self.nodes)*T))
		needs=[]
		for n in self.nodes:
			needs.extend([0.0]*(2*T))
			self.flexPricesIndicatorsP[n]=[0.01]*T
			self.flexPricesIndicatorsM[n]=[0.01]*T
			self.fP[n]=[0.0]*T
			self.fM[n]=[0.0]*T
		
		# Status variables
		data.personal[self.name]['flexNeedsForecast']=needs
		data.personal[self.name]['statusVariables'].append('flexNeedsForecast')

	## Settlement.
	# @param data Data.
	def settlement(self,data):
		# Compute the imbalance wrt to flex services provision nodes
		nonDeliveredCosts=0
		for t in range(data.general['T']):
			if data.general['Shed quantities'][t] > options.EPS:
				for n in self.nodes:
					if data.personal[self.name]['bsp'][n][t] > options.EPS and (self._iP[n][t] > options.EPS or self._iM[n][t] > options.EPS) :
						nonDeliveredCosts+=(self._iP[n][t]+self._iM[n][t])*data.general['pi^i']

		data.personal[self.name]['costs'][0]+=nonDeliveredCosts
		data.personal['DSO']['costs'][0]-=nonDeliveredCosts

		# Dynamic ranges restrictions
		dynamicRangesCosts=0
		for n in self.nodes:
			for t in range(data.general['T']):
				dynamicRangesCosts+=(max(0,data.personal[self.name]['p'][n][t]-data.personal[self.name]['D'][n][t])+max(0,data.personal[self.name]['d'][n][t]-data.personal[self.name]['p'][n][t]))*data.general['pi^i']
		
		data.personal[self.name]['costs'][0]+=dynamicRangesCosts
		data.personal['DSO']['costs'][0]-=dynamicRangesCosts
		
	## Get the reference flexibility price of the FSP.
	# The children shoud implement this method.
	# @param n node.
	# @param t period.
	def referenceFlexPrice(self,n,t):
		return 0.0
		
	## Build the flexibility prices indicators based on the new data.
	# @param T Number of periods.
	# @param upwardNeeds Upward flexibility needs for each flexible nodes and each periods.
	# @param downwardNeeds Downward flexibility needs for each flexible nodes and each periods.
	def buildFlexPricesIndicators(self,T,upwardNeeds,downwardNeeds):
		for n in self.nodes:
			# Obtain the flexibility needs by nodes
			rU=upwardNeeds[n]
			rL=downwardNeeds[n]
			
			sumRU=sum(map(abs,rU))+options.EPS*T
			sumRL=sum(map(abs,rL))+options.EPS*T
			
			# Build indicators
			for t in range(T):
				if rU[t] > options.EPS:
					self.flexPricesIndicatorsP[n][t]=(self.referenceFlexPrice(n,t)*rU[t]+options.EPS)/sumRU
				else:
					self.flexPricesIndicatorsP[n][t]=options.EPS
					
				if rL[t] < -options.EPS:
					self.flexPricesIndicatorsM[n][t]=(-self.referenceFlexPrice(n,t)*rL[t]+options.EPS)/sumRL
				else:
					self.flexPricesIndicatorsM[n][t]=options.EPS 
	
	## Get the forecasted needs for each flexible nodes and each periods
	# @param data Data.
	# @return Forecasted needs upward and downward in a two elements list.
	def getForecastedNeeds(self, data):
		T=data.general['T']
		fc=self.flexNeedsForecast.x
		data.personal[self.name]['flexNeedsForecast']=fc
		upwardNeeds={}
		downwardNeeds={}
		i=0
		for n in self.nodes:
			upwardNeeds[n]=fc[i:i+T]
			i+=T
			downwardNeeds[n]=fc[i:i+T]
			i+=T
		return [upwardNeeds,downwardNeeds]
	
	## Fetch the flexibility activation requests.
	# @param data
	def fetchFlexibilityActivationToProvide(self,data):
		T=data.general['T']
		flexPlatform=data.general['flexibilityPlatform']
		
		data.personal[self.name]['h']={} # flexibility request
		data.personal[self.name]['H']=[0.0]*T # Total flexibility activated
		data.personal[self.name]['bsp']={} # Is a balance service provider for each node and each period
		for n in self.nodes:
			data.personal[self.name]['h'][n]=[0.0]*T
			data.personal[self.name]['bsp'][n]=[0.0]*T
		
		# Fetch single periods
		spBidList=flexPlatform.getAcceptedSPBids(self)
		for b in spBidList:
			n=b.bus
			t=b.t
			data.personal[self.name]['bsp'][n][t]=1.0 # TODO this should be true only if the buyer is the bsp
			data.personal[self.name]['h'][n][t]+=b.modulation
			data.personal[self.name]['H'][t]+=b.modulation
			data.personal[self.name]['costs'][0]-=b.reservationBenefits
			data.personal[self.name]['costs'][0]-=b.activationBenefits # TODO not correct in case of alternative costs
		
		# Fecth ec bids
		ecBidList=flexPlatform.getAcceptedECBids(self)
		for b in ecBidList:
			n=b.bus
			data.personal[self.name]['costs'][0]-=b.reservationBenefits
			for t in range(T):
				data.personal[self.name]['bsp'][n][t]=1.0 # TODO this should be true only if the buyer is the bsp
				data.personal[self.name]['h'][n][t]+=b.modulation[t]
				data.personal[self.name]['H'][t]+=b.modulation[t]
				data.personal[self.name]['costs'][0]-=b.activationBenefits

	## Reset the personal dynamic ranges.
	# @param data Data.
	def resetDynamicRanges(self,data):
		T=data.general['T']
		for n in self.nodes:
			data.personal[self.name]['d'][n]=[data.personal[self.name]['k'][n]]*T
			data.personal[self.name]['D'][n]=[data.personal[self.name]['K'][n]]*T

	## Write the flexibility activation to provide to a data file.
	# The flexibility activation should be fetched first.
	# @see fetchFlexibilityActivationToProvide .
	# @param data Data.
	def writeFlexbilityActivationToProvide(self,data):
		T=data.general['T'] 
		with open(options.FOLDER+'/'+FSP.flexToActivatedDataFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n, t, h, bsp, d, D\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s,%s,%s,%s\n" % (n,t+1, data.personal[self.name]['h'][n][t], data.personal[self.name]['bsp'][n][t],
						   								data.personal[self.name]['d'][n][t],data.personal[self.name]['D'][n][t]))
			file.write("# n, k, K, l, L\n")
			for n in self.nodes:
				file.write("%s,%s,%s,%s,%s\n" % (n,data.personal[self.name]['k'][n],data.personal[self.name]['K'][n],
												 data.personal[self.name]['l'][n],data.personal[self.name]['L'][n]))
		
	## Write flexibility obligations.
	# @param data Data.
	def writeFlexObligations(self,data):
		T=data.general['T']
		with open(options.FOLDER+'/'+FSP.flexObligationsDataFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n, t, alpha, beta, d, D\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s,%s,%s,%s\n" % (n,t+1, data.personal[self.name]['alpha'][n][t], data.personal[self.name]['beta'][n][t],
						   						data.personal[self.name]['d'][n][t],data.personal[self.name]['D'][n][t]))
			file.write("# n, k, K, l, L\n")
			for n in self.nodes:
				file.write("%s,%s,%s,%s,%s\n" % (n,data.personal[self.name]['k'][n],data.personal[self.name]['K'][n],
												 data.personal[self.name]['l'][n],data.personal[self.name]['L'][n]))
	
	## Write the flexibility to provide to a data file.
	# The flexibility to provide should be fetched first.
	# @see fetchFlexbilityToProvide .
	# @param data Data.
	def writeFlexbilityToProvide(self,data):
		T=data.general['T'] 
		with open(options.FOLDER+'/'+FSP.flexDataFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n, t, f^+, f^-, d, D\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s,%s,%s,%s\n" % (n,t+1, self.fP[n][t], self.fM[n][t],
						   								data.personal[self.name]['d'][n][t],data.personal[self.name]['D'][n][t]))
			file.write("# n, k, K, l, L\n")
			for n in self.nodes:
				file.write("%s,%s,%s,%s,%s\n" % (n,data.personal[self.name]['k'][n],data.personal[self.name]['K'][n],
													   data.personal[self.name]['l'][n],data.personal[self.name]['L'][n]))
			 
	## Write a data file with the flexibility prices indicators.
	# @param T Number of periods.
	def writeFlexPricesIndicators(self,T):
		with open(options.FOLDER+'/'+FSP.flexIndicatorsDataFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n,t, pi^f+, pi^f-\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s,%s\n" % (n,t+1, self.flexPricesIndicatorsP[n][t], self.flexPricesIndicatorsM[n][t]))
					
	## Provide the flexibility needs to the forecast for the next rounds.
	# @param data Data.
	def updateFlexibilityNeedsForecast(self, data):
		measurements=[]
		for n in self.nodes:
			measurements.extend(data.general['R+'][n])
			measurements.extend(data.general['R-'][n])
		self.flexNeedsForecast.measure(measurements)

	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		T=data.general['T']
		dt=data.general['dt']
		s=""

		# Flexibility graph
		s+='\t<timegraph id="fsp" title="" ylabel="Power [MW]">\n'
		for attr in ['H']:
			s+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		s+='\t</timegraph>\n'
		
		return s

	## @var flexPricesIndicatorsP
	# Dictionary of T upward flexibility prices indicators where the key are the flexible nodes.
	## @var flexPricesIndicatorsM
	# Dictionary of T downward flexibility prices indicators where the key are the flexible nodes.
	## @var fP
	# Positive flexibility to provide for each flexible node and each period.
	## @var fM
	# Positive flexibility to provide for each flexible node and each period.
	## @var flexNeedsForecast
	# Forecasts of the flexibility needs for each node and each period.
	# The state list has the following form : [forecasts flexible node 1,forecasts flexible node 2, ...].
	