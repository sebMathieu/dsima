##@package producer
#@author Sebastien MATHIEU

import os,shutil, csv

from .agent.stateAgent import StateAgent
from .fsu import FSU
from .fsp import FSP
from .brp import BRP
from . import options,tools
from .spbid import SPBid, SPObligationBid

## Producer agent.
class Producer(StateAgent,FSU,FSP,BRP):
	## Name of the data file with the baselines.
	baselinesDataFile='producer-baselines.dat'
	
	## Constructor.
	# @param dataFile Data of the producer. @see _dataFile
	# @param name Producer's name. @see rename()
	def __init__(self,dataFile,name=""): 
		StateAgent.__init__(self,name)  
		self._dataFile=dataFile
		
		
	def initialize(self, data):
		StateAgent.initialize(self,data)
		self._readData(data)
		
		FSP.initialize(self,data)
		BRP.initialize(self,data)
		FSU.initialize(self,data)
		
		# Producer data
		T=data.general['T']
		data.personal[self.name]['costs']=[0.0]
		
		# Override fsp obligations
		for n in self.nodes:
			data.personal[self.name]['alpha'][n]=[data.general['interaction model'].productionFlexObligations]*T # Downward flexibility obligations ratio.
			data.personal[self.name]['beta'][n]=[0.0]*T # Upward flexibility obligations ratio.

		# Initialize flexible nodes dependent data
		self._avp={}
		for n in self.nodes:			
			self._avp[n]=[0.0]*T
			
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
			raise Exception('Producer \"%s\" has no action available for layer \"%s\".' % (self.name,layer))
		
	def referenceFlexPrice(self,n,t):
		return self._piR[n][t]
	
	## Settlement
	# @param data Data.
	def _settlement(self,data):
		FSP.settlement(self,data)
		BRP.settlement(self,data)

		# Production costs
		T=data.general['T'] 
		for n in self.nodes:
			for t in range(T):
				data.personal[self.name]['costs'][0]+=data.personal[self.name]['p'][n][t]*self._c[n][t]


	## Optimize the final imbalance of the producer.
	# @param data Data.
	def _optimizeImbalance(self,data):
		self.writeBaselines(Producer.baselinesDataFile,data)
		self.fetchFlexibilityActivationToProvide(data)
		self.writeFlexbilityActivationToProvide(data)
		self.writeFlexbilityActivated(data)
			
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/producer.dat')
		else: # Rename instead of copy if debug
			shutil.move(self._dataFile,options.FOLDER+'/producer.dat')
		
		# Optimize position
		try:
			self.optimizeImbalance("producer-imbalance",data)
						
		finally: # Move back the data file
			if not options.COPY:
				shutil.copy(options.FOLDER+'/producer.dat',self._dataFile)
				
	## Activation of the contracted flexibility.
	# @param data Data.
	def _flexibilityActivation(self,data):		
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/producer.dat')
		else: # Rename instead of copy if debug
			shutil.move(self._dataFile,options.FOLDER+'/producer.dat')
	
		# Optimize position
		try:
			self.writeBaselines(Producer.baselinesDataFile,data)
			self.writeFlexbilityToProvide(data)
			self.flexiblityActivationRequest("producer-flexActivation",data)
						
		finally: # Move back the data file
			if not options.COPY:
				shutil.copy(options.FOLDER+'/producer.dat',self._dataFile)
		
	## Evaluate and request the flexibility offers.
	# @param data Data.
	def flexibilityEvaluation(self, data):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/producer.dat')
		else: # Rename instead of copy if debug
			shutil.move(self._dataFile,options.FOLDER+'/producer.dat')
		
		# Optimize position
		try:
			self.writeBaselines(Producer.baselinesDataFile,data)
			self.writeFlexbilityToProvide(data)
			self.flexiblityEvaluationAndRequest("producer-flexEvaluation",data)
						
		finally: # Move back the data file
			if not options.COPY:
				shutil.copy(options.FOLDER+'/producer.dat',self._dataFile)
				
	## Optimize the flexibility of the producer.
	# @param data Data.
	def _optimizeFlexibility(self,data):
		T=data.general['T'] 
			
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/producer.dat')
		else: # Rename instead of copy if debug
			shutil.move(self._dataFile,options.FOLDER+'/producer.dat')
		
		# Optimize position
		try:
			solutionFile="producer-flexibility.sol"
			self.buildFlexPricesIndicators(T,data.general['R+'],data.general['R-'])
			self.writeFlexPricesIndicators(T)
			self.writeBaselines(Producer.baselinesDataFile,data)
			self.writeFlexObligations(data)
				
			# Retrieve the solution
			solver=data.general['solver']
			solver.solve("producer-flexibility.zpl",solutionFile,cwd=options.FOLDER)
			solver.checkFeasible()
			
			# Parse the solution			
			flexibilityPlatform=data.general['flexibilityPlatform']
			piE=data.general['pi^E']
			for n in self.nodes:
				self.fM[n]=list(map(lambda x: -x,solver.variableVectorValue(T, 'fM#%s#'%n, 1)))
				self.fP[n]=solver.variableVectorValue(T, 'fP#%s#'%n, 1)
				
				# Split in bids
				for t in range(T):
					if self.fM[n][t] < -options.EPS:
						# Flexibility obligations
						obligation=min(0,-data.personal[self.name]['alpha'][n][t]*data.personal[self.name]['p^b'][n][t],
									   data.personal[self.name]['L'][n]-data.personal[self.name]['p^b'][n][t])
						if obligation < -options.EPS:
							dsoCost=self._c[n][t]+piE[t]
							if data.general['interaction model'].DSOFlexCost in ["imbalance"]:
								dsoCost=-options.EPS
							ob=SPObligationBid(t, bus=n,rc=self._piR[n][t],ac=self._c[n][t],owner=self, dsoRc=options.EPS,dsoAc=dsoCost)
							ob.min=obligation
							flexibilityPlatform.registerSPBid(ob,data)
						
						# Submit usual flexibility offer
						if self.fM[n][t]-obligation < -options.EPS:
							dsoCost=self._c[n][t]+piE[t]
							if data.general['interaction model'].DSOFlexCost in ["full"]:
								dsoCost=self._c[n][t]
							b=SPBid(t,bus=n,rc=self._piR[n][t],ac=self._c[n][t],dsoRc=self._piR[n][t],dsoAc=dsoCost,owner=self)
							b.min=self.fM[n][t]-obligation
							flexibilityPlatform.registerSPBid(b,data)

					if self.fP[n][t] > options.EPS:
						b=SPBid(t,bus=n,rc=self._piR[n][t],ac=self._c[n][t],dsoRc=self._piR[n][t],dsoAc=self._c[n][t],owner=self)
						b.max=self.fP[n][t]
						flexibilityPlatform.registerSPBid(b,data)
						
		finally: # Move back the data file
			if not options.COPY:
				shutil.copy(options.FOLDER+'/producer.dat',self._dataFile)
	
	## Optimize the consumption strategy of the producer.
	# @param data Data.
	# @param layer Layer
	def _optimizeBaseline(self, data, layer=None):
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
			tools.safeCopy(self._dataFile,options.FOLDER+'/producer.dat')
		else: # Rename instead of copy if debug
			shutil.move(self._dataFile,options.FOLDER+'/producer.dat')
		
		# Optimize position
		try:
			BRP.optimizeBaseline(self,'producer-baseline',data,layer=layer)
		finally: # Move back the data file
			if not options.COPY:
				shutil.copy(options.FOLDER+'/producer.dat',self._dataFile)
	
	## Read the data file of the producer.
	# @param data Data.
	def _readData(self,data):
		T=data.general['T']
		accessBoundsComputation=data.general['interaction model'].accessBoundsComputation
		
		# clear
		self.nodes=[]
		self._c={}
		self._piR={}
		data.personal[self.name]['E']=[0.0]*T
		data.personal[self.name]['k']={}
		data.personal[self.name]['K']={}
		data.personal[self.name]['l']={}
		data.personal[self.name]['L']={}
		
		# Fetch data in the data file
		with open(self._dataFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			
			# Get first row
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			
			# Get second row, node list
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			for e in row:
				self.nodes.append(int(e))

			# Initialize access ranges
			for n in self.nodes:
				self._c[n]=[0.0]*T
				self._piR[n]=[options.EPS]*T
				data.personal[self.name]['k'][n]=0.0
				data.personal[self.name]['K'][n]=0.0
			
			# Get the marginal costs
			for n in self.nodes:
				for t in range(T):
					row=[options.COMMENT_CHAR]
					while row[0].startswith(options.COMMENT_CHAR):
						row=next(csvReader)

					nIndex = int(row[0])
					if accessBoundsComputation is None or accessBoundsComputation.lower() != "installed":
						data.personal[self.name]['k'][nIndex]=min(data.personal[self.name]['k'][nIndex], float(row[2]))
						data.personal[self.name]['K'][nIndex]=max(data.personal[self.name]['K'][nIndex], float(row[3]))

					self._c[nIndex][t]=float(row[4])*data.general['dt']
					self._piR[nIndex][t]=float(row[5])*data.general['dt']
					
			# Get the external imbalance
			for t in range(T):
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)
				data.personal[self.name]['E'][t]=float(row[1])

			# Installed capacity bounds
			for n in self.nodes:
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)
				if accessBoundsComputation is not None and accessBoundsComputation.lower() in ["installed","periodic"]:
					nIndex = int(row[0])
					data.personal[self.name]['k'][nIndex]=float(row[1])
					data.personal[self.name]['K'][nIndex]=float(row[2])

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
	# List of nodes with flexible production units.
	## @var _c
	# Marginal cost for each node and each period.
	## @var _piR
	# Base reservation cost for each node and each period.
	