import sys
import maya.cmds as cmds
import maya.mel  as mel

import maya.api.OpenMaya as aom

from rawkee.RKInterfaces import *
from rawkee.RKIO         import *
from rawkee.RKXNodes     import *

import numpy as np

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
        self.localImagePath = "image/"

        # Holds the path starting below the localPath where audio files are stored
        self.localAudioPath = "audio/"
        
        # Holds the path starting below the localPath where inline files are stored
        self.localInlinePath = "inline/"

        # Holds the base url used in all URL fields
        self.exBaseURL = "./"
        
        # Holds the url used in URL fields of all textures
        self.exTextureURL = "image/"

        # Holds the url used in URL fields of AudioClip nodes
        self.exAudioURL = "audio/"
        
        # Holds the url used in URL fields of Inline nodes
        self.exInlineURL = "inline/"

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
            x3dNode.description = dagNode.findPlug("x3dDescription").asString()
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
        if nodeName == None:
            nodeName = depNode.name()
        tNode = self.rkio.createNodeFromString(x3dType)
        
        hasBeen = self.rkio.checkIfHasBeen(nodeName)
        if hasBeen == True:
            self.rkio.useDecl(tNode, nodeName, x3dParentNode, x3dFieldName)
        else:
            tNode.DEF = nodeName
            self.rkio.setAsHasBeen(nodeName, tNode)
            nodeField = getattr(x3dParentNode, x3dFieldName)
            if isinstance(nodeField, list):
                self.rkio.cMessage(x3dFieldName)
                nodeField.append(tNode)
            else:
                self.rkio.cMessage("Not a list")
                self.rkio.cMessage(x3dFieldName)
                nodeField = tNode
            
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
                
                if bpNode != None:
                    self.processHAnimHumanoid(   dragPath, dagNode, x3dPF, bpNode)
                else:
                    self.processTransformSorting(dragPath, dagNode, x3dPF)



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
        
        newDragPath = dragPath + "|" + supMeshName
        
        myMesh = aom.MFnMesh(dagNode.object())
        
        shList1 = []
        shList2 = []
        
        shaders = []
        groups  = []
        
        shaders, groups = myMesh.getConnectedSetsAndMembers(False, True)
        
        #Check for Metadata - skipping how this is done here for the moment.
        
        
    
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
