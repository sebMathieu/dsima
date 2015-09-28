##@package timedata
#@author Sebastien MATHIEU

import csv,math

## Set of timedata.
class TimeData:
	## Constructor.
	# @param folderPath Folder with the timedata files. @see TimeData.readFromFolder
	def __init__(self,folderPath=None):
		self.energyPrices=[]
		self.windPower=[]
		self.load=[]
		self.upwardImbalancePrices=[]
		self.downwardImbalancePrices=[]
		self.systemImbalance=[]
		
		if folderPath:
			self.readFromFolder(folderPath)
			
	## Get the mean and the maximum value excluding the extreme one.
	# @param datalist List of data
	# @param excludedProportion Proportion of data to be excluded.
	# @return Tuple (mean,max) values.
	def getMeanMax(datalist,excludedProportion=0.025):
		maxIndex=math.ceil(excludedProportion*len(datalist))
		return sum(datalist)/len(datalist),sorted(datalist)[-maxIndex]
	
	## Adjust a list of floats to meet a given mean and max value.
	# @param datalist List of floats.
	# @param newMean New mean of the resulting list.
	# @param newMax New max of the resulting list.
	# @return Adjusted maplist of floats.
	def adjustMeanMax(datalist,newMean=0,newMax=1):
		iMean,iMax=TimeData.getMeanMax(datalist)
		return map(lambda x : (x-iMean)*(newMax-newMean)/(iMax-iMean)+newMean, datalist)
		
	## Get the value for a period t in {0,...T-1} from a data vector.
	# If the length of data is greater than T, take the mean values of the data covered by the period t.
	# It the length of data is less or equal than T, take the corresponding value.	
	# @param data Data as a vector of numbers.
	# @param t Period index
	# @param T Number of periods in the output time horizon.
	def periodValue(data, t, T):
		N=len(data)
		if N > T:
			omega=math.floor(N/T)
			return sum(data[omega*t:omega*(t+1)])/omega
		else:
			return data[math.floor(t/(T/N))]
			
	## Read timedata from a folder.
	# @param folderPath Folder with the timedata files.
	# The folder should contains the following files:
	#	- energyPrices.csv
	#	- load.csv
	#	- windPower.csv
	def readFromFolder(self,folderPath):
		for p in ['energyPrices','load','windPower','downwardImbalancePrices','upwardImbalancePrices','systemImbalance']:
			setattr(self,p,self.readColumn("%s/%s.csv"%(folderPath,p.lower()),2))
		self._buildImbalancePricesForecast()
	
	## Read a column of a csv file.
	# @param filePath Path to the csv file.
	# @param column Column index.
	# @return List with the column entries converted to float.
	def readColumn(self,filePath,column=0):
		result=[]
		COMMENT_CHAR='#'
		DELIMITER_CHAR=','

		with open(filePath, 'r') as csvfile:
			csvReader = csv.reader(csvfile, delimiter=DELIMITER_CHAR, quotechar='\"')
			for row in csvReader:
				if not row[0].startswith(COMMENT_CHAR):
					result.append(float(row[column]))

		return result

	## Replace the read upward and downward imbalance prices by forecasts based on the previous data.
	def _buildImbalancePricesForecast(self):
		TOL=0.01
		T=len(self.energyPrices)
		if len(self.upwardImbalancePrices) != T or len(self.downwardImbalancePrices)!= T:
			raise Exception("Upward and/or downward imbalance prices vector does not have the same size.")
		
		for t in range(T):
			piE=self.energyPrices[t]
			
			# See if what data we need
			needUpward=(self.upwardImbalancePrices[t] <= TOL)
			needDownward=(self.downwardImbalancePrices[t] <= TOL)
			if not needUpward and not needDownward:
				continue
			
			# Get the period with the closest energy price starting from t
			closest=t
			k=1
			maxDifference=float('Inf')
			while k < max(t,T-t):
				# Check previous periods
				tau=t+k
				if tau < T and ((needUpward and self.upwardImbalancePrices[tau] > TOL) or (needDownward and self.downwardImbalancePrices[tau] > TOL)):
					difference=self.energyPrices[tau]-t
					if abs(maxDifference) > difference:
						closest=tau
						maxDifference=difference
						if maxDifference < 0.01:
							break
				
				# Check future periods
				tau=t-k
				if tau >= 0 and ((needUpward and self.upwardImbalancePrices[tau] > TOL) or (needDownward and self.downwardImbalancePrices[tau] > TOL)):
					difference=self.energyPrices[tau]-t
					if abs(maxDifference) > difference:
						closest=tau
						maxDifference=difference
						if maxDifference < 0.01:
							break
			
				k+=1
			
			# If null imbalance price set it to the closest one
			if needUpward:
				self.upwardImbalancePrices[t]=self.upwardImbalancePrices[closest]
			if needDownward:
				self.downwardImbalancePrices[t]=self.downwardImbalancePrices[closest]
		
	## @var energyPrices
	# Energy prices for each quarter.
	## @var windPower
	# Wind powers for each quarter.
	## @var load
	# Load consumption for each quarter.
	## @var upwardImbalancePrices
	# Upward imbalance prices for each quarter.
	## @var downwardImbalancePrices
	# Upward imbalance prices for each quarter.
	## @var systemImbalance
	# System imbalance for each quarter.
