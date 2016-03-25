##@package dso
#@author Sebastien MATHIEU

import os, csv, math

from .agent.stateAgent import StateAgent
from .fsu import FSU
from . import tools,options
from . import xmlsolution

## Distribution System Operator agent.
class DSO(StateAgent, FSU):
	## Name of the data file for the network.
	networkFile='network.csv'
	## Name of the data file with the baselines for the flexibility needs computation.
	baselinesFile='baselines.dat'
	## Name of the data file with the baselines for all periods.
	baselinesFullFile='baselines-full.dat'
	## Name of the data file with information on the qualified flexibility.
	qualifiedFlexibilityFile='qualified-flex.csv'
	## Name of the data file with the access requests.
	accessRequestsFile='accessRequests.dat'
	
	## Constructor.
	# @param networkDataFile Data of the network. @see _networkDataFile
	# @param qualifiedFlexibilityFile Data of the flexibility. @see _qualifiedFlexibilityFile
	# @param name DSO's name. @see rename()
	def __init__(self,networkDataFile,qualifiedFlexibilityFile,name="DSO"):
		StateAgent.__init__(self,name)   
		self._networkDataFile=networkDataFile
		self._qualifiedFlexibilityFile=qualifiedFlexibilityFile
		self._gridUsers=[]
	
	def initialize(self, data):
		StateAgent.initialize(self,data)
		self._readNetworkData(data)
		FSU.initialize(self,data)

		# Time variables
		data.general['Shed quantities']=[0.0]*self.T
		data.general['Total production']=[0.0]*self.T
		data.general['Total consumption']=[0.0]*self.T
		data.personal[self.name]['R+']=[0.0]*self.T # Total requirement of upward flex
		data.personal[self.name]['R-']=[0.0]*self.T # Total requirement of downward flex
		data.personal[self.name]['I']=[0.0]*self.T

		# Status variables
		data.personal[self.name]['costs']=[0.0]
		data.personal[self.name]['statusVariables'].extend(('R+','R-','costs','I'))
		
		# Line solution display allocation
		lineAttributes=['dC','f^b','f','f^r','flow violation']
		if options.OPF_METHOD == "linearOpf":
			lineAttributes.extend(['p','q','p^r', 'q^r','p^b','q^b'])

		for la in lineAttributes:
			data.personal[self.name][la]={}
			for l in range(1,self.L+1):
				data.personal[self.name][la][l]=[0.0]*self.T

		# Sheddings
		data.general['z']=[]
		for n in self.nodes:
			data.general['z'].append([0.0]*self.T)

		# Bus solution display allocation
		nodeAttributes=[]
		if options.OPF_METHOD == "linearOpf":
			nodeAttributes.extend(['v','phi','v^r','phi^r','v^b','phi^b', 'voltage violation'])

		for na in nodeAttributes:
			data.personal[self.name][na]=[]
			for n in self.nodes:
				data.personal[self.name][na].append([0.0]*self.T)
		
	def act(self, data, layer):
		if options.DEBUG:
			tools.log("\t%s" % layer.name, options.LOG, options.PRINT_TO_SCREEN)
		if layer.name == "Access agreement":
			self._accessAgreement(data)
		elif layer.name == "Dynamic ranges computation":
			self._capacityNeeds(data,proposals=True)
			self._flexibilityNeedsAndDynamicRanges(data)
		elif layer.name == "Flexibility needs":
			data.personal[self.name]['costs'][0]=0.0

			if data.general['interaction model'].accessRestriction.lower() != "dynamicbaseline":
				self._capacityNeeds(data)

			if data.general['interaction model'].accessRestriction.lower() == "dynamic":
				self._flexibilityNeedsAndDynamicRanges(data)
			else:
				self._flexibilityNeeds(data)
		elif layer.name == "Flexibility requesting":
			self._flexiblityEvaluation(data)	
		elif layer.name == "Flexibility activation requesting":
			self._flexibilityActivation(data)
		elif layer.name == "Operation":
			self._operation(data)  	
		elif layer.name == "Settlement":
			self._settlement(data)  
		else:
			raise Exception('%s has no action available for layer \"%s\".' % (self.name,layer)) 
	
	## Set the list of grid users.
	# @param users List of grid users.
	def setGridUsers(self,users):
		self._gridUsers=users
	
	## Define the access agreements.
	# @param data Data.
	def _accessAgreement(self,data):
		# Collect the requests of access per node
		data.general['g']=[0.0]*self.N
		data.general['G']=[0.0]*self.N
		data.general['k']=[0.0]*self.N
		data.general['K']=[0.0]*self.N
		data.general['l']=[0.0]*self.N
		data.general['L']=[0.0]*self.N
		
		for a in self._gridUsers:
			for n in a.nodes:
				g=data.personal[a.name]['k'][n]
				G=data.personal[a.name]['K'][n]
				# Check the input
				if g > 0:
					raise Exception("Illegal access bound request g of %s: %s"%(a.name,g))
				if G < 0:
					raise Exception("Illegal access bound request G of %s: %s"%(a.name,G))

				# Collect
				data.general['g'][n]+=g
				data.general['G'][n]+=G
		self._writeAccessRequests(data)
		
		if data.general['interaction model'].accessRestriction in ["flexible","conservative","safe","dynamic","dynamicBaseline"]:
			# Optimize
			# Move the data file to the operation folder
			if options.COPY:
				tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			else: # Rename instead of copy if debug
				os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			
			try:
				solver=data.general['solver']
				
				# Solve
				solutionFile="DSO-accessAgreement.sol"
				model="DSO-accessAgreement.zpl" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-accessAgreement.zpl"
				solver.solve(model, solutionFile,cwd=options.FOLDER)
				solver.checkFeasible()
				
				# Obtain general bounds by node
				data.general['b']=list(map(lambda x,y: x+y, data.general['g'], solver.variableVectorValue(self.N-1, 'dg#', 0)))
				data.general['B']=list(map(lambda x,y: x-y, data.general['G'], solver.variableVectorValue(self.N-1, 'dG#', 0)))
				data.general['l']=data.general['b']
				data.general['L']=data.general['B']
				if data.general['interaction model'].accessRestriction in ["conservative","safe"]:
					data.general['k']=data.general['b']
					data.general['K']=data.general['B']
				else:
					data.general['k']=data.general['g']
					data.general['K']=data.general['G']
		
			finally: # Move back the data file
				if not options.COPY:
					os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)  
		elif data.general['interaction model'].accessRestriction in ["none"]:
			data.general['b']=data.general['g']
			data.general['B']=data.general['G']
			data.general['k']=data.general['g']
			data.general['K']=data.general['G']
			data.general['l']=data.general['g']
			data.general['L']=data.general['G']
		else:
			raise Exception("Unknown access restriction parameter of the interaction model: %s"%data.general['interaction model'])

		# Default general dynamic ranges
		data.general['d']={}
		data.general['D']={}
		for n in range(self.N):
			data.general['d'][n]=[data.general['k'][n]]*self.T
			data.general['D'][n]=[data.general['K'][n]]*self.T

		# Dispatch the bounds between the grid users
		for a in self._gridUsers:
			data.personal[a.name]['d'][n]={}
			data.personal[a.name]['D'][n]={}

			for n in a.nodes:
				# Lower bounds
				if data.general['g'][n]-data.general['b'][n] < -options.EPS:
					data.personal[a.name]['l'][n]=min(0,data.personal[a.name]['k'][n]+(data.general['g'][n]-data.general['b'][n])*data.personal[a.name]['k'][n]/data.general['g'][n])
					if data.general['interaction model'].accessRestriction in ["conservative","safe"]:
						data.personal[a.name]['k'][n]=data.personal[a.name]['l'][n]
				else:
					data.personal[a.name]['l'][n]=data.personal[a.name]['k'][n]

				# Upper bounds
				if data.general['G'][n]-data.general['B'][n] > options.EPS:
					data.personal[a.name]['L'][n]=max(0,data.personal[a.name]['K'][n]-(data.general['G'][n]-data.general['B'][n])*data.personal[a.name]['K'][n]/data.general['G'][n])
					if data.general['interaction model'].accessRestriction in ["conservative","safe"]:
						data.personal[a.name]['K'][n]=data.personal[a.name]['L'][n]
				else:
					data.personal[a.name]['L'][n]=data.personal[a.name]['K'][n]

				# Default dynamic ranges
				data.personal[a.name]['d'][n]=[data.personal[a.name]['k'][n]]*self.T
				data.personal[a.name]['D'][n]=[data.personal[a.name]['K'][n]]*self.T

	## Settlement
	# @param data Data.
	def _settlement(self,data):
		# Reduction of the costs due to imbalance of FSPs is computed in the FSP class.
		pass
		
	## Operation of the network.
	# @param data Data.
	def _operation(self,data):		
		# Write real baselines
		self._writeRealBaselinesFull(data)
			
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		
		try:
			solutionFile="DSO-operation.sol"
			self._writeRealBaselinesFull(data)
			
			# Retrieve the solution
			solver=data.general['solver']
			model="DSO-operation.zpl" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-operation.zpl"
			solver.solve(model, solutionFile,cwd=options.FOLDER)
			solver.checkFeasible()
	
			# Parse the solution
			data.personal[self.name]['protectionsCost']=solver.objectiveValue()
			data.general['Shed quantities']=[0.0]*self.T
			data.general['Number of sheddings']=[0]*self.T
			data.general['Total production']=[0.0]*self.T
			data.general['Total consumption']=[0.0]*self.T
			for n in self.nodes:
				# Get the sheddings
				z=solver.variableVectorValue(self.T, 'z#%s#'%n, 1)
				data.general['z'][n]=list(map(lambda x: (x > options.EPS),z))
				
				activatedFlex=solver.variableVectorValue(self.T, 'r#%s#'%n, 1) # Activated flex
				for t in range(self.T):
					if z[t] > options.EPS:
						data.general['Number of sheddings'][t]+=1
					else:
						data.general['p'][n][t]=data.general['p^r'][n][t]
				
					if activatedFlex[t] > options.EPS:
						data.general['U+'][n][t]+=activatedFlex[t]
					elif activatedFlex[t] < -options.EPS:
						data.general['U-'][n][t]-=activatedFlex[t]

				# Voltages
				if options.OPF_METHOD == "linearOpf":
					e=solver.variableVectorValue(self.T, 'e#%s#'%n, 1)
					f=solver.variableVectorValue(self.T, 'f#%s#'%n, 1)
					data.personal[self.name]['v'][n]=list(map(lambda a,b: math.sqrt(a*a+b*b)*data.personal[self.name]['Vb'], e, f))
					data.personal[self.name]['phi'][n]=list(map(lambda a,b: math.atan(b/a)/math.pi*180 if a > options.EPS else 0, e, f))

					er=solver.variableVectorValue(self.T, 'er#%s#'%n, 1)
					fr=solver.variableVectorValue(self.T, 'fr#%s#'%n, 1)
					data.personal[self.name]['v^r'][n]=list(map(lambda a,b: math.sqrt(a*a+b*b)*data.personal[self.name]['Vb'], er, fr))
					data.personal[self.name]['phi^r'][n]=list(map(lambda a,b: math.atan(b/a)/math.pi*180 if a > options.EPS else 0, er, fr))

					data.personal[self.name]['voltage violation'][n]=list(map(lambda a:a*data.personal[self.name]['Vb'],solver.variableVectorValue(self.T, 'voltageViolation#%s#'%n, 1)))
				
				# Shedding
				if max(z) > options.EPS:
					if options.DEBUG:
						tools.log("\t\tz[n=%s] : %s" % (n,z), options.LOG, options.PRINT_TO_SCREEN) 
					for t in range(self.T):
						if z[t] > options.EPS:
							data.general['Shed quantities'][t]+=(data.general['p^r'][n][t])*data.general['dt']
				
				if options.DEBUG:
					# Flex activation display
					if max(activatedFlex) > options.EPS:
						tools.log("\t\tr[n=%s] : %s" % (n,activatedFlex), options.LOG, options.PRINT_TO_SCREEN)
			
			for l in range(1,self.L):
				data.personal[self.name]['flow violation'][l]=list(map(lambda a:a*data.personal[self.name]['Sb'], solver.variableVectorValue(self.T, 'flowViolation#%s#'%l, 1)))

				if options.OPF_METHOD == "linearOpf":
					data.personal[self.name]['p^r'][l]=solver.variableVectorValue(self.T, 'pr#%s#'%l, 1)
					data.personal[self.name]['q^r'][l]=solver.variableVectorValue(self.T, 'qr#%s#'%l, 1)
					data.personal[self.name]['f^r'][l]=list(map(lambda a,b: math.sqrt(a*a+b*b)*data.personal[self.name]['Sb']*(1 if a >= 0 else -1), data.personal[self.name]['p^r'][l], data.personal[self.name]['q^r'][l]))

					data.personal[self.name]['p'][l]=solver.variableVectorValue(self.T, 'p#%s#'%l, 1)
					data.personal[self.name]['q'][l]=solver.variableVectorValue(self.T, 'q#%s#'%l, 1)
					data.personal[self.name]['f'][l]=list(map(lambda a,b: math.sqrt(a*a+b*b)*data.personal[self.name]['Sb']*(1 if a >= 0 else -1) , data.personal[self.name]['p'][l], data.personal[self.name]['q'][l]))
				else:
					data.personal[self.name]['f^r'][l]=solver.variableVectorValue(self.T, 'fr#%s#'%l, 1)
					data.personal[self.name]['f'][l]=solver.variableVectorValue(self.T, 'f#%s#'%l, 1)
				
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)  

					
	## Activation of the contracted flexibility.
	# @param data Data.
	def _flexibilityActivation(self,data):	
		# Only perform the step if the DSO is a FSU
		if not data.general['interaction model'].DSOIsFSU:
			self._writeAnnouncedBaselinesFull(data) #TODO for now, only to compute the variables ab
			return

		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		
		try:
			self._writeAnnouncedBaselinesFull(data)
			model="DSO-flexActivation" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-flexActivation"
			self.flexiblityActivationRequest(model,data)
	
			# Retrieve imbalance
			T=data.general['T']
			solver=data.general['solver']
			data.personal[self.name]['I']=solver.variableVectorValue(T, 'I#', 1)
			for t in range(T):
				data.general['I'][t]+=data.personal[self.name]['I'][t]
			
			IP=solver.variableVectorValue(T, 'IP#', 1)
			IM=solver.variableVectorValue(T, 'IM#', 1)
			data.personal[self.name]['costs'][0]+=sum(map(lambda x,y:x*y,IP,data.general['pi^I+']))
			data.personal[self.name]['costs'][0]+=sum(map(lambda x,y:x*y,IM,data.general['pi^I-']))

		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)  
	   
	## Evaluate the flexibility offers.
	# @param data Data.
	def flexibilityEvaluation(self,data):
		# Only perform the step if the DSO is a FSU
		if not data.general['interaction model'].DSOIsFSU:
			return

		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
		
		try: # Evaluate the flexibility offers.
			self._writeAnnouncedBaselinesFull(data)
			model="DSO-flexEvaluation" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-flexEvaluation"
			self.flexiblityEvaluationAndRequest(model,data)
			
		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)	   

	## Define the flexibility needs for each node and the dynamic ranges for each actor, node and period.
	# @param data Data.
	def _flexibilityNeedsAndDynamicRanges(self,data):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			tools.safeCopy(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			os.rename(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)

		# Solve the optimization problem & fetch results
		try:
			self._writeBaselineRanges(data)

			# Baseline key
			blKey='p^b'
			if data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline":
				blKey='p^p'

			# Solve
			solver=data.general['solver']
			model="DSO-flexNeedsAndRanges.zpl" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-flexNeedsAndRanges.zpl"
			solver.solve(model,"DSO-flexNeedsAndRanges.sol",cwd=options.FOLDER)
			solver.checkFeasible()

			# Parse the flexibility needs
			for t in range(self.T):
				data.personal[self.name]['R+'][t]=0.0 # Total requirement of upward flex
				data.personal[self.name]['R-'][t]=0.0
			rL=solver.variableVectorValue(self.N-1, 'rL#', 0)
			rU=solver.variableVectorValue(self.N-1, 'rU#', 0)
			for n in self.nodes:
				data.personal[self.name]['R+'][t]+=rU[n]
				data.personal[self.name]['R-'][t]+=rL[n]
				data.general['R+'][n][t]+=rU[n]
				data.general['R-'][n][t]-=rL[n]

			# Parse the dynamic restrictions
			dpL={}
			dpU={}
			data.general['d']={}
			data.general['D']={}
			for n in self.nodes:
				dpL[n]=solver.variableVectorValue(self.T, 'dpL#%s#'%n, 1)
				dpU[n]=solver.variableVectorValue(self.T, 'dpU#%s#'%n, 1)

				# Compute the node dynamic range
				data.general['d'][n]=list(map(lambda x,y: min(data.general['l'][n],x+y),data.general[blKey][n],dpL[n]))
				data.general['D'][n]=list(map(lambda x,y: max(data.general['L'][n],x-y),data.general[blKey][n],dpU[n]))

			# Dispatch the bounds between the grid users
			for a in self._gridUsers:
				data.personal[a.name]['d']={}
				data.personal[a.name]['D']={}
				for n in a.nodes:
					# Compute d contribution
					data.personal[a.name]['d'][n]=list(map(lambda x,y,z,w: min(data.personal[a.name]['l'][n],x+(y*z/w if w > options.EPS else 0)), data.personal[a.name][blKey][n], dpL[n],data.personal[a.name]['dpL^max'][n],data.general['dpL^max'][n]))
					# Compute D contribution
					data.personal[a.name]['D'][n]=list(map(lambda x,y,z,w: max(data.personal[a.name]['L'][n],x-(y*z/w if w > options.EPS else 0)), data.personal[a.name][blKey][n], dpU[n],data.personal[a.name]['dpU^max'][n],data.general['dpU^max'][n]))

		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)
				os.rename(options.FOLDER+'/'+DSO.qualifiedFlexibilityFile,self._qualifiedFlexibilityFile)

	## Define the flexibility needs for each node.
	# @param data Data.
	def _flexibilityNeeds(self,data):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			tools.safeCopy(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			os.rename(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)

		# Get the flexibility needs for each period
		try:
			for t in range(self.T):
				# Flexibility needs
				solver=data.general['solver']
				self._writeAnnouncedBaselines(data,t)
				model="DSO-flexNeeds.zpl" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-flexNeeds.zpl"
				solutionFile="DSO-flexNeeds-%s.sol" % t
				solver.solve(model,solutionFile,cwd=options.FOLDER)
				solver.checkFeasible()

				# Parse the solution
				data.personal[self.name]['R+'][t]=0.0 # Total requirement of upward flex
				data.personal[self.name]['R-'][t]=0.0
				rL=solver.variableVectorValue(self.N-1, 'rL#', 0)
				rU=solver.variableVectorValue(self.N-1, 'rU#', 0)
				for n in self.nodes:
					data.personal[self.name]['R+'][t]+=rU[n]
					data.personal[self.name]['R-'][t]+=rL[n]
					data.general['R+'][n][t]+=rU[n]
					data.general['R-'][n][t]-=rL[n]

		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)
				os.rename(options.FOLDER+'/'+DSO.qualifiedFlexibilityFile,self._qualifiedFlexibilityFile)

	## Compute the capacity needs of the network.
	# @param data Data.
	# @param proposals If true, uses the proposal baselines instead of the final baselines.
	def _capacityNeeds(self, data, proposals=False):
		# Move the data file to the operation folder
		if options.COPY:
			tools.safeCopy(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			tools.safeCopy(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)
		else: # Rename instead of copy if debug
			os.rename(self._networkDataFile,options.FOLDER+'/'+DSO.networkFile)
			os.rename(self._qualifiedFlexibilityFile,options.FOLDER+'/'+DSO.qualifiedFlexibilityFile)

		try:
			# Compute the ideal needs for each periods
			for t in range(self.T):
				self._writeAnnouncedBaselines(data,t,proposals)

				solver=data.general['solver']
				model="DSO-capaNeeds.zpl" if options.OPF_METHOD != "linearOpf" else "DSO-linearOpf-capaNeeds.zpl"
				solutionFile="DSO-capaNeeds-%s.sol" % t
				solver.solve(model,solutionFile,cwd=options.FOLDER)

				solver.checkFeasible()

				# parse the solution
				dC=solver.variableVectorValue(self.L, 'dC#', 1)
				flow=[]
				if options.OPF_METHOD == "linearOpf":
					e=solver.variableVectorValue(self.N, 'e#', 0)
					f=solver.variableVectorValue(self.N, 'f#', 0)
					p=solver.variableVectorValue(self.L, 'p#', 1)
					q=solver.variableVectorValue(self.L, 'q#', 1)
					v=list(map(lambda a,b: math.sqrt(a*a+b*b), e, f))
					phi=list(map(lambda a,b: math.atan(b/a)/math.pi*180 if a > options.EPS else 0, e, f))
					flow=list(map(lambda a,b:math.sqrt(a*a+b*b)*data.personal[self.name]['Sb']*(1 if a >= 0 else -1),p,q))

					for n in self.nodes:
						data.personal[self.name]['v^b'][n][t]=v[n]*data.personal[self.name]['Vb']
						data.personal[self.name]['phi^b'][n][t]=phi[n]
				else:
					flow=solver.variableVectorValue(self.L, 'f#', 1)

				for l in range(1,self.L+1):
					data.personal[self.name]['f^b'][l][t]=flow[l-1]
					data.personal[self.name]['dC'][l][t]=dC[l-1]

		finally: # Move back the data file
			if not options.COPY:
				os.rename(options.FOLDER+'/'+DSO.networkFile,self._networkDataFile)
				os.rename(options.FOLDER+'/'+DSO.qualifiedFlexibilityFile,self._qualifiedFlexibilityFile)

	## Write the access requests data file.
	# @param data Data.
	def _writeAccessRequests(self,data):
		with open(options.FOLDER+'/'+DSO.accessRequestsFile, 'w') as file:
			file.write("# N, minCurtail, EPS\n%s, %s, %s\n" % (self.N, 0.1,options.EPS))
			file.write("# n, g, G\n")
			for n in self.nodes:
				file.write("%s,%s,%s\n" % (n,data.general['g'][n],data.general['G'][n]))
			
	## Write real baselines for all periods.
	# @param data Data.
	def _writeRealBaselinesFull(self,data):
		with open(options.FOLDER+'/'+DSO.baselinesFullFile, 'w') as file:
			file.write("# N, T, gamma, dt, EPS\n%s,%s,%s,%s,%s\n" % (self.N,self.T,data.general['interaction model'].DSOImbalancePriceRatio/100,data.general['dt'],options.EPS))
			file.write("# n, t, p^r\n")
			for n in self.nodes:
				for t in range(self.T):
					file.write("%s,%s,%s\n" % (n,t+1,data.general['p^r'][n][t]))
					
	## Write announced baselines for all periods.
	# @param data Data.
	# @param proposals If true, writes the proposal baselines instead of the final baselines.
	def _writeAnnouncedBaselinesFull(self,data,proposals=False):
		with open(options.FOLDER+'/'+DSO.baselinesFullFile, 'w') as file:
			file.write("# N, t, gamma, dt, EPS\n%s,%s,%s,%s,%s\n" % (self.N,self.T,data.general['interaction model'].DSOImbalancePriceRatio/100,data.general['dt'],options.EPS))
			file.write("# n, t, p^b\n")
			for n in self.nodes:
				for t in range(self.T):
					file.write("%s,%s,%s\n" % (n,t+1,data.general['p^b' if not proposals else 'p^p'][n][t]))

	## Write for each node and each actor a range of baseline and the possible access restriction if the access bounds computation type is dynamic.
	# @param data Data.
	def _writeBaselineRanges(self,data):
		im=data.general['interaction model']

		# Prepare the structures
		pL=[]
		pU=[]
		data.general['dpL^max']=[]
		data.general['dpU^max']=[]
		for n in self.nodes:
			pL.append([0.0]*self.T)
			pU.append([0.0]*self.T)
			data.general['dpL^max'].append([0.0]*self.T)
			data.general['dpU^max'].append([0.0]*self.T)

		# Fetch the allowed deviation from the submitted baselines
		relativeDeviation=data.general['interaction model'].relativeDeviation

		# Prepare the data by aggregating the actor for each node
		for a in self._gridUsers:
			data.personal[a.name]['dpL^max']={}
			data.personal[a.name]['dpU^max']={}
			for n in a.nodes:
				data.personal[a.name]['dpL^max'][n]=[0.0]*self.T
				data.personal[a.name]['dpU^max'][n]=[0.0]*self.T

				pb=None
				if data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline":
					pb=data.personal[a.name]['p^p'][n]
				else:
					pb=data.personal[a.name]['p^b'][n]

				l=data.personal[a.name]['l'][n]
				L=data.personal[a.name]['L'][n]
				for t in range(self.T):
					if l <= pb[t] <= L:
						# Baseline in the safe range
						pL[n][t]+=max(l,pb[t]-relativeDeviation*abs(pb[t]))
						pU[n][t]+=min(L,pb[t]+relativeDeviation*abs(pb[t]))

						data.personal[a.name]['dpL^max'][n][t]=0
						data.personal[a.name]['dpU^max'][n][t]=0
					else:
						# Baseline in the flexible range
						pL[n][t]+=pb[t]
						pU[n][t]+=pb[t]

						data.personal[a.name]['dpL^max'][n][t]=max(l-pb[t],0)
						data.personal[a.name]['dpU^max'][n][t]=max(pb[t]-L,0)

						data.general['dpL^max'][n][t]+=data.personal[a.name]['dpL^max'][n][t]
						data.general['dpU^max'][n][t]+=data.personal[a.name]['dpU^max'][n][t]

		# Write the file
		with open(options.FOLDER+'/'+DSO.baselinesFile, 'w') as file:
			file.write("# N, T, gamma, dt, EPS\n%s,%s,%s,%s,%s\n" % (self.N,self.T,im.DSOImbalancePriceRatio/100,data.general['dt'],options.EPS))

			file.write("# n, t, pL, pU, dpL max, dpU max\n")
			for n in range(self.N):
				for t in range(self.T):
					file.write("%s,%s,%s,%s,%s,%s\n" % (n,t+1,pL[n][t],pU[n][t],data.general['dpL^max'][n][t],data.general['dpU^max'][n][t]))

			file.write("# n, l, L\n")
			for n in range(self.N):
				file.write("%s,%s,%s\n" % (n,data.general['l'][n],data.general['L'][n]))

	## Write announced baselines for a single period.
	# @param t Period.
	# @param data Data.
	# @param proposals If true, writes the proposal baselines instead of the final baselines.
	def _writeAnnouncedBaselines(self,data,t,proposals=False):
		with open(options.FOLDER+'/'+DSO.baselinesFile, 'w') as file:
			file.write("# N, T, gamma, dt, EPS\n%s,%s,%s,%s,%s\n" % (self.N,t+1,data.general['interaction model'].DSOImbalancePriceRatio/100,data.general['dt'],options.EPS))
			file.write("# n, p^b\n")
			for n in range(self.N):
				file.write("%s,%s\n" % (n,data.general['p^b' if not proposals else 'p^p'][n][t]))
	
	# Read network data file.
	# @param data Data.
	def _readNetworkData(self,data):
		self.N=data.general['N']
		self.nodes=list(range(self.N))
		self.T=data.general['T']
		
		with open(self._networkDataFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')

			# Get first row
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			self.L=int(row[1])
			data.personal[self.name]['L']=self.L
			data.personal[self.name]['Sb']=float(row[4]) # Base power
			data.personal[self.name]['Vb']=float(row[5]) # Base voltage
			
			# Get line capacities
			data.personal[self.name]['C']={}
			for l in range(1, self.L+1):
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)

				lineIndex=int(row[0])
				if lineIndex < 1 or lineIndex > self.L:
					raise Exception('Invalid line index %s in network data file "%s".' % (lineIndex, self._networkDataFile))
				data.personal[self.name]['C'][lineIndex]=float(row[5])

			# Get node voltages bounds
			data.personal[self.name]['Vmin']=[0.0]*self.N
			data.personal[self.name]['Vmax']=[0.0]*self.N
			for n in self.nodes:
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)

				busIndex=int(row[0])
				data.personal[self.name]['Vmin'][busIndex]=float(row[2])
				data.personal[self.name]['Vmax'][busIndex]=float(row[3])
		   
	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		s='\t<element id="%s" name="%s">\n'%(self.name,self.name)
		s+='\t\t<data id="costs">%s</data>\n'%data.personal[self.name]['costs'][0]
		s+='\t\t<data id="Protections cost">%s</data>\n'%data.personal[self.name]['protectionsCost']
		s+='\t\t<data id="Total imbalance">%s</data>\n'%(sum(map(abs,data.personal[self.name]['I']))*data.general['dt'])
		
		# Imbalance caused
		s+='\t<timegraph id="brp" title="" ylabel="Power [MW]">\n'
		for attr in ['R+','R-','I']:
			s+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		s+='\t</timegraph>\n'
		
		s+=FSU.xmlData(self,data)
		
		s+='\t</element>\n'
		return s
		 
	## @var N
	# Number of nodes.
	## @var nodes
	# List of nodes.
	## @var T
	# Number of periods.
	## @var L
	# Number of lines.
	## @var _networkDataFile
	# CSV file with the network data.
	## @var _qualifiedFlexibilityFile
	# CSV file with information on the qualified flexibility.
	## @var _gridUsers
	# List of grid users with access contract.
	