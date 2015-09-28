##@package dso
#@author Sebastien MATHIEU

import os,shutil, csv

from .agent.stateAgent import StateAgent
from .fsu import FSU
from . import tools,options,xmlsolution

## Transmission system operator
class TSO(StateAgent, FSU):
	## Name of the data file with the needs of the TSO.
	needsFile='tso.dat'
	
	## Constructor.
	# @param dataFile Data file with the needs of the TSO.
	# @param name TSO's name. @see rename()
	def __init__(self,dataFile,name="TSO"): 
		StateAgent.__init__(self,name)   
		self._dataFile=dataFile
				
	def initialize(self, data):
		StateAgent.initialize(self,data)
		
		self.N=data.general['N']
		self.nodes=list(range(self.N))
		FSU.initialize(self,data)
		
		# Fetch flexibility needs
		T=data.general['T']
		data.personal[self.name]['R+']=[0.0]*T
		data.personal[self.name]['R-']=[0.0]*T
		data.personal[self.name]['E']=[0.0]*T
		data.personal[self.name]['I']=[0.0]*T
		data.general['SI']=[0.0]*T
		with open(self._dataFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			
			# Get first row
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			data.personal[self.name]['pi^S+']=float(row[1])*data.general['dt'] 
			data.personal[self.name]['pi^S-']=float(row[2])*data.general['dt'] 
				
			for i in range(T):
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)
				t=int(row[0])-1
				data.personal[self.name]['R+'][t]=float(row[1])
				data.personal[self.name]['R-'][t]=float(row[2])
				data.personal[self.name]['E'][t]=float(row[3])
				data.general['SI'][t]=-data.personal[self.name]['E'][t]
				
		# Status variables
		data.personal[self.name]['costs']=[0.0]
		data.personal[self.name]['statusVariables'].append('costs')
		
	def act(self, data, layer):
		if layer.name == "Flexibility needs":
			data.personal[self.name]['costs'][0]=0.0
			self._flexibilityNeeds(data)	
		elif layer.name == "Flexibility requesting":
			self._flexiblityEvaluation(data)	
		elif layer.name == "Flexibility activation requesting":
			self._flexibilityActivation(data)
		else:
			raise Exception('%s has no action available for layer \"%s\".' % (self.name,layer)) 
		   
	## Activation of the contracted flexibility.
	# @param data Data.
	def _flexibilityActivation(self,data):	 
		# Add as benefits the reserve achieved to satisfy
		data.personal[self.name]['costs'][0]-=sum(map(lambda x,y,w,z : data.personal[self.name]['pi^S+']*min(x,w)+data.personal[self.name]['pi^S-']*max(y,z),
												data.personal[self.name]['A+'],data.personal[self.name]['A-'],data.personal[self.name]['R+'],data.personal[self.name]['R-']))
			
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/'+TSO.needsFile)
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/'+TSO.needsFile)
		
		try:
			model="TSO-flexActivation"
			self.flexiblityActivationRequest(model,data)
			
			# Add as benefits the imbalance achieved to solve
			data.personal[self.name]['costs'][0]-=sum(map(lambda px,x,py,y : px*x+py*y,data.general['pi^I+'],data.personal[self.name]['U+'],data.general['pi^I-'],data.personal[self.name]['U-']))
			
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+TSO.needsFile,self._dataFile)

	## Evaluate the flexibility offers.
	# @param data Data.
	def flexibilityEvaluation(self,data):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._dataFile,options.FOLDER+'/'+TSO.needsFile)
		else: # Rename instead of copy if debug
			os.rename(self._dataFile,options.FOLDER+'/'+TSO.needsFile)
		
		try: # Evaluate the flexibility offers.
			model="TSO-flexEvaluation"
			self.flexiblityEvaluationAndRequest(model,data)
			
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+TSO.needsFile,self._dataFile)

	## Define the flexibility needs.
	# @param data Data.
	def _flexibilityNeeds(self,data):
		T=data.general['T']
		for n in self.nodes:
			for t in range(T):
				data.general['R+'][n][t]+=data.personal[self.name]['R+'][t]
				data.general['R-'][n][t]+=data.personal[self.name]['R-'][t]

	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		s='\t<element id="%s" name="%s">\n'%(self.name,self.name)
		s+='\t\t<data id="costs">%s</data>\n'%data.personal[self.name]['costs'][0]

		s+=FSU.xmlData(self,data)
		
		# Flexibility graph
		s+='\t<timegraph id="service" title="" ylabel="Power [MW]">\n'
		for attr in ['R+','R-','E','U']:
			s+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		s+='\t</timegraph>\n'
		
		s+='\t</element>\n'
		return s

	## @var _dataFile 
	# Name of the data file with the needs of the TSO.
