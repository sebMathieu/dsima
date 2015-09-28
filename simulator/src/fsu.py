##@package fsu
#@author Sebastien MATHIEU

from . import tools,options, xmlsolution

from .ecbid import ECBid, ECBidRequest
from .spbid import SPBid, SPBidRequest, SPObligationBid
from . import xmlsolution

## Flexibility services user.
# Needed to inherit:
#	- name
#	- 'costs' personal data
#	- A ZIMPL model to evaluate the flexibility offers.
#	- A method flexibilityEvaluation wrapping the method FSU.flexiblityActivationRequest .
class FSU:
	# Name of the data file with accepted flexibility.
	acceptedFlexFile='acceptedFlex.dat'
	# Name of the data file with accepted flexibility.
	activatedFlexFile='activatedFlex.dat'
	
	# Initialization procedure of the internal data.
	# @param data Global data set.
	def initialize(self, data):
		T=data.general['T']
		N=data.general['N']
		
		# Create personal variables
		data.personal[self.name]['a+']={} # Upward flexibility reserved in each node and each period
		data.personal[self.name]['a-']={} # Upward flexibility reserved in each node and each period
		data.personal[self.name]['A+']=[0.0]*T # Upward flexibility contracted in each period
		data.personal[self.name]['A-']=[0.0]*T # Downward flexibility contracted in each period
		data.personal[self.name]['U+']=[0.0]*T # Upward flexibility activated in each period
		data.personal[self.name]['U-']=[0.0]*T # Downward flexibility activated in each period
		data.personal[self.name]['U']=[0.0]*T # Flexibility activated in each period
		for n in range(N):
			data.personal[self.name]['a+'][n]=[0.0]*T
			data.personal[self.name]['a-'][n]=[0.0]*T
			
		# Register to the flexibility platform
		data.general['flexibilityPlatform'].registerFSU(self)
			
	## Write the flexibility activated to a data file.
	# Suppose that the flexibility activation request has been determined in the personal data 'u' for each node and each period.
	# @see flexiblityActivationRequest .
	# @param data Data.
	def writeFlexbilityActivated(self,data):
		T=data.general['T'] 
		with open(options.FOLDER+'/'+FSU.activatedFlexFile, 'w') as file:
			file.write("# T\n%s\n" % T)
			file.write("# N set\n%s\n" % ",".join(map(str,self.nodes)))
			file.write("# n, t, u\n")
			for n in self.nodes:
				for t in range(T):
					file.write("%s,%s,%s\n" % (n,t+1, data.personal[self.name]['u'][n][t]))
		
	## Activate the contracted flexibility through the flexibility platform.
	# @param model Flexibility activation model file without the extension.
	# @param data Data.
	def flexiblityActivationRequest(self,model,data):
		from .dso import DSO
		
		T=data.general['T']
		N=data.general['N']
		flexPlatform=data.general['flexibilityPlatform']
		
		# Re-initialize reserved flexibility
		data.personal[self.name]['a+']={} # Upward flexibility reserved in each node and each period
		data.personal[self.name]['a-']={} # Upward flexibility reserved in each node and each period
		data.personal[self.name]['A+']=[0.0]*T # Upward flexibility reserved in each period
		data.personal[self.name]['A-']=[0.0]*T # Upward flexibility reserved in each period
		data.personal[self.name]['U+']=[0.0]*T # Upward flexibility activated in each period
		data.personal[self.name]['U-']=[0.0]*T # Downward flexibility activated in each period
		data.personal[self.name]['U']=[0.0]*T # Flexibility activated in each period
		for n in range(N):
			data.personal[self.name]['a+'][n]=[0.0]*T
			data.personal[self.name]['a-'][n]=[0.0]*T
		
		# Gather the energy constrained bids
		ecBidRequestsList=flexPlatform.getAcceptedECBidRequests(self)
		for r in ecBidRequestsList:
			b=r.bid
			n=b.bus
			if isinstance(self,DSO):
				data.personal[self.name]['costs'][0]+=b.dsoReservationCost
			else:
				data.personal[self.name]['costs'][0]+=b.reservationCost
			for t in range(T):
				data.personal[self.name]['A+'][t]+=b.max[t]
				data.personal[self.name]['a+'][n][t]+=b.max[t]
				data.personal[self.name]['A-'][t]+=b.min[t]
				data.personal[self.name]['a-'][n][t]+=b.min[t]
			
		# Fetch the single period bids
		spBidRequestsList=flexPlatform.getAcceptedSPBidRequests(self)
		for r in spBidRequestsList:
			b=r.bid
			n=b.bus
			t=b.t
			if isinstance(self,DSO):
				data.personal[self.name]['costs'][0]+=b.dsoReservationCost*(abs(r.aw)+abs(r.aW))
			else:
				data.personal[self.name]['costs'][0]+=b.reservationCost*(abs(r.aw)+abs(r.aW))
			data.personal[self.name]['A+'][t]+=r.aW
			data.personal[self.name]['a+'][n][t]+=r.aW
			data.personal[self.name]['A-'][t]+=r.aw
			data.personal[self.name]['a-'][n][t]+=r.aw
			
		# Write the contracted flexibility
		self._writeContractedFlex(spBidRequestsList,ecBidRequestsList,data)
		
		# Solve the optimization problem
		solver=data.general['solver']
		solver.solve("%s.zpl"%model,"%s.sol"%model,cwd=options.FOLDER)
		solver.checkFeasible()
		
		# Parse solution
		flexPlatform=data.general['flexibilityPlatform']
		data.personal[self.name]['u']={}
		for n in range(N):
			data.personal[self.name]['u'][n]=[0.0]*T
		
		v=solver.variableVectorValue(len(spBidRequestsList)-1, 'v#', 0)
		for i in range(len(v)):
			request=spBidRequestsList[i]
			bid=request.bid
			flexPlatform.activateSPBid(spBidRequestsList[i],v[i],data);
			
			# Personal effect
			if isinstance(self,DSO):
				data.personal[self.name]['costs'][0]+=v[i]*bid.dsoActivationCost
			else:
				data.personal[self.name]['costs'][0]+=v[i]*bid.activationCost
			data.personal[self.name]['u'][bid.bus][bid.t]+=v[i]
			if v[i] > 0:
				 data.personal[self.name]['U+'][bid.t]+=v[i]
			else:
				 data.personal[self.name]['U-'][bid.t]+=v[i]
		
		for i in range(len(ecBidRequestsList)):
			request=ecBidRequestsList[i]
			bid=request.bid
			x=solver.variableVectorValue(T, 'x#%s#'%i, 1)
			flexPlatform.activateECBid(ecBidRequestsList[i],x,data);
				
			# Personal effect
			for t in range(T):
				if isinstance(self,DSO):
					data.personal[self.name]['costs'][0]+=abs(x[t])*bid.dsoActivationCost
				else:
					data.personal[self.name]['costs'][0]+=abs(x[t])*bid.activationCost
				
				data.personal[self.name]['u'][bid.bus][t]+=x[t]
				if x[t] > 0:
					 data.personal[self.name]['U+'][t]+=x[t]
				else:
					 data.personal[self.name]['U-'][t]+=x[t]
		
		
		data.personal[self.name]['U']=list(map(lambda x,y:x+y, data.personal[self.name]['U+'], data.personal[self.name]['U-']))
		
	## Evaluate the flexibility offers and request them on the flexibility platform.
	# @param model Flexibility evaluation model file without the extension.
	# @param data Data.
	def flexiblityEvaluationAndRequest(self,model,data):
		# The offers are written by the flexibility platform.
		solver=data.general['solver']
		solver.solve("%s.zpl"%model,"%s.sol"%model,cwd=options.FOLDER)
		solver.checkFeasible()

		# Parse the solution
		flexPlatform=data.general['flexibilityPlatform']
		F=flexPlatform.ECBidsCount() # Number of ECBids
		y=solver.variableVectorValue(F-1, 'y#', 0)
		for id in range(F):
			if y[id] > options.EPS:
				flexPlatform.requestECBid(id,self,y[id])
		
		B=flexPlatform.spBidsCount()
		w=solver.variableVectorValue(B-1, 'w#', 0)
		W=solver.variableVectorValue(B-1, 'W#', 0)
		for id in range(B):
			if W[id]-w[id] > options.EPS:
				flexPlatform.requestSPBid(id,self,w[id],W[id])
	
	## Write the contracted flexibility in a CSV file.
	# @param spBidRequestsList List of accepted single period requests.
	# @param ecBidRequestsList List of accepted energy constrained bid requests.
	# @param data Data.
	def _writeContractedFlex(self,spBidRequestsList,ecBidRequestsList,data):	  
		from .dso import DSO  
		
		with open(options.FOLDER+'/'+FSU.acceptedFlexFile, 'w') as file:
			T=data.general['T']
			B=len(spBidRequestsList)
			F=len(ecBidRequestsList)
			file.write("# B, F, T\n%s,%s,%s\n" % (B+1,F+1,T))
			# Single period bids
			file.write("#SPFOs\n")
			file.write("# b, n, tau, pi^r, pi^a, aw, aW\n")
			i=0
			for r in spBidRequestsList:
				b=r.bid
				if isinstance(self,DSO) and isinstance(b, SPObligationBid):
					 file.write("%s, %s, %s, %s, %s, %s, %s\n" % (i, b.bus, b.t+1, b.dsoReservationCost,b.dsoActivationCost, min(r.aw,0), max(r.aW,0)))
				else:
					file.write("%s, %s, %s, %s, %s, %s, %s\n" % (i, b.bus, b.t+1, b.reservationCost, b.activationCost, min(r.aw,0), max(r.aW,0)))
				i+=1 
			file.write("%s, %s, %s, %s, %s, %s, %s\n" % (i, 0, 1, options.INF,0, 0, 0))
			
			# Energy constrained bids
			file.write("#ECFOs\n")
			file.write("# b, n, pi^r, pi^a\n")
			i=0
			for r in ecBidRequestsList:
				b=r.bid
				file.write("%s,%s,%s,%s\n" % (i,b.bus,b.reservationCost,b.activationCost))
				i+=1
			file.write("%s,%s,%s,%s\n" % (i,0,options.INF,0)) # Dummy bid
			
			file.write("# b, t, m, M\n")
			i=0
			for r in ecBidRequestsList:
				b=r.bid
				for t in range(T):
					file.write("%s,%s,%s,%s\n" % (i,t+1,min(b.min[t],0),max(b.max[t],0)))
				i+=1
			# Dummy bid
			for t in range(T):
				file.write("%s,%s,%s,%s\n" % (i,t+1,0,0))
		
	## Get the data to display.
	# @param data Data.
	# @return XML data string.
	def xmlData(self,data):
		T=data.general['T']
		dt=data.general['dt']
		
		s=""
		s+='\t\t<data id="Flexibility accepted">%s</data>\n' % ((sum(data.personal[self.name]['A+'])-sum(data.personal[self.name]['A-']))*dt)
		s+='\t\t<data id="Flexibility used">%s</data>\n' % ((sum(data.personal[self.name]['U+'])-sum(data.personal[self.name]['U-']))*dt)
		
		# List of personal time-depedent attributes
		for attr in ['U+','U-']: 
			s+='\t\t<timedata id="%s">%s</timedata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		
		# Flexibility graph
		s+='\t<timegraph id="fsu" title="" ylabel="Power [MW]">\n'
		for attr in ['U','A+','A-']:
			s+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(xmlsolution.translate(attr),xmlsolution.floats2str(data.personal[self.name][attr]))
		s+='\t</timegraph>\n'
		
		return s
	