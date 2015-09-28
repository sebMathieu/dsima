##@package instance
#@author Sebastien MATHIEU

import os, shutil
import csv
import random

from .timedata import TimeData

# Instance with its generation methods.
class Instance:
	## Numerical tolerance.
	EPS=0.00001
		
	## Constructor.
	# @param instanceParameters Parameters for the generation of the instance.
	# @param timeData Base annual data for the instance generation.
	# @param outputDirectory Output directory.
	def __init__(self,instanceParameters,timeData,outputDirectory=None):
		self.instanceParameters=instanceParameters
		if outputDirectory is None:
			self._path=instanceParameters.hash
		else:
			self._path='%s/%s'%(outputDirectory,instanceParameters.hash)
		self._generate(timeData)
	
	## Instance generation method
	# @param timeData Base annual data for the instance generation.
	def _generate(self,timeData):
		ip=self.instanceParameters
		
		# Deterministic random generation control
		random.seed(42)
		
		# Create output folders
		if not os.path.exists(self._path):
			os.makedirs(self._path)
		for d in ip.days:
			dayDirectory='%s/%s'%(self._path,d)
			if not os.path.exists(dayDirectory):
				os.makedirs(dayDirectory)
			
		# Network related
		shutil.copy('networks/%s/%s-image.svg'%(ip.network,ip.network),'%s/image.svg'%(self._path))
		for d in ip.days:
			shutil.copy('networks/%s/%s-network.csv'%(ip.network,ip.network),'%s/%s/network.csv'%(self._path,d))
		self._getDistribution()
		self._makeQualificationIndicators(timeData)
		
		# Producers and retailers
		self._makeProducers(timeData)
		self._makeRetailers(timeData)
		
		# Prices
		self._makePrices(timeData)
	
		# TSO
		self._makeTSO(timeData)
	
		# Interaction model
		self._makeInteractionModel()
	
	## Get the distribution of production and consumption in the network. 
	def _getDistribution(self):
		ip=self.instanceParameters
		COMMENT_CHAR='#'
		DELIMITER_CHAR=','
		
		with open('networks/%s/%s-distribution.csv'%(ip.network,ip.network), 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=DELIMITER_CHAR, quotechar='\"')
			
			# Total number of nodes
			row=[COMMENT_CHAR]
			while row[0].startswith(COMMENT_CHAR):
				row=next(csvReader)
			self._nodes=int(row[0])
			
			# Consumption distribution
			row=[COMMENT_CHAR]
			while row[0].startswith(COMMENT_CHAR):
				row=next(csvReader)
			nodes=int(row[0])
			
			self._consumptionDistribution={}
			for i in range(nodes):
				row=[COMMENT_CHAR]
				while row[0].startswith(COMMENT_CHAR):
					row=next(csvReader)
				self._consumptionDistribution[int(row[0])]=float(row[1])		
			
			# Production distribution
			row=[COMMENT_CHAR]
			while row[0].startswith(COMMENT_CHAR):
				row=next(csvReader)
			nodes=int(row[0])
			
			self._productionDistribution={}
			for i in range(nodes):
				row=[COMMENT_CHAR]
				while row[0].startswith(COMMENT_CHAR):
					row=next(csvReader)
				self._productionDistribution[int(row[0])]=float(row[1])		
	
	## Make the CSV files with the flexibility qualification indicator.
	# @param timeData Base annual data for the instance generation.
	def _makeQualificationIndicators(self,timeData):
		ip=self.instanceParameters
	
		# Write the file for each day
		for d in ip.days:
			dayDirectory='%s/%s/'%(self._path,d)
			with open('%s/qualified-flex.csv'%(dayDirectory), 'w') as file:
				file.write('# N\n%s\n'%self._nodes)
				file.write('# n, d+, d-\n')
				for n in range(self._nodes):
					if n==0:
						file.write('%s,%s,%s\n'%(n,Instance.EPS,Instance.EPS))
					else:
						maxFlexUpward=ip.consumption['mean']*ip.consumption['flexibility']
						maxFlexDownward=ip.production['max']*ip.production['flexibility']
						dU=Instance.EPS+1.0/(maxFlexUpward/10.0+maxFlexDownward/10.0+Instance.EPS)
						dD=Instance.EPS+1.0/(maxFlexUpward/1.0+maxFlexDownward/10.0+Instance.EPS)
						file.write('%s,%s,%s\n'%(n,dU,dD))

	## Make the CSV prices files.
	# @param timeData Base annual data for the instance generation.
	def _makePrices(self,timeData):
		#TODO should contains the value of lost load and production
		ip=self.instanceParameters
		dt=24.0/ip.T
		
		# Scale annual data
		initEPMean,initEPMax=TimeData.getMeanMax(timeData.energyPrices)
		scaledEnergyPrices=list(TimeData.adjustMeanMax(timeData.energyPrices, ip.prices['mean'], ip.prices['max']))
		
		initUIPMean,initUIPMax=TimeData.getMeanMax(timeData.upwardImbalancePrices)
		targetUIPMax=ip.prices['max']*initUIPMax/initEPMax
		scaledUpwardImbalancePrices=list(TimeData.adjustMeanMax(timeData.upwardImbalancePrices, ip.prices['mean']*initUIPMean/initEPMean, targetUIPMax))
		initDIPMean,initDIPMax=TimeData.getMeanMax(timeData.downwardImbalancePrices)
		targetDIPMax=ip.prices['max']*initDIPMax/initEPMax
		scaledDownwardImbalancePrices=list(TimeData.adjustMeanMax(timeData.downwardImbalancePrices, ip.prices['mean']*initDIPMean/initEPMean, targetDIPMax))
		
		# Computation of the local imbalance penalty
		localImbalancePenalty=1.5*max(targetUIPMax,targetDIPMax)

		# Write the price file for each day
		for d in ip.days:
			dayDirectory='%s/%s/'%(self._path,d)
			with open('%s/prices.csv'%(dayDirectory), 'w') as file:
				file.write('# T, EPS, pi^l, dt\n')
				file.write('%s, %s, %s, %s\n'%(ip.T, Instance.EPS,localImbalancePenalty, dt)) 
				
				file.write('# t, pi^E, pi^I+, pi^I-\n')
				for t in range(ip.T):
					piE=TimeData.periodValue(scaledEnergyPrices,(d-1)*ip.T+t,365*ip.T)
					piIU=TimeData.periodValue(scaledUpwardImbalancePrices,(d-1)*ip.T+t,365*ip.T)
					
					minImbalancePrice=max([Instance.EPS,piE+Instance.EPS,-piE+Instance.EPS])
					if piIU < minImbalancePrice:
						piIU=minImbalancePrice
					piID=TimeData.periodValue(scaledDownwardImbalancePrices,(d-1)*ip.T+t,365*ip.T)
					if piID < minImbalancePrice:
						piID=minImbalancePrice
					file.write('%s,%s,%s,%s\n'%(t+1,piE,piIU,piID))
 
	## Make a CSV file for each producer with its parameters.
	# @param timeData Base annual data for the instance generation.
	def _makeProducers(self,timeData):
		ip=self.instanceParameters
		
		# Assign a producer to each unit
		producerUnits=[[] for i in range(ip.producers)]
		for key in self._productionDistribution:
			producerUnits[random.randrange(ip.producers)].append(key)
		
		# Scale data
		totalProduction=list(TimeData.adjustMeanMax(timeData.windPower, ip.production['mean'], ip.production['max']))
		maxTotalProduction=max(totalProduction)

		# Write producers data
		for d in ip.days:
			# Create directory
			dayDirectory='%s/%s/producers'%(self._path,d)
			if not os.path.exists(dayDirectory):
				os.makedirs(dayDirectory)
			
			# For each producer, write its parameters
			for i in range(ip.producers):
				if not producerUnits[i]:
					# Do not create a producer with empty portfolio. As a result there may be less producers than expected.
					continue

				with open('%s/producer-%s.csv'%(dayDirectory,i), 'w') as file:
					file.write('# T, pi^r\n')
					file.write('%s,%s\n'%(ip.T,Instance.EPS))
					file.write('# Node set\n')
					file.write(",".join(map(str,producerUnits[i])))
					
					file.write('\n# n,t, p^min, p^max, c, piR\n')
					meanProduction=0.0
					for n in producerUnits[i]:
						for t in range(ip.T):
							pMax=self._productionDistribution[n]*TimeData.periodValue(totalProduction,(d-1)*ip.T+t,365*ip.T)
							pMax=max(0,pMax) # Ensure positive production
							pMin=pMax*(1.0-ip.production['flexibility'])
							piR=Instance.EPS # Reservation cost
							file.write('%s,%s,%s,%s,%s,%s\n'%(n,t+1,pMin,pMax,ip.production['costs'],piR))
				
							meanProduction+=pMax
					meanProduction/=ip.T
					
					file.write('# t, E\n')
					for t in range(ip.T):
						maxExternalImbalance=ip.production['externalimbalance']*meanProduction
						externalImbalance=random.uniform(-maxExternalImbalance,maxExternalImbalance)
						file.write('%s,%s\n'%(t+1,externalImbalance))

					file.write('# n, g, G\n')
					for n in producerUnits[i]:
						file.write('%s,0,%s\n'%(n,maxTotalProduction*self._productionDistribution[n]))
						
	## Make a CSV file for each producer with its parameters.
	# @param timeData Base annual data for the instance generation.
	def _makeRetailers(self,timeData):
		ip=self.instanceParameters
		
		# Retailer share for each consumption node
		shares=[{} for i in range(ip.retailers)]
		for key in self._consumptionDistribution:
			totalRand=0
			for i in range(ip.retailers):
				r=random.random()
				totalRand+=r
				shares[i][key]=r
			for i in range(ip.retailers):
				shares[i][key]/=totalRand
		
		# Compute the total base consumption in the network by scaling the orginal load consumption data
		totalBase=list(TimeData.adjustMeanMax(timeData.load, ip.consumption['mean'], ip.consumption['max']))
		minTotalBase=min(totalBase)
		maxTotalBase=max(totalBase)

		# Write retailers data
		for d in ip.days:
			# Create directory
			dayDirectory='%s/%s/retailers'%(self._path,d)
			if not os.path.exists(dayDirectory):
				os.makedirs(dayDirectory)
				
			# Get the total energy need for each node
			energyNeeds={}
			for n,part in self._consumptionDistribution.items():
				energyNeeds[n]=0.0
				for t in range(ip.T):
					energyNeeds[n]+=part*TimeData.periodValue(totalBase,(d-1)*ip.T+t,365*ip.T)*(24.0/ip.T)
			
			# For each retailer, write its parameters
			for i in range(ip.retailers):
				with open('%s/retailer-%s.csv'%(dayDirectory,i), 'w') as file:
					file.write('# T, pi^r, pi^f\n')
					file.write('%s,%s,%s\n'%(ip.T,ip.consumption['flexreservationcost'], ip.consumption['benefits'])) #TODO value of pi^r
					file.write('# Node set\n')
					file.write(",".join(map(str,[x for x in shares[i]])))
					
					meanConsumption=0
					file.write('\n# # n,t, p^min, p^max\n')
					for n in shares[i]:
						for t in range(ip.T):
							# Flexibility band around the mean total static consumption/share of the retailer
							pBase=-shares[i][n]*self._consumptionDistribution[n]*TimeData.periodValue(totalBase,(d-1)*ip.T+t,365*ip.T)
							pMin=pBase*(1+ip.consumption['flexibility'])
							pMax=pBase*(1-ip.consumption['flexibility'])
							# Ensure min/max if production instead of consumption
							file.write('%s,%s,%s,%s\n'%(n,t+1,min(pMin,pMax),max(pMin,pMax))) 
							
							meanConsumption+=pBase
					meanConsumption/=ip.T
					
					file.write('# n, D, g, G\n')
					for n in shares[i]:
						extremeCases=[0.0,-shares[i][n]*minTotalBase,-shares[i][n]*maxTotalBase]
						file.write('%s,%s,%s,%s\n'%(n,-shares[i][n]*energyNeeds[n],min(extremeCases),max(extremeCases)))				
					
					file.write('# t, E\n')
					for t in range(ip.T):
						maxExternalImbalance=ip.consumption['externalimbalance']*meanConsumption
						externalImbalance=random.uniform(-maxExternalImbalance,maxExternalImbalance)
						file.write('%s,%s\n'%(t+1,externalImbalance))
						
	## Make a CSV file for each producer with its parameters.
	# @param timeData Base annual data for the instance generation.
	def _makeTSO(self,timeData):
		ip=self.instanceParameters
		
		for d in ip.days:
			dayDirectory='%s/%s/'%(self._path,d)
			with open('%s/tso.csv'%(dayDirectory), 'w') as file:
				file.write('# T, pi^S+, pi^S-\n')
				file.write('%s,%s,%s\n'%(ip.T,ip.tsoReservationPrice,-ip.tsoReservationPrice))
				
				file.write('# t, R+, R-, E\n')
				for t in range(ip.T):
					upwardFlexNeeds=ip.tsoFlexibilityRequest
					downwardFlexNeeds=-upwardFlexNeeds

					# Generate and imbalance of the same sign than the annual data
					externalImbalance=TimeData.periodValue(timeData.systemImbalance,(d-1)*ip.T+t,365*ip.T)
					if externalImbalance > 0:
						externalImbalance=random.uniform(downwardFlexNeeds,0)
					else:
						externalImbalance=random.uniform(0,upwardFlexNeeds)

					file.write('%s,%s,%s,%s\n'%(t+1,upwardFlexNeeds,downwardFlexNeeds,externalImbalance))
	
	## Make the CSV with the interaction model's parameter.
	def _makeInteractionModel(self):
		ip=self.instanceParameters
		
		for d in ip.days:
			dayDirectory='%s/%s/'%(self._path,d)
			with open('%s/interaction-model.csv'%dayDirectory, 'w') as file:
				for p in ip.imParameters:
					file.write('%s,%s\n'%(p[0],p[1]));
		
	## @var instanceParameters
	# Parameters for the generation of the instance.
	## @var _path
	# Output path.
	## @var _nodes
	# Number of nodes in the selected network.
	## @var _productionDistribution
	# Dictionary with for a node its relative contribution to the total production.
	## @var _consumptionDistribution
	# Dictionary with for a node its relative contribution to the total consumption.
	