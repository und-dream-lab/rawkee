import sys
import maya.cmds as cmds
import maya.mel  as mel

import maya.api.OpenMaya as aom
import maya.api.OpenMayaAnim as aoma
from   maya.api.OpenMaya import MFn as rkfn

from rawkee.RKInterfaces import *
from rawkee.RKIO         import *
from rawkee.RKXNodes     import *
from rawkee.RKPseudoNode import *

import numpy as np

import json

import os

#Python implementation of C++ x3dExportOrganizer

        # For processing the Maya nodes as X3D equivelents
        # transform - Transform - ############ - children - 4
        # transform - Group     - x3dGroup     - children - 4
        # transform - Billboard - x3dBillboard - children - 4
        # transform - Anchor    - x3dAnchor    - children - 4
        # transform - Collision - x3dCollision - children - 4
        # transform - Switch    - x3dSwitch    - choice   - 101
        # lodGroup  - LOD       - ############ - level    - 102


class RKOrganizer():
    def __init__(self):
        #print("RKOrganizer")
        
        self.rkint = RKInterfaces()
        self.rkio  = RKIO()
        
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



        self.optionsString = ""
        
        '''
        X3D Encodings: 0 - XML     - *.x3d
                       1 - Classic - *.x3dv
                       2 - VMRl97  - *.vrml
                       4 - binary  - *.x3db, *.x3de
                       5 - json    - *.x3dj, *.json
                       
        Import/Export file coding
        '''
        self.exEncoding = 0
        
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
        
        # Arrays of Array Strings used to store the names of nodes which have already been exported
        self.textureNames = []

        # Object used to get the Root of the DAG for export.
        self.worldRoot = None
        
        ################################
        self.imageMoveDir  = ""
        self.audioMoveDir  = ""
        self.inlineMoveDir = ""


    def __del__(self):
        del self.rkio
        del self.rkint
        
    def loadRawKeeOptions(self):
        self.rkCastlePrjDir    = cmds.optionVar( q='rkCastlePrjDir'   )
        self.rkSunrizePrjDir   = cmds.optionVar( q='rkSunrizePrjDir'  )
        self.rkPrjDir          = cmds.optionVar( q='rkPrjDir'         )
        self.rkBaseDomain      = cmds.optionVar( q='rkBaseDomain'     )
        self.rkSubDir          = cmds.optionVar( q='rkSubDir'         )
        self.rkImagePath       = cmds.optionVar( q='rkImagePath'      )
        self.rkAudioPath       = cmds.optionVar( q='rkAudioPath'      )
        self.rkInlinePath      = cmds.optionVar( q='rkInlinePath'     )
        
        self.rk2dTexWrite      = cmds.optionVar( q='rk2dTexWrite'     )
        self.rkMovTexWrite     = cmds.optionVar( q='rkMovTexWrite'    )
        self.rkAudioWrite      = cmds.optionVar( q='rkAudioWrite'     )
        self.rk2dFileFormat    = cmds.optionVar( q='rk2dFileFormat'   )
        self.rkMovFileFormat   = cmds.optionVar( q='rkMovFileFormat'  )
        self.rkAudioFileFormat = cmds.optionVar( q='rkAudioFileFormat')
        self.rkExportCameras   = cmds.optionVar( q='rkExportCameras'  )
        self.rkExportLights    = cmds.optionVar( q='rkExportLights'   )
        self.rkExportSounds    = cmds.optionVar( q='rkExportSounds'   )
        self.rkExportMetadata  = cmds.optionVar( q='rkExportMetadata' )
        self.rkProcTexNode     = cmds.optionVar( q='rkProcTexNode'    )
        self.rkFileTexNode     = cmds.optionVar( q='rkFileTexNode'    )
        self.rkLayerTexNode    = cmds.optionVar( q='rkLayerTexNode'   )
        self.rkAdjTexSize      = cmds.optionVar( q='rkAdjTexSize'     )
        
        self.rkMovieAsURI      = cmds.optionVar( q='rkMovieAsURI'     )
        self.rkAudioAsURI      = cmds.optionVar( q='rkAudioAsURI'     )
        self.rkInlineAsURI     = cmds.optionVar( q='rkInlineAsURI'    )
        
        self.rkDefTexWidth     = cmds.optionVar( q='rkDefTexWidth'    )
        self.rkDefTexHeight    = cmds.optionVar( q='rkDefTexHeight'   )
        self.rkColorOpts       = cmds.optionVar( q='rkColorOpts'      )
        self.rkNormalOpts      = cmds.optionVar( q='rkNormalOpts'     )
        self.rkHtmlShaderOpts  = cmds.optionVar( q='rkNormalOpts'     )
        
        self.rkFrontLoadExt    = cmds.optionVar( q='rkFrontLoadExt'   )
        
        self.rkExportMode      = cmds.optionVar( q='rkExportMode'     )
        
        self.rkCreaseAngle     = cmds.optionVar( q='rkCreaseAngle'    )
        
        self.activePrjDir = self.rkPrjDir
        
        if self.rkExportMode == 1:
            self.activePrjDir = self.rkCastlePrjDir
        elif self.rkExportMode == 2:
            self.activePrjDir = self.rkSunrizePrjDir
            


    def newTemplateId(self, myMesh):
        templateID = 0
        while myMesh.isBlindDataTypeUsed(templateID):
            templateID += 1
            
        return templateID

    
    def processImportFile(self, fullFilePath, rkFilter):
        self.rkio.cMessage("Importing!!!")
        self.rkio.cMessage(fullFilePath)
        self.rkio.cMessage(rkFilter)
        
        
        
    def processExportFile(self, fullFilePath, rkFilter):
        self.rkio.cMessage("Exporting!!!")
        self.rkio.cMessage(fullFilePath)
        self.rkio.cMessage(rkFilter)
    
    #######################################################################################
    ### maya2x3d(self - RKOrganizer, x3d.Scene, MFnDagPath lsit [], MFnDagNode list [], string - pVersion <rawkee version>) ###
    #######################################################################################
    # Traverses the Maya DAG and converts the Maya nodes it    #
    # finds into X3D nodes and places them in a location in    #
    # the X3D Scenegraph that roughly corresponds to there     #
    # locations in the Maya DAG/DepGraph. Returns nothing.     #
    ############################################################
    def maya2x3d(self, x3dScene, parentDagPaths, dagNodes, pVersion, fullPath, exEncoding):
        self.exEncoding = exEncoding
        
        self.loadRawKeeOptions()

        self.checkSubDirs(fullPath)

        self.rkio.comments.clear()
        self.rkio.comments.append(pVersion)
        self.rkio.commentNames.clear()
        self.rkio.commentNames.append("created_with")

        # Should aways be a new root.
        # Telling the IO object that this node has been 
        # visited bofore.
        self.rootName = "|!!!!!_!!!!!|world"
        self.rkio.setAsHasBeen(self.rootName, x3dScene)
        
        #Traverse Maya Scene Downward without using an MFIt object
        dNum = len(dagNodes)
        for i in range(dNum):
            self.traverseDownward(parentDagPaths[i], dagNodes[i])
        
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
            parentDagPaths.append(dragPath)
            topDagNodes.append(aom.MFnDagNode(worldDag.child(i)))

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
            selectedDagNodes.append(aom.MFnDagNode(dagPath))
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
        x3dScene = self.rkio.resetSceneRoot(x3dDoc)
        self.rootName = "|!!!!!_!!!!!|world"
        self.rkio.setAsHasBeen(self.rootName, x3dScene)
        
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
        x3dScene = self.rkio.resetSceneRoot(x3dDoc)
        self.rootName = "|!!!!!_!!!!!|world"
        self.rkio.setAsHasBeen(self.rootName, x3dScene)

        cNum = len(dagList)
        for i in range(cNum):
            self.traverseDownward(dragList[i], dagList[i])

#############################   Break   ####################################
############################################################################
        
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
    
    def processMayaLOD(self, dragPath, dagNode, cField="children"):
        pass
        
    #########################################################################################################
    #   Sound Related Functions
    def processX3DSound(self, dagNode, x3dPF):
        if dagNode.childCount() > 0:
            depNode = aom.MFnDependencyNode(dagNode.child(0))
            bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "Sound", dagNode.name())
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
                bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "OrthoViewpoint", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicViewpointFields(x3dNode, dagNode, depNode)
                    
                    # X3D fieldOfView
                    oWidth = depNode.findPlug("orthographicWidth", False).asFloat() / 2
                    x3dNode.fieldOfView =  (oWidth * -1, oWidth * -1, oWidth, oWidth)
                     
            else:
                bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "Viewpoint", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicViewpointFields(x3dNode, dagNode, depNode)
                    
                    # X3D fieldOfView
                    hoz = depNode.findPlug("horizontalFilmAperture", False).asFloat()
                    focal = depNode.findPlug("focalLength", False).asFloat()
                    fov = (0.5 * hoz) / (focal * 0.03937)
                    fov = 2.0 * np.arctan(fov)
                    fov = 57.29578 * fov
                    x3dNode.fieldOfView = np.deg2rad(fov)

    def processBasicViewpointFields(self, x3dNode, dagNode, depNode):
        mlist = aom.MSelectionList()
        mlist.add(dagNode.name())
        tForm = aom.MFnTransform(mlist.getDependNode(0))

        # X3D centerOfRotation
        x3dNode.centerOfRotation = self.rkint.getSFVec3fFromMPoint(tForm.rotatePivot(aom.MSpace.kTransform))
        
        # X3D description - must be addedmanually by the user if camera node not created through the RawKee GUI
        try:
            x3dNode.description = dagNode.findPlug("x3dDescription", False).asString()
        except:
            self.rkio.cMessage("No 'description' X3D Field Found")
        
        # X3D farDistance
        x3dNode.farDistance = depNode.findPlug("farClipPlane", False).asFloat()
        
        # X3D jump - must be addedmanually by the user if camera node not created through the RawKee GUI
        try:
            x3dNode.jump = dagNode.findPlug("x3dJump",False).asBool()
        except:
            self.rkio.cMessage("No 'jump' X3D Field Found")
        
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
            self.rkio.cMessage("No 'retainUserOffsets' X3D Field Found")
            
        # X3D viewAll
        try:
            x3dNode.viewAll = dagNode.findPlug("x3dViewAll", False).asBool()
        except:
            self.rkio.cMessage("No 'viewAll' X3D Field Found")
    
    ##########################################################################################################
    # Lighting Related Functions
    def processX3DLighting(self, dagNode, x3dPF):
        if dagNode.childCount() > 0:
            depNode = aom.MFnDependencyNode(dagNode.child(0))
            if depNode.typeName == "directionalLight":
                bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "DirectionalLight", dagNode.name())
                if bna[0] == False:
                    x3dNode = bna[1]
                    self.processBasicLightFields(x3dNode, dagNode, depNode)

                    # X3D Direction
                    mlist = aom.MSelectionList()
                    mlist.add(dagNode.name())
                    tForm = aom.MFnTransform(mlist.getDependNode(0))
                    x3dNode.direction = self.rkint.getDirection(tForm.rotation(aom.MSpace.kTransform, False))
                    
            elif depNode.typeName == "spotLight":
                bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "SpotLight", dagNode.name())
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
                bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "PointLight", dagNode.name())
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

            else:
                pass
    
    def processBasicLightFields(self, x3dNode, dagNode, depNode):
        # X3D AmbientIntensity - Maya Directional Light does not have an Amb Intensity attribute,
        # skipping this X3D Field
        
        # X3D Color
        nColor = depNode.findPlug("color", False)
        rc = nColor.child(0).asFloat()
        gc = nColor.child(1).asFloat()
        bc = nColor.child(2).asFloat()
        strCol = "r: " + str(rc) + ", g: " + str(gc) + ", b: " + str(bc)
        self.rkio.cMessage(strCol)
        x3dNode.color = (rc, gc, bc)
        
        # X3D Global
        # Always set to True until I can figure out a way to set it to False, probably a custom attribute
        #x3dNode.global_ = True
        #self.rkio.cMessage(dir(x3dNode))
        x3dNode.global_ = True
        
        # X3D Intensity
        x3dNode.intensity = depNode.findPlug("intensity", False).asFloat()

        # X3D Metadata - TODO

        # X3D 'on'
        # DirLight field "on" is set to isConnected()
        nodes = cmds.listConnections(dagNode.name())
        isCon = False
        for n in nodes:
            if n == "defaultLightSet":
                isCon = True
        x3dNode.on = isCon
        
        # X3D shadows - TODO
        x3dNode.shadows = depNode.findPlug("useDepthMapShadows", False).asBool()
        
        # X3D shadowIntensity - TODO
        sColor = depNode.findPlug("shadowColor", False)
        sr = sColor.child(0).asFloat()
        sg = sColor.child(1).asFloat()
        sb = sColor.child(2).asFloat()
        tInt = (sr + sg + sb ) / 3
        x3dNode.shadowIntensity = 1 - tInt
        
    ######################################################################################################################
    #   Transform Related Functions
    def processX3DTransform(self, dragPath, dagNode, x3dPF):
        depNode = aom.MFnDependencyNode(dagNode.object())
        dragPath = dragPath + "|" + depNode.name()
        bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "Transform")
        if bna[0] == False:
            self.processBasicTransformFields(depNode, bna[1])
            
            #Traverse Maya Scene Downward without using an MFIt object
            groupDag = aom.MFnDagNode(depNode.object())
            cNum = groupDag.childCount()
            for i in range(cNum):
                self.traverseDownward(dragPath, aom.MFnDagNode(groupDag.child(i)))
                

    def processBasicTransformFields(self, depNode, x3dNode):
        mlist = aom.MSelectionList()
        mlist.add(depNode.name())
        tForm = aom.MFnTransform(mlist.getDependNode(0))

        #X3D translation - tForm.translation() returns an MVector, getSFVec3f returns a tuple (x, y, z)
        x3dNode.translation = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))
        
        #X3D Rotation - tForm.rotation().asAxisAngle() returns a tuple (MVector, float) getSFRotation returns a tuple (x, y, z, w) 
        x3dNode.rotation = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())

        #X3D Scale - tForm.scale() returns a List [ x, y, z] What? Why not an MVector Autodesk?
        chVals = tForm.scale()
        if depNode.typeName == "joint":
            chVals[0] = abs(chVals[0])
            chVals[1] = abs(chVals[1])
            chVals[2] = abs(chVals[2])
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
        x3dNode.center = self.rkint.getSFVec3fFromMPoint(tForm.rotatePivot(aom.MSpace.kTransform))

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
        
    def processUnboundHAnimHumanoid(self, dragPath, dagNode, x3dPF):
        pass
    
    ######################################################################################################################
    # HAnimHumanoid Related Functions
    ######################################################################################################################
    def processHAnimHumanoid(self, dragPath, dagNode, x3dPF):
        depNode = aom.MFnDependencyNode(dagNode.object())
        
        ######################################################################
        # Look for HAnimHumanoid Export Type attribute, and call Default Pose
        # usually an I-pose, unless character is a non-human.
        ######################################################################
        # Value 0: Standard HAnim Skeleton Generated by RawKee 
        #          Character Editor
        # Value 1: Convert Advanced Skeleton rig to HAnim Rig using RawKee
        #          Character Ediotr
        ######################################################################
        try:
            etValue = cmds.getAttr(depNode.name() + ".RKExportType")
            if etValue == 0:
                #TODO Implement Code that puts skeleton in bind pose
                pass
            elif etValue == 1:
                # RawKee funciton that puts converted skeleton into
                # user-defined default export pose at time of export.
                cmds.rkLoadDefPoseForHAnim()
        except:
            print("ET Value Doesn't Exist. Results undefined.")
            
        dragPath = dragPath + "|" + depNode.name()
        bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "HAnimHumanoid")
        
        if bna[0] == False:
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
                bna[1].skeletalConfiguration = cmds.getAttr(bna[1].DEF + ".skeletalConfiguration")
            except:
                bna[1].skeletalConfiguration = "CUSTOM"
                
            try:
                bna[1].loa = cmds.getAttr(bna[1].DEF + ".LOA")
            except:
                bna[1].loa = -1

            
            # MFnDagNode version of Humanoid Node
            groupDag = aom.MFnDagNode(depNode.object())
            cNum = groupDag.childCount()
            
            # 'sm' is a list of mesh nodes used for the skin of this HAnimHumanoid
            sm = []
            
            # 'sc' is a list of skinClsuters
            sc = []

            # Traverse the Skeleton
            for i in range(cNum):
                dagChild = aom.MFnDagNode(groupDag.child(i))
                if   dagChild.typeName == "joint":
                    self.processHAnimJoint(dragPath, dagChild, bna[1], bna[1], cField="skeleton", sk=sm)
#                else:
#                    print("Skeleton Traverse Miss: " + dagChild.name() + ", Type:"+ dagChild.typeName)

                
            # Get Weight/point Index Offset and Skin Coordinate Node name.
            # wio length might be 0 and cName might equal "" if sm length is 0.
            wio, cName = self.getSkinCoordinateNode(depNode, bna[1], sm)
            
            # Get Normal Vertex Index Offset and Skin Normal Node name
            # Depnding on export options 'sno' length might = 0, and 
            # sName might be equial to "".
            sno, sName = self.getSkinNormalNode(depNode, bna[1], sm)
            
            # Adds X3D Shape nodes to 'skin' field of the humanoid. Assumes 
            # that mesh is point values are in world coordinates.
            smLen = len(sm)
            snLen = len(sno)
            for i in range(smLen):
                # This is needed if the sno length is zero so as not to throw an out-of-bounds error on the list.
                if snLen == 0:
                    sno.append(snLen)
                self.processMayaMesh(dragPath, aom.MFnDagNode(sm[i].object()), "skin", wio[i], sno[i], cName, sName)
            
            
            ###### self.convertMayaAnimClips_To_HAnimMotion(dragPath, bpNode)
            

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


    def getSkinNormalNode(self, depNode, x3dParent, skm):
        sno = []
        nName = ""
        
        if self.rkNormalOpts > 0 and len(skm) > 0:
            nName = depNode.name() + "_Normal"
            normalbna = self.processBasicNodeAddition(depNode, x3dParent, "skinNormal", "Normal", nName)
            #normalbna = self.processBasicNodeAddition(depNode, x3dParent, "skinBindingNormals", "Normal", nName)
            #sknbna    = self.processBasicNodeAddition(depNode, x3dParent, "skinNormal", "Normal", nName)

            for sm in skm:
                interSM = self.getIntermediateMesh(sm)
                mIter = aom.MItMeshPolygon(interSM.object())
                slen = len(sno)
                offset = 0
                while not mIter.isDone():
                    #Normals Per Vertex
                    if self.rkNormalOpts == 1 or self.rkNormalOpts == 4:
                        tns = mIter.getNormals()
                        for tn in tns:
                            if normalbna[0] == False:
                                normalbna[1].vector.append((tn.x, tn.y, tn.z))
                            offset += 1
                        
                    #Normals Per Face
                    elif self.rkNormalOpts == 2 or self.rkNormalOpts == 3:
                        tn = mIter.getNormal()
                        if normalbna[0] == False:
                            normalbna[1].vector.append((tn.x, tn.y, tn.z))
                        offset += 1
                        
                    mIter.next()
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


    def getSkinCoordinateNode(self, depNode, x3dParent, skm):
        ##### Add an X3D Coordiante Node
        wio = []
        cName = ""
        skmLen = len(skm)
        
        if skmLen > 0:
            cName = depNode.name() + "_Coord"
            coordbna = self.processBasicNodeAddition(depNode, x3dParent, "skinCoord", "Coordinate", cName)
            #coordbna = self.processBasicNodeAddition(depNode, x3dParent, "skinBindingCoords", "Coordinate", cName)
            #skcbna   = self.processBasicNodeAddition(depNode, x3dParent, "skinCoord", "Coordinate", cName)
            for sm in skm:
                ###########################################################################
                # 
                # Add code to grabe the original mesh intermediate object
                # 
                ###########################################################################
                interSM = self.getIntermediateMesh(sm)
                points = interSM.getFloatPoints()
                wlen = len(wio)
                offset = 0
                for point in points:
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
                    x3dJoint = self.rkio.getGeneratedX3D(dPaths[l].partialPathName())
                    
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

                
                


    # sc is MFnSkinCluster list, wo is list of ints that are the per-mesh offset from 0 of the weights index for that mesh, sk is MFnMesh node list
    def processHAnimJoint(self, dragPath, jNode, x3dHumanoid, x3dParent, cField="children", sc=[], wo=[], sk=[], hasSC=False, jOffset=(0.0, 0.0, 0.0)):
        dragPath = dragPath + "|" + jNode.name()

        bna   = self.processBasicNodeAddition(jNode, x3dParent,   cField,   "HAnimJoint")
        bnajt = self.processBasicNodeAddition(jNode, x3dHumanoid, "joints", "HAnimJoint")
    

        if bna[0] == False:
            #######################################
            # Process X3D Fields and set Binding 
            # Position for this Joint
            #######################################
            mlist = aom.MSelectionList()
            mlist.add(jNode.name())
            mlist.add(x3dHumanoid.DEF)

            tMatrix   = cmds.getAttr(jNode.name() + ".offsetParentMatrix")
            #####opmPlug   = jNode.findPlug("offsetParentMatrix", False)
            #####opmMatrix = opmPlug.asMMatrix()
            #####tMatrix   = aom.MTransformationMatrix(opmMatrix)
            #####tPivot    = tMatrix.translation(aom.MSpace.kTransform)
            
            tForm = aom.MFnTransform(mlist.getDependNode(0))

            #######################################################
            ### test

            ### jDpath        = mlist.getDagPath(0)
            ### jWorldMatrix  = jDpath.inclusiveMatrix()
            ### jTransMatrix  = aom.MTransformationMatrix(jWorldMatrix)
            ### jWorldRotPiv  = jTransMatrix.rotatePivot(aom.MSpace.kObject)

            ### hDagPath      = mlist.getDagPath(1)
            ### hWorldMatrix  = hDagPath.inclusiveMatrix()
            ### hWorldIMatrix = hWorldMatrix.inverse()
            
            ### jRPHSpace     = jWorldRotPiv * hWorldIMatrix
            
            ###
            #######################################################
            
            ############################################################################################
            # For use with tForm
            #tPivot = self.rkint.getSFVec3f(tForm.translation(aom.MSpace.kTransform))
            #localPivot = (tPivot[0] + jOffset[0], tPivot[1] + jOffset[1], tPivot[2] + jOffset[2])
            ############################################################################################

            
            ############################################################################################
            # For use with offsetParentMatrix
            localPivot = (tMatrix[12] + jOffset[0], tMatrix[13] + jOffset[1], tMatrix[14] + jOffset[2])
            ############################################################################################
            
            bna[1].center = localPivot #(jRPHSpace.x, jRPHSpace.y, jRPHSpace.z)
            
            ############################################################################################
            # For use with tForm
            #X3D Rotation - tForm.rotation().asAxisAngle() returns a tuple (MVector, float) getSFRotation returns a tuple (x, y, z, w) 
            ### bna[1].rotation = self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle())
            ### x3dHumanoid.jointBindingRotations.append(self.rkint.getSFRotation(tForm.rotation(aom.MSpace.kTransform, True).asAxisAngle()))

            ############################################################################################
            # For use with tForm
            #X3D Scale - tForm.scale() returns a List [ x, y, z] What? Why not an MVector Autodesk?
            ### chVals = tForm.scale()
            ### chVals[0] = abs(chVals[0])
            ### chVals[1] = abs(chVals[1])
            ### chVals[2] = abs(chVals[2])
            ### bna[1].scale = self.rkint.getSFVec3fFromList(chVals)

            nType = cmds.getAttr(jNode.name() + ".type")
            if nType == 18:
                bna[1].name = cmds.getAttr(jNode.name() + ".otherType")

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
                    self.processHAnimJoint(dragPath, dagChild, x3dHumanoid, bna[1], cField="children", sc=sc, wo=wo, sk=sk, hasSC=False, jOffset=localPivot)
                elif dagChild.typeName == "transform":
                    mySegName = dagChild.name() + "_segment"
                    bnaSeg  = self.processBasicNodeAddition(jNode, bna[1],      "children", "HAnimSegment", nodeName=mySegName)
                    bnaSeg2 = self.processBasicNodeAddition(jNode, x3dHumanoid, "segments", "HAnimSegment", nodeName=mySegName)
                    
                    if bnaSeg[0] == False:
                    #    bnaSeg[1].centerOfMass = bna[1].center
                        pass
                    
                    self.traverseDownward(dragPath + "|" + mySegName, dagChild)
                    x3dTransChild = self.rkio.getGeneratedX3D(dagChild.name())
                    x3dTransChild.translation = bna[1].center

#                else:
#                    print("Skeleton Traverse Miss: " + dagChild.name() + ", Type: "+ dagChild.typeName)

                


    def convertMayaAnimClips_To_HAnimMotion(self, dragPath, bpNode, cField="motions"):
        pass
        

    
    ######################################################################################################################
    #   Basic Node Functions
    def processBasicNodeAddition(self, depNode, x3dParentNode, x3dFieldName, x3dType, nodeName=None):
        # Determine the DEF/USE value of the node to be created
        if nodeName == None:
            nodeName = depNode.name()
            
        # Create Node from String where x3dType is a string that identifies 
        # the type of X3D to be created. Must be a node defined by the X3D 4.0 Specification.
        tNode = self.rkio.createNodeFromString(x3dType)
        
        # Add the 'containerField' name to this node to export for XML encodings.
        tNode._RK__containerField = x3dFieldName
        
        # Print node object to the console. Mostly included here to let the user
        # know that the scene is being constucted.
###        print(tNode)
#        print("DEF: " + nodeName)
        #self.rkio.cMessage(tNode)
        
        # Check to see if the node has previously been created with a DEF 
        # attribute.
        hasBeen = self.rkio.checkIfHasBeen(nodeName)
        
        # If has been created already, assign the "nodeName" value to the 
        # X3D node's USE attribute and leave the DEF attribute as None.
        if hasBeen == True:
            tNode.USE = nodeName
        
        # However, if the node has not been previously created, set the 
        # X3D node's DEF attribute to the value of "nodeName", and then
        # record the node has having been created by calling the 
        # "setHasBeen()" method.
        else:
            tNode.DEF = nodeName
            self.rkio.setAsHasBeen(nodeName, tNode)
            
        # Now it is time to add the new node to the X3D Scene. First 
        # we must obtain the value of the X3D Field of the parent by 
        # calling "getattr". Doing so will return the field's value, 
        # which will either be a "list" (populated or empty) or a 
        # 'None' value.           
        nodeField = getattr(x3dParentNode, x3dFieldName)
        
        # Once this value has been obtained, we check to see if the
        # value is an 'instance' of the 'list' data type. If it is 
        # an instance of the list data type, then append the new 
        # X3D node to this list.
        if isinstance(nodeField, list):
            nodeField.append(tNode)
            
        # If the value is not an instance of list, then use the 
        # 'setattr' method to set the parent's field value to the 
        # value of the new X3D node.
        else:
            setattr(x3dParentNode, x3dFieldName, tNode)
            
        # Return a list containing the value of 'hasBeen', which lets
        # the calling section of code know whether the X3D node in question
        # had once before, already been added to the scene. This allows the 
        # section of the code that originally called this method to know 
        # whether other X3D field values should be added to this new node.
        # And then also return the new node so if it does need values 
        # assigned to it's other attributes, the section of the code that
        # called this metod can do so.
        return [hasBeen, tNode]
    
    def getX3DParentAndContainerField(self, dagNode, dragPath=None):
        if dragPath == None:
            dragPath = dagNode.getPath().fullPathName()
        sp = dragPath.split('|')
        spLen = len(sp)
        pName = sp[spLen-2]
        
        if spLen == 2:
            pName = self.rootName

        x3dParent = self.rkio.findExisting(pName)
        
        if x3dParent == None:
#            x3dParent = self.rkio.x3dDoc.Scene
            x3dParent = self.rkio.findExisting(self.rootName)
        
        #Use this code when using the 'traverseDownward()' function for traversing the scene graph
        #x3dParent = self.rkio.findExisting(pX3DName)

        #TODO: maybe something here in the future to determine x3dField
        x3dField = "children"

        return [x3dParent, x3dField]
        attributes = dir(x3dParent)
        self.rkio.cMessage(attributes)

    def getX3DParent(self, dagNode, dragPath=None):
        if dragPath == None:
            dragPath = dagNode.getPath().fullPathName()
        sp = dragPath.split('|')
        spLen = len(sp)
        pName = sp[spLen-2]
        
        if spLen == 2:
            pName = self.rootName

        x3dParent = self.rkio.findExisting(pName)
        
        if x3dParent == None:
            x3dParent = self.rkio.findExisting(self.rootName)
        
        return x3dParent


    ############################################################################################
    #   Export Organizing Related Functions
    def processMayaTransformNode(self, dragPath, dagNode, cField="children"):
        isTransform = True
        x3dTypeAttr = None
        xta = ""

        try: 
            x3dTypeAttr = dagNode.findPlug("x3dNodeType", False)
            xta = x3dTypeAttr.asString()
            self.rkio.cMessage("x3dNodeType exists!")
        except:
            self.rkio.cMessage("x3dNodeType does not exist")
        
        dragPath = dragPath + "|" + dagNode.name()

        x3dPF = []
        x3dPF.append(self.getX3DParent(dagNode, dragPath))
        x3dPF.append(cField)

        if x3dPF[0] == None:
            self.rkio.cMessage("Parent Not Found. Ignore node: " + dagNode.name())
        else:
            if x3dPF[0] != None and xta != "":
                self.rkio.cMessage("xta items")
                if xta == "Anchor":
                    isTransform = False
                    self.processX3DAnchor(   dragPath, dagNode, x3dPF)
                elif xta == "Billboard":
                    isTransform = False
                    self.processX3DBillboard(dragPath, dagNode, x3dPF)
                elif xta == "Collision":
                    isTransform = False
                    self.processX3DCollision(dragPath, dagNode, x3dPF)
                elif xta == "Group":
                    isTransform = False
                    self.processX3DGroup(    dragPath, dagNode, x3dPF)
                elif xta == "Switch":
                    isTransform = False
                    self.processX3DSwitch(   dragPath, dagNode, x3dPF)
                elif xta == "ViewpointGroup":
                    isTransform = False
                    self.processX3DViewpointGroup(dragPath, dagNode, x3dPF)
                elif xta == "MetadataSet":
                    isTransform = False
                    self.rkio.cMessage("Do nothing. MetadataSet nodes are not processed by this function.")
                
            if isTransform == True:
                ###########################################################################
                # Check this transform to see if it has a joint as a direct child. If so 
                # call a processHAnimHumoind method to process this transform as an 
                # HAnimHumanoid node.
                ###########################################################################
                if self.checkForMayaJoints(dagNode):
                    self.processHAnimHumanoid(       dragPath, dagNode, x3dPF)
                else:
                    self.processTransformSorting(    dragPath, dagNode, x3dPF)



    ###########################################################################################
    # Process 'transform' nodes that are the parent to leaf nodes such as cameras, lights, or
    # x3dSound nodes, and 'transform' nodes which correspond to typical X3D 'Transform' nodes.
    ###########################################################################################
    def processTransformSorting(self, dragPath, dagNode, x3dPF):
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
            self.processX3DTransform(dragPath, dagNode, x3dPF)


    #   Primary SceneGraph Traversal Function - Primarily Depth First
    #   pDagNode is the parent node of dagNode, which is the node about to be written.
    def traverseDownward(self, dragPath, dagNode, cField="children"):
        nodeName = dagNode.name()
        
        if self.rkio.checkIfIgnored(nodeName) == False:
            
            if self.rkio.checkForRawKeeNoExportLayer(dagNode) == False:
                #Use cMessage instead of print so that we can block Verbose Export at the cMessage Level
                self.rkio.cMessage("Node was NOT ignored: " + dagNode.typeName + ", NodeName: " + nodeName)
                if dagNode.typeName == "transform":
                    self.processMayaTransformNode(dragPath, dagNode, cField)
                elif dagNode.typeName == "mesh":
                    if dagNode.isIntermediateObject == True:
                        newDragPath, newDagNode = self.processForIntermediateMesh(dragPath, dagNode)
                        if newDagNode != None:
                            self.processMayaMesh(newDragPath, newDagNode, cField)
                    else:
                        self.processMayaMesh(dragPath, dagNode, cField)
                        
                elif dagNode.typeName == "lodGroup":
                    self.processMayaLOD(dragPath, dagNode, cField)
            else:
                self.rkio.cMessage("Node: " + nodeName + " will not be exported as it is connected to the 'RawKeeNoExport' Maya layer")
        else:
            self.rkio.cMessage("Sorry - Node: " + nodeName + " of Type: " + dagNode.typeName + " is not yet supported for RawKee export.")
            
            

#####################################################
############    Other Functions     #################
#####################################################

    def processForIntermediateMesh(self, dragPath, dagNode):
        newDragPath = None
        newDagNode  = None
        
        iRels = cmds.listRelatives(dagNode.name(), allDescendents=True, noIntermediate=True, fullPath=True)
        meshShapes = cmds.ls(iRels, type="mesh")
        
        if meshShapes:
            selection_list = om.MSelectionList()
            selection_list.add(meshShapes[0])
            mObj = selection_list.getDependNode(0)
            newDagNode = aom.MFnDagNode(mObj)
            newDragPath = dragPath
        
        return (newDragPath, newDagNode)
        
    
    def processMayaMesh(self, dragPath, dagNode, cField="children", cOffset=0, nOffset=0, sharedCoord="", sharedNormal=""):
        
        supMeshName = dagNode.name()

#        if self.rkio.checkIfHasBeen(supMeshName) == True:
#            self.rkio.useDecl(tNode, supMeshName, x3dParentNode, cField)
#            return
            
        newDragPath = dragPath + "|" + supMeshName
        
        myMesh = aom.MFnMesh(dagNode.object())
        
        shList1 = []
        shList2 = []
        
        shaders  = []
        groups   = []
        polygons = []
        
        shaders, meshComps = myMesh.getConnectedSetsAndMembers(0, True)

        # Generate Mesh / Shader Combo Mappings
        self.genMSComboMappings(myMesh, shaders, meshComps)
        
        # Check for Metadata - TODO: skipping how this is done here for the moment.
        
        x3dPF = []
        x3dPF.append(self.getX3DParent(dagNode, dragPath))
        x3dPF.append(cField)
        
        shLen = len(shaders)
        if shLen > 1:
            bna = self.processBasicNodeAddition(dagNode, x3dPF[0], x3dPF[1], "Group", supMeshName)
            if bna[0] == True:
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
        
        for idx in range(shLen):
            shapeName = supMeshName
            if shLen > 1:
                shapeName = shapeName + "_SubShape_" + str(idx)
                
            #boundingBoxSizeX boundingBoxSizeY boundingBoxSizeZ center boundingBoxCenterX
            
            sbna = self.processBasicNodeAddition(dagNode, x3dPF[0], x3dPF[1], "Shape", shapeName)
            if sbna[0] == False:
                
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
                self.processForAppearance(myMesh, shaders[idx], meshComps[idx], sbna[1], cField="appearance", index=idx)
                
                self.processForGeometry(  myMesh, shaders, meshComps, sbna[1], nodeName=shapeName, cField="geometry", nodeType="IndexedFaceSet", index=idx, gcOffset=cOffset, gnOffset=nOffset, gsharedCoord=sharedCoord, gsharedNormal=sharedNormal)


    def processForAppearance(self, myMesh, shadingEngineObj, component, parentNode, cField="appearance", index=0):
        texTrans = []
        depNode = aom.MFnDependencyNode(shadingEngineObj)
        
        mapJSON = myMesh.findPlug("x3dTextureMappings", False).asString()
        meshTMaps = json.loads(mapJSON)
        allMaps = meshTMaps['shadingEngines']
        mappings = allMaps[index]
        isStringRay = False

        print("Before Appearance")
        print(mapJSON)
        # Create an Appearance Node using the name of the Shader Engine node.
        bna = self.processBasicNodeAddition(depNode, parentNode, cField, "Appearance")
        if bna[0] == False:
            print("After Appearance")
            # Lists for tracking Maya texture nodes and place2dTexture* nodes - (*equivelent to X3D TextureTransform node)
            mTextureNodes        = []
            mTextureFields       = []
            retPlace2d           = []

            x3dAppearance = bna[1]
            matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())
            
            ##########################################################################################
            # *** Use normal maps designed for OpenGL. Do NOT use normal maps designed for Direct X. #
            ##########################################################################################
            # This gets exported as an X3D Material node. Yawn... this is boring.
            #############################################################################################
            if   matNode.typeName == "phong" or matNode.typeName == "phongE" or matNode.typeName == "blinn" or matNode.typeName == "lambert":
                newCField   = "material"
                newNodeType = "Material"
                
                ##########################################################
                # When exporting for non-inlined use for X3DOM.
                # X3DOM doesn't currently support the X3D 4.0 version
                # of the Material node, so we have to use 
                # CommonSurfaceShader instead, which is not standard
                # X3D and is exclusive to X3DOM only. CommonSurfaceShader
                # is an actual 'shader' so it needs to be added to the 
                # 'shaders' field of the Appearance node, instead of the
                # 'material' field like the Material node is added.
                ##########################################################
                
                xhtml = False
                hasDT = False
                
                print(self.exEncoding)
                if self.exEncoding == "html":
                    newCField = "shaders"
                    newNodeType = "CommonSurfaceShader"
                    xhtml = True
                    
                    
                x3dMat = self.processBasicNodeAddition(matNode, x3dAppearance, newCField, newNodeType)
                if x3dMat[0] == False:
                    material = x3dMat[1]
                    retPlace2d.clear()
                    
                    ambientIntensity = matNode.findPlug("diffuse", False)
                    ambientFactor    = matNode.findPlug("ambientColor", False)
                    ambientTexture   = matNode.findPlug("ambientColor", True )
                    diffuseColor     = matNode.findPlug("color", False)
                    diffuseTexture   = matNode.findPlug("color", True )
                    diffuseValue     = matNode.findPlug("diffuse", False)
                    emissiveColor    = matNode.findPlug("incandescence", False)
                    emissiveTexture  = matNode.findPlug("incandescence", True )
                    normalCamera     = matNode.findPlug("normalCamera" , True )

                    transparency     = matNode.findPlug("transparency", False)
                    alphaTexture     = matNode.findPlug("transparency", True )
                    
                    setTransmission = False
                    transmissionFactor = None
                    transmissionTexture = None
                    trDepth = None
                    trFocus = None
                    
                    if matNode.typeName == "phong" or matNode.typeName == "phongE" or matNode.typeName == "Blinn":
                        setTransmission     = True
                        transmissionFactor  = matNode.findPlug("translucence"     , False)
                        transmissionTexture = matNode.findPlug("translucence"     , True )
                        trDepth             = matNode.findPlug("translucenceDepth", False)
                        trFocus             = matNode.findPlug("translucenceFocus", False)
                    

                    
                    occlIsSet = False
                    occlusionStrength = None
                    occlusionTexture  = None
                    
                    reflIsSet = False
                    reflectivityValue = None
                    reflectionFactor  = None
                    reflectionTexture = None
                    
                    specularColor     = None
                    specularTexture   = None
                    specIsSet = False
                    
                    if   matNode.typeName != "lambert":
                        if xhtml == True:
                            reflectivityValue = matNode.findPlug("reflectivity"  , False)
                            reflectionFactor  = matNode.findPlug("reflectedColor", False)
                            reflectionTexture = matNode.findPlug("reflectedColor", True )
                            reflIsSet = True
                        else:
                            occlusionStrength = matNode.findPlug("reflectivity"  , False)
                            occlusionTexture  = matNode.findPlug("reflectedColor", True )
                            occlIsSet = True
                            
                        specularColor     = matNode.findPlug("specularColor", False)
                        specularTexture   = matNode.findPlug("specularColor", True )
                        specIsSet = True
                    
                    shineIsSet        = False
                    shininess         = None
                    shininessTexture  = None
                    
                    if matNode.typeName == "phongE":
                        # Highlight Size - ignored
                        shininess        = matNode.findPlug("roughness", False)
                        shininessTexture = matNode.findPlug("whiteness", True )
                        shineIsSet = True
                    elif matNode.typeName == "blinn":
                        shininess        = matNode.findPlug("eccentricity", False)
                        shininessTexture = matNode.findPlug("eccentricity", True )
                        shineIsSet = True
                    
                    texCount = 0
                    
                    if xhtml:
                        pass
                    else:
                        material.ambientIntensity = ambientIntensity.asFloat()
                    
                    ambTex = ambientTexture.source().node()
                    if not ambTex.isNull() and (ambTex.apiType() == rkfn.kTexture2d or ambTex.apiType() == rkfn.kFileTexture or ambTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(ambTex))
                        mTextureFields.append("ambientTexture")
                        if xhtml:
                            material.ambientTextureCoordinatesId = texCount
                            texCount += 1
                        else:
                            retPlace2d.append(None)
                    elif xhtml == True:
                        material.ambientFactor = (ambientFactor.child(0).asFloat(), ambientFactor.child(1).asFloat(), ambientFactor.child(2).asFloat())
                    
                    diffTex = diffuseTexture.source().node()
                    if not diffTex.isNull() and (diffTex.apiType() == rkfn.kTexture2d or diffTex.apiType() == rkfn.kFileTexture or diffTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(diffTex))
                        mTextureFields.append("diffuseTexture")
                        if xhtml:
                            material.diffuseTextureCoordinatesId = texCount
                            material.diffuseFactor = (diffuseValue.asFloat(), diffuseValue.asFloat(), diffuseValue.asFloat())
                            hasDT = True
                            texCount += 1
                        else:
                            material.diffuseColor = (1.0, 1.0, 1.0)

                        retPlace2d.append(None)
                        
                    else:
                        if xhtml:
                            material.diffuseFactor = (diffuseColor.child(0).asFloat(), diffuseColor.child(1).asFloat(), diffuseColor.child(2).asFloat())
                        else:
                            material.diffuseColor  = (diffuseColor.child(0).asFloat(), diffuseColor.child(1).asFloat(), diffuseColor.child(2).asFloat())
                    
                    emisTex = emissiveTexture.source().node()
                    if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kFileTexture or emisTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(emisTex))
                        mTextureFields.append("emissiveTexture")
                        if xhtml:
                            material.emissiveTextureCoordinatesId = texCount
                            texCount += 1
#                        else:
#                            retPlace2d.append(None)
                        retPlace2d.append(None) # Test Export for More Dynamic Content
                            
                    else:
                        if xhtml:
                            material.emissiveFactor = (emissiveColor.child(0).asFloat(), emissiveColor.child(1).asFloat(), emissiveColor.child(2).asFloat())
                        else:
                            material.emissiveColor  = (emissiveColor.child(0).asFloat(), emissiveColor.child(1).asFloat(), emissiveColor.child(2).asFloat())
                        
                    bumpObj = normalCamera.source().node()
                    if not bumpObj.isNull() and (bumpObj.apiType() == rkfn.kBump):
                        bumpNode = aom.MFnDependencyNode(bumpObj)
                        bdValue  = bumpNode.findPlug("bumpDepth" , False).asFloat()
                        nsValue  = bumpNode.findPlug("bumpFilter", False).asFloat()
                        normalBias  = (-1.0, -1.0, bdValue)
                        normalScale = (nsValue, nsValue, nsValue)
                        normalSpace = "TANGENT"
                        if bumpNode.findPlug("bumpInterp", False).asInt() == 2:
                            normalSpace = "OBJECT"
                        
                        normTex  = bumpNode.findPlug("bumpValue", True).source().node()
                        if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kFileTexture or normTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(normTex))
                            mTextureFields.append("normalTexture")
                            if xhtml:
                                material.normalBias  = normalBias
                                material.normalScale = normalScale
                                material.normalSpace = normalSpace
                                material.normalTextureCoordinatesId = texCount
                                texCount += 1
#                            else:
#                                retPlace2d.append(None)
                            retPlace2d.append(None) # Test Export for dynamic content
                        
                    if occlIsSet == True:
                        material.occlusionStrength = occlusionStrength.asFloat()
                        occlTex = occlusionTexture.source().node()
                        if not occlTex.isNull() and (occlTex.apiType() == rkfn.kTexture2d or occlTex.apiType() == rkfn.kFileTexture or occlTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(occlTex))
                            mTextureFields.append("occlusionTexture")
                            retPlace2d.append(None)
                            
                    if reflIsSet == True:
                        reflVal = reflectivityValue.asFloat()
                        reflTex = reflectionTexture.source().node()
                        if not reflTex.isNull() and (reflTex.apiType() == rkfn.kTexture2d or reflTex.apiType() == rkfn.kFileTexture or reflTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(reflTex))
                            mTextureFields.append("reflectionTexture")
                            material.reflectionFactor = (reflVal, reflVal, reflVal)

                            material.reflectionTextureCoordinatesId = texCount
                            texCount += 1
                        else:
                            material.reflectionFactor = (reflectionFactor.child(0).asFloat() * reflVal, reflectionFactor.child(1).asFloat() * reflVal, reflectionFactor.child(2).asFloat() * reflVal)
                        
                    
                    if specIsSet == True:
                        specTex = specularTexture.source().node()
                        if not specTex.isNull() and (specTex.apiType() == rkfn.kTexture2d or specTex.apiType() == rkfn.kFileTexture or specTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(specTex))
                            mTextureFields.append("specularTexture")
                            if xhtml:
                                material.specularTextureCoordinatesId = texCount
                                texCount += 1
                            else:
                                material.specularColor  = (1.0, 1.0, 1.0)
#                                retPlace2d.append(None)
                            retPlace2d.append(None) # Test export for more dynamic content
                        else:
                            if xhtml:
                                material.specularFactor = (specularColor.child(0).asFloat(), specularColor.child(1).asFloat(), specularColor.child(2).asFloat())
                            else:
                                material.specularColor  = (specularColor.child(0).asFloat(), specularColor.child(1).asFloat(), specularColor.child(2).asFloat())
                            
                    if shineIsSet == True:
                        shinTex = shininessTexture.source().node()
                        if not shinTex.isNull() and (shinTex.apiType() == rkfn.kTexture2d or shinTex.apiType() == rkfn.kFileTexture or shinTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(shinTex))
                            mTextureFields.append("shininessTexture")

                            if matNode.typeName == "phongE":
                                if xhtml:
                                    material.shininessFactor = shininess.asFloat()
                                else:
                                    material.shininess = 1 - shininess.asFloat()

                            if xhtml:
                                material.shininessTextureCoordinatesId = texCount
                                texCount += 1
#                            else:
#                                retPlace2d.append(None)
                            retPlace2d.append(None) # test export for more dynamic content
                        else:
                            if xhtml:
                                material.shininessFactor = shininess.asFloat()
                            else:
                                material.shininess = 1 - shininess.asFloat()
                    
                    trans = (transparency.child(0).asFloat() + transparency.child(1).asFloat() + transparency.child(2).asFloat()) / 3.0
                    if xhtml:
                        material.alphaFactor  = 1 - trans
                        alphaTex = alphaTexture.source().node()
                        if not alphaTex.isNull() and (alphaTex.apiType() == rkfn.kTexture2d or alphaTex.apiType() == rkfn.kFileTexture or alphaTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(alphaTex))
                            mTextureFields.append("alphaTexture")
                            material.alphaTextureCoordinatesId = texCount
                            texCount += 1
                        if setTransmission == True:
                            missionTex = transmissionTexture.source().node()
                            if not missionTex.isNull() and (missionTex.apiType() == rkfn.kTexture2d or missionTex.apiType() == rkfn.kFileTexture or missionTex.apiType() == rkfn.kLayeredTexture):
                                tmFactor = (trDepth.asFloat() + trFocus.asFloat()) / 2
                                mTextureNodes.append(aom.MFnDependencyNode(missionTex))
                                mTextureFields.append("transmissionTexture")
                                material.transmissionFactor = (tmFactor, tmFactor, tmFactor)
                                material.transmissionTextureCoordinatesId = texCount
                                texCount += 1
                            else:
                                tmFactor = transmissionFactor.asFloat() * ((trDepth.asFloat() + trFocus.asFloat())/2)
                                material.transmissionFactor = (tmFactor, tmFactor, tmFactor)
                    else:
                        material.transparency = trans
                    
                    mtexLen = len(mTextureNodes)
                    
                    print("MTEXTURE LENGTH: " + str(mtexLen))

                    if xhtml == False:
                        for a in range(mtexLen):
                            gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], material, mTextureFields[a])
                            if not gPlace2d.object().isNull():
                                texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                print("Mapping: " + mTextureFields[a] + "Mapping")
                                retPlace2d[a]  = gPlace2d
                    else:
                        for a in range(mtexLen):
                            gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], material, mTextureFields[a])
                            if not gPlace2d.object().isNull():
                                retPlace2d[a]  = gPlace2d
                                
                    '''
                    if xhtml == False:
                        for a in range(mtexLen):
                            gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], material, mTextureFields[a])
                            if not gPlace2d.object().isNull():
                                texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                retPlace2d[a]  = gPlace2d
                    else:
                        if hasDT == True:
                            idx = material.diffuseTextureCoordinatesId
                            gPlace2d = self.processTexture(mTextureNodes[idx].object().apiType(), mTextureNodes[idx], material, mTextureFields[idx])
                            retPlace2d[0] = gPlace2d
                    '''
                    
            #############################################################################################
            # This gets exported as an X3D PhysicalMaterial node
            # - RawKee expects one of two Dependency Graphs based on:
            #   1)  Textures exported from Adobe Substance 3D Painter 
            #       using the 'Unreal 4 Packed' template as described
            #       by this YouTube video:
            #       'How to Connect PBR Textures in Maya'               (By Abe Leal 3D)
            #           https://www.youtube.com/watch?v=Zy0dYnHMRPY
            #
            #   2)  The process of setting up a glTF PBR Materials for
            #       Maya as described by the Verge3D User Manual.
            #       'glTF PBR Materials / Maya'
            #           https://www.soft8soft.com/docs/manual/en/maya/GLTF-Materials.html
            #############################################################################################
            elif matNode.typeName == "aiStandardSurface" or matNode.typeName == "standardSurface":
                #Everything goes in the try incase the user didn't setup node connections properly.
                newCField = "material"
                newNodeType = "PhysicalMaterial"
                
                xhtml = False

                if self.exEncoding == "html":
                    newCField = "shaders"
                    newNodeType = "CommonSurfaceShader"
                    xhtml = True

                try:
                    x3dMat = self.processBasicNodeAddition(matNode, x3dAppearance, newCField, newNodeType)
                    if x3dMat[0] == False:
                        physMat = x3dMat[1]
                        comShad = x3dMat[1]
                        
                        aiBase       = matNode.findPlug("base", True)
                        aiBaseColor  = matNode.findPlug("baseColor", True)
                        aiBaseColorF = matNode.findPlug("baseColor", False)
                        aiMetalness  = matNode.findPlug("metalness", True)
                        aiSpecular   = matNode.findPlug("specular", True)
                        aiRoughness  = matNode.findPlug("specularRoughness", True)
                        aiNormalCam  = matNode.findPlug("normalCamera", True)
                        aiEmisColor  = matNode.findPlug("emissionColor", True)
                        aiEmisColorF = matNode.findPlug("emissionColor", False)
                        aiEmisWeight = matNode.findPlug("emission", True)
                        aiOpacity    = matNode.findPlug("opacity", False)
                        

                        # Check for an aiMultiply node
                        checkTest = aiBaseColor.source().node()
                        checkNode = aom.MFnDependencyNode(checkTest)
                        
                        # Branch to 'Abe Leal 3D' / 'Unreal 4 Packed' Style of Maya material
                        if not checkTest.isNull() and checkNode.typeName == "aiMultiply":
                            
                            retPlace2d.clear()
                            texCount = 0
                            
                            baseTex = checkNode.findPlug("input1", True).source().node()
                            if not baseTex.isNull() and (baseTex.apiType() == rkfn.kTexture2d or baseTex.apiType() == rkfn.kFileTexture or baseTex.apiType() == rkfn.kLayeredTexture):
                                mTextureNodes.append(aom.MFnDependencyNode(baseTex))
                                if xhtml == False:
                                    mTextureFields.append("baseTexture")
                                    retPlace2d.append(None)
                                else:
                                    mTextureFields.append("diffuseTexture")
                                    comShad.diffuseTextureCoordinatesId = texCount
                                    texCount += 1

                            if xhtml == False:
                                occlTex = checkNode.findPlug("input2R", True).source().node()
                                if not occlTex.isNull() and (occlTex.apiType() == rkfn.kTexture2d or occlTex.apiType() == rkfn.kFileTexture or occlTex.apiType() == rkfn.kLayeredTexture):
                                    mTextureNodes.append(aom.MFnDependencyNode(baseTex))
                                    mTextureFields.append("occlusionTexture")
                                    retPlace2d.append(None)
                                
                                
                            emisTex = aiEmisColor.source().node()
                            eWeight = aiEmisWeight.asFloat()
                            if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kFileTexture or emisTex.apiType() == rkfn.kLayeredTexture):
                                mTextureNodes.append(aom.MFnDependencyNode(emisText))
                                mTextureFields.append("emissiveTexture")
                                if xhtml == False:
                                    retPlace2d.append(None)
                                    physMat.emissiveColor  = (eWeight, eWeight, eWeight)
                                else:
                                    comShad.emissiveFactor = (eWeight, eWeight, eWeight)
                                    comShad.emissiveTextureCoordinatesId = texCount
                                    texCount += 1
                            else:
                                if xhtml == False:
                                    physMat.emissiveColor  = (aiEmisColorF.child(0).asFloat() * eWeight, aiEmisColorF.child(1).asFloat() * eWeight, aiEmisColorF.child(2).asFloat() * eWeight)
                                else:
                                    comShad.emissiveFactor = (aiEmisColorF.child(0).asFloat() * eWeight, aiEmisColorF.child(1).asFloat() * eWeight, aiEmisColorF.child(2).asFloat() * eWeight)

                            
                            if xhtml == False:
                                metlTex = aiMetalness.source().node()
                                if not metlTex.isNull() and (metlTex.apiType() == rkfn.kTexture2d or metlTex.apiType() == rkfn.kFileTexture or metlTex.apiType() == rkfn.kLayeredTexture):
                                    mTextureNodes.append(aom.MFnDependencyNode(metlTex))
                                    mTextureFields.append("metallicRoughnessTexture")
                                    retPlace2d.append(None)
                                else:
                                    rougTex = aiRoughness.source().node()
                                    if not rougTex.isNull() and (rougTex.apiType() == rkfn.kTexture2d or rougTex.apiType() == rkfn.kFileTexture or rougTex.apiType() == rkfn.kLayeredTexture):
                                        mTextureNodes.append(aom.MFnDependencyNode(rougTex))
                                        mTextureFields.append("metallicRoughnessTexture")
                                        retPlace2d.append(None)
                            else:
                                pass
                            

                            normBmp = aiNormalCam.source().node()
                            if not normBmp.isNull():
                                bump2d = aom.MFnDependencyNode(normBmp)
                                if bump2d.typeName == "bump2d":
                                    normTex = bump2d.findPlug("bumpValue", True).source().node()
                                    if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kFileTexture or normTex.apiType() == rkfn.kLayeredTexture):
                                        mTextureNodes.append(aom.MFnDependencyNode(normTex))
                                        mTextureFields.append("normalTexture")
                                        if xhtml == False:
                                            retPlace2d.append(None)
                                        else:
                                            comShad.normalTextureCoordinatesId = texCount
                                            texCount += 1
                                            
                            if xhtml == False:
                                physMat.transparency = 1 - ( (aiOpacity.child(0).asFloat() + aiOpacity.child(1).asFloat() + aiOpacity.child(2).asFloat()) / 3.0)
                            else:
                                comShad.alphaFactor  = (aiOpacity.child(0).asFloat() + aiOpacity.child(1).asFloat() + aiOpacity.child(2).asFloat()) / 3.0
                            
                            mtexLen = len(mTextureNodes)
                            
                            for a in range(mtexLen):
                                if xhtml == False:
                                    gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], physMat, mTextureFields[a])
                                    if not gPlace2d.isNull():
                                        texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                        setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                        retPlace2d[a]  = gPlace2d
                                else:
                                    gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], comShad, mTextureFields[a])
                                    if not gPlace2d.isNull():
                                        retPlace2d[a]  = gPlace2d
                        
                        
                        #############################################################################################
                        # Otherwise assume Verge3D Style of Maya material - (More styles can be added in the future)
                        #############################################################################################
                        else:
                            # aiBase       = matNode.findPlug("base")
                            # aiBaseColor  = matNode.findPlug("baseColor")
                            # aiMetalness  = matNode.findPlug("metalness")
                            # aiSpecular   = matNode.findPlug("specular")
                            # aiRoughness  = matNode.findPlug("specularRoughness")
                            # aiNormalCam  = matNode.findPlug("normalCamera")
                            # aiEmisColor  = matNode.findPlug("emissionColor")
                            # aiEmisWeight = matNode.findPlug("emission")
                            # aiOpacity    = matNode.findPlug("opacity", False)

                            retPlace2d.clear()
                            texCount = 0

                            baseTex = aiBaseColor.source().node()
                            if not baseTex.isNull() and (baseTex.apiType() == rkfn.kTexture2d or baseTex.apiType() == rkfn.kFileTexture or baseTex.apiType() == rkfn.kLayeredTexture):
                                mTextureNodes.append(aom.MFnDependencyNode(baseTex))
                                if xhtml == False:
                                    mTextureFields.append("baseTexture")
                                    retPlace2d.append(None)
                                else:
                                    mTextureFields.append("diffuseTexture")
                                    comShad.diffuseTextureCoordinatesId = texCount
                                    texCount += 1
                            else:
                                if xhtml == False:
                                    physMat.baseColor     = (aiBaseColorF.child(0).asFloat(), aiBaseColorF.child(1).asFloat(), aiBaseColorF.child(2).asFloat())
                                else:
                                    comShad.diffuseFactor = (aiBaseColorF.child(0).asFloat(), aiBaseColorF.child(1).asFloat(), aiBaseColorF.child(2).asFloat())


                            if xhtml == False:
                                omrTex = aiBase.source().node()
                                if not  omrTex.isNull() and ( omrTex.apiType() == rkfn.kTexture2d or  omrTex.apiType() == rkfn.kFileTexture or  omrTex.apiType() == rkfn.kLayeredTexture):
                                    genTexture = aom.MFnDependencyNode(omrTex)
                                    mTextureNodes.append(genTexture)
                                    mTextureFields.append("metallicRoughnessTexture")
                                    retPlace2d.append(None)

                                    mTextureNodes.append(genTexture)
                                    mTextureFields.append("occlusionTexture")
                                    retPlace2d.append(None)

                                
                            bumpTex = aiNormalCam.source().node()
                            if not bumpTex.isNull() and bumpTex.apiType() == rkfn.kBump:
                                normTex = aom.MFnDependencyNode(bumpTex).findPlug("bumpValue", True).source().node()
                                if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kFileTexture or normTex.apiType() == rkfn.kLayeredTexture):
                                    mTextureNodes.append(aom.MFnDependencyNode(normTex))
                                    mTextureFields.append("normalTexture")
                                    if xhtml == False:
                                        retPlace2d.append(None)
                                    else:
                                        comShad.normalTextureCoordinatesId = texCount
                                        texCount += 1

                            
                            emisTex = aiEmisColor.source().node()
                            eWeight = aiEmisWeight.asFloat()
                            if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kFileTexture or emisTex.apiType() == rkfn.kLayeredTexture):
                                mTextureNodes.append(aom.MFnDependencyNode(emisText))
                                mTextureFields.append("emissiveTexture")
                                if xhtml == False:
                                    retPlace2d.append(None)
                                    physMat.emissiveColor  = (eWeight, eWeight, eWeight)
                                else:
                                    comShad.emissiveFactor = (eWeight, eWeight, eWeight)
                                    comShad.emissiveTextureCoordinatesId = texCount
                                    texCount += 1
                            else:
                                if xhtml == False:
                                    physMat.emissiveColor  = (aiEmisColorF.child(0).asFloat() * eWeight, aiEmisColorF.child(1).asFloat() * eWeight, aiEmisColorF.child(2).asFloat() * eWeight)
                                else:
                                    comShad.emissiveFactor = (aiEmisColorF.child(0).asFloat() * eWeight, aiEmisColorF.child(1).asFloat() * eWeight, aiEmisColorF.child(2).asFloat() * eWeight)

                                
                            if xhtml == False:
                                physMat.transparency = 1 - ( (aiOpacity.child(0).asFloat() + aiOpacity.child(1).asFloat() + aiOpacity.child(2).asFloat()) / 3.0)
                            else:
                                comShad.alphaFactor  = (aiOpacity.child(0).asFloat() + aiOpacity.child(1).asFloat() + aiOpacity.child(2).asFloat()) / 3.0
                            
                            mtexLen = len(mTextureNodes)

                            print("MTEXTURE LENGTH - B: " + str(mtexLen))
                            
                            for a in range(mtexLen):
                                if xhtml == False:
                                    gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], physMat, mTextureFields[a])
                                    if not gPlace2d.isNull():
                                        texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                        setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                        retPlace2d[a]  = gPlace2d
                                else:
                                    gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], comShad, mTextureFields[a])
                                    if not gPlace2d.isNull():
                                        retPlace2d[a]  = gPlace2d
                                        
                except:
                    self.rkio.cMessage("Error when attempting to export Arnold aiStandardShader/StandardShader as PhysicalMaterial node. Skipping Material export. Check your shader inputs.")
                    return
                    
            #############################################################################################
            # This gets exported as an X3D PhysicalMaterial node
            # - RawKee expects one the Dependency Graph based on the 
            #       process of setting up a glTF PBR Materials for
            #       Maya as described by the Verge3D User Manual.
            #       'glTF PBR Materials / Maya'
            #           https://www.soft8soft.com/docs/manual/en/maya/GLTF-Materials.html
            #############################################################################################
            elif matNode.typeName == "usdPreviewSurface":
                newCField = "material"
                newNodeType = "PhysicalMaterial"

                xhtml = False

                if self.exEncoding == "html":
                    newCField = "shaders"
                    newNodeType = "CommonSurfaceShader"
                    xhtml = True

                try:
                    x3dMat = self.processBasicNodeAddition(matNode, x3dAppearance, newCField, newNodeType)
                    if x3dMat[0] == False:
                        physMat = x3dMat[1]
                        comShad = x3dMat[1]
                        
                        usdDiffuseColor   = matNode.findPlug("diffuseColor", True)
                        usdDiffuseColorF  = matNode.findPlug("diffuseColor", False)
                        usdEmissiveColor  = matNode.findPlug("emissiveColor", True)
                        usdEmissiveColorF = matNode.findPlug("emissiveColor", False)
                        usdMetallic       = matNode.findPlug("metallic", True)
                        usdRoughness      = matNode.findPlug("roughness", True)
                        usdOcclusion      = matNode.findPlug("occlusion", True)
                        usdNormal         = matNode.findPlug("normal", True)
                        usdSpecularColor  = matNode.findPlug("specularColor", True)
                        usdSpecularColorF = matNode.findPlug("specularColor", False)
                        usdOpacity        = matNode.findPlug("opacity", False)
 
                        retPlace2d.clear()
                        texCount = 0

                        diffTex = usdDiffuseColor.source().node()
                        if not diffTex.isNull() and (diffTex.apiType() == rkfn.kTexture2d or diffTex.apiType() == rkfn.kFileTexture or diffTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(diffTex))
                            if xhtml == False:
                                mTextureFields.append("baseTexture")
                                retPlace2d.append(None)
                            else:
                                mTextureFields.append("diffuseTexture")
                                comShad.diffuseTextureCoordinatesId = texCount
                                texCount += 1
                        else:
                            if xhtml == False:
                                physMat.baseColor     = (usdDiffuseColorF.child(0).asFloat(), usdDiffuseColorF.child(1).asFloat(), usdDiffuseColorF.child(2).asFloat())
                            else:
                                comShad.diffuseFactor = (usdDiffuseColorF.child(0).asFloat(), usdDiffuseColorF.child(1).asFloat(), usdDiffuseColorF.child(2).asFloat())


                        #TODO: Figure out how to make this work for CommonSurfaceShader
                        if xhtml == False:
                            occlTex = usdOcclusion.source().node()
                            if not occlTex.isNull() and ( occlTex.apiType() == rkfn.kTexture2d or  occlTex.apiType() == rkfn.kFileTexture or  occlTex.apiType() == rkfn.kLayeredTexture):
                                occlTexture = aom.MFnDependencyNode(occlTex)
                                mTextureNodes.append(occlTexture)
                                mTextureFields.append("occlusionTexture")
                                retPlace2d.append(None)
                            else:
                                physMat.occlusionStrength = usdOcclusion.asFloat()

                            # TODO - Address 'Use Specular Workflow' attribute

                            metlTex = usdMetallic.source().node()
                            rougTex = usdRoughness.source().node()
                            if not metlTex.isNull() and (metlTex.apiType() == rkfn.kTexture2d or metlTex.apiType() == rkfn.kFileTexture or metlTex.apiType() == rkfn.kLayeredTexture):
                                metalTexture = aom.MFnDependencyNode(metlTex)
                                mTextureNodes.append(metalTexture)
                                mTextureFields.append("metallicRoughnessTexture")
                                retPlace2d.append(None)
                                if rougTex.isNull():
                                    physMat.roughness = usdRoughness.asFloat()
                            else:
                                physMat.metallic = usdMetallic.asFloat()
                                if not rougTex.isNull() and (rougTex.apiType() == rkfn.kTexture2d or rougTex.apiType() == rkfn.kFileTexture or rougTex.apiType() == rkfn.kLayeredTexture):
                                    roughTexture = aom.MFnDependencyNode(rougTex)
                                    mTextureNodes.append(roughTexture)
                                    mTextureFields.append("metallicRoughnessTexture")
                                    retPlace2d.append(None)


                        normTex = usdNormal.source().node()
                        if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kFileTexture or normTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(normTex))
                            mTextureFields.append("normalTexture")
                            if xhtml == False:
                                retPlace2d.append(None)
                            else:
                                comShad.normalTextureCoordinatesId = texCount
                                texCount += 1
                        
                        
                        emisTex = usdEmissiveColor.source().node()
                        eWeight = 1.0
                        if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kFileTexture or emisTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(emisText))
                            mTextureFields.append("emissiveTexture")
                            if xhtml == False:
                                retPlace2d.append(None)
                                physMat.emissiveColor  = (eWeight, eWeight, eWeight)
                            else:
                                comShad.emissiveFactor = (eWeight, eWeight, eWeight)
                                comShad.emissiveTextureCoordinatesId = texCount
                                texCount += 1
                        else:
                            if xhtml == False:
                                physMat.emissiveColor  = (usdEmissiveColorF.child(0).asFloat(), usdEmissiveColorF.child(1).asFloat(), usdEmissiveColorF.child(2).asFloat())
                            else:
                                comShad.emissiveFactor = (usdEmissiveColorF.child(0).asFloat(), usdEmissiveColorF.child(1).asFloat(), usdEmissiveColorF.child(2).asFloat())
                        
                            
                        if xhtml == False:
                            physMat.transparency = 1 - usdOpacity.asFloat()
                        else:
                            comShad.alphaFactor  = usdOpacity.asFloat()

                            
                        mtexLen = len(mTextureNodes)
                        
                        print("MTEXTURE LENGTH - C: " + str(mtexLen))

                        for a in range(mtexLen):
                            if xhtml == False:
                                gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], physMat, mTextureFields[a])
                                if not gPlace2d.isNull():
                                    texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                    setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                    retPlace2d[a]  = gPlace2d
                            else:
                                gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], comShad, mTextureFields[a])
                                if not gPlace2d.isNull():
                                    retPlace2d[a]  = gPlace2d
                except:
                    self.rkio.cMessage("Error when attempting to export usePreviewSurface as PhysicalMaterial node. Skipping Material export. Check your shader inputs.")
                    return
                    
                    
            #############################################################################################
            # This gets exported as an X3D PhysicalMaterial node. For an example of how
            # a Stringray PBS material gets created by the Maya artist, visit the following
            # YouTube Videos:
            #   Export textures from Substance                                          ##########################################
            #   - 'Exporting Textures from Substance Painter for Maya Stingray PBS'     ##  *** Do NOT use Direct X normal maps ## 
            #       https://www.youtube.com/watch?v=t3N5_eKRbYg    (By JoAnn Patel)     ##########################################
            #   - 'Setting up a Maya Stingray PBS shader'                               ##      X3D is a WebGL-friendly format. ##
            #       https://www.youtube.com/watch?v=_SAJ9zOfnc8    (By JoAnn Patel)     ##########################################
            # Generic videos
            #   - 'How to create a Stingray PBS Shader Material in Maya - Maya High Poly to Low Poly Tutorial'
            #       https://www.youtube.com/watch?v=OXCrR5X_eTc
            #   - '3 Introduction PBS, Maya Stingray. (English)'
            #       https://www.youtube.com/watch?v=xFYezP0Qrgc
            #   - '004 Maya Stingray Shader'
            #       https://www.youtube.com/watch?v=UazuTTr5t_4
            #############################################################################################
            elif matNode.typeName == "StingrayPBS":
                #StingrayPBS uses an internal single TextureTransform for all Textures, and thus must
                # also use the same UVSet for all the textures. If you're trying to use more than one
                # UVSet for this mesh, then you're probably want to use a different shader. Same goes
                # for if you want to animate your textures via TextureTansform nodes.
                isStringRay = True
                
                newCField = "material"
                newNodeType = "PhysicalMaterial"

                xhtml = False

                if self.exEncoding == "html":
                    newCField = "shaders"
                    newNodeType = "CommonSurfaceShader"
                    xhtml = True

                try:
                    x3dMat = self.processBasicNodeAddition(matNode, x3dAppearance, newCField, newNodeType)
                    if x3dMat[0] == False:
                        physMat = x3dMat[1]
                        comShad = x3dMat[1]

                        styColrMap = matNode.findPlug("TEX_color_map",     True)
                        styEmisMap = matNode.findPlug("TEX_emissive_map",  True)
                        styMetlMap = matNode.findPlug("TEX_metallic_map",  True)
                        styRougMap = matNode.findPlug("TEX_roughness_map", True)
                        styNormMap = matNode.findPlug("TEX_normal_map",    True)
                        styOcclMap = matNode.findPlug("TEX_ao_map",        True)
                        
                        styBaseColor = matNode.findPlug("base_color",         False)
                        styEmisColor = matNode.findPlug("emissive",           False)
                        styEmisInten = matNode.findPlug("emissive_intensity", False)
                        styMetallic  = matNode.findPlug("metallic",           False)
                        styRoughness = matNode.findPlug("roughness",          False)
                        
                        emMul = styEmisInten.asFloat()
                        if xhtml == False:
                            physMat.baseColor     = (styBaseColor.child(0).asFloat(), styBaseColor.child(1).asFloat(), styBaseColor.child(2).asFloat())
                            physMat.emissiveColor = (styEmisColor.child(0).asFloat() * emMul, styEmisColor.child(1).asFloat() * emMul, styEmisColor.child(2).asFloat() * emMul)
                            physMat.metallic      = styMetallic.asFloat()
                            physMat.roughness     = styRoughness.asFloat()
                        else:
                            comShad.diffuseFactor   = (styBaseColor.child(0).asFloat(), styBaseColor.child(1).asFloat(), styBaseColor.child(2).asFloat())
                            comShad.emissiveFactor  = (styEmisColor.child(0).asFloat() * emMul, styEmisColor.child(1).asFloat() * emMul, styEmisColor.child(2).asFloat() * emMul)
                            comShad.shininessFactor = (styRoughness.asFloat(), styRoughness.asFloat(), styRoughness.asFloat())

                        retPlace2d.clear()
                        texCount = 0

                        diffTex = styColrMap.source().node()
                        if not diffTex.isNull() and (diffTex.apiType() == rkfn.kTexture2d or diffTex.apiType() == rkfn.kFileTexture or diffTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(diffTex))
                            mTextureFields.append("baseTexture")
                            retPlace2d.append(None)


                        #TODO: Figure out how to map this data properly to CommonSurfaceShader
                        if xhtml == False:
                            occlTex = styOcclMap.source().node()
                            if not occlTex.isNull() and ( occlTex.apiType() == rkfn.kTexture2d or  occlTex.apiType() == rkfn.kFileTexture or  occlTex.apiType() == rkfn.kLayeredTexture):
                                occlTexture = aom.MFnDependencyNode(occlTex)
                                mTextureNodes.append(occlTexture)
                                mTextureFields.append("occlusionTexture")
                                retPlace2d.append(None)

                            metlTex = styMetlMap.source().node()
                            rougTex = styRougMap.source().node()
                            if not metlTex.isNull() and (metlTex.apiType() == rkfn.kTexture2d or metlTex.apiType() == rkfn.kFileTexture or metlTex.apiType() == rkfn.kLayeredTexture):
                                metalTexture = aom.MFnDependencyNode(metlTex)
                                mTextureNodes.append(metalTexture)
                                mTextureFields.append("metallicRoughnessTexture")
                                retPlace2d.append(None)
                            else:
                                if not rougTex.isNull() and (rougTex.apiType() == rkfn.kTexture2d or rougTex.apiType() == rkfn.kFileTexture or rougTex.apiType() == rkfn.kLayeredTexture):
                                    roughTexture = aom.MFnDependencyNode(rougTex)
                                    mTextureNodes.append(roughTexture)
                                    mTextureFields.append("metallicRoughnessTexture")
                                    retPlace2d.append(None)


                        normTex = styNormMap.source().node()
                        if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kFileTexture or normTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(normTex))
                            mTextureFields.append("normalTexture")
                            if xhtml == False:
                                retPlace2d.append(None)
                            else:
                                comShad.normalTextureCoordinatesId = texCount
                                texCount += 1

                        
                        emisTex = styEmisMap.source().node()
                        if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kFileTexture or emisTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(emisText))
                            mTextureFields.append("emissiveTexture")
                            if xhtml == False:
                                retPlace2d.append(None)
                            else:
                                comShad.emissiveTextureCoordinatesId = texCount
                                texCount += 1

                        
                        mtexLen = len(mTextureNodes)

                        print("MTEXTURE LENGTH - D: " + str(mtexLen))
                        
                        for a in range(mtexLen):
                            if xhtml == False:
                                gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], physMat, mTextureFields[a])
                                if not gPlace2d.isNull():
                                    texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                    setattr(material, mTextureFields[a] + "Mapping", texturemapping)
                                    retPlace2d[a]  = gPlace2d
                            else:
                                gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], comShad, mTextureFields[a])
                                if not gPlace2d.isNull():
                                    retPlace2d[a]  = gPlace2d
                                    
                except:
                    self.rkio.cMessage("Error when attempting to export StingrayPBS as PhysicalMaterial node. Skipping Material export. Check your shader inputs.")
                    return
                    
                    
            #############################################################################################
            # TODO: but low priority
            # The intent is export this as an X3D PackagedShader node - probably
            #############################################################################################
            elif matNode.typeName == "shaderfxShader":
                print("The material shaderfxShader is currently unsupported, but is on the future TODO list.")


            #############################################################################################
            # Set TextureTransform's
            #############################################################################################
            textTransforms = []
            
            for place in retPlace2d:
                print("Called the place.")
                if place:# != None:
                    print("Place is not None")
                    textTransforms.append(place)
            
            if   len(textTransforms) == 1:
                x3dTTrans = self.processBasicNodeAddition(textTransforms[0], x3dAppearance, "textureTransform", "TextureTransform")
                if x3dTTrans[0] == False:
                    self.setTextureTransformFields(textTransforms[0], x3dTTrans[1])

                '''
                if   len(textTransforms) == 1 or isStringRay == True :
                    if isStringRay == False:
                        x3dTTrans = self.processBasicNodeAddition(textTransforms[0], x3dAppearance, "textureTransform", "TextureTransform")
                        if x3dTTrans[0] == False:
                            self.setTextureTransformFields(textTransforms[0], x3dTTrans[1])
                    else:
                        srTTName = matNode.name() + "_TT" #Blah
                        #depNode, x3dParentNode, x3dFieldName, x3dType, nodeName=None
                        srTTrans = self.processBasicNodeAddition(None, x3dAppearance, "textureTransform", "TextureTransform", srTTName)
                        if srTTrans[0] == False:
                            uOff = matNode.findPlug("uv_offsetX", False).asFloat()
                            vOff = matNode.findPlug("uv_offsetY", False).asFloat()
                            uSca = matNode.findPlug("uv_scaleX",  False).asFloat()
                            vSca = matNode.findPlug("uv_scaleY",  False).asFloat()
                            srTTrans.translation = (uOff, vOff)
                            srTTrans.scale       = (uSca, vSca)
                '''

            elif len(textTransforms)  > 1:
                x3dMTTrans = self.processBasicNodeAddition(matNode, x3dAppearance, "textureTransform", "MultiTextureTransform", matNode.name() + "_MTT")
                if x3dMTTrans[0] == False:
                    for idx in range(len(textTransforms)):
                        x3dTTrans = self.processBasicNodeAddition(textTransforms[idx], x3dMTTrans[1], "textureTransform", "TextureTransform")
                        if x3dTTrans[0] == False:
                            self.setTextureTransformFields(textTransforms[idx], x3dTTrans[1])
                        
                    
            ########################################################################
            # If you need another material such as something that comes in a plugin
            # from Vray or Maxwell then please join the RawKee development team.
            #
            #   Potential Options:
            #       - Renderaman 
            #       - VRay
            #       - Redshift
            #       - Maxwell
            #
            ########################################################################
    
    # Assumes that the function has been passed a 'Connected' plug)
    def surfGraphForTextureNode(self, matPlug):
        tFound = False
        tNode  = None
        
        textIter = aom.MItDependencyGraph(matPlug, rkfn.kFileTexture, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        while not textIter.isDone():
            try:
                cNode = textIter.currentNode()
                if tFound == False and cNode.apiType() == rkfn.kFileTexture:
                    tFound = True
                    tNode  = aom.MFnDependencyNode(cNode)
            except:
                print("failed kFileTexture")
                
            textIter.next()

        textIter = aom.MItDependencyGraph(matPlug, rkfn.kTexture2d, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)

        if tFound == False:
            while not textIter.isDone():
                try:
                    cNode = textIter.currentNode()
                    if tFound == False and cNode.apiType() == rkfn.kTexture2d:
                        tFound = True
                        tNode  = aom.MFnDependencyNode(cNode)
                except:
                    print("failed kTexture2d")
                
                textIter.next()

        return tFound, tNode

    
    def genMSComboMappings(self, mesh, shaders, components):
        mappings = []
        
        for i in range(len(shaders)):
            mappings.append("")
            shader = shaders[i]
            comp   = components[i]
            depNode = aom.MFnDependencyNode(shader)
            matPlug = depNode.findPlug("surfaceShader", True)
            
            if matPlug.isConnected:
                matNode = aom.MFnDependencyNode(matPlug.source().node())
                
                usedUVSets, texNodes = self.getUsedUVSetsAndTexturesInOrder(mesh, shader)
                
                mapInt  = 0
                mapStr  = '{"shaderName":"' + depNode.name() + '",'
                mapStr += '"mappings":['
############
                if  matNode.typeName == "phong" or matNode.typeName == "phongE" or matNode.typeName == "blinn" or matNode.typeName == "lambert":
                    
                    matAmbientColor  = matNode.findPlug("ambientColor", True)                 # ambientTexture
                    matColor         = matNode.findPlug("color", True)                        # diffuseTexture
                    matIncandescence = matNode.findPlug("incandescence", True)                # emissiveTexture
                    matNormalCamera  = matNode.findPlug("normalCamera", True)                 # normalTexture
                    
                    matReflectedColor = None
                    matSpecularColor  = None
                    matWhiteness      = None
                    
                    if matNode.typeName != "lambert":
                        matReflectedColor = matNode.findPlug("reflectedColor", True)          # occlusionTexture
                        matSpecularColor  = matNode.findPlug("specularColor", True)           # specularTexture
                        if  matNode.typeName == "phongE":
                            matWhiteness  = matNode.findPlug("whiteness", True)               # shininessTexture
                        else:
                            matWhiteness  = matNode.findPlug("reflectedColor", True)          # shininessTexture
                    
                    ambientTexture   = None
                    diffuseTexture   = None
                    emissiveTexture  = None
                    normalTexture    = None
                    occlusionTexture = None
                    specularTexture  = None
                    shininessTexture = None
                    
                    ####################################################################################
                    # surfGraphForTextureNode only returns True if apiType is kTexture2d or kFileTexture
                    ####################################################################################
                    
                    # ambientTextureMapping
                    if matAmbientColor.isConnected:
                        tFound, ambientTexture = self.surfGraphForTextureNode(matAmbientColor)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(ambientTexture)
                            mIdx  = self.extractSetTexMatch(ambientTexture, texNodes)
                            mapStr += '{"fieldName":"ambientTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    
                    if matColor.isConnected:
                        tFound, diffuseTexture = self.surfGraphForTextureNode(matColor)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(diffuseTexture)
                            mIdx  = self.extractSetTexMatch(diffuseTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"diffuseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        else:
                            print("Diffuse Texture Not Found")
                    else:
                        print("matColor is not connected")
                    
                    if matIncandescence.isConnected:
                        tFound, emissiveTexture = self.surfGraphForTextureNode(matIncandescence)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(emissiveTexture)
                            mIdx  = self.extractSetTexMatch(emissiveTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"emissiveTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                            
                    if matNormalCamera.isConnected:
                        tFound, normalTexture = self.surfGraphForTextureNode(matNormalCamera)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(normalTexture)
                            mIdx  = self.extractSetTexMatch(normalTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"normalTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    
                    if matNode.typeName != "lambert":
                        if matReflectedColor.isConnected:
                            tFound, occlusionTexture = self.surfGraphForTextureNode(matReflectedColor)
                            if tFound == True:
                                p2dTT = self.getPlace2dFromMayaTexture(occlusionTexture)
                                mIdx  = self.extractSetTexMatch(occlusionTexture, texNodes)
                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"occlusionTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1

                        if matSpecularColor.isConnected:
                            tFound, specularTexture = self.surfGraphForTextureNode(matSpecularColor)
                            if tFound == True:
                                p2dTT = self.getPlace2dFromMayaTexture(specularTexture)
                                mIdx  = self.extractSetTexMatch(specularTexture, texNodes)
                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"specularTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1
                        
                        if matWhiteness.isConnected:
                            tFound, shininessTexture = self.surfGraphForTextureNode(matWhiteness)
                            if tFound == True:
                                p2dTT = self.getPlace2dFromMayaTexture(shininessTexture)
                                mIdx  = self.extractSetTexMatch(shininessTexture, texNodes)
                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"shininessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1
                else:
                    # Attribute Names:
                    # Default to StingRay PBS names
                    attColor = "TEX_color_map"
                    attEmiss = "TEX_emissive_map"
                    attMetal = "TEX_metallic_map"
                    attRough = "TEX_roughness_map"
                    attNorm  = "TEX_normal_map"
                    attOccl  = "TEX_ao_map"
                    attExtra = ""
                    
                    if matNode.typeName == "usdPreviewSurface":
                        attColor = "diffuseColor"
                        attEmiss = "emissiveColor"
                        attMetal = "metallic"
                        attRough = "roughness"
                        attNorm  = "normal"
                        attOccl  = "occlusion"
                        
                        #Test for Specular Color
                        usdSpecularColor = matNode.findPlug("specularColor", True)
                        if usdSpecularColor.isConnected:
                            attRough = "specularColor"
                    elif matNode.typeName == "aiStandardSurface" or matNode.typeName == "standardSurface":
                        attColor = "baseColor"
                        attEmiss = "emission"
                        attMetal = "metalness"#         B
                        attRough = "specularRoughness"# G
                        attNorm  = "normalCamera"
                        attOccl  = "specular"#          R
                        
                        #Test for Multiplier Node for 'Abe Leal 3D' / 'Unreal 4 Packed' Style
                        ssBaseColor = matNode.findPlug("baseColor", True)
                        if ssBaseColor.isConnected:
                            ssNode = ssBaseColor.source().node()
                            ssDepNode = aom.MFnDependencyNode(ssNode)
                            if ssDepNode.typeName == "aiMultiply":
                                attExtra = "baseColor"
                    
                    # aiStandardSurface or standardSurface
                    #ssBaseColor  = matNode.findPlug("baseColor", True)#                 color                                          (Verge3D/Other Style of Maya material)
                    #                                                                    aiMultiply - input1: color, input2: occlusion  ('Abe Leal 3D' / 'Unreal 4 Packed' Style)
                    #ssEmisWeight = matNode.findPlug("emission", True)#                  emissive                                       (All Styles)
                    #ssMetalness  = matNode.findPlug("metalness", True)#                 metallic                                       (All Styles)
                    #ssRoughness  = matNode.findPlug("specularRoughness", True)#         roughness                                      (All Styles)
                    #ssSpecular   = matNode.findPlug("specular", True)#                  occlusion (also with 'base' attribute)         (Verge3D Style of Maya material)
                    #ssNormalCam  = matNode.findPlug("normalCamera", True)#              normal                                         (All Styles)
                    
                    # USD Preview Surface
                    #usdDiffuseColor   = matNode.findPlug("diffuseColor", True)#         color
                    #usdEmissiveColor  = matNode.findPlug("emissiveColor", True)#        emissive
                    #usdMetallic       = matNode.findPlug("metallic", True)#             metallic                                       (Verge 3D Style)
                    #usdRoughness      = matNode.findPlug("roughness", True)#            roughness                                      (Verge 3D Style)
                    #usdOcclusion      = matNode.findPlug("occlusion", True)#            occlusion
                    #usdNormal         = matNode.findPlug("normal", True)#               normal
                    #usdSpecularColor  = matNode.findPlug("specularColor", True)#        metallic/roughess                              (Other style)
                    #usdOpacity        = matNode.findPlug("opacity", False)
                    
                    # Stringray PBS
                    #styColrMap = matNode.findPlug("TEX_color_map",     True)#           color
                    #styEmisMap = matNode.findPlug("TEX_emissive_map",  True)#           emissive
                    #styMetlMap = matNode.findPlug("TEX_metallic_map",  True)#           metallic
                    #styRougMap = matNode.findPlug("TEX_roughness_map", True)#           roughness
                    #styNormMap = matNode.findPlug("TEX_normal_map",    True)#           normal
                    #styOcclMap = matNode.findPlug("TEX_ao_map",        True)#           occlusion
                    
                    matColor = matNode.findPlug(attColor, True)
                    matOccl  = matNode.findPlug(attOccl,  True)
                    if attExtra == "baseColor":
                        attColor = "input1"
                        attOccl  = "input2R"
                        ssNode   = matNode.findPlug(attExtra, True).source().node()
                        matColor = aom.MFnDependencyNode(ssNode).findPlug(attColor)
                        matOccl  = aom.MFnDependencyNode(ssNode).findPlug(attOccl)
                    matEmiss = matNode.findPlug(attEmiss, True)
                    matMetal = matNode.findPlug(attMetal, True)
                    matRough = matNode.findPlug(attRough, True)
                    matNorm  = matNode.findPlug(attNorm,  True)
                    
                    if matColor.isConnected:
                        tFound, baseTexture = self.surfGraphForTextureNode(matColor)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(baseTexture)
                            mIdx  = self.extractSetTexMatch(baseTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"baseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    
                    if matEmiss.isConnected:
                        tFound, emissiveTexture = self.surfGraphForTextureNode(matEmiss)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(emissiveTexture)
                            mIdx  = self.extractSetTexMatch(emissiveTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"emissiveTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    
                    # Ideally, we'd look for a way to combine separate textures here. But that's advanced coding for another time or location in the code. For now
                    # we have to assume that these Texutres are the same texture in the DependencyGraph
                    if matMetal.isConnected:
                        tFound, metallicRoughnessTexture = self.surfGraphForTextureNode(matMetal)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(metallicRoughnessTexture)
                            mIdx  = self.extractSetTexMatch(metallicRoughnessTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"metallicRoughnessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        elif matRough.isConnected:
                            ttFound, metallicRoughnessTexture = self.surfGraphForTextureNode(matRough)
                            if ttFound == True:
                                p2dTT = self.getPlace2dFromMayaTexture(metallicRoughnessTexture)
                                mIdx  = self.extractSetTexMatch(metallicRoughnessTexture, texNodes)
                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"metallicRoughnessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1
                    
                    # This gets weird, in that in the X3D PhysicalMaterial node, these are likely to be separate Textures, but in Maya they are often linked to the same
                    # texture node as the Roughness and Metallic shader attributes
                    if matOccl.isConnected:
                        tFound, occlusionTexture = self.surfGraphForTextureNode(matOccl)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(occlusionTexture)
                            mIdx  = self.extractSetTexMatch(occlusionTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"occlusionTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    
                    if matNorm.isConnected:
                        tFound, normalTexture = self.surfGraphForTextureNode(matNorm)
                        if tFound == True:
                            p2dTT = self.getPlace2dFromMayaTexture(normalTexture)
                            mIdx  = self.extractSetTexMatch(normalTexture, texNodes)
                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"normalTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
############
                mapStr += ']}'
                
                mappings[i] = mapStr
                
            else:
                print("No SurfaceShader Connection Found")
    
        mapJSON = '{"shadingEngines":['
        
        mapLen = len(mappings)
        for mIdx in range(mapLen):
            mapJSON += mappings[mIdx]
            if mIdx < mapLen -1:
                mapJSON += ','
        mapJSON += ']}'

        pFound = False
        try:
            plug = mesh.findPlug("x3dTextureMappings", False)
            plug.setString(mapJSON)
        except:
            attrFn = aom.MFnTypedAttribute()
            newAttr = attrFn.create("x3dTextureMappings", "x3dTMaps", aom.MFnData.kString)
            attrFn.storable = False
            attrFn.keyable  = False
            mesh.addAttribute(newAttr)
            
            plug = mesh.findPlug("x3dTextureMappings", False)
            plug.setString(mapJSON)


    '''
    def genMSComboMappings(self, mesh, shaders, components):
        mappings = []
        
        for i in range(len(shaders)):
            mappings.append("")
            shader  = shaders[i]
            comp    = components[i]
            
            depNode = aom.MFnDependencyNode(shader)
            matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())

            usedUVSets, texNodes  = self.getUsedUVSetsAndTexturesInOrder(mesh, shader)
            
            mapInt  = 0
            mapStr  = '{"shaderName":"' + depNode.name() + '",'
            mapStr += '"mappings":['
            
            if   matNode.typeName == "phong" or matNode.typeName == "phongE" or matNode.typeName == "blinn" or matNode.typeName == "lambert":
                matAmbientColor  = matNode.findPlug("ambientColor", True)                 # ambientTexture
                matColor         = matNode.findPlug("color", True)                        # diffuseTexture
                matIncandescence = matNode.findPlug("incandescence", True)                # emissiveTexture
                matNormalCamera  = matNode.findPlug("normalCamera", True)                 # normalTexture
                
                matReflectedColor = None
                matSpecularColor  = None
                matWhiteness      = None
                
                if matNode.typeName != "lambert":
                    matReflectedColor = matNode.findPlug("reflectedColor", True)          # occlusionTexture
                    matSpecularColor  = matNode.findPlug("specularColor", True)           # specularTexture
                    if  matNode.typeName == "phongE":
                        matWhiteness  = matNode.findPlug("whiteness", True)               # shininessTexture
                    else:
                        matWhiteness  = matNode.findPlug("reflectedColor", True)          # shininessTexture
                
                ambientTexture   = None
                diffuseTexture   = None
                emissiveTexture  = None
                normalTexture    = None
                occlusionTexture = None
                specularTexture  = None
                shininessTexture = None
        
                # ambientTextureMapping
                chkObject = matAmbientColor.source().node()
                ambientTexture = aom.MFnDependencyNode(chkObject)
                if ambientTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                    p2dTT = self.getPlace2dFromMayaTexture(ambientTexture)
                    mIdx  = self.extractSetTexMatch(ambientTexture, texNodes)
                    mapStr += '{"fieldName":"ambientTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                    mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                    mapInt +=1
                
                chkObject = matColor.source().node()
                diffuseTexture = aom.MFnDependencyNode(chkObject)
                if diffuseTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                    p2dTT = self.getPlace2dFromMayaTexture(diffuseTexture)
                    mIdx  = self.extractSetTexMatch(diffuseTexture, texNodes)
                    if mapInt > 0:
                        mapStr += ','
                    mapStr += '{"fieldName":"diffuseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                    mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                    mapInt +=1
                
                chkObject = matIncandescence.source().node()
                emissiveTexture = aom.MFnDependencyNode(chkObject)
                if emissiveTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                    p2dTT = self.getPlace2dFromMayaTexture(emissiveTexture)
                    mIdx  = self.extractSetTexMatch(emissiveTexture, texNodes)
                    if mapInt > 0:
                        mapStr += ','
                    mapStr += '{"fieldName":"emissiveTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                    mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                    mapInt +=1
                
                chkObject = matNormalCamera.source().node()
                aBump2d = aom.MFnDependencyNode(chkObject)
                if aBump2d != None and aBump2d.typeName == "bump2d":
                    chkObject = aBump2d.findPlug("bumpValue", True).source().node()
                    normalTexture = aom.MFnDependencyNode(chkObject)
                    if normalTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                        p2dTT = self.getPlace2dFromMayaTexture(normalTexture)
                        mIdx  = self.extractSetTexMatch(normalTexture, texNodes)
                        if mapInt > 0:
                            mapStr += ','
                        mapStr += '{"fieldName":"normalTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                        mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                        mapInt +=1
                    
                if matReflectedColor:
                    chkObject = matReflectedColor.source().node()
                    occlusionTexture = aom.MFnDependencyNode(chkObject)
                    if occlusionTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                        p2dTT = self.getPlace2dFromMayaTexture(occlusionTexture)
                        mIdx  = self.extractSetTexMatch(occlusionTexture, texNodes)
                        if mapInt > 0:
                            mapStr += ','
                        mapStr += '{"fieldName":"occlusionTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                        mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                        mapInt +=1
                    
                if matWhiteness:
                    chkObject = matWhiteness.source().node()
                    shininessTexture = aom.MFnDependencyNode(chkObject)
                    if shininessTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                        p2dTT = self.getPlace2dFromMayaTexture(shininessTexture)
                        mIdx  = self.extractSetTexMatch(shininessTexture, texNodes)
                        if mapInt > 0:
                            mapStr += ','
                        mapStr += '{"fieldName":"shininessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                        mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                        mapInt +=1

                if matSpecularColor:
                    chkObject = matSpecularColor.source().node()
                    specularTexture = aom.MFnDependencyNode(chkObject)
                    if specularTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kFileTexture or chkObject.apiType() == rkfn.kLayeredTexture):
                        p2dTT = self.getPlace2dFromMayaTexture(specularTexture)
                        mIdx  = self.extractSetTexMatch(specularTexture, texNodes)
                        if mapInt > 0:
                            mapStr += ','
                        mapStr += '{"fieldName":"specularTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                        mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                        mapInt +=1
                    
            elif matNode.typeName == "aiStandardSurface":
                aiBase       = matNode.findPlug("base", True)
                aiBaseColor  = matNode.findPlug("baseColor", True)
                aiMetalness  = matNode.findPlug("metalness", True)
                aiRoughness  = matNode.findPlug("specularRoughness", True)
                aiNormalCam  = matNode.findPlug("normalCamera", True)
                aiEmisWeight = matNode.findPlug("emission", True)

                baseTexture = None
                occlTexture = None
                normTexture = None
                rougTexture = None
                metlTexture = None
                emisTexture = None
                
                checkNode = aom.MFnDependencyNode(aiBaseColor.source().node())
                if checkNode != None:
                    if checkNode.typeName == "aiMultiply":
                        # baseTextureMapping
                        baseTexture = aom.MFnDependencyNode(checkNode.findPlug("input1", True).source().node())
                        if baseTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(baseTexture)
                            mIdx  = self.extractSetTexMatch(baseTexture, texNodes)
                            mapStr += '{"fieldName":"baseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        # occlusionTextureMapping
                        occlTexture = aom.MFnDependencyNode(checkNode.findPlug("input2R", True).source().node())
                        if occlTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(occlTexture)
                            mIdx  = self.extractSetTexMatch(occlTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"occlusionTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        
                        # metallicRoughnessTextureMapping
                        metlTexture = aom.MFnDependencyNode(aiMetalness.source().node())
                        rougTexture = aom.MFnDependencyNode(aiRoughness.source().node())
                        useOccl = False
                        if metlTexture !=None and occlTexture !=None and metlTexture.name() == occlTexture.name():
                            useOccl = True
                        elif rougTexture !=None and occlTexture !=None and rougTexture.name() == occlTexture.name():
                            useOccl = True
                            
                        if useOccl:
                            p2dTT = self.getPlace2dFromMayaTexture(occlTexture)
                            mIdx  = self.extractSetTexMatch(occlTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"metallicRoughnessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        elif metlTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(metlTexture)
                            mIdx  = self.extractSetTexMatch(metlTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"metallicRoughnessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1

                        elif rougTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(rougTexture)
                            mIdx  = self.extractSetTexMatch(rougTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"metallicRoughnessTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1

                        # normalTextureMapping
                        bump2d = aom.MFnDependencyNode(aiNormalCam.source().node())
                        if bum2d != None and bump2d.typeName == "bump2d":
                            normTexture = aom.MFnDependencyNode(bump2d.findPlug("bumpValue", True).source().node())
                            if normTexture != None:
                                p2dTT = self.getPlace2dFromMayaTexture(normTexture)
                                mIdx  = self.extractSetTexMatch(normTexture, texNodes)

                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"normalTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1

                                                
                        # emissiveTextureMapping
                        emisTexture = aom.MFnDependencyNode(aiEmisColor.source().node())
                        if emisTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(emisTexture)
                            mIdx  = self.extractSetTexMatch(emisTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"emissiveTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                    else:
                        # baseTextureMapping
                        baseTexture = aom.MFnDependencyNode(aiBaseColor.source().node())
                        if baseTexture != None:
                            p2dTT = self.getPlace2dFromMayaTexture(baseTexture)
                            mIdx  = self.extractSetTexMatch(baseTexture, texNodes)
                            mapStr += '{"fieldName":"baseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        # occlusionTextureMapping and metallicRoughnessTextureMapping
#                        print("Base End")
#                        bValue = aiBase.source().node()
#                        if bValue == None:
#                            print("BValue was None")
#                        else:
#                            print("BValue was not None")
#                        print("BValue")
#                        print(type(bValue))
#                        print(bValue.apiType())
#                        if aiBase.isConnected:
#                            print("aiBase is connected")
#                        else:
#                            print("aiBase is not connected")
                        omrTexture = aom.MFnDependencyNode(aiBase.source().node())
                        if omrTexture != None:
#                            print("OMR Name: " + omrTexture.name())
#                            print(omrTexture)
#                            print(None)
                            p2dTT = self.getPlace2dFromMayaTexture(omrTexture)
                            mIdx  = self.extractSetTexMatch(omrTexture, texNodes)

                            if mapInt > 0:
                                mapStr += ','
                            mapStr += '{"fieldName":"occlusionTextureMapping","mapName":"'              + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        
                            mapStr += ',{"fieldName":"metallicRoughnessTextureMapping","mapName":"'     + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                            mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                            mapInt +=1
                        print("Roughness End")

                        # normalTextureMapping
                        bump2d = aom.MFnDependencyNode(aiNormalCam.source().node())
                        if bum2d != None and bump2d.typeName == "bump2d":
                            normTexture = aom.MFnDependencyNode(bump2d.findPlug("bumpValue", True).source().node())
                            if normTexture != None:
                                p2dTT = self.getPlace2dFromMayaTexture(normTexture)
                                mIdx  = self.extractSetTexMatch(normTexture, texNodes)

                                if mapInt > 0:
                                    mapStr += ','
                                mapStr += '{"fieldName":"normalTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                                mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                                mapInt +=1
                        print("Normal End")

                                                
                        
            elif matNode.typeName == "standardSurface":
                pass
            elif matNode.typeName == "usdPreviewSurface":
                pass
            elif matNode.typeName == "StingrayPBS":
                pass
            elif matNode.typeName == "shaderfxShader":
                pass

            mapStr += ']}'
            
            mappings[i] = mapStr
            
        mapJSON = '{"shadingEngines":['
        
        mapLen = len(mappings)
        for mIdx in range(mapLen):
            mapJSON += mappings[mIdx]
            if mIdx < mapLen -1:
                mapJSON += ','
        mapJSON += ']}'

        pFound = False
        try:
            plug = mesh.findPlug("x3dTextureMappings", False)
            plug.setString(mapJSON)
        except:
            attrFn = aom.MFnTypedAttribute()
            newAttr = attrFn.create("x3dTextureMappings", "x3dTMaps", aom.MFnData.kString)
            attrFn.storable = False
            attrFn.keyable  = False
            mesh.addAttribute(newAttr)
            
            plug = mesh.findPlug("x3dTextureMappings", False)
            plug.setString(mapJSON)
    '''

    
    def extractSetTexMatch(self, texture, texNodes):
        for i in range(len(texNodes)):
            try:
                print(texture.name())
                print(texNodes[i].name())
                if texture.name() == texNodes[i].name():
                    return i
            except:
                print(str(i))
                pass

    
    def getMappingValue(self, mappings, fieldName):
        for item in mappings['mappings']:
            if item['fieldName'] == fieldName:
                return item['mapName']
    
            
    def setTextureTransformFields(self, place2d, x3dtt):
        # Set the 'center' field of TextureTransform
        x3dtt.center = (place2d.findPlug("offsetU", False).asFloat(), place2d.findPlug("offsetV", False).asFloat())

        # Set the 'mapping' field of TextureTransform
        try:
            tmVal = place2d.findPlug("x3dTextureMapping", False).asString()
            x3dtt.mapping = tmVal
        except:
            print("x3dTextureMapping is not defined.")

        # Set the 'metadata' field of TextureTransform
        # TODO
        
        # Set the 'rotation' field of TextureTransform
        x3dtt.rotation = place2d.findPlug("rotateFrame", False).asFloat()

        # Set the 'scale' field of TextureTransform
        try:
            x3dtt.scale = (place2d.findPlug("coverageU", False).asFloat(), place2d.findPlug("coverageV", False).asFloat())
        except:
            print("Fail in set Texture Transform")
        
        # Set the 'translation' field of TextureTransform
        x3dtt.translation = (place2d.findPlug("translateFrameU", False).asFloat(), place2d.findPlug("translateFrameV", False).asFloat())

    #This method may be eliminated
    def processMaterial(self):
        pass

    def processForGeometry(self, myMesh, shaders, meshComps, x3dParentNode, nodeName=None, cField="geometry", nodeType="IndexedFaceSet", index=0, gcOffset=0, gnOffset=0, gsharedCoord="", gsharedNormal=""):
        meshMP = 0
        if nodeName == None:
            nodeName = myMesh.name()

        depNode = aom.MFnDependencyNode(shaders[index])

        mapJSON = myMesh.findPlug("x3dTextureMappings", False).asString()
        meshTMaps = json.loads(mapJSON)
        allMaps = meshTMaps['shadingEngines']
        mappings = allMaps[index]

        if nodeType == "IndexedFaceSet":
            msList = aom.MSelectionList()
            msList.add(myMesh.name())
            tDagPath = msList.getDagPath(0)
            
            mIter = aom.MItMeshPolygon(tDagPath, meshComps[index])
            
            geomName = nodeName + "_IFS"
            if index > 1:
                geomName = geomName + "_" + str(index)
                
            bna = self.processBasicNodeAddition(myMesh, x3dParentNode, cField, "IndexedFaceSet", geomName)
            if bna[0] == False:
                # TODO: Future code for implementing 'attrib'

                ##### Add an X3D Coordiante Node
                
                #### use gsharedCoord if this is a mesh in an HAnimHumanoid
                if gsharedCoord != "":
                    coordbna = self.processBasicNodeAddition(myMesh, bna[1], "coord", "Coordinate", gsharedCoord)

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
                    geoNameCoord = nodeName + "_Coord"
                    coordbna = self.processBasicNodeAddition(myMesh, bna[1], "coord", "Coordinate", geoNameCoord)
                    if coordbna[0] == False:
                        # TODO: Metadata processing
                        
                        
                        # point field of Coordinate node
                        points = myMesh.getFloatPoints()
                        meshMP = len(points)
                        for point in points:
                            coordbna[1].point.append((point.x, point.y, point.z))
                
                        # Using the MItMeshPolygon Iterator and the propoper sub-component
                        # this secion of the code builds the array of MFInt32 field of IndexedFaceSet
                        while not mIter.isDone():
                            #vertices = mIter.getVertices()
                            nVerts = mIter.polygonVertexCount()
                            for vIdx in range(nVerts):
                                mIdx = mIter.vertexIndex(vIdx)
                                bna[1].coordIndex.append(mIdx)
                            bna[1].coordIndex.append(-1)
                            mIter.next()
                    
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
                if self.rkNormalOpts > 0 and self.rkNormalOpts < 4:
                    bna[1].creaseAngle = self.rkCreaseAngle

                ##### Set Norml Node, normalIndex, and normalPerVertex
                if   self.rkNormalOpts == 0:
                    # Though not technically required, set
                    # normalPerVertex to True and then do nothing
                    # more with normals because we are using
                    # the default values for IndexedFaceSet nodes
                    # where there is no other info required by the spec.
                    ##### bna[1].normalPerVertex = True
                    pass
                    
                elif self.rkNormalOpts == 1 or self.rkNormalOpts == 4:
                    # Normals Per Vertex Values
                    bna[1].normalPerVertex = True
                    
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], idx=index, nOffset=gnOffset, sharedNormal=gsharedNormal)
                else:
                    # Normals Per Face Values
                    bna[1].normalPerVertex = False
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], npv=False, idx=index, nOffset=gnOffset, sharedNormal=gsharedNormal)

                ### faceIDs and mappings and uvSetName
                if mappings != None:
                   
                    mapLen = len(mappings['mappings'])
                    bnaTXC = None
                    
                    mtxHasBeen = False
                    if mapLen > 1:
                        bnaTXC = self.processBasicNodeAddition(myMesh, bna[1], "texCoord", "MultiTextureCoordinate", geomName + "_MTC_" + str(index))
                        mtxHasBeen = bnaTXC[0]

                    # Write out TextureCoordinate nodes
                    if mtxHasBeen == False and mapLen > 0:

                        tPolyVerts = 0
                        mIter.reset()
                        while not mIter.isDone():
                            tPolyVerts += mIter.polygonVertexCount()
                            mIter.next()
                    
                        # The texCoords list is a list of lists, so that
                        # it is a list of "points" array for each TextureCoordinate that aligns each 'mapping'.
                        # The total number of 2D (u,v) poins in each points array is equal to the value of 
                        # tPolyVerts. We are populating each list in the texCoords list with points equal to
                        # (0.0, 0.0)
                        texCoords = []
                        for item in mappings['mappings']:
                            tpv = []
                            for cval in range(tPolyVerts):
                                tpv.append((0.0, 0.0))
                            texCoords.append(tpv)
                        
                        
                        idxCount = 0
                        mIter.reset()
                        while not mIter.isDone():
                            '''
                            nVerts = mIter.polygonVertexCount()
                            for t in range(mapLen):
                                tMap = mappings['mappings'][t]
                                hasUV = mIter.hasUVs(tMap['uvSetName'])
                                ul = []
                                vl = []
                                if hasUV == True:
                                    ul, vl = mIter.getUVs(tMap['uvSetName'])
                                else:
                                    for lIdx in range(nVerts):
                                        ul.append(0.0)
                                        vl.append(0.0)

                                for uIdx in range(nVerts):
                                    texCoords[t][idxCount+uIdx] = (ul[uIdx], vl[uIdx])
                            
                            for nvIdx in range(nVerts):
                                bna[1].texCoordIndex.append(idxCount)
                                idxCount += 1
                            
                            bna[1].texCoordIndex.append(-1)
                            mIter.next()
                            '''
                            nVerts = mIter.polygonVertexCount()
                            hasUV  = mIter.hasUVs()
                            
                            for vIdx in range(nVerts):#vertices:
                                mu = 0.0
                                mv = 0.0
                                
                                for t in range(mapLen):
                                    tMap = mappings['mappings'][t]
                                    if hasUV == True:
                                        mu,mv = mIter.getUV(vIdx, tMap['uvSetName'])
                                    texCoords[t][idxCount] = (mu, mv)
                                
                                bna[1].texCoordIndex.append(idxCount)
                                idxCount += 1
                            bna[1].texCoordIndex.append(-1)
                            mIter.next()

                        txcParent = bna[1]
                        if bnaTXC != None:
                            txcParent = bnaTXC[1]
                            
                        for n in range(mapLen):
                            item = mappings['mappings'][n]
                            txc = self.processBasicNodeAddition(myMesh, txcParent, "texCoord", "TextureCoordinate", geomName + "_TC_" + str(index) + "_" + str(n))
                            if txc[0] == False:
                                for ptx in texCoords[n]:
                                    txc[1].point.append(ptx)
                                txc[1].mapping = item['mapName']



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
        
        bna = self.processBasicNodeAddition(myMesh, x3dParent, cField, nodeType, colorNodeName)
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
            bna = self.processBasicNodeAddition(myMesh, x3dParent, cField, "Normal", sharedNormal)

            while not mIter.isDone():
                if npv == True:
                    tns = mIter.getNormals()
                    for tn in tns:
                        x3dParent.normalIndex.append(fCount + nOffset)
                        fCount += 1
                    x3dParent.normalIndex.append(-1)
                else:
                    x3dParent.normalIndex.append(fCount + nOffset)
                    fCount += 1
                mIter.next()
        else:
            bna = self.processBasicNodeAddition(myMesh, x3dParent, cField, "Normal", normalNodeName)
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
                        tn = mIter.getNormal()
                        bna[1].vector.append((tn.x, tn.y, tn.z))
                        x3dParent.normalIndex.append(fCount)
                        fCount += 1
                    
                    mIter.next()

                # Assign MFVec3f to the node.
                #bna[1].vector = mNormal

        
                
            
    
    def getUsedUVSetsAndTexturesInOrder(self, myMesh, shader):
        uvSetNames = myMesh.getUVSetNames()
        hasTex = False
        
        usedUVSets = []
        texNodes   = []
        
        textureList = self.gatherShaderTextures(shader) #getShaderTexturesInOrder(shader)
        print("TextureList: " + str(len(textureList)))
        
        if len(textureList) == 0:
            return (usedUVSets, texNodes)
        
        for t in textureList:
            print("GetUsed - textureList: " + t.name())
            usedUVSets.append("map1")
            texNodes.append(None)
            
        for i in range(len(uvSetNames)):
            print("My UV Set Names: " + uvSetNames[i])
            print("My mesh name: " + myMesh.name())
            assocTexObj = myMesh.getAssociatedUVSetTextures(uvSetNames[i])
            
            for j in range(len(assocTexObj)):
                texDep = aom.MFnDependencyNode(assocTexObj[j])
                print("Assoc Text Obj - texDep: " + texDep.name())
                
                for k in range(len(textureList)):
                    if texDep.name() == textureList[k].name():
                        usedUVSets[k] = uvSetNames[i]
                        texNodes[k]   = texDep

        return (usedUVSets, texNodes)



    def gatherShaderTextures(self, shader):
        textureList = []
        
        depNode = aom.MFnDependencyNode(shader) #shader is a shadingEngine object
        matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())

        matIter = aom.MItDependencyGraph(matNode.object(), rkfn.kFileTexture, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        while not matIter.isDone():
            mObject = matIter.currentNode()
            if mObject.apiType() == rkfn.kLayeredTexture or mObject.apiType() == rkfn.kTexture2d or mObject.apiType() == rkfn.kFileTexture:
                tFound = False
                tNode = aom.MFnDependencyNode(mObject)

                for t in textureList:
                    if t.name() == tNode.name():
                        tFound = True

                if tFound == False:
                    textureList.append(tNode)
                    print("Add to my Texture List: " + tNode.name())
                if mObject.apiType() == rkfn.kLayeredTexture:
                    matIter.prune()
        
            matIter.next()
        
        return textureList



    #################################################################
    # This function is probably going to go away.
    #################################################################
    def getShaderTexturesInOrder(self, shader):
        textureList = []
        
        depNode = aom.MFnDependencyNode(shader) #shader is a shadingEngine object
        matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())
        

        #################################################################################
        # Material Node Texture Fields:
        #################################################################################
        # SFNode   [in,out] ambientTexture            NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] diffuseTexture            NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] emissiveTexture           NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] normalTexture             NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] occlusionTexture          NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] shininessTexture          NULL         [X3DSingleTextureNode]
        # SFNode   [in,out] specularTexture           NULL         [X3DSingleTextureNode]
        ##################################################################################
        # Need new iterator for each plug capable of having a texture node connected to it
        # through an upsteam connection of the DependencyGraph.
        ##################################################################################
        
        if   matNode.typeName == "phong":
            pass
            
        elif matNode.typeName == "phongE":
            pass
            
        elif matNode.typeName == "blinn":
            pass
            
        elif matNode.typeName == "lambert":
            pass

        #################################################################################
        # PysicalMaterial Node Texture Fields:
        #################################################################################
        # SFNode   [in,out] baseTexture                     NULL   [X3DSingleTextureNode]
        # SFNode   [in,out] emissiveTexture                 NULL   [X3DSingleTextureNode]
        # SFNode   [in,out] metallicRoughnessTexture        NULL   [X3DSingleTextureNode]
        # SFNode   [in,out] normalTexture                   NULL   [X3DSingleTextureNode]
        # SFNode   [in,out] occlusionTexture                NULL   [X3DSingleTextureNode]
        ##################################################################################
        # Need new iterator for each plug capable of having a texture node connected to it
        # through an upsteam connection of the DependencyGraph.
        ##################################################################################
        
        elif matNode.typeName == "aiStandardSurface":
            # Assumes that this SufaceShader is connected to textures using a graph similar in layout to that defined
            # in the Abe Leal 3D Tutorial on YouTube
            # https://www.youtube.com/watch?v=Zy0dYnHMRPY
            aiSIter = aom.MItDependencyGraph(matNode.object(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
            
            while not aiSIter.isDone():
                mObject = aiSIter.currentNode()
                if mObject.apiType() == rkfn.kLayeredTexture or mObject.apiType() == rkfn.kTexture2d or mObject.apiType() == rkfn.kFileTexture:
                    tFound = False
                    tNode = aom.MFnDependencyNode(mObject)

                    for t in textureList:
                        if t.name() == tNode.name():
                            tFound = True

                    if tFound == False:
                        textureList.append(tNode)
                    if mObject.apiType() == rkfn.kLayeredTexture:
                        aiSIter.prune()
                
                aiSIter.next()

        elif matNode.typeName == "standardSurface":
            pass

        elif matNode.typeName == "usdPreviewSurface":
            pass

        elif matNode.typeName == "StingrayPBS":
            pass

        elif matNode.typeName == "shaderfxShader":
            pass #TODO: not yet supported
        
        #################################################################################
        # UnlitMaterial Node Texture Fields (TODO: NOT YET SUPPORTED):
        #################################################################################
        # SFNode   [in,out] emissiveTexture                 NULL   [X3DSingleTextureNode]
        # SFNode   [in,out] normalTexture                   NULL   [X3DSingleTextureNode]
        ##################################################################################
        # Need new iterator for each plug capable of having a texture node connected to it
        # through an upsteam connection of the DependencyGraph.
        ##################################################################################
             
        return textureList
             
        ##################################################
        #       Shading Models                           #
        ##################################################
        # Two Shading Models in the 3D world:
        #    - Metal Roughness
        #      - Base Color
        #      - Roughness
        #      - metallic
        #    - Specular Glossiness
        #      - diffuse
        #      - glossiness
        #      - specular
        #
        # Recommended YouTube Video Search - 'Using Substance textures in maya'
        # - How to Connect PBR Texture in Maya - By Abe Leal 3D
        #   https://www.youtube.com/watch?v=Zy0dYnHMRPY
        #
        # Other maps used:
        #    - ambient occlusion - help to get a little bit of extra shadow
        #    - normal (map)      - captures the extra detail when baking from a high poly to low poly model
        #    - height (map)      - used for displacement
        ##################################################

    
        
    def processTexture(self, mApiType, mTextureNode, x3dParent, x3dField, getPlace2d=True):
        
        relativeTexPath = self.rkImagePath
        fullWebTexPath  = self.rkBaseDomain + self.rkSubDir + relativeTexPath
        localTexWrite   = self.activePrjDir + "/" + relativeTexPath
        
        x3dNodeType = "PixelTexture"
        mPlace2d = None
        if getPlace2d:
            mPlace2d = self.getPlace2dFromMayaTexture(mTextureNode)
        
        if mApiType == rkfn.kTexture2d or mApiType == rkfn.kFileTexture:
            if mTextureNode.typeName == "file":
                if  self.rkFileTexNode == 0 or self.rkFileTexNode == 1:
                    x3dNodeType = "ImageTexture"
                    x3dURIData  = ""

                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        filePath = mTextureNode.findPlug("fileTextureName", False).asString()
                        fileName = self.rkint.getFileName(filePath)
                        fileExt  = os.path.splitext(fileName)[1]
                        fileName = os.path.splitext(fileName)[0]
                    
                    if   self.rk2dFileFormat == 1:
                        fileName = fileName + ".png"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'png')
                        
                    elif self.rk2dFileFormat == 2:
                        fileName = fileName + ".jpg"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'jpg')
                        
                    elif self.rk2dFileFormat == 3:
                        fileName = fileName + ".gif"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileFormatConvert(filePath, localTexWrite, 'gif')
                        
                    elif self.rk2dFileFormat == 4:
                        fileName = fileName + ".webp"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        
                        self.rkint.fileConvertToWebP(filePath, localTexWrite)
                    else:
                        fileName = fileName + fileExt
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName

                        if self.rk2dTexWrite == True:
                            localTexWrite   = localTexWrite   + fileName
                            movePath = self.imageMoveDir + "/" + fileName
                            self.rkint.copyFile(filePath, movePath)
                        else:
                            localTexWrite = filePath

                    # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                    if self.rkFileTexNode == 1:
                        print("Printing LocalTexWrite:\n" + localTexWrite )
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        x3dTexture[1].url.append(x3dURIData)
                    else:
                        x3dTexture[1].url.append(fileName       )
                        x3dTexture[1].url.append(relativeTexPath)
                        x3dTexture[1].url.append(fullWebTexPath )
                        
                    if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                        x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                        x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()

                else:
                    x3dNodeType = "PixelTexture"
                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        print("PixelTexture One - Around 2725")
                        x3dTexture[1].image = self.rkint.image2pixel(mTextureNode.findPlug("fileTextureName", False).asString())

                        if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                            x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                            x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()

            elif mTextureNode.typeName == "movie":
                x3dNodeType = "MovieTexture"
                x3dURIData  = ""
                
                x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                if x3dTexture[0] == False:
                    filePath = mTextureNode.findPlug("fileTextureName", False).asString()
                    fileName = self.rkint.getFileName(filePath)
                    fileExt  = os.path.splitext(fileName)[1]
                    fileName = os.path.splitext(fileName)[0]
                    
                    # inPath, outPath, newFormat
                    if   self.rkMovFileFormat == 1:
                        fileName = fileName + ".mp4"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.movieFormatConvert(filePath, localTexWrite, "MP4")
                        
                    elif self.rkMovFileFormat == 2:
                        fileName = fileName + ".mov"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.movieFormatConvert(filePath, localTexWrite, "MOV")
                        
                    elif self.rkMovFileFormat == 3:
                        fileName = fileName + ".ogg"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.movieFormatConvert(filePath, localTexWrite, "OGG")
                        
                    elif self.rkMovFileFormat == 4:
                        fileName = fileName + ".webm"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.movieFormatConvert(filePath, localTexWrite, "WEBM")
                        
                    elif self.rkMovFileFormat == 5:
                        fileName = fileName + ".avi"
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        localTexWrite   = localTexWrite   + fileName
                        self.rkint.movieFormatConvert(filePath, localTexWrite, "AVI")
                        
                    else:
                        fileName        = fileName + fileExt
                        relativeTexPath = relativeTexPath + fileName
                        fullWebTexPath  = fullWebTexPath  + fileName
                        
                        if self.rkMovTexWrite == True:
                            localTexWrite = localTexWrite + fileName
                            movePath = self.imageMoveDir + "/" + fileName
                            self.rkint.copyFile(filePath, movePath)
                        else:
                            localTexWrite = filePath

                    # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                    if self.rkMovieAsURI == True:
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        x3dTexture[1].url.append(x3dURIData)
                    else:
                        x3dTexture[1].url.append(fileName)
                        x3dTexture[1].url.append(relativeTexPath)
                        x3dTexture[1].url.append(fullWebTexPath)
                        
                    if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                        x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                        x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()

                    #TextureProperties   - TODO at a later date
                
            else:
                # If Maya Procedural Textures are to be Exported as an ImageTexture node with 
                # a standard file path in the URL field or with a DataURI in the URL field.
                if  self.rkProcTexNode == 0 or self.rkProcTexNode == 1:
                    x3dNodeType = "ImageTexture"
                    x3dURIData  = ""
                    
                    # Determine the actual filename before adding the file extension
                    procFileName = mTextureNode.name()
                    if   self.rk2dFileFormat == 4:
                        # Set the file extention and the relative full path
                        procTFileName   = procFileName + ".tif"
                        procFileName    = procFileName + ".webp"
                        
                        relativeTexPath = relativeTexPath + procFileName
                        fullWebTexPath  = fullWebTexPath + procFileName
                        
                        # Write the PNG file to disk if the export option of 
                        # Consolidate Media - 2D Textures box is checked, or if
                        # the Texture expor Option of ImageTexture with DataURI 
                        # is selected
                        if self.rk2dTexWrite == True or self.rkProcTexNode == 1:
                            localTTexWrite = localTexWrite + procTFileName
                            localTexWrite  = localTexWrite + procFileName
                            
                            # Texture Image file to disk in the Active Project's image directory as specified
                            # by the 'Image Path' option - aka 'self.rkImagePath'.
                            self.rkint.proc2file(mTextureNode.object(), localTTexWrite, 'tif')
                            self.rkint.fileConvertToWebP(localTTexWrite, localTexWrite)
                            
                        
                    elif self.rk2dFileFormat == 3:
                        # Set the file extention and the relative full path
                        procFileName    = procFileName + ".gif"
                        relativeTexPath = relativeTexPath + procFileName
                        fullWebTexPath  = fullWebTexPath + procFileName
                        
                        # Write the PNG file to disk if the export option of 
                        # Consolidate Media - 2D Textures box is checked, or if
                        # the Texture expor Option of ImageTexture with DataURI 
                        # is selected
                        if self.rk2dTexWrite == True or self.rkProcTexNode == 1:
                            localTexWrite = localTexWrite + procFileName
                            
                            # Texture Image file to disk in the Active Project's image directory as specified
                            # by the 'Image Path' option - aka 'self.rkImagePath'.
                            self.rkint.proc2file(mTextureNode.object(), localTexWrite, 'gif')

                    elif self.rk2dFileFormat == 2:
                        # Set the file extention and the relative full path
                        procFileName    = procFileName + ".jpg"
                        relativeTexPath = relativeTexPath + procFileName
                        fullWebTexPath  = fullWebTexPath + procFileName
                        
                        # Write the PNG file to disk if the export option of 
                        # Consolidate Media - 2D Textures box is checked, or if
                        # the Texture expor Option of ImageTexture with DataURI 
                        # is selected
                        if self.rk2dTexWrite == True or self.rkProcTexNode == 1:
                            localTexWrite = localTexWrite + procFileName
                            
                            # Texture Image file to disk in the Active Project's image directory as specified
                            # by the 'Image Path' option - aka 'self.rkImagePath'.
                            self.rkint.proc2file(mTextureNode.object(), localTexWrite, 'jpg')

                    else:
                        # Set the file extention and the relative full path
                        procFileName    = procFileName + ".png"
                        relativeTexPath = relativeTexPath + procFileName
                        fullWebTexPath  = fullWebTexPath + procFileName
                        
                        # Write the PNG file to disk if the export option of 
                        # Consolidate Media - 2D Textures box is checked, or if
                        # the Texture expor Option of ImageTexture with DataURI 
                        # is selected
                        if self.rk2dTexWrite == True or self.rkProcTexNode == 1:
                            localTexWrite = localTexWrite + procFileName
                            
                            # Texture Image file to disk in the Active Project's image directory as specified
                            # by the 'Image Path' option - aka 'self.rkImagePath'.
                            self.rkint.proc2file(mTextureNode.object(), localTexWrite, 'png')
                            
                    # If the with DataURI option is selected, convert contents of image file to a DataURI string.
                    if self.rkProcTexNode == 1:
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        
                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        if x3dURIData == "":
                            x3dTexture[1].url.append(procFileName   )
                            x3dTexture[1].url.append(relativeTexPath)
                            x3dTexture[1].url.append(fullWebTexPath )
                        else:
                            x3dTexture[1].url.append(x3dURIData)
                            
                        if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                            x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                            x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()


                else:
                    x3dNodeType = "PixelTexture"
                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        print("PixelTexture One - Around 2910")
                        localTTexWrite = self.imageMoveDir + "/" + mTextureNode.name() + ".tif"
                        self.rkint.proc2file(mTextureNode.object(), localTTexWrite, 'tif') 
                        x3dTexture[1].image = self.rkint.image2pixel(localTTexWrite)

                        if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                            x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                            x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()
                    

        elif mApiTypeType == rkfn.kLayeredTexture:#TODO: MultiTexture
            x3dNodeType = "MultiTexture"
            
            if   self.rkLayerTexNode == 0:
                x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                
                if x3dTexture[0] == False:
                    textureList = self.getTexturesFromLayeredTexture(mTextureNode)
                    
                    for sTexture in textureList:
                        #                             (mApiType,                mTextureNode,     x3dParent,  x3dField, getPlace2d=True)
                        tPlace2d = self.processTexture(sTexture.object().apiType(), sTexture, x3dTexture[1], "texture", False)
                        #Toss because tPlace2d is None
                print("LayeredTexture isn't fully supported.\nRawKee developers suggest that LayeredTexture be exported as\nan ImageTexture or PixelTexture.")
                print("However, a MultiTexture option is offered here if the author wants to hand-edit the node in a text editor.")
                        
            elif self.rkLayerTexNode == 1 or self.rkLayerTexNode == 2:
                x3dNodeType = "ImageTexture"
                
                # Determine the actual filename before adding the file extension
                layerFileName = mTextureNode.name()
                
                fileFormat = [ 'png',  'png',  'jpg',  'gif',  'webp']
                fileExt    = ['.png', '.png', '.jpg', '.gif', '.webp']
                
                # Set the file extention and the relative full path
                layerTFileName = layerFileName + ".tif"
                layerFileName  = layerFileName + fileExt[self.rk2dFileFormat]
                
                relativeTexPath = relativeTexPath + layerFileName
                fullWebTexPath  = fullWebTexPath  + layerFileName
                
                localTTexWrite = localTexWrite + procTFileName
                localTexWrite  = localTexWrite + procFileName
                
                # Texture Image file to disk in the Active Project's image directory as specified
                # by the 'Image Path' option - aka 'self.rkImagePath'.
                self.rkint.proc2file(mTextureNode.object(), localTTexWrite, 'tif')
                if self.rk2dFileFormat < 4:
                    self.rkint.proc2file(mTextureNode.object(), localTexWrite, fileFormat[self.rk2dFileFormat])
                else:
                    self.rkint.fileConvertToWebP(localTTexWrite, localTexWrite)

                # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                if self.rkFileTexNode == 1:
                    x3dURIData = self.rkint.media2uri(localTexWrite)
                    x3dTexture[1].url.append(x3dURIData)
                else:
                    x3dTexture[1].url.append(layerFileName  )
                    x3dTexture[1].url.append(relativeTexPath)
                    x3dTexture[1].url.append(fullWebTexPath )
                    
                if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                    x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                    x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()
                        
            else:
                x3dNodeType = "PixelTexture"
                x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                if x3dTexture[0] == False:
                    print("PixelTexture One - Around 2978")
                    localTTexWrite = self.imageMoveDir + "/" + mTextureNode.name() + ".tif"
                    self.rkint.proc2file(mTextureNode.object(), localTTexWrite, 'tif') 
                    x3dTexture[1].image = self.rkint.image2pixel(localTTexWrite)

                    if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                        x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                        x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()
                
        return mPlace2d
        
    def getTexturesFromLayeredTexture(self, mLayeredTexture):
        mTextures2d = []
        
        txtIt = aom.MItDependencyGraph(mLayeredTexture.object(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # Returns first place2dTexture node found.
        while not txtIt.isDone():
            cNode = aom.MFnDependencyNode(txtIt.currentNode())
            if cNode.object().apiType() == rkfn.kTexture2d or cNode.object().apiType() == rkfn.kFileTexture:
                mTextures2d.append(cNode)
            txtIt.next()

        return mTextures2d
        
    def getPlace2dFromMayaTexture(self, mTextureNode):
        mPlace2d = None

        txtIt = aom.MItDependencyGraph(mTextureNode.object(), rkfn.kPlace2dTexture, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # Returns first place2dTexture node found.
        while not txtIt.isDone():
            cNode = aom.MFnDependencyNode(txtIt.currentNode())
            if cNode.typeName == "place2dTexture":
                mappingName = mTextureNode.name() + "_" + cNode.name()

                plugExists = True
                try:
                    tmplug = cNode.findPlug("x3dTextureMapping", False)
                    tmplug.setString(mappingName)
                except:
                    plugExists = False
                
                if plugExists == False:
                    strFn = aom.MFnTypedAttribute()
                    nAttr = strFn.create("x3dTextureMapping", "x3dTextureMapping", aom.MFnData.kString)
                    cNode.addAttribute(nAttr)
                    myplug = cNode.findPlug("x3dTextureMapping", False)
                    myplug.setString(mappingName)
                    
                mPlace2d = cNode
                break
                
            txtIt.next()
        
        return mPlace2d
    
    ######################################################
    # These next methods might not be needed
    ######################################################
    def writeRoutes(self):
        pass
    
    def writeScript(self, dObject, contFieldName):
        pass

    def packageMeshShape(self, mObject, contFieldName):
        pass
        
    def checkForMetadata(self, childName):
        # TODO: Add code to determine if the return should be True or False
        return True

    def isInHiddenLayer(self, nodeName):
        # TODO: Add code to determine if the return should be True or False
        return True
    
    def isReferenceNode(self, nodeName):
        # TODO: Add code to determine if the return should be True or False
        return True

    def evalIntermediacy(self, nodeName):
        # TODO: Add code to determine if the return should be True or False
        return True

    def getCFValue(self, cfChoice):
        # TODO: Add code to determine what the string for the return should be
        cfValue = ""
        return cfValue

    def getRigidBodyState(self, mObject):
        # TODO: Add code to determine if the return should be True or False
        return True
        
    def outputCollidableShapes(self):
        pass
        
    def setUpMetadataNodes(self):
        pass
        
    def outputAudio(self):
        pass
        
    def outputFiles(self):
        pass
        
    def processDynamics(self):
        pass
        
    def processRigidBody(self, mObject):
        pass

    def processScripts(self):
        pass

    def getInlineNodeNames(self):
        nodeNames = []
        return nodeNames
    ########################################################
    # End Group
    ########################################################
    
        
    # Function that gathers data necesasry for export
    def prepForSceneTraversal(self):
        
        # Test if RK-IO is traversing the DAG for the purpose of Building an X3D tree for the RawKee GUI
        # If not, then execute the following funtions perparing for export.
        if self.isTreeBuilding == False:
            
            self.rkio.clearMemberLists()
            self.setIgnoreStatusForDefaults()
    
    
    #################################################################################################
    # There are some default nodes in Maya that we just want to ignore by default. These nodes are 
    # different depending on what version of Maya you are using. This function tells the exporter
    # to ignore these nodes if they exist.
    #################################################################################################
    def setIgnoreStatusForDefaults(self):
        self.rkio.setIgnored("persp")
        self.rkio.setIgnored("top")
        self.rkio.setIgnored("front")
        self.rkio.setIgnored("side")
        self.rkio.setIgnored("groundPlane_transform")
        self.rkio.setIgnored("defaultUfeProxyCameraTransformParent")
        self.rkio.setIgnored("defaultLightSet")
        self.rkio.setIgnored("defaultObjectSet")
        self.rkio.setIgnored("defaultUfeProxyTransform")
        self.rkio.setIgnored("Manipulator1")
        self.rkio.setIgnored("UniversalManip")
        self.rkio.setIgnored("CubeCompass")
        
        

    def checkSubDirs(self, fullPath):
        pdir = os.path.dirname(fullPath)
        
        imgPath = os.path.dirname(pdir + "/" + cmds.optionVar( q='rkImagePath' ))
        audPath = os.path.dirname(pdir + "/" + cmds.optionVar( q='rkAudioPath' ))
        inlPath = os.path.dirname(pdir + "/" + cmds.optionVar( q='rkInlinePath'))
        
        if not os.path.exists(imgPath):
            os.mkdir(imgPath)

        if not os.path.exists(audPath):
            os.mkdir(audPath)

        if not os.path.exists(inlPath):
            os.mkdir(inlPath)

        self.imageMoveDir  = imgPath
        self.audioMoveDir  = audPath
        self.inlineMoveDir = inlPath