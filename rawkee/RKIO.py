import sys
import maya.cmds as cmds
import maya.mel  as mel

from typing import Final

import maya.api.OpenMaya as aom
from   maya.api.OpenMaya import MFn as rkfn

########################################################
####   Python implementation of C++ sax3dWriter     ####
########################################################

########################################################
# This module installed in mayapy using pip.         ### 
########################################################
#from rawkee import RKSceneTraversal
from rawkee import RKSceneTraversal as rkST
from rawkee import RKSceneLoaderJSON

import xmltodict
import json
import io
#from rawkee.rkx3d import *                          ###
#from rawkee.RKPseudoNode import *                   ###
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
        
        self.comments      = []
        self.commentNames  = []
        self.additionalComps = []
        self.additionalCompsLevels = []
        self.ignoredNodes  = []
        self.haveBeenNodes = {}
        self.generatedX3D  = {}
        
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
        
        self.trv = rkST.RKSceneTraversal()
        
        self.jsonLoader = RKSceneLoaderJSON.RKSceneLoaderJSON()


    # Function that writes to disk.
    def x3d2disk(self, x3dDoc, fullPath, exEncoding):
        
        with open(fullPath, "w") as self.exFile:
            self.trv.startExport(x3dDoc, self.exFile, exEncoding)


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
        rNode = self.generatedX3D.get(nodeDEF, None)
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
        
    def checkForRawKeeNoExportLayer(self, depNode):

        layIter = aom.MItDependencyGraph(depNode.object(), rkfn.kDisplayLayer, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)

        while not layIter.isDone():
            mObject = layIter.currentNode()
            layNode = aom.MFnDependencyNode(mObject)
            
            dtValue = cmds.getAttr(layNode.name() + ".displayType")
            #if layNode.name() == "RawKeeNoExport":
            if dtValue > 0:
                return True
            layIter.next()
            
        return False

    def setAsHasBeen(self, nodeName, x3dNode):
        self.haveBeenNodes[nodeName] = True
        self.generatedX3D[ nodeName] = x3dNode
        
    '''
        This method checks the List that holds the names
        of nodes that have already been exported. It returns
        a value of True if a match for a node name is found
        in this List
    '''
    
    def getGeneratedX3D(self, namedDEF):
        foundNode = self.generatedX3D.get(namedDEF, None)
        return foundNode
    
    def checkIfHasBeen(self, nodeName):
        hasBeenExported = self.haveBeenNodes.get(nodeName, False)
            
        return hasBeenExported
    
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
            
    def createNodeFromString(self, x3dType):
        #return self.trv.instantiateNodeFromString(x3dType)
        return rkST.instantiateNodeFromString(x3dType)
        
    def createRouteObject(self):
        return self.trv.getRouteObject()
        
    def createFieldObject(self):
        return self.trv.getFieldObject()

    
