##@package brp
#@author Sebastien MATHIEU

from . import tools,options,xmlsolution

## Balance Responsible Party
# Needed to inherit from a state agent and have the following properties:
#	- name
#	- 'costs' personal data
#	-  nodes, a list of nodes to consider
class BRP:

	# Initialization procedure of the internal data.
	# @param data Global data set.
	def initialize(self, data):
		T=data.general['T']

		self._iP={}
		self._iM={}
		data.personal[self.name]['p^b']={}
		data.personal[self.name]['p']={}
		data.personal[self.name]['h']={} # flexibility request
		data.personal[self.name]['u']={} # Flexibility activated in each node and each period
		data.personal[self.name]['d']={}
		data.personal[self.name]['D']={}
		for n in self.nodes:
			self._iP[n]=[0.0]*T
			self._iM[n]=[0.0]*T
			data.personal[self.name]['p^b'][n]=[0.0]*T
			data.personal[self.name]['p'][n]=[0.0]*T
			data.personal[self.name]['h'][n]=[0.0]*T
			data.personal[self.name]['u'][n]=[0.0]*T
			data.personal[self.name]['d'][n]=[0.0]*T
			data.personal[self.name]['D'][n]=[0.0]*T
			
		data.personal[self.name]['I']=[0.0]*T
		data.personal[self.name]['P^b']=[0.0]*T
		data.personal[self.name]['P^r']=[0.0]*T
		data.personal[self.name]['P']=[0.0]*T # Total that actually occured
		data.personal[self.name]['statusVariables'].extend(('P^b','P^r','I'))
	
	## Settlement.
	# @param data Data.
	def settlement(self,data):
		T=data.general['T']
		data.personal[self.name]['P']=[0.0]*T

		# Consider shedding effect on imbalance
		for t in range(T):
				for n in self.nodes:
					if data.general['z'][n][t]:
						data.personal[self.name]['I'][t]-=data.personal[self.name]['p^b'][n][t]+data.personal[self.name]['h'][n][t]+data.personal[self.name]['u'][n][t]
						data.personal[self.name]['p'][n][t]=0
					else:
						data.personal[self.name]['P'][t]+=data.personal[self.name]['p'][n][t]
						if data.personal[self.name]['p'][n][t] > 0:
							data.general['Total production'][t]+=data.personal[self.name]['p'][n][t]
						else:
							data.general['Total consumption'][t]+=data.personal[self.name]['p'][n][t]

		# Update general imbalance and add imbalance costs to the total costs
		for t in range(T):
			# Compute the imbalance created in distribution
			data.general['I'][t]+=data.personal[self.name]['I'][t]

			# Charge the imbalance based on the system imbalance sign
			if data.personal[self.name]['I'][t] >= 0:
				if data.general['SI'][t] > 0:
					# Charged for increasing the global imbalance
					data.personal[self.name]['costs'][0]+=data.personal[self.name]['I'][t]*data.general['pi^I+'][t]
				else:
					# Rewarded for decreasing the global imbalance
					data.personal[self.name]['costs'][0]-=data.personal[self.name]['I'][t]*data.general['pi^I+'][t]
			else:
				if data.general['SI'][t] > 0:
					# Rewarded for decreasing the global imbalance
					data.personal[self.name]['costs'][0]+=data.personal[self.name]['I'][t]*data.general['pi^I-'][t]
				else:
					# Charged for increasing the global imbalance
					data.personal[self.name]['costs'][0]-=data.personal[self.name]['I'][t]*data.general['pi^I-'][t]

	## Optimize the final imbalance of the BRP.
	# @param model Imbalance evaluation model file without the extension.
	# @param data Data.
	def optimizeImbalance(self,model,data):
		T=data.general['T']
		solver=data.general['solver']
		
		solutionFile="%s.sol"%model
		solver.solve("%s.zpl"%model, solutionFile,cwd=options.FOLDER)
		solver.checkFeasible()

		# Parse the solution
		data.personal[self.name]['I']=solver.variableVectorValue(T, 'I#', 1)
		data.personal[self.name]['P^r']=solver.variableVectorValue(T, 'P#', 1)
	
		for n in self.nodes:
			data.personal[self.name]['p'][n]=solver.variableVectorValue(T, 'p#%s#'%n, 1)
			for t in range(T):
				data.general['p^r'][n][t]+=data.personal[self.name]['p'][n][t]

	## Optimize the baseline.
	# @param model Baseline optimization model file without the extension.
	# @param data Data.
	# @param submitToDAMarket Boolean equals to true if submit to day-ahead market.
	# @param layer Layer
	def optimizeBaseline(self, model, data, submitToDAMarket=True, layer=None):
		T=data.general['T']
		solver=data.general['solver']
		
		# Retrieve the solution
		solutionFile="%s.sol"%model
		solver.solve("%s.zpl"%model,solutionFile,cwd=options.FOLDER)
		solver.checkFeasible()

		# Parse the solution
		if layer is None or layer.name == "Baseline optimization":
			data.personal[self.name]['P^b']=solver.variableVectorValue(T, 'Pa#', 1)
			data.personal[self.name]['costs'][0]+=sum(map(lambda x,y:-x*y,data.personal[self.name]['P^b'],data.general['pi^E']))

			if options.DEBUG:
				tools.log("\t\t\t%s's energy costs: %s" %(self.name,sum(map(lambda x,y:-x*y,data.personal[self.name]['P^b'],data.general['pi^E']))), options.LOG, options.PRINT_TO_SCREEN)

			for n in self.nodes:
				baseline=solver.variableVectorValue(T, 'pa#%s#'%n, 1)
				# Announcement of the baseline
				data.personal[self.name]['p^b'][n]=baseline
				for t in range(T):
					data.general['p^b'][n][t]+=baseline[t]

		elif layer.name == "Baseline proposal":
			data.personal[self.name]['P^p']=solver.variableVectorValue(T, 'Pa#', 1)
			data.personal[self.name]['p^p']={}
			for n in self.nodes:
				baseline=solver.variableVectorValue(T, 'pa#%s#'%n, 1)
				# Announcement of the baseline
				data.personal[self.name]['p^p'][n]=baseline
				for t in range(T):
					data.general['p^p'][n][t]+=baseline[t]
		else:
			raise Exception('BRP has no action available for layer \"%s\" in the baseline optimization.'%layer)
			
					
	## Write the baselines to a data file.
	# @param baselinesDataFile Path to the data file.
	# @param data Data.
	def writeBaselines(self,baselinesDataFile,data):
		T=data.general['T'] 
		Pa=data.personal[self.name]['P^b']
		with open(options.FOLDER+'/'+baselinesDataFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# T, Pb\n")
			for t in range(T):
				file.write("%s,%s\n"%(t+1,Pa[t]))
			file.write("# n, t, pb\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s\n" % (n,t+1, data.personal[self.name]['p^b'][n][t]))
					
	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		s=""
		
		s+='\t\t<data id="Total imbalance">%s</data>\n'%(sum(map(abs,data.personal[self.name]['I']))*data.general['dt'])
		s+='\t\t<data id="Realization energy">%s</data>\n'%(sum(data.personal[self.name]['P'])*data.general['dt'])
		s+='\t\t<data id="Baseline energy">%s</data>\n'%(sum(data.personal[self.name]['P^b'])*data.general['dt'])
		
		# BRP graph
		s+='\t<timegraph id="brp" title="" ylabel="Power [MW]">\n'
		for attr in ['P^b','P^r','P','I']:
			s+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		s+='\t</timegraph>\n'
		
		return s

	## @var _iP
	# Positive imbalance for each flexible node and each period.
	## @var _iM
	# Negative imbalance for each flexible node and each period.
	