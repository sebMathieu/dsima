##@package bid
#@author Sebastien MATHIEU

from . import options

# Bid request.
class BidRequest:
    ## Constructor
    # @param bid Corresponding bid.
    # @param buyer Buyer with an attribute 'nodes' with a list of nodes.
    def __init__(self,bid,buyer):
        self.buyer=buyer
        self.bid=bid
        self.acceptation=False
            
    ## @var bid
    # Corresponding bid.
    ## @var buyer 
    # Buyer.
    ## @var acceptation 
    # Boolean true for the partial or total acceptation of the reservation. 
    
## Bid.
class Bid:
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
        self.t=t
        self.id=id
        self.bus=bus
        self.reservationCost=rc
        self.activationCost=ac
        self.dsoReservationCost=dsoRc
        self.dsoActivationCost=dsoAc
        self.owner=owner
        self.requests=[]
        self.reservationBenefits=0.0
        self.activationBenefits=0.0
        
    ## @var id
    # Identification number of the bid.
    ## @var bus
    # Bus of the bid.
    ## @var t
    # Period of application.
    ## @var reservationCost
    # Reservation cost of the bid.
    ## @var activationCost
    # Activation cost of the bid.
    ## @var requests
    # List of buyer's requests for a bid.
    ## @var reservationBenefits
    # Benefits from the reservation costs computed by the flexibility platform.
    ## @var activationBenefits
    # Benefits from the activation costs computed by the flexibility platform.
    ## @var dsoReservationCost
    # Reservation cost of the bid for the DSO.
    ## @var dsoActivationCost
    # Activation cost of the bid for the DSO.
