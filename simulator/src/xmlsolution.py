##@package xmlsolution
#@author Sebastien MATHIEU

import time,re,zlib,zipfile,decimal
from . import options

## Get the maximum value of an index.
# @param vect Vector of elements.
# @return value,index+1.
def maxValueAndIndex(vect):
	val,index=max((abs(v), i) for i, v in enumerate(vect))
	return vect[index],index+1

## Convert a list of floats to a string where the floats are separated by a comma.
# @param floatList List of floats.
def floats2str(floatList):	
	return ",".join(map(lambda x: "%.4f"%x , floatList))

## Translate dictionary
TRANSLATE_DICT={
	'I':'Imbalance','O':'Opposite usage of flexibility','TU':'Total usage of flexibility',
	'R+':'Requirement of upward flexibility','R-':'Requirement of downward flexibility',
	'S+':'Submitted upward flexibility','S-':'Submitted downward flexibility',
	'A+':'Upward flexibility contracted','A-':'Downward flexibility contracted',
	'U+':'Activated upward flexibility','U-':'Activated downward flexibility',
	'pi^E':'Energy price','pi^I+':'Upward imbalance price','pi^I-':'Downward imbalance price',
	'C':'Line capacity','dC':'Max. capacity upgrade',
	'g':'Downward access request bound','G':'Upward access request bound',
	'b':'Safe downward access bound','B':'Safe upward access bound',
	'k':'Downward flexible access bound','K':'Upward flexible access bound',
	'l':'Downward full access bound','L':'Upward full access bound',
	'v':'Voltage', 'phi':'Voltage angle', 'q': 'Reactive power',
	'v^r':'Corrected voltage', 'phi^r':'Corrected voltage angle', 'q^r': 'Corrected reactive power',
	'v^b':'Baseline voltage', 'phi^b':'Baseline voltage angle', 'q^b': 'Baseline reactive power',
	'p^b':'Local baseline','p^r':'Local corrected baseline','p':'Local realization','p^p':'Baseline proposal',
	'P^b':'Global baseline','P^r':'Global corrected baseline','P':'Global realization',
	'H':'Flexibility request','U':'Flexibility activation',
	'h':'Local flexibility request','u':'Local flexibility activation',
	'f^b':'Announced flow','f^r':'Corrected flow','f':'Flow realization',
	'dpL^max':'Maximum upward dynamic flexibility', 'dpU^max':'Maximum downward dynamic flexibility',
	'dpL':'Upward dynamic flexibility', 'dpU':'Downward dynamic flexibility',
	'd':'Downward periodic access bound', 'D':'Upward periodic access bound'
}

## Translate an internal symbol to a user comprehensive text.
# @param symbol Symbol to translate.
# @return The translation. If no correspondance is found, returns the symbol itself.
def translate(symbol):
	try:
		v=TRANSLATE_DICT[symbol]
		symbol=v
	except KeyError:
		pass
	return symbol

## Export the solution to a XML file.
# @param xmlPath Path to the XML file.
# @param data Data.
# @param externs List of externs to the image which needs to output data. 
# The externs should implement a method "xmlData" which takes the data structure as argument and returns a string with the data.
def export(xmlPath,data,externs=[]):
	#Fist create the xmlContent
	xmlContent='<?xml version="1.0" encoding="ISO-8859-1" ?>\n<xml>\n'
	
	# Periods
	T=data.general['T']
	N=data.general['N']
	xmlContent+='<periods>%s</periods>\n'%T	 
	
	# External elements
	if len(externs) > 0:
		xmlContent+='<externals>\n'
		for e in externs:
			xmlContent+=e.xmlData(data)
		xmlContent+='</externals>\n'
		
	# General
	xmlContent+='<general>\n'
	xmlContent+='\t<data id="Solved">%s</data>\n'% time.strftime("%H:%M:%S %d/%m/%Y")
	xmlContent+='\t<data id="Time">%s</data>\n' % data.general['time']
	xmlContent+='\t<data id="Iterations">%s</data>\n' % data.general['iterations']
	xmlContent+='\t<data id="OPF method">%s</data>\n' % options.OPF_METHOD
	
	xmlContent+='\t<data id="Welfare">%.5f</data>\n' % data.personal["Quantitative criteria"]['welfare'][0]
	xmlContent+='\t<data id="DSOs costs">%.5f</data>\n' % data.personal["Quantitative criteria"]['dsosCosts'][0]
	xmlContent+='\t<data id="Protections cost">%.5f</data>\n' % (data.personal['Quantitative criteria']['protectionsCost'][0])
	xmlContent+='\t<data id="TSOs surplus">%.5f</data>\n' % -data.personal["Quantitative criteria"]['tsosCosts'][0]
	xmlContent+='\t<data id="Producers surplus">%.5f</data>\n' % -data.personal["Quantitative criteria"]['producersCosts'][0]
	xmlContent+='\t<data id="Retailers surplus">%.5f</data>\n' % -data.personal["Quantitative criteria"]['retailersCosts'][0]
	
	xmlContent+='\t<data id="Total energy shed">%.5f</data>\n' % sum(data.general['Shed quantities'])
	xmlContent+='\t<data id="Total production">%.5f</data>\n' % sum(data.general['Total production'])
	xmlContent+='\t<data id="Total consumption">%.5f</data>\n' % sum(data.general['Total consumption'])
		
	xmlContent+='\t<data id="Max. imbalance">%.5f</data>\n' % maxValueAndIndex(data.general['I'])[0]
	xmlContent+='\t<data id="Total imbalance">%.5f</data>\n' % (sum(map(abs,data.general['I']))*data.general['dt'])
	
	xmlContent+='\t<data id="Total opp. usage of flex.">%.5f</data>\n' % (sum(data.general['O'])*data.general['dt'])
	xmlContent+='\t<data id="Total usage of flex.">%.5f</data>\n' % (sum(data.general['TU'])*data.general['dt'])
	
	# List of general time depedent attributes
	for attr in ['I','O','TU','U']:
		xmlContent+='\t<timedata id="%s">%s</timedata>\n'%(translate(attr),floats2str(data.general[attr]))
	
	# List of general time depedent attributes to aggregate from nodal data
	for attr in ['R+','R-','S+','S-','A+','A-','U+','U-']:
		values=[]
		for t in range(T):
			v=0.0
			for n in range(N):
				v+=data.general[attr][n][t]
			values.append(v)			
		xmlContent+='\t<timedata id="%s">%st</timedata>\n'%(translate(attr),floats2str(values))
	
	# Time graphs
	# Prices
	xmlContent+='\t<timegraph id="prices" title="Prices" ylabel="Price [euro/MW period]">\n'
	for attr in ['pi^E','pi^I+','pi^I-']:
		xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.general[attr]))
	xmlContent+='\t</timegraph>\n'
	
	# Sheddings
	xmlContent+='\t<timegraph id="sheddings" title="" ylabel="Shed quantities [MWh]">\n'
	xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'% ('Shed quantities',floats2str(data.general['Shed quantities']))
	xmlContent+='\t</timegraph>\n'
	
	# Flexibility graph
	xmlContent+='\t<timegraph id="fs" title="" ylabel="Power [MW]">\n'
	for attr in ['R+','R-','S+','S-','A+','A-','U+','U-']:
		values=[]
		for t in range(T):
			v=0.0
			for n in range(N):
				v+=data.general[attr][n][t]
			values.append(v)
		xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(values))
	xmlContent+='\t</timegraph>\n'

	xmlContent+='</general>\n'   
	
	# Elements
	xmlContent+='<elements>\n'
	
	# Lines
	dsoName="DSO"
	for l in range(1, data.personal[dsoName]['L']+1):
		xmlContent+='\t<element id="LINE%s" name="Line %s">\n'%(l,l)
		
		# Data
		xmlContent+='\t\t<data id="Line capacity">%s</data>\n' % (data.personal[dsoName]['C'][l])
		maxdC, maxdCIndex=maxValueAndIndex(data.personal[dsoName]['dC'][l])
		if maxdC > options.EPS:
			xmlContent+='\t\t<data id="Max. capacity upgrade">%.5f in period %s</data>\n' % (maxdC,maxdCIndex)
		else:
			xmlContent+='\t\t<data id="Max. capacity upgrade">%.5f</data>\n' % (maxdC)
			
		# Baseline graph
		xmlContent+='\t<timegraph id="baseline" title="" ylabel="Power [MW]">\n'
		xmlContent+='\t\t<timegraphdata id="Line capacity">%s</timegraphdata>\n'%(floats2str([data.personal[dsoName]['C'][l]]*T))
		xmlContent+='\t\t<timegraphdata id="- Line capacity">%s</timegraphdata>\n'%(floats2str([-data.personal[dsoName]['C'][l]]*T))
		for attr in ['f^b','f^r','f','flow violation']:
			xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.personal[dsoName][attr][l]))
		xmlContent+='\t</timegraph>\n'
		
		# Style
		xmlContent+='\t\t<timestyle>\n'
		xmlContent+='\t\t\t<default>'
		maxFlowViolation=max(data.personal[dsoName]['flow violation'][l])
		if maxFlowViolation > options.EPS:
			xmlContent+='fill:#A20025;stroke:#A20025;stroke-width:2'
		elif maxdC > options.EPS:
			xmlContent+='fill:#1BA1E2;stroke:#1BA1E2;stroke-width:2'
		else:
			xmlContent+='fill:#000000;stroke:#000000;stroke-width:2'
		xmlContent+='</default>\n'
		timeStyles=[]
		for t in range(T):
			if data.personal[dsoName]['flow violation'][l][t] > options.EPS:
				timeStyles.append('fill:#A20025;stroke:#1BA1E2;stroke-width:2')
			elif data.personal[dsoName]['dC'][l][t] > options.EPS:
				timeStyles.append('fill:#1BA1E2;stroke:#1BA1E2;stroke-width:2')
			else:
				timeStyles.append('fill:#000000;stroke:#000000;stroke-width:2')
		xmlContent+='\t\t\t<periods>%s</periods>\n'%(",".join(timeStyles))	
		xmlContent+='\t\t</timestyle>\n'
		
		# Text
		xmlContent+='\t\t<timetext>\n'
		xmlContent+='\t\t\t<default></default>\n'
		timeTexts=[]
		for t in range(T):
			timeTexts.append("%.1f/%.1f"%(data.personal[dsoName]['f'][l][t],data.personal[dsoName]['C'][l]))
		xmlContent+='\t\t\t<periods>%s</periods>\n'%(",".join(timeTexts))	
		xmlContent+='\t\t</timetext>\n'
		
		xmlContent+='\t</element>\n'
		
	# Buses
	for n in range(data.general['N']):
		xmlContent+='\t<element id="BUS%s" name="Bus %s">\n'%(n,n)
		
		# Data				
		periodsShed=['%s'%(i+1) for i,v in enumerate(data.general['z'][n]) if v]
		if len(periodsShed) > 0:
			xmlContent+='\t\t<data id="Shed">in period(s) %s</data>\n' % (', '.join(periodsShed))
			
		periodsFlexActivated=['%s'%(i+1) for i,v in enumerate(map(lambda x,y: abs(x)+abs(y),data.general['U+'][n],data.general['U-'][n])) if v > options.EPS]
		if len(periodsFlexActivated) > 0:
			xmlContent+='\t\t<data id="Flexibility used">in period(s) %s</data>\n' % (','.join(periodsFlexActivated))
		
		periodsOppositeFlex=['%s'%(i+1) for i,v in enumerate(map(lambda x,y: (x > options.EPS and abs(y) > options.EPS),data.general['U+'][n],data.general['U-'][n])) if v]
		if len(periodsOppositeFlex) > 0:
			xmlContent+='\t\t<data id="Opposite flex usage">in period(s) %s</data>\n' % (','.join(periodsOppositeFlex))
		
		# List of general bus attributes without time dependence
		for attr in ['g','G','b','B']:
			xmlContent+='\t\t<data id="%s">%s</data>\n' % (translate(attr),data.general[attr][n])
			
		# List of general bus attributes
		for attr in ['R+','R-']:
			xmlContent+='\t<timedata id="%s">%s</timedata>\n'%(translate(attr),floats2str(data.general[attr][n]))

		# Voltage graph
		periodsVoltageIssues=[]
		periodsUnderVoltage=[]
		periodsOverVoltage=[]
		if options.OPF_METHOD == "linearOpf":
			vMin=data.personal[dsoName]['Vmin'][n]*data.personal[dsoName]['Vb']
			vMax=data.personal[dsoName]['Vmax'][n]*data.personal[dsoName]['Vb']

			# Voltage issues
			periodsVoltageIssues=['%s'%(i+1) for i,v in enumerate(data.personal[dsoName]['v^b'][n]) if v<vMin+options.EPS or v>vMax+options.EPS]
			periodsUnderVoltage=['%s'%(i+1) for i,v in enumerate(data.personal[dsoName]['v'][n]) if v<vMin+options.EPS]
			periodsOverVoltage=['%s'%(i+1) for i,v in enumerate(data.personal[dsoName]['v'][n]) if v>vMax-options.EPS]

			# Voltage graph
			xmlContent+='\t<timegraph id="voltage" title="" ylabel="Voltage [kV]">\n'
			xmlContent+='\t\t<timegraphdata id="Min. voltage">%s</timegraphdata>\n'%(floats2str(([vMin])*T))
			xmlContent+='\t\t<timegraphdata id="Max. voltage">%s</timegraphdata>\n'%(floats2str(([vMax])*T))
			for attr in ['v^b','v^r','v','voltage violation']:
				xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.personal[dsoName][attr][n]))
			xmlContent+='\t</timegraph>\n'

			# Angle graphs
			xmlContent+='\t<timegraph id="voltageAngle" title="" ylabel="Voltage angle [deg]">\n'
			for attr in ['phi^b','phi^r','phi']:
				xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.personal[dsoName][attr][n]))
			xmlContent+='\t</timegraph>\n'

		# Baseline graph
		xmlContent+='\t<timegraph id="baseline" title="" ylabel="Power [MW]">\n'
		for attr in ['p^p','p^b','p^r','p','d','D']:
			try:
				xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.general[attr][n]))
			except KeyError:
				pass
		xmlContent+='\t</timegraph>\n'
		
		# Flexibility graph
		xmlContent+='\t<timegraph id="fs" title="" ylabel="Power [MW]">\n'
		for attr in ['S+','S-','A+','A-','U+','U-']:
			xmlContent+='\t\t<timegraphdata id="%s">%s</timegraphdata>\n'%(translate(attr),floats2str(data.general[attr][n]))
		xmlContent+='\t</timegraph>\n'
		
		# Global style
		xmlContent+='\t\t<timestyle>\n'
		xmlContent+='\t\t\t<default>'
		if len(periodsShed) > 0:
			xmlContent+='fill:#A20025'
		elif len(periodsOverVoltage) > 0:
			xmlContent+='fill:#FFED69'
		elif len(periodsUnderVoltage) > 0:
			xmlContent+='fill:#9D7BFC'
		elif len(periodsVoltageIssues) > 0:
			xmlContent+='fill:#656565'
		elif len(periodsOppositeFlex) > 0:
			xmlContent+='fill:#FA6800'
		elif len(periodsFlexActivated) > 0:
			xmlContent+='fill:#A4C400'
		else:
			xmlContent+='fill:#000000'

		if options.OPF_METHOD == "linearOpf":
			if len(periodsUnderVoltage) > 0 and len(periodsOverVoltage) > 0:
				xmlContent+=';stroke:#A20025'
			elif len(periodsUnderVoltage) > 0:
				xmlContent+=';stroke:#9D7BFC'
			elif len(periodsOverVoltage) > 0:
				xmlContent+=';stroke:#FFED69'
			else:
				xmlContent+=';stroke:#000000'
		else:
			xmlContent+=';stroke:#000000'
		xmlContent+='</default>\n'

		# Time styles
		timeStyles=[]
		for t in range(T):
			if data.general['z'][n][t]:
				timeStyles.append('fill:#A20025;stroke:#000000')
			elif "%s"%t in periodsOverVoltage:
				timeStyles.append('fill:#FFED69;stroke:#FFED69')
			elif "%s"%t in periodsUnderVoltage:
				timeStyles.append('fill:#9D7BFC;stroke:#9D7BFC')
			elif "%s"%t in periodsVoltageIssues:
				timeStyles.append('fill:#656565;stroke:#000000')
			elif data.general['U+'][n][t] and abs(data.general['U-'][n][t]) > options.EPS:
				timeStyles.append('fill:#FA6800;stroke:#000000')
			elif data.general['U+'][n][t]+abs(data.general['U-'][n][t]) > options.EPS:
				timeStyles.append('fill:#A4C400;stroke:#000000')
			else:
				timeStyles.append('fill:#000000;stroke:#000000')
		xmlContent+='\t\t\t<periods>%s</periods>\n'%(",".join(timeStyles))	
		xmlContent+='\t\t</timestyle>\n'
		
		xmlContent+='\t</element>\n'

	xmlContent+='</elements>\n'
	
	xmlContent+='</xml>'
	
	# Write the xmlContent
	if xmlPath.endswith('.zip'):
		xmlName=re.compile('([^(/|\\)]+)\.zip$').search(xmlPath).group(1)
		with zipfile.ZipFile(xmlPath,'w',zipfile.ZIP_DEFLATED) as zipFile:
			zipFile.writestr('%s.xml'%xmlName, xmlContent.encode('latin-1'))
	else:
		with open(xmlPath, 'w') as file:
			file.write(xmlContent)
			