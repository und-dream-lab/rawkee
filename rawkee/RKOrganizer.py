import sys
import maya.cmds as cmds
import maya.mel  as mel

import maya.api.OpenMaya as aom
from   maya.api.OpenMaya import MFn as rkfn

from rawkee.RKInterfaces import *
from rawkee.RKIO         import *
from rawkee.RKXNodes     import *

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
    def maya2x3d(self, x3dScene, parentDagPaths, dagNodes, pVersion):
        self.loadRawKeeOptions()
        
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
        activeList = aom.MGlobal.getActiveSelectionList()
        iterGP = aom.MItSelectionList( activeList, aom.MFn.kDagNode )
        itDag  = aom.MItDag(aom.MItDag.kBreadthFirst, aom.MFn.kTransform)
        
        dagList  = []
        dragList = []
        
        while iterGP.isDone() != False:
            dagPath = iterGP.getDagPath()
            if dagPath != None:
                itDag.reset(dagPath, aom.MItDag.kDepthFirst, aom.MFn.kTransform)
                topNode = aom.MFnDagNode(itDag.root())
                selectedDagNodes.append(topNode)
                parentDagPaths.append(topNode.getPath().fullPathName()) # this is wrong, this is not the parent dagpath of this node.
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
        x3dNode.scale = self.rkint.getSFVec3fFromList(tForm.scale())
        
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
        
    def checkForUnboundJoints(self, dagNode):
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
    def processHAnimHumanoid(self, dragPath, dagNode, x3dPF, bpNode):
        depNode = aom.MFnDependencyNode(dagNode.object())
        dragPath = dragPath + "|" + depNode.name()
        bna = self.processBasicNodeAddition(depNode, x3dPF[0], x3dPF[1], "HAnimHumanoid")
        if bna[0] == False:
            self.processBasicTransformFields(depNode, bna[1])
            
            #Traverse Maya Scene Downward without using an MFIt object
            groupDag = aom.MFnDagNode(depNode.object())
            cNum = groupDag.childCount()
            
            for i in range(cNum):
                
                dagChild = aom.MFnDagNode(groupDag.child(i))
                if   dagChild.typeName == "joint":
                    self.processHAnimJoint(dragPath, dagChild, cFields="skeleton")
                    
                elif dagChild.typeName == "transform" or dagChild.typeName == "lodGroup" or dagChild.typeName == "mesh":
                    cField = "skin"
                    
                    uDesignated = ""
                    try:
                        ucField     = dagChild.findPlug("x3dContainerField", False)
                        uDesignated = ucField.asString()
                        
                    except:
                        pass
                
                    if uDesignated != "":
                        cField = uDesignated
                    
                    if   cField == "skin":
                        self.processHAnimSkin(   dragPath, dagChild)
                        
                    elif cField == "sites" or cField == "viewpoints":
                        self.processHAnimSite(   dragPath, dagChild, cField)
                        
                    elif cField == "segments":
                        self.processHAnimSegment(dragPath, dagChild)
                        
                    else:
                        animMessage = "Sorry - 'containerField' value: '" + cField + "' is not recognized as a valid 'containerField' value for HAnimHumanoid.\n"
                        animMessage = animMessage + "Skipping Node: " + dagChild.name() + " of Maya Type: " + dagChild.typeName + ".\n"
                        self.rkio.cmessage(animMessage)
                        
                else:
                    animMessage = "Sorry - Node: " + thisChild.name() + " of Type: " + thisChild.typeName + " is not yet supported by RawKee Python for HAnim export.\n"
                    animMessage = animMessage + "Skipping node.\n"
                    self.rkio.cmessage(animMessage)
            
            self.convertMayaAnimClips_To_HAnimMotion(dragPath, bpNode)

    def processHAnimJoint(self, dragPath, jNode, cField="children"):
        if cField == "skeleton":
            # TODO: If the 'cField' arguement is set to "skeleton", then add joint to "skeleton" containerField of the X3D 
            #       HAnimHumanoid node with a "USE", but do not call the 'setAsHasBeen' method. Then:
            #       - Then reprocess this jNode (maya dag node) by calling the 'processHAnimJoint' method by setting the 
            #         'cField' variable to "joints" in the method's arguements.
            pass
        elif cField == "joints":
            # TODO: If the 'cField' arguement is set to "joints", then call 'checkIfHasBeen' method.
            # --- If the 'hasBeen' result is False, then:
            #       - call the 'setAsHasBeen' method for this node
            #       - add this joint to the "joints" field of the HAninHumanoid X3D node using the DEF designator
            #       - call the 'setAsHasBeen' method on this node
            #       - using a 'for' loop, process all of its children based on the appropriate node type. Any children 
            #         that are Maya 'joint' nodes should be processed by calling 'processHAnimJoint' method without 
            #         setting the 'cField' argument.
            # --- If the 'hasBeen' result is True, then:
            #       - add this joint to the "joints" field of the HAnimHumanoid X3D node using the USE designator.
            pass
        elif cField == "children":
            # TODO: If the 'cField' argument is set to "children", then call 'checkIfHasBeen' method.
            # --- if the hasBeen' result is False, then:
            #       - call the 'setAsHasBeen' method for this node.
            #       - add this joint to the "children" field of the HAnimJoint parent node using the DEF designator.
            #       - using a 'for' loop, process all of its children based on the appropriate node type. Any children 
            #         that are Maya 'joint' nodes should be processed by calling 'processHAnimJoint' method without 
            #         setting the 'cField' argument.
            #       - then reprocess this jNode (maya dag node) by calling the 'processHAnimJoint' method by settting the
            #         'cField' method argument to "joints"
            # --- If the 'hasBeen' result is True, then:
            #       - add this joint to the "children" field of the HAnimJoint parent node using the USE designator.
            pass
        
    def convertMayaAnimClips_To_HAnimMotion(self, dragPath, bpNode, cField="motions"):
        pass
        
    def processHAnimSegment(self, dragPath, segNode, cField="segments"):
        pass

    def processHAnimSkin(self, dragPath, skNode, cField="skin"):
        pass
        
    def processHAnimDisplacer(self, dragPath, disNode, cField="displacers"):
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
        
        # Print node object to the console. Mostly included here to let the user
        # know that the scene is being constucted.
        print(tNode)
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
                ###############################################################################
                # Check to see if the 'transform' node is connected to a 'bindPose' node. if it
                # is, that means this 'transform' hosts a character rig as a child, and should
                # be processed as an HAnimHumanoid X3D node.
                ###############################################################################
                bpNode = self.getBindPoseNode(dagNode)
                
                # There maybe a type of transform node that should be exported as an 
                # HAnimHumanoid node, but is not connect to a BindPose node.
                # TODO: Check for this situation and call a processHAnimHumoind method that
                # can accoutn for this.
                if bpNode != None:
                    self.processHAnimHumanoid(       dragPath, dagNode, x3dPF, bpNode)
                if self.checkForUnboundJoints(dagNode):
                    self.processUnboundHAnimHumanoid(dragPath, dagNode, x3dPF)
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
            #Use cMessage instead of print so that we can block Verbose Export at the cMessage Level
            self.rkio.cMessage("Node was NOT ignored: " + dagNode.typeName + ", NodeName: " + nodeName)
            if dagNode.typeName == "transform":
                self.processMayaTransformNode(dragPath, dagNode, cField)
            elif dagNode.typeName == "mesh":
                self.processMayaMesh(dragPath, dagNode, cField)
            elif dagNode.typeName == "lodGroup":
                self.processMayaLOD(dragPath, dagNode, cField)
        else:
            self.rkio.cMessage("Sorry - Node: " + nodeName + " of Type: " + dagNode.typeName + " is not yet supported for RawKee export.")
            
            

#####################################################
############    Other Functions     #################
#####################################################
    
    def processMayaMesh(self, dragPath, dagNode, cField="children"):
        
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
        bdID = self.genMSComboMappings(myMesh, shaders, meshComps)
        
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

                # trackTextureTransforms(self, shaderName, texTransList):
                # getTexTransList(self, shaderName):
                self.processForAppearance(myMesh, shaders[idx], meshComps[idx], sbna[1], bdID, cField="appearance", index=idx)
                
                #ifsName = shapeName + "_IFS"
                self.processForGeometry(  myMesh, shaders, meshComps, sbna[1], bdID, nodeName=shapeName, cField="geometry", nodeType="IndexedFaceSet", index=idx)


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
                if ambientTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
                    p2dTT = self.getPlace2dFromMayaTexture(ambientTexture)
                    mIdx  = self.extractSetTexMatch(ambientTexture, texNodes)
                    mapStr += '{"fieldName":"ambientTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                    mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                    mapInt +=1
                
                chkObject = matColor.source().node()
                diffuseTexture = aom.MFnDependencyNode(chkObject)
                if diffuseTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
                    p2dTT = self.getPlace2dFromMayaTexture(diffuseTexture)
                    mIdx  = self.extractSetTexMatch(diffuseTexture, texNodes)
                    if mapInt > 0:
                        mapStr += ','
                    mapStr += '{"fieldName":"diffuseTextureMapping","mapName":"' + p2dTT.findPlug("x3dTextureMapping", False).asString() + '",'
                    mapStr += '"uvSetName":"' + usedUVSets[mIdx] + '","textureTransformName":"' + p2dTT.name() + '"}'
                    mapInt +=1
                
                chkObject = matIncandescence.source().node()
                emissiveTexture = aom.MFnDependencyNode(chkObject)
                if emissiveTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
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
                    if normalTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
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
                    if occlusionTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
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
                    if shininessTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
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
                    if specularTexture != None and (chkObject.apiType() == rkfn.kTexture2d or chkObject.apiType() == rkfn.kLayeredTexture):
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
                        omrTexture = aom.MFnDependencyNode(aiBase.source().node())
                        if omrTexture != None:
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
            
        # Apply mappings to components
        strList = []
        lName = "jsonTextureMappings_"
        sName = "jtm_"
        tIdx   = self.newTemplateId(mesh)
        faceIDs = []
        
        
        for j in range(len(mappings)):
            tStrList = []
            tStrList.append(lName + str(j))
            tStrList.append(sName + str(j))
            tStrList.append("string")
            tTuple = (tStrList)
            strList.append(tTuple)
        mesh.createBlindDataType(tIdx, strList)
        
        
        #mesh.createBlindDataType(iIdx, (lName, sName, dType))
        
        for j in range(len(components)):
            msList = aom.MSelectionList()
            msList.add(mesh.name())
            tDagPath = msList.getDagPath(0)
            
            mpIter = aom.MItMeshPolygon(tDagPath, components[j])
#            mpIter = aom.MItMeshPolygon(mesh.dagPath(), components[j])
            faceIDs.clear()
            
            while not mpIter.isDone():
                faceIDs.append(mpIter.index())
                mpIter.next()
            
            mesh.setStringBlindData(faceIDs, aom.MFn.kMeshPolygonComponent, tIdx, lName + str(j), mappings[j])
            
        return tIdx
    
    
    def extractSetTexMatch(self, texture, texNodes):
        for i in range(len(texNodes)):
            if texture.name() == texNodes[i].name():
                return i

    
    def processForAppearance(self, myMesh, shadingEngineObj, component, parentNode, bdID, cField="appearance", index=0):
        texTrans = []
        depNode = aom.MFnDependencyNode(shadingEngineObj)
        faceIDs, mapJSON = myMesh.getStringBlindData(aom.MFn.kMeshPolygonComponent, bdID, "jsonTextureMappings_" + str(index))
        mappings = json.loads(mapJSON[0])

        print("Before Appearance")
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
                x3dMat = self.processBasicNodeAddition(matNode, x3dAppearance, "material", "Material")
                if x3dMat[0] == False:
                    material = x3dMat[1]
                    retPlace2d.clear()
                    
                    ambientIntensity = matNode.findPlug("diffuse", False)
                    ambientTexture   = matNode.findPlug("ambientColor", True)
                    diffuseColor     = matNode.findPlug("color", False)
                    diffuseTexture   = matNode.findPlug("color", True)
                    emissiveColor    = matNode.findPlug("incandescence", False)
                    emissiveTexture  = matNode.findPlug("incandescence", True)
                    
                    nScaleSet = False
                    normalScale = None
                    if   matNode.typeName == "phongE":
                        normalScale   = matNode.findPlug("roughness", True)
                        nScaleSet = True
                    elif matNode.typeName == "blinn":
                        normalScale   = matNode.findPlug("eccentricity", True)
                        nScaleSet = True
                    aBump2d           = matNode.findPlug("normalCamera", True)
                    
                    occlIsSet = False
                    occlusionStrength = None
                    occlusionTexture  = None
                    specularColor     = None
                    specularTexture   = None
                    specIsSet = False
                    
                    if   matNode.typeName != "lambert":
                        occlusionStrength = matNode.findPlug("reflectivity", False)
                        occlusionTexture  = matNode.findPlug("reflectedColor", True)
                        occlIsSet = True
                        specularColor     = matNode.findPlug("specularColor", False)
                        specularTexture   = matNode.findPlug("specularColor", True)
                        specIsSet = True
                    
                    shineIsSet        = False
                    isCosPower        = False
                    shininess         = None
                    shininessTexture  = None
                    if   matNode.typeName == "phong":
                        shininess        = matNode.findPlug("cosinePower", False)
                        shininessTexture = matNode.findPlug("reflectedColor", True)
                        isCosPower = True
                        shineIsSet = True
                    elif matNode.typeName == "phongE":
                        shininess        = matNode.findPlug("highlightSize", False)
                        shininessTexture = matNode.findPlug("whiteness", True)
                        shineIsSet = True
                    elif matNode.typeName == "blinn":
                        shininess        = matNode.findPlug("specularRollOff", False)
                        shininessTexture = matNode.findPlug("reflectedColor", True)
                        shineIsSet = True
                    
                    transparency         = matNode.findPlug("transparency", False)
                    
                    
                    material.ambientIntensity = ambientIntensity.asFloat()
                    
                    ambTex = ambientTexture.source().node()
                    if not ambTex.isNull() and (ambTex.apiType() == rkfn.kTexture2d or ambTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(ambTex))
                        mTextureFields.append("ambientTexture")
                        retPlace2d.append(None)
                    
                    diffTex = diffuseTexture.source().node()
                    if not diffTex.isNull() and (diffTex.apiType() == rkfn.kTexture2d or diffTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(diffTex))
                        mTextureFields.append("diffuseTexture")
                        retPlace2d.append(None)
                        material.diffuseColor = (1.0, 1.0, 1.0)
                    else:
                        material.diffuseColor = (diffuseColor.child(0).asFloat(), diffuseColor.child(1).asFloat(), diffuseColor.child(2).asFloat())
                    
                    emisTex = emissiveTexture.source().node()
                    if not emisTex.isNull() and (emisTex.apiType() == rkfn.kTexture2d or emisTex.apiType() == rkfn.kLayeredTexture):
                        mTextureNodes.append(aom.MFnDependencyNode(emisTex))
                        mTextureFields.append("emissiveTexture")
                        retPlace2d.append(None)
                        material.emissiveColor = (0.0, 0.0, 0.0)
                    else:
                        material.emissiveColor = (emissiveColor.child(0).asFloat(), emissiveColor.child(1).asFloat(), emissiveColor.child(2).asFloat())
                        
                    if nScaleSet == True:
                        material.normalScale = normalScale.asFloat()

                    bumpObj = aBump2d.source().node()
                    if not bumpObj.isNull() and (bumpObj.apiType() == rkfn.kBump):
                        normTex = aom.MFnDependencyNode(bumpObj).findPlug("bumpValue", True).source().node()
                        if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(normTex))
                            mTextureFields.append("normalTexture")
                            retPlace2d.append(None)
                        
                    if occlIsSet == True:
                        material.occlusionStrength = occlusionStrength.asFloat()
                        
                    if occlIsSet == True:
                        occlTex = occlusionTexture.source().node()
                        if not occlTex.isNull() and (occlTex.apiType() == rkfn.kTexture2d or occlTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(occlTex))
                            mTextureFields.append("occlusionTexture")
                            retPlace2d.append(None)
                    
                    if specIsSet == True:
                        specTex = specularTexture.source().node()
                        if not specTex.isNull() and (specTex.apiType() == rkfn.kTexture2d or specTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(specTex))
                            mTextureFields.append("specularTexture")
                            retPlace2d.append(None)
                            material.specularColor = (0.0, 0.0, 0.0)
                        else:
                            material.specularColor = (specularColor.child(0).asFloat(), specularColor.child(1).asFloat(), specularColor.child(2).asFloat())
                            
                    if shineIsSet == True:
                        shinVal = shininess.asFloat()
                        if isCosPower == True:
                            shinVal = shinVal / 100.0
                        material.shininess = shinVal 
                        
                    if shineIsSet == True:
                        shinTex = shininessTexture.source().node()
                        if not shinTex.isNull() and (shinTex.apiType() == rkfn.kTexture2d or shinTex.apiType() == rkfn.kLayeredTexture):
                            mTextureNodes.append(aom.MFnDependencyNode(shinTex))
                            mTextureFields.append("shininessTexture")
                            retPlace2d.append(None)
                    
                    material.transparency = (transparency.child(0).asFloat() + transparency.child(1).asFloat() + transparency.child(2).asFloat()) / 3.0
                    
                    mtexLen = len(mTextureNodes)
                    for a in range(mtexLen):
                        gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], material, mTextureFields[a])
                        if not gPlace2d.isNull():
                            texturemapping = getattr(material, mTextureFields[a] + "Mapping")
                            texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                            retPlace2d[a]  = gPlace2d
                
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
            elif matNode.typeName == "aiStandardSurface":
                #Everything goes in the try incase the user didn't setup node connections properly.
                try:
                    x3dMat = self.processBasicNodeAddition(matNode, x3dApperance, "material", "PhysicalMaterial")
                    if x3dMat[0] == False:
                        physMat = x3dMat[1]
                        
                        aiBase       = matNode.findPlug("base", True)
                        aiBaseColor  = matNode.findPlug("baseColor", True)
                        aiMetalness  = matNode.findPlug("metalness", True)
                        aiSpecular   = matNode.findPlug("specular", True)
                        aiRoughness  = matNode.findPlug("specularRoughness", True)
                        aiNormalCam  = matNode.findPlug("normalCamera", True)
                        aiEmisColor  = matNode.findPlug("emissionColor", True)
                        aiEmisWeight = matNode.findPlug("emission", True)
                        
                        # Chec k for an aiMultiply node
                        checkNode = aom.MFnDependencyNode(aiBaseColor.source().node())
                        
                        # Branch to 'Abe Leal 3D' / 'Unreal 4 Packed' Style of Maya material
                        if checkNode.typeName == "aiMultiply":
                            # baseTexture
                            bIdx = 0
                            # occlTexture
                            oIdx = 1
                            # normTexture
                            nIdx = 2
                            # emisTexture - TODO: Account for layered textures
                            eIdx = 3
                            retPlace2d.clear()
                            retPlace2d.append(None)
                            retPlace2d.append(None)
                            retPlace2d.append(None)
                            retPlace2d.append(None)
                            
                            baseTexture = aom.MFnDependencyNode(checkNode.findPlug("input1", True).source().node())
                            btType = baseTexture.object().apiType()
                            occlTexture = aom.MFnDependencyNode(checkNode.findPlug("input2R", True).source().node())
                            otType = occlTexture.object().apiType()
                            
                            if (btType == rkfn.kTexture2d or btType == rkfn.kLayeredTexture) and (otType == rkfn.kTexture2d or otType == rkfn.kLayeredTexture):
                                mTextureNodes.append(baseTexture)
                                mTextureNodes.append(occlTexture)
                                
                                bump2d = aom.MFnDependencyNode(aiNormalCam.source().node())
                                if bump2d.typeName == "bump2d":
                                    #bump2d is to be used as a "Tangent Space Normals"
                                    normTexture = aom.MFnDependencyNode(bump2d.findPlug("bumpValue", True).source().node())
                                    ntType = normTexture.object().apiType()
                                    
                                    if ntType == rkfn.kTexture2d or ntType == rkfn.kLayeredTexture:
                                        mTextureNodes.append(normTexture)
                                        
                                        rougTexture = aom.MFnDependencyNode(aiRoughness.source().node())
                                        rtType = rougTexture.object().apiType()
                                        metlTexture = aom.MFnDependencyNode(aiMetalness.source().node())
                                        mtType = metlTexture.object().apiType()
                                        
                                        if ((rtType == rkfn.kTexture2d or rtType == rkfn.kLayeredTexture) and rougTexture.name() == occlTexture.name()) and ((mtType == rkfn.kTexture2d or mtType == rkfn.kLayeredTexture) and metlTexture.name() == occlTexture.name()):
                                            emisTexture = aom.MFnDependencyNode(aiEmisColor.source().node())
                                            etType = emisTexture.object().apiType()
                                            
                                            if etType == rkfn.kTexture2d or etType == rkfn.kLayeredTexture:
                                                mTextureNodes.append(emisTexture)
                                                
                                                place2dBT = self.processTexture(btType, mTextureNodes[bIdx], physMat, "baseTexture")
                                                place2dET = self.processTexture(etType, mTextureNodes[eIdx], physMat, "emissiveTexture")
                                                place2dOT = self.processTexture(otType, mTextureNodes[oIdx], physMat, "metallicRoughnessTexture")
                                                place2dNT = self.processTexture(ntType, mTextureNodes[nIdx], physMat, "normalTexture")
                                                place2dOT = self.processTexture(otType, mTextureNodes[oIdx], physMat, "occlusionTexture")
                                                
                                                if not place2dBT.isNull():
                                                    physMat.baseTextureMapping              = self.getMappingValue(mappings, "baseTextureMapping")
                                                    retPlace2d[0] = place2dBT
                                                    
                                                if not place2dET.isNull():
                                                    physMat.emissiveTextureMapping          = self.getMappingValue(mappings, "emissiveTextureMapping")
                                                    retPlace2d[1] = place2dET
                                                    
                                                if not place2dOT.isNull():
                                                    physMat.metallicRoughnessTextureMapping = self.getMappingValue(mappings, "metallicRoughnessTextureMapping")
                                                    physMat.occlusionTextureMapping         = self.getMappingValue(mappings, "occlusionTextureMapping")
                                                    retPlace2d[2] = place2dOT
                                                    
                                                if not place2dNT.isNull():
                                                    physMat.normalTextureMapping            = self.getMappingValue(mappings, "normalTextureMapping")
                                                    retPlace2d[3] = place2dNT

                                                #Add Code Here - physMat.transparency 0
                                                
                                            else:
                                                self.rkio.cMessage("Unexpected node found while traversing aiStandardSurface Up Stream Dependency Graph for Emission map. Skipping Material export.")
                                                return
                                        else:
                                            self.rkio.cMessage("Unexpected node found while traversing aiStandardSurface Up Stream Dependency Graph for MetalnessRoughness map. Skipping Material export.")
                                            return
                                    else:
                                        self.rkio.cMessage("Unexpected node found while traversing aiStandardSurface Up Stream Dependency Graph for Normal map. Skipping Material export.")
                                        return
                                else:
                                    self.rkio.cMessage("Unexpected node found while traversing aiStandardSurface Up Stream Dependency Graph for Normal map. Skipping Material export.")
                                    return
                            else:
                                self.rkio.cMessage("Unexpected node found while traversing aiStandardSurface Up Stream Dependency Graph. Skipping Material export.")
                                return
                        
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
                            
                            # normTexture = aom.MFnDependencyNode(bump2d.findPlug("bumpValue").source().node())

                            retPlace2d.clear()

                            baseTex = aiBaseColor.source().node()
                            if not baseTex.isNull() and (baseTex.apiType() == rkfn.kTexture2d or baseTex.apiType() == rkfn.kLayeredTexture):
                                mTextureNodes.append(aom.MFnDependencyNode(baseTex))
                                mTextureFields.append("baseTexture")
                                retPlace2d.append(None)

                            omrTex = aiBase.source().node()
                            if not omrTex.isNull() and (omrTex.apiType() == rkfn.kTexture2d or omrTex.apiType() == rkfn.kLayeredTexture):
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
                                if not normTex.isNull() and (normTex.apiType() == rkfn.kTexture2d or normTex.apiType() == rkfn.kLayeredTexture):
                                    mTextureNodes.append(aom.MFnDependencyNode(baseTex))
                                    mTextureFields.append("normalTexture")
                                    retPlace2d.append(None)
                                    
                            mtexLen = len(mTextureNodes)
                            for a in range(mtexLen):
                                gPlace2d = self.processTexture(mTextureNodes[a].object().apiType(), mTextureNodes[a], physMat, mTextureFields[a])
                                if not gPlace2d.isNull():
                                    texturemapping = getattr(material, mTextureFields[a] + "Mapping")
                                    texturemapping = self.getMappingValue(mappings, mTextureFields[a] + "Mapping")
                                    retPlace2d[a]  = gPlace2d

                            
                except:
                    self.rkio.cMessage("Object not found error while traversing aiStandardSurface Up Stream Dependency Graph. Skipping Material export. Check your shader inputs.")
                    return
                    
            #############################################################################################
            # This gets exported as an X3D PhysicalMaterial node
            # - RawKee expects the Dependency Graph like the one created through the use
            #   of the Adobe Substance 3D Painter plugin for Maya.
            #############################################################################################
            elif matNode.typeName == "standardSurface":
                x3dMat = self.processBasicNodeAddition(matNode, x3dApperance, "material", "PhysicalMaterial")
                if x3dMat[0] == False:
                    pass
                    
            #############################################################################################
            # This gets exported as an X3D PhysicalMaterial node
            # - RawKee expects one the Dependency Graph based on the 
            #       process of setting up a glTF PBR Materials for
            #       Maya as described by the Verge3D User Manual.
            #       'glTF PBR Materials / Maya'
            #           https://www.soft8soft.com/docs/manual/en/maya/GLTF-Materials.html
            #############################################################################################
            elif matNode.typeName == "usdPreviewSurface":
                x3dMat = self.processBasicNodeAddition(matNode, x3dApperance, "material", "PhysicalMaterial")
                if x3dMat[0] == False:
                    pass
                    
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
                x3dMat = self.processBasicNodeAddition(matNode, x3dApperance, "material", "PhysicalMaterial")
                if x3dMat[0] == False:
                    pass
                    
                    
            #############################################################################################
            # TODO: but low priority
            # The intent is export this as an X3D PackagedShader node - probably
            #############################################################################################
            elif matNode.typeName == "shaderfxShader":
                print("The material shaderfxShader is currently unsupported, but is on the future TODO list.")

            # Set textureTransform
            textTransforms = []
            
            for place in retPlace2d:
                if place:# != None:
                    textTransforms.append(place)
            
            if   len(textTransforms) == 1:
                x3dTTrans = self.processBasicNodeAddition(textTransforms[0], x3dApperance, "textureTransform", "TextureTransform")
                if x3dTTrans[0] == False:
                    self.setTextureTransformFields(textTransforms[0], x3dTTrans[1])
            elif len(textTransforms)  > 1:
                x3dMTTrans = self.processBasicNodeAddition(matNode, x3dApperance, "textureTransform", "MultiTextureTransform", matNode.name() + "_MTT")
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
    
    
    def getMappingValue(self, mappings, fieldName):
        for item in mappings['mappings']:
            if item['fieldName'] == fieldName:
                return item['mapName']
    
            
    def setTextureTransformFields(self, place2d, x3dtt):
        # Set the 'center' field of TextureTransform
        centerXY = place2d.findPlug("offset", False).array()
        x3dtt.center = (centerXY[0].asFloat(), centerXY[1].asFloat())

        # Set the 'mapping' field of TextureTransform
        try:
            x3dtt.mapping = place2d.findPlug("x3dTextureMapping", False).asString()
        except:
            print("x3dTextureMapping is not defined.")

        # Set the 'metadata' field of TextureTransform
        # TODO
        
        # Set the 'rotation' field of TextureTransform
        x3dtt.rotation = place2d.findPlug("rotateFrame", False).asFloat()

        # Set the 'scale' field of TextureTransform
        scaleXY = place2d.findPlug("coverage", False).array()
        x3dtt.scale = (scaleXY[0].asFloat(), scaleXY[1].asFloat())
        
        # Set the 'translation' field of TextureTransform
        transXY = place2d.findPlug("translateFrame", False).array()
        x3dtt.translation = (transXY[0].asFloat(), transXY[1].asFloat())

    #This method may be eliminated
    def processMaterial(self):
        pass

    def processForGeometry(self, myMesh, shaders, meshComps, x3dParentNode, bdID, nodeName=None, cField="geometry", nodeType="IndexedFaceSet", index=0):
        meshMP = 0
        if nodeName == None:
            nodeName = myMesh.name()

        depNode = aom.MFnDependencyNode(shaders[index])
        faceIDs, mapJSON = myMesh.getStringBlindData(aom.MFn.kMeshPolygonComponent, bdID, "jsonTextureMappings_" + str(index))
        mappings = json.loads(mapJSON[0])
        
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
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], idx=index)
                else:
                    # Normals Per Face Values
                    bna[1].normalPerVertex = False
                    self.processForNormalNode(myMesh, mIter, nodeName, "Normal", bna[1], npv=False, idx=index)

                ### faceIDs and mappings and uvSetName
                if mappings != None:
                   
                    mapLen = len(mappings['mappings'])
                    bnaTXC = None
                    
                    mtxHasBeen = False
                    if mapLen > 1:
                        bnaTXC = self.processBasicNodeAddition(myMesh, bna[1], "texCoord", "MultiTextureCoordinate", geomName + "_MTC_" + str(index))
                        mtxHasBeen = bnaTXC[0]

                    if mtxHasBeen == False and mapLen > 0:

                        texCoords = []
                        for item in mappings['mappings']:
                            texCoords.append([])
                            
                        mIter.reset()
                        while not mIter.isDone():
                            vertices = mIter.getVertices()
                            
                            for vIdx in vertices:
                                mIdx = mIter.vertexIndex(vIdx)
                                
                                for t in range(mapLen):
                                    tMap = mappings['mappings'][t]
                                    mu,mv = mIter.getUV(vIdx, tMap['uvSetName'])
                                    texCoords[t].append((mu, mv))
                                    
                                bna[1].texCoordIndex.append(mIdx)
                            bna[1].texCoordIndex.append(-1)
                            mIter.next()

                        txcParent = bna[1]
                        if bnaTXC != None:
                            txcParent = bnaTXC
                            
                        for n in range(mapLen):
                            item = mappings['mappings'][n]
                            txc = self.processBasicNodeAddition(myMesh, txcParent, "texCoord", "TextureCoordinate", geomName + "_TC_" + str(index) + "_" +str(n))
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
            
        
    def processForNormalNode(self, myMesh, mIter, nodeName, nodeType, x3dParent, npv=True, cField="normal", idx=0):
        normalNodeName = nodeName + "_" + nodeType + "_" + str(idx)

        mNormal = ()
        mIndex  = []
        
        mIter.reset()

        fCount = 0
        
        while not mIter.isDone():
            if npv == True:
                tns = mIter.getNormals()
                for tn in tns:
                    mNormal = mNormal + (tn.x, tn.y, tn.z)
                    mIndex.append(fCount)
                    fCount += 1
                mIndex.append(-1)
            else:
                tn = mIter.getNormal()
                mNormal = mNormal + (tn.x, tn.y, tn.z)
                mIndex.append(fCount)
                fCount += 1
            
            mCount = fCount % 10
            messageVal = "Normal generation is complex, this may take a while."
            for mcIdx in range(mCount):
                messageVal += "."
            print(messageVal)
            mIter.next()

        tIndex = (mIndex)
        x3dParent.normalIndex = tIndex
        print("Normal Calculation is Complete")

        bna = self.processBasicNodeAddition(myMesh, x3dParent, cField, "Normal", normalNodeName)
        if bna[0] == False:
            # TODO: Future code for implementing 'metadata'
            
            # Assign MFVec3f to the node.
            bna[1].vector = mNormal
            
            print("Normal Node Created.")
            
    
    def getUsedUVSetsAndTexturesInOrder(self, myMesh, shader):
        uvSetNames = myMesh.getUVSetNames()
        hasTex = False
        
        usedUVSets = []
        texNodes   = []
        
        textureList = self.gatherShaderTextures(shader) #getShaderTexturesInOrder(shader)
        
        if len(textureList) == 0:
            return (usedUVSets, texNodes)
            
        for t in textureList:
            usedUVSets.append("map1")
            texNodes.append(None)
            
        for i in range(len(uvSetNames)):
            assocTexObj = myMesh.getAssociatedUVSetTextures(uvSetNames[i])
            
            for j in range(len(assocTexObj)):
                texDep = aom.MFnDependencyNode(assocTexObj[j])
                
                for k in range(len(textureList)):
                    if texDep.name() == textureList[k]:
                        usedUVSets[k] = uvSetNames[i]
                        texNodes[k]   = texDep
    
        return (usedUVSets, texNodes)



    # Method slated for removal.
    '''
    def processForTexCoordNode(self, myMesh, shader, x3dParent, parentName, cField="texCoord"):
        usedUVSets = []
        texNodes   = []
        
        usedUVSets, texNodes = self.getUsedUVSetsAndTexturesInOrder(myMesh, shader)
        
                        
        # TODO - implement TextureCoordinate, TextureTransform, and texCoordIndex info
    '''
    def gatherShaderTextures(self, shader):
        textureList = []
        
        depNode = aom.MFnDependencyNode(shader) #shader is a shadingEngine object
        matNode = aom.MFnDependencyNode(depNode.findPlug("surfaceShader", True).source().node())

        matIter = aom.MItDependencyGraph(matNode.object(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        while not matIter.isDone():
            mObject = matIter.currentNode()
            if mObject.apiType() == rkfn.kLayeredTexture or mObject.apiType() == rkfn.kTexture2d:
                tFound = False
                tNode = aom.MFnDependencyNode(mObject)

                for t in textureList:
                    if t.name() == tNode.name():
                        tFound = True

                if iFound == False:
                    textureList.append(tNode)
                if mObject.apiType() == rkfn.kLayeredTexture:
                    matIter.prune()
            
            matIter.next()
        
        return textureList

        
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
                if mObject.apiType() == rkfn.kLayeredTexture or mObject.apiType() == rkfn.kTexture2d:
                    tFound = False
                    tNode = aom.MFnDependencyNode(mObject)

                    for t in textureList:
                        if t.name() == tNode.name():
                            tFound = True

                    if iFound == False:
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
             
    
    #Slated to be removed
    '''
    def getUsedUVSetsInOrder(self, mMesh, uvSetNames, subNode): # hasT - the return value
        
        hasTextures = True
        returnList  = []
        textureList = self.getShaderTexturesInOrder(mMesh, subNode)
        
        if len(textureList) == 0:
            hasTextures = False
        
        else:
            for t in textureList:
                returnList.append("map1")
                
            for i in range(len(uvSetNames)):
                associatedTextures = mMesh.getAssociatedUVSetTextures(uvSetNames[i])
                
                if len(associatedTextures) == 0:
                    hasTextures = False
                else:
                    for atex in associatedTextures:
                        depFn = aom.MFnDependencyNode(atex)
                        
                        for j in range(len(textureList)):
                            if depFn.name() == textureList[j]:
                                returnList[j] = uvSetNames[i]
        
        return hasTextures, returnList
    '''
    
    
    def getColorIndex(self, dagNode):
        pass
        
    def getCoordIndex(self, dagNode):
        pass
        
    def getNormalIndex(self, dagNode):
        pass
        
    def getTextureCoordIndex(self, dagNode):
        pass

    
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
    ''' - Slated for removal.
    def getShaderTexturesInOrder(mMesh, subNode):
        textureList = []
        shaders, groups = mMesh.getConnectedSetsAndMembers(0, True)
        
        depSh = aom.MFnDependencyNode(shaders[subNode])
        
        shaderPlug = depSh.findPlug("surfaceShader")
        
        ############################################################
        # I don't know if this is needed.
        # isLayeredShader = False
        
        # To be an MFnDependencyNode
        shader = None
        
        #Appearance Iterator
        appIt = aom.MItDependencyGraph(shaderPlug.asMObject(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        while not appIt.isDone():
            cItem = appIt.currentNode()
            if cItme != None:
                depTest = aom.MFnDependencyNode(cItem)
                tName = depTest.typeName
                
                if   tName == "lambert" or tName == "blinn" or tName == "phong" or tName == "phongE":
                    shader = aom.MFnDependencyNode(cItem)
                    break
                    
                elif tName == "oceanShader":
                    shader = aom.MFnDependencyNode(cItem)
                    break
                    
                elif tName == "ShaderfxShader"    or tName == "ShaderfxGameHair":
                    shader = aom.MFnDependencyNode(cItem)
                    break
                    
                elif tName == "StingrayPBS" or tName == "aiStandardSurface":
                    shader = aom.MFnDependencyNode(cItem)
                    break
            appIt.next()
        
        if shader != None:
            depIt = aom.MItDependencyGraph(shader.object(), rkfn.kTexture2d, aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
            
            while not depIt.isDone():
                textureList.append(aom.MFnDependencyNode(depIt.currentNode()).name())
                depIt.next()
            
            if   shader.typeName == "aiStandardSurface":
                pass
            elif shader.typeName == "usdPreviewSurface":
                pass
            elif shader.typeName == "openPBRSurface":
                pass
            elif shader.typeName == "shaderfxShader":
                pass
            elif shader.typeName == "shaderfxGameHair":
                pass
            elif shader.typeName == "oceanShader":
                pass
            elif shader.typeName == "surfaceShader":
                pass
            elif shader.typeName == "standardSurface":
                pass
            elif shader.typeName == "lambert":
                pass
            elif shader.typeName == "blinn":
                pass
            elif shader.typeName == "phong":
                pass
            elif shader.typeName == "phongE":
                pass
                    
        return textureList
    '''    
    
        
    def processTexture(self, mApiType, mTextureNode, x3dParent, x3dField, getPlace2d=True):
        
        relativeTexPath = self.rkImagePath + "/"
        fullWebTexPath  = self.rkBaseDomain + self.rkSubDir + relativeTexPath
        localTexWrite   = self.activePrjDir + relativeTexPath
        
        x3dNodeType = "PixelTexture"
        mPlace2d = None
        if getPlace2d:
            mPlace2d = self.getPlace2dFromMayaTexture(mTextureNode)
        
        if mApiType == rkfn.kTexture2d:
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
                            self.rkint.copyFile(filePath, localTexWrite)
                        else:
                            localTexWrite = filePath

                    # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                    if self.rkFileTexNode == 1:
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        x3dTexture[1].url.append(x3dURIData)
                    else:
                        x3dTexture[1].url.append(relativeTexPath)
                        x3dTexture[1].url.append(fullWebTexPath)
                        
                    if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                        x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                        x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()

                else:
                    x3dNodeType = "PixelTexture"
                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        x3dTexture[1].image = self.rkint.image2pixel(mTextureNode.object())

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
                            self.rkint.copyFile(filePath, localTexWrite)
                        else:
                            localTexWrite = filePath

                    # If the with DataURI option is selected, convert contents of movie file to a DataURI string.
                    if self.rkMovieAsURI == True:
                        x3dURIData = self.rkint.media2uri(localTexWrite)
                        x3dTexture[1].url.append(x3dURIData)
                    else:
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
                            x3dTexture[1].url.append(relativeTexPath)
                            x3dTexture[1].url.append(fullWebTexPath)
                        else:
                            x3dTexture[1].url.append(x3dURIData)
                            
                        if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                            x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                            x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()


                else:
                    x3dNodeType = "PixelTexture"
                    x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                    if x3dTexture[0] == False:
                        x3dTexture[1].image = self.rkint.image2pixel(mTextureNode.object())

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
                    x3dTexture[1].url.append(relativeTexPath)
                    x3dTexture[1].url.append(fullWebTexPath)
                    
                if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                    x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                    x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()
                        
            else:
                x3dNodeType = "PixelTexture"
                x3dTexture = self.processBasicNodeAddition(mTextureNode, x3dParent, x3dField, x3dNodeType)
                if x3dTexture[0] == False:
                    x3dTexture[1].image = self.rkint.image2pixel(mTextureNode.object())

                    if mPlace2d != None and mPlace2d.typeName == "place2dTexture":
                        x3dTexture[1].repeatS = mPlace2d.findPlug("wrapU", False).asBool()
                        x3dTexture[1].repeatT = mPlace2d.findPlug("wrapV", False).asBool()
                
        return mPlace2d
        
    def processTextureTransforms(self):
        pass

    def getTexturesFromLayeredTexture(self, mLayeredTexture):
        mTextures2d = []
        
        txtIt = aom.MItDependencyGraph(mLayeredTexture.object(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # Returns first place2dTexture node found.
        while not txtIt.isDone():
            cNode = aom.MFnDependencyNode(txtIt.currentNode())
            if cNode.object().apiType() == rkfn.kTexture2d:
                mTextures2d.append(cNode)
            txtIt.next()

        return mTextures2d
        
    def getPlace2dFromMayaTexture(self, mTextureNode):
        mPlace2d = None

        txtIt = aom.MItDependencyGraph(mTextureNode.object(), aom.MItDependencyGraph.kUpstream, aom.MItDependencyGraph.kDepthFirst, aom.MItDependencyGraph.kNodeLevel)
        
        # Returns first place2dTexture node found.
        while not txtIt.isDone():
            cNode = aom.MFnDependencyNode(txtIt.currentNode())
            if cNode.typeName == "place2dTexture":
                strFn = aom.MFnTypedAttribute()
                strDt = aom.MFnStringData()
                nAttr = strFn.create("x3dTextureMapping", "x3dTextureMapping", aom.MFnData.kString, strDt.create(mTextureNode.name() + "_" + cNode.name()))
                cNode.addAttribute(nAttr)
                mPlace2d = cNode
                break
                
            txtIt.next()
        
        return mPlace2d
    
    # New to Python Version - to replace writeLeafNode
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
        
    # TODO: Not sure this function is needed without a FileTranslator object
    def setExportStyle(self, filter):
        if self.isTreeBuilding == True:
            if filter == "*.x3dv":
                self.exEncoding = X3DVENC
            elif filter == "*.wrl":
                self.exEncoding = VRML97ENC
            elif filter == "*.x3db":
                self.exEncoding = X3DBENC
            else:
                self.exEncoding = X3DENC
                
            self.rkio.exEncoding = self.exEncoding          # sax3dw.exEncoding = exEncoding;
            self.rkint.setExportEncoding(self.exEncoding)   # web3dem.setExportEncoding(exEncoding);


    # Function that gathers data necesasry for export
    def organizeExport(self):
        
        # This method extracts the export options information for us from the optionVar variables.
        self.grabExporterOptions()
        
        # Test if RK-IO is traversing the DAG for the purpose of Building an X3D tree for the RawKee GUI
        # If not, then execute the following funtions perparing for export.
        if self.isTreeBuilding == False:
            
            # This methods creates the local directories in which we will place any image, movie, or audio
            # files created or transferred during the export process.
            self.createResourceDir()    #TODO
        
            '''
            This method evaluates the export options for textures. If needed the method changes the file format
            of the image textures, the size of textures, writes them or transfers these files as necessary to the 
            directory found in the images path designated by our export options. Internal Maya textures are exported
            at this time as well in the same manner.
            '''
            self.textureSetup()          #TODO
        
            '''
            This methods evaluates the export options for audioClips in a manner similar to the textureSetup method
            above. Currently, no sound export functionality has been implemented so this method does nothing.
            '''
            self.soundSetup()            #TODO

            '''
            This methods evaluates the export options for Inlines in a manner similar to the textureSetup method
            above.
            '''
            self.inlineSetup()            #TODO
            
            ##################################
            # Preparing for Underworld Nodes
            ##################################
            '''
            This method evaluates the RawKee underworld nodes such as x3dIndexedFaceSet, x3dColor 
            and x3dNormal in order to prepare them for export. This includes any required data collection.
            '''
            self.prepareUnderworldNodes() #TODO
            
            '''
            This method evalutes the RawKee interpolator nodes such as x3dPositionInterpolator and 
			x3dOrientationInterpolator nodes in order to prepare them for export. This includes any 
            required data collection.
            '''
            self.rkio.clearMemberLists()                       #sax3dw.clearMemberLists(); <-- TODO: Look at this function to determine if it is needed.
            self.setIgnoreStatusForDefaults() #TODO
        
    def createResourceDir(self):
        pass
    def textureSetup(self):
        pass
    def soundSetup(self):
        pass
    def inlineSetup(self):
        pass
    def prepareUnderworldNodes(self):
        pass

    '''
        There are some default nodes in Maya that we just want to ignore by default. These nodes are 
        different depending on what version of Maya you are using. This function tells the exporter
        to ignore these nodes if they exist.
    '''
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
        
    def getInlineNodeNames(self):
        nodeNames = []
        return nodeNames
        
    '''
      This method extracts the export options information for us from the 
        optionVar variables
    '''
    def grabExporterOptions(self):
        # User feedback letting the content author know that the plugin is retrieving the export options.
        if self.isTreeBuilding == False:
            self.rkio.cMessage("Analyzing export options.")    # sax3dw.msg.set("Analyzing export options.") #<--- Is this necessary?
            self.rkio.cMessage(" ")                            # sax3dw.msg.set(" ") #<--- Is this necessary?


        inlineNodeArray = self.getInlineNodeNames() #String array
        exInline = False
        
        if len(inlineNodeArray) > 0:
            exInline = True

        optionsArray = self.optionsString.split('*') #String Array
        for i, rkFlag in enumerate(optionsArray):
            if rkFlag == "x3dUseEmpties":
                if rkFlag[i+1] == "0":
                    self.useEmpties = False
                else:
                    self.useEmpties = True
            elif rkFlag == "x3dExportMetadata":
                if rkFlag[i+1] == "0":
                    self.exMetadata = False
                else:
                    self.exMetadata = True
            elif rkFlag == "x3dConsolidateMedia":
                if rkFlag[i+1] == "0":
                    self.conMedia = False
                    self.rkint.setConsolidate(False)
                else:
                    self.conMedia = True
                    self.rkint.setConsolidate(True)
            elif rkFlag == "x3dFileOverwrite":
                if rkFlag[i+1] == "0":
                    self.fileOverwrite = False
                else:
                    self.fileOverwrite = True
            elif rkFlag == "x3dExportTextures":
                if rkFlag[i+1] == "0":
                    self.exTextures = False
                else:
                    self.exTextures = True
            elif rkFlag == "x3dTextureDirectory":
                self.getTextureDir = rkFlag[i+1]
                if self.getTextureDir == " ":
                    self.getTextureDir = ""
            elif rkFlag == "x3dNPV":
                self.npvNonD = int(rkFlag[i+1])
                if self.npvNonD == 1:
                    self.rkint.setGlobalNPV(True)
                    pass
                else:
                    self.rkint.setGlobalNPV(False)
                    pass
            elif rkFlag == "x3dCreaseAngle":
                self.caGlobalValue = float(rkFlag[i+1])
                self.rkint.setGlobalCA(self.caGlobalValue)
            elif rkFlag == "x3dExportAudio":
                if rkFlag[i+1] == "0":
                    self.exAudio = False
                else:
                    self.exAudio = True
            elif rkFlag == "x3dRigidBodyExport":
                if rkFlag[i+1] == "0":
                    self.exRigidBody = False
                else:
                    self.exRigidBody = True
            elif rkFlag == "x3dHAnimExport":
                if rkFlag[i+1] == "0":
                    self.exHAnim = False
                else:
                    self.exHAnim = True
            elif rkFlag == "x3dIODeviceExport":
                if rkFlag[i+1] == "0":
                    self.exIODevice = False
                else:
                    self.exIODevice = True
            elif rkFlag == "x3dNSHAnim": # Non-Standard HAnim
                if rkFlag[i+1] == "0":
                    self.nonStandardHAnim = False
                else:
                    self.nonStandardHAnim = True
            elif rkFlag == "x3dBCFlag":
                if rkFlag[i+1] == "0":
                    self.exBCFlag = 0
                elif rkFlag[i+1] == "2":
                    self.exBCFlag = 2
                else:
                    self.exBCFlag = 1
            elif rkFlag == "x3dAudioDirectory":
                self.getAudioDir = rkFlag[i+1]
                if self.getAudioDir == " ":
                    self.getAudioDir = ""
            elif rkFlag == "x3dUseRelURL":
                if rkFlag[i+1] == "0":
                    self.useRelURL = False
                else:
                    self.useRelURL = True
                self.rkint.setUseRelURL(self.useRelURL)
            elif rkFlag == "x3dUseRelURLW":
                if rkFlag[i+1] == "0":
                    self.useRelURLW = False
                else:
                    self.useRelURLW = True
                self.rkint.setUseRelURLW(self.useRelURLW)
            elif rkFlag == "x3dInlineDirectory":
                self.getInlineDir = rkFlag[i+1]
                if self.getInlineDir == " ":
                    self.getInlineDir = ""
            elif rkFlag == "x3dBaseUrl":
                self.exBaseURL = rkFlag[i+1]
                if self.exBaseURL == " ":
                    self.exBaseURL = ""
            elif rkFlag == "x3dTextTempStore":
                self.tempTexturePath = rkFlag[i+1]
            elif rkFlag == "updateMethod":
                updateString = rkFlag[i+1]
                if updateString == "1":
                    self.updateMethod = 1
                elif updateString == "2":
                    self.updateMethod = 2
                else:
                    self.updateMethod = 0

        if self.isTreeBuilding == False:
            imagePath = self.getTextureDir
            
            if self.getTextureDir != "":
                ipArray = imagePath.split('/')
                newIP = ""
                for rkIP in ipArray:
                    newIP = newIP + rkIP
                    newIP = newIP + "/"
                imagePath = newIP
                self.rkint.setImageDir(imagePath)

            audioPath = self.getAudioDir
            if self.getAudioDir != "":
                apArray = audioPath.split('/')
                newAP == ""
                
                for rkAP in apArray:
                    newAP = newAP + rkAP
                    newAP = newAP + "/"
                audioPath = newAP
                self.rkint.setAudioDir(audioPath)

            inlinePath = self.getInlineDir
            if self.getInlineDir != "":
                inArray = inlinePath.split('/')
                newIN = ""
                for rkIN in inArray:
                    newIN = newIN + rkIN
                    newIN = newIN + "/"
                inlinePath = newIN
                self.rkint.setInlineDir(inlinePath)

            basePath = ""
            if self.exBaseURL != "":
                basePath = self.exBaseURL
                urlend = basePath.rfind('/');
                strLen = len(basePath)
                if strLen > 0:
                    strLen = strLen - 1
                if urlend != strLen and len(basePath) > 0:
                    basePath = basePath + "/"
                self.rkint.setBaseUrl(basePath)

            self.localImagePath = self.localPath;
            self.localImagePath = self.localImagePath + imagePath

            self.localAudioPath = self.localPath;
            self.localAudioPath = self.localAudioPath + audioPath

            self.localInlinePath = self.localPath;
            self.localInlinePath = self.localInlinePath  + inlinePath
