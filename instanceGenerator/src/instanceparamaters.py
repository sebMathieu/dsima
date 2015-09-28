##@package instanceparameters
#@author Sebastien MATHIEU

import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import ParseError

## Instance paramaters structure.
class InstanceParameters:
	## Constructor
	# @param filePath Path of xml data file.
	def __init__(self,filePath=None):
		self.hash=""
		self.network=""
		self.periods=1
		self.producers=1
		self.retailers=1
		self.production=None
		self.consumption=None
		self.prices=None
		self.days=None
		self.imParameters=[]
		self.tsoFlexibilityRequest=0
		self.tsoReservationPrice=0
		
		if filePath:
			self.readFile(filePath)
	
	## Read paramaters of the instance from an xml file.
	# @param filePath Path of xml data file.
	def readFile(self,filePath):
		try:
			root=ElementTree.parse(filePath).getroot()
			
			self.hash=root.find('hash').text
			self.network=root.find('network').text
			self.T=int(root.find('periods').text)
			
			self.producers=int(root.find('producers').text)
			self.retailers=int(root.find('retailers').text)
			
			tag=root.find('production')
			self.production={'mean':float(tag.find('mean').text),
							'max':float(tag.find('max').text),
							'flexibility':float(tag.find('flexibility').text),
							'costs':float(tag.find('costs').text),
							'externalimbalance':float(tag.find('externalimbalance').text)
							}
						 
			tag=root.find('consumption')
			self.consumption={'mean':float(tag.find('mean').text),
							'max':float(tag.find('max').text),
							'flexibility':float(tag.find('flexibility').text),
							'benefits':float(tag.find('benefits').text),
							'externalimbalance':float(tag.find('externalimbalance').text),
							'flexreservationcost':float(tag.find('flexreservationcost').text)
							}
			
			tag=root.find('prices')
			self.prices={'mean':float(tag.find('mean').text),
						 'max':float(tag.find('max').text)}
			
			tag=root.find('days')
			self.days=list(range(int(tag.find('start').text), int(tag.find('end').text)))
			
			tag=root.find('tso')
			self.tsoFlexibilityRequest=float(tag.find('flexibilityrequest').text)
			self.tsoReservationPrice=float(tag.find('reservationprice').text)

			tag=root.find('im')
			for t in tag:
				if t.tag == "parameter":
					self.imParameters.append((t.get('id'),t.text));
			
		except ParseError as e:
			raise e
		except AttributeError as e:
			raise e
		
	## @var hash
	# Hash code of the instance.
	## @var network
	# Network base.
	## @var T
	# Number of periods per day.
	## @var producers
	# Number of producers.
	## @var retailers
	# Number of retailers.
	## @var production
	# Production parameters dictionary.
	## @var consumption
	# Consumption parameters dictionary.
	## @var prices
	# Prices parameters dictionary.
	## @var days
	# List of days index in [0,364].
	## @var tsoFlexibilityRequest
	# Flexibility request of the TSO with respect in MW.
	## @var tsoReservationPrice
	# Regulated TSO reservation price.
	## @var imParameters
	# List of parameters of the interaction model, tuple (name,value).
	