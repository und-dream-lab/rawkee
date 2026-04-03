import sys
import random
import maya.cmds as cmds
import maya.mel  as mel
import maya.OpenMaya as om

import maya.api.OpenMaya as aom
import maya.api.OpenMayaAnim as aoma
from   maya.api.OpenMaya import MFn as rkfn

import ufe
import rawkee.maya.RKufe as rkufe

from rawkee.maya.RKInterfaces   import RKInterfaces
from rawkee.io.RKSceneTraversal import RKSceneTraversal

# Pushed Material Export into RKMaterials.py
import rawkee.maya.RKMaterials as rkMat

import numpy as np

import math as math

import json

import os

class RKOrganizer():
    def __init__(self):
        #print("RKOrganizer")
        
        #self.rkint     = RKInterfaces.RKInterfaces()
        self.rkint     = RKInterfaces()
        self.animation = []
        self.isVerbose = False
        #self.trv       = RKSceneTraversal.RKSceneTraversal()
        self.trv       = RKSceneTraversal()

        self.isTreeBuilding = False
        self.hasPassed = False
        self.isDone = False
        self.useRelURL = True
        self.useRelURLW = True
        self.x3dTreeStrings = ""
        self.x3dTreeDelStrings = ""
        self.updateMethod = 0
        self.fileOverwrite = False
        self.exRigidBody = False
        self.exHAnim = False
        self.exIODevice = False
        self.nonStandardHAnim = False
        self.exBCFlag = 1
        self.avatarMeshNames = []
        self.avatarDagPaths = []
        
        self.bPoseStore = []

        self.rkUseHAnimSites = 0
        self.rkSkinInfluence = 0

        self.rkBindPose = {}
        self.rkMotions  = {}
        self.rkSkelConf = {}
        
        self.allMeshMappings = {}
        


        self.optionsString = ""
        
        self.eofScene = None
        
        '''
        X3D Encodings: 0 - XML     - *.x3d
                       1 - Classic - *.x3dv
                       2 - VMRl97  - *.vrml
                       4 - binary  - *.x3db, *.x3de
                       5 - json    - *.x3dj, *.json
                       
        Import/Export file coding
        '''
        self.exEncoding = "x3d"
        
        # Tells RK-IO whether or not location-defined leaf nodes should be exported as syblings to their parents
        self.asSyblings = False
        
        # Tells RK-IO whether or not to export/import empty grouping nodes
        self.useEmpties = True
        
        # Tells RK-IO whether or not to export Metadata nodes
        self.exMetadata = True

        # Tells RK-IO whether or not to export textures
        self.exTextures = True
        
        # Tells RK-IO whether or not to export other media
        self.exAudio = True
        
        # Tells RK-IO whether or not to export Inlined files
        self.exInline = False

        # Tells RK-IO whether or not the external X3D viewer should be launched at the completion of the export.
        self.launchExt = False
        
        # Tells RK-IO the switch value for Texture Export.
        '''
        0 is current
        1 is gif
        2 is jpg
        3 is png
        
        Not to be confused with "exTextureFormat", which actually holds the string that is the file extension.
        '''
        self.x3dTextureForInt = 0


        # Tells RK-IO whether or not to consolidate external media into sub folders of the directory in which the X3D file is written.
        self.conMedia = True

        # Tells RI-IO whether or not to adjust the texture size of the textures we are using. If TRUE, the textures will be 
        # exported to the folder designated by the localImagePath variable.
        self.adjTexture = True
        
        # Tells RI-IO whether or not to save internal Maya  Textures as external files. If TRUE, the texture files will be 
        # exported to the folder designated by the localImagePath variable.
        self.saveMayaTex = True
        
        # Temporary path for writing out texture files
        self.tempTexturePath = ""

        # Tells RK-IO whether or not ColorPerVertex data should be exported for those mesh nodes that have no geometry node defining 
        # this parameter in these mesh's underworld.
        self.cpvNonD = False
        
        # Tells RK-IO whether or not NormalPerVertex data should be exported for those mesh nodes that have no geometry node 
        # defining this parameter in these meshes' underworld.
        self.npvNonD = False

        # Tells RK-IO whether or not the geometry of those mesh nodes that have no geometry node defining "solid" this parameter 
        # in these meshes' underworld is solid or not.
        self.solidGlobalValue = True
        
        # Export external texturs as pixel texture
        self.internalPixel = False
        
        # Export internal maya textures as pixel texture
        self.externalPixel = False

        # Tells RK-IO the size of what exported textures should be if they are created by Maya
        self.x3dTextureWidth  = 256
        self.x3dTextureHeight = 256

        # Tells RK-IO the creaseAngle of mesh nodes that do not have this parameter designated by an underworld geometry node.
        self.caGlobalValue = 0.0


        # Holds the path to where the X3D File will be written
        self.localPath = "./"

        # Holds the file name to where the X3D file will be written
        self.fileName = "";

        # Holds the path starting below the localPath where image/movie files are stored
        self.localImagePath = "/image"

        # Holds the path starting below the localPath where audio files are stored
        self.localAudioPath = "/audio"
        
        # Holds the path starting below the localPath where inline files are stored
        self.localInlinePath = "/inline"

        # Holds the base url used in all URL fields
        self.exBaseURL = "./"
        
        # Holds the url used in URL fields of all textures
        self.exTextureURL = "/image"

        # Holds the url used in URL fields of AudioClip nodes
        self.exAudioURL = "/audio"
        
        # Holds the url used in URL fields of Inline nodes
        self.exInlineURL = "/inline"

        # Holds specified Texture Directory found in OptionVars
        self.getTextureDir = ""
        
        # Holds specified Audio Directory found in OptionVars
        self.getAudioDir = ""
        
        # Holds specified Inline Directory found in OptionVars
        self.getInlineDir = ""
        
        # Current Tab count for offsettng text in file so that it's more easily read
        self.treeTabs = 0
        
        #Set the max number of tabs as some text editors can't handle a lot of tabs.
        self.ttabsMax = 0
        
        # --- not sure ---
        self.mayaArray = []
        
        # --- not sure ---
        self.x3dArray = []

        '''
        -----------------------------------------
        Variables for checking that the mesh node has underworld nodes attached to it. For
        instance, if an x3dColor node was a child of a mesh node, then hasColor would be true.
        -----------------------------------------
        '''
        self.hasColor    = False
        self.hasCoord    = False
        self.hasNormal   = False
        self.hasTexCoord = False
        self.hasGeometry = False
        self.hasTexture  = False
        
        self.hasMaterialX = False
        
        # Arrays of Array Strings used to store the names of nodes which have already been exported
        self.textureNames = []

        # Object used to get the Root of the DAG for export.
        self.worldRoot = None
        
        ################################
        self.imageMoveDir  = ""
        self.audioMoveDir  = ""
        self.inlineMoveDir = ""


    def __del__(self):
        del self.trv
        del self.rkint
        
        
    def loadRawKeeOptions(self):
        ## NEW ###################################################################################
        self.rkCastlePrjDir  = cmds.optionVar( q='rkCastlePrjDir' )
        self.rkSunrizePrjDir = cmds.optionVar( q='rkSunrizePrjDir')
        self.rkPrjDir        = cmds.optionVar( q='rkPrjDir'       )

        self.rkImagePath     = cmds.optionVar( q='rkImagePath'    )
        self.rkAudioPath     = cmds.optionVar( q='rkAudioPath'    )
        self.rkMatXPath      = cmds.optionVar( q='rkAudioPath'    )

        self.rkUseHAnimSites = cmds.optionVar( q='rkUseHAnimSites')
        self.rkSkinInfluence = cmds.optionVar( q='rkSkinInfluence')

        self.rkAdjTexSize    = cmds.optionVar(q='rkAdjTexSize'   )
        self.rkDefTexWidth   = cmds.optionVar(q='rkTextureWidth' )
        self.rkDefTexHeight  = cmds.optionVar(q='rkTextureHeight')

        self.rkExportMtlxInfo = cmds.optionVar(q='rkExportMtlxInfo')
        self.rkMtlx2Uri       = cmds.optionVar(q='rkMtlx2Uri'      )
        self.rkConsolidate    = cmds.optionVar(q='rkConsolidate'   )
        self.rkProcTexType    = cmds.optionVar(q='rkProcTexType'   )
        self.rkFileTexType    = cmds.optionVar(q='rkFileTexType'   )
        self.rkMovieTexType   = cmds.optionVar(q='rkMovieTexType'  )
        self.rkAudioClipType  = cmds.optionVar(q='rkAudioClipType' )
        self.rkProcTexFormat  = cmds.optionVar(q='rkProcTexFormat' )
        self.rkFileTexFormat  = cmds.optionVar(q='rkFileTexFormat' )

        self.rkNormalOpts  = cmds.optionVar(q='rkNormalOpts' )
        self.rkCreaseAngle = cmds.optionVar(q='rkCreaseAngle')
        self.rkColorOpts   = cmds.optionVar(q='rkColorOpts'  )

        self.rkExportMode  = cmds.optionVar( q='rkExportMode')
        self.rkMatXPath    = cmds.optionVar( q='rkMatXPath'  )
        self.activePrjDir = self.rkPrjDir
        
        if self.rkExportMode == 1:
            self.activePrjDir = self.rkCastlePrjDir
        elif self.rkExportMode == 2:
            self.activePrjDir = self.rkSunrizePrjDir


    #######################################################################################
    ### maya2x3d(self - RKOrganizer, x3d.Scene, MFnDagPath lsit [], MFnDagNode list [], string - pVersion <rawkee version>) ###
    #######################################################################################
    # Traverses the Maya DAG and converts the Maya nodes it    #
    # finds into X3D nodes and places them in a location in    #
    # the X3D Scenegraph that roughly corresponds to there     #
    # locations in the Maya DAG/DepGraph. Returns nothing.     #
    ############################################################
    def maya2x3d(self, x3dScene, eofScene, parentDagPaths, dagNodes, pVersion, fullPath, exEncoding):
        self.exEncoding = exEncoding
        
        self.loadRawKeeOptions()

        self.checkSubDirs(fullPath)
        
        self.relMatXDocPaths, self.actMatXDocPaths = rkMat.saveMaterialXDocuments(self.activePrjDir, self.rkMatXPath, self.rkImagePath)

        self.animation.clear()
        
        # Should aways be a new root.
        # Telling the IO object that this node has been 
        # visited bofore.
        self.rootName = "|!!!!!_!!!!!|world"
        self.trv.setAsHasBeen(self.rootName, x3dScene)
        
        ##########################################################
        # Needed for writing animation data at the end of the file
        ##########################################################
        self.eofScene = eofScene
        
        ##########################################################
        # Generate Background Nodes
        self.generateBackgroundNodes(x3dScene)

        #Traverse Maya Scene Downward without using an MFIt object
        dNum = len(dagNodes)
        for i in range(dNum):
            parentDagPaths[i] = self.rootName
            self.traverseDownward(parentDagPaths[i], dagNodes[i])
            
        self.collectInterpolatorData()
        
        ##########################################################
        # Needed for writing animation data at the end of the file
        # 
        # End of Export
        ##########################################################
        cLen = len(eofScene.children)
            
        for i in range(cLen):
            x3dScene.children.append(eofScene.children.pop(0))
                
        self.eofScene = None
            
        # Reset Animations as best as possible.
        
        #cmds.currentTime(0)
        for bPose in self.bPoseStore:
            cmds.dagPose( bPose, restore=True )
        # RawKee Export Bind Pose - Don't know why there would be more than one.
        self.bPoseStore.clear()
        
        # Dictionary containing the Matrix Animation offsets for HAnim Joints.
        self.rkBindPose.clear()
        
        # Dictionary containing any HAnimMotion Settings.
        self.rkMotions.clear()
        
        # Dictionary holding HAnim Skeleton Configurations while organizing the export
        self.rkSkelConf.clear()
        
        # texture/textureTransform/textureCoordinate mappings
        self.allMeshMappings.clear()
        
        # General X3D File Settings
        self.trv.x3dVersion = "4.1"
        self.trv.metatags.append({"name":"generator", "content":"RawKee X3D Exporter for Maya 2025+ [Python Edition], https://github.com/und-dream-lab/rawkee/"})
        
        if self.hasMaterialX == True:
            for doc in self.relMatXDocPaths:
                self.trv.metatags.append(doc)

        self.hasMaterialX = False
        self.relMatXDocPaths.clear()
        self.actMatXDocPaths.clear()
   
        # Set Profile and Components
        compLen = len(self.trv.profDict)
        if   compLen >= 36:
            self.trv.evaluateForFull()
        elif compLen >= 20:
            self.trv.evaluateForImmersive()
        elif compLen >= 16:
            self.trv.evaluateForInteractive()
        elif compLen >= 14:
            self.trv.evaluateForMP4Interactive()
        elif compLen >= 12:
            self.trv.evaluateForInterchange()
        elif compLen >= 10:
            self.trv.evaluateForCADInterchange()
        else:
            self.trv.evaluateForCore()
        
        self.trv.setAdditionalComponents()
        
        
    ############################################################
    ###  getAllTopDagNodes(self - RKOrganizer)               ###
    ############################################################
    # Selects the top level Maya Transform nodes that are      #
    # immediate children of the Maya DAG 'world' root and      #
    # returns them as a Python list. If a non-Transform node   #
    # is parented to the Maya 'world' root (such as a 'joint'  #
    # node), that node is not selected to be returned.         #
    ############################################################
    def getAllTopDagNodes(self):
        topDagNodes    = []
        parentDagPaths = [] # All will be the same because they are all the Maya world root.
                            # Keeping it consistant with traversal by selection
        #Grab the Maya World Root
        itDag = aom.MItDag(aom.MItDag.kBreadthFirst, aom.MFn.kTransform)
        worldDag = aom.MFnDagNode(itDag.root())
        
        dragPath = worldDag.getPath().fullPathName()

        ################################################################
        # Create a list of traversable dagnodes and the dagpath of their 
        # parent node - aka: dragPath - so named because the methods
        # are draging along the dagpath of their parent in order to 
        # properly check for node instances.
        cNum = worldDag.childCount()
        for i in range(cNum):
            tdNode = aom.MFnDagNode(worldDag.child(i))
            if tdNode.typeName != "objectSet":
                #parentDagPaths.append(dragPath)
                parentDagPaths.append("")
                topDagNodes.append(tdNode)

        return parentDagPaths, topDagNodes
        
    ########
    # TODO # - Think about how this is done. This function doesn't return what is needed.
    ########
    def getSelectedDagNodes(self):
        selectedDagNodes = []
        parentDagPaths   = []

        # Grab the selected Transforms
        activeList = aom.MGlobal.getActiveSelectionList(True)
        iterGP = aom.MItSelectionList( activeList, aom.MFn.kTransform )
        
        while not iterGP.isDone():
            dagPath   = iterGP.getDagPath()
            tdNode = aom.MFnDagNode(dagPath)
            if tdNode.typeName != "objectSet":
                selectedDagNodes.append(tdNode)
                parentDagPaths.append("|!!!!!_!!!!!|world")
            iterGP.next()
            
        return parentDagPaths, selectedDagNodes
    
    ##############################################################################################
    #   Export Initiators
    ##############################################################################################
    def exportAll(self, x3dDoc):
        #Grab the Maya World Root
        itDag = aom.MItDag(aom.MItDag.kDepthFirst, aom.MFn.kTransform)
        worldDag = aom.MFnDagNode(itDag.root())
        
        #Create the X3D Scene Root
        x3dScene = x3dDoc.Scene
        x3dScene.children.clear()
        
        self.rootName = "|!!!!!_!!!!!|world"
        self.trv.setAsHasBeen(self.rootName, x3dScene)
        
        dragPath = worldDag.getPath().fullPathName()

        #Traverse Maya Scene Downward without using an MFIt object
        cNum = worldDag.childCount()
        for i in range(cNum):
            self.traverseDownward(dragPath, aom.MFnDagNode(worldDag.child(i)))
        
        #If the RigidBody Physics option is selected, attempt to export Rigid Body physics nodes.
        if self.exRigidBody == True:
            self.processDynamics()
        
        # Export out X3D Script Nodes if they exist
        self.processScripts()
        
        self.isDone = True
    
        
    def exportSelected(self, x3dDoc):
        
        # Grab the selected Transforms
        activeList = aom.MGlobal.getActiveSelectionList()
        iterGP = aom.MItSelectionList( activeList, aom.MFn.kDagNode )
        itDag  = aom.MItDag(aom.MItDag.kDepthFirst, aom.MFn.kTransform)
        
        dagList  = []
        dragList = []
        
        while iterGP.isDone() != False:
            dagPath = iterGP.getDagPath()
            if dagPath != None:
                itDag.reset(dagPath, aom.MItDag.kDepthFirst, aom.MFn.kTransform)
                topNode = aom.MFnDagNode(itDag.root())
                dagList.append(topNode)
                dragList.append(topNode.getPath().fullPathName())
            iterGP.next()
            
        #Create the X3D Scene Root
        x3dScene = x3dDoc.Scene
        x3dScene.children.clear()

        self.rootName = "|!!!!!_!!!!!|world"
        self.trv.setAsHasBeen(self.rootName, x3dScene)

        cNum = len(dagList)
        for i in range(cNum):
            self.traverseDownward(dragList[i], dagList[i])

#############################   Break   ####################################
############################################################################
    
    ########################################################################
    # Function that generates background nodes based on imagePlaneShape
    # nodes in scene.
    def generateBackgroundNodes(self, x3dScene):
        ipIter = aom.MItDependencyNodes(rkfn.kImagePlane)

        while not ipIter.isDone():
            ipNode = aom.MFnDependencyNode(ipIter.thisNode())
            typeVal = cmds.getAttr(ipNode.name() + ".type")
            if typeVal == 1:
                cons = cmds.listConnections(ipNode.name() + ".sourceTexture")
                if len(cons) > 0:
                    if cmds.nodeType(cons[0]) == "envCube":
                        bkNode = self.trv.processBasicNodeAddition(x3dScene, "children", "Background", ipNode.name())
                        if bkNode[0] == False:
                            textureNodes = []
                            textureNodes = cmds.listConnections(cons[0], destination=True, type="file")
                            tDict = {}
                            tnl = len(textureNodes)
                            if tnl == 6:
                                for i in range(tnl):
                                    relativeTexPath = self.rkImagePath
                                    localTexWrite   = self.activePrjDir + "/" + relativeTexPath
                                    
                                    filePath = cmds.getAttr(textureNodes[i] + ".fileTextureName")
                                    fileName = self.rkint.getFileName(filePath)
                                    fileExt  = os.path.splitext(fileName)[1]
                                    fileName = os.path.splitext(fileName)[0]
                                    
                                    if   self.rkFileTexFormat == 1:
                                        fileName = fileName + ".png"
                                        relativeTexPath = relativeTexPath + fileName
                                        localTexWrite   = localTexWrite   + fileName
                                        
                                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'png')
                                        
                                    elif self.rkFileTexFormat == 2:
                                        fileName = fileName + ".jpg"
                                        relativeTexPath = relativeTexPath + fileName
                                        localTexWrite   = localTexWrite   + fileName
                                        
                                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'jpg')
                                        
                                    else:
                                        fileName = fileName + fileExt
                                        relativeTexPath = relativeTexPath + fileName

                                        if self.rkConsolidate == True:
                                            localTexWrite   = localTexWrite   + fileName
                                            movePath = self.imageMoveDir + "/" + fileName
                                            self.rkint.copyFile(filePath, movePath)
                                        else:
                                            localTexWrite = filePath

                                    # If the with DataURI option is selected, convert contents of 
                                    # file to a DataURI string.
                                    tList = []
                                    if self.rkFileTexType == 1:
                                        x3dURIData = self.rkint.media2uri(localTexWrite)
                                        tList.append(x3dURIData)
                                    else:
                                        tList.append(fileName)
                                        tList.append(relativeTexPath)
                                    tDict[str(i)] = tList
                            
                                bkNode[1].rightUrl  = tDict["0"]
                                bkNode[1].leftUrl   = tDict["1"]
                                bkNode[1].topUrl    = tDict["2"]
                                bkNode[1].bottomUrl = tDict["3"]
                                bkNode[1].frontUrl  = tDict["4"]
                                bkNode[1].backUrl   = tDict["5"]
                                    
            ipIter.next()
    
    
    ########################################################################
    # Function that collects Interpolator Data at the end of the maya2x3d()
    # function execution.
    ########################################################################
    def collectInterpolatorData(self):
        for animPackage in self.animation:
            apNode  = animPackage[0]
            apKeys = []
            fSteps = []
            
            #Maya Timeline Key Frame Step (Timeline steps)
            kfs  = cmds.getAttr(apNode.name() + ".keyFrameStep")
            
            #Maya Timeline Start Frame
            tsaf = cmds.getAttr(apNode.name() + ".timelineStartFrame")
            
            #Maya Timeline Stop Frame
            tsof = cmds.getAttr(apNode.name() + ".timelineStopFrame")
            
            #Number of frames per second
            fps  = cmds.getAttr(apNode.name() + ".framesPerSecond")
            
            #Number of Maya frames covered by this sensor.
            frameDistance = tsof - tsaf
            
            #rkAPType 
            rkAPType = cmds.getAttr(apNode.name() + ".mimickedType")
            
            # Calculate what the fractional values will be for the keys
            # of the itnerpolators assigned to this timing sensor (aka AnimPack node).
            fraction = 0.0
            cFrame   = tsaf
            kSteps      = 1
            kSteps     += (frameDistance // kfs)
            if (frameDistance % kfs) > 0:
                kSteps += 1
                
            for i in range(kSteps):
                apKeys.append(fraction)
                fSteps.append(cFrame)
                cFrame += kfs
                if cFrame > tsof:
                    cFrame = tsof
                fraction = (cFrame - tsaf) / frameDistance

            if rkAPType == 2:
                moNode  = animPackage[1]
                mop     = animPackage[2]

                moNode.channels = ""
                for j in range(len(mop.joints)):
                    mList = aom.MSelectionList()
                    mList.add(mop.joints[j].USE)
                    trsKey = apNode.name() + "." + mop.joints[j].USE + ".translate"
                    rotKey = apNode.name() + "." + mop.joints[j].USE + ".rotate"
                    jPath = mList.getDagPath(0)
                    
                    fValues = 0
                    trs = self.rkMotions.get(trsKey, False)
                    rot = self.rkMotions.get(rotKey, False)
                    
                    if trs == True:
                        fValues += 3
                        
                    if rot == True:
                        fValues += 3
                    
                    if fValues > 0:
                        moNode.channels += str(fValues)
                        if trs == True:
                            moNode.channels = moNode.channels + " " + "Xposition Yposition Zposition"
                        if rot == True:
                            moNode.channels = moNode.channels + " " + "Zrotation Yrotation Xrotation"
                        moNode.channels += " "
                        moNode.channelsEnabled.append(True)
                        defNode = self.trv.findExisting(mop.joints[j].USE)
                        if defNode is not None:
                            moNode.joints = moNode.joints + defNode.name + " "
                        
                moNode.channels = moNode.channels.strip()
                moNode.joints   = moNode.joints.strip()
                
                for step in fSteps:
                    cmds.currentTime(step)
                
                    for j in range(len(mop.joints)):
                        mList = aom.MSelectionList()
                        mList.add(mop.joints[j].USE)
                        jPath = mList.getDagPath(0)
                        trsKey = apNode.name() + "." + mop.joints[j].USE + ".translate"
                        rotKey = apNode.name() + "." + mop.joints[j].USE + ".rotate"

                        # Current Local Matrix
                        clm   = jPath.inclusiveMatrix() * jPath.exclusiveMatrix().inverse()
                        
                        # Bound Local Matrix
                        blm   = self.rkBindPose[mop.joints[j].USE]
                        
                        # Animation Data
                        deltaMatrix = clm * blm.inverse()
                        
                        #Transformation Matrix
                        transMatrix  = aom.MTransformationMatrix(deltaMatrix)

                        if self.rkMotions.get(trsKey, False) == True:
                            tv  = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))
                            moNode.values.append((tv[0], tv[1], tv[2]))
                        
                        if self.rkMotions.get(rotKey, False) == True:
                            rv  = transMatrix.rotation(aom.MSpace.kTransform).asEulerRotation()#.reorder(aom.MEulerRotation.kZYX)
                            moNode.values.append( (math.degrees(rv.z),math.degrees(rv.y),math.degrees(rv.x)) )
                            
            else:
                # Else AudioClip, MovieTexture, TimeSensor
                # Here we set the keys for the interpolators based on the AnimPack node's settings.
                intList = animPackage[2:]
                for l in intList:
                    l[1].key = apKeys
                    
                # Here we scrub through the Maya timeline frames to collect the keyValue data for
                # each key in each Interpolator.
                for step in fSteps:
                    cmds.currentTime(step)

                    # [tExp, bni[1], cParts[0], cParts[1], mod, mlist.getPlug(1)]
                    for l in intList:
                        expNode  = l[0] # Currently Not Needed
                        x3dNode  = l[1]
                        mayaName = l[2] # Currently Not Needed
                        mayaAttr = l[3]
                        modifier = l[4]
                        readPlug = l[5]
                        
                        animNode = aom.MFnDagNode(readPlug.node())
                        animList = aom.MSelectionList()
                        animList.add(animNode.name())
                        
                        isJNode = False
                        if animNode.typeName == "joint":
                            isJNode = True
                        deltaMatrix = aom.MMatrix()
                        path = animList.getDagPath(0)
                        
                        if isJNode == True:
                            
                            # Determin if this is an HAnimJoint node or a Skin Transform Node
                            isHAnim = False
                            cPath = path
                            while cPath.length() > 0:
                                pObj = cPath.parent(0)
            
                                if pObj.isNull():
                                    break

                                # Use an MFnDagNode to check the type of the parent
                                pDag = aom.MFnDagNode(pObj)
            
                                # Check if the parent is a transform node
                                if pDag.typeName != "joint":
                                    try:
                                        x3dType = cmds.getAttr(pDag.name() + ".x3dGroupType")
                                        if x3dType == "HAnimHumanoid":
                                            isHAnim = True
                                            break
                                    except:
                                        break
                                else:
                                    cPath = pDag.getPath()                                
                            
                            if isHAnim == True:
                                boundMatrix    = self.rkBindPose[animNode.name()]
                                currentLocalMatrix  = self.getJointLocalMatrix(animList.getDagPath(0))
                                deltaMatrix = currentLocalMatrix * boundMatrix.inverse()
                            else:
                                cjMat = path.inclusiveMatrix()
                                cpMat = path.exclusiveMatrix()
                                deltaMatrix = cjMat * cpMat.inverse()
                            
                        #################################
                        # Joints and Transforms
                        #################################999999
                        if   mayaAttr == "translate":
                            if isJNode == True:
                                transMatrix  = aom.MTransformationMatrix(deltaMatrix)
                                dTranslate   = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))
                                x3dNode.keyValue.append(dTranslate)
                            else:
                                x3dNode.keyValue.append((readPlug.child(0).asFloat(), readPlug.child(1).asFloat(), readPlug.child(2).asFloat()))
                            
                        elif mayaAttr == "rotate":
                            if isJNode == True:
                                transMatrix  = aom.MTransformationMatrix(deltaMatrix)
                                oriValue     = self.rkint.getSFRotation(transMatrix.rotation(aom.MSpace.kTransform).asAxisAngle())
                                x3dNode.keyValue.append(oriValue)
                            else:
                                tForm = aom.MFnTransform(readPlug.node())
                                oriValue = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())
                                x3dNode.keyValue.append(oriValue)
                                
                        elif mayaAttr == "scale":
                            if isJNode == True:
                                transMatrix  = aom.MTransformationMatrix(deltaMatrix)
                                chVals       = transMatrix.scale(aom.MSpace.kTransform)
                                
                                if animNode.typeName == "joint":
                                    chVals[0] = abs(chVals[0])
                                    chVals[1] = abs(chVals[1])
                                    chVals[2] = abs(chVals[2])

                                try:
                                    x3dNode.keyValue.append((chVals[0], chVals[1], chVals[2]))
                                except:
                                    print("Scale failed in Process Basic Transform")                                
                            else:
                                x3dNode.keyValue.append( readPlug.child(0).asFloat(), readPlug.child(1).asFloat(), readPlug.child(2).asFloat() )
                        
                        ############################################
                        # Maya placeTexture2d / X3D TextureTransform
                        ############################################
                        elif mayaAttr == "translateFrame":
                            x3dNode.keyValue.append((readPlug.child(0).asFloat(), readPlug.child(1).asFloat()))
                            
                        elif mayaAttr == "rotateFrame":
                            x3dNode.keyValue.append(readPlug.asMAngle().asRadians())
                            
                        elif mayaAttr == "coverage":
                            x3dNode.keyValue.append((readPlug.child(0).asFloat(), readPlug.child(1).asFloat()))
                            
                        ############################################
                        # Mesh / Shape - Coordinate/Normal/Tanget
                        # Geometry Cashing
                        ############################################
                        elif mayaAttr == "outMesh" and modifier == "coord":
                            #TODO
                            pass
                            
                        elif mayaAttr == "outMesh" and modifier == "normal":
                            #TODO
                            pass
                            
                        # There current isn't an Interpolator that can
                        # animate MFVec4f fields.
                        elif mayaAttr == "outMesh" and modifier == "tangent":
                            #TODO
                            pass
                        
        self.animation.clear()


    def getWorldPoseMatrixForJoint(self, jNode, poseName="rkEPose"):
        cPlugs = cmds.listConnections(poseName + '.members', plugs=True, c=True, s=False, d=True)

        # Joint Index in the pose
        jIdx = -1
        for i in range(0, len(cPlugs), 2):
            sPlug = cPlugs[i]
            dPlug = cPlugs[i+1] # Get the destination plug

            cNode = dPlug.split('.')[0]

            if cNode == jNode.name():
                idxStr = sPlug.split('[')[-1].replace(']', '')
                jIdx = int(idxStr)
                break

        mList = [1.0, 0.0, 0.0, 0.0,
			0.0, 1.0, 0.0, 0.0,
			0.0, 0.0, 1.0, 0.0,
			0.0, 0.0, 0.0, 1.0]
        
        if jIdx >= 0:
            mList = cmds.getAttr(poseName + '.matrix[' + str(jIdx) + ']')

        return aom.MMatrix(mList)

    
    def processX3DAnchor(self, dragPath, dagNode, x3dPF):
        pass
        
    def processX3DBillboard(self, dagNode, x3dPF):
        pass
        
    def processX3DCollision(self, dagNode, x3dPF):
        pass
        
    def processX3DGroup(self, dagNode, x3dPF):
        pass
        
    def processX3DSwitch(self, dagNode, x3dPF):
        pass
        
    def processX3DViewportGroup(self, dagNode, x3dPF):
        pass
    
    def processMayaLOD(self, x3dParentDEF, dagNode, cField="children"):
        pass
        
    #########################################################################################################
    #   Sound Related Functions
    def processX3DSound(self, dagNode, x3dPF):
        if dagNode.childCount() > 0:
            depNode = aom.MFnDependencyNode(dagNode.child(0))
            bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Sound", dagNode.name())
            if bna[0] == False:
                x3dNode = bna[1]

                # X3D Direction
                mlist = aom.MSelectionList()
                mlist.add(dagNode.name())
                tForm = aom.MFnTransform(mlist.getDependNode(0))
                x3dNode.direction = self.rkint.getDirection(tForm.rotation(aom.MSpace.kTransform, False), (0.0, 0.0, 1.0))
                
                # X3D Location
                x3dNode.location = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))

    
    #########################################################################################################
    #   Viewpoint Realted Functions
    def processX3DViewpoint(self, dagNode, x3dPF):
        if dagNode.childCount() > 0:
            depNode = aom.MFnDependencyNode(dagNode.child(0))
            isOrtho = depNode.findPlug("orthographic", False).asBool()
            if isOrtho:
                bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "OrthoViewpoint", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicViewpointFields(x3dNode, dagNode.name(), depNode)
                    
                    # X3D fieldOfView
                    oWidth = depNode.findPlug("orthographicWidth", False).asFloat() / 2
                    x3dNode.fieldOfView =  (oWidth * -1, oWidth * -1, oWidth, oWidth)
                     
            else:
                bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Viewpoint", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicViewpointFields(x3dNode, dagNode.name(), depNode)
                    
                    # X3D fieldOfView
                    hoz = depNode.findPlug("horizontalFilmAperture", False).asFloat()
                    focal = depNode.findPlug("focalLength", False).asFloat()
                    fov = (0.5 * hoz) / (focal * 0.03937)
                    fov = 2.0 * np.arctan(fov)
                    fov = 57.29578 * fov
                    x3dNode.fieldOfView = np.deg2rad(fov)


    def processBasicViewpointFields(self, x3dNode, dagNodeName, depNode):
        mlist = aom.MSelectionList()
        mlist.add(dagNodeName)
        tForm = aom.MFnTransform(mlist.getDependNode(0))

        # X3D centerOfRotation
        x3dNode.centerOfRotation = self.rkint.getSFVec3fFromMPoint(tForm.rotatePivot(aom.MSpace.kTransform))
        
        # X3D description - must be added manually by the user if camera node not created through the RawKee GUI
        dagNode = aom.MFnDagNode(mlist.getDependNode(0))
        try:
            x3dNode.description = dagNode.findPlug("x3dDescription", False).asString()
        except:
            self.cMessage("No 'description' X3D Field Found")
        
        # X3D farDistance
        x3dNode.farDistance = depNode.findPlug("farClipPlane", False).asFloat()
        
        # X3D jump - must be addedmanually by the user if camera node not created through the RawKee GUI
        try:
            x3dNode.jump = dagNode.findPlug("x3dJump",False).asBool()
        except:
            self.cMessage("No 'jump' X3D Field Found")
        
        ################################################################
        # X3D metadata
        # TODO: Implement metadata field
        
        ################################################################
        # X3D navigationInfo
        # TODO: Implement mechanism for implementing custom NavigationInfo
        # node within this Maya 'transform'
        
        # X3D nearDistance
        x3dNode.nearDistance = depNode.findPlug("nearClipPlane", False).asFloat()
        
        # X3D orientation
        x3dNode.orientation = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())

        # X3D position
        x3dNode.position = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))
        
        # X3D retainUserOffsets - must be addedmanually by the user if camera node not created through the RawKee GUI
        try:
            x3dNode.retainUserOffsets = dagNode.findPlug("x3dRetainUserOffsets", False).asBool()
        except:
            self.cMessage("No 'retainUserOffsets' X3D Field Found")
            
        # X3D viewAll
        try:
            x3dNode.viewAll = dagNode.findPlug("x3dViewAll", False).asBool()
        except:
            self.cMessage("No 'viewAll' X3D Field Found")
    
    ##########################################################################################################
    # Lighting Related Functions
    def processX3DLighting(self, dagNode, x3dPF):
        if dagNode.childCount() > 0:
            depNode = aom.MFnDependencyNode(dagNode.child(0))
            if depNode.typeName == "directionalLight":
                bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "DirectionalLight", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicLightFields(x3dNode, dagNode, depNode)

                    # X3D Direction
                    mlist = aom.MSelectionList()
                    mlist.add(dagNode.name())
                    tForm = aom.MFnTransform(mlist.getDependNode(0))
                    x3dNode.direction = self.rkint.getDirection(tForm.rotation(aom.MSpace.kTransform, False))
                    
            elif depNode.typeName == "spotLight":
                bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "SpotLight", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicLightFields(x3dNode, dagNode, depNode)
                
                    # X3D attenuation - Not sure this is anything close to being correct - TODO: Revise in the future.
                    dPlug = depNode.findPlug("dropoff", False)
                    dropOff = dPlug.asFloat()
                    dropOff = dropOff / 255.0
                    x3dNode.attenuation = (1.0, dropOff, 0.0)
                    
                    # X3D cutOffAngle and beamWidth
                    tCone   = depNode.findPlug("coneAngle", False).asMAngle(aom.MDGContext.kNormal).asRadians() / 2
                    cOffset = depNode.findPlug("penumbraAngle", False).asMAngle(aom.MDGContext.kNormal).asRadians() / 2
                    
                    #####################################
                    # This code is probably wrong.      #
                    #####################################
                    if tCone > 1.570796:                #
                        tCone = 1.570796                #
                    elif tCone < 0:                     #
                        tCone = 0                       #
                                                        #
                    if cOffset < -1.570796:             #
                        cOffset = -1.570796             #
                    elif cOffset > 1.570796:            #
                        cOffset = 1.570796              #
                                                        #
                    tBoth = tCone + cOffset             #
                                                        #
                    if tCone <= tBoth:                  #
                        if tBoth > 1.570796:            #
                            tBoth = 1.570796            #
                            if tCone > tBoth:           #
                                tCone = tBoth           #
                                                        #
                        x3dNode.cutOffAngle = tBoth     #
                        x3dNode.beamWidth   = tCone     #
                    else:                               #
                        if tCone > 1.570796:            #
                            tCone = 1.570796            #
                            if tBoth > tCone:           #
                                tBoth = 1.570796        #
                                                        #
                        x3dNode.cutOffAngle = tCone     #
                        x3dNode.beamWidth   = tBoth     #
                    #####################################

                    # X3D Direction
                    mlist = aom.MSelectionList()
                    mlist.add(dagNode.name())
                    tForm = aom.MFnTransform(mlist.getDependNode(0))
                    x3dNode.direction = self.rkint.getDirection(tForm.rotation(aom.MSpace.kTransform, False))
                    
                    # X3D Location
                    x3dNode.location = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))
                    
                    # X3D Radius - The C++ exporter used "Center of Illumination", but I no longer think that is correct
                    # ..skipping implementation for now.
                    # x3dNode.radius = depNode.findPlug("centerOfIllumination").asFloat()

            elif depNode.typeName == "pointLight":
                bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "PointLight", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicLightFields(x3dNode, dagNode, depNode)

                    # X3D attenuation - Not sure this is anything close to being correct - TODO: Revise in the future.
                    x3dNode.attenuation = (1.0, 0.0, 0.0)
                    
                    # X3D Location
                    mlist = aom.MSelectionList()
                    mlist.add(dagNode.name())
                    tForm = aom.MFnTransform(mlist.getDependNode(0))
                    x3dNode.location = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))

                    # X3D Radius - The C++ exporter used "Center of Illumination", but I no longer think that is correct
                    # ...skipping implementation for now.
                    # x3dNode.radius = depNode.findPlug("centerOfIllumination").asFloat()

            
            elif depNode.typeName == "aiSkyDomeLight":
                self.processEnviornmentLight(depNode, x3dPF[0], x3dPF[1], "EnvironmentLight", dagNode)
    
    
    def processNodeAsEnviornmentLight(self, envNode, texAttr, x3dParent, x3dField):
        # Use listConnections to find connected nodes
        # - source=True, destination=False: Look for upstream connections
        # - type='file': Filter the results to only include 'file' type nodes
        # - unique=True: Ensure only unique node names are returned
        tFile = cmds.listConnections(envNode.name() + "." + texAttr, source=True, destination=False, type='file', unique=True)
        print("tFile - Pass")
        if tFile:
            print("tFile - Is Valid")
            tfList = aom.MSelectionList()
            tfList.add(tFile[0])
            tfNode = aom.MFnDependencyNode(tfList.getDependNode(0))
            fbna = self.trv.processBasicNodeAddition(x3dParent, x3dField, "ImageCubeMapTexture", tfNode.name())
            if fbna[0] == False:
                relativeTexPath = self.rkImagePath
                localTexWrite   = self.activePrjDir + "/" + relativeTexPath

                filePath = cmds.getAttr(tFile[0] + ".fileTextureName")
                fileName = self.rkint.getFileName(filePath)
                fileExt  = os.path.splitext(fileName)[1]
                fileName = os.path.splitext(fileName)[0]
                
                if self.rkFileTexFormat > 0:
                    fileName = fileName + ".png"
                    localTexWrite   = localTexWrite + fileName
                    self.rkint.hdri2png(filePath, localTexWrite, bits=8)
                elif self.rkConsolidate == True:
                    fileName = self.rkint.getFileName(filePath)
                    localTexWrite = localTexwrite + fileName
                    self.rkint.copyFile(filePath, localTexWrite)
                else:
                    localTexWrite = filePath
                    
                if  self.rkFileTexType > 0:
                    x3dURIData = self.rkint.media2uri(localTexWrite)
                    fbna[1].url.append(x3dURIData)
                else:
                    relativeTexPath = relativeTexPath + fileName
                    fbna[1].url.append(fileName)
                    fbna[1].url.append(relativeTexPath)
        elif texAttr == "image":
            print("tFile - Is Not Valid - image")
            lcol = cmds.getAttr(envNode.name() + "." + texAttr)[0]
            x3dParent.color = self.getSFColor(lcol[0], lcol[1], lcol[2])
        else:
            print("tFile - Is Not Valid")


    def processEnviornmentLight(self,       skyDomeLight, x3dParent, x3dField, x3dType, dagNode):
        print("EL - Print me")
        bna = self.trv.processBasicNodeAddition(x3dParent, x3dField, x3dType, dagNode.name())
        if bna[0] == False:
            x3dNode = bna[1]
            self.processBasicLightFields(x3dNode, dagNode, skyDomeLight)
            
            # Use listConnections to find connected nodes
            # - source=True, destination=False: Look for upstream connections
            # - type='file': Filter the results to only include 'file' type nodes
            # - unique=True: Ensure only unique node names are returned
            tFile = cmds.listConnections(skyDomeLight.name() + ".color", source=True, destination=False, type='file')
            if tFile:
                tfList = aom.MSelectionList()
                tfList.add(tFile[0])
                tfNode = aom.MFnDependencyNode(tfList.getDependNode(0))
                fbna = self.trv.processBasicNodeAddition(bna[1], "specularTexture", "ImageCubeMapTexture", tfNode.name())
                if fbna[0] == False:
                    relativeTexPath = self.rkImagePath
                    localTexWrite   = self.activePrjDir + "/" + relativeTexPath

                    filePath = cmds.getAttr(tFile[0] + ".fileTextureName")
                    fileName = self.rkint.getFileName(filePath)
                    fileExt  = os.path.splitext(fileName)[1]
                    fileName = os.path.splitext(fileName)[0]
                    
                    if self.rkFileTexFormat > 0:
                        fileName = fileName + ".png"
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.hdri2png(filePath, localTexWrite)
                    elif self.rkConsolidate == True:
                        fileName = self.rkint.getFileName(filePath)
                        localTexWrite = localTexWrite + "/" + fileName
                        self.rkint.copyFile(filePath, localTexWrite)
                    else:
                        localTexWrite = filePath
                        
                    if  self.rkFileTexType > 0:
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        fbna[1].url.append(x3dURIData)
                    else:
                        relativeTexPath = relativeTexPath + fileName
                        fbna[1].url.append(fileName)
                        fbna[1].url.append(relativeTexPath)
            
            
    def processBasicLightFields(self, x3dNode, dagNode, depNode):
        # X3D AmbientIntensity - Maya Directional Light does not have an Amb Intensity attribute,
        # skipping this X3D Field
        
        # X3D 'global'
        # Lights are global if they are found in defaultLightSet, else 
        # they are scoped.
        nodes = cmds.listConnections(dagNode.name())
        isCon = False
        for n in nodes:
            if n == "defaultLightSet":
                isCon = True
                break
        x3dNode.global_ = isCon

        # X3D Color
        colorCons = cmds.listConnections(depNode.name() + ".color")
        if colorCons:
            pass
        else:
            co = cmds.getAttr(depNode.name() + ".color")[0]
            x3dNode.color = self.getSFColor(co[0], co[1], co[2])
        
        # X3D Intensity
        x3dNode.intensity = cmds.getAttr(depNode.name() + ".intensity")
        
        shCol = "shadowColor"

        if depNode.typeName == "aiSkyDomeLight":
            #X3D light is on
            if cmds.getAttr(depNode.name() + ".aiDiffuse") > 0:
                x3dNode.on = True
            elif cmds.getAttr(depNode.name() + ".aiSpecular") > 0:
                x3dNode.on = True

            # X3D shadows
            x3dNode.shadows = cmds.getAttr(depNode.name() + ".aiCastShadows")
            shCol = "aiShadowColor"
        
        else:
            #X3D light is on
            x3dNode.on = False
            if cmds.getAttr(depNode.name() + ".emitDiffuse") == True:
                x3dNode.on = True
            elif cmds.getAttr(depNode.name() + ".emitSpecular") == True:
                x3dNode.on = True
        
            # X3D shadows
            x3dNode.shadows = cmds.getAttr(depNode.name() + ".useRayTraceShadows")
        
        # X3D shadowIntensity
        so = cmds.getAttr(depNode.name() + "." + shCol)[0]
        tInt = (so[0] + so[1] + so[2] ) / 3
        x3dNode.shadowIntensity = 1 - tInt


    ######################################################################################################################
    #   Transform Related Functions
    def processX3DTransform(self, x3dParentDEF, dagNode, x3dPF):
        depNode = aom.MFnDependencyNode(dagNode.object())
        #dragPath = dragPath + "|" + depNode.name()
        bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Transform", depNode.name())
        if bna[0] == False:
            self.processBasicTransformFields(depNode, bna[1])
            
            #Traverse Maya Scene Downward without using an MFIt object
            groupDag = aom.MFnDagNode(depNode.object())
            cNum = groupDag.childCount()
            for i in range(cNum):
                child = aom.MFnDagNode(groupDag.child(i))
                self.traverseDownward(bna[1].DEF, child)
                

    def processBasicTransformFields(self, depNode, x3dNode, scaleFix=False):#888888
        # Transform Options
        x3dType = x3dNode.NAME()
        mayaType = depNode.typeName
        
        mlist = aom.MSelectionList()
        mlist.add(depNode.name())
        
        #####################################################################
        # MFloatMatrix way of doing things
        #####################################################################
        myDagPath    = mlist.getDagPath(0)
        fullMatrix   = myDagPath.inclusiveMatrix()
        fullPaMatrix = myDagPath.exclusiveMatrix()
        
        #####################################################################
        # Need to handle parentOffsetMatrix
        #####################################################################
        
        dataMatrix = aom.MMatrix()
        if (mayaType == "transform" and (x3dType == "Transform" or x3dType == "HAnimHumanoid")) or (mayaType == "joint" and x3dType == "Transform"):
            dataMatrix = fullMatrix * fullPaMatrix.inverse()
        
        transMatrix         = aom.MTransformationMatrix(dataMatrix)
        
        #X3D translation - transMatrix.translation() returns an MVector, getSFVec3f returns a tuple (x, y, z)
        x3dNode.translation = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))
        
        #X3D Rotation - tForm.rotation().asAxisAngle() returns a tuple (MVector, float) getSFRotation returns a tuple (x, y, z, w) 
        x3dNode.rotation = self.rkint.getSFRotation(transMatrix.rotation(aom.MSpace.kTransform).asAxisAngle())

        #X3D Scale - tForm.scale() returns a List [ x, y, z] What? Why not an MVector Autodesk?
        chVals = transMatrix.scale(aom.MSpace.kTransform)
        
        if mayaType == "joint" or scaleFix==True:
            chVals[0]     = abs(chVals[0])
            chVals[1]     = abs(chVals[1])
            chVals[2]     = abs(chVals[2])

            '''
            if chVals[0]  < 0.000001:
                chVals[0] = 0.0
                
            if chVals[1]  < 0.000001:
                chVals[1] = 0.0
                
            if chVals[2]  < 0.000001:
                chVals[2] = 0.0
            '''

        try:
            x3dNode.scale = self.rkint.getSFVec3fFromList(chVals)
        except:
            print("Scale failed in Process Basic Transform")
        
        ############################################################################################
        # X3D scaleOrientation - TODO
        # It's unclear to me how to extract the scaleOrientation X3D field value from Maya. My 
        # guess is that it could be calculated from some combo of "shear" and "scalePivot" 
        # attributes. But that kind of math hurts my brain - Aaron Bergstrom
        #
        # More than happy to get input from others to figure out how to calculate that. But until 
        # that happens, this X3D field for transform-style nodes will not be calculated.
        ############################################################################################
        
        ############################################################################################
        # X3D metadata - TODO
        ############################################################################################


        #X3D center
        ############################################################################################
        # In Maya the "center" roughly corresponds to the "Rotate" and "Scale" pivots. Unless you 
        # specifically set these values to be different, these Maya attributes usually have the 
        # same value. Oddly, even though the AttributeEditor displays these pivots as a 3 x float 
        # value, the Python API returns them as an MPoint object, which is a 4 x float value 
        # (x,y,z,w).
        ############################################################################################
        # Becuase some future code addition will likely use the "Scale" pivot to calculate the 
        # scaleOrientation value, I'm only using the "Rotate" pivot to represent the X3D "center" 
        # field value using only the x,y,z values of the MPoint object.
        ############################################################################################
        #### OLD WAY#### x3dNode.center = self.rkint.getSFVec3fFromMPoint(tForm.rotatePivot(aom.MSpace.kTransform))
        if mayaType == "transform" and (x3dType == "Transform" or x3dType == "HAnimHumanoid"):
            x3dNode.center = self.rkint.getSFVec3fFromMPoint(transMatrix.rotatePivot(aom.MSpace.kTransform))
        ############################################################################################
        #Keeping this old "center" field code incase I need this later.
        ############################################################################################
        #mPiv = depNode.findPlug("rotatePivot", False)
        #x3dNode.center = (mPiv.child(0).asFloat(), mPiv.child(1).asFloat(), mPiv.child(2).asFloat())
        
        ############################################################################################
        # X3D bboxSize and bboxCenter
        ############################################################################################
        cXMn = depNode.findPlug("boundingBoxMinX", False).asFloat()
        cXMx = depNode.findPlug("boundingBoxMaxX", False).asFloat()
        cYMn = depNode.findPlug("boundingBoxMinY", False).asFloat()
        cYMx = depNode.findPlug("boundingBoxMaxY", False).asFloat()
        cZMn = depNode.findPlug("boundingBoxMinZ", False).asFloat()
        cZMx = depNode.findPlug("boundingBoxMaxZ", False).asFloat()
        
        xLen = cXMx - cXMn
        yLen = cYMx - cYMn
        zLen = cZMx - cZMn
        
        # TODO: add option to not expoert bboxSize/Center
        if xLen > 0 and yLen > 0 and zLen > 0:
            x3dNode.bboxSize   = ( xLen,  yLen,  zLen )
            x3dNode.bboxCenter = ( (cXMx + cXMn) / 2, (cYMx + cYMn) / 2, (cZMx + cZMn) / 2 )
        
        x3dNode.visible = depNode.findPlug("visibility", False).asBool()
    
    
    ###################################################################################################
    # Check the dag node (probably a transform node) to see if it is connected to a 'bindPose' node. If
    # so, then return a boolean as True and the bindPose node's object wrapped in a MFNDependencyNode 
    # function set.
    #
    # TODO - the next 3 functions can probably be removed.
    #
    ###################################################################################################
    def getBindPoseNode(self, dagNode):
        for plug in dagNode.getConnections():
            depNode = aom.MFnDependencyNode(plug.connectedTo(False, True)[0].node())
            
            if depNode.typeName == "bindPose":
                return depNode
        
        return None


    def getBindPoseNodes(self, dagNode):
        
        bpList = []
        for plug in dagNode.getConnections():
            depNode = aom.MFnDependencyNode(plug.connectedTo(False, True)[0].node())
            
            if depNode.typeName == "bindPose":
                bpList.append(depNode)
        
        return bpList


    def checkForMayaJoints(self, dagNode):
        #Traverse Maya Scene Downward without using an MFIt object
        cNum = dagNode.childCount()
        for i in range(cNum):
            if aom.MFnDagNode(dagNode.child(i)).typeName == "joint":
                return True

        return False

    
    ######################################################################################################################
    # HAnimHumanoid Related Functions
    # HAnimMotion nodes are only allowed if the dagNode is a Maya "transform" node that has the "x3dType" 
    # custom attribute defined and it is set to "HAnimHumanoid"
    ######################################################################################################################
    def processHAnimHumanoid(self, dagNode, x3dPF, skinSpaceMatrix=aom.MMatrix()):
        depNode = aom.MFnDependencyNode(dagNode.object())
        
        hName = depNode.name()
            
        # Create X3D HAnimHumanoid node
        bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "HAnimHumanoid", nodeName=hName)
        
        if bna[0] == False:
            if depNode.typeName != "joint":
                self.processBasicTransformFields(depNode, bna[1])
            
            #############################################################################################
            #############################################################################################
            #############################################################################################
            ###
            ###
            ###    Beginning of Parsing the Character Rig - This could get quite complex.
            ###
            ###
            #############################################################################################
            #############################################################################################
            #############################################################################################
            
            try:
                bna[1].skeletalConfiguration = cmds.getAttr(hName + ".skeletalConfiguration")
            except:
                bna[1].skeletalConfiguration = "BASIC"
                
            try:
                bna[1].loa = cmds.getAttr(hName + ".LOA")
            except:
                bna[1].loa = -1
                
            
            # 'sm' is a list of mesh nodes used for the skin of this HAnimHumanoid
            sm = []
            
            # 'sc' is a list of skinClsuters
            sc = []

            # MFnDagNode version of Humanoid Node
            cNum = dagNode.childCount()

            # Traverse the Skeleton
            # Process as the rooe node if the depNode/dagNode is a Maya "joint" node
            if depNode.typeName == "joint":
                self.processHAnimJoint(        bna[1].DEF, dagNode, bna[1], bna[1], cField="skeleton", sk=sm, wssm=skinSpaceMatrix)
            # Else assume depNode/dagNode is a Transform intended to serve as a 
            # representation of an HAnimHumanoid node, and process all of its 
            # children that are Maya "joint" nodes. The assumption that there is
            # only one joint node in its immediate children, but this is not 
            # enforced. If the transform's immediate children contain more than
            # one Maya joint node, results are undefined.
            else:
                for i in range(cNum):
                    dagChild = aom.MFnDagNode(dagNode.child(i))
                    if   dagChild.typeName == "joint":
                        self.processHAnimJoint(bna[1].DEF, dagChild, bna[1], bna[1], cField="skeleton", sk=sm, wssm=skinSpaceMatrix)
                
            # Get Weight/point Index Offset and Skin Coordinate Node name.
            # wio length might be 0 and cName might equal "" if sm length is 0.
            wio, cName = self.getSkinCoordinateNode(bna[1], sm, coordName=hName, wssm=skinSpaceMatrix)
            
            # Get Normal Vertex Index Offset and Skin Normal Node name
            # Depnding on export options 'sno' length might = 0, and 
            # sName might be equial to "".
            sno, sName = self.getSkinNormalNode(bna[1], sm, normalName=hName)
            
            # Adds X3D Shape nodes to 'skin' field of the humanoid. Assumes 
            # that mesh is point values are in world coordinates.
            smLen = len(sm)
            snLen = len(sno)
            for i in range(smLen):
                # This is needed if the sno length is zero so as not to throw an out-of-bounds error on the list.
                if snLen == 0:
                    sno.append(snLen)
                self.processMayaMesh(bna[1].DEF, aom.MFnDagNode(sm[i].object()), "skin", wio[i], sno[i], cName, sName, isAvatar=True)
            
            # Section where we add HAnimMotion, or other timing nodes (aka TimeSensor, AudioClip, and MovieTexture)
            nonMotionRKAPNodes = []
            for i in range(cNum):
                dagChild = aom.MFnDagNode(dagNode.child(i))
                if dagChild.typeName == "rkAnimPack":
                    
                    # Determine what time of timing node this is.
                    apType = cmds.getAttr(dagChild.name() + ".mimickedType")
                    
                    # If rkAnimPack node is designated as an HAnimMotion node process now.
                    if apType == 2:
                        self.processHAnimMotion(bna[1].DEF, dagChild, bna[1])
                        
                    # If it's any other type of timing node, append to the non-Motion node list
                    # for later processing.
                    elif apType == 1 or apType == 3 or apType == 4:
                        nonMotionRKAPNodes.append(dagChild)
            
            if len(nonMotionRKAPNodes) > 0:
                self.processRKAnimPacks(bna[1].DEF, nonMotionRKAPNodes, bna[1], "skin")


    def processRKAnimPacks(self, x3dParentDEF, rkAPNodes, x3dParent, x3dField):
        parentNode = x3dParent
        cField = x3dField
        
        ######################################################
        # Run this code to export Animation data 
        # at the end of the file is selected.
        ######################################################
        parentNode = self.eofScene
        cField = "children"
            
        bna = self.trv.processBasicNodeAddition(parentNode, cField, "Group", x3dParent.DEF + "_TimerGroup")
        if bna[0] == False:
            for apNode in rkAPNodes:
                apType = cmds.getAttr(apNode.name() + ".mimickedType")
                if apType == 1:
                    self.processAudioClipNode(   apNode, bna[1], "children")
                elif apType == 3:
                    self.processMovieTextureNode(apNode, bna[1], "children")
                elif apType == 4:
                    self.processTimeSensorNode(  apNode, bna[1], "children")
                    

    def processSingleRKAnimPack(self, x3dParentDEF, apNode, x3dField="children"):
        x3dParent = self.getX3DParent(apNode, x3dParentDEF) 
        
        apType = cmds.getAttr(apNode.name() + ".mimickedType")
        if apType == 1:
            self.processAudioClipNode(   apNode, x3dParent, x3dField)
        elif apType == 3:
            self.processMovieTextureNode(apNode, x3dParent, x3dField)
        elif apType == 4:
            self.processTimeSensorNode(  apNode, x3dParent, x3dField)


    def processAudioClipNode   (self, apNode, timerGroup, cField):
        bna = self.trv.processBasicNodeAddition(timerGroup, cField, "AudioClip", apNode.name())

        
    def processMovieTextureNode(self, apNode, timerGroup, cField):
        bna = self.trv.processBasicNodeAddition(timerGroup, cField, "MovieTexture", apNode.name())

    #Processing TimeSensor Node
    def processTimeSensorNode   (self, apNode, timerGroup, cField):
        bna = self.trv.processBasicNodeAddition(timerGroup, cField, "TimeSensor", apNode.name())
        
        if bna[0] == False:
            ##########################################
            # Store for later collection
            ##########################################
            aLen = len(self.animation)
            self.animation.append([])
            animPackage = self.animation[aLen]
            animPackage.append(apNode)
            animPackage.append(bna[1])
            ##########################################
            
            #Maya Timeline Key Frame Step (Timeline steps)
            kfs  = cmds.getAttr(apNode.name() + ".keyFrameStep")
            
            #Maya Timeline Start Frame
            tsaf = cmds.getAttr(apNode.name() + ".timelineStartFrame")
            
            #Maya Timeline Stop Frame
            tsof = cmds.getAttr(apNode.name() + ".timelineStopFrame")
            
            #Number of frames per second
            fps  = cmds.getAttr(apNode.name() + ".framesPerSecond")
            
            #Number of Maya frames covered by this sensor.
            frameDistance = tsof - tsaf
            
            #Calcualte the X3D cycleInterval
            bna[1].cycleInterval = frameDistance / fps
            
            #To Be Removed later
            cmds.setAttr(apNode.name() + ".cycleInterval", bna[1].cycleInterval)
            
            bna[1].description = cmds.getAttr(apNode.name() + ".description")
            bna[1].resumeTime  = cmds.getAttr(apNode.name() + ".resumeTime")
            bna[1].pauseTime   = cmds.getAttr(apNode.name() + ".pauseTime")
            bna[1].startTime   = cmds.getAttr(apNode.name() + ".startTime")
            bna[1].stopTime    = cmds.getAttr(apNode.name() + ".stopTime")

            bna[1].enabled     = cmds.getAttr(apNode.name() + ".enabled")
            bna[1].loop        = cmds.getAttr(apNode.name() + ".loop")
            
            # Time to actually collect the animation data and store it in X3D objects
            timerExpressions = []
            mIter = aom.MItDependencyGraph(apNode.object(), rkfn.kExpression, aom.MItDependencyGraph.kDownstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
            while not mIter.isDone():
                eNode = aom.MFnDependencyNode(mIter.currentNode())
                interp = ""
                try:
                    interp = cmds.getAttr(eNode.name() + '.x3dInterpolatorType')
                except:
                    pass
                if interp != "":
                    timerExpressions.append(eNode)
                    
                mIter.next()
            
            ###### preFrame = cmds.currentTime(query=True)## --- ################
            for tExp in timerExpressions:
                x3dNodeType = cmds.getAttr(tExp.name() + '.x3dInterpolatorType')
                bni = self.trv.processBasicNodeAddition(timerGroup, cField, x3dNodeType, tExp.name())
                if bni[0] == False:
                    ############################################################################
                    ###### cons   = cmds.listConnections(tExp.name(), p=True, s=True, et=True, sh=True)
                    ###### cParts = cons[0].split('.')

                    ###### mlist = aom.MSelectionList()
                    ###### mlist.add(cParts[0])
                    ###### tForm = aom.MFnTransform(mlist.getDependNode(0))
                    ####################################################
                    ####################################################
                    
                    # TODO - write code that sets the value of modifier, for now make it
                    # equal to ""
                    modifier      = ""
                    toConnection  = cmds.listConnections(tExp.name(), p=True, s=True, et=True, sh=True)
                    attrSList     = aom.MSelectionList()
                    attrSList.add(toConnection[0])
                    attrParts     = toConnection[0].split('.')
                    interpPackage = [tExp, bni[1], attrParts[0], attrParts[1], modifier, attrSList.getPlug(0)]
                    animPackage.append(interpPackage)
                    ####################################################
                    ####################################################
                    
                    #tForm.translation()
                    
                    #self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())

                    ###### lStep = 0
                    ###### fraction = 0.0
                    ###### while fraction < 1.0:
                    ######     bni[1].key.append(fraction)
                    ######     cmds.currentTime(tsaf + (lStep * kfs))
                    ######     ########### 
                    ######     # Get data
                    ######     value = cmds.getAttr(tExp.name() + ".receivedData")
                    ######     if x3dNodeType == "PositionInterpolator":
                    ######         bni[1].keyValue.append((value[0][0], value[0][1], value[0][2]))
                    ######     elif x3dNodeType == "OrientationInterpolator":
                    ######         #tForm = aom.MFnTransform(mlist.getDependNode(0))
                    ######         oriValue = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())#self.rkint.getSFRotationFromEuler([value[0][0], value[0][1], value[0][2]])
                    ######         bni[1].keyValue.append(oriValue)#(oriValue[0], oriValue[1], oriValue[2], oriValue[3]))
                    ######     lStep += 1
                    ######     fraction = kfs * lStep / frameDistance
                    ###### bni[1].key.append(1.0)
                    ###### cmds.currentTime(tsof)
                    ###### ###########
                    ###### # Get data
                    ###### value = cmds.getAttr(tExp.name() + ".receivedData")
                    ###### if x3dNodeType == "PositionInterpolator":
                    ######     bni[1].keyValue.append((value[0][0], value[0][1], value[0][2]))
                    ###### elif x3dNodeType == "OrientationInterpolator":
                    ######     oriValue = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())#self.rkint.getSFRotationFromEuler([value[0][0], value[0][1], value[0][2]])
                    ######     bni[1].keyValue.append(oriValue)#(oriValue[0], oriValue[1], oriValue[2], oriValue[3]))
                    
                    ##################
                    # Build Routes
                    ##################
                    setFieldValue = "set_"
                    if x3dNodeType        == "PositionInterpolator":
                        if attrParts[1]   == "translate":
                            setFieldValue += "translation"
                        elif attrParts[1] == "scale":
                            setFieldValue += "scale"
                    elif x3dNodeType      == "OrientationInterpolator":
                        if attrParts[1]   == "rotate":
                            setFieldValue += "rotation"
                            
                    self.generateRoutes(bna[1].DEF, 'fraction_changed', bni[1].DEF,   'set_fraction', timerGroup, cField)
                    self.generateRoutes(bni[1].DEF, 'value_changed',    attrParts[0], setFieldValue,  timerGroup, cField)
                    
            ###### cmds.currentTime(preFrame)


    def generateRoutes(self, fromNode, outEvent, toNode, inEvent, x3dParentNode, x3dFieldName):
        newRoute = self.trv.getRouteObject()
        newRoute.fromNode  = fromNode
        newRoute.fromField = outEvent
        newRoute.toNode    = toNode
        newRoute.toField   = inEvent
        
        nodeField = getattr(x3dParentNode, x3dFieldName)
        if isinstance(nodeField, list):
            nodeField.append(newRoute)


    def generateFields(self, fieldName, fieldType, fieldAccessType):
        newField = self.trv.getFieldObject()
        newField.name       = fieldName
        newField.type       = fieldType
        newField.accessType = fieldAccessType
        
        return newField
        
    def processHAnimMotion(self, x3dParentDEF, moNode, x3dHumanoid, cField="motions"):
        bna = self.trv.processBasicNodeAddition(x3dHumanoid, cField, "HAnimMotion", moNode.name())

        if bna[0] == False:
            #Maya Timeline Key Frame Step (Timeline steps)
            kfs  = cmds.getAttr(moNode.name() + ".keyFrameStep")
            
            #Maya Timeline Start Frame
            tsaf = cmds.getAttr(moNode.name() + ".timelineStartFrame")
            
            #Maya Timeline Stop Frame
            tsof = cmds.getAttr(moNode.name() + ".timelineStopFrame")
            
            #Motion Stop Frame
            bna[1].endFrame = tsof - tsaf
            
            #Number of frames per second
            fps  = cmds.getAttr(moNode.name() + ".framesPerSecond")
            
            #Motion Frame Duration
            bna[1].frameDuration = 1.0 / fps
            
            #####################################
            # Other motion fields set to default:
            # startFrame     0 
            # frameIncrement 1
            # frameIndex     0
            
            bna[1].loa     = cmds.getAttr(moNode.name() + ".loa")
            bna[1].enabled = cmds.getAttr(moNode.name() + ".enabled")
            bna[1].loop    = cmds.getAttr(moNode.name() + ".loop")
            bna[1].description = cmds.getAttr(moNode.name() + ".description")
            bna[1].name    = moNode.name() 
            
            trsJoints = []
            rotJoints = []
            moeNodes  = cmds.listConnections(moNode.name() + ".message", et=True, d=True,         t='expression')
            
            for mexp in moeNodes:
                retList = cmds.listConnections( mexp +  ".receivedData", et=True, s=True, p=True, t="joint"     )
                if ".translate" in retList[0] or ".rotate" in retList[0]:
                    aniKey = moNode.name() + "." + retList[0]
                    self.rkMotions[aniKey] = True

            ##########################################
            # Store for later collection
            ##########################################
            aLen = len(self.animation)
            self.animation.append([])
            animPackage = self.animation[aLen]
            animPackage.append(moNode)
            animPackage.append(bna[1])
            animPackage.append(self.getX3DParent(moNode, x3dParentDEF))

                
    def calculateHAnimJointInfoForHAnimMotion(self, moNode):
        for j in range(moNode.jLen):
            
            hAnimJointName = ""
            
            sideVal = cmds.getAttr(moNode.jvName[j] + ".side")
            if moNode.loa == -1:
                if sideVal == 0:
                    hAnimJointName += "Center_"
                    #hAnimJointName += "c_"
                elif sideVal == 1:
                    hAnimJointName += "Left_"
                    #hAnimJointName += "l_"
                elif sideVal == 2:
                    hAnimJointName += "Right_"
                    #hAnimJointName += "r_"
            elif moNode.loa > 0:
                if sideVal == 1:
                    hAnimJointName += "l_"
                if sideVal == 2:
                    hAnimJointName += "r_"

            nType = cmds.getAttr(moNode.jvName[j] + ".type")
            if nType == 18:
                otherType = cmds.getAttr(moNode.jvName[j] + ".otherType")
                if otherType == "":
                    hAnimJointName += moNode.jvName[j]
                else:
                    hAnimJointName += otherType
            else:
                #hAnimJointName += self.getJointType(nType)
                nameType = self.getJointType(str(nType))
                if nameType == "":
                     hAnimJointName += moNode.jvName[j]
                else:
                     hAnimJointName += nameType
            
            localName = hAnimJointName
            if moNode.jvLen[j] == 0:
                localName = "IGNORED"
                moNode.jvLen[j] = 3
                moNode.jvText[j] = "Xrotation Yrotation Zrotation"
            
            moNode.channels += (str(moNode.jvLen[j]) + " ")
            moNode.channels += moNode.jvText[j]
            
            if localName == "IGNORED":
                moNode.channelsEnabled.append(False)
            else:
                moNode.channelsEnabled.append(True)
            moNode.joints += localName
            if j < moNode.jLen-1:
                moNode.channels += " "
                moNode.joints   += " "


    def getMeshFromJoint(self, jNode, sm):
        mIter = aom.MItDependencyGraph(jNode.object(), rkfn.kMesh, aom.MItDependencyGraph.kDownstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
        while not mIter.isDone():
            mNode = aom.MFnMesh(mIter.currentNode())
            hasFound = False
            for m in sm:
                if m.name() == mNode.name():
                    hasFound = True
            if hasFound == False:
                sm.append(mNode)
            
            mIter.next()


    def getSkinNormalNode(self, x3dParent, skm, normalName="humanoid"):
        sno = []
        nName = normalName
        
        if self.rkNormalOpts > 0 and len(skm) > 0:
            nName = nName + "_Normal"
            normalbna = self.trv.processBasicNodeAddition(x3dParent, "skinNormal", "Normal", nName)
            #normalbna = self.trv.processBasicNodeAddition(x3dParent, "skinBindingNormals", "Normal", nName)
            #sknbna    = self.trv.processBasicNodeAddition(x3dParent, "skinNormal", "Normal", nName)

            for sm in skm:
                interSM = self.getIntermediateMesh(sm)
                #mList = aom.MSelectionList()
                #mList.add(interSM.name())
                #mIter = aom.MItMeshPolygon(mList.getDagPath(0)) #interSM.object())
                
                slen = len(sno)
                offset = 0

                na = interSM.getNormals()
                if self.rkNormalOpts == 1 or self.rkNormalOpts == 4:
                    for n in na:
                        if normalbna[0] == False:
                            normalbna[1].vector.append((n.x, n.y, n.z))
                            offset += 1
                elif self.rkNormalOpts == 2 or self.rkNormalOpts == 5:
                    for i in range(interSM.numPolygons):
                        pn = interSM.getPolygonNormal(i)
                        if normalbna[0] == False:
                            normalbna[1].vector.append((pn.x, pn.y, pn.z))
                            offset += 1

                #while not mIter.isDone():
                #    #Normals Per Vertex
                #    if self.rkNormalOpts == 1 or self.rkNormalOpts == 4:
                #        tns = mIter.getNormals()
                #        for tn in tns:
                #            if normalbna[0] == False:
                #                normalbna[1].vector.append((tn.x, tn.y, tn.z))
                #            offset += 1
                #    
                #    #Normals Per Face
                #    elif self.rkNormalOpts == 2 or self.rkNormalOpts == 5:
                #        tn = mIter.getNormal(aom.MSpace.kObject)
                #        if normalbna[0] == False:
                #            normalbna[1].vector.append((tn.x, tn.y, tn.z))
                #        offset += 1
                #        
                #    mIter.next()
                if slen > 0:
                    offset = offset + sno[slen-1]
                sno.append(offset)
            
            # Need to shift the Noraml offset over, because index 0 should have a
            # value of 0
            n = len(sno)
            last = 0
            for nIdx in range(n):
                tLast = sno[nIdx]
                sno[nIdx] = last
                last = tLast

        return sno, nName


    def getSkinCoordinateNode(self, x3dParent, skm, coordName="humanoid", wssm=aom.MMatrix()):
        ##### Add an X3D Coordiante Node
        wio = []
        cName = coordName
        skmLen = len(skm)
        
        if skmLen > 0:
            cName = cName + "_Coord"
            coordbna = self.trv.processBasicNodeAddition(x3dParent, "skinCoord", "Coordinate", cName)
            #coordbna = self.trv.processBasicNodeAddition(x3dParent, "skinBindingCoords", "Coordinate", cName)
            #skcbna   = self.trv.processBasicNodeAddition(x3dParent, "skinCoord", "Coordinate", cName)
            for sm in skm:
                ###########################################################################
                # 
                # Add code to grabe the original mesh intermediate object
                # 
                ###########################################################################
                interSM = self.getIntermediateMesh(sm)

                # Multiplier to translate mesh verticies into character/avatar Model Space
                sType=aom.MSpace.kWorld
                if wssm == aom.MMatrix():
                    sType = aom.MSpace.kObject
                else:
                    inList = aom.MSelectionList()
                    inList.add(interSM.name())
                    wssm = inList.getDagPath(0).inclusiveMatrix() * wssm.inverse()
                
                points = interSM.getFloatPoints(space=sType)
                wlen = len(wio)
                offset = 0
                for point in points:
                    point  = point * aom.MFloatMatrix(wssm)
                    if coordbna[0] == False:
                        coordbna[1].point.append((point.x, point.y, point.z))
                        #skcbna[1].point.append((0.0, 0.0, 0.0))
                    offset += 1
                if wlen > 0:
                    offset = offset + wio[wlen-1]
                wio.append(offset)
            
            # Need to shift the Weigth/Coordiante offset over, because index 0 should have a
            # value of 0
            n = len(wio)
            last = 0
            for nIdx in range(n):
                tLast = wio[nIdx]
                wio[nIdx] = last
                last = tLast
                
        if skmLen > 0:
            for mIdx in range(skmLen):
                print("Mesh before collect Skin Weights: " + skm[mIdx].name())
                self.collectSkinWeightsForMesh(skm[mIdx], x3dParent.joints, wio, mIdx)

        coordLen = 0

        return wio, cName


    def getIntermediateMesh(self, mNode):
        return mNode

        # The code below should be removed. We only need the deformed mesh, assuming that we can pose the character in teh default I-pose at 
        # time of export.
        ##############################
        # Old Code
        ##############################
        # meshIter = aom.MItDependencyGraph(mNode.object(), rkfn.kMesh, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # while not meshIter.isDone():
        #    return aom.MFnMesh(meshIter.currentNode())
        #    meshIter.next()
        #
        #return None


    ################################################################
    #   mNode is an MFnMesh object
    #   x3dShape is the X3D Shape node holding the influenced 
    #            X3D geometry node.
    def collectCGESkinWeightsForMesh(self, mNode, x3dShape):
        weightData = []
        smlist = aom.MSelectionList()
        smlist.add(mNode.name())
        mpath = smlist.getDagPath(0)
        compIDs   = [m for m in range(mNode.numVertices)]
        singleFn  = aom.MFnSingleIndexedComponent()
        shapeComp = singleFn.create(aom.MFn.kMeshVertComponent)
        singleFn.addElements(compIDs)
        
        ######################################################
        # Get a list of skin clusters that affect this MFnMesh
        skClusters = []
        skIter     = aom.MItDependencyGraph(mNode.object(), rkfn.kSkinClusterFilter, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
        while not skIter.isDone():
            skClusters.append(aoma.MFnSkinCluster(skIter.currentNode()))
            skIter.next()
        
        ######################################################
        # Collect the weighting and joint influences for each
        # Vertex in the Mesh ndoe.
        rkWeightSort = [[] for _ in range(mNode.numVertices)]
        rkJointSort  = [[] for _ in range(mNode.numVertices)]
        
        for skc in skClusters:
            #wMethod     = skc.findPlug("skinningMethod", False).asInt()
            dPaths      = skc.influenceObjects()
            jNames      = []
            for dp in dPaths:
                jNode = aom.MFnDagNode(dp)
                jNames.append(jNode.name())
            meshWeights = []
            numInf      = 0
            meshWeights, numInf = skc.getWeights(mpath, shapeComp)
            mWeights = []
            for value in meshWeights:
                mWeights.append(float(value))
                
            wSort = [mWeights  [i:i + numInf] for i in range(0, len(mWeights), numInf)]
            
            for wIdx in range(mNode.numVertices):
                for fIdx in range(numInf):
                    rkWeightSort[wIdx].append(wSort[wIdx][fIdx])
                    rkJointSort[ wIdx].append(jNames[fIdx])

        x3dShape.rkWeightsData = rkWeightSort
        x3dShape.rkJointsData  = rkJointSort
        

    def collectSkinWeightsForMesh(self, mNode, xjList, wio, mIdx):
        smlist = aom.MSelectionList()
        smlist.add(mNode.name())
        mpath = smlist.getDagPath(0)
        comp_ids   = [m for m in range(mNode.numVertices)]
        single_fn  = aom.MFnSingleIndexedComponent()
        shape_comp = single_fn.create(aom.MFn.kMeshVertComponent)
        single_fn.addElements(comp_ids)
        
        print("Looking for skin clusters for " + mNode.name())
        skClusters = []
        scIter = aom.MItDependencyGraph(mNode.object(), rkfn.kSkinClusterFilter, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
        while not scIter.isDone():
            skClusters.append(aoma.MFnSkinCluster(scIter.currentNode()))
            scIter.next()
        
        if len(skClusters) > 0:
            wMethod = skClusters[0].findPlug("skinningMethod", False).asInt()

            dPaths = skClusters[0].influenceObjects()

            meshWeights = []
            numInf      = 0
            nVtx = mNode.numVertices

            if wMethod == 0:
                meshWeights, numInf = skClusters[0].getWeights(     mpath, shape_comp)
            else:
                #meshWeights         = skClusters[0].getBlendWeights(mpath, shape_comp)
                #numInf = len(dPaths)
                #blendWeights         = skClusters[0].getBlendWeights(mpath, shape_comp)
                #newWeights = [blendWeights[i] for i in range(len(blendWeights))]
                #skClusters[0].setWeights(mpath, shape_comp, dPaths, newWeights, True) # Normalize set to False
                meshWeights, numInf = skClusters[0].getWeights(     mpath, shape_comp)

            lWeights = []
            
            # Create and hold an array of weight values per influence object (aka joint)
            for i in range(numInf):
                lWeights.append([])
            
            print(mNode.name() + "Mesh Weights: " + str(len(meshWeights)) + ", numInf: " + str(numInf) + ", mw/ni: " + str(len(meshWeights)/numInf) + ", numVerts: " + str(nVtx))
            
            try:
                for h in range(nVtx):
                    nextWeight = h * numInf
                    try:
                        for j in range(numInf):
                            lWeights[j].append(meshWeights[nextWeight+j])
                    except:
                        if h < 500:
                            print("H Value Failed: " + str(h))

                for l in range(len(dPaths)):
                    x3dJoint = self.trv.getGeneratedX3D(dPaths[l].partialPathName())
                    
                    jWeights = lWeights[l]
                    for vIdx in range(nVtx):
                        if jWeights[vIdx] > 0:
                            x3dJoint.skinCoordIndex.append(vIdx + wio[mIdx])
                            x3dJoint.skinCoordWeight.append(jWeights[vIdx])
            except Exception as e:
                print(mNode.name() + ", numInf: " + str(numInf) + ", dPaths len: " + str(len(dPaths)) + ", lWeights len: " + str(len(lWeights)))
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")                            
#                print("Node Type: " + aom.MFnDependencyNode(dPaths[l].node()).name() + ", Name: " + dPaths[l].partialPathName())
        else:
            print("Couldn't find skinClusters for: " + mNode.name())

    
    def processCGESkin(self, rNode, x3dPF, skinSpaceMatrix=aom.MMatrix()):
        
        #Setup Skin Node DEF value.
        skinName = "CGESkin"
        skNameInt = 0
        skinDEF = skinName + "_" + str(skNameInt)
        skNameExists = True
        while skNameExists == True:
            skNameExists = self.trv.checkIfHasBeen(skinDEF) #cmds.objExists(skinDEF)
            if skNameExists == True:
                skNameInt += 1
                skinDEF = skinName + "_" + str(skNameInt)
            
        #No dragPath change 777777
        #bna = self.trv.processBasicNodeAddition(None, x3dParent, cField, "CGESkin", skinDEF)
        bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "CGESkin", skinDEF)
        if bna[0] == False:
            #################################################
            # List holding all Mesh node objects influenced
            # by this skeleton
            allShapes = []
            
            #################################################
            # List holding all Maya Joint node objects in
            # this skeleton
            allJoints = []
            
            #################################################
            # Process CGESkin "skeleton" and "joints" fields
            self.processMayaJointAsCGETransform(bna[1].DEF, rNode, bna[1], bna[1], cField="skeleton", allShapes=allShapes, allJoints=allJoints)

            # The dict {} that associates the appropriate Maya mesh with this skins X3D Shape nodes.
            mCollector = {}
            
            #################################################t
            # Process CGESkin "shapes" field
            for mesh in allShapes:
                #cgeShape = self.processMayaMesh(bna[1].DEF, mesh, cField="shapes", isAvatar=True, adjustment=skinSpaceMatrix)
                #bLen = len(bna[1].shapes)
                tmc = self.processMayaMesh(bna[1].DEF, mesh, cField="shapes", isAvatar=True, adjustment=skinSpaceMatrix)
                for key in tmc:
                    mCollector[key] = tmc[key]
                #aLen = len(bna[1].shapes)
                
            ######################################################################
            # Grab the new shape nodes from the CG Skin node, and populate it with 
            # weighting and joint info
            cRange = len(mCollector)
            
            print("Mesh Collector Length: " + str(cRange))
            for i in range(cRange):
                try:
                    mcMesh = mCollector.get(bna[1].shapes[i].DEF, None)
                    if mcMesh:
                        self.populateCGEWeightInformation(mcMesh, bna[1].shapes[i], allJoints)
                    else:
                        print("####\n\n\n--" + bna[1].shapes[i].DEF + "--\n\n\n####")
                except Exception as e:
                    print(f"Exception Type: {type(e).__name__}")
                    print(f"Exception Message: {e}")                            

            self.populateCGEInverseBindMatrices(bna[1], allJoints, ssm=skinSpaceMatrix)


    def populateCGEInverseBindMatrices(self, x3dSkin, allJoints, ssm=aom.MMatrix()):
        jList = aom.MSelectionList()
        for joint in allJoints:
            jList.add(joint)
        
        for i in range(len(allJoints)):
            path = jList.getDagPath(i)
            
            # Store Bind Pose for Later
            jMat = path.inclusiveMatrix()
            pMat = path.exclusiveMatrix()
            self.rkBindPose[allJoints[i]] = (jMat, pMat)

            jMat = jMat * ssm.inverse()
            jsm  = jMat.inverse()
            imx  = (jsm.getElement(0,0), jsm.getElement(0,1), jsm.getElement(0,2), jsm.getElement(0,3),
                    jsm.getElement(1,0), jsm.getElement(1,1), jsm.getElement(1,2), jsm.getElement(1,3),
                    jsm.getElement(2,0), jsm.getElement(2,1), jsm.getElement(2,2), jsm.getElement(2,3),
                    jsm.getElement(3,0), jsm.getElement(3,1), jsm.getElement(3,2), jsm.getElement(3,3))

            x3dSkin.inverseBindMatrices.append(imx)
            bna = self.trv.processBasicNodeAddition(x3dSkin, "joints", "Transform", nodeName=allJoints[i])


    def populateCGEWeightInformation(self, mesh, shape, allJoints):
        # (meshWeights, numInf, jNames)
        points = mesh.getFloatPoints()
        pLen   = mesh.numVertices

        #####################################################
        # Making a list of lists of the length that equals 
        # the total number vertices.
        pointWeights = shape.rkWeightsData#[[] for _ in range(pLen)]
        influJoints  = [[] for _ in range(pLen)]
        
        lwd = len(shape.rkJointsData)
        for p in range(lwd):
            
            ajLen = len(allJoints)
            for r in range(len(shape.rkJointsData[p])):
                for j in range(ajLen):
                    if shape.rkJointsData[p][r] == allJoints[j]:
                        #print("Influnce Name: " + allJoints[j] + ", index: " + str(j))
                        influJoints[p].append(j)
                
        for l in range(pLen):#444444
            
            comboSort = sorted(zip(pointWeights[l], influJoints[l]), key=lambda x: x[0], reverse=True)
            pointWeights[l], influJoints[l] = zip(*comboSort)
            
            #print("weights len: " + str(len(pointWeights[l])))
            #print("joints len: " + str(len(influJoints[l])))
            
        for idx in range(pLen):
            wg = pointWeights[idx]
            jt = influJoints[idx]
            
            #print("wg len: " + str(len(wg)))
            #print("jt len: " + str(len(jt)))
            
            limit  = 4
            aLimit = 0
            
            if rkSkinInfluence > 0:
                limit = 8
                
            if len(wg) < limit:
                aLimit = len(wg)
            else:
                aLimit = limit
            tWg  = wg[:aLimit]
            tJt  = jt[:aLimit]
            wVal = 1.0 - sum(tWg)
            avg  = wVal / aLimit
            
            if wVal < 1.0 and wVal > 0.0:
                tList = list(tWg)                
                for iv in range(aLimit):
                    tList[iv] += avg
                tWg = tuple(tList)

            while aLimit < limit:
                tWg = tWg + (0.0,)
                tJt = tJt + (0,)
                aLimit += 1
            
            for m in range(limit):
                if m < 4:
                    #print("Less than 4 - w: " + str(tWg[m]))
                    #print("Less than 4 - j: " + str(tJt[m]))
                    shape.geometry.skinWeights0.append(tWg[m])
                    shape.geometry.skinJoints0.append( tJt[m])
                else:
                    #print("Less than 8 - w: " + str(tWg[m]))
                    #print("Less than 8 - j: " + str(tJt[m]))
                    shape.geometry.skinWeights1.append(tWg[m])
                    shape.geometry.skinJoints1.append( tJt[m])
        
        print("Deleting rkWeightsData for " + shape.DEF)
        del shape.rkWeightsData
        del shape.rkJointsData


    def getJointLocalMatrix(self, dagPath):
        """
        Returns a joint's true local matrix, correctly accounting for
        segmentScaleCompensate (SSC).
        dagPath: MDagPath to the joint
        """

        # World matrix of *this* joint
        inclusive = dagPath.inclusiveMatrix()

        # World matrix of *parent*
        exclusive = dagPath.exclusiveMatrix()

        # First-pass local matrix (if no SSC)
        local = inclusive * exclusive.inverse()

        # Handle segment scale compensation
        fnJoint = aoma.MFnIkJoint(dagPath)
        
        ssc = True
        try:
            sscPlug = fnJoint.findPlug("segmentScaleCompensate", False)
            ssc = sscPlug.asBool()
        except:
            pass
            
        if ssc == False:
            # Get joint's parent
            paDagPath = aom.MDagPath(dagPath)
            try:
                paDagPath.pop()
            except RuntimeError:
                #if pop fails, then the joint is at world root.
                return local
            
            # Remove parent's scale from the local matrix
            ptrans = aom.MFnTransform(paDagPath.node())
            parentScale = ptrans.scale()  # MVector [sx, sy, sz]

            x = 1.0 / parentScale[0]
            y = 1.0 / parentScale[1]
            z = 1.0 / parentScale[2]
            mVals = [
                  x, 0.0, 0.0, 0.0,
                0.0,   y, 0.0, 0.0,
                0.0, 0.0,   z, 0.0,
                0.0, 0.0, 0.0, 1.0
            ]            
            sInv = aom.MMatrix(mVals)
            
            # Apply inverse scale
            local = local * sInv

        return local


    def processMayaJointAsCGETransform(self, x3dParentDEF, jNode, x3dSkin, x3dParent, cField="children", allShapes=[], allJoints=[], isBasic=False, wssm=aom.MMatrix()):

        bna   = self.trv.processBasicNodeAddition(x3dParent, cField, "Transform", jNode.name())
        if bna[0] == False:
            # Gather shapes related to this joint.
            self.getMeshFromJoint(jNode, allShapes)
            
            # Calculate the inverse bind matrix for this joint
            jointName = jNode.name()
            allJoints.append(jointName)

            #skinSpaceMatrix

            jList = aom.MSelectionList()
            jList.add(jointName)
            jPath = jList.getDagPath(0)
            
            localSpace = jPath.inclusiveMatrix() * jPath.exclusiveMatrix().inverse()

            ###########################################################
            # Get Local Space Transform Information
            transMatrix = aom.MTransformationMatrix(localSpace)

            # Get x3d translation value
            bna[1].translation = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))

            # Get joint rotation value
            bna[1].rotation    = self.rkint.getSFRotation(transMatrix.rotation(aom.MSpace.kTransform).asAxisAngle())

            # Get joint scale
            # Must be a positive scale as X3D scale does not accept negative numbers in this field
            chVals             = transMatrix.scale(aom.MSpace.kTransform)
            chVals[0]          = abs(chVals[0])
            chVals[1]          = abs(chVals[1])
            chVals[2]          = abs(chVals[2])
            try:
                bna[1].scale = self.rkint.getSFVec3fFromList(chVals)
            except:
                print("Scale failed in Process Basic Transform")
                
            ###############################################
            # Store joint label in a metadata node in case 
            # author does not rename this joint with the 
            # label text
            jLabel = self.getCGEJointLabel(jNode)
            bnam = self.trv.processBasicNodeAddition(bna[1], "metadata", "MetadataString", jointName + "_joint_label")
            bnam[1].name = "joint_label"
            bnam[1].value.append(jLabel)
            
            #######################################
            # Process Children of Joint Node
            #######################################
            # Count up children
            groupDag = aom.MFnDagNode(jNode.object())
            cNum = groupDag.childCount()

            # First Pass - Interate children with a priority of Joint nodes
            for i in range(cNum):
                dagChild = aom.MFnDagNode(groupDag.child(i))
                if   dagChild.typeName == "joint":
                    try:
                        self.processMayaJointAsCGETransform(bna[1].DEF, dagChild, x3dSkin, bna[1], cField="children", allShapes=allShapes, allJoints=allJoints)
                    except:
                        print("CGE Joint Export Fail!")
        else:
            print("CGE Skin is not a new node.")


    def getCGEJointMatrixList(self, jNode):
        jList = aom.MSelectionList()
        jList.add(jNode.name())
        
        jDagPath = jList.getDagPath(0)
        incMat = jDagPath.inclusiveMatrix()

        matList = []
        isJoint = True
        while isJoint is True:
            matList.append(jDagPath.exclusiveMatrix())
            jDagPath.pop()
            
            try:
                tNode = aom.MFnDependencyNode(jDagPath)
                if tNode.typeName != "joint":
                    isJoint = False
            except:
                isJoint = False
        
        return incMat, matList
        
        
    def calculateCGEJointMatrices(self, incMat, matList):#222222
        pMat = aom.MMatrix(incMat)
        mLen  = len(matList)
        jMats = []

        for i in range(mLen):
            pMat = pMat * matList[i]
        
        useMat = aom.MMatrix()
        useMat.setElement(3,0,pMat.getElement(3,0))
        useMat.setElement(3,1,pMat.getElement(3,1))
        useMat.setElement(3,2,pMat.getElement(3,2))
        
        modMat = incMat.inverse() * useMat
            
        #inv = aom.MFloatMatrix(useMat.inverse())
        inv = aom.MFloatMatrix(useMat)
        imx = (  inv[0],  inv[1],  inv[2],  inv[3],
                 inv[4],  inv[5],  inv[6],  inv[7],
                 inv[8],  inv[9], inv[10], inv[11],
                inv[12], inv[13], inv[14], inv[15])
        
        transMatrix = aom.MTransformationMatrix(useMat)
        translation = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))

        return modMat, translation, imx


    # sc is MFnSkinCluster list, wo is list of ints that are the per-mesh offset from 0 of the weights index for that mesh, sk is MFnMesh node list
    def processHAnimJoint(self, x3dParentDEF, jNode, x3dHumanoid, x3dParent, cField="children", sc=[], wo=[], sk=[], hasSC=False, jOffset=(0.0, 0.0, 0.0), wssm=aom.MMatrix()):
        skinSpaceMatrix = wssm
        bna   = self.trv.processBasicNodeAddition(  x3dParent,   cField, "HAnimJoint", jNode.name())
        bnajt = self.trv.processBasicNodeAddition(x3dHumanoid, "joints", "HAnimJoint", jNode.name())
    

        if bna[0] == False:
            #######################################
            # Process X3D Fields and set Binding 
            # Position for this Joint
            #######################################
            mlist = aom.MSelectionList()
            mlist.add(jNode.name())

            # Set the HAnimJoint "center" field based on the Maya joint's position  
            # in Skin Space using the world space inclusiveMatrix and the Skin Space Matrix inverse.
            #blm = self.getWorldPoseMatrixForJoint(jNode)

            localPivot = (0.0, 0.0, 0.0)
            tMatrix = mlist.getDagPath(0).inclusiveMatrix() * skinSpaceMatrix.inverse()
            jPath = mlist.getDagPath(0)
            blm = jPath.inclusiveMatrix() * jPath.exclusiveMatrix().inverse()#self.getJointLocalMatrix(mlist.getDagPath(0))
            
            if   x3dHumanoid.skeletalConfiguration == "BASIC":
                transMatrix   = aom.MTransformationMatrix(tMatrix)
                tPivot = self.rkint.getSFVec3f(transMatrix.translation(aom.MSpace.kTransform))
                localPivot = (tPivot[0], tPivot[1], tPivot[2])
                bna[1].center = localPivot
                self.rkBindPose[jNode.name()] = blm
            elif x3dHumanoid.skeletalConfiguration == "RAWKEE":
                bTrx = aom.MTransformationMatrix(blm)
                bna[1].translation = self.rkint.getSFVec3f(bTrx.translation(aom.MSpace.kTransform))
                bna[1].rotation    = self.rkint.getSFRotation(bTrx.rotation(aom.MSpace.kTransform).asAxisAngle())
                sv    = bTrx.scale(aom.MSpace.kTransform)
                sv[0] = abs(sv[0])
                sv[1] = abs(sv[1])
                sv[2] = abs(sv[2])
                bna[1].scale = (sv[0], sv[1], sv[2])
                
                # Set Joint Bindings
                bjTrx = aom.MTransformationMatrix(tMatrix.inverse())
                x3dHumanoid.jointBindingPositions.append(self.rkint.getSFVec3f(   bjTrx.translation(aom.MSpace.kTransform)              ))
                x3dHumanoid.jointBindingRotations.append(self.rkint.getSFRotation(bjTrx.rotation(   aom.MSpace.kTransform).asAxisAngle()))
                svj    = bjTrx.scale(aom.MSpace.kTransform)
                svj[0] = abs(svj[0])
                svj[1] = abs(svj[1])
                svj[2] = abs(svj[2])
                x3dHumanoid.jointBindingScales.append( (svj[0], svj[1], svj[2]) )

                self.rkBindPose[jNode.name()] = aom.MMatrix()
            
            
            # Get HAnimJoint "name" field
            hAnimJointName = ""
            
            sideVal = cmds.getAttr(jNode.name() + ".side")
            if x3dHumanoid.loa == -1:
                if sideVal == 0:
                    hAnimJointName += "Center_"
                elif sideVal == 1:
                    hAnimJointName += "Left_"
                elif sideVal == 2:
                    hAnimJointName += "Right_"
            elif x3dHumanoid.loa > 0:
                if sideVal == 1:
                    hAnimJointName += "l_"
                if sideVal == 2:
                    hAnimJointName += "r_"

            nType = cmds.getAttr(jNode.name() + ".type")
            if nType == 18:
                otherType = cmds.getAttr(jNode.name() + ".otherType")
                if otherType == "":
                     hAnimJointName += jNode.name()
                else:
                     hAnimJointName += otherType
            else:
                nameType = self.getJointType(str(nType))
                if nameType == "":
                     hAnimJointName += jNode.name()
                else:
                     hAnimJointName += nameType
            
            bna[1].name = hAnimJointName

            #Search for influenced Meshes
            self.getMeshFromJoint(jNode, sk)
            
            #######################################
            # Process Children of Joint Node
            #######################################

            # Count up children
            groupDag = aom.MFnDagNode(jNode.object())
            cNum = groupDag.childCount()
        
            # First Pass - Interate children with a priority of HAnimJoint nodes
            for i in range(cNum):
                dagChild = aom.MFnDagNode(groupDag.child(i))
                if   dagChild.typeName == "joint":
                    #self.processHAnimJoint(dragPath, dagChild, x3dHumanoid, bna[1], cField="children", sc=sc, wo=wo, sk=sk, hasSC=False)
                    self.processHAnimJoint(bna[1], dagChild, x3dHumanoid, bna[1], cField="children", sc=sc, wo=wo, sk=sk, hasSC=False, jOffset=localPivot, wssm=skinSpaceMatrix)
                elif dagChild.typeName == "transform":
                    mySegName = dagChild.name() + "_segment"
                    bnaSeg  = self.trv.processBasicNodeAddition(bna[1],      "children", "HAnimSegment", nodeName=mySegName)
                    bnaSeg2 = self.trv.processBasicNodeAddition(x3dHumanoid, "segments", "HAnimSegment", nodeName=mySegName)
                    
                    if bnaSeg[0] == False:
                    #    bnaSeg[1].centerOfMass = bna[1].center
                        pass
                    
                    self.traverseDownward(mySegName, dagChild)
                    x3dTransChild = self.trv.getGeneratedX3D(dagChild.name())
                    x3dTransChild.translation = bna[1].center


    def getX3DParent(self, dagNode, searchName=""):
        if searchName == "":
            sp = dagNode.getPath().fullPathName().split('|')
            spLen = len(sp)
            pName = sp[spLen-2]
            
            if spLen == 2:
                searchName = self.rootName
            else:
                searchName = pName

        x3dParent = self.trv.findExisting(searchName)
        
        if x3dParent == None:
            x3dParent = self.trv.findExisting(self.rootName)
        
        return x3dParent


    ############################################################################################
    #   Export Organizing Related Functions
    def processMayaTransformNode(self, x3dParentDEF, dagNode, cField="children"):
        isTransform = True
        x3dTypeAttr = None
        xta = ""

        try: 
            x3dTypeAttr = dagNode.findPlug("x3dNodeType", False)
            xta = x3dTypeAttr.asString()
            self.cMessage("x3dNodeType exists!")
        except:
            self.cMessage("x3dNodeType does not exist")
        
        #dragPath = dragPath + "|" + dagNode.name()

        x3dPF = []
        x3dPF.append(self.getX3DParent(dagNode, x3dParentDEF))
        x3dPF.append(cField)

        if x3dPF[0] == None:
            self.cMessage("Parent Not Found. Ignore node: " + dagNode.name())
        else:
            if x3dPF[0] != None and xta != "":
                self.cMessage("xta items")
                if xta == "Anchor":
                    isTransform = False
                    self.processX3DAnchor(   x3dParentDEF, dagNode, x3dPF)
                elif xta == "Billboard":
                    isTransform = False
                    self.processX3DBillboard(x3dParentDEF, dagNode, x3dPF)
                elif xta == "Collision":
                    isTransform = False
                    self.processX3DCollision(x3dParentDEF, dagNode, x3dPF)
                elif xta == "Group":
                    isTransform = False
                    self.processX3DGroup(    x3dParentDEF, dagNode, x3dPF)
                elif xta == "Switch":
                    isTransform = False
                    self.processX3DSwitch(   x3dParentDEF, dagNode, x3dPF)
                elif xta == "ViewpointGroup":
                    isTransform = False
                    self.processX3DViewpointGroup(x3dParentDEF, dagNode, x3dPF)
                elif xta == "MetadataSet":
                    isTransform = False
                    self.cMessage("Do nothing. MetadataSet nodes are not processed by this function.")
                
            if isTransform == True:
                ###########################################################################
                # Check this transform to see if it has a joint as a direct child. If so 
                # call a processHAnimHumanoind method to process this transform as an 
                # HAnimHumanoid node.
                ###########################################################################
                x3dType = ""

                try:
                    x3dType = cmds.getAttr(dagNode.name() + ".x3dGroupType")
                except Exception as e:
                    #print(mNode.name() + ", numInf: " + str(numInf) + ", dPaths len: " + str(len(dPaths)) + ", lWeights len: " + str(len(lWeights)))
                    #print(f"Exception Type: {type(e).__name__}")
                    #print(f"Exception Message: {e}")
                    print("Process as Transform " + dagNode.name())
                    
                if x3dType == "HAnimHumanoid":
                    if cmds.objExists("rkEPose"):
                        #cmds.currentTime(0)
                        cmds.dagPose( "rkEPose", restore=True )
                        self.bPoseStore.append("rkEPose")
                        print("RawKee Export Bind Pose WAS FOUND!")
                    else:
                        print("RawKee Export Bind Pose HAS NOT been set!")
                            
                    hhList = aom.MSelectionList()
                    hhList.add(dagNode.name())
                    dnPath = hhList.getDagPath(0)
                    self.processHAnimHumanoid(dagNode, x3dPF, skinSpaceMatrix=dnPath.exclusiveMatrix())
                else:
                    self.processTransformSorting( x3dParentDEF, dagNode, x3dPF)



    ###########################################################################################
    # Process 'transform' nodes that are the parent to leaf nodes such as cameras, lights, or
    # x3dSound nodes, and 'transform' nodes which correspond to typical X3D 'Transform' nodes.
    ###########################################################################################
    def processTransformSorting(self, x3dParentDEF, dagNode, x3dPF):
        hasLight  = False
        hasCamera = False
        hasSound  = False
        isLeaf    = False
    
        for index in range(dagNode.childCount()):
            cNode = aom.MFnDependencyNode(dagNode.child(index))
            if cNode.typeName == "camera"        and index == 0:
                hasCamera = True
                isLeaf    = True
            if cNode.typeName.find("Light") > -1 and index == 0:
                hasLight  = True
                isLeaf    = True
            if cNode.typeName == "x3dSound"      and index == 0:
                hasSound  = True
                isLeaf    = True
                
        if hasCamera  == True:
            self.processX3DViewpoint(dagNode, x3dPF) #TODO fix the problem.
        elif hasLight == True:
            self.processX3DLighting (dagNode, x3dPF)
        elif hasSound == True:
            self.processX3DSound    (dagNode, x3dPF)
        elif isLeaf   == False:
            self.processX3DTransform(x3dParentDEF, dagNode, x3dPF)


    #   Primary SceneGraph Traversal Function - Primarily Depth First
    #   pDagNode is the parent node of dagNode, which is the node about to be written.
    def traverseDownward(self, x3dParentDEF, dagNode, cField="children"):
        nodeName = dagNode.name()
        
        if self.trv.checkIfIgnored(nodeName) == False:
            
            if self.checkForRawKeeNoExportLayer(dagNode) == False:
                #Use cMessage instead of print so that we can block Verbose Export at the cMessage Level
                self.cMessage("Node was NOT ignored: " + dagNode.typeName + ", NodeName: " + nodeName)
                if dagNode.typeName == "transform":
                    self.processMayaTransformNode(x3dParentDEF, dagNode, cField)
                    
                elif dagNode.typeName == "mesh":
                    if dagNode.isIntermediateObject == True:
                        pass
                        #newDragPath, newDagNode = self.processForIntermediateMesh(dragPath, dagNode)
                        #if newDagNode != None:
                        #    self.processMayaMesh(newDragPath, newDagNode, cField)
                    else:
                        self.processMayaMesh(x3dParentDEF, dagNode, cField)
                        
                elif dagNode.typeName == "lodGroup":
                    self.processMayaLOD(x3dParentDEF, dagNode, cField)
                    
                elif dagNode.typeName == "rkAnimPack":
                    self.processSingleRKAnimPack(x3dParentDEF, dagNode, cField)
                    
                elif dagNode.typeName == "joint":
                    if cmds.objExists("rkEPose"):
                        #cmds.currentTime(0)
                        cmds.dagPose( "rkEPose", restore=True )
                        self.bPoseStore.append("rkEPose")
                        print("RawKee Export Bind Pose WAS FOUND!")
                    else:
                        print("RawKee Export Bind Pose HAS NOT been set!")

                    x3dPF = [self.getX3DParent(dagNode, x3dParentDEF), cField]
                    self.processCGESkin(dagNode, x3dPF)#, skinSpaceMatrix=ssn)
                        
            else:
                self.cMessage("Node: " + nodeName + " will not be exported as it is connected to the 'RawKeeNoExport' Maya layer")
        else:
            self.cMessage("Sorry - Node: " + nodeName + " of Type: " + dagNode.typeName + " is not yet supported for RawKee export.")
            
            

#####################################################
############    Other Functions     #################
#####################################################

    def processForIntermediateMesh(self, dragPath, dagNode):
        newDragPath = None
        newDagNode  = None
        
        iRels = cmds.listRelatives(dagNode.name(), allDescendents=True, noIntermediate=True, fullPath=True)
        meshShapes = cmds.ls(iRels, type="mesh")
        
        if meshShapes:
            selection_list = aom.MSelectionList()
            selection_list.add(meshShapes[0])
            mObj = selection_list.getDependNode(0)
            newDagNode = aom.MFnDagNode(mObj)
            newDragPath = dragPath
        
        return (newDragPath, newDagNode)
        
    
    def processMayaMesh(self, x3dParentDEF, dagNode, cField="children", cOffset=0, nOffset=0, sharedCoord="", sharedNormal="", isAvatar=False, adjustment=aom.MMatrix()):
        supMeshName = dagNode.name()
        myMesh = aom.MFnMesh(dagNode.object())
        meshCollector = {}
        
        shList1 = []
        shList2 = []
        
        shaders  = []
        groups   = []
        polygons = []
        
        shaders, meshComps = myMesh.getConnectedSetsAndMembers(0, True)

        # Check for Metadata - TODO: skipping how this is done here for the moment.
        x3dPF = []
        x3dPF.append(self.getX3DParent(dagNode, x3dParentDEF))
        x3dPF.append(cField)
        
        shLen = len(shaders)
        ##### print("Mesh Name: " + myMesh.name() + ", shLen: " + str(shLen) + ", isAvatar: " + str(isAvatar) )
        if shLen > 1 and isAvatar == False:
            bna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Group", supMeshName)
            if bna[0] == False:
                return
            else:
                bbSize = []
                bbSize.append(dagNode.findPlug("boundingBoxSizeX", False).asFloat())
                bbSize.append(dagNode.findPlug("boundingBoxSizeY", False).asFloat())
                bbSize.append(dagNode.findPlug("boundingBoxSizeZ", False).asFloat())
                
                tCenter = dagNode.findPlug("center", False)
                cen = []
                cen.append(tCenter.child(0).asFloat())
                cen.append(tCenter.child(1).asFloat())
                cen.append(tCenter.child(2).asFloat())
                
                bna[1].bboxCenter = self.rkint.getSFVec3fFromList(cen)
                bna[1].bboxSize   = self.rkint.getSFVec3fFromList(bbSize)
                
                x3dPF[0] = bna[1]
                x3dPF[1] = "children" # Because the cField might not already be "children" depending on how this function is called.
        
        ####################################################################
        # Setup Enviornmental Lighting for Legacy Materaials that have 
        # an envBall, envSphere, envCube, or envChrome node. Or if a modern
        # PBR material is affected by a non-global aiSkyDomeLight
        envLightingGroups = {}
        for idx in range(shLen):
            seNode = aom.MFnDependencyNode(shaders[idx])
            stray = cmds.listConnections(seNode.name() + ".surfaceShader", t="StingrayPBS")
            if stray:
                rList = aom.MSelectionList()
                rList.add(stray[0])
                nodeEnv["name"] = stray[0]
                nodeEnv["node"] = aom.MFnDependencyNode(rList.getDependNode(0))
                envLightingGroups[str(idx)] = nodeEnv
            else:
                aiSDL = cmds.ls(type="aiSkyDomeLight")
                if aiSDL:
                    for lName in aiSDL:
                        isLinked = False
                        #isLinked = cmds.lightlink(query=True, light=lName, object=seNode.name())
                        linkedLights = cmds.lightlink(query=True, object=seNode.name()) or []
                        for ll in linkedLights:
                            if ll == lName:
                                isLinked = True
                                break
                        if isLinked == True:
                            isIDefault = False
                            descendants = cmds.listRelatives(lName, allDescendents=True) or []
                            for item in descendants:
                                if lName == item:
                                    isIDefault = True
                                    break
                            
                            if isIDefault == True:
                                lList = aom.MSelectionList()
                                lList.add(lName)
                                nodeEnv = {}
                                nodeEnv["name"] = lName
                                nodeEnv["node"] = aom.MFnDependencyNode(lList.getDependNode(0))
                                envLightingGroups[str(idx)] = nodeEnv
                                break
                else:
                    ssNode = aom.MFnDependencyNode(seNode.findPlug("surfaceShader", True).source().node())
                    if ssNode.typeName == "blinn":
                        nodeEnv = {}
                        
                        envIter = aom.MItDependencyGraph(ssNode, rkfn.kInvalid, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
                        
                        while not envIter.isDone():
                            envCheck = aom.MFnDependencyNode(envIter.currentNode())
                            if envCheck.typeName == "envBall" or envCheck.typeName == "envSphere" or envCheck.typeName == "envCube" or envCheck.typeName == "envChrome":
                                nodeEnv["name"] = envCheck.name()
                                nodeEnv["node"] = envCheck
                                envLightingGroups[str(idx)] = nodeEnv
                                break
                                
                            textIter.next()

        for idx in range(shLen):
            shapeName = supMeshName
            lightName = supMeshName + "_LGroup"
            if shLen > 1:
                shapeName = shapeName + "_SubShape_" + str(idx)
                lightName = lightName + "_SubShape_" + str(idx)
                
                # Apply non-global environmental lighting to this shape if it exists.
                if cField != "shapes":
                    envNode = envLightingGroups.get(str(idx), False)
                    if envNode:
                        envBna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Group", lightName)
                        if envBna[0] == False:
                            x3dPF[0] = lightName
                            x3dPF[1] = "children"

                            if cmds.nodeType(envNode["name"]) == "aiSkyDomeLight":
                                lList = aom.MSelectionList()
                                lList.add(envNode["name"])
                                sdLight = aom.MFnDependencyNode(lList.getDependNode(0))
                                self.processEnviornmentLight(sdLight, x3dPF[0], x3dPF[1], "EnvironmentLight", envNode["name"])
                            else:
                                eNode = envNode["node"]
                                lightName = envNode["name"]
                                if eNode.typeName == "StingrayPBS":
                                    lightName = lightName + "_SPBS_EnvLight"
                                lhtBna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "EnvironmentLight", lightName)
                                if lhtBna[0] == False:
                                    lhtBna[1].on = True
                                    lhtBna[1].global_ = False
                                    if eNode.typeName == "StingrayPBS":
                                        self.processNodeAsEnviornmentLight(eNode, "TEX_global_diffuse_cube",  lhtBna[1], "diffuseTexture")
                                        self.processNodeAsEnviornmentLight(eNode, "TEX_global_specular_cube", lhtBna[1], "specularTexture")
                                    elif eNode.typeName == "envBall" or eNode.typeName == "envSphere":
                                        self.processNodeAsEnviornmentLight(eNode, "image", lhtBna[1], "specularTexture")
                                    elif eNode.typeName == "envChrome":
                                        #TODO
                                        pass
                
            sbna = self.trv.processBasicNodeAddition(x3dPF[0], x3dPF[1], "Shape", shapeName)
            if sbna[0] == False:
                
                #if shLen == 1:
                #    cgeShape = sbna[1]
                
                # meshCollector is a dict {}, it associates the CGE Skin shape with the appropriate Maya mesh
                # The only time it is not None is if is evoked during the execution of processCGESkin
                meshCollector[shapeName] = myMesh
                    
                # Yeah, this is sloppy, I'm using the bounding Box info for the while DAG Node over and over again. 
                # The Group node holding all this geometry together and all of the children nodes each have the same
                # bounding box info.
                #
                # I suppose someone who feels the need to change this can probaby figure out the bounding box info 
                # for each Shape node from the Maya mesh node data. TODO
                bbSize = []
                bbSize.append(dagNode.findPlug("boundingBoxSizeX", False).asFloat())
                bbSize.append(dagNode.findPlug("boundingBoxSizeY", False).asFloat())
                bbSize.append(dagNode.findPlug("boundingBoxSizeZ", False).asFloat())
                
                tCenter = dagNode.findPlug("center", False)
                cen = []
                cen.append(tCenter.child(0).asFloat())
                cen.append(tCenter.child(1).asFloat())
                cen.append(tCenter.child(2).asFloat())
                
                sbna[1].bboxCenter = self.rkint.getSFVec3fFromList(cen)
                sbna[1].bboxSize   = self.rkint.getSFVec3fFromList(bbSize)
                
#                if self.exEncoding == "html":
#                    self.processForAppearanceHTML(myMesh, shaders[idx], meshComps[idx], sbna[1], cField="appearance", index=idx)
#                else:
#                    self.processForAppearance(myMesh, shaders[idx], meshComps[idx], sbna[1], cField="appearance", index=idx)
                x3dApp = self.processX3DAppearance(myMesh, shaders[idx], meshComps[idx], sbna[1], cField="appearance", index=idx)
#                self.processForAppearance(myMesh, shaders[idx], meshComps[idx], sbna[1], cField="appearance", index=idx)
                
                if cField == "shapes":
                    self.processForGeometry(  myMesh, x3dApp, shaders, meshComps, sbna[1], nodeName=shapeName, cField="geometry", nodeType="CGEIndexedFaceSet", index=idx, gcOffset=cOffset, gnOffset=nOffset, gsharedCoord=sharedCoord, gsharedNormal=sharedNormal, isAvatar=isAvatar, adjMatrix=adjustment)
                else:
                    self.processForGeometry(  myMesh, x3dApp, shaders, meshComps, sbna[1], nodeName=shapeName, cField="geometry", nodeType="IndexedFaceSet", index=idx, gcOffset=cOffset, gnOffset=nOffset, gsharedCoord=sharedCoord, gsharedNormal=sharedNormal, isAvatar=isAvatar, adjMatrix=adjustment)
            else:
                print("Returned a None for: " + myMesh.name() + ", DEF-USE: " + shapeName + ", was USE - 1")

        return meshCollector


    def processX3DOMAppearance(self):
        pass

    def processX3DAppearance(self, mesh, seObj, comp, pNode, cField="appearance", index=0):
        #uvSetNames = mesh.getUVSetNames()
        matchedSets = self.getUsedUVSetDictionary(mesh, seObj)
        
        # Texture Transform List
        ttList = []
        
        # Get the Dependency Node for the Shading Engine
        seNode = aom.MFnDependencyNode(seObj)
        
        #Create the Appearance Node using the Name of the Shader Engine
        bna = self.trv.processBasicNodeAddition(pNode, cField, "Appearance", seNode.name())
        if bna[0] == False:
            mTextureNodes        = []
            mTextureFields       = []
            mTextureParents      = []
            retPlace2d           = []
            
            #try:
            ssNode = aom.MFnDependencyNode(seNode.findPlug("surfaceShader", True).source().node())
        
            # Check to see if surfaceShader is Double Sided, and then process appropriately
            if ssNode.typeName == "aiTwoSided":
                #self.processDoubleSidedAppearance(matchedSets, ssNode, bna[1], mappings, mTextureNodes, mTextureFields, mTextureParents, retPlace2d)
                self.processDoubleSidedAppearance(matchedSets, ssNode, bna[1], mTextureNodes, mTextureFields, mTextureParents, retPlace2d)
            else:
                #self.processSingleSidedAppearance(matchedSets, ssNode, bna[1], mappings, mTextureNodes, mTextureFields, mTextureParents, retPlace2d)
                self.processSingleSidedAppearance(matchedSets, ssNode, bna[1], mTextureNodes, mTextureFields, mTextureParents, retPlace2d)
            #except:
            #    print("Failure at inital SurfaceShader search")
            
                            
        print("Made it to the end of the appearance.")
        
        return bna[1]
                
    
    def processDoubleSidedAppearance(self, matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d):
        sShaders = []
        sShaders.append(aom.MFnDependencyNode(mayaShader.findPlug("front", True).source().node()))
        sShaders.append(aom.MFnDependencyNode(mayaShader.findPlug("back", True).source().node()))
            
        #try:
        self.processSingleSidedAppearance(matchedSets, sShaders[0], x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d)
        #except:
        #    print("Failure at search for front side of a double sided appearance node")
            
        #try:
        self.processSingleSidedAppearance(matchedSets, sShaders[1], x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField="backMaterial")
        #except:
        #    print("Failure at search for back side of a double sided appearance node")

        
    def processSingleSidedAppearance(self, matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField="material"):
        print("Inside Single Sided Appearance.")
        
        x3dMaterial = None

        if mayaShader.typeName == "MaterialXSurfaceShader":
            matXType = mayaShader.name() + ".asX3DShader"
            if cmds.objExists(matXType):
                asX3DShader = cmds.getAttr(matXType)
                if asX3DShader == True:
                    x3dMaterial = self.processMaterialX_X3DShaderSet(   mayaShader, x3dAppearance, matchedSets, "shaders")
                else:
                    x3dMaterial = self.processMaterialX_X3DMaterialType(mayaShader, x3dAppearance, matchedSets, cField   )
            else:
                x3dMaterial = self.processMaterialX_X3DMaterialType(mayaShader, x3dAppearance, matchedSets, cField   )
                #x3dMaterial  = self.processMaterialX_X3DShaderSet(   mayaShader, x3dAppearance, matchedSets, "shaders")
            
        elif mayaShader.typeName == "aiFlat" or mayaShader.typeName == "surfaceShader":
            x3dMaterial = self.processUnlit_Material(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)
        
        elif mayaShader.typeName == "StingrayPBS":
            x3dMaterial = self.processStingrayPBS_PhysicalMaterial(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)

        elif mayaShader.typeName == "aiStandardSurface" or mayaShader.typeName == "standardSurface":
            x3dMaterial = self.processStandard_PhysicalMaterial(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)

        elif mayaShader.typeName == "openPBRSurface":
            x3dMaterial = self.processOpenPBRSurface(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)
        
        elif mayaShader.typeName == "usdPreviewSurface":
            x3dMaterial = self.processUSDPreview_PhysicalMaterial(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)

        elif mayaShader.typeName == "blinn":
            x3dMaterial = self.processBlinn_PhysicalMaterial(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)

        elif mayaShader.typeName == "lambert" or mayaShader.typeName == "aiLambert" or mayaShader.typeName == "phong" or mayaShader.typeName == "phongE":
            x3dMaterial = self.processLegacy_Material(matchedSets, mayaShader, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField)

        else:
            print("###############################################################################")
            print("# The " + mayaShader.name() + " material is not supported")
            print("###############################################################################\n")


    def processLegacy_Material(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        mNode = self.trv.processBasicNodeAddition(x3dAppearance, cField, "Material", material.name())
        if mNode[0] == False:
            x3dMat = mNode[1]

            ignoreTT          = False
            textureTransforms = []
            
            colorStore = {}

            rkMat.getLegacyBaseColorAndOcclusionTextures(material, colorStore)

            # Get BaseTexture
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, x3dMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)
            else:
                try:
                    bc = cmds.getAttr(material.name() + ".color")[0]
                    x3dMat.diffuseColor = self.getSFColor(bc[0], bc[1], bc[2])
                except:
                    bc = cmds.getAttr(material.name() + ".KdColor")[0]
                    x3dMat.diffuseColor = self.getSFColor(bc[0], bc[1], bc[2])
                    
            #######################################################
            # Get AmbientTexture and AmbientIntensity
            ambientIntensity = 1.0
            if material.typeName != "aiLambert":
                ambiConn = material.findPlug("ambientColor", True)
                ambiTexture = self.findTextureFromPlug(ambiConn)
                if ambiTexture:
                    ignoreTT = self.processTexture(ambiTexture, x3dAppearance, x3dMat, "ambientTexture", matchedSets, textureTransforms, ignoreTT)
                else:
                    ac = cmds.getAttr(material.name() + ".ambientColor")[0]
                    ambientIntensity = (ac[0] + ac[1] + ac[2]) / 3
            else:
                ambientIntensity = cmds.getAttr(material.name() + ".Kd")
            x3dMat.ambientIntesity = ambientIntensity
            
            #######################################################
            # Get EmissiveTexture and EmissiveColor
            if material.typeName != "aiLambert":
                emiConn = material.findPlug("incandescence")
                emiTexture = self.findTextureFromPlug(emiConn)
                if emiTexture:
                    ignoreTT = self.processTexture(emiTexture, x3dAppearance, x3dMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                    x3dMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
                else:
                    eColor = cmds.getAttr(material.name() + ".incadescence")[0]
                    x3dMat.emissiveColor = self.getSFColor(eColor[0], eColor[1], eColor[2])
            
            #######################################################
            # Get Transparency
            try:
                op = cmds.getAttr(material.name() + ".opacity")[0]
                x3dMat.transparency = 1 - ((op[0] + op[1] + op[2]) / 3)
            except:
                transp = cmds.getAttr(material.name() + ".transparency")[0]
                x3dMat.transparency = (t[0] + t[1] + t[2]) / 3

            ######################################################
            # Get Normal Map
            normConn    = material.findPlug("normalCamera", True)
            normTexture = self.findTextureFromPlug(normConn)
            if normTexture:
                ignoreTT = self.processTexture(normTexture, x3dAppearance, x3dMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)
            
            normAdj = self.findNormScaleNode(normConn)
            if normAdj:
                if normAdj.typeName == "aiNormalMap":
                    x3dMat.normalScale = cmds.getAttr(normAdj.name() + ".strength")
                    
                elif normAdj.typeName == "bump2d":
                    nsValue = cmds.getAttr(normAdj.name() + ".bumpDepth")
                    if nsValue < 0.01:
                        nsValue = 0.01
                    x3dMat.normalScale = nsValue

            #########################################################
            # Get Occlusion Texture
            occlTexture = colorStore.get("occlusionTexture", False)
            if occlTexture:
                ignoreTT = self.processTexture(occlTexture, x3dAppearance, x3dMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT)

            if material.typeName == "phong" and material.typeName == "phongE":
                #######################################################
                # Get shininess and shininessTexture values
                shineAttr = "cosinePower"
                if material.typeName == "phongE":
                    shineAttr = "roughness"
                shiConn = material.findPlug(shineAttr)
                shiTexture = self.findTextureFromPlug(shiConn)
                if shiTexture:
                    ignoreTT = self.processTexture(shiTexture, x3dAppearance, x3dMat, "shininessTexture", matchedSets, textureTransforms, ignoreTT)
                    x3dMat.shininess = 1.0
                else:
                    x3dMat.shininess = cmds.getAttr(material.name() + "." + shineAttr)

                #######################################################
                # Get specularColor and specularTexture values
                spcConn = material.findPlug("specularColor", True)
                spcTexture = self.findTextureFromPlug(spcConn)
                if spcTexture:
                    ignoreTT = self.processTexture(spcTexture, x3dAppearance, x3dMat, "specularTexture", matchedSets, textureTransforms, ignoreTT)
                else:
                    spc = cmds.getAttr(material.name() + ".specularColor")[0]
                    x3dMat.specularColor = self.getSFColor(spc[0], spc[1], spc[2])
            
                if cmds.objExists(material.name() + ".reflectedColor"):
                    reflConn = material.findPlug("reflectedColor", True)
                    reflTexture = self.findTextureFromPlug(reflConn)
                    
                    if reflTexture.typeName == "envChrome" or reflTexture.typeName == "envCube" or reflTexture.typeName == "envBall" or reflTexture.typeName == "envSphere":
                        refBna = self.trv.processBasicNodeAddition(x3dAppearance, "texture", "GeneratedCubeMapTexture", reflTexture.name())
                        ignoreTT = True

                # Check for GeneratedCubeMapTexture
                if ignoreTT == True:
                    x3dAppearance.material = None
                else:
                    rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    def processMaterialX_X3DMaterialType(self, matXSS, x3dAppearance, matchedSets, cField):
        isX3DOM = False
        if self.exEncoding == "html":
            isX3DOM = True

        textureTransforms = []
        ignoreTT = False

        surfacePath = cmds.getAttr(matXSS.name() + ".ufePath")
        smSceneItem = rkMat.getMatXSurfaceMaterialSceneItem(surfacePath)
        shSceneItem = rkMat.getMatXSurfaceShaderSceneItem(  smSceneItem, surfacePath)
        
        shaderType = shSceneItem.nodeType()
        if   shaderType == "ND_gltf_pbr_surfaceshader":
            self.processMatX_gltf_pbr(    matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "ND_open_pbr_surface_surfaceshader":
            self.processMatX_open_pbr(    matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "ND_standard_surface_surfaceshader":
            self.processMatX_stnd_pbr(    matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "ND_UsdPreviewSurface_surfaceshader":
            self.processMatX_usd_preview_pbr(    matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "MayaND_phong_surfaceshader":
            self.processMatX_maya_phong(  matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "MayaND_blinn_surfaceshader":
            self.processMatX_maya_blinn(  matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "MayaND_lambert_surfaceshader":
            self.processMatX_maya_lambert(matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        elif shaderType == "ARNOLD_ND_lambert":
            self.processMatX_ai_lambert(matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)

        # Check for GeneratedCubeMapTexture
        if ignoreTT == True:
            x3dAppearance.material = None
        else:
            rkMat.attachMatXTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    def processMatX_usd_preview_pbr(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        # Collect basic PhysicalMaterial node information
        attributes = {}
        
        # baseColor / baseTexture
        #baseColorAttrText = rkMat.getUFEAttribute(shSceneItem, "baseColor", connected=True)
        baseColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "diffuseColor")
        if baseColorTexture:
            attributes["baseTexture"] = baseColorTexture
        else:
            baseColorAttr = rkMat.getMatXAttribute(shSceneItem, "diffuseColor")
            bcv = baseColorAttr.get()
            attributes["baseColor"] = self.getSFColor(bcv.r(), bcv.g(), bcv.b())
            
        # emissiveColor / emissiveTexture
        emissiveColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "emissiveColor")
        if emissiveColorTexture:
            attributes["emissiveTexture"] = emissiveColorTexture
        else:
            emissiveColorAttr = rkMat.getMatXAttribute(shSceneItem, "emissiveColor")
            ecv = emissiveColorAttr.get()
            attributes["emissiveColor"] = self.getSFColor(ecv.r(), ecv.g(), ecv.b())
            
        spcWork = rkMat.getMatXAttribute(shSceneItem, "useSpecularWorkflow").get()
        
        metallicTexture = None

        if spcWork == 0:
            # metallic / metallicRoughnessTexture
            metallicTexture = rkMat.getUFEConnectedTexture(shSceneItem, "metallic")
            if not metallicTexture:
                attributes["metallic"] = rkMat.getMatXAttribute(shSceneItem, "metallic").get()
        else:
            attributes["metallic"] = 0.0
        
        roughnessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "roughness")
        if not roughnessTexture:
            attributes["roughness"] = rkMat.getMatXAttribute(shSceneItem, "roughness").get()
            
        if metallicTexture:
            attributes["metallicRoughnessTexture"] = metallicTexture
        elif roughnessTexture:
            attributes["metallicRoughnessTexture"] = roughnessTexture
        
        # Get occlusionStrength / occlusionTexture
        occlusionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "occlusion")
        if occlusionTexture:
            attributes["occlusionTexture"] = occlusionTexture
        else:
            attributes["occlusionStrength"] = rkMat.getMatXAttribute(shSceneItem, "occlusion").get()
        
        # Get normalStrength / normalTexture
        normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normal", connected=True)
        if normalScaleAttr:
            scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
            scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
            if not scaleAttr:
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
            if scaleAttr:
                attributes["normalScale"] = scaleAttr.get()
                
            normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
            if normalTexture:
                attributes["normalTexture"] = normalTexture

        if spcWork == 1:
        # Get basic specular information
            specularColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specularColor")
            if specularColorTexture:
                attributes["specularColorTexture"] = specularColorTexture
                try:
                    iPath = rkMat.getMatXAttribute(specularColorTexture, "file", grasp=True)
                    img = aom.MImage()
                    img.readFromFile(iPath)
                    if img.depth() == 4:
                        attributes["specularTexture"] = specularColorTexture
                except:
                    pass
            else:
                specularColorAttr = rkMat.getMatXAttribute(shSceneItem, "specularColor")
                spc = specularColorAttr.get()
                attributes["specularColor"] = self.getSFColor(spc.r(), spc.g(), spc.b())
                
            attributes["specularWeight"] = 1.0

        # Alpha Information
        trspAttr = rkMat.getMatXAttribute(shSceneItem, "opacity")
        attributes["transparency"] = 1 - trspAttr.get()
        attributes["alphaCutoff" ] = rkMat.getMatXAttribute(shSceneItem, "opacityThreshold")
        
        # Populate the PhysicalMaterial fields with values.
        if isX3DOM:
            # For X3DOM
            attributes["diffuseColor"] = (1.0, 1.0, 1.0)
            attributes["shininess"   ] = 0.0
            #self.setMatX_PhysicalMaterialX3DOM(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialX3DOM(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        else:
            ###################################################################################
            ###################################################################################
            # Collect Up PhysicalMaterial X_ITE Material Extensions for PhysicalMaterialEXT
            #
            #Clearcoat Material
            ccTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat")
            if ccTexture:
                attributes["clearcoatTexture"] = ccTexture
                attributes["clearcoat"] = 1.0
            else:
                attributes["clearcoat"] = rkMat.getMatXAttribute(shSceneItem, "clearcoat").get()
            
            ccrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoatRoughness")
            if ccrTexture:
                attributes["clearcoatRoughnessTexture"] = ccrTexture
                attributes["clearcoatRoughness"] = 1.0
            else:
                attributes["clearcoatRoughness"] = rkMat.getMatXAttribute(shSceneItem, "clearcoatRoughness").get()
            
            attributes["indexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "ior").get()
            
            # For X_ITE and CGE
            #self.setMatX_PhysicalMaterialEXT(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialEXT(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def processMatX_gltf_pbr(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        # Collect basic PhysicalMaterial node information
        attributes = {}
        
        # baseColor / baseTexture
        #baseColorAttrText = rkMat.getUFEAttribute(shSceneItem, "baseColor", connected=True)
        baseColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base_color")
        if baseColorTexture:
            attributes["baseTexture"] = baseColorTexture
        else:
            baseColorAttr = rkMat.getMatXAttribute(shSceneItem, "base_color")
            bcv = baseColorAttr.get()
            attributes["baseColor"] = self.getSFColor(bcv.r(), bcv.g(), bcv.b())
        
        # emissiveColor / emissiveTexture
        #emissiveColorAttrText = rkMat.getUFEAttribute(shSceneItem, "emissive", connected=True)
        emissiveColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "emissive")
        if emissiveColorTexture:
            attributes["emissiveTexture"] = emissiveColorTexture
        else:
            emissiveColorAttr = rkMat.getMatXAttribute(shSceneItem, "emissive")
            ecv = emissiveColorAttr.get()
            attributes["emissiveColor"] = self.getSFColor(ecv.r(), ecv.g(), ecv.b())
            
        # metallic / metallicRoughnessTexture
        #metallicAttrTexture = rkMat.getUFEAttribute(shSceneItem, "metallic", connected=True)
        metallicTexture = rkMat.getUFEConnectedTexture(shSceneItem, "metallic")
        
        if not metallicTexture:
            attributes["metallic"] = rkMat.getMatXAttribute(shSceneItem, "metallic").get()
        
        roughnessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "roughness")
        if not roughnessTexture:
            attributes["roughness"] = rkMat.getMatXAttribute(shSceneItem, "roughness").get()
            
        if metallicTexture:
            attributes["metallicRoughnessTexture"] = metallicTexture
        elif roughnessTexture:
            attributes["metallicRoughnessTexture"] = roughnessTexture
        
        # Get occlusionStrength / occlusionTexture
        occlusionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "occlusion")
        if occlusionTexture:
            attributes["occlusionTexture"] = occlusionTexture
        else:
            attributes["occlusionStrength"] = rkMat.getMatXAttribute(shSceneItem, "occlusion").get()
        
        # Get normalStrength / normalTexture
        normalConnection = rkMat.getUFEAttribute(shSceneItem, "normal", connected=True)
        if normalConnection:
            scaleItem = ufe.Hierarchy.createItem(normalConnection.src.path)
            scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
            if not scaleAttr:
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
                
            if scaleAttr:
                attributes["normalScale"] = scaleAttr.get()
                
            normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
                
            if normalTexture:
                attributes["normalTexture"] = normalTexture

        # Get basic specular information
        specularColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specular_color")
        if specularColorTexture:
            attributes["specularColorTexture"] = specularColorTexture
            try:
                iPath = rkMat.getMatXAttribute(specularColorTexture, "file", grasp=True)
                img = aom.MImage()
                img.readFromFile(iPath)
                if img.depth() == 4:
                    attributes["specularTexture"] = specularColorTexture
            except:
                pass
        else:
            specularColorAttr = rkMat.getMatXAttribute(shSceneItem, "specular_color")
            spc = specularColorAttr.get()
            attributes["specularColor"] = self.getSFColor(spc.r(), spc.g(), spc.b())
            
        specularWeightAttr = rkMat.getMatXAttribute(shSceneItem, "specular")
        attributes["specularWeight"] = specularWeightAttr.get()

        # Alpha Information
        trspAttr = rkMat.getMatXAttribute(shSceneItem, "alpha")
        attributes["transparency"] = 1 - trspAttr.get()
        attributes["alphaCutoff"] = rkMat.getMatXAttribute(shSceneItem, "alpha_cutoff").get()
        attributes["alphaMode"]   = rkMat.getMatXAttribute(shSceneItem, "alpha_mode").get()
        
        # Populate the PhysicalMaterial fields with values.
        if isX3DOM:
            print("X3DOM Version")
            print(isX3DOM)
            # For X3DOM
            #self.setMatX_PhysicalMaterialX3DOM(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialX3DOM(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        else:
            ###################################################################################
            ###################################################################################
            # Collect Up PhysicalMaterial X_ITE Material Extensions for PhysicalMaterialEXT
            #
            print("X3D Standard")
            print(isX3DOM)
            attributes["emissiveStrength"] =  rkMat.getMatXAttribute(shSceneItem, "emissive_strength").get()
            
            transmissionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "transmission")
            if transmissionTexture:
                attributes["transmissionTexture"] = transmissionTexture
                attributes["transmission"]        = 1.0
            else:
                attributes["transmission"] = rkMat.getMatXAttribute(shSceneItem, "transmission").get()
            
            # Volumetric Matrial
            thicknessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "thickness")
            if thicknessTexture:
                attributes["thicknessTexture"] = thicknessTexture
                attributes["thickness"]        = 1.0
            else:
                thk = rkMat.getMatXAttribute(shSceneItem, "thickness").get()
                if thk > 0.0:
                    attributes["thickness"] = thk
                    
            thkVal = attributes.get("thickness", 0.0)
            if thkVal > 0.0:
                attributes["attenuationDistance"] = rkMat.getMatXAttribute(shSceneItem, "attenuation_distance").get()
                atCol = rkMat.getMatXAttribute(shSceneItem, "attenuation_color").get()
                attributes["attenuationColor"] = self.getSFColor(atCol.r(), atCol.g(), atCol.b())

            #Clearcoat Material
            ccTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat")
            if ccTexture:
                attributes["clearcoatTexture"] = ccTexture
                attributes["clearcoat"] = 1.0
            else:
                ccVal = rkMat.getMatXAttribute(shSceneItem, "clearcoat").get()
                if ccVal > 0.0:
                    attributes["clearcoat"] = ccVal
            
            ccrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat_roughness")
            if ccrTexture:
                attributes["clearcoatRoughnessTexture"] = ccrTexture
                attributes["clearcoatRoughness"] = 1.0
            else:
                ccrVal = rkMat.getMatXAttribute(shSceneItem, "clearcoat_roughness").get()
                if ccrVal > 0.0:
                    attributes["clearcoatRoughness"] = ccrVal
            
            ccnTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat_normal")
            if ccnTexture:
                attributes["clearcoatNormalTexture"] = ccnTexture

            attributes["indexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "ior").get()

            shnrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "sheen_roughness")
            if shnrTexture:
                attributes["sheenRoughnessTexture"] = shnrTexture
                attributes["sheenRoughness"] = 1.0
            else:
                shnrVal = rkMat.getMatXAttribute(shSceneItem, "sheen_roughness").get()
                if shnrVal > 0.0:
                    attributes["sheenRoughness"] = shnrVal
            
            shncTexture = rkMat.getUFEConnectedTexture(shSceneItem, "sheen_color")
            if shncTexture:
                attributes["sheenColorTexture"] = shncTexture
                attributes["sheenColor"] = (1.0, 1.0, 1.0)
            else:
                shncVal = rkMat.getMatXAttribute(shSceneItem, "sheen_color").get()
                attributes["sheenColor"] = self.getSFColor(shncVal.r(), shncVal.g(), shncVal.b())
            
            iridTexture = rkMat.getUFEConnectedTexture(shSceneItem, "iridescence")
            if iridTexture:
                attributes["iridescenceTexture"] = iridTexture
                attributes["iridescence"] = 1.0
            else:
                iridVal = rkMat.getMatXAttribute(shSceneItem, "iridescence").get()
                if iridVal > 0.0:
                    attributes["iridescence"] = shnrVal
            
            attributes["iridescenceIndexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "iridescence_ior").get()

            irthTexture = rkMat.getUFEConnectedTexture(shSceneItem, "iridescence_thickness")
            if irthTexture:
                attributes["iridescenceThicknessTexture"] = irthTexture
                attributes["iridescenceThicknessMinimum"] = 100
                attributes["iridescenceThicknessMaximum"] = 400
            else:
                ikValue = rkMat.getMatXAttribute(shSceneItem, "iridescence_thickness").get()
                attributes["iridescenceThicknessMinimum"] = ikValue
                attributes["iridescenceThicknessMaximum"] = ikValue
            
            # For X_ITE and CGE
            #self.setMatX_PhysicalMaterialEXT(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            print("JB4 MatX PM EXT")
            self.setMatX_PhysicalMaterialEXT(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def processMatX_open_pbr(    self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        # Collect basic PhysicalMaterial node information
        attributes = {}
        
        # baseColor / baseTexture
        baseColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base_color")
        if baseColorTexture:
            attributes["baseTexture"] = baseColorTexture
        else:
            baseColorAttr = rkMat.getMatXAttribute(shSceneItem, "base_color")
            bcv = baseColorAttr.get()
            attributes["baseColor"] = self.getSFColor(bcv.r(), bcv.g(), bcv.b())
        
        metalTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base_metalness")
        if metalTexture:
            attributes["metallic"] = 1.0
        else:
            attributes["metallic"] = rkMat.getMatXAttribute(shSceneItem, "base_metalness").get()
            
        roughTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specular_roughness")
        if roughTexture:
            attributes["roughness"] = 1.0
        else:
            attributes["roughness"] = rkMat.getMatXAttribute(shSceneItem, "specular_roughness").get()
        
        if metalTexture:
            attributes["metallicRoughnessTexture"] = metalTexture
        elif roughTexture:
            attributes["metallicRoughnessTexture"] = roughTexture
            
        occlusionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base_weight")
        if occlusionTexture:
            attributes["occlusionTexture"]  = occlusionTexture
            attributes["occlusionStrength"] = 1.0
        else:
            attributes["occlusionStrength"] = rkMat.getMatXAttribute(shSceneItem, "base_weight").get()
            occlusionTexture2 = rkMat.getUFEConnectedTexture(shSceneItem, "specular_weight")
            if occlusionTexture2:
                attributes["occlusionTexture"]  = occlusionTexture2
        
        if not occlusionTexture2:
            attributes["specularWeight"] = rkMat.getMatXAttribute(shSceneItem, "specular_weight").get()
                
        emissiveColorTexture =  rkMat.getUFEConnectedTexture(shSceneItem, "emission_color")
        if emissiveColorTexture:
            attributes["emissiveTexture"] = emissiveColorTexture
            attributes["emissiveColor"]   = (1.0, 1.0, 1.0)
        
        # Get normalStrength / normalTexture
        normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "geometry_normal", connected=True)
        if normalScaleAttr:
            scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
            scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
            if not scaleAttr:
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
            if scaleAttr:
                attributes["normalScale"] = scaleAttr.get()
                
            normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
            if normalTexture:
                attributes["normalTexture"] = normalTexture

        # Get basic specular information
        specularColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specular_color")
        if specularColorTexture:
            attributes["specularColorTexture"] = specularColorTexture
            try:
                iPath = rkMat.getMatXAttribute(specularColorTexture, "file", grasp=True)
                img = aom.MImage()
                img.readFromFile(iPath)
                if img.depth() == 4:
                    attributes["specularTexture"] = specularColorTexture
            except:
                pass
        else:
            specularColorAttr = rkMat.getMatXAttribute(shSceneItem, "specular_color")
            spc = specularColorAttr.get()
            attributes["specularColor"] = self.getSFColor(spc.r(), spc.g(), spc.b())
            
        trspAttr = rkMat.getMatXAttribute(shSceneItem, "geometry_opacity")
        attributes["transparency"] = 1 - trspAttr.get()

        if isX3DOM:
            # For X3DOM
            #self.setMatX_PhysicalMaterialX3DOM(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialX3DOM(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        else:
            ###################################################################################
            ###################################################################################
            # Collect Up PhysicalMaterial X_ITE Material Extensions for PhysicalMaterialEXT
            #
 
            attributes["emissiveStrength"] =  rkMat.getMatXAttribute(shSceneItem, "emission_luminance").get()
            
            tWeight = rkMat.getMatXAttribute(shSceneItem, "transmission_weight" ).get()
            sWeight = rkMat.getMatXAttribute(shSceneItem, "subsurface_weight"   ).get()
            isTWall = rkMat.getMatXAttribute(shSceneItem, "geometry_thin_walled").get()
            
            if tWeight != 0.0:
                attributes["transparency"] = 0.0
                attributes["transmission"] = tWeight

                transmissionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "transmission_color")
                if transmissionTexture:
                    attributes["transmissionTexture"] = transmissionTexture
                    attributes["diffuseTransmissionColor"] = (1.0, 1.0, 1.0)
                else:
                    trCol = rkMat.getMatXAttribute(shSceneItem, "transmission_color").get()
                    attributes["diffuseTransmissionColor"] = self.getSFColor(trCol.r(), trCol.g(), trCol.b())
            if isTWall == True:
                attributes["diffuseTransmission"] = sWeight
                diffuseTransmissionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "subsurface_color")
                if diffuseTransmissionTexture:
                    attributes["diffuseTransmissionTexture"] = diffuseTransmissionTexture
                else:
                    dtc  = attributes.get("diffuseTransmissionColor", (1.0, 1.0, 1.0))
                    dtc2 = rkMat.getMatXAttribute(shSceneItem, "subsurface_color").get()
                    attributes["diffuseTransmissionColor"] = (dtc[0] * dtc2.r(), dtc[1] * dtc2.g(), dtc[2] * dtc2.b())
            else:
            
                # Volumetric Material
                myThickness = 1.0
                thicknessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "transmission_depth")
                if thicknessTexture:
                    attributes["thicknessTexture"] = thicknessTexture
                else:
                    myThickness = rkMat.getMatXAttribute(shSceneItem, "transmission_depth").get()

                vmThickness = tWeight ## More like water
                if sWeight > tWeight:
                    vmThickness = sWeight ## More like skin/wax
                    
                attributes["thickness"] = vmThickness * myThickness
                
                ac  = rkMat.getMatXAttribute(shSceneItem, "subsurface_radius_scale").get()
                bc  = attributes.get("diffuseTransmissionColor", (1.0, 1.0, 1.0))
                bcc = attributes.get("baseColor", (1.0, 1.0, 1.0))
                
                attributes["baseColor"] = self.getSFColor( (bcc[0] * (1.0 - sWeight)) + (bc[0] * sWeight), (bcc[1] * (1.0 - sWeight)) + (bc[1] * sWeight), (bcc[2] * (1.0 - sWeight)) + (bc[2] * sWeight) )

                attributes["attenuationDistance"] = rkMat.getMatXAttribute(shSceneItem, "subsurface_radius").get()
                attributes["attenuationColor"   ] = self.getSFColor(ac.r(), ac.g(), ac.b())
                
                tsc = rkMat.getMatXAttribute(shSceneItem, "transmission_scatter").get()
                attributes["scatterAnisotropy"  ] = rkMat.getMatXAttribute(shSceneItem, "transmission_scatter_anisotropy").get()
                attributes["multiscatterColor"  ] = self.getSFColor(tsc.r(), tsc.g(), tsc.b())
                
                noScaleDisp = rkMat.getMatXAttribute(shSceneItem, "transmission_dispersion_abbe_number").get()
                attributes["dispersion"         ] = noScaleDisp * rkMat.getMatXAttribute(shSceneItem, "transmission_dispersion_scale").get()
            
            #Specular Stuff - already done
            attributes["indexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "specular_ior").get()
            aniso = rkMat.getMatXAttribute(shSceneItem, "specular_roughness_anisotropy").get()
            if aniso > 0.0:
                attributes["anisotropyStrength"] = aniso
                anisotropyTexture = rkMat.getUFEConnectedTexture(shSceneItem, "geometry_tangent")
                if anisotropyTexture:
                    attributes["anisotropyTexture"] = anisotropyTexture
            
            #Clearcoat Material
            cWeight = rkMat.getMatXAttribute(shSceneItem, "coat_weight").get()
            if cWeight > 0.0:
                attributes["clearcoat"] = cWeight
                clearcoatTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat_color")
                if clearcoatTexture:
                    attributes["clearcoatTexture"] = clearcoatTexture
                else:
                    bc  = attributes.get("baseColor", (1.0, 1.0, 1.0))
                    ccc = rkMat.getMatXAttribute(shSceneItem, "clearcoat_color").get()
                    attributes["baseColor"] = self.getSFColor((bc[0] * (1 - cWeight)) + (ccc.r() * cWeight), (bc[1] * (1 - cWeight)) + (ccc.g() * cWeight), (bc[2] * (1 - cWeight)) + (ccc.b() * cWeight))
                    
                ccrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat_roughness")
                if ccrTexture:
                    attributes["clearcoatRoughnessTexture"] = ccrTexture
                    attributes["clearcoatRoughness"] = 1.0
                else:
                    attributes["clearcoatRoughness"] = rkMat.getMatXAttribute(shSceneItem, "clearcoat_roughness").get()
                
                ccnTexture = rkMat.getUFEConnectedTexture(shSceneItem, "clearcoat_normal")
                if ccnTexture:
                    attributes["clearcoatNormalTexture"] = ccnTexture

            #Sheen Material
            fWeight = rkMat.getMatXAttribute(shSceneItem, "fuzz_weight").get()
            if fWeight> 0.0:
                shncTexture = rkMat.getUFEConnectedTexture(shSceneItem, "fuzz_color")
                if shncTexture:
                    attributes["sheenColorTexture"] = shncTexture
                    attributes["sheenColor"] = (1.0 * fWeight, 1.0 * fWeight, 1.0 * fWeight)
                else:
                    shncVal = rkMat.getMatXAttribute(shSceneItem, "fuzz_color").get()
                    attributes["sheenColor"] = self.getSFColor(shncVal.r() * fWeight, shncVal.g() * fWeight, shncVal.b() * fWeight)

                shnrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "fuzz_roughness")
                if shnrTexture:
                    attributes["sheenRoughnessTexture"] = shnrTexture
                    attributes["sheenRoughness"] = 1.0 * fWeight
                else:
                    shnrVal = rkMat.getMatXAttribute(shSceneItem, "fuzz_roughness").get()
                    attributes["sheenRoughness"] = shnrVal * fWeight
            
            iridescenceTexture = rkMat.getUFEConnectedTexture(shSceneItem, "thin_film_weight")
            iridWeight    = 1.0
            iridThickness = 1.0
            hasIrid = False
            
            if iridescenceTexture:
                hasIrid = True
            else:
                iridWeight = rkMat.getMatXAttribute(shSceneItem, "thin_film_weight").get()
            
            iridescenceThicknessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "thin_film_thickness")
            if iridescenceThicknessTexture:
                hasIrid = True
            else:
                iridThickness = rkMat.getMatXAttribute(shSceneItem, "thin_film_thickness").get()
                
            if iridWeight * iridThickness > 0.0:
                hasIrid = True
                
            if hasIrid == True:
                if iridescenceTexture:
                    attributes["iridescenceTexture"] = iridescenceTexture
                if iridescenceThicknessTexture:
                    attributes["iridescenceThicknessTexture"] = iridescenceThicknessTexture
                    
                attributes["iridescence"] = iridWeight
                attributes["iridescenceThicknessMinimum" ] = iridThickness * 1000
                attributes["iridescenceThicknessMaximum" ] = iridThickness * 1000
                attributes["iridescenceIndexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "thin_film_ior").get()
            
            # For X_ITE and CGE
            #self.setMatX_PhysicalMaterialEXT(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialEXT(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def processMatX_stnd_pbr(    self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        # Collect basic PhysicalMaterial node information
        attributes = {}
        
        baseColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base_color")
        if baseColorTexture:
            attributes["baseTexture"] = baseColorTexture
        else:
            baseColorAttr = rkMat.getMatXAttribute(shSceneItem, "base_color")
            bcv = baseColorAttr.get()
            attributes["baseColor"] = self.getSFColor(bcv.r(), bcv.g(), bcv.b())
        
        metalTexture = rkMat.getUFEConnectedTexture(shSceneItem, "metalness")
        if metalTexture:
            attributes["metallic"] = 1.0
        else:
            attributes["metallic"] = rkMat.getMatXAttribute(shSceneItem, "metalness").get()
            
        roughTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specular_roughness")
        if roughTexture:
            attributes["roughness"] = 1.0
        else:
            cRough = rkMat.getMatXAttribute(shSceneItem, "specular_roughness").get()
            if isX3DOM == False:
                cRough = cRough + rkMat.getMatXAttribute(shSceneItem, "transmission_extra_roughness").get()
            if cRough > 1.0:
                cRough = 1.0
            attributes["roughness"] = cRough
        
        if metalTexture:
            attributes["metallicRoughnessTexture"] = metalTexture
        elif roughTexture:
            attributes["metallicRoughnessTexture"] = roughTexture
            
        occlusionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "base")
        if occlusionTexture:
            attributes["occlusionTexture"]  = occlusionTexture
            attributes["occlusionStrength"] = 1.0
        else:
            attributes["occlusionStrength"] = rkMat.getMatXAttribute(shSceneItem, "base").get()
            occlusionTexture2 = rkMat.getUFEConnectedTexture(shSceneItem, "specular")
            if occlusionTexture2:
                attributes["occlusionTexture"]  = occlusionTexture2
        
        if not occlusionTexture2:
            attributes["specularWeight"] = rkMat.getMatXAttribute(shSceneItem, "specular").get()
                
        emissiveColorTexture =  rkMat.getUFEConnectedTexture(shSceneItem, "emission_color")
        if emissiveColorTexture:
            attributes["emissiveTexture"] = emissiveColorTexture
            attributes["emissiveColor"]   = (1.0, 1.0, 1.0)
        
        # Get normalStrength / normalTexture
        normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normal", connected=True)
        if normalScaleAttr:
            scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
            scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
            if not scaleAttr:
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
            if scaleAttr:
                attributes["normalScale"] = scaleAttr.get()
                
            normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
            if not normalTexture:
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
            if normalTexture:
                attributes["normalTexture"] = normalTexture

        # Get basic specular information
        specularColorTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specular_color")
        if specularColorTexture:
            attributes["specularColorTexture"] = specularColorTexture
            try:
                iPath = rkMat.getMatXAttribute(specularColorTexture, "file", grasp=True)
                img = aom.MImage()
                img.readFromFile(iPath)
                if img.depth() == 4:
                    attributes["specularTexture"] = specularColorTexture
            except:
                pass
        else:
            specularColorAttr = rkMat.getMatXAttribute(shSceneItem, "specular_color")
            spc = specularColorAttr.get()
            attributes["specularColor"] = self.getSFColor(spc.r(), spc.g(), spc.b())
            
        trspAttr = rkMat.getMatXAttribute(shSceneItem, "geometry_opacity")
        attributes["transparency"] = 1 - trspAttr.get()

        if isX3DOM:
            # For X3DOM
            #self.setMatX_PhysicalMaterialX3DOM(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialX3DOM(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        else:
            ###################################################################################
            ###################################################################################
            # Collect Up PhysicalMaterial X_ITE Material Extensions for PhysicalMaterialEXT
            #
 
            attributes["emissiveStrength"] =  rkMat.getMatXAttribute(shSceneItem, "emission").get()
            
            tWeight = rkMat.getMatXAttribute(shSceneItem, "transmission").get()
            sWeight = rkMat.getMatXAttribute(shSceneItem, "subsurface"  ).get()
            isTWall = rkMat.getMatXAttribute(shSceneItem, "thin_walled" ).get()
            
            if tWeight != 0.0:
                attributes["transparency"] = 0.0
                attributes["transmission"] = tWeight

                transmissionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "transmission_color")
                if transmissionTexture:
                    attributes["transmissionTexture"] = transmissionTexture
                    attributes["diffuseTransmissionColor"] = (1.0, 1.0, 1.0)
                else:
                    trCol = rkMat.getMatXAttribute(shSceneItem, "transmission_color").get()
                    attributes["diffuseTransmissionColor"] = self.getSFColor(trCol.r(), trCol.g(), trCol.b())
            if isTWall == True:
                attributes["diffuseTransmission"] = sWeight
                diffuseTransmissionTexture = rkMat.getUFEConnectedTexture(shSceneItem, "subsurface_color")
                if diffuseTransmissionTexture:
                    attributes["diffuseTransmissionTexture"] = diffuseTransmissionTexture
                else:
                    dtc  = attributes.get("diffuseTransmissionColor", (1.0, 1.0, 1.0))
                    dtc2 = rkMat.getMatXAttribute(shSceneItem, "subsurface_color").get()
                    attributes["diffuseTransmissionColor"] = (dtc[0] * dtc2.r(), dtc[1] * dtc2.g(), dtc[2] * dtc2.b())
            else:
            
                # Volumetric Material
                myThickness = 1.0
                thicknessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "transmission_depth")
                if thicknessTexture:
                    attributes["thicknessTexture"] = thicknessTexture
                else:
                    myThickness = rkMat.getMatXAttribute(shSceneItem, "transmission_depth").get()

                vmThickness = tWeight ## More like water
                if sWeight > tWeight:
                    vmThickness = sWeight ## More like skin/wax
                    
                attributes["thickness"] = vmThickness * myThickness
                
                ac  = rkMat.getMatXAttribute(shSceneItem, "subsurface_radius").get()
                bc  = attributes.get("diffuseTransmissionColor", (1.0, 1.0, 1.0))
                bcc = attributes.get("baseColor", (1.0, 1.0, 1.0))
                
                attributes["baseColor"] = self.getSFColor( (bcc[0] * (1.0 - sWeight)) + (bc[0] * sWeight), (bcc[1] * (1.0 - sWeight)) + (bc[1] * sWeight), (bcc[2] * (1.0 - sWeight)) + (bc[2] * sWeight) )

                attributes["attenuationDistance"] = rkMat.getMatXAttribute(shSceneItem, "subsurface_scale").get()
                attributes["attenuationColor"   ] = self.getSFColor(ac.r(), ac.g(), ac.b())
                
                tsc = rkMat.getMatXAttribute(shSceneItem, "transmission_scatter").get()
                attributes["scatterAnisotropy"  ] = rkMat.getMatXAttribute(shSceneItem, "transmission_scatter_anisotropy").get()
                attributes["multiscatterColor"  ] = self.getSFColor(tsc.r(), tsc.g(), tsc.b())
                
                attributes["dispersion"         ] = rkMat.getMatXAttribute(shSceneItem, "transmission_dispersion").get()
            
            #Specular Stuff - already done
            attributes["indexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "specular_IOR").get()
            aniso = rkMat.getMatXAttribute(shSceneItem, "specular_anisotropy").get()
            if aniso > 0.0:
                attributes["anisotropyStrength"] = aniso
                attributes["rotation"]           = rkMat.getMatXAttribute(shSceneItem, "specular_rotation").get()
                anisotropyTexture = rkMat.getUFEConnectedTexture(shSceneItem, "tangent")
                if anisotropyTexture:
                    attributes["anisotropyTexture"] = anisotropyTexture
            
            #Clearcoat Material
            cWeight = rkMat.getMatXAttribute(shSceneItem, "coat").get()
            if cWeight > 0.0:
                attributes["clearcoat"] = cWeight
                clearcoatTexture = rkMat.getUFEConnectedTexture(shSceneItem, "coat_color")
                if clearcoatTexture:
                    attributes["clearcoatTexture"] = clearcoatTexture
                else:
                    bc  = attributes.get("baseColor", (1.0, 1.0, 1.0))
                    ccc = rkMat.getMatXAttribute(shSceneItem, "coat_color").get()
                    attributes["baseColor"] = self.getSFColor((bc[0] * (1 - cWeight)) + (ccc.r() * cWeight), (bc[1] * (1 - cWeight)) + (ccc.g() * cWeight), (bc[2] * (1 - cWeight)) + (ccc.b() * cWeight))
                    
                ccrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "coat_roughness")
                if ccrTexture:
                    attributes["clearcoatRoughnessTexture"] = ccrTexture
                    attributes["clearcoatRoughness"] = 1.0
                else:
                    attributes["clearcoatRoughness"] = rkMat.getMatXAttribute(shSceneItem, "coat_roughness").get()
                
                ccnTexture = rkMat.getUFEConnectedTexture(shSceneItem, "coat_normal")
                if ccnTexture:
                    attributes["clearcoatNormalTexture"] = ccnTexture

            #Sheen Material
            shWeight = rkMat.getMatXAttribute(shSceneItem, "sheen").get()
            if shWeight> 0.0:
                shncTexture = rkMat.getUFEConnectedTexture(shSceneItem, "sheen_color")
                if shncTexture:
                    attributes["sheenColorTexture"] = shncTexture
                    attributes["sheenColor"] = (1.0 * shWeight, 1.0 * shWeight, 1.0 * shWeight)
                else:
                    shncVal = rkMat.getMatXAttribute(shSceneItem, "sheen_color").get()
                    attributes["sheenColor"] = self.getSFColor(shncVal.r() * shWeight, shncVal.g() * shWeight, shncVal.b() * shWeight)

                shnrTexture = rkMat.getUFEConnectedTexture(shSceneItem, "sheen_roughness")
                if shnrTexture:
                    attributes["sheenRoughnessTexture"] = shnrTexture
                    attributes["sheenRoughness"] = 1.0 * shWeight
                else:
                    shnrVal = rkMat.getMatXAttribute(shSceneItem, "fuzz_roughness").get()
                    attributes["sheenRoughness"] = shnrVal * shWeight
            
            #iridescenceTexture = rkMat.getUFEConnectedTexture(shSceneItem, "thin_film_weight")
            iridWeight    = 1.0
            iridThickness = 1.0
            hasIrid = False
            
            iridescenceThicknessTexture = rkMat.getUFEConnectedTexture(shSceneItem, "thin_film_thickness")
            if iridescenceThicknessTexture:
                hasIrid = True
            else:
                iridThickness = rkMat.getMatXAttribute(shSceneItem, "thin_film_thickness").get()
                
            if iridWeight * iridThickness > 0.0:
                hasIrid = True
                
            if hasIrid == True:
                if iridescenceThicknessTexture:
                    attributes["iridescenceThicknessTexture"] = iridescenceThicknessTexture
                    
                attributes["iridescence"] = iridWeight
                attributes["iridescenceThicknessMinimum" ] = iridThickness * 1000
                attributes["iridescenceThicknessMaximum" ] = iridThickness * 1000
                attributes["iridescenceIndexOfRefraction"] = rkMat.getMatXAttribute(shSceneItem, "thin_film_IOR").get()
            
            # For X_ITE and CGE
            #self.setMatX_PhysicalMaterialEXT(attributes, physMat, matXSS, x3dAppearance, uvSetNames, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
            self.setMatX_PhysicalMaterialEXT(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def addTextureToAppearance(self,x3dAppearance, ufeTextureNodes, matchedSets, textureTransforms, ignoreTT, isX3DOM):
        if len(ufeTextureNodes) > 1:
            mtBna = self.trv.processBasicNodeAddition(x3dAppearance, "texture", "MultiTexture", x3dAppearance.DEF + "_MULT")
            if mtBna[0] == False:
                for texture in ufeTextureNodes:
                    ignoreTT = self.processMatXTexture(texture, x3dAppearance, mtBna[1], "texture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    
        elif len(ufeTextureNodes) == 1:
            ignoreTT = self.processMatXTexture(ufeTextureNodes[0], x3dAppearance, x3dAppearance, "texture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            
    
    def processMatX_maya_lambert(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        attributes = {}
        
        appTexture = []
        
        dv             = rkMat.getMatXAttribute(shSceneItem, "diffuse").get()
        diffuseTexture = rkMat.getUFEConnectedTexture(shSceneItem, "color")
        if diffuseTexture:
            if  isX3DOM == False:
                attributes["diffuseTexture"] = diffuseTexture
            else:
                appTexture.append(("base", diffuseTexture))
            attributes["diffuseColor"      ] = self.getSFColor(1.0 * dv, 1.0 * dv, 1.0 * dv)
        else:
            dc = rkMat.getMatXAttribute(shSceneItem, "color").get()
            attributes["diffuseColor"    ] = self.getSFColor(dc.r() * dv, dc.g() * dv, dc.b() * dv)

        tpc  = rkMat.getMatXAttribute(shSceneItem, "transparency").get()
        tpca = (tpc.r() + tpc.g() + tpc.b()) / 3
        if tpca > 1.0:
            tpca = 1.0

        attributes["transparency"    ] = tpca
        attributes["ambientIntensity"] = 0.0
        attributes["shininess"       ] = 0.0
        
        emissiveTexture = rkMat.getUFEConnectedTexture(shSceneItem, "incandescence")
        if emissiveTexture:
            if isX3DOM == False:
                attributes["emissiveTexture"] = emissiveTexture
                attributes["emissiveColor"] = self.getSFColor(1.0, 1.0, 1.0)
            else:
                appTexture.append(("emissive", emissiveTexture))
        else:
            ec = rkMat.getMatXAttribute(shSceneItem, "incandescence").get()
            attributes["emissiveColor"    ] = self.getSFColor(ec.r(), ec.g(), ec.b())
        
        if isX3DOM == False:
            # Get normalStrength / normalTexture
            normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normalCamera", connected=True)
            if normalScaleAttr:
                scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
                if not scaleAttr:
                    scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
                if scaleAttr:
                    attributes["normalScale"] = scaleAttr.get()
                    
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
                if normalTexture:
                    attributes["normalTexture"] = normalTexture

        if len(appTexture) > 0:
            self.addTextureToAppearance(x3dAppearance, appTexture, matchedSets, textureTransforms, ignoreTT, isX3DOM)

        self.setMatX_Material(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)
        

    def processMatX_ai_lambert(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        attributes = {}
        
        appTexture = []
        
        diffuseTexture =  rkMat.getUFEConnectedTexture(shSceneItem, "Kd_color")
        if diffuseTexture:
            if  isX3DOM == False:
                attributes["diffuseTexture"] = diffuseTexture
            else:
                appTexture.append(("base", diffuseTexture))
            attributes["diffuseColor"      ] = (1.0, 1.0, 1.0)
        else:
            kdc = rkMat.getMatXAttribute(shSceneItem, "Kd_color").get()
            attributes["diffuseColor"    ] = self.getSFColor(kdc.r(), kdc.g(), kdc.b())

        attributes["ambientIntensity"] = 0.0
        attributes["shininess"       ] = 0.0
        
        opc  = rkMat.getMatXAttribute(shSceneItem, "opacity").get()
        opca = (opc.r() + opc.g() + opc.b()) / 3
        if opca > 1.0:
            opca = 1.0
        attributes["transparency"] = 1 - opca
        
        if isX3DOM == False:
            # Get normalStrength / normalTexture
            normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normal", connected=True)
            if normalScaleAttr:
                scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
                if not scaleAttr:
                    scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
                if scaleAttr:
                    attributes["normalScale"] = scaleAttr.get()
                    
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
                if normalTexture:
                    attributes["normalTexture"] = normalTexture

        if len(appTexture) > 0:
            self.addTextureToAppearance(x3dAppearance, appTexture, matchedSets, textureTransforms, ignoreTT, isX3DOM)

        self.setMatX_Material(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def processMatX_maya_phong(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        attributes = {}
        
        appTexture = []
        
        dv             = rkMat.getMatXAttribute(shSceneItem, "diffuse").get()
        diffuseTexture = rkMat.getUFEConnectedTexture(shSceneItem, "color")
        if diffuseTexture:
            if  isX3DOM == False:
                attributes["diffuseTexture"] = diffuseTexture
            else:
                appTexture.append(("base", diffuseTexture))
            attributes["diffuseColor"      ] = self.getSFColor(1.0 * dv, 1.0 * dv, 1.0 * dv)
        else:
            dc = rkMat.getMatXAttribute(shSceneItem, "color").get()
            attributes["diffuseColor"    ] = self.getSFColor(dc.r() * dv, dc.g() * dv, dc.b() * dv)

        tpc  = rkMat.getMatXAttribute(shSceneItem, "transparency").get()
        tpca = (tpc.r() + tpc.g() + tpc.b()) / 3
        if tpca > 1.0:
            tpca = 1.0

        attributes["transparency"    ] = tpca
        
        cosPwr =  rkMat.getMatXAttribute(shSceneItem, "cosinePower")
        
        # TODO shininess Texture
        attributes["shininess"       ] = np.log2(cosPwr) / 7
        
        ref =  rkMat.getMatXAttribute(shSceneItem, "reflectivity")
        specularTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specularColor")
        
        if specularTexture:
            if isX3DOM == False:
                attributes["specularTexture"] = specularTexture
                attributes["specularColor"] = self.getSFColor(1.0 * ref, 1.0 * ref, 1.0 * ref)
            else:
                appTexture.append(("specular", specularTexture))
        else:
            ec = rkMat.getMatXAttribute(shSceneItem, "specularColor").get()
            attributes["specularColor"    ] = self.getSFColor(ec.r() * ref, ec.g() * ref, ec.b() * ref)

        emissiveTexture = rkMat.getUFEConnectedTexture(shSceneItem, "incandescence")
        if emissiveTexture:
            if isX3DOM == False:
                attributes["emissiveTexture"] = emissiveTexture
                attributes["emissiveColor"] = self.getSFColor(1.0, 1.0, 1.0)
            else:
                appTexture.append(("emissive", emissiveTexture))
        else:
            ec = rkMat.getMatXAttribute(shSceneItem, "incandescence").get()
            attributes["emissiveColor"    ] = self.getSFColor(ec.r(), ec.g(), ec.b())
        
        ect = attributes.get("emissiveColor", (0.0, 0.0, 0.0))
        
        attributes["ambientIntensity"] = (ect[0] + ect[1] + ect[2]) / 3
        
            
        #reflectedTexture = rkMat.getUFEConnectedTexture(shSceneItem, "reflectedColor")
        #if reflectedTexture:
        #    if isX3DOM == False:
        #        attributes["specularTexture"] = reflectedTexture
        #    else:
        #        appTexture.append(("reflected", reflectedTexture))        
        
        if isX3DOM == False:
            # Get normalStrength / normalTexture
            normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normalCamera", connected=True)
            if normalScaleAttr:
                scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
                if not scaleAttr:
                    scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
                if scaleAttr:
                    attributes["normalScale"] = scaleAttr.get()
                    
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
                if normalTexture:
                    attributes["normalTexture"] = normalTexture

        if len(appTexture) > 0:
            self.addTextureToAppearance(x3dAppearance, appTexture, matchedSets, textureTransforms, ignoreTT, isX3DOM)

        self.setMatX_Material(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def processMatX_maya_blinn(self, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        attributes = {}
        
        appTexture = []
        
        dv             = rkMat.getMatXAttribute(shSceneItem, "diffuse").get()
        diffuseTexture = rkMat.getUFEConnectedTexture(shSceneItem, "color")
        if diffuseTexture:
            if  isX3DOM == False:
                attributes["diffuseTexture"] = diffuseTexture
            else:
                appTexture.append(("base", diffuseTexture))
            attributes["diffuseColor"      ] = self.getSFColor(1.0 * dv, 1.0 * dv, 1.0 * dv)
        else:
            dc = rkMat.getMatXAttribute(shSceneItem, "color").get()
            attributes["diffuseColor"    ] = self.getSFColor(dc.r() * dv, dc.g() * dv, dc.b() * dv)

        tpc  = rkMat.getMatXAttribute(shSceneItem, "transparency").get()
        tpca = (tpc.r() + tpc.g() + tpc.b()) / 3
        if tpca > 1.0:
            tpca = 1.0

        attributes["transparency"    ] = tpca
        
        eccent =  rkMat.getMatXAttribute(shSceneItem, "eccentricity")
        
        # TODO shininess Texture
        attributes["shininess"       ] = 1 - eccent
        
        ref  = rkMat.getMatXAttribute(shSceneItem, "reflectivity")
        spro = rkMat.getMatXAttribute(shSceneItem, "specularRollOff")
        ref  = ref * spro
        specularTexture = rkMat.getUFEConnectedTexture(shSceneItem, "specularColor")
        if specularTexture:
            if isX3DOM == False:
                attributes["specularTexture"] = specularTexture
                attributes["specularColor"] = self.getSFColor(1.0 * ref, 1.0 * ref, 1.0 * ref)
            else:
                appTexture.append(("specular", specularTexture))
        else:
            ec = rkMat.getMatXAttribute(shSceneItem, "specularColor").get()
            attributes["specularColor"    ] = self.getSFColor(ec.r() * ref, ec.g() * ref, ec.b() * ref)
            
        emissiveTexture = rkMat.getUFEConnectedTexture(shSceneItem, "incandescence")
        if emissiveTexture:
            if isX3DOM == False:
                attributes["emissiveTexture"] = emissiveTexture
                attributes["emissiveColor"] = self.getSFColor(1.0, 1.0, 1.0)
            else:
                appTexture.append(("emissive", emissiveTexture))
        else:
            ec = rkMat.getMatXAttribute(shSceneItem, "incandescence").get()
            attributes["emissiveColor"    ] = self.getSFColor(ec.r(), ec.g(), ec.b())
        
        ect = attributes.get("emissiveColor", (0.0, 0.0, 0.0))
        
        attributes["ambientIntensity"] = ((0.2126 * ect[0]) + (0.2126 * ect[1]) + (0.2126 * ect[2])) / 3
        
        #reflectedTexture = rkMat.getUFEConnectedTexture(shSceneItem, "reflectedColor")
        #if reflectedTexture:
        #    if isX3DOM == False:
        #        attributes["specularTexture"] = reflectedTexture
        #    else:
        #        appTexture.append(("reflected", reflectedTexture))        
        
        if isX3DOM == False:
            # Get normalStrength / normalTexture
            normalScaleAttr = rkMat.getUFEAttribute(shSceneItem, "normalCamera", connected=True)
            if normalScaleAttr:
                scaleItem = ufe.Hierarchy.createItem(normalScaleAttr.src.path)
                scaleAttr = rkMat.getMatXAttribute(scaleItem, "scale")
                if not scaleAttr:
                    scaleAttr = rkMat.getMatXAttribute(scaleItem, "bump_height")
                if scaleAttr:
                    attributes["normalScale"] = scaleAttr.get()
                    
                normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "bump_map")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "height")
                if not normalTexture:
                    normalTexture = rkMat.getUFEConnectedTexture(scaleItem, "in")
                if normalTexture:
                    attributes["normalTexture"] = normalTexture

        if len(appTexture) > 0:
            self.addTextureToAppearance(x3dAppearance, appTexture, matchedSets, textureTransforms, ignoreTT, isX3DOM)

        self.setMatX_Material(attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM)


    def setMatX_Material(self, attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        matBna = self.trv.processBasicNodeAddition(x3dAppearance, cField, "Material", matXSS.name())
        if matBna[0] == False:
            ambientTexture = attributes.get("ambientTexture", None)
            if ambientTexture:
                ignoreTT = self.processMatXTexture(ambientTexture, x3dAppearance, material, "ambientTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.ambientIntensity = 1.0
            else:
                material.ambientIntensity = attributes.get("ambientIntensity", 0.2)

            diffuseTexture = attributes.get("diffuseTexture", None)
            if diffuseTexture:
                ignoreTT = self.processMatXTexture(diffuseTexture, x3dAppearance, material, "diffuseTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.diffuseColor = (1.0, 1.0, 1.0)
            else:
                material.diffuseColor = attributes.get("diffuseColor",  (0.8, 0.8, 0.8))

            emissiveTexture = attributes.get("emissiveTexture", None)
            if emissiveTexture:
                ignoreTT = self.processMatXTexture(emissiveTexture, x3dAppearance, material, "emissiveTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.emissiveColor = (1.0, 1.0, 1.0)
            else:
                material.emissiveColor = attributes.get("emissiveColor", (0.0, 0.0, 0.0))

            normalTexture = attributes.get("normalTexture", None)
            if normalTexture:
                ignoreTT = self.processMatXTexture(normalTexture, x3dAppearance, material, "normalTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                physMat.normalScale = attributes.get("normalScale", 1.0)

            occlusionTexture = attributes.get("occlusionTexture", None)
            if occlusionTexture:
                ignoreTT = self.processMatXTexture(occlusionTexture, x3dAppearance, material, "occlusionTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.occlusionStrength = 1.0
            else:
                material.occlusionStrength = attributes.get("occlusionStrength",  1.0)

            shininessTexture = attributes.get("shininessTexture", None)
            if shininessTexture:
                ignoreTT = self.processMatXTexture(shininessTexture, x3dAppearance, material, "shininessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.shininess = 1.0
            else:
                material.shininess = attributes.get("shininess", 0.2)

            specularTexture = attributes.get("specularTexture", None)
            if specularTexture:
                ignoreTT = self.processMatXTexture(specularTexture, x3dAppearance, material, "specularTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                material.specularColor = (1.0, 1.0, 1.0)
            else:
                material.specularColor = attributes.get("specularColor", (0.0, 0.0, 0.0))

            material.transparency = attributes.get("transparency", 0.0)



    def setMatX_PhysicalMaterialEXT(self, attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        matBna = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterialExt", matXSS.name())
        if matBna[0] == False:
            physMat = matBna[1]
            
            x3dAppearance.alphaCutoff = attributes.get("alphaCutoff", 0.5)
            x3dAppearance.alphaMode   = rkMat.getAlphaMode(attributes["alphaMode"])
            
            physMat.baseColor = attributes.get("baseColor", (1.0, 1.0, 1.0))
           
            baseTexture = attributes.get("baseTexture", None)
            if baseTexture:
                ignoreTT = self.processMatXTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            
            physMat.emissiveColor = attributes.get("emissiveColor", (0.0, 0.0, 0.0))

            emissiveTexture = attributes.get("emissiveTexture", None)
            if emissiveTexture:
                ignoreTT = self.processMatXTexture(emissiveTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                physMat.emissiveColor = (1.0, 1.0, 1.0)

            normalTexture = attributes.get("normalTexture", None)
            if normalTexture:
                ignoreTT = self.processMatXTexture(normalTexture, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                physMat.normalScale = attributes.get("normalScale", 1.0)

            metallicRoughnessTexture = attributes.get("metallicRoughnessTexture", None)
            if metallicRoughnessTexture:
                ignoreTT = self.processMatXTexture(metallicRoughnessTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)

            physMat.metallic = attributes.get("metallic", 1.0)
                
            physMat.roughness = attributes.get("roughness", 1.0)

            occlusionTexture  = attributes.get("occlusionTexture", None)
            if occlusionTexture:
                ignoreTT = self.processMatXTexture(occlusionTexture, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            
            physMat.occlusionStrength = attributes.get("occlusionStrength", 1.0)
            
            physMat.transparency = attributes.get("transparency", 0.0)
            
            # X_ITE Material Extensions
            emissiveStrength = attributes.get("emissiveStrength", False)
            if emissiveStrength:
                esBna = self.trv.processBasicNodeAddition(physMat, "extensions", "EmissiveStrengthMaterialExtension", physMat.DEF + "_ESME")
                if esBna[0] == False:
                    esBna[1].emissiveStrength = emissiveStrength
            
            transmissionWeight = attributes.get("transmission", 0.0)
            if transmissionWeight > 0.0:
                trBna = self.trv.processBasicNodeAddition(physMat, "extensions", "TransmissionMaterialExtension", physMat.DEF + "_TRME")
                if trBna[0] == False:
                    trBna[1].transmission = transmissionWeight
                    transmissionTexture   = attributes.get("transmissionTexture", None)
                    if transmissionTexture:
                        ignoreTT = self.processMatXTexture(transmissionTexture, x3dAppearance, trBna[1], "transmissionTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)

            diffuseTransmission = attributes.get("diffuseTransmission", 0.0)
            if diffuseTransmission > 0.0:
                dtBna = self.trv.processBasicNodeAddition(physMat, "extensions", "DiffuseTransmissionMaterialExtension", physMat.DEF + "_DTME")
                if dtBna[0] == False:
                    dtBna[1].diffuseTransmission    = diffuseTransmission
                    diffuseTransmissionColorTexture = attributes.get("diffuseTransmissionColorTexture", None)
                    diffuseTransmissionTexture      = attributes.get("diffuseTransmissionTexture",      None)
                    if diffuseTransmissionColorTexture:
                        ignoreTT = self.processMatXTexture(diffuseTransmissionColorTexture, x3dAppearance, dtBna[1], "diffuseTransmissionColorTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if diffuseTransmissionTexture:
                        ignoreTT = self.processMatXTexture(diffuseTransmissionTexture,      x3dAppearance, dtBna[1], "diffuseTransmissionTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                        #try:
                        #    iPath = rkMat.getMatXAttribute(diffuseTransmissionColorTexture, "file", grasp=True)
                        #    img = aom.MImage()
                        #    img.readFromFile(iPath)
                        #    if img.depth() == 4:
                        #        ignoreTT = self.processMatXTexture(diffuseTransmissionColorTexture, x3dAppearance, dtBna[1], "diffuseTransmissionTexture", uvSetNames, textureTransforms, ignoreTT, isX3DOM)
                        #except:
                        #    pass
                        
            #Volume Stuff
            thickness = attributes.get("thickness", 0.0)
            if thickness > 0.0:
                vmBna = self.trv.processBasicNodeAddition(physMat, "extensions", "VolumeMaterialExtension", physMat.DEF + "_VLME")
                if vmBna[0] == False:
                    vmBna[1].thickness = thickness
                    vmBna[1].attenuationDistance = attributes.get("attenuationDistance",      1000000)
                    vmBna[1].attenuationColor    = attributes.get("attenuationColor", (1.0, 1.0, 1.0))
                    thicknessTexture = attributes.get("thicknessTexture", None)
                    if thicknessTexture:
                        ignoreTT = self.processMatXTexture(thicknessTexture, x3dAppearance, trBna[1], "thicknessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                        
            scatterAnisotropy = attributes.get("scatterAnisotropy", None)
            if scatterAnisotropy:
                multiscatterColor = attributes.get("multiscatterColor", (0.0, 0.0, 0.0))
                vmsBna = self.trv.processBasicNodeAddition(physMat, "extensions", "VolumeScatterMaterialExtension", physMat.DEF + "_VSME")
                if vmsBna[0] == False:
                    vmsBna[1].scatterAnisotropy = scatterAnisotropy
                    vmsBna[1].multiscatterColor = multiscatterColor
                    
            dispersion = attributes.get("dispersion", None)
            if dispersion:
                dmBna = self.trv.processBasicNodeAddition(physMat, "extensions", "DispersionMaterialExtension", physMat.DEF + "_DSPME")
                if dmBna[0] == False:
                    #noScaleDisp = 20/cmds.getAttr(material.name() + ".transmissionDispersionAbbeNumber")
                    #dmBna[1].dispersion = noScaleDisp * cmds.getAttr(material.name() + ".transmissionDispersionScale")
                    dmBna[1].dispersion = dispersion
                    
            specular = attributes.get("specularWeight", 0.0)
            if specular > 0.0:
                spcBna = self.trv.processBasicNodeAddition(physMat, "extensions", "SpecularMaterialExtension", physMat.DEF + "_SpecME")
                if spcBna[0] == False:
                    spcBna[1].specular         = specular
                    spcBna[1].specularStrength = attributes.get("specularStrength",      1.0)
                    specularTexture            = attributes.get("specularTexture",      None)
                    specularColorTexture       = attributes.get("specularColorTexture", None)
                    if specularTexture:
                        ignoreTT = self.processMatXTexture(specularTexture,      x3dAppearance, spcBna[1], "specularTexture",      matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if specularColorTexture:
                        ignoreTT = self.processMatXTexture(specularColorTexture, x3dAppearance, spcBna[1], "specularColorTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)

            iorBna = self.trv.processBasicNodeAddition(physMat, "extensions", "IORMaterialExtension", physMat.DEF + "_IORME")
            if iorBna[0] == False:
                iorBna[1].indexOfRefraction = attributes.get("indexOfRefraction", 1.5)

            anisotropy = attributes.get("anisotropy", 0.0)
            if anisotropy > 0.0:
                aniBna = self.trv.processBasicNodeAddition(physMat, "extensions", "AnisotropyMaterialExtension", physMat.DEF + "_AniME")
                if aniBna[0] == False:
                    aniBna[1].anisotropyStrength = anisotropy
                    aniBna[1].anisotropyRotation = attributes.get("anisotropyRotation", 0.0)
                    anisotropyTexture = attributes.get("anisotropyTexture", None)
                    if anisotropyTexture:
                        ignoreTT = self.processMatXTexture(anisotropyTexture, x3dAppearance, spcBna[1], "anisotropyTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)

            clearcoat = attributes.get("clearcoat", 0.0)
            if clearcoat > 0.0:
                coaBna = self.trv.processBasicNodeAddition(physMat, "extensions", "ClearcoatMaterialExtension", physMat.DEF + "_CoatME")
                if coaBna[0] == False:
                    coaBna[1].clearcoat = clearcoat
                    coaBna[1].clearcoatRoughness = attributes.get("clearcoatRoughness",         0.0)
                    clearcoatTexture             = attributes.get("clearcoatTexture",          None)
                    clearcoatRoughnessTexture    = attributes.get("clearcoatRoughnessTexture", None)
                    clearcoatNormalTexture       = attributes.get("clearcoatNormalTexture",    None)
                    if clearcoatTexture:
                        ignoreTT = self.processMatXTexture(clearcoatTexture,          x3dAppearance, coaBna[1], "clearcoatTexture",          matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if clearcoatRoughnessTexture:
                        ignoreTT = self.processMatXTexture(clearcoatRoughnessTexture, x3dAppearance, coaBna[1], "clearcoatRoughnessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if clearcoatNormalTexture:
                        ignoreTT = self.processMatXTexture(clearcoatNormalTexture,    x3dAppearance, coaBna[1], "clearcoatNormalTexture",    matchedSets, textureTransforms, ignoreTT, isX3DOM)

            sheenColor = attributes.get("sheenColor", None)
            if sheenColor:
                shnBna = self.trv.processBasicNodeAddition(physMat, "extensions", "SheenMaterialExtension", physMat.DEF + "_SheenME")
                if shnBna[0] == False:
                    shnBna[1].sheenColor     = sheenColor
                    shnBna[1].sheenRoughness = attributes.get("sheenRoughness",         1.0)
                    sheenColorTexture        = attributes.get("sheenColorTexture",     None)
                    sheenRoughnessTexture    = attributes.get("sheenRoughnessTexture", None)
                    if sheenColorTexture:
                        ignoreTT = self.processMatXTexture(sheenColorTexture,     x3dAppearance, shnBna[1], "sheenColorTexture",     matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if sheenRoughnessTexture:
                        ignoreTT = self.processMatXTexture(sheenRoughnessTexture, x3dAppearance, shnBna[1], "sheenRoughnessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)

            iridescence = attributes.get("iridescence", 0.0)
            if iridescence > 0.0:
                iriBna = self.trv.processBasicNodeAddition(physMat, "extensions", "IridescenceMaterialExtension", physMat.DEF + "_IridME") 
                if iriBna[0] == False:
                    iriBna[1].iridescence                  = iridescence
                    iriBna[1].iridescenceIndexOfRefraction = attributes.get("iridescenceIndexOfRefraction", 1.3)
                    iriBna[1].iridescenceThicknessMinimum  = attributes.get("iridescenceThicknessMinimum",  100)
                    iriBna[1].iridescenceThicknessMaximum  = attributes.get("iridescenceThicknessMaximum",  400)
                    iridescenceTexture                     = attributes.get("iridescenceTexture",          None)
                    iridescenceThicknessTexture            = attributes.get("iridescenceThicknessTexture", None)
                    if iridescenceTexture:
                        ignoreTT = self.processMatXTexture(iridescenceTexture,          x3dAppearance, iriBna[1], "iridescenceTexture",          matchedSets, textureTransforms, ignoreTT, isX3DOM)
                    if iridescenceThicknessTexture:
                        ignoreTT = self.processMatXTexture(iridescenceThicknessTexture, x3dAppearance, iriBna[1], "iridescenceThicknessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)


    def setMatX_PhysicalMaterialX3DOM(self, attributes, matXSS, x3dAppearance, matchedSets, cField, textureTransforms, ignoreTT, surfacePath, smSceneItem, shSceneItem, isX3DOM):
        # For X3DOM
        matBna = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterial_X3DOM", matXSS.name())
        if matBna[0] == False:
            physMat = matBna[1]
            
            physMat.alphaCutoff = attributes.get("alphaCutoff", 0.5)
            physMat.alphaMode   = rkMat.getAlphaMode(attributes["alphaMode"])
            
            baseColor = attributes.get("baseColor", (1.0, 1.0, 1.0))
            physMat.baseColorFactor = (baseColor[0], baseColor[1], baseColor[2], 1.0)

            baseTexture = attributes.get("baseTexture", None)
            if baseTexture:
                ignoreTT = self.processMatXTexture(baseTexture, x3dAppearance, physMat, "baseColorTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            
            mv = attributes.get("metallic", 0.0)
            physMat.diffuseColor  = attributes.get("diffuseColor", (0.8, 0.8, 0.8))
            physMat.diffuseFactor = (mv, mv, mv, 1.0)
            
            physMat.shininess     = attributes.get("shininess", 0.2)

            emissiveTexture = attributes.get("emissiveTexture", None)
            if emissiveTexture:
                physMat.emissiveColor = (1.0, 1.0, 1.0)
                ignoreTT = self.processMatXTexture(emissiveTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            else:
                physMat.emissiveColor = attributes.get("emissiveColor", (0.0, 0.0, 0.0))
            physMat.emissiveFactor = (1.0, 1.0, 1.0)

            normalTexture = attributes.get("normalTexture", None)
            if normalTexture:
                ignoreTT = self.processMatXTexture(normalTexture, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                physMat.normalScale = attributes.get("normalScale", 1.0)

            physMat.metallicFactor  = mv
            physMat.roughnessFactor = attributes.get("roughness", 1.0)

            metallicRoughnessTexture = attributes.get("metallicRoughnessTexture", None)
            if metallicRoughnessTexture:
                ignoreTT = self.processMatXTexture(metallicRoughnessTexture, x3dAppearance, physMat, "roughnessMetallicTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            else:
                occlusionTexture = attributes.get("occlusionTexture", None)
                if occlusionTexture:
                    ignoreTT = self.processMatXTexture(occlusionTexture, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            
            physMat.specularColor = attributes.get("specularColor", (0.0, 0.0, 0.0))
            
            specularColorTexture = attributes.get("specularColorTexture", None)
            if specularColorTexture:
                ignoreTT = self.processMatXTexture(specularColorTexture, x3dAppearance, physMat, "specularGlossinessTexture", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                physMat.specularColor = (1.0, 1.0, 1.0)

            sw = attributes.get("specularWeight", 1.0)
            physMat.specularFactor = self.getSFColor(sw, sw, sw)

            physMat.transparency = attributes.get("transparency", 0.0)


    def processMaterialX_X3DShaderSet(  self, matXSS, x3dAppearance, matchedSets, cField):
        ##############################################################
        # Prep for MaterialX document and GLSL I/O
        ##############################################################
        isX3DOM = False
        if self.exEncoding == "html":
            isX3DOM = True

        textureTransforms = []
        ignoreTT = False
        
        appTexture = []
        pkgFields  = []
        cmpFields  = []

        self.hasMaterialX = True

        # Setup Shader Export Paths
        localPrepPath  = self.activePrjDir + "/" + self.rkMatXPath + matXSS.name()
        matXExportPath = localPrepPath + ".mtlx"
        glslFragPath   = localPrepPath + ".frag"
        glslVertPath   = localPrepPath + ".vert"
        glslFragFile   = matXSS.name() + ".frag"
        glslVertFile   = matXSS.name() + ".vert"

        print("The Maya MaterialXShader node '" + matXSS.name() + "' was exported as two X3D shader nodes,")
        print("PackagedShader with MTLX language and ComposedShader with GLSL language, and each was appended ")
        print("to the 'shaders' field of an Appearance node.")

        # Write GLSL shader language files to project directory export location for shaders
        defines, x3dFields, surfComp = rkMat.getX3DShaderFieldNames(matXSS.name())
        #x3dFieldValues, matXDocName, matXShader = rkMat.saveGLSLFiles(glslFragPath, glslVertPath, self.relMatXDocPaths, cmds.getAttr(matXSS.name() + ".ufePath"), defines, x3dFields)
        x3dFieldValues, matXDocName, matXShader = rkMat.saveGLSLFiles(glslFragPath, glslVertPath, self.actMatXDocPaths, cmds.getAttr(matXSS.name() + ".ufePath"), defines, x3dFields)
        print("GLSL Frag and Vert files for Maya Shader " + matXSS.name() + " were saved to:\n    " + glslFragPath + "\n    " + glslVertPath)
        
        # Dictionary that holds Shader Field tag information
        # 
        fTags = {}
        rkMat.getShaderFieldTags(fTags, x3dFields, x3dFieldValues, surfComp)
        
        # Add a PackagedShader using the MaterialX shader document
        pShader = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PackagedShader", matXSS.name() + "_PkSdr")
        if pShader[0] == False:
            shader = pShader[1]
            
            # Set Shader Language to MaterialX XML
            shader.language = "MTLX"
            
            #Data URI's not implemented for MaterialXDocuments
            isDataUri, pkUrl = self.rkint.getMaterialXDocURLs(matXExportPath, self.rkMatXPath, matXDocName, matXShader)
            shader.url = pkUrl
            if isDataUri == True:
                print("PackagedShader URL Field was NOT exported as a dataURI. RawKee does not export shader files as DataURIs.")

            for key,value in fTags.items():
                fChop = value.split(',')
                fieldName  = key
                fieldType  = fChop[0]
                fieldAType = fChop[1]
                fieldValue = fChop[2]
                newField = self.generateFields(fieldName, fieldType, fieldAType)
                
                if fieldType == "SFNode":
                    if len(fChop) == 4:
                        shaderTexture = rkMat.getUFEConnectedTextureCmpd(surfComp, fieldName)
                        if shaderTexture:
                            pkgFields.append(newField)
                            appTexture.append(shaderTexture)
                        else:
                            print("PackagedShader: " + fieldName + " texture was not found.")
                    else:
                        pass

                else:
                    newField.value = fieldValue

                nodeField = getattr(shader, "field")
                nodeField.append(newField)
        
        cShader = self.trv.processBasicNodeAddition(x3dAppearance, cField, "ComposedShader", matXSS.name() + "_CpSdr")
        if cShader[0] == False:
            shader = cShader[1]
            
            # Set Shader Language to OpenGL
            shader.language = "GLSL"
            
            # Setup the FRAGMENT ShaderPart
            fragPart = self.trv.processBasicNodeAddition(shader, "parts", "ShaderPart", matXSS.name() + "_CpSdr_Frag")
            if fragPart[0] == False:
                frag = fragPart[1]

                isFragUri, fgUrl = self.rkint.getFragmentURLs(glslFragFile, self.rkMatXPath)
                frag.url = fgUrl
                if isFragUri == True:
                    print("Frag ShaderPart URL Field was NOT exported as a dataURI. RawKee does not export shader files as DataURIs.")
                    
                frag.type = "FRAGMENT"

            # Setup the VERTEX ShadePart
            vertPart = self.trv.processBasicNodeAddition(shader, "parts", "ShaderPart", matXSS.name() + "_CpSdr_Vert")
            if vertPart[0] == False:
                vert = vertPart[1]

                isVertUri, vtUrl = self.rkint.getVertexURLs(glslVertFile, self.rkMatXPath)
                vert.url = vtUrl
                if isVertUri == True:
                    print("Vert ShaderPart URL Fieldwas NOT exported as a dataURI. RawKee does not export shader files as DataURIs.")
                    
            # Populate the Shader's "field" values... images are delayed export.
            for key,value in fTags.items():
                fChop = value.split(',')
                fieldName  = key
                fieldType  = fChop[0]
                fieldAType = fChop[1]
                fieldValue = fChop[2]
                newField = self.generateFields(fieldName, fieldType, fieldAType)
                
                if fieldType == "SFNode":
                    if len(fChop) == 4:
                        shaderTexture = rkMat.getUFEConnectedTextureCmpd(surfComp, fieldName)
                        if shaderTexture:
                            cmpFields.append(newField)
                            #ignoreTT = self.processMatXTexture(shaderTexture, x3dAppearance, newField, "children", matchedSets, textureTransforms, ignoreTT, isX3DOM)
                        else:
                            print("ComposedShader: " + fieldName + " texture was not found.")
                    else:
                        pass

                else:
                    newField.value = fieldValue

                nodeField = getattr(shader, "field")
                nodeField.append(newField)

        self.addTextureToAppearance(x3dAppearance, appTexture, matchedSets, textureTransforms, ignoreTT, isX3DOM)
        atl = len(appTexture)
        for i in range(atl):
            ignoreTT = self.processMatXTexture(appTexture[i], x3dAppearance, pkgFields[i], "children", matchedSets, textureTransforms, ignoreTT, isX3DOM)
            ignoreTT = self.processMatXTexture(appTexture[i], x3dAppearance, cmpFields[i], "children", matchedSets, textureTransforms, ignoreTT, isX3DOM)

                
        rkMat.attachMatXTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)



    def processUSDPreview_PhysicalMaterial(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        pMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterialExt", material.name()) # marker
        if pMat[0] == False:
            physMat = pMat[1]

            ignoreTT          = False
            textureTransforms = []

            colorStore = {}
            usePrev = 3
            rkMat.getAdvBaseColorAndOcclusionTextures(material, colorStore, usePrev)

            ########################################################
            # Get BaseTexture
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                #mappingName = matchedSets.get(baseTexture.name(), "")
                #self.processTexture(baseTexture, physMat, "baseTexture", mappingName, textureTransforms)
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)
            else:
                bc = cmds.getAttr(material.name() + ".diffuseColor")[0]
                physMat.baseColor = self.getSFColor(bc[0], bc[1], bc[2])
                
            #######################################################
            # Get EmissiveTexture
            emissConn = material.findPlug("emissiveColor", True)
            emsTexture = self.findTextureFromPlug(emissConn)
            if emsTexture:
                ignoreTT = self.processTexture(emsTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                eColor = cmds.getAttr(material.name() + ".emissiveColor")[0]
                physMat.emissiveColor = self.getSFColor(eColor[0], eColor[1], eColor[2])

            ######################################################
            # Get Normal Map
            normConn    = material.findPlug("normal", True)
            normTexture = self.findTextureFromPlug(normConn)
            if normTexture:
                ignoreTT = self.processTexture(normTexture, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)
            

            #####################################################
            # Transparency
            x3dAppearance.alphaMode = "MASK"
            x3dAppearance.alphaCutoff = cmds.getAttr(material.name() + ".opacityThreshold")
            
            opVals = cmds.getAttr(material.name() + ".opacity")[0]
            opAvg  = (opVals[0] + opVals[1] + opVals[2]) / 3
            physMat.transparency = 1 - opAvg
            
            # Decide whether to process with Specular Workflow
            isSpcw = cmds.getAttr(material.name() + ".useSpecularWorkflow")
            metallic = 1.0
            metalTexture   = None
            
            if isSpcw == True:
                metallic = 0.0
                #####################################################################
                # Get SpecularColor values
                spcBna = self.trv.processBasicNodeAddition(physMat, "extensions", "SpecularMaterialExtension", physMat.DEF + "_SpecME")
                if spcBna[0] == False:
                    spcBna[1].specular = 1.0
                    
                    specConn = material.findPlug("specularColor", True)
                    specTexture = self.findTextureFromPlug(specConn)
                    if specTexture:
                        # Check to see if this file has an Alpha channel, if it does add the specularTexture value.
                        iPath = cmds.getAttr(specTexture.name() + ".fileTextureName")
                        img = aom.MImage()
                        img.readFromFile(iPath)
                        if img.depth() == 4:
                            ignoreTT = self.processTexture(specTexture, x3dAppearance, spcBna[1], "specularTexture", matchedSets, textureTransforms, ignoreTT)
                        ignoreTT = self.processTexture(specTexture, x3dAppearance, spcBna[1], "specularColorTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.metallic = metallic
                
            else:
                #####################################################################
                # Get Metallic values
                metalConn    = material.findPlug("metallic", True)
                metalTexture = self.findTextureFromPlug(metalConn)
                if not metalTexture:
                    metallic = cmds.getAttr(material.name() + ".metallic")
                physMat.metallic = metallic
                    
                #####################################################################
                # Get IOR values
                iorBna = self.trv.processBasicNodeAddition(physMat, "extensions", "IORMaterialExtension", physMat.DEF + "_IORME")
                if iorBna[0] == False:
                    iorBna[1].indexOfRefraction = cmds.getAttr(material.name() + ".ior")

            #####################################################################
            # Get Roughness values
            roughConn    = material.findPlug("roughness", True)
            roughTexture = self.findTextureFromPlug(roughConn)
            
            # Assumes that the metalTexture and the roughTexture nodes ar the same kTexture2d node
            if metalTexture:
                ignoreTT = self.processTexture(metalTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            elif roughTexture:
                ignoreTT = self.processTexture(roughTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)

            #####################################################
            # PBR Occlusion
            occlTexture = colorStore.get("occlusionTexture", None)
            if occlTexture:
                ignoreTT = self.processTexture(occlTexture, x3dAppearance, physMat, "occluisionTexture", matchedSets, textureTransforms, ignoreTT)
            else:
                physMat.occlusionStrength = cmds.getAttr(material.name() + ".occlusion")
                
            ####################################################
            # Clearcoat    
            coaBna = self.trv.processBasicNodeAddition(physMat, "extensions", "ClearcoatMaterialExtension", physMat.DEF + "_CoatME")
            if coaBna[0] == False:
                coatConn = material.findPlug("clearcoat")
                coatTexture = self.findTextureFromPlug(coatConn)
                if coatTexture:
                    ignoreTT = self.processTexture(coatTexture, x3dAppearance, coaBna[1], "clearcoatTexture", matchedSets, textureTransforms, ignoreTT)
                    coaBna[1].clearcoat = 1.0
                else:
                    coaBna[1].clearcoat = cmds.getAttr(material.name() + ".clearcoat")
                    
                cRouConn = material.findPlug("clearcoatRoughness")
                cRouTexture = self.findTextureFromPlug(cRouConn)
                if cRouTexture:
                    ignoreTT = self.processTexture(cRouTexture, x3dAppearance, coaBna[1], "clearcoatRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
                    coaBna[1].roughness = 1.0
                else:
                    coaBna[1].roughness = cmds.getAttr(material.name() + ".clearcoatRoughness")
            
            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    def processBlinn_PhysicalMaterial(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        pMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterial", material.name())
        if pMat[0] == False:
            physMat = pMat[1]
            
            ignoreTT          = False
            textureTransforms = []

            colorStore = {}

            rkMat.getLegacyBaseColorAndOcclusionTextures(material, colorStore)

            # Get BaseTexture
            hasBaseTexture = False
            diffuse = cmds.getAttr(material.name() + ".diffuse")
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.baseColor = (diffuse, diffuse, diffuse)
                hasBaseTexture = True
            else:
                bc = cmds.getAttr(material.name() + ".color")[0]
                physMat.baseColor = (bc[0] * diffuse, bc[1] * diffuse, bc[2] * diffuse)
                
            #######################################################
            # Get EmissiveTexture
            emissConn = material.findPlug("incandescence", True)
            emsTexture = self.findTextureFromPlug(emissConn)
            if emsTexture:
                ignoreTT = self.processTexture(emsTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                eColor = cmds.getAttr(material.name() + ".incandescence")[0]
                physMat.emissiveColor = self.getSFColor(eColor[0], eColor[1], eColor[2])

            ######################################################
            # Get Normal Map
            normConn    = material.findPlug("normalCamera", True)
            normTexture = self.findTextureFromPlug(normConn)
            if normTexture:
                ignoreTT = self.processTexture(normTexture, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)
            
            normAdj = self.findNormScaleNode(normConn)
            if normAdj:
                if normAdj.typeName == "aiNormalMap":
                    physMat.normalScale = cmds.getAttr(normAdj.name() + ".strength")
                    
                elif normAdj.typeName == "bump2d":
                    nsValue = cmds.getAttr(normAdj.name() + ".bumpDepth")
                    if nsValue < 0.01:
                        nsValue = 0.01
                    physMat.normalScale = nsValue
            
            #####################################################
            # PBR Metallic
            metalConn     = material.findPlug("reflectivity", True)
            metalTexture = self.findTextureFromPlug(metalConn)
            if metalTexture:
                physMat.metallic = 1.0
            else:
                spColor      = cmds.getAttr(material.name() + ".specularColor")[0]
                reflectivity = cmds.getAttr(material.name() + ".reflectivity")
                
                # Simple saturation check for Specular Tint
                max_s = max(spColor)
                min_s = min(spColor)
                saturation = (max_s - min_s) / max_s if max_s > 0 else 0

                if saturation > 0.1 and diffuse < 0.5:
                    physMat.metallic = reflectivity
                else:
                    physMat.metallic = 0.0

            #####################################################
            # PBR Roughness
            roughConn    = material.findPlug("eccentricity", True)
            roughTexture = self.findTextureFromPlug(roughConn)
            if roughTexture:
                physMat.roughness = 1.0
            else:
                physMat.roughness = cmds.getAttr(material.name() + ".eccentricity")
                # Because of Antialiasing issues
                if physMat.roughness == 0.0:
                    physMat.roughness = 0.001
                    
            if metalTexture:
                ignoreTT = self.processTexture(metalTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            elif roughTexture:
                ignoreTT = self.processTexture(roughTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            
            #####################################################
            # PBR Occlusion
            oTex = colorStore.get("occlusionTexture", None)
            if oTex:
                ignoreTT = self.processTexture(oTex, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT)
            
            # Occlusion Strength
            physMat.occlusionStrength = cmds.getAttr(material.name() + ".specularRollOff")

            # Get Transparency
            transp = cmds.getAttr(material.name() + ".transparency")[0]
            t = (transp[0] + transp[1] + transp[2]) / 3
            physMat.transparency = t
            
            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    def processStandard_PhysicalMaterial(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        pMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterialExt", material.name())
        if pMat[0] == False:
            physMat = pMat[1]

            ignoreTT          = False
            textureTransforms = []

            colorStore = {}
            
            stand = 0
            rkMat.getAdvBaseColorAndOcclusionTextures(material, colorStore, stand)

            ####################################################
            # Get BaseTexture
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)

            bc = cmds.getAttr(material.name() + ".baseColor")[0]
            physMat.baseColor = self.getSFColor(bc[0], bc[1], bc[2])
            
            ####################################################
            # Get Emissive Values
            emissConn    = material.findPlug("emissionColor", True)
            emissTexture = self.findTextureFromPlug(emissConn)
            if emissTexture:
                ignoreTT = self.processTexture(emissTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                ec = cmds.getAttr(material.name() + ".emissionColor")[0]
                physMat.emissiveColor = self.getSFColor(ec[0], ec[1], ec[2])

            # Only Materaial Extension Used
            esBna = self.trv.processBasicNodeAddition(physMat, "extensions", "EmissiveStrengthMaterialExtension", physMat.DEF + "_ESME")
            if esBna[0] == False:
                esBna[1].emissiveStrength = cmds.getAttr(material.name() + ".emission")
            
            ######################################################
            # Get Normal Map
            normConn = material.findPlug("normalCamera", True)
            normTex = self.findTextureFromPlug(normConn)
            if normTex:
                ignoreTT = self.processTexture(normTex, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)
            
            normAdj = self.findNormScaleNode(normConn)
            if normAdj:
                if normAdj.typeName == "aiNormalMap":
                    physMat.normalScale = cmds.getAttr(normAdj.name() + ".strength")
                elif normAdj.typeName == "bump2d":
                    nsValue = cmds.getAttr(normAdj.name() + ".bumpDepth")
                    if nsValue < 0.0:
                        nsValue = 0.0
                    physMat.normalScale = nsValue

            #####################################################################
            # Analyze for existing shared Metallic, Roughness, Occlusion texture:
            #
            hasMetal = False
            hasRough = False
            hasOccl  = False
            metalRoughSame = False
            occlIsSame     = False

            metalConn    = material.findPlug("metalness", True)
            metalTexture = self.findTextureFromPlug(metalConn)
            
            roughConn    = material.findPlug("specularRoughness", True)
            roughTexture = self.findTextureFromPlug(roughConn)
            
            if metalTexture:
                ignoreTT = self.processTexture(metalTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            elif roughTexture:
                ignoreTT = self.processTexture(roughTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
                
            occlTexture = colorStore.get("occlusionTexture", False)
            if occlTexture:
                ignoreTT = self.processTexture(occlTexture, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT)
            
            ####################################################
            # PBR Occlusion
            #oTex = mroStore.get("occlusionTexture", False)
            #if oTex:
            #    occImage = aom.MImage()
            #    occImage.readFromTextureNode(oTex, aom.MImage.kFloat)
            #    mro["red"] = occImage
            #    mroTexture["textTrans"] = rkMat.getTextureTransform(oTex)

            ####################################################
            # PBR Roughness
            if not roughTexture:
                physMat.roughness = cmds.getAttr(material.name() + ".specularRoughness")

            # For Antialiasing Issues
            if physMat.roughness == 0.0:
                physMatroughness = 0.001
            
            if not metalTexture:
                physMat.metallic = cmds.getAttr(material.name() + ".metalness")
            
            
            #####################################################################
            # Ignore Transmission Info to set Transparency
            opVals = cmds.getAttr(material.name() + ".opacity")[0]
            opAvg  = (opVals[0] + opVals[1] + opVals[2]) / 3
            physMat.transparency = 1 - opAvg
            
            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    # Assumes that the ShaderFX interface is not used.
    def processStingrayPBS_PhysicalMaterial(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        pMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterialExt", material.name())
        if pMat[0] == False:
            physMat = pMat[1]

            ignoreTT          = False
            textureTransforms = []
            
            colorStore = {}
            
            stingray = 4
            rkMat.getAdvBaseColorAndOcclusionTextures(material, colorStore, stingray)

            ####################################################
            # Get BaseTexture
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)

            bc = cmds.getAttr(material.name() + ".baseColor")[0]
            physMat.baseColor = self.getSFColor(bc[0], bc[1], bc[2])
            
            ####################################################
            # Get metallic, roughness values.
            # Just assume that transparency is default value 0.0
            # and occlusionStrength is default value of 1.0
            physMat.metallic  = cmds.getAttr(material.name() + ".metallic" )
            physMat.roughness = cmds.getAttr(material.name() + ".roughness")
            if physMat.roughness == 0.0:
                physMat.roughness = 0.001
            
            ####################################################
            # Get Emissive Values
            emissConn    = material.findPlug("TEX_emissive_map", True)
            emissTexture = self.findTextureFromPlug(emissConn)
            if emissTexture:
                ignoreTT = self.processTexture(emissTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                ec = cmds.getAttr(material.name() + ".emissive")[0]
                physMat.emissiveColor = self.getSFColor(ec[0], ec[1], ec[2])

            # Only Materaial Extension Used
            esBna = self.trv.processBasicNodeAddition(physMat, "extensions", "EmissiveStrengthMaterialExtension", physMat.DEF + "_ESME")
            if esBna[0] == False:
                esBna[1].emissiveStrength = cmds.getAttr(material.name() + ".emissiveIntensity")
            
            ######################################################
            # Get Normal Map
            normConn = material.findPlug("TEX_normal_map", True)
            normTex = self.findTextureFromPlug(normConn)
            if normTex:
                ignoreTT = self.processTexture(normTexture, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)

            #####################################################################
            # Analyze for existing shared Metallic, Roughness, Occlusion texture:
            #
            metalConn    = material.findPlug("TEX_metallic_map", True)
            metalTexture = self.findTextureFromPlug(metalConn)
            
            roughConn    = material.findPlug("TEX_roughness_map", True)
            roughTexture = self.findTextureFromPlug(roughConn)
                    
            if metalTexture:
                ignoreTT = self.processTexture(metalTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            elif roughTexture:
                ignoreTT = self.processTexture(roughTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
                
            occlTexture = colorStore.get("occlusionTexture", False)
            if occlTexture:
                ignoreTT = self.processTexture(occlTexture, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT)

            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)


    def processOpenPBRSurface(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        pMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "PhysicalMaterialExt", material.name())
        if pMat[0] == False:
            physMat           = pMat[1]
            
            ignoreTT          = False
            textureTransforms = []

            colorStore = {}
            openPBR = 2
            rkMat.getAdvBaseColorAndOcclusionTextures(material, colorStore, openPBR)

            # Get BaseTexture
            baseTexture = colorStore.get("baseTexture", False)
            if baseTexture:
                ignoreTT = self.processTexture(baseTexture, x3dAppearance, physMat, "baseTexture", matchedSets, textureTransforms, ignoreTT)
            else:
                bc = cmds.getAttr(material.name() + ".baseColor")[0]
                physMat.baseColor = self.getSFColor(bc[0], bc[1], bc[2])
                
            # Get EmissiveTexture
            emissConn    = material.findPlug("emissionColor", True)
            emissTexture = self.findTextureFromPlug(emissConn)
            if emissTexture:
                ignoreTT = self.processTexture(emissTexture, x3dAppearance, physMat, "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                physMat.emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                ec = cmds.getAttr(material.name() + ".emissionColor")[0]
                physMat.emissiveColor = self.getSFColor(ec[0], ec[1], ec[2])

            esBna = self.trv.processBasicNodeAddition(physMat, "extensions", "EmissiveStrengthMaterialExtension", physMat.DEF + "_ESME")
            if esBna[0] == False:
                luminance = float(cmds.getAttr(material.name() + ".emissionLuminance"))
                esBna[1].emissiveStrength = luminance / 1000.0

            ###################################################################################################
            # Transmission and Transparency
            opacity = cmds.getAttr(material.name() + ".geometryOpacity")
            tWeight = cmds.getAttr(material.name() + ".transmissionWeight")
            sWeight = cmds.getAttr(material.name() + ".subsurfaceWeight")
            isTWall = cmds.getAttr(material.name() + ".geometryThinWalled")
            
            if tWeight == 0.0:
                physMat.transparency = 1 - opacity # This is always 0.0 since we are using the TransmissionMaterialExtension
            else:
                # TransmissionMaterialExtension
                trBna = self.trv.processBasicNodeAddition(physMat, "extensions", "TransmissionMaterialExtension", physMat.DEF + "_TRME")
                if trBna[0] == False:
                    trBna[1].transmission = cmds.getAttr(material.name() + ".transmissionWeight")
                    #The Transmission value is stored in the R channel of the Transmission texture.
                    transConn    = material.findPlug("transmissionColor", True)
                    transTexture = self.findTextureFromPlug(transConn)
                    if transTexture:
                        ignoreTT = self.processTexture(transTexture, x3dAppearance, trBna[1], "transmissionTexture", matchedSets, textureTransforms, ignoreTT)
                        hasTrTexture = True
                        
            if isTWall == True:
                dtBna = self.trv.processBasicNodeAddition(physMat, "extensions", "DiffuseTransmissionMaterialExtension", physMat.DEF + "_DTME")
                if dtBna[0] == False:
                    dtBna[1].diffuseTransmission = cmds.getAttr(material.name() + ".subsurfaceWeight")
                    subsConn = material.findPlug("subsurfaceColor")
                    subsTexture = self.findTextureFromPlug(subsConn)
                    if subsTexture:
                        ignoreTT = self.processTexture(subsTexture, x3dAppearance, dtBna[1], "diffuseTransmissionColorTexture", matchedSets, textureTransforms, ignoreTT)
                        
                        try:
                            iPath = cmds.getAttr(subsTexture.name() + ".fileTextureName")
                            img = aom.MImage()
                            img.readFromFile(iPath)
                            if img.depth() == 4:
                                ignoreTT = self.processTexture(subsTexture, x3dAppearance, dtBna[1], "diffuseTransmissionTexture", matchedSets, textureTransforms, ignoreTT)
                        except:
                            pass
            else:
                # VolumeMaterialExtension
                vmBna = self.trv.processBasicNodeAddition(physMat, "extensions", "VolumeMaterialExtension", physMat.DEF + "_VLME")
                if vmBna[0] == False:
                    #The Thickness value is stored in the G channel of the Transmission texture.
                    myThickness = 1.0
                    thickConn    = material.findPlug("transmissionDepth", True)
                    thickTexture = self.findTextureFromPlug(thickConn)
                    if thickTexture:
                        ignoreTT = self.processTexture(thickTexture, x3dAppearance, vmBna[1], "thicknessTexture", matchedSets, textureTransforms, ignoreTT)
                    else:
                        myThickness = cmds.getAttr(material.name() + ".transmissionDepth")

                    # Get thickness
                    vmThickness = tWeight # More like Water
                    if sWeight > tWeight: # More like Skin/Wax
                        vmThickness = sWeight
                    vmBna[1].thickness = vmThickness * myThickness
                    
                    subWeight = cmds.getAttr(material.name() + ".subsurfaceWeight")
                    if subWeight > 0.0:
                        # Get Attenuation Color
                        ac = cmds.getAttr(material.name() + ".subsurfaceRadiusScale")[0]
                        
                        # Adjust PhysicalMaterial baseColor
                        bc = cmds.getAttr(material.name() + ".subsurfaceColor")[0]
                        bcc = physMat.baseColor
                        physMat.baseColor = self.getSFColor( (bcc[0] * (1.0 - subWeight)) + (bc[0] * subWeight), (bcc[1] * (1.0 - subWeight)) + (bc[1] * subWeight), (bcc[2] * (1.0 - subWeight)) + (bc[2] * subWeight) )
                        # X3D baseColor = (base_color x (1.0 - subsurface_weight)) + (subsurface_color x subsurface_weight))

                        vmBna[1].attenuationColor    = self.getSFColor(ac[0], ac[1], ac[2])
                        vmBna[1].attenuationDistance = cmds.getAttr(material.name() + ".subsurfaceRadius")
                        
                # VolumeScatterMaterialExtension
                vmsBna = self.trv.processBasicNodeAddition(physMat, "extensions", "VolumeScatterMaterialExtension", physMat.DEF + "_VSME")
                if vmsBna[0] == False:
                    vmsBna[1].multiscatterColor = cmds.getAttr(material.name() + ".transmissionScatter")[0]
                    vmsBna[1].scatterAnisotropy = cmds.getAttr(material.name() + ".transmissionScatterAnisotropy")

                # DispersionMaterialExtension
                dmBna = self.trv.processBasicNodeAddition(physMat, "extensions", "DispersionMaterialExtension", physMat.DEF + "_DSPME")
                if dmBna[0] == False:
                    noScaleDisp = 20/cmds.getAttr(material.name() + ".transmissionDispersionAbbeNumber")
                    dmBna[1].dispersion = noScaleDisp * cmds.getAttr(material.name() + ".transmissionDispersionScale")
                
            
            ######################################################
            # Get Normal Map
            normConn = material.findPlug("normalCamera", True)
            normTex = self.findTextureFromPlug(normConn)
            if normTex:
                ignoreTT = self.processTexture(normTex, x3dAppearance, physMat, "normalTexture", matchedSets, textureTransforms, ignoreTT)
            
            normAdj = self.findNormScaleNode(normConn)
            if normAdj:
                if normAdj.typeName == "aiNormalMap":
                    physMat.normalScale = cmds.getAttr(normAdj.name() + ".strength")
                elif normAdj.typeName == "bump2d":
                    nsValue = cmds.getAttr(normAdj.name() + ".bumpDepth")
                    if nsValue < 0.0:
                        nsValue = 0.0
                    physMat.normalScale = nsValue

            #####################################################################
            # Analyze for existing shared Metallic, Roughness, Occlusion texture:
            #
            hasRough     = False
            metalConn    = material.findPlug("baseMetalness", True)
            metalTexture = self.findTextureFromPlug(metalConn)
            
            roughConn    = material.findPlug("specularRoughness", True)
            roughTexture = self.findTextureFromPlug(roughConn)
            if roughTexture:
                hasRough = True

            if metalTexture:
                ignoreTT = self.processTexture(metalTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
            elif roughTexture:
                ignoreTT = self.processTexture(roughTexture, x3dAppearance, physMat, "metallicRoughnessTexture", matchedSets, textureTransforms, ignoreTT)

            occlTexture = colorStore.get("occlusionTexture", False)
            if occlTexture:
                ignoreTT = self.processTexture(occlTexture, x3dAppearance, physMat, "occlusionTexture", matchedSets, textureTransforms, ignoreTT)

            #######################################################################
            # Evaluate metallic and Specular Values
            if not metalTexture:
                physMat.metallic = cmds.getAttr(material.name() + ".baseMetalness")
                
            spcBna = self.trv.processBasicNodeAddition(physMat, "extensions", "SpecularMaterialExtension", physMat.DEF + "_SpecME")
            if spcBna[0] == False:
                spcBna[1].specular = cmds.getAttr(material.name() + ".specularWeight")
                
                specConn = material.findPlug("specularColor", True)
                specTexture = self.findTextureFromPlug(specConn)
                if specTexture:
                    ignoreTT = self.processTexture(specTexture, x3dAppearance, spcBna[1], "specularColorTexture", matchedSets, textureTransforms, ignoreTT)
                    try:
                        iPath = cmds.getAttr(specTexture.name() + ".fileTextureName")
                        img = aom.MImage()
                        img.readFromFile(iPath)
                        if img.depth() == 4:
                            ignoreTT = self.processTexture(specTexture, x3dAppearance, spcBna[1], "specularTexture", matchedSets, textureTransforms, ignoreTT)
                    except:
                        pass
                else:
                    spCol = cmds.getAttr(material.name() + ".specularColor")[0]
                    spcBna[1].specularColor = self.getSFColor(spCol[0], spCol[1], spCol[2])
            
            iorBna = self.trv.processBasicNodeAddition(physMat, "extensions", "IORMaterialExtension", physMat.DEF + "_IORME")
            if iorBna[0] == False:
                iorBna[1].indexOfRefraction = cmds.getAttr(material.name() + ".specularIOR")
                
            aniso = cmds.getAttr(material.name() + ".specularRoughnessAnisotropy")
            if aniso > 0.0:
                aniBna = self.trv.processBasicNodeAddition(physMat, "extensions", "AnisotropyMaterialExtension", physMat.DEF + "_AniME")
                if aniBna[0] == False:
                    aniBna[1].anisotropyStrength = aniso
                    if cmds.objExists(material.name() + ".tangentUCamera"):
                        tangConn = material.findPlug("tangentUCamera")
                        tangTexture = self.findTextureFromPlug(tangConn)
                        if tangTexture:
                            ignoreTT = self.processTexture(tangTexture, x3dAppearance, aniBna[1], "anisotropyTexture", matchedSets, textureTransforms, ignoreTT)
                    elif cmds.objExists(material.name() + ".specularAnisotropyRotation"):
                        aniBna[1].rotation = cmds.getAttr(material.name()  + ".specularAnisotropyRotation")
            
            #################################################### # marker
            # Clearcoat    
            coatWeight = cmds.getAttr(material.name() + ".coatWeight")
            if coatWeight > 0.0:
                coaBna = self.trv.processBasicNodeAddition(physMat, "extensions", "ClearcoatMaterialExtension", physMat.DEF + "_CoatME")
                if coaBna[0] == False:
                    coaBna[1].clearcoat = coatWeight
                    coatConn = material.findPlug("coatColor")
                    coatTexture = self.findTextureFromPlug(coatConn)
                    if coatTexture:
                        ignoreTT = self.processTexture(coatTexture, x3dAppearance, coaBna[1], "clearcoatTexture", matchedSets, textureTransforms, ignoreTT)
                    cRouConn = material.findPlug("coatRoughness")
                    cRouTexture = self.findTextureFromPlug(cRouConn)
                    if cRouTexture:
                        ignoreTT = self.processTexture(cRouTexture, x3dAppearance, coaBna[1], "clearcoatRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
                    else:
                        coaBna[1].roughness = cmds.getAttr(material.name() + ".coatRoughness")
                    
                    # Get Coat Normal Map
                    cNorConn = material.findPlug("geometryCoatNormal", True)
                    cNorTexture = self.findTextureFromPlug(cNorConn)
                    if cNorTexture:
                        ignoreTT = self.processTexture(cNorTexture, x3dAppearance, coaBna[1], "clearcoatNormalTexture", matchedSets, textureTransforms, ignoreTT)
                            
            ######################################################################
            # Fuzz / Sheen Weight
            fuzz = cmds.getAttr(material.name() + ".fuzzWeight")
            if fuzz > 0.0:
                fuzBna = self.trv.processBasicNodeAddition(physMat, "extensions", "SheenMaterialExtension", physMat.DEF + "_SheenME")
                if fuzBna[0] == False:
                    fColConn = material.findPlug("fuzzColor", True)
                    fColTexture = self.findTextureFromPlug(fColConn)
                    if fColTexture:
                        ignoreTT = self.processTexture(fColTexture, x3dAppearance, fuzBna[1], "sheenColorTexture", matchedSets, textureTransforms, ignoreTT)
                    else:
                        fCol = cmds.getAttr(material.name() + ".fuzzColor")[0]
                        fuzBna[1].sheenColor = self.getSFColor(fCol[0] * fuzz, fCol[1] * fuzz, fCol[2] * fuzz)

                    fRouConn = material.findPlug("fuzzRoughness", True)
                    fRouTexture = self.findTextureFromPlug(fRouConn)
                    if fRouTexture:
                        ignoreTT = self.processTexture(fRouTexture, x3dAppearance, fuzBna[1], "sheenRoughnessTexture", matchedSets, textureTransforms, ignoreTT)
                    else:
                        fuzBna[1].sheenRoughenss = cmds.getAttr(material.name() + ".fuzzRoughness")
                        
                    # TODO - Find a way to deal with Fuzz/Sheen AOVs
                    
            ##############################################################
            # Thickness / Iridescence
            iridConn      = material.findPlug("thinFilmWeight", True)
            iridTexture   = self.findTextureFromPlug(iridConn)
            iridWeight    = 1.0
            iridThickness = 1.0
            hasIrid = False
            if iridTexture:
                hasIrid = True
            else:
                iridWeight = cmds.getAttr(material.name() + ".thinFilmWeight")
                
            iThkConn = material.findPlug("thinFilmThickness", True)
            iThkTexture = self.findTextureFromPlug(iThkConn)
            if iThkTexture:
                hasIrid = True
            else:
                iridThickness = cmds.getAttr(material.name() + ".thinFilmThickness")
            
            if iridWeight * iridThickness > 0.0:
                hasIrid = True
                
            if hasIrid == True:
                iriBna = self.trv.processBasicNodeAddition(physMat, "extensions", "IridescenceMaterialExtension", physMat.DEF + "_IridME") 
                if iriBna[0] == False:
                    if iridTexture:
                        ignoreTT = self.processTexture(iridTexture, x3dAppearance, iriBna[1], "iridescenceTexture", matchedSets, textureTransforms, ignoreTT)
                    if iThkTexture:
                        ignoreTT = self.processTexture(iThkTexture, x3dAppearance, iriBna[1], "iridescenceTexture", matchedSets, textureTransforms, ignoreTT)
                    iriBna[1].iridescence = iridWeight
                    iriBna[1].iridescenceThicknessMinimum  = iridThickness * 1000
                    iriBna[1].iridescenceThicknessMaximum  = iridThickness * 1000
                    iriBna[1].iridescenceIndexOfRefraction = cmd.getAttr(material.name() + ".thinFilmIOR")

            ##########################################################
            # Set PBR Roughness value.
            if hasRough == True:
                physMat.roughness == 1.0
            else:
                physMat.roughness = cmds.getAttr(material.name() + ".specularRoughness")
            
            # To avoid Aliasing problems.
            if physMat.roughness == 0.0:
                physMat.roughness = 0.001

            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)
        


    def processUnlit_Material(self, matchedSets, material, x3dAppearance, mTextureNodes, mTextureFields, mTextureParents, retPlace2d, cField):
        unlitMat = self.trv.processBasicNodeAddition(x3dAppearance, cField, "UnlitMaterial", material.name())
        if unlitMat[0] == False:
            ignoreTT          = False
            textureTransforms = []
            
            unlMat = 0 # aiFlat material
            if material.typeName == "surfaceShader":
                unlMat = 1
            
            emissAttr = "outColor"
            if unlMat < 1: emissAttr = "color"
            
            emissConn = material.findPlug(emissAttr, True)
            emsTex    = self.findTextureFromPlug(emissConn)
            if emsTex:
                ignoreTT = self.processTexture(emsTex, x3dAppearance, unlitMat[1], "emissiveTexture", matchedSets, textureTransforms, ignoreTT)
                
                unlitMat[1].emissiveColor = self.getSFColor(1.0, 1.0, 1.0)
            else:
                eColor = cmds.getAttr(material.name() + "." + emissAttr)[0]
                unlitMat[1].emissiveColor = self.getSFColor(eColor[0], eColor[1], eColor[2])

            if unlMat < 1:
                normConn = material.findPlug("normalCamera", True)

                normTex = self.findTextureFromPlug(normConn)
                if normTex:
                    ignoreTT = self.processTexture(normText, x3dAppearance, unlitMat[1], "normalTexture", matchedSets, textureTransforms, ignoreTT)
                    
                normAdj = self.findNormScaleNode(normConn)
                if normAdj:
                    if normAdj.typeName == "aiNormalMap":
                        unlitMat[1].normalScale = cmds.getAttr(normAdj.name() + ".strength")
                    elif normAdj.typeName == "bump2d":
                        nsValue = cmds.getAttr(normAdj.name() + ".bumpDepth")
                        if nsValue < 0.0:
                            nsValue = 0.0
                        unlitMat[1].normalScale = nsValue
                
            if unlMat > 0:
                transp = mcmds.getAttr(material.name() + ".outTransparency")[0]
                unlitMat[1].transparency = (transp[0] + transp[1] + transp[2]) / 3
                
            # Check for GeneratedCubeMapTexture
            if ignoreTT == True:
                x3dAppearance.material = None
            else:
                rkMat.attachTextureTransforms(self.trv, self.rkint, textureTransforms, x3dAppearance)

    
    ##########################################################################
    # wmsm and wssm are always identity unless the geometry being exported
    # are for an HAnimHumanoid or a CGE Skin character.
    # wmsm (World Mesh Space Matrix)
    # wssm (World Skin Space Matrix)
    # vMat (vertex Matrix) is the multiplier for character/avatar coordinate vertices
    def processForGeometry(self, myMesh, x3dApp, shaders, meshComps, x3dParentNode, nodeName=None, cField="geometry", nodeType="IndexedFaceSet", index=0, gcOffset=0, gnOffset=0, gsharedCoord="", gsharedNormal="", isAvatar=False, adjMatrix=aom.MMatrix()):
        
        meshMP = 0
        if nodeName == None:
            nodeName = myMesh.name()

        depNode = aom.MFnDependencyNode(shaders[index])

        myUVSetNames = myMesh.getUVSetNames()
        
        if nodeType == "IndexedFaceSet" or nodeType == "CGEIndexedFaceSet":
            msList = aom.MSelectionList()
            msList.add(myMesh.name())
            tDagPath = msList.getDagPath(0)
            
            mIter = aom.MItMeshPolygon(tDagPath, meshComps[index])
            
            geomName = nodeName + "_IFS"
            if index > 1:
                geomName = geomName + "_" + str(index)
                
            bna = self.trv.processBasicNodeAddition(x3dParentNode, cField, nodeType, geomName)
            if bna[0] == False:
                # TODO: Future code for implementing 'attrib'

                ##### Add an X3D Coordiante Node
                
                #### use gsharedCoord if this is a mesh in an HAnimHumanoid
                if gsharedCoord != "":
                    coordbna = self.trv.processBasicNodeAddition(bna[1], "coord", "Coordinate", gsharedCoord)

                    # Using the MItMeshPolygon Iterator and the propoper sub-component
                    # this secion of the code builds the array of MFInt32 field of IndexedFaceSet
                    while not mIter.isDone():
                        #vertices = mIter.getVertices()
                        nVerts = mIter.polygonVertexCount()
                        for vIdx in range(nVerts):
                            mIdx = mIter.vertexIndex(vIdx)
                            bna[1].coordIndex.append(mIdx + gcOffset)
                        bna[1].coordIndex.append(-1)
                        mIter.next()
                        
                else:
                    ####################################
                    # Get a list of vertex index used
                    vertIdxList = []
                    
                    geoNameCoord = nodeName + "_Coord"
                    coordbna = self.trv.processBasicNodeAddition(bna[1], "coord", "Coordinate", geoNameCoord)
                    if coordbna[0] == False:
                        # TODO: Metadata processing
                        
                        # Multiplier to translate mesh verticies into character/avatar Model Space
                        sType=aom.MSpace.kWorld
                        if adjMatrix == aom.MMatrix() and isAvatar==False:
                            sType = aom.MSpace.kObject
                        else:
                            adjList = aom.MSelectionList()
                            adjList.add(myMesh.name())
                            adjMatrix = adjList.getDagPath(0).inclusiveMatrix() * adjMatrix.inverse()

                        # point field of Coordinate node
                        meshList = aom.MSelectionList()
                        meshList.add(myMesh.name())
                        newMesh = aom.MFnMesh(meshList.getDagPath(0))
                        
                        #points = myMesh.getFloatPoints(sType)
                        points = newMesh.getFloatPoints(sType)
                        #meshMP = len(points)
                        for point in points:
                            point = point * aom.MFloatMatrix(adjMatrix)
                            coordbna[1].point.append((point.x, point.y, point.z))
                
                        # Using the MItMeshPolygon Iterator and the propoper sub-component
                        # this secion of the code builds the array of MFInt32 field of IndexedFaceSet
                        while not mIter.isDone():
                            #vertices = mIter.getVertices()
                            nVerts = mIter.polygonVertexCount()
                            for vIdx in range(nVerts):
                                mIdx = mIter.vertexIndex(vIdx)
                                vertIdxFound = False
                                
                                ##################################
                                # Get a used vertex index list   #
                                ##################################
                                # for vil in vertIdxList:        #
                                #     if mIdx == vil:            #
                                #         vertIdxFound = True    #
                                # if vertIdxFound == False:      #
                                #     vertIdxList.append(mIdx)   #
                                ##################################
                                
                                bna[1].coordIndex.append(mIdx)
                            bna[1].coordIndex.append(-1)
                            mIter.next()
                    
                    ###############################
                    # Put list in order
                    # vertIdxList.sort()
                    
                    ####################################################################################
                    # Compile node weighting information here for CGESkin node use.
                    if nodeType == "CGEIndexedFaceSet":
                        self.collectCGESkinWeightsForMesh(newMesh, x3dParentNode)
                    
                #
                #
                #####
                '''
                    ciValue = 0
                    points = myMesh.getFloatPoints()
                    while not mIter.isDone():
                        verts = mIter.getVertices()
                        for vex in verts:
                            mPoint = points[vex]
                            coordbna[1].point.append((mPoint.x, mPoint.y, mPoint.z))
                            bna[1].coordIndex.append(ciValue)
                            ciValue += 1
                        bna[1].coordIndex.append(-1)
                        mIter.next()
                '''
                #####
                #
                #
                    
                ##### Add an X3DColorNode
                # Code for Adding a Color/ColorRGBA Node to the 'color' field of the IFS
                if   self.rkColorOpts == 0:
                    # Though not technically required, set
                    # colorPerVertex to True and then do nothing
                    # more with mesh colors because we are using
                    # the default values for IndexedFaceSet nodes
                    # where there is no color node.
                    bna[1].colorPerVertex = True
                elif self.rkColorOpts == 1 :
                    # Color per Face Values
                    bna[1].colorPerVertex = True
                    self.processForColorNode(myMesh, mIter, nodeName,     "Color", bna[1], idx=index)
                elif self.rkColorOpts == 2 :
                    # Color per Face Values
                    bna[1].colorPerVertex = True
                    self.processForColorNode(myMesh, mIter, nodeName, "ColorRGBA", bna[1], idx=index)
                elif self.rkColorOpts == 3 :
                    # Color per Face Values
                    bna[1].colorPerVertex = False
                    self.processForColorNode(myMesh, mIter, nodeName,     "Color", bna[1], cpv=False, idx=index)
                else:
                    bna[1].colorPerVertex = False
                    self.processForColorNode(myMesh, mIter, nodeName, "ColorRGBA", bna[1], cpv=False, idx=index)
                    
                
                ##### Set Crease Angle
                if self.rkNormalOpts == 1 or self.rkNormalOpts == 2 or self.rkNormalOpts == 3:
                    bna[1].creaseAngle = self.rkCreaseAngle

                ##### Set Norml Node, normalIndex, and normalPerVertex
                # if self.rkNormalOpts == 0:
                    # Then do nothing:
                    #    - Do not collect any normal data
                    #    - Do not set the crease angle
                    #    - Use the default normalPerVertex value, which is True
                    
                if self.rkNormalOpts == 1 or self.rkNormalOpts == 4:
                    # Normals Per Vertex Values
                    bna[1].normalPerVertex = True
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], idx=index, nOffset=gnOffset, sharedNormal=gsharedNormal)

                elif self.rkNormalOpts == 2 or self.rkNormalOpts == 5:
                    # Normals Per Face Values
                    bna[1].normalPerVertex = False
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], npv=False, idx=index, nOffset=gnOffset, sharedNormal=gsharedNormal)


                self.processForTextureMaps(myMesh, bna[1], x3dApp, shaders[index], geomName, mIter, index)


    def processForTextureMaps(self, myMesh, x3dGeometry, x3dApp, seObj, geomName, mIter, index):
        x3dParent = x3dGeometry
        if x3dApp.texture:
            if x3dApp.texture.NAME() == "GeneratedCubeMapTexture":
                genTC = self.trv.processBasicNodeAddition(x3dParent, "texCoord", "TextureCoordinateGenerator", geomName + "_GenTC")
                if genTC[0] == False:
                    genTC[1].mode = "SPHERE-REFLECT-LOCAL"
                    
                return

        # If a TextureCoordinateGenerator was NOT created, then export all the texture maps for this mesh.
        mapDict = self.getUsedUVSetDictionary(myMesh, seObj)
        
        redux = {}
        for key in mapDict:
            redux[mapDict[key]] = True

        myUVSetNames = []
        for key in redux:
            myUVSetNames.append(key)
        
        if len(myUVSetNames) > 0:
            
            tPolyVerts = 0
            mIter.reset()
            while not mIter.isDone():
                tPolyVerts += mIter.polygonVertexCount()
                mIter.next()
            
            texCoords = []
            for item in myUVSetNames:
                tpv = []
                for cval in range(tPolyVerts):
                    tpv.append((0.0, 0.0))
                texCoords.append(tpv)

            idxCount = 0
            mIter.reset()
            while not mIter.isDone():
                nVerts = mIter.polygonVertexCount()
                hasUV  = mIter.hasUVs()
                
                for vIdx in range(nVerts):#vertices:
                    mu = 0.0
                    mv = 0.0
                    
                    for t in range(len(myUVSetNames)):
                        if hasUV == True:
                            mu,mv = mIter.getUV(vIdx, myUVSetNames[t])
                        texCoords[t][idxCount] = (mu, mv)
                    
                    x3dGeometry.texCoordIndex.append(idxCount)
                    idxCount += 1
                x3dGeometry.texCoordIndex.append(-1)
                mIter.next()

            if  len(myUVSetNames) == 1:
                bnaMap = self.trv.processBasicNodeAddition(x3dParent, "texCoord", "TextureCoordinate", geomName + "_" + myUVSetNames[0] + "_" + str(index))
                if bnaMap[0] == False:
                    for ptx in texCoords[0]:
                        bnaMap[1].point.append(ptx)
                    bnaMap[1].mapping = myUVSetNames[0]
            elif len(myUVSetNames) > 1:
                bnaTXC = self.trv.processBasicNodeAddition(x3dParent, "texCoord", "MultiTextureCoordinate", geomName + "_MTC_" + str(index))
                if bnaTXC[0] == False:
                    x3dParent = bnaTXC[1]
                    for n in range(len(myUVSetNames)):
                        bnaMap = self.trv.processBasicNodeAddition(x3dParent, "texCoord", "TextureCoordinate", geomName + "_" + myUVSetNames[n] + "_" + str(index))
                        if bnaMap[0] == False:
                            for ptx in texCoords[n]:
                                bnaMap[1].point.append(ptx)
                            bnaMap[1].mapping = myUVSetNames[n]


    def processForColorNode(self, myMesh, mIter, nodeName, nodeType, x3dParent, cpv=True, cField="color", idx=0):
        colorNodeName = nodeName + "_" + nodeType + "_" + str(idx)

        mColors = ()
        mIndex = []

        mIter.reset()
        
        fCount = 0
        while not mIter.isDone():
            vCount = mIter.polygonVertexCount()
            colorList = []
            
            for idx in range(vCount):
                if mIter.hasColor(idx) == False:
                    return
                else:
                    c = mIter.getColor(idx)
                    colorList.append(c)
            
            if cpv == True:
                for c in colorList:
                    if nodeType == "Color":
                        mColors = mColors + (c.r, c.g, c.b)
                    else:
                        mColors = mColors + (c.r, c.g, c.b, c.a)
                    mIndex.append(fCount)
                    fCount += 1
                mIndex.append(-1)
            else:
                sc = aom.MColor()
                for c in colorList:
                    vr = sc.r + c.r
                    vg = sc.g + c.g
                    vb = sc.b + c.b
                    va = sc.a + c.a
                    sc.setColor(vr, vg, vb, va)
                tr = sc.r / vCount
                tg = sc.g / vCount
                tb = sc.b / vCount
                ta = sc.a / vCount
                if nodeType == "Color":
                    mColors = mColors + (tr, tg, tb)
                else:
                    mColors = mColors + (tr, tg, tb, ta)
                mIndex.append(fCount)
                fCount += 1

            mIter.next()

        tIndex = (mIndex)
        x3dParent.colorIndex = tIndex
        
        bna = self.trv.processBasicNodeAddition(x3dParent, cField, nodeType, colorNodeName)
        if bna[0] == False:
            # TODO: Future code for implementing 'metadata'
            
            # Assign color to the node.
            bna[1].color = mColors
            
        
    def processForNormalNode(self, myMesh, mIter, nodeName, nodeType, x3dParent, npv=True, cField="normal", idx=0, nOffset=0, sharedNormal=""):
        normalNodeName = nodeName + "_" + nodeType + "_" + str(idx)

        #mNormal = []
        #mIndex  = []
        mIter.reset()
        fCount = 0

        if sharedNormal != "":
            bna = self.trv.processBasicNodeAddition(x3dParent, cField, "Normal", sharedNormal)

            ################################
            #msList = aom.MSelectionList()
            #msList.add(myMesh.name())
            #tDagPath = msList.getDagPath(0)
            
            #mIter = aom.MItMeshPolygon(tDagPath, meshComps[index])
            ################################

            #### old ######
            #while not mIter.isDone():
            #    if npv == True:
            #        nVerts = mIter.polygonVertexCount()
            #        for vIdx in range(nVerts):
            #            nIdx = mIter.normalIndex(vIdx)
            #            x3dParent.normalIndex.append(nIdx + nOffset)
            #        x3dParent.normalIndex.append(-1)
            #    else:
            #        x3dParent.normalIndex.append(fCount + nOffset)
            #        fCount += 1
            #    mIter.next()
            
            while not mIter.isDone():
                if npv == True:
                    vertIDs = mIter.getVertices()
                    vLen = len(vertIDs)
                    for vIdx in range(vLen):
                        x3dParent.normalIndex.append(mIter.normalIndex(vIdx) + nOffset)
                    x3dParent.normalIndex.append(-1)
                else:
                    x3dParent.normalIndex.append(mIter.index() + nOffset)
                    #x3dParent.normalIndex.append(fCount + nOffset)
                    #fCount += 1
                mIter.next()

            #while not mIter.isDone():
            #    if npv == True:
            #        tns = mIter.getNormals()
            #        for tn in tns:
            #            x3dParent.normalIndex.append(fCount + nOffset)
            #            fCount += 1
            #        x3dParent.normalIndex.append(-1)
            #    else:
            #        x3dParent.normalIndex.append(fCount + nOffset)
            #        fCount += 1
            #    mIter.next()
            
        else:
            bna = self.trv.processBasicNodeAddition(x3dParent, cField, "Normal", normalNodeName)
            if bna[0] == False:
                # TODO: Future code for implementing 'metadata'
                
                while not mIter.isDone():
                    if npv == True:
                        tns = mIter.getNormals()
                        for tn in tns:
                            bna[1].vector.append((tn.x, tn.y, tn.z))
                            x3dParent.normalIndex.append(fCount)
                            fCount += 1
                        x3dParent.normalIndex.append(-1)
                    else:
                        pn = myMesh.getPolygonNormal(mIter.index())
                        bna[1].vector.append((pn.x, pn.y, pn.z))
                        x3dParent.normalIndex.append(mIter.index())
                        #x3dParent.normalIndex.append(fCount)
                        #fCount += 1
                        
                        #fNormal = mIter.getNormal(aom.MSpace.kObject)
                        #bna[1].vector.append((fNormal.x, fNormal.y, fNormal.z))
                        #x3dParent.normalIndex.append(fCount)
                        #fCount += 1
                    
                    mIter.next()

                # Assign MFVec3f to the node.
                #bna[1].vector = mNormal
            
    
    def getUsedUVSetDictionary(self, myMesh, shader):
        sortByTexture = {}
        uvSetNames    = myMesh.getUVSetNames()
        
        textureList, isUfe = self.gatherShaderTextures(shader)
        if isUfe == True:
            rkMat.getMatXUVSetNames(sortByTexture, textureList, uvSetNames)
        else:
            print("TextureList: " + str(len(textureList)))
            
            for i in range(len(uvSetNames)):
                print("My UV Set Names: " + uvSetNames[i])
                print("My mesh name: " + myMesh.name())
                assocTexObj = myMesh.getAssociatedUVSetTextures(uvSetNames[i])
                
                for j in range(len(assocTexObj)):
                    texDep = aom.MFnDependencyNode(assocTexObj[j])
                    print("Assoc Text Obj - texDep: " + texDep.name())
                    
                    for k in range(len(textureList)):
                        if texDep.name() == textureList[k].name():
                            sortByTexture[texDep.name()] = uvSetNames[i]

        return sortByTexture


    def gatherShaderTextures(self, shader):
        textureList = []
        isUfe = False
        
        depNode = aom.MFnDependencyNode(shader) #shader is a shadingEngine object
        matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())

        if matNode.typeName == "MaterialXSurfaceShader":
            isUfe = True
            rkMat.searchForUFETextures(matNode, textureList)
        else:
            isUfe = False
            matIter = aom.MItDependencyGraph(matNode.object(), rkfn.kFileTexture, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
            
            while not matIter.isDone():
                tFound = False
                tNode = aom.MFnDependencyNode(matIter.currentNode())

                for t in textureList:
                    if t.name() == tNode.name():
                        tFound = True

                if tFound == False:
                    textureList.append(tNode)
                    print("Add to my Texture List: " + tNode.name())
            
                matIter.next()
        
        return (textureList, isUfe)


    def processTexture(self, textureNode, x3dAppearance, x3dParent, x3dField, matchedSets, textureTransforms, ignoreTT):
        
        if ignoreTT == True:
            return ignoreTT
            
        relativeTexPath = self.rkImagePath
        localTexWrite   = self.activePrjDir + "/" + relativeTexPath

        nType = textureNode.typeName
        if nType == "envChrome" or nType == "envCube" or nType == "envBall" or nType == "envSphere":
            refBna = self.trv.processBasicNodeAddition(x3dAppearance, "texture", "GeneratedCubeMapTexture", textureNode.name())

            return True
            
        textureMappingField = x3dField + "Mapping"
        mapName             = matchedSets.get(textureNode.name(), "")
        setattr(x3dParent, textureMappingField, mapName)

        tt = self.getPlace2dFromMayaTexture(textureNode)
        if tt:
            textureTransforms.append((tt, mapName))

        x3dNodeType = "PixelTexture"
        
        if textureNode.typeName == "file":
            if  self.rkFileTexType == 0 or self.rkFileTexType == 1:
                x3dNodeType = "ImageTexture"
                x3dURIData  = ""

                x3dTexture = self.trv.processBasicNodeAddition(x3dParent, x3dField, x3dNodeType, textureNode.name())
                if x3dTexture[0] == False:
                    filePath = textureNode.findPlug("fileTextureName", False).asString()
                    fileName = self.rkint.getFileName(filePath)
                    fileExt  = os.path.splitext(fileName)[1]
                    fileName = os.path.splitext(fileName)[0]
                
                    if   self.rkFileTexFormat == 1:
                        fileName = fileName + ".png"
                        relativeTexPath = relativeTexPath + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'png')
                        
                    elif self.rkFileTexFormat == 2:
                        fileName = fileName + ".jpg"
                        relativeTexPath = relativeTexPath + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'jpg')
                        
                    else:
                        fileName = fileName + fileExt
                        relativeTexPath = relativeTexPath + fileName

                        if self.rkConsolidate == True:
                            localTexWrite   = localTexWrite   + fileName
                            movePath = self.imageMoveDir + "/" + fileName
                            self.rkint.copyFile(filePath, movePath)
                        else:
                            localTexWrite = filePath

                    # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                    if self.rkFileTexType == 1:
                        print("Printing LocalTexWrite:\n" + localTexWrite )
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        x3dTexture[1].url.append(x3dURIData)
                    else:
                        print(x3dTexture[1])
                        x3dTexture[1].url.append(fileName       )
                        x3dTexture[1].url.append(relativeTexPath)
                if tt:
                    x3dTexture[1].repeatS = tt.findPlug("wrapU", False).asBool()
                    x3dTexture[1].repeatT = tt.findPlug("wrapV", False).asBool()
    
        elif mTextureNode.typeName == "movie":
            x3dNodeType = "MovieTexture"
            x3dURIData  = ""
            
            x3dTexture = self.trv.processBasicNodeAddition(x3dParent, x3dField, x3dNodeType, mTextureNode.name())
            if x3dTexture[0] == False:
                filePath = mTextureNode.findPlug("fileTextureName", False).asString()
                fileName = self.rkint.getFileName(filePath)
                fileExt  = os.path.splitext(fileName)[1]
                fileName = os.path.splitext(fileName)[0]
                        
                fileName        = fileName + fileExt
                relativeTexPath = relativeTexPath + fileName
                
                #if self.rkMovTexWrite == True:#
                if  self.rkConsolidate == True:#
                    localTexWrite = localTexWrite + fileName
                    movePath = self.imageMoveDir + "/" + fileName
                    self.rkint.copyFile(filePath, movePath)
                else:
                    localTexWrite = filePath

                # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                #if self.rkMovieAsURI == True:
                if self.rkMovieTexType == True:
                    x3dURIData = self.rkint.media2uri(localTexWrite)
                    x3dTexture[1].url.append(x3dURIData)
                else:
                    x3dTexture[1].url.append(fileName)
                    x3dTexture[1].url.append(relativeTexPath)
                    
                if tt:
                    x3dTexture[1].repeatS = tt.findPlug("wrapU", False).asBool()
                    x3dTexture[1].repeatT = tt.findPlug("wrapV", False).asBool()

        return False


    def processMatXTexture(self, textureItem, x3dAppearance, x3dParent, x3dField, matchedSets, textureTransforms, ignoreTT, isX3DOM):
        relativeTexPath = self.rkImagePath
        localTexWrite   = self.activePrjDir + "/" + relativeTexPath
        
        x3dNodeType = "ImageTexture"
        filePath  = rkMat.getMatXAttribute(textureItem, "file", grasp=True).get()
        
        if isinstance(filePath, str):
            print(filePath)
            fileParts = filePath.split('.')
            fileExt   = fileParts[len(fileParts)-1]
            if fileExt == "m3u8" or fileExt == "ts" or fileExt == "m4s" or fileExt == "mov" or fileExt == "qt" or fileExt == "webm" or fileExt == "mp4" or fileExt == "m4v" or fileExt == "mkv" or fileExt == "avi" or fileExt == "ogv" or fileExt == "ogg":
                x3dNodeType = "MovieTexture"

        ttItem = None
        if not isX3DOM:
            # Get UFE Connection to MaterialX place2d node
            ttConn = rkMat.getUFEAttribute(textureItem, "texcoord", connected=True)
            if ttConn:
                # Get place2d SceneItem
                ttItem = ufe.Hierarchy.createItem(ttConn.src.path)
                if "nd_placd2d" in ttItem.nodeType().lower() or "nd_usdtransform2d" in ttItem.nodeType().lower():
                    textureTransforms.append( (ttItem, matchedSets.get(textureItem.path(), "")) )
        
        x3dURIData  = ""
        x3dTexture = self.trv.processBasicNodeAddition(x3dParent, x3dField, x3dNodeType, textureItem.nodeName())
        if x3dTexture[0] == False:
            fileName = self.rkint.getFileName(filePath)
            fileExt  = os.path.splitext(fileName)[1]
            fileName = os.path.splitext(fileName)[0]
        
            if   x3dNodeType == "ImageTexture" and self.rkFileTexFormat == 1:
                fileName = fileName + "png"
                relativeTexPath = relativeTexPath + fileName
                localTexWrite   = localTexWrite   + fileName
                
                self.rkint.fileFormatConvert(filePath, localTexWrite, 'png')
                
            elif x3dNodeType == "ImageTexture" and self.rkFileTexFormat == 2:
                fileName = fileName + ".jpg"
                relativeTexPath = relativeTexPath + fileName
                localTexWrite   = localTexWrite   + fileName
                
                self.rkint.fileFormatConvert(filePath, localTexWrite, 'jpg')
                
            else:
                fileName = fileName + fileExt
                relativeTexPath = relativeTexPath + fileName

                if self.rkConsolidate == True:
                    localTexWrite   = localTexWrite   + fileName
                    movePath = self.imageMoveDir + "/" + fileName
                    self.rkint.copyFile(filePath, movePath)
                else:
                    localTexWrite = filePath

            # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
            if self.rkFileTexType == 1:
                print("Printing LocalTexWrite:\n" + localTexWrite )
                x3dURIData = self.rkint.media2uri(localTexWrite)
                x3dTexture[1].url.append(x3dURIData)
            else:
                print(x3dTexture[1])
                x3dTexture[1].url.append(fileName       )
                x3dTexture[1].url.append(relativeTexPath)
                
        #if "tiled" not in textureItem.nodeType():
        #    x3dTexture[1].repeatS = False
        #    x3dTexture[1].repeatT = False
        
        ################################################################
        # Set Texture Mapping
        mappingField = x3dField + "Mapping"
        if hasattr(x3dParent, mappingField):
            mappingFieldValue = matchedSets.get(str(textureItem.path()), "")
            setattr(x3dParent, mappingField, mappingFieldValue)
        ##################################################################

        if ttItem:
            return True
        else:
            return False


    def getPlace2dFromMayaTexture(self, mTextureNode):
        mPlace2d = None

        txtIt = aom.MItDependencyGraph(mTextureNode.object(), rkfn.kPlace2dTexture, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # Returns first place2dTexture node found.
        while not txtIt.isDone():
            cNode = aom.MFnDependencyNode(txtIt.currentNode())
            if cNode.typeName == "place2dTexture":
                mPlace2d = cNode
                break
                
            txtIt.next()
        
        return mPlace2d
    
        
    # Function that gathers data necesasry for export
    def prepForSceneTraversal(self):
        
        # Test if RK-IO is traversing the DAG for the purpose of Building an X3D tree for the RawKee GUI
        # If not, then execute the following funtions perparing for export.
        if self.isTreeBuilding == False:
            
            self.trv.clearMemberLists()
            self.setIgnoreStatusForDefaults()
    
    
    #################################################################################################
    # There are some default nodes in Maya that we just want to ignore by default. These nodes are 
    # different depending on what version of Maya you are using. This function tells the exporter
    # to ignore these nodes if they exist.
    #################################################################################################
    def setIgnoreStatusForDefaults(self):
        self.trv.setIgnored("persp")
        self.trv.setIgnored("top")
        self.trv.setIgnored("front")
        self.trv.setIgnored("side")
        self.trv.setIgnored("groundPlane_transform")
        self.trv.setIgnored("defaultUfeProxyCameraTransformParent")
        self.trv.setIgnored("defaultLightSet")
        self.trv.setIgnored("defaultObjectSet")
        self.trv.setIgnored("defaultUfeProxyTransform")
        self.trv.setIgnored("Manipulator1")
        self.trv.setIgnored("UniversalManip")
        self.trv.setIgnored("CubeCompass")
        

    def checkSubDirs(self, fullPath):
        pdir = os.path.dirname(fullPath)
        
        imgPath = os.path.dirname(pdir + "/" + self.rkImagePath) #cmds.optionVar( q='rkImagePath' ))
        audPath = os.path.dirname(pdir + "/" + self.rkAudioPath) #cmds.optionVar( q='rkAudioPath' ))
        #inlPath = os.path.dirname(pdir + "/" + cmds.optionVar( q='rkInlinePath'))
        
        if not os.path.exists(imgPath):
            os.mkdir(imgPath)

        if not os.path.exists(audPath):
            os.mkdir(audPath)

        #if not os.path.exists(inlPath):
        #    os.mkdir(inlPath)

        self.imageMoveDir  = imgPath
        self.audioMoveDir  = audPath
        #self.inlineMoveDir = inlPath


    def getSFColor(self, r, g, b):
        red   = r
        green = g
        blue  = b
        
        if red > 1.0:
            red = 1.0
        elif red < 0.0:
            red = 0.0
            
        if green > 1.0:
            green = 1.0
        elif green < 0.0:
            green = 0.0
            
        if blue > 1.0:
            blue = 1.0
        elif blue < 0.0:
            blue = 0.0
            
        return (red, green, blue)


    def getSFColorRGBA(self, r, g, b, a):
        red   = r
        green = g
        blue  = b
        alpha = a
        
        if red > 1.0:
            red = 1.0
        elif red < 0.0:
            red = 0.0
            
        if green > 1.0:
            green = 1.0
        elif green < 0.0:
            green = 0.0
            
        if blue > 1.0:
            blue = 1.0
        elif blue < 0.0:
            blue = 0.0
            
        if alpha > 1.0:
            alpha = 1.0
        elif alpha < 0.0:
            alpha = 0.0
            
        return (red, green, blue, alpha)
        
    def getJointType(self, jtVal):
        jtValMapping = {
            ####################################### A
            '0':'',# None
            '1':'Root',
            '2':'Hip',
            '3':'Knee',
            '4':'Foot',
            '5':'Toe',
            '6':'Spine',
            '7':'Neck',
            '8':'Head',
            '9':'Collar',
            '10':'Shoulder',
            '11':'Elbow',
            '12':'Hand',
            '13':'Finger',
            '14':'Thumb',
            '15':'PropA',
            '16':'PropB',
            '17':'ProbC',
            '18':'Other',
            '19':'Index_Finger',
            '20':'Middle_Finger',
            '21':'Ring_Finger',
            '22':'Pinky_Finger',
            '23':'Extra_Finger',
            '24':'Big_Toe',
            '25':'Index_Toe',
            '26':'Middle_Toe',
            '27':'Ring_Toe',
            '28':'Pinky_Toe',
            '29':'Foot_Thumb'
        }
        
        return jtValMapping[str(jtVal)]


    def getCGEJointLabel(self, jNode):
        jointName = ""
        hasMeat = True

        sideVal = cmds.getAttr(jNode.name() + ".side")
        if sideVal == 0:
            jointName = "Center_"
        elif sideVal == 1:
            jointName = "Left_"
        elif sideVal == 2:
            jointName = "Right_"

        nType = cmds.getAttr(jNode.name() + ".type")
        
        typeText = self.getJointType(str(nType))
        
        if typeText == "Other":
            typeText = cmds.getAttr(jNode.name() + ".otherType")
            
        if typeText == "":
            hasMeat = False

        if hasMeat == True:
            jointName += typeText
        else:
            jointName = jNode.name()
        
            #if jointName == "":
            #    jointName = "Random_" + str(random.randint(1000001, 2000000))
            #   print("CGE WARNING: Printed random joint name because it was not defined in the Maya joint's (Side), (Type), and (OtherType) attributes - CGE Joint Name: " + jointName)
        
        return jointName
        

    def findTextureFromPlug(self, texturePlug):
        nodeNames = ["file", "movie", "envChrome", "envCube", "envBall", "envSphere"]
        for nName in nodeNames:
            tIter = aom.MItDependencyGraph(texturePlug, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kPlugLevel)

            while not tIter.isDone():
                cNode = tIter.currentNode()
                
                depNode = aom.MFnDependencyNode(cNode)
                # Check if the current node is a texture node
                if depNode.typeName == nName:
                    return depNode  # Found a texture node 
                    
                tIter.next()
                    
        return None
        
    def findNormScaleNode(self, texturePlug):
        mIter = aom.MItDependencyGraph(texturePlug, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kPlugLevel)
        
        while not mIter.isDone():
            cObj = mIter.currentNode()
            
            # Check if the current node is a bump2d node
            cNode = aom.MFnDependencyNode(cObj)
            if cNode.typeName == "bump2d" or cNode.typeName == "aiNormalMap":
                return cNode
                
            mIter.next()
        
        return None #aom.MObject.kNullObj


    def cMessage(self, msg):
        if self.isVerbose:
            print(msg)


    def checkForRawKeeNoExportLayer(self, depNode):
        layIter = aom.MItDependencyGraph(depNode.object(), 
                                         aom.MFn.kDisplayLayer,
                                         aom.MItDependencyGraph.kUpstream, 
                                         aom.MItDependencyGraph.kDepthFirst, 
                                         aom.MItDependencyGraph.kNodeLevel)
        while not layIter.isDone():
            mObject = layIter.currentNode()
            layNode = aom.MFnDependencyNode(mObject)
            
            dtValue = cmds.getAttr(layNode.name() + ".displayType")
            if dtValue > 0:
                return True
            layIter.next()
        
        if depNode.typeName == "transform":
            groupDag = aom.MFnDagNode(depNode.object())
            cNum = groupDag.childCount()
            for i in range(cNum):
                child = aom.MFnDependencyNode(groupDag.child(i))
                if child.typeName == "materialxStack":
                    return True

        return False

