##@package ecbid
#@author Sebastien MATHIEU

from .bid import Bid, BidRequest
from . import options

# Request of a energy constrained bid.
class ECBidRequest(BidRequest):
    ## Constructor
    # @param bid Corresponding bid.
    # @param buyer Buyer.
    # @param reservation Reservation indicator.
    def __init__(self,bid,buyer,reservation):
        BidRequest.__init__(self,bid,buyer)
        self.reservation=reservation
    
    ## @var reservation 
    # Reservation indicator.

## Energy constrained bid.
# Sign convention is positive for production.
# The reference is 0: min <= 0 <= max.
class ECBid(Bid):
    ## Constructor.
    # @param T Number of periods.
    # @param id Identification number of the bid.
    # @param bus Bus of the bid.
    # @param rc Reservation cost of the bid.
    # @param ac Activation cost of the bid.
    # @param dsoRc Reservation cost of the bid for the DSO.
    # @param dsoAc Activation cost of the bid for the DSO.
    # @param owner Owner of the bid.
    def __init__(self,T,id=0,bus=0,rc=options.EPS, ac=options.EPS, dsoRc=options.EPS,dsoAc=options.EPS, owner=""):
        Bid.__init__(self,T,id,bus,rc,ac,dsoRc,dsoAc,owner)
        
        self.reservation=0
        self.min=[0.0]*T
        self.max=[0.0]*T
        self.modulation=[0.0]*T
        
    ## @var reservation
    # Reservation status of a bid in [0,1].
    ## @var min
    # Minimum flexibility for each period.
    ## @var max
    # Maximum flexibility for each period.
    ## @var modulation
    # Modulation request for each period.
    
## Energy constrained obligation bid.
class ECObligationBid(ECBid):
    ## Constructor.
    # @param T Number of periods.
    # @param id Identification number of the bid.
    # @param bus Bus of the bid.
    # @param rc Reservation cost of the bid.
    # @param ac Activation cost of the bid.
    # @param dsoRc Reservation cost of the bid for the DSO.
    # @param dsoAc Activation cost of the bid for the DSO.
    # @param owner Owner of the bid.
    def __init__(self,T,id=0,bus=0,rc=options.EPS, ac=options.EPS, dsoRc=options.EPS,dsoAc=options.EPS, owner=""):
        ECBid.__init__(self, T, id, bus, rc, ac, dsoRc, dsoAc, owner)
    
    