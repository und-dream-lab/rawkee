import sys
import maya.cmds as cmds
import maya.mel  as mel

from typing import Final

import maya.api.OpenMaya as aom

########################################################
####   Python implementation of C++ sax3dWriter     ####
########################################################

########################################################
# This module installed in mayapy using pip.         ### 
########################################################
from rawkee import RKSceneTraversal

import xmltodict
import json
import io
from x3d import *                                    ###
#from rawkee.RKPseudoNode import *                    ###
########################################################


# --define-- defValue "------"

X3DXENC: Final[str] = "x3d"
X3DVENC: Final[int] = "x3dv"
X3DJENC: Final[int] = "x3dj"

class RKIO():
    def __init__(self):
        print("RKIO")
        
        ############################
        # Required File IO variables
        ############################
        self.exFile      = None    #
        self.exEncoding  = X3DXENC #
        self.tabNumber   = 0       #
        self.hasMultiple = False   #
        ############################
        
        self.profileType = "Full"
        self.x3dVersion  = "4.0"
        
        
        self.comments      = []
        self.commentNames  = []
        self.additionalComps = []
        self.additionalCompsLevels = []
        self.ignoredNodes  = []
        self.haveBeenNodes = []
        self.generatedX3D  = []
        
        # Thought this was needed, but the 'processForGeometry' method already has access to the 
        # associated shader engine, regardless of whether the shaderEngine has already been processed
        # as an Appearance node. There is no need to store this information separately
        #self.shaderNames   = []
        #self.texTransLists = []

        
        self.fullPath = ""
        
        self.x3dDoc = None
        
        self.isVerbose = False
        
        self.debugging = True
        
        self.x3d_scene = None
        
        self.trv = RKSceneTraversal.RKSceneTraversal()


    # Function that writes to disk. TODO
    def x3d2disk(self, x3dDoc, fullPath, exEncoding):
        
        with open(fullPath, "w") as self.exFile:
            self.trv.startExport(x3dDoc, self.exFile, exEncoding)
        
        return 
        
        ####################################################
        
        self.fullPath   = fullPath
        self.exEncoding = exEncoding
        
        print(self.fullPath)
        print(self.exEncoding)
        
        with open(fullPath, "w") as self.exFile:
            if   self.exEncoding == "x3d":
                self.exFile.write(x3dDoc.XML())
                
            elif self.exEncoding == "x3dv":
                self.exFile.write(x3dDoc.VRML())
                
            elif self.exEncoding == "x3dj":
                self.exFile.write(x3dDoc.JSON())
                
            elif self.exEncoding == "json":
                self.exFile.write(json.dumps(xmltodict.parse(x3dDoc.XML()), indent=4))
                
            elif self.exEncoding == "html":
                htmlHeader  = '<html>\n\t<head>\n'
                htmlHeader += '\t\t<meta charset="utf-8">\n\t\t<script src="x3dom-1.8.3/x3dom-full.js"></script>\n'
                htmlHeader += '\t\t<link rel="stylesheet" href="x3dom-1.8.3/x3dom.css">\n\t</head>\n\t<body>\n'
                htmlHeader += '\t\t<div style="width: 600px; height: 600px;">\n'
                self.exFile.write(htmlHeader)
                self.exFile.write(x3dDoc.HTML5())
                htmlFooder = "\n\t</body>\n</html>"

        #    self.startDocument()

    def profileDecl(self):
        if  self.exEncoding == X3DVENC:
            self.exFile.write("PROFILE " + self.profileType + "\n")
            
        elif self.exEncoding == X3DJENC:
            self.writeTabs()
            self.exFile.write('"@profile": "' + self.profileType + '",\n')
            self.writeTabs()
            self.exFile.write('"@xmlns:xsd": "http://www.w3.org/2001/XMLSchema-instance",\n')
            self.writeTabs()
            self.exFile.write('"@xsd:noNamespaceSchemaLocation": "https://www.web3d.org/specifications/x3d-')
            self.exFile.write(self.x3dVersion + '.xsd",\n')
            
        else:
            self.exFile.write("profile='" + self.profileType + "' version='" + self.x3dVersion + "' ")
            self.exFile.write("xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-")
            self.exFile.write(self.x3dVersion + ".xsd'>\n")
        
    def writeComponents(self):
        if   self.exEncoding == X3DVENC:
            self.exFile.write('COMPONENT "' + self.additionalComps[i] + '":"' + self.additionalCompsLevels[i] + '"\n')
            
        elif self.exEncoding == X3DJENC:
            pass
        else:
            self.writeTabs()
            self.exFile.write("<component name='" + self.additionalComps[i] + "' level='"  + self.additionalCompsLevels[i] + "'/>\n")
        
    ########################################################################
    ########################################################################
    # Custom IO Functions not needed if x3d.py I/O Functions work properly #
    #    if   self.exEncoding == X3DVENC:
    #        pass
    #        
    #    elif self.exEncoding == X3DJENC:
    #        pass
    #        
    #    else:
    #        pass
    #
    ########################################################################
    ########################################################################
    def startDocument(self):                                               #
        self.tabNumber   = 0       #
        self.hasMultiple = False   #
        #self.profileType = "Full"
 
        if   self.exEncoding == X3DVENC:
            self.exFile.write("#X3D V" + self.x3dVersion + "utf8\n")
            self.exFiel.write("#X3D-to-ClassicVRML serialization by X3DPSAIL (x3d.py) and RawKee Python\n\n")
            self.profileDecl()
            self.writeComponents()
            
            for i in range(len(self.commentNames)):
                self.exFile.write("META \"" + self.commentNames[i] + "\" \"" + self.comments[i] + "\"\n")
                
            self.exFile.write("\n")
            
        elif self.exEncoding == X3DJENC:
            self.exFile.write("{\n")
            self.tabNumber += 1
            self.writeTabs()
            self.exFile.write("\"X3D\": {\n")
            self.tabNumber += 1
            self.writeTabs()
            self.exFile.write("\"@version\": \"" + self.x3dVersion + "\",\n")
            self.profileDecl()
            self.writeComponents()
            
            for i in range(len(self.commentNames)):
                #self.writeTabs()
                #self.exFile.write('"#comment:' + self.commentNames[i] + '": "' + self.comments[i] + '",\n')
                pass
            
            self.writeTabs()
            self.exFile.write('"Scene": {\n')
            self.tabNumber += 1
            
        else:
            self.exFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            self.exFile.write("<!DOCTYPE X3D PUBLIC \"ISO//Web3D//DTD X3D " + self.x3dVersion + "//EN\" \"https://www.web3d.org/specifications/x3d-" + self.x3dVersion +".dtd\">\n")
            self.exFile.write("<X3D ")
            self.profileDecl()
            
            self.tabNumber += 1
            self.writeTabs()
            self.exFile.write("<head>\n")
            
            self.tabNumber += 1
            self.writeComponents()
            
            for i in range(len(self.commentNames)):
                self.writeTabs()
                self.exFile.write("<meta name='" + self.commentNames[i] + "' content='" + self.comments[i] + "'/>\n")
            
            self.tabNumber -= 1
            self.writeTabs()
            self.exFile.write("</head>\n")
            
            self.writeTabs()
            self.exFile.write("<Scene>\n")
            self.tabNumber += 1
            

    def endDocument(self):
        if   self.exEncoding == X3DVENC:
            self.exFile.write("#End of X3DV file\n")
            
        elif self.exEncoding == X3DJENC:
            self.exFile.write("\t\t}\n\t}\n}\n")
            
        else:
            self.exFile.write("\t</Scene>\n</X3D>\n")
    
        
    def startNode(self, x3dType, x3dName, fields, fieldValues, hasMore):
        pass

    def endNode(self, x3dType, x3dName):
        pass

    def writeScriptFile(self, fileName, contents, filePath):
        pass
        
    def addScriptNonNodeField(self, accessType, fieldType, fieldName, fieldValue):
        pass
        
    def addScriptNodeField(self, accessType, fieldType, fieldName):
        pass
        
    def addScriptNodeFieldValue(self, value):
        pass
        
    def endScriptNodeField(self):
        pass

    def writeScriptSBracket(self):
        pass

    def writeScriptEBracket(self):
        pass

    def writeRawCode(self, rawCode):
        pass

    def writeRoute(self, fromNode, fromField, toNode, toField):
        pass
        
    def startField(self, x3dFName, x3dFValue):
        pass
        
    def fieldValue(self, x3dFValue):
        pass
        
    def endField(self):
        pass
    
    def ioUseDecl(x3dType, x3dName, cField, cValue):
        if   self.exEncoding == X3DVENC:
            if self.hasMultiple:
                self.writeTabs()
            self.hasMultiple = False
            self.exFile.write("USE " + x3dName + "\n")
        elif self.exEncoding == X3DJENC:
            self.writeTabs()
            self.exFile.write("\"" + x3dType + "\": {\n")
            self.tabNumber += 1
            self.writeTabs()
            self.exFile.write("\"@USE\": \"" + x3dName + "\"\n")
            self.tabNumber -= 1
            self.writeTabs()
            self.exFile.write("}\n")
        else:
            self.writeTabs()
            self.exFile.write("<" + x3dType)
            self.exFile.write(" USE='" + x3dName + "'")
            self.startField(cField, cValue)
            self.fieldValue(cValue)
            self.exFile.write("/>\n")
        
    def writeTabs(self):
        nTab = ""
        for i in range(self.tabNumber):
            nTab = nTab + "\t"
        self.exFile.write(nTab)
        
    def profileDecl(self):
        pass
        
    def writeComponents(self):
        pass

    def outputCData(self, rawdata):
        pass

    def writeSBracket(self):
        pass

    def writeEBracket(self):
        pass
                                                                 #
    def preWriteField(self, fieldName):                          #
        pass                                                     #
    ##############################################################





    ##############################################################
    # def resetSceneRoot(self, x3dDoc):                          #
    #                                                            #
    #                  Slated to be deleted                      #
    #            but I don't want to deal with errors            #
    #                      at the moment                         #
    #                                                            #
    #                                                            #
    ##############################################################
    def resetSceneRoot(self, x3dDoc):                            #
                                                                 #
        self.x3dDoc = x3dDoc                                     #
        self.x3dDoc.Scene.children.clear()                       #
                                                                 #
        return self.x3dDoc.Scene                                 #
    ##############################################################

    def sendToX3DOM(self):
        pass
        
    def sendToSunrize(self):
        pass

    ####################################################################
    # Function that adds a node name to ignore to the "ignoreNodes" List
    ####################################################################
    def setIgnored(self, nodeName):
        self.ignoredNodes.append(nodeName)

    def cMessage(self, msg):
        if self.isVerbose:
            print(msg)
        
    def findExisting(self, nodeDEF):
        rNode = None
        nLen = len(self.haveBeenNodes)
        
        for index in range(nLen):
            if self.haveBeenNodes[index] == nodeDEF:
                rNode = self.generatedX3D[index]
                return rNode
        return rNode        


    #######################################################
    # Function clears out the list of node names that have
    # either been used already or are to be ignored.
    def clearMemberLists(self):
        self.ignoredNodes.clear()
        self.haveBeenNodes.clear()
        self.generatedX3D.clear()

        # Thought this was needed, but the 'processForGeometry' method already has access to the 
        # associated shader engine, regardless of whether the shaderEngine has already been processed
        # as an Appearance node. There is no need to store this information separately
        #self.shaderNames.clear()
        #self.texTransLists.clear()

             
    '''
        This method checks the List that holds the names
        of nodes that are to be ignored. It returns
        a value of True if a match for a node name is found
        in this List
    '''
    def checkIfIgnored(self, nodeName):
        hasBeen = False
        hbLength = len(self.ignoredNodes)
        i = 0

        while i < hbLength and hasBeen == False:
            if nodeName == self.ignoredNodes[i]:
                hasBeen = True
            i = i + 1
            
        return hasBeen

    def setAsHasBeen(self, nodeName, x3dNode):
        self.haveBeenNodes.append(nodeName)
        self.generatedX3D.append(x3dNode)
        
    '''
        This method checks the List that holds the names
        of nodes that have already been exported. It returns
        a value of True if a match for a node name is found
        in this List
    '''
    def checkIfHasBeen(self, nodeName):
        
        for aName in self.haveBeenNodes:
            if nodeName == aName:
                return True
        '''        
        hbLength = len(self.haveBeenNodes)
        i = 0

        while i < hbLength and hasBeen == False:
            if nodeName == self.haveBeenNodes[i]:
                return True
            i = i + 1
        ''' 
        return False
    
    # Thought this was needed, but the 'processForGeometry' method already has access to the 
    # associated shader engine, regardless of whether the shaderEngine has already been processed
    # as an Appearance node. There is no need to store this information separately
    #def trackTextureTransforms(self, shaderName, texTransList):
    #    self.shaderNames.append(shaderName)
    #    self.texTransLists.append(texTransList)
        
    #def getTexTransList(self, shaderName):
    #    for idx in range(len(self.shaderNames)):
    #        if shaderName == self.shaderNames[idx]:
    #            return self.texTransLists[idx]
    #    return None
    
    def useDecl(self, x3dNode, nodeName, x3dParentNode, x3dFieldName):
        x3dNode.USE = nodeName
        
        nodeField = getattr(x3dParentNode, x3dFieldName)
        if isinstance(nodeField, list):
            nodeField.append(x3dNode)
        else:
            setattr(x3dParentNode, x3dFieldName, x3dNode)
#            nodeField = x3dNode
            
    def createNodeFromString(self, x3dType):
        return self.trv.createNodeFromString(x3dType)

