##@package spbid
#@author Sebastien MATHIEU

from .bid import Bid, BidRequest
from . import options

# Request of a single period bid.
class SPBidRequest(BidRequest):
    ## Constructor
    # @param bid Corresponding bid.
    # @param buyer Buyer.
    # @param w Downward flexibility request (<0).
    # @param W Upward flexibility request (>0).
    def __init__(self,bid,buyer,w,W):
        BidRequest.__init__(self,bid,buyer)
        self.w=w
        self.W=W
        self.acceptation=0
        self.aw=0
        self.aW=0
            
    ## @var w
    # Downward flexibility request (<0).
    ## @var W
    # Upward flexibility request (>0).
    ## @var aw
    # Acceptation of the downward request in volume.
    ## @var aW
    # Acceptation of the upward request in volume.

## Single period bid.
# Sign convention is positive for production.
# The reference is 0: min <= 0 <= max.
class SPBid(Bid):
    ## Constructor.
    # @param t Period.
    # @param id Identification number of the bid.
    # @param bus Bus of the bid.
    # @param rc Reservation cost of the bid.
    # @param ac Activation cost of the bid.
    # @param dsoRc Reservation cost of the bid for the DSO.
    # @param dsoAc Activation cost of the bid for the DSO.
    # @param owner Owner of the bid.
    def __init__(self,t,id=0,bus=0,rc=options.EPS,ac=options.EPS,dsoRc=options.EPS,dsoAc=options.EPS,owner=""):
        Bid.__init__(self,t,id,bus,rc,ac,dsoRc,dsoAc,owner)
        
        self.min=0.0
        self.max=0.0
        self.acceptedMin=0.0
        self.acceptedMax=0.0
        self.modulation=0.0
        
    ## @var min
    # Minimum flexibility.
    ## @var max
    # Maximum flexibility.
    ## @var acceptedMin
    # Accepted minimum flexibility.
    ## @var acceptedMax
    # Accepted maximum flexibility.
    ## @var modulation
    # Modulation request.
    
## Single period obligation bid.
class SPObligationBid(SPBid):
    ## Constructor.
    # @param t Period.
    # @param id Identification number of the bid.
    # @param bus Bus of the bid.
    # @param rc Reservation cost of the bid.
    # @param ac Activation cost of the bid.
    # @param dsoRc Reservation cost of the bid for the DSO.
    # @param dsoAc Activation cost of the bid for the DSO.
    # @param owner Owner of the bid.
    def __init__(self,t,id=0,bus=0,rc=options.EPS,ac=options.EPS,dsoRc=options.EPS,dsoAc=options.EPS,owner=""):
        SPBid.__init__(self, t, id, bus, rc, ac, dsoRc, dsoAc, owner)
