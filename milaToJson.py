"""
Copyright (c) <2013> <Shane Marks>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


Author: Shane Marks  
Last Modified:  1st June 2013
Descripiton:  Script to convert a shading network to a json file and back again. Main usage is as  an automated way to rebuild shading networks when the  shaders  have been changed

usage:
mila2Json ()  -> Will  start at the selected node and  and graph down the network storing the connecteions and attributes of each
json2Mila ()  -> Loads the json file and rebuilds network    
"""

import maya.cmds as cmds
import sys
import json

#### pymel is used for general.setAttr as it seems more robust than the maya.cmds version
import pymel.core.general  as general


class node:

	##### variables
	##### attributes: store the attribute as a key name associated with a list containing: [value,valueType(string/int etc)]
	##### connections:  lis of connections going backward  (the attribute and what connects to it.
	##### name: name of the node
	##### type: node type (mila_scatter,bump node etc)
	##### classification: Helper string to determine where  the  node should be stored in the hypergraph

	###### functions:
	###### addValue(attribute name, value, type of attribute (string, float , long etc)):
	###### Add an attribute to the dictionary

	###### addConnection ("Attribute name on node", "Attribute it connects to"):
	###### add connection to dictionary

	def __init__(self,name):
		self.name=name
		self.type= cmds.nodeType(name)
		self.classification = cmds.getClassification(self.type)
		self.attributes=dict()  
		self.connections=dict()        

	def addValue(self, attr,value,type):
		self.attributes[attr]=[value,type]



	def addConnection(self,attr,connection):
		self.connections[attr]=connection




 
### gets connections returns (destination, source)
### used by mila2Json
def _getConnections(nodeName):
	c = cmds.listConnections(nodeName,p=True,d=False,c=True,s=True)
	try:
		return zip(c[0::2], c[1::2])
	except:
		return None


### function to extract the object name from an attribute stored as objectName.attribute
### used by mila2Json
def _objFromAttr(attr):
	return attr[0:attr.find(".")]


### recursive function to map down a network starting at the top node
### used by mila2Json
def _mapNetwork(node,objectList):
	if node not in objectList:
		objectList.append(node)
		connections = getConnections(node)
	if connections is not None:
		for i in connections:
			objectList = mapNetwork(_objFromAttr(i[1]),objectList)
	return objectList
	

### function to convert nodelist to json and write to file
### used my mila2Json

def writeJson(nodeList):
	dictionaries = []   
	for i in nodeList:
		dictionaries.append(i.__dict__)

	try:
		location =cmds.fileDialog2(cap="save mila",okc="save",ff="Json File (*.json)")
		print location
		f = open(location[0],"w")

		f.write(json.dumps(dictionaries))
		f.close()
	except:
		print "unable to save"    

### Generates  shading node from node class
### used by json2Mila
def _generateNode(i):
	if cmds.objExists(i["name"]):
		raise Exception ("Node already exists")
	print i["classification"]
	print i["name"]
	if i["classification"][0].find("material:shader") >-1:
		i["name"]=cmds.shadingNode(i["type"],name=i["name"],asShader=True)
	elif i["classification"][0].find("texture") >-1:
		i["name"]=cmds.shadingNode(i["type"],name=i["name"],asTexture=True)
	elif i["classification"][0].find("utility") >-1:
		i["name"]=cmds.shadingNode(i["type"],name=i["name"],asUtility=True)  



### Loads json data from  file
### used by json2Mila
def _loadJson():
	location =cmds.fileDialog2(cap="open mila",okc="open",ff="Json File (*.json)",fm=1)
	f = open(location[0]) 
	return json.load(f)


### function to set attribute  if it fails without a type, it tries with the type, if unknown it attempts to guess.
### This function needs to be rewritten
### used by json2Mila

def _setAttribute(attribute,v,t):
 	attrTypes = ["numeric","bool","long","short","byte","char","enum","float","double","doubleAngle","doubleLinear","compound","message","time","matrix","fltMatrix","reflectanceRGB","reflectance","spectrumRGB","spectrum","float2","float3","double2","double3","long2","long3","short2","short3","doubleArray","floatArray","Int32Array","vectorArray","nurveCurve","mesh","lattice","pointArray"]   
	try:
		general.setAttr(attribute,v)  
	except:
		print "complex attribute... trying with type"
	if v!=None and t!=None:
		try:
			general.setAttr(attribute,v,type=t)  
		except:
			print "could not set! :("                                                 
	else:
		print "type unknown, guessing:"
		for a in attrTypes:
			try:
				general.setAttr(attribute,v,type=a)                                  
				print "success!"
				break;
			except Exception, e:
				pass   

### function to generate the shading network from json   
def json2Mila():
	#creating  variables to  store converted json
	data =None
	try:
		data = _loadJson()
		for i in data:
			_generateNode(i)
		  
	except Exception, e:
		print "Problem Creating nodes: %s" % str(e)

						
	### set attributes on each node
	for i in data:
		for attr,value in i["attributes"].iteritems():
			attribute = "%s.%s"%(i["name"], attr)
			v = value[0]    ### stores value of attribute
			t = value[1]    ### stores type of  of attribute, None if unknown
			print "attr: %s, value: %s, type: %s" %(attribute,v,t)
			_setAttribute(attribute,v,t)

					  
	### build all connections.                                       
	for i in data:                  
		for destination, source  in i["connections"].iteritems() :
			print "destination: %s   source: %s "%(destination,source)
			try:
				cmds.connectAttr(source,destination,force=True)
			except:
				print "could not make connection! :("
			 




			 
### loop through list of nodes and populate connections and attributes
def mila2Json():
	objectList=[]
	nodeList=[]
	### generate list of nodes in network 
	selection = cmds.ls(sl=True)
	if selection ==[] or len (selection) >1:
		print "Please select one shader object"
		sys.exit(2)
		
	_mapNetwork (selection[0],objectList)
	### create node objects
	for i in objectList:
		nodeList.append(node(i))
		
	for n in nodeList:
		print "reading: %s"%n.name
		print "type: %s"%n.type

	### connections
		c=_getConnections(n.name)
		if c  is not None:
			for connection in c:
				print "adding connection: %s" % str(connection)
				try:
					n.addConnection(connection[0],connection[1])
				except:
					print("unable to add connection: %s " %connection)

	#### attributes
		print "getting attrs"
		attrs = cmds.listAttr(n.name,multi=True)
		for a in attrs:
			attribute = "%s.%s"%(n.name,a)
			isConnected=None
			try:
				isConnected =cmds.connectionInfo(attribute,ges=True)
			except:
				print "trouble checking conneciton of attr, skipping"
			if (isConnected == ""):
				print "getting attr %s" %attribute

				try:
					type = cmds.attributeQuery(a,node=n.name,at=True)
				except:
					type= None
					print "type: %s" %type    
					
				if type !="message":
					try:
						value= cmds.getAttr(attribute)
					except:
						pass
					n.addValue(a,value,type)
					print n.attributes[a]
				else:
					print "ignoring message"
			else:
				print "skipping, attribute connected  %s.%s" %(n.name,a)

	writeJson(nodeList)    