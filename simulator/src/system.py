##@package system
#@author Sebastien MATHIEU

import glob,os.path,shutil,csv,time,datetime

from .agent.stateSystem import StateSystem
from .agent.layer import Layer
from .ephemerallayer import EphemeralLayer
from .dso import DSO
from .tso import TSO
from .retailer import Retailer
from .producer import Producer
from .flexibilityplatform import FlexibilityPlatform
from .interactionmodel import InteractionModel
from .quantitativecriteria import QuantitativeCriteria
from . import options,tools,xmlsolution
from .solver.scipsolver import ScipSolver
from .solver.cplexsolver import CplexSolver

## Class that generates the system from a data folder.
# The system class defines the following global data:
#	 - DSO,TSO, flexibilityPlatform : pointing to the instance of the actors.
#	 - time : After a run, provides the time taken.
#	 - iterations : After a run, provides the number of iterations performed.
#	 - T : Number of periods in the system.
#	 - N : Number of nodes.
#	 - pi^i : Nodal imbalance price in case of DSO network failure.
#	 - pi^E, pi^I+, pi^I- : For each period, the energy price and the downward and upward imbalance tariffs.
class System(StateSystem):
	## Name of the file with the prices.
	pricesFile="prices.csv"
	## Name of the data file for the network.
	networkFile='network.csv'
	
	## Constructor
	# @param dataFolder Folder with the data of the whole market.
	# @param maximumIterations Maximum number of iterations. 
	# @param outputSolutionFile XML output solution file.
	# @param convergenceTolerance Numerical tolerance for the convergence criteria. If none, set to options.EPS
	def __init__(self,dataFolder, maximumIterations=1000,outputSolutionFile="data.xml",convergenceTolerance=None):
		if convergenceTolerance is None:
			convergenceTolerance=options.EPS
		StateSystem.__init__(self,maximumIterations=maximumIterations,accuracy=convergenceTolerance)
		
		self._dataFolder=dataFolder
		self._outputSolutionFile=outputSolutionFile
		self.generate()
		
	## Generate the system.
	def generate(self):
		self._readGeneralData()
		
		# Instantiate solver
		if options.SOLVER == 'cplex':
			self.data.general['solver']=CplexSolver(lp=options.DEBUG)

			if options.DEBUG:
				tools.log("Solve using CPLEX.", options.LOG, options.PRINT_TO_SCREEN)
		else:
			self.data.general['solver']=ScipSolver(lp=options.DEBUG)

		# Create the quantifier
		quantifier=QuantitativeCriteria()
		
		# Create the flexibility platform
		flexibilityPlatform=FlexibilityPlatform()
		self.data.general['flexibilityPlatform']=flexibilityPlatform
		
		# Interaction models
		iteractionModelFilePath='%s/interaction-model.csv'%self._dataFolder
		if os.path.isfile(iteractionModelFilePath):
			self.data.general['interaction model']=InteractionModel(iteractionModelFilePath)
		else:
			self.data.general['interaction model']=InteractionModel()
		
		# Create the DSO
		self._dso=DSO(self._dataFolder+'/network.csv', self._dataFolder+'/qualified-flex.csv')
		self.data.general['DSO']=self._dso
		quantifier.registerUser(self._dso)
		
		# Create the TSO
		self._tso=TSO(self._dataFolder+'/tso.csv')
		self.data.general['TSO']=self._tso
		quantifier.registerUser(self._tso)
		
		# Retailers
		self._retailers=[]
		retailersList=glob.glob(self._dataFolder+'/retailers/*.csv')
		for file in retailersList:
			fileName=os.path.splitext(os.path.basename(file))[0]
			r=Retailer(dataFile=file,name=fileName)
			self._retailers.append(r)
			quantifier.registerUser(r)
		
		if options.DEBUG:
			tools.log("System with %s retailer(s)." % (len(retailersList)), options.LOG, options.PRINT_TO_SCREEN)
		
		# Producers
		self._producers=[]
		producersList=glob.glob(self._dataFolder+'/producers/*.csv')
		for file in producersList:
			fileName=os.path.splitext(os.path.basename(file))[0]
			p=Producer(dataFile=file,name=fileName)
			self._producers.append(p)
			quantifier.registerUser(p)
		
		if options.DEBUG:
			tools.log("System with %s producer(s)." % (len(producersList)), options.LOG, options.PRINT_TO_SCREEN)
		
		# Layers
		#--------		
		# Cleaning the flexibility platform
		self.layerList.append(Layer([self.data.general['flexibilityPlatform']],name="Flexibility platform cleaning"))
		
		# Bounds requesting
		self._dso.setGridUsers(self._producers+self._retailers)
		self.layerList.append(EphemeralLayer([self._dso],name="Access agreement"))
		
		# Optimization of the baselines
		if self.data.general['interaction model'].accessRestriction.lower() == "dynamicbaseline":
			self.layerList.append(Layer(self._retailers+self._producers, name="Baseline proposal"))
			self.layerList.append(Layer([self._dso], name="Dynamic ranges computation"))
			self.layerList.append(Layer(self._retailers+self._producers, name="Baseline optimization"))
		else:
			self.layerList.append(Layer(self._retailers+self._producers, name="Baseline optimization"))

		# Determination of the flexibility needs
		self.layerList.append(Layer([self._dso,self._tso], name="Flexibility needs"))
		
		# Flexibility offers
		self.layerList.append(Layer(self._retailers+self._producers, name="Flexibility optimization"))
		
		# Flexibility platform clearing
		self.layerList.append(Layer([flexibilityPlatform],name="Flexibility platform clearing"))
	
		# Flexibility activation
		self.layerList.append(Layer([self._dso,self._tso]+self._producers+self._retailers, name="Flexibility activation requesting"))
		
		# Create the second optimization layer
		self.layerList.append(Layer(self._retailers+self._producers, name="Imbalance optimization")) 
		
		# Create the operation layer
		self.layerList.append(Layer([self._dso], name="Operation"))
		
		# Create the settlement layer
		self.layerList.append(Layer([self._dso,flexibilityPlatform]+self._retailers+self._producers, name="Settlement"))
	
		# Quantification layer
		self.layerList.append(Layer([quantifier], name="Quantification"))
		
	
	def run(self):
		tic=time.time()
		
		tools.clearFolder(options.FOLDER)
		self._prepareOperationFolder()
		tools.safeCopy(self._dataFolder+System.pricesFile,options.FOLDER+'/'+System.pricesFile)
		runningResult=StateSystem.run(self)
		
		self.data.general['time']=time.time()-tic
		self.data.general['iterations']=self.iterations
		
		xmlsolution.export(self._outputSolutionFile,self.data,[self._dso,self._tso]+self._producers+self._retailers)
		
		return runningResult
	
	def hasConverged(self):
		returnValue=StateSystem.hasConverged(self)
		tools.log("\tMaximum difference : %s" % (self._maxDifference), options.LOG, options.PRINT_TO_SCREEN)
		if returnValue == None:
			tools.log("Iteration %s" % (self.iterations+1), options.LOG, options.PRINT_TO_SCREEN)
		return returnValue
	
	## Prepare the operation folder.
	# Creates it if needed and copy the models into it.
	def _prepareOperationFolder(self):
		# Create the operation folder if it doesn't exists
		if not os.path.exists(options.FOLDER):
			os.makedirs(options.FOLDER)
			
		MODEL_FOLDER='models'
		for filename in os.listdir(MODEL_FOLDER):
			file='%s/%s'%(MODEL_FOLDER,filename)
			if os.path.isfile(file):
				tools.safeCopy(file,'%s/%s'%(options.FOLDER,filename))
			
	## Read general data of the system. 
	def _readGeneralData(self):
		self.data.general['T']=0
		
		# Read prices
		with open(self._dataFolder+'/'+System.pricesFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			
			# Get first row, T
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			T=int(row[0])
			self.data.general['T']=T
			options.EPS=float(row[1])   
			self.data.general['dt']=float(row[3])
			self.data.general['pi^i']=float(row[2])*self.data.general['dt']    
			
			# Get prices
			i=0
			self.data.general['pi^E']=[0.0]*T
			self.data.general['pi^I+']=[0.0]*T
			self.data.general['pi^I-']=[0.0]*T
			while i<T:
				row=[options.COMMENT_CHAR]
				while row[0].startswith(options.COMMENT_CHAR):
					row=next(csvReader)
				
				t=int(row[0])-1
				
				self.data.general['pi^E'][t]=float(row[1])*self.data.general['dt']       
				self.data.general['pi^I+'][t]=float(row[2])*self.data.general['dt']       
				self.data.general['pi^I-'][t]=float(row[3])*self.data.general['dt']       
				
				i+=1
		
		# Read network parameters
		with open(self._dataFolder+'/'+System.networkFile, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			
			# Get first row, N
			row=[options.COMMENT_CHAR]
			while row[0].startswith(options.COMMENT_CHAR):
				row=next(csvReader)
			self.data.general['N']=int(row[0])
		
				
	## @var _dataFolder
	# Folder with the data of the whole market. 
	## @var _dso
	# DSO.
	## @var _tso
	# TSO.
	## @var _flexibilityPlatform
	# Flexibility platform.
	## @var _retailers
	# List of retailers.
	## @var _producers
	# List of producers.
	## @var _outputSolutionFile
	# XML output solution file.
	