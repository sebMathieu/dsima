"""
Scripts that create an xml file with the global results
"""

## List of attributes to display in the global results.
attributes={"Welfare":{"unit":"&#8364;"},
			"Protections cost":{"unit":"&#8364;"},
			"DSOs costs":{"unit":"&#8364;"},
			"TSOs surplus":{"unit":"&#8364;"},
			"Producers surplus":{"unit":"&#8364;"},
			"Retailers surplus":{"unit":"&#8364;"},
			"Total energy shed":{"unit":"MWh"},
			"Max. imbalance":{"unit":"MW"},
		 	"Total production":{"unit":"MWh"},
		 	"Total consumption":{"unit":"MWh"},
			"Total imbalance":{"unit":"MWh"},
			"Total usage of flex.":{"unit":"MWh"},
			"Total opp. usage of flex.":{"unit":"MWh"}
			}
			
## List of data to get for each day.
dayData={"Welfare":{"unit":"&#8364;"},
		 "Time":{"unit":"s"},
		 "Iterations":{"unit":''},
		 "DSOs costs":{"unit":"&#8364;"},
		 "Protections cost":{"unit":"&#8364;"},
		 "TSOs surplus":{"unit":"&#8364;"},
		 "Producers surplus":{"unit":"&#8364;"},
		 "Retailers surplus":{"unit":"&#8364;"},
		 "Total energy shed":{"unit":"MWh"},
		 "Total production":{"unit":"MWh"},
		 "Total consumption":{"unit":"MWh"},
		 "Max. imbalance":{"unit":"MW"},
		 "Total imbalance":{"unit":"MWh"},
		 "Total usage of flex.":{"unit":"MWh"}
		}
			
import sys,os,zipfile,re
import xml.etree.ElementTree as ElementTree

## Add the results given by the xml file.
# @param results Dictionnary with the results of the previous days.
# @param dayResults Dictionnary with the individual results of the previous days.
# @param actorCosts Costs for each actors.
# @param xmlFile File like object containing the results.
# @param day Day index
def addResults(results, dayResults, actorCosts, xmlFile, day):
	tree=ElementTree.parse(xmlFile)
	root=tree.getroot()
	
	# Global data
	for a,resultsAttribute in results.items():
		field=root.find('./general/data[@id="%s"]'%a)
		
		v=float(field.text)
		resultsAttribute['mean']+=v
		resultsAttribute['min']=min(v,resultsAttribute['min'])
		resultsAttribute['max']=max(v,resultsAttribute['max'])
	
	# Day data
	for a,dailyData in dayResults.items():
		field=root.find('./general/data[@id="%s"]'%a)
		
		while len(dailyData)<=day:
			dailyData.append(None)
		dailyData[day]=field.text

	for actor in root.findall('./externals/element'):
		name=actor.attrib['name']
		actorResults=None
		try:
			actorResults=actorCosts[name]
		except KeyError:
			actorCosts[name]={'mean':0,'min':float("inf"),'max':float("-inf")}
			actorResults=actorCosts[name]
		
		# Get cost or operational cost if defined
		v=0
		if actor.find('./data[@id="Operation costs"]') != None: # TODO Clean that
			v=float(actor.find('./data[@id="Operation costs"]').text)
		else:
			v=float(actor.find('./data[@id="costs"]').text)
		
		actorResults['mean']+=v
		actorResults['min']=min(v,actorResults['min'])
		actorResults['max']=max(v,actorResults['max'])

## Create an xml file with the global results.
# @param path Target path.
# @param results Results dictionary.
# @param dayResults Dictionnary with the individual results of the previous days.
# @param actorCosts Costs for each actors.
def outputXML(path, results, dayResults, actorCosts):
	with open(path, 'w') as file:
		file.write('<?xml version="1.0" encoding="ISO-8859-1" ?>\n<xml>\n')
		
		file.write('<attributes>\n')
		for a,r in results.items():
			file.write('\t<attribute id="%s" unit="%s">\n'%(a,attributes[a]['unit']))
			for mode,value in r.items():
				file.write('\t\t<%s>%s</%s>\n'%(mode,value,mode))
			file.write('\t</attribute>\n')
		file.write('</attributes>\n')
		
		file.write('<dayresults>\n')
		for a,r in dayResults.items():
			file.write('\t<timedata id="%s" unit="%s">%s</timedata>\n'%(a,dayData[a]['unit'],','.join(r)))
		file.write('</dayresults>\n')
		
		file.write('<actors>\n')
		for a,r in actorCosts.items():
			file.write('\t<actor id="%s" unit="&#8364;">\n'%a)
			for mode,value in r.items():
				file.write('\t\t<%s>%s</%s>\n'%(mode,value,mode))
			file.write('\t</actor>\n')
		file.write('</actors>\n')
		
		file.write('</xml>\n')

## Get the global results for the simulated days.
# @param hash Hash of the instance.
# @param path Path to the instance simulation results.
def getGlobalResults(hash,path="instances"):
	total=0
	results={}
	actorCosts={}
	dayResults={}
	
	# Get the days
	xmlFilePath="%s/%s/%s.xml"%(path,hash,hash)
	tree=ElementTree.parse(xmlFilePath)
	root=tree.getroot()
	tag=root.find('days')
	dayStart=int(tag.find('start').text)
	days=list(range(dayStart, int(tag.find('end').text)))
	
	# Initialize the results structure
	for a in attributes.keys():
		results[a]={'mean':0,'min':float("inf"),'max':float("-inf")}
	for a in dayData.keys():
		dayResults[a]=[]
	
	# Get the results of the simulated days
	for day in days:
		fullPath="%s/%s/%s/result-%s-d%s.zip"%(path,hash,day,hash,day)
		if not os.path.exists(fullPath):
			raise Exception("%s does not exist !"%fullPath)
		
		# Extract the xml file
		zipFile=zipfile.ZipFile(fullPath,mode='r')
		xmlFile=zipFile.open('result-%s-d%s.xml'%(hash,day))
		
		addResults(results, dayResults, actorCosts, xmlFile,day-dayStart)
		total+=1
	
	# Compute the mean
	for a in attributes:
		results[a]['mean']/=total
	for actorResults in actorCosts.values():
		actorResults['mean']/=total
		
	# Create the xml result file
	outputXML('%s/%s/globalResults-%s.xml'%(path,hash,hash),results,dayResults,actorCosts)
		
# Starting point from python #   
if __name__ == "__main__":
	if len(sys.argv) < 2 :
		print('Usage : python globalResults hash [path]')
		sys.exit(2)

	import time
	tic=time.time()
	if len(sys.argv) == 2:
		getGlobalResults(sys.argv[1])
	else:
		getGlobalResults(sys.argv[1],sys.argv[2])
	print('%.2f s'%(time.time()-tic))
	