##@package flexibilityplatform
#@author Sebastien MATHIEU

from .ecbid import ECBid, ECBidRequest, ECObligationBid
from .spbid import SPBid, SPBidRequest, SPObligationBid
from .agent.agent import Agent
from .dso import DSO
from .tso import TSO
from . import options
from . import tools
	
## Platform to centralize the flexibility.
class FlexibilityPlatform(Agent):
	## Name of the data file with the energy constrained bids.
	ecBidsDataFile="ecBids.dat"
	## Name of the data file with the single period bids.
	spBidsDataFile="spBids.dat"
	
	def __init__(self):
		self._FSUs=[]
		
	def initialize(self, data):
		self.clean(data)
		
	def act(self, data, layer):
		if options.DEBUG:
			tools.log("\t%s" % layer.name, options.LOG, options.PRINT_TO_SCREEN)
		if layer.name == "Flexibility platform cleaning":
			self.clean(data)
		elif layer.name == "Flexibility platform clearing":
			self._clearing(data)
		elif layer.name == "Flexibility platform activation":
			self._activation(data)
		elif layer.name == "Settlement":
			self._settlement(data)
		else:
			raise Exception('Flexibility platform has no action available for layer \"%s\".' % layer)
		
	## Clean the flexibility platform of all registration.
	# @param data Data.
	def clean(self,data):
		self._ecBids=[]
		self._spBids=[]
		
		N=data.general['N']
		T=data.general['T']
		data.general['U+']={} # Activated upward flex
		data.general['A+']={} # Upward flexibility reserved
		data.general['S+']={} # Submitted upward flexibility
		data.general['R+']={} # Requirement of upward flexibility
		data.general['U-']={} # Activated downward flex
		data.general['A-']={} # Downward flexibility reserved
		data.general['S-']={} # Submitted downward flexibility
		data.general['R-']={} # Requirement of downward flexibility
		data.general['I']=[0.0]*T # Total imbalance
		data.general['O']=[0.0]*T # Opposite usage of flexibility
		data.general['TU']=[0.0]*T # Usage of flexibility
		data.general['U']=[0.0]*T #  Flexibility effect
		data.general['Tripped flex.']= [0.0]*T
		data.general['p^b']={} # Announced baseline
		data.general['p^r']={} # Real baseline
		data.general['p']={} # Real production
		if data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline":
			data.general['p^p']={}
		for n in range(N):
			data.general['U+'][n]=[0.0]*T
			data.general['A+'][n]=[0.0]*T
			data.general['S+'][n]=[0.0]*T
			data.general['R+'][n]=[0.0]*T
			data.general['U-'][n]=[0.0]*T
			data.general['A-'][n]=[0.0]*T
			data.general['S-'][n]=[0.0]*T
			data.general['R-'][n]=[0.0]*T
			data.general['p^b'][n]=[0.0]*T
			data.general['p^r'][n]=[0.0]*T
			data.general['p'][n]=[0.0]*T
			if data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline":
				data.general['p^p'][n]=[0.0]*T
			
	## Activate a single period bid.
	# @param request Request of the bid.
	# @param modulation Requested modulation to activate.
	# @param data Data.
	def activateSPBid(self,request,modulation,data):
		bid=request.bid
		bid.modulation+=modulation
		
		if modulation > options.EPS:
			data.general['U+'][bid.bus][bid.t]+=modulation;
		elif modulation < options.EPS:
			data.general['U-'][bid.bus][bid.t]+=modulation;
			
		if isinstance(request.buyer,DSO):
			bid.activationBenefits+=modulation*bid.dsoActivationCost
		else:
			bid.activationBenefits+=modulation*bid.activationCost
			
	## Activate an energy constrained period bid.
	# @param request Request of the bid.
	# @param modulation Requested modulation to activate for each period.
	# @param data Data.
	def activateECBid(self,request,modulation,data):
		bid=request.bid
		for t in range(bid.t):
			bid.modulation[t]+=modulation[t];
			if modulation[t] > options.EPS:
				data.general['U+'][bid.bus][t]+=modulation[t];
			elif modulation[t] < options.EPS:
				data.general['U-'][bid.bus][t]+=modulation[t];
				
			if isinstance(request.buyer,DSO):
				bid.activationBenefits+=abs(modulation[t])*bid.dsoActivationCost
			else:
				bid.activationBenefits+=abs(modulation[t])*bid.activationCost
	
	## Function to get the accepted requests from a bid list.
	# @param bidList List of bids.
	# @param buyer Buyer.
	# @return List of requests.
	def _getAcceptedBidRequests(self,bidList,buyer):
		lr=[]
		for b in bidList:
			for r in b.requests:
				if r.buyer == buyer and r.acceptation == True:
					lr.append(r)		
		return lr
	
	# Get the list of energy constrained bid requests.
	# @param buyer Buyer.
	# @return List of energy constrained bid requests.
	def getAcceptedECBidRequests(self,buyer):
		return self._getAcceptedBidRequests(self._ecBids,buyer)
	
	# Get the list of single period requests.
	# @param buyer Buyer.
	# @return List of single period requests.
	def getAcceptedSPBidRequests(self,buyer):
		return self._getAcceptedBidRequests(self._spBids,buyer)
	
	# Get the accepted energy constrained bids of a seller.
	# @param owner Seller.
	# @return List of energy constrained bids.
	def getAcceptedECBids(self,owner):
		l=[]
		for b in self._ecBids:
			if b.owner == owner and b.reservation > options.EPS:
				l.append(b)
		return l
	
	# Get the accepted single periods of a seller.
	# @param owner Seller.
	# @return List of single periods.
	def getAcceptedSPBids(self,owner):
		l=[]
		for b in self._spBids:
			if b.owner == owner and (b.acceptedMax > options.EPS or b.acceptedMin < -options.EPS):
				l.append(b)
		return l
	
	## Register a flexibility service user.
	# @param fsu Flexibility service user.
	def registerFSU(self, fsu):
		self._FSUs.append(fsu)
	
	## Register a energy constrained bid.
	# @param b ECBid.
	# @param data Data.
	def registerECBid(self,b,data):
		# Append the bid to the list
		b.id=len(self._ecBids)
		self._ecBids.append(b)
		
		# Append to the submitted quantities
		n=b.bus
		T=data.general['T']
		for t in range(T):
			data.general['S+'][n][t]+=b.max[t]
			data.general['S-'][n][t]+=b.min[t]
		
	## Register a single period.
	# @param b Classic bid.
	# @param data Data.
	def registerSPBid(self,b,data):
		# Append the bid to the list
		b.id=len(self._spBids)
		self._spBids.append(b)
		
		# Append to the submitted quantities
		n=b.bus
		t=b.t
		data.general['S+'][n][t]+=b.max
		data.general['S-'][n][t]+=b.min
			
	## Request a energy constrained bid.
	# @param bidId Bid Id.
	# @param buyer Buyer.
	# @param reservation Reservation indicator.
	def requestECBid(self,bidId,buyer,reservation):
		if reservation > options.EPS:
			bid=self._ecBids[bidId] 
			bid.requests.append(ECBidRequest(bid,buyer,reservation))
			
			if options.DEBUG:
				tools.log("\t\t\tECF request of %s in node %s" % (buyer.name,bid.bus), options.LOG, options.PRINT_TO_SCREEN)   
				
	## Request a single period.
	# @param bidId Bid Id.
	# @param buyer Buyer.
	# @param w Upward flexibility request (<0).
	# @param W Downward flexibility request (>0).
	def requestSPBid(self,bidId,buyer,w,W):
		if W > options.EPS or w < options.EPS:
			bid=self._spBids[bidId] 
			bid.requests.append(SPBidRequest(bid, buyer,w,W))
	
			if options.DEBUG:
				tools.log("\t\t\tSPF request of %s in node %s and period %s  [%s,%s]" % (buyer.name,bid.bus,bid.t,w,W), options.LOG, options.PRINT_TO_SCREEN)   
				
	## Get the number of energy constrained bids.
	# @return number of energy constrained bids.
	def ECBidsCount(self):
		return len(self._ecBids)
	
	## Get the number of classic control bids.
	# @return number of classic control bids.
	def spBidsCount(self):
		return len(self._spBids)
	
	## Assign a priority to request.
	# @param r Request.
	def fsuToPriorityRequest(r):
		buyer=r.buyer
		bid=r.bid
		if isinstance(buyer,DSO):
			return 1
		elif bid.bus in buyer.nodes:
			return 2
		elif isinstance(buyer, TSO):
			return 3
		return 4
	
	# Assign a priority to a flexibility service user.
	# @param fsu Flexibility service user.
	def fsuToPriority(fsu):
		if isinstance(fsu,DSO):
			return 1
		elif isinstance(fsu, TSO):
			return 2
		return 3
	
	## Settlement.
	# Mainly monitor the opposite usage of flexibility.
	def _settlement(self,data):
		T=data.general['T']
		N=data.general['N']
		
		for t in range(T):
			for n in range(N):
				if data.general['U+'][n][t] > options.EPS and -data.general['U-'][n][t] > options.EPS:
					data.general['O'][t]+=min(data.general['U+'][n][t],-data.general['U-'][n][t])
				data.general['TU'][t]+=data.general['U+'][n][t]-data.general['U-'][n][t]
				data.general['U'][t]+=data.general['U+'][n][t]+data.general['U-'][n][t]
				if data.general['z'][n][t]:
					data.general['Tripped flex.'][t]+=data.general['U+'][n][t]-data.general['U-'][n][t]
				
	## Clearing of the flexibility platform.
	# @param data Data.
	def _clearing(self,data): 
		self._FSUs.sort(key=FlexibilityPlatform.fsuToPriority)
		
		for fsu in self._FSUs:
			if options.DEBUG:
				tools.log("\t\tFlex clearing of %s. " % (fsu.name), options.LOG, options.PRINT_TO_SCREEN)   
			
			# Write the remaining offers
			if isinstance(fsu,DSO):
				self._writeRegisteredSPBids(data,True,data.general['interaction model'].DSOIsFSU)
				self._writeRegisteredECBids(data,True,data.general['interaction model'].DSOIsFSU)
			else:
				self._writeRegisteredSPBids(data)
				self._writeRegisteredECBids(data)
			
			# Propose the FSs to the FSU
			fsu.flexibilityEvaluation(data)
			
			# Clear single periods
			for b in self._spBids:
				# Sort the requests
				b.requests.sort(key=FlexibilityPlatform.fsuToPriorityRequest)
				
				for r in b.requests:
					if not r.acceptation:
						# Downward
						if r.w+options.EPS >= b.min-b.acceptedMin:
							r.aw=r.w
							b.acceptedMin+=r.w
							data.general['A-'][b.bus][b.t]+=r.w
							r.acceptation=True
							
							if isinstance(r.buyer,DSO):
								b.reservationBenefits+=b.dsoReservationCost*r.w
							else:
								b.reservationBenefits+=b.reservationCost*r.w
							
						# Upward
						if r.W-options.EPS <= b.max-b.acceptedMax:
							r.aW=r.W
							b.acceptedMax+=r.W
							data.general['A+'][b.bus][b.t]+=r.W
							r.acceptation=True
							if isinstance(r.buyer,DSO):
								b.reservationBenefits+=b.dsoReservationCost*r.W
							else:
								b.reservationBenefits+=b.reservationCost*r.W
							
			# Clear energy constrained bids	   
			for b in self._ecBids:
				if b.reservation < options.EPS:
					# Sort the requests
					b.requests.sort(key=FlexibilityPlatform.fsuToPriorityRequest)
					
					# Take the first request
					if len(b.requests) > 0:
						r=b.requests[0]
						b.reservation=r.reservation
						if r.reservation > options.EPS:
							r.acceptation=True
						if isinstance(r.buyer,DSO):
							b.reservationBenefits=b.dsoReservationCost
						else:
							b.reservationBenefits=b.reservationCost
						
						# Append to the accepted quantities
						n=b.bus
						T=data.general['T']
						for t in range(T):
							data.general['A+'][n][t]+=b.max[t]
							data.general['A-'][n][t]+=b.min[t]
				 
		# Display quantities
		if options.DEBUG:
			N=data.general['N']
			for n in range(N):
				if sum(data.general['S+'][n])+sum(data.general['S-'][n]) > options.EPS:
					tools.log("\t\tNode %s :" % n, options.LOG, options.PRINT_TO_SCREEN)
					tools.log("\t\t\tA+ : %s" % (data.general['A+'][n]), options.LOG, options.PRINT_TO_SCREEN)	
					tools.log("\t\t\tS+ : %s" % (data.general['S+'][n]), options.LOG, options.PRINT_TO_SCREEN)	
					tools.log("\t\t\tA- : %s" % (data.general['A-'][n]), options.LOG, options.PRINT_TO_SCREEN)	
					tools.log("\t\t\tS- : %s" % (data.general['S-'][n]), options.LOG, options.PRINT_TO_SCREEN)	   
	
	## Write the registered single periods to the single periods data file.
	# @param data Data.
	# @param dsoCosts Consider DSO costs instead of the normal one. Default: False.
	# @param allBids If false, write only obligation bids. Default : True
	def _writeRegisteredSPBids(self,data,dsoCosts=False,allBids=True):
		with open(options.FOLDER+'/'+FlexibilityPlatform.spBidsDataFile, 'w') as file:
			T=data.general['T']
			B=len(self._spBids)
			file.write("# B, T\n%s,%s\n" % (B+1,T))
			file.write("# b, n, t, pi^r, pi^a, m, M\n")
			for b in self._spBids:
				if not allBids and not isinstance(b, SPObligationBid):
					file.write("%s,%s,%s,%s,%s,%s,%s\n" % (b.id,b.bus,b.t+1,options.INF,0,0,0))
				elif dsoCosts:
					file.write("%s,%s,%s,%s,%s,%s,%s\n" % (b.id,b.bus,b.t+1,b.dsoReservationCost,b.dsoActivationCost,min(b.min-b.acceptedMin,0),max(b.max-b.acceptedMax,0)))
				else:
					file.write("%s,%s,%s,%s,%s,%s,%s\n" % (b.id,b.bus,b.t+1,b.reservationCost,b.activationCost,min(b.min-b.acceptedMin,0),max(b.max-b.acceptedMax,0)))
			file.write("%s,%s,%s,%s,%s,%s,%s\n" % (B,0,1,options.INF,0,0,0))
			
	## Write the registered energy constrained bids to the flexible loads data file.
	# @param data Data.
	# @param dsoCosts Consider DSO costs instead of the normal one. Default: False.
	# @param allBids If false, write only obligation bids. Default : True
	def _writeRegisteredECBids(self,data,dsoCosts=False,allBids=True):
		with open(options.FOLDER+'/'+FlexibilityPlatform.ecBidsDataFile, 'w') as file:
			T=data.general['T']
			B=len(self._ecBids)
			file.write("# B, T\n%s,%s\n" % (B+1,T))
			file.write("# b, n, pi^r, pi^a\n")
			for b in self._ecBids:
				if b.reservation > options.EPS or (not allBids and not isinstance(b, ECObligationBid)):
					file.write("%s,%s,%s,%s\n" % (b.id,b.bus,options.INF,0))
				elif dsoCosts:
					file.write("%s,%s,%s,%s\n" % (b.id,b.bus,b.dsoReservationCost, b.dsoActivationCost))
				else:
					file.write("%s,%s,%s,%s\n" % (b.id,b.bus,b.reservationCost, b.activationCost))
			file.write("%s,%s,%s,%s\n" % (B,0,options.INF,0)) # Dummy bid
			
			file.write("# b, t, m, M\n")
			for b in self._ecBids:
				for t in range(T):
					if allBids:
						file.write("%s,%s,%s,%s\n" % (b.id,t+1,min(b.min[t]*(1-b.reservation),0),max(b.max[t]*(1-b.reservation),0)))
					else:
						file.write("%s,%s,%s,%s\n" % (b.id,t+1,0,0))
			# Dummy bid
			for t in range(T):
				file.write("%s,%s,%s,%s\n" % (B,t+1,0,0))
		
	## @var _ecBids
	# List of registered energy constrained bids.
	## @var _spBids
	# List of registered single periods.
	## @var _FSUs
	# List of flexibility service users.
	# This attribute is not cleaned by the the clean method.
	