##@package retailer
#@author Sebastien MATHIEU

import os,shutil, csv

from .agent.stateAgent import StateAgent
from .fsu import FSU
from .fsp import FSP
from .brp import BRP
from .ecbid import ECBid, ECObligationBid 
from . import options,tools

## Retailer agent.
class Retailer(StateAgent, FSU, FSP, BRP):
	## Name of the data file with the baselines.
	baselinesDataFile='retailer-baselines.dat'
	## Name of the data file with the submitted nodal total consumptions.
	submittedNodalTotalConsumptionsDataFile='retailer-submittedNodalTotalConsumptions.dat'
	
	## Constructor.
	# @param dataFile Data of the retailer. @see _dataFile
	# @param name Retailer's name. @see rename()
	def __init__(self,dataFile,name=""): 
		StateAgent.__init__(self,name)   
		self._dataFile=dataFile
	
	def initialize(self, data):
		StateAgent.initialize(self,data)
		self._readData(data)
		
		FSP.initialize(self,data)
		BRP.initialize(self,data)
		FSU.initialize(self,data)
		
		# Retailer data
		T=data.general['T']
		data.personal[self.name]['costs']=[0.0]
		
		# Override fsp obligations
		for n in self.nodes:
			data.personal[self.name]['alpha'][n]=[0]*T # Downward flexibility obligations ratio.
			data.personal[self.name]['beta'][n]=[data.general['interaction model'].consumptionFlexObligations]*T # Upward flexibility obligations ratio.
			
		# Status variable
		data.personal[self.name]['statusVariables'].append('costs')
	
	def act(self, data, layer):
		if layer.name == "Baseline optimization" or layer.name == "Baseline proposal":
			data.personal[self.name]['costs']=[0.0]
			self._optimizeBaseline(data,layer)
		elif layer.name == "Flexibility optimization":
			self.updateFlexibilityNeedsForecast(data)
			self._optimizeFlexibility(data)
		elif layer.name == "Flexibility activation requesting":
			self._flexibilityActivation(data)
		elif layer.name == "Imbalance optimization":
			self._optimizeImbalance(data)
		elif layer.name == "Settlement":
			self._settlement(data)
		else:
			raise Exception('Retailer \"%s\" has no action available for layer \"%s\".' % (self.name,layer))

	def referenceFlexPrice(self,n,t):
		return self.piR
	
	## Settlement.
	# @param data Data.
	def _settlement(self,data):
		FSP.settlement(self,data)
		BRP.settlement(self,data)
		
		# Benefits from retailing
		if options.DEBUG:
				tools.log("\t\t\tRetailing benefits of %s: %s" % (self.name,sum(data.personal[self.name]['P'])*self.piF), options.LOG, options.PRINT_TO_SCREEN)
		data.personal[self.name]['costs'][0]+=sum(data.personal[self.name]['P'])*self.piF
				 
	## Optimize the final imbalance of the retailer.
	# @param data Data.
	def _optimizeImbalance(self,data):
		self.writeBaselines(Retailer.baselinesDataFile,data)
		self.fetchFlexibilityActivationToProvide(data)
		self.writeFlexbilityActivationToProvide(data)
		self.writeFlexbilityActivated(data)
		
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/retailer.dat')
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/retailer.dat')
		
		# Optimize position
		try:
			BRP.optimizeImbalance(self,"retailer-imbalance",data)
			
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/retailer.dat',self._dataFile)
			
	## Activation of the contracted flexibility.
	# @param data Data.
	def _flexibilityActivation(self,data):		
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/retailer.dat')
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/retailer.dat')
	
		# Optimize position
		try:
			self.writeBaselines(Retailer.baselinesDataFile,data)
			self.writeFlexbilityToProvide(data)
			self.flexiblityActivationRequest("retailer-flexActivation",data)
						
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/retailer.dat',self._dataFile)
				
	## Evaluate and request the flexibility offers.
	# @param data Data.
	def flexibilityEvaluation(self, data):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/retailer.dat')
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/retailer.dat')
		
		# Optimize position
		try:
			self.writeBaselines(Retailer.baselinesDataFile,data)
			self.writeFlexbilityToProvide(data)
			self.flexiblityEvaluationAndRequest("retailer-flexEvaluation",data)
						
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/retailer.dat',self._dataFile)
				
	## Optimize the flexibility of the retailer.
	# @param data Data.
	def _optimizeFlexibility(self,data):
		T=data.general['T'] 
			
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/retailer.dat')
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/retailer.dat')
		
		# Optimize position
		try:
			solutionFile="retailer-flexibility.sol"
			self._writeNodalTotalConsumption(data)
			self.buildFlexPricesIndicators(T,data.general['R+'],data.general['R-'])
			self.writeFlexPricesIndicators(T)
			self.writeBaselines(Retailer.baselinesDataFile,data)
			self.writeFlexObligations(data)
			
			# Retrieve the solution file
			solver=data.general['solver']
			solver.solve("retailer-flexibility.zpl",solutionFile,cwd=options.FOLDER)
			solver.checkFeasible()
			
			# Parse the solution
			piE=data.general['pi^E']	 
			flexibilityPlatform=data.general['flexibilityPlatform']
			for n in self.nodes:
				# Global available flex
				fM=solver.variableVectorValue(T, 'fM#%s#'%n, 1)
				fP=solver.variableVectorValue(T, 'fP#%s#'%n, 1)
				totalVolume=sum(map(lambda x,y:x+y,fM,fP))
				
				# Reservation cost
				p0=solver.variableVectorValue(T, 'p0#%s#'%n, 1)
				shiftCosts=sum(map(lambda p,x,y:p*(x-y),piE,data.personal[self.name]['p^b'][n],p0))
				totalReservationCost=max(options.EPS,shiftCosts+self.piR*totalVolume/2)
				
				# Flexibility obligations
				obligations=solver.variableValue('obligations#%s'%n)
				if obligations > options.EPS:
					b=ECObligationBid(T, bus=n, owner=self)
					b.min=[-obligations]*T
					b.max=[obligations]*T
					b.reservationCost=max(options.EPS,((obligations*2*T)/totalVolume)*totalReservationCost)
					b.dsoReservationCost=options.EPS
					flexibilityPlatform.registerECBid(b,data)
				elif obligations < 0:
					obligations=0
				
				# Classic bid
				b=ECBid(T, bus=n, owner=self)
				b.min=list(map(lambda x: -x+obligations,fM))
				b.max=list(map(lambda x: x-obligations,fP))
				for t in range(T):
					if b.min[t] > -options.EPS:
						b.min[t]=0
					elif b.max[t] < options.EPS:
						b.max[t]=0
				if totalVolume <= options.EPS:
					b.reservationCost=options.EPS
				else:
					b.reservationCost=max(options.EPS,((totalVolume-obligations*2*T)/totalVolume)*totalReservationCost)
				b.dsoReservationCost=b.reservationCost
				flexibilityPlatform.registerECBid(b,data)
		
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/retailer.dat',self._dataFile)
				
	## Optimize the consumption strategy of the retailer.
	# @param data Data.
	# @param layer Layer
	def _optimizeBaseline(self, data,layer=None):
		T=data.general['T'] 

		# Restart dynamic bounds
		if (data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline" and layer.name == "Baseline proposal"
			) or (data.general['interaction model'].accessRestriction.lower() != "dynamicbaseline" and layer.name == "Baseline optimization"):
			self.resetDynamicRanges(data)

		# Write data
		self.buildFlexPricesIndicators(T,*self.getForecastedNeeds(data))
		self.writeFlexPricesIndicators(T)
		self.writeFlexObligations(data)

		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/retailer.dat')
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/retailer.dat')
		
		# Optimize position
		try:
			BRP.optimizeBaseline(self,'retailer-baseline',data,layer=layer)
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/retailer.dat',self._dataFile)
				if not os.path.isfile(self._dataFile):
					raise Exception(self._dataFile+' was not restored to the instance folder!')
	
	## Write the nodal total consumption based on the submitted baselines.
	def _writeNodalTotalConsumption(self,data):
		with open(options.FOLDER+'/'+Retailer.submittedNodalTotalConsumptionsDataFile, 'w') as file:
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n, D^b\n")
			for n in self.nodes:
				file.write("%s,%s\n" % (n, sum(data.personal[self.name]['p^b'][n])*data.general['dt']))
			
	## Read the data file of the retailer.
	# @param data Data.
	def _readData(self,data):
		T=data.general['T']
		accessBoundsComputation=data.general['interaction model'].accessBoundsComputation
		
		# clear
		self.nodes=[]
		self.piR=options.EPS
		data.personal[self.name]['E']=[0.0]*T
		data.personal[self.name]['k']={}
		data.personal[self.name]['K']={}
		data.personal[self.name]['l']={}
		data.personal[self.name]['L']={}
		
		# Fetch costs
		with open(self._dataFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			
			# Get first row
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			self.piR=float(row[1])*data.general['dt']
			self.piF=float(row[2])*data.general['dt']
			
			# Get second row, node list
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			for e in row:
				self.nodes.append(int(e))

			# Initialize access ranges
			for n in self.nodes:
				data.personal[self.name]['k'][n] = 0
				data.personal[self.name]['K'][n] = 0

			# Min and max consumptions 
			for n in self.nodes:
				for t in range(T):
					row = [options.COMMENT_CHAR]
					while row[0].startswith(options.COMMENT_CHAR):
						row = next(csvReader)

					if accessBoundsComputation is None or accessBoundsComputation.lower() != "installed":
						nIndex = int(row[0])
						data.personal[self.name]['k'][nIndex] = min(data.personal[self.name]['k'][nIndex], float(row[2]))
						data.personal[self.name]['K'][nIndex] = max(data.personal[self.name]['K'][nIndex], float(row[3]))
			
			# Get the installed capacity
			for n in self.nodes:
				row = [options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row = next(csvReader)
				if accessBoundsComputation is not None and accessBoundsComputation.lower() in ["installed","periodic"]:
					nIndex = int(row[0])
					data.personal[self.name]['k'][nIndex] = float(row[2])
					data.personal[self.name]['K'][nIndex] = float(row[3])

			# Get the external imbalance
			for t in range(T):
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)
				data.personal[self.name]['E'][t]=float(row[1])
				
			# Default full access bound are installed bounds.
			for n in self.nodes:
				data.personal[self.name]['l'][n]=data.personal[self.name]['k'][n]
				data.personal[self.name]['L'][n]=data.personal[self.name]['K'][n]

	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		s='\t<element id="%s" name="%s">\n'%(self.name,self.name)
		s+='\t\t<data id="costs">%s</data>\n'%data.personal[self.name]['costs'][0]
			
		s+=BRP.xmlData(self,data)
		s+=FSU.xmlData(self,data)
		s+=FSP.xmlData(self,data)
		
		s+='\t</element>\n'
		return s
	
	## @var _dataFile
	# CSV file with the fixed data of the problem.
	## @var nodes
	# List of nodes with flexible loads.
	## @var piR
	# Base reservation cost per period.
	## @var piF
	# Retailing price per period.
	
	
	