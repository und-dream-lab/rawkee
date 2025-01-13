import sys
import maya.cmds as cmds
import maya.mel  as mel

import maya.api.OpenMaya as aom

from rawkee.RKInterfaces import *
from rawkee.RKIO         import *
import numpy as np

#Python implementation of C++ x3dExportOrganizer

class RKOrganizer():
    def __init__(self):
        print("RKOrganizer")
        
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
        print("Importing!!!")
        print(fullFilePath)
        print(rkFilter)
        
    def processExportFile(self, fullFilePath, rkFilter):
        print("Exporting!!!")
        print(fullFilePath)
        print(rkFilter)
        
    def exportAll(self):
        #Grab the Scene Root
        self.itDag = aom.MItDag(aom.MItDag.kDepthFirst, aom.MFn.kTransform)
        worldDag = aom.MFnDagNode(self.itDag.root())
        x3dScene = self.rkio.createSceneRoot()

        self.rootName = "|!!!!!_!!!!!|world"
        self.rkio.setAsHasBeen(self.rootName, x3dScene)
#        self.x3dParentNode = x3dScene
#        self.x3dFieldName = "children"
        
        while not self.itDag.isDone():
            self.itDag.next()
            #try:
            if self.itDag.isDone():
                print("Iterator is complete")
            else:
                self.processCNode()
            #except:
            #    print("Some Dag Failure")

        
        #Process the Root Branch of the DAG
        #self.processBranchNode(worldDag.object(), 0)
        #self.processScene(aom.MFnDependencyNode(worldDag.object()))
        
        #If the RigidBody Physics option is selected, attempt to export Rigid Body physics nodes.
        if self.exRigidBody == True:
            self.processDynamics()
        
        # Export out X3D Script Nodes if they exist
        self.processScripts()
        
        self.isDone = True
        
 # self, x3dNodeType, nodeName, x3dParentNode, x3dFieldName       
        
#    def processScene(self, wObject):
    def processScene(self, worldNode, itDag):
        dagFn = aom.MFnDagNode(wObject)
        cNumb = dagFn.childCount()
        
        for index in range(cNumb):
            aChild = dagFn.child(index)
            #self.processCNode(aom.MFnDependencyNode(aChild).object(), self.rkio.x3dDoc.Scene, "children")

    def processSelectedBranches(self, childObjList):
        for aChild in childObjList:
            #self.processCNode(aChild, self.rkio.x3dDoc.Scene, "children")
            pass
    
    def processX3DAnchor(self, dagNode):
        pass
        
    def processX3DBillboard(self, dagNode):
        pass
        
    def processX3DCollision(self, dagNode):
        pass
        
    def processX3DGroup(self, dagNode):
        pass
        
    def processX3DLOD(self, dagNode):
        pass
        
    def processX3DSwitch(self, dagNode):
        pass
        
    def processX3DViewportGroup(self, dagNode):
        pass
        
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
    
    def processX3DTransform(self, depNode, x3dParentNode, x3dFieldName):
        bna = self.processBasicNodeAddition(depNode, x3dParentNode, x3dFieldName, "Transform")
        if bna[0] == False:
            self.processBasicTransformFields(depNode, bna[1])

    def processHAnimAvatar(self, depNode, x3dParentNode, x3dFieldName):
        bna = self.processBasicNodeAddition(depNode, x3dParentNode, x3dFieldName, "HAnimHumanoid")
        if bna[0] == False:
            self.processBasicTransformFields(depNode, bna[1])
    
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
                print(x3dFieldName)
                nodeField.append(tNode)
            else:
                print("Not a list")
                print(x3dFieldName)
                nodeField = tNode
            
        return [hasBeen, tNode]
    
    def getX3DParentAndContainerField(self, dagNode):
        p = dagNode.getPath().fullPathName()
        sp = p.split('|')
        spLen = len(sp)
        pName = sp[spLen-2]
        
        if spLen == 2:
            pName = self.rootName

        x3dParent = self.rkio.findExisting(pName)

        #TODO: maybe something here in the future to determine x3dField
        x3dField = "children"

        return [x3dParent, x3dField]
        attributes = dir(x3dParent)
        print(attributes)
    
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
            print("No 'description' X3D Field Found")
        
        # X3D farDistance
        x3dNode.farDistance = depNode.findPlug("farClipPlane", False).asFloat()
        
        # X3D jump - must be addedmanually by the user if camera node not created through the RawKee GUI
        try:
            x3dNode.jump = dagNode.findPlug("x3dJump",False).asBool()
        except:
            print("No 'jump' X3D Field Found")
        
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
            print("No 'retainUserOffsets' X3D Field Found")
            
        # X3D viewAll
        try:
            x3dNode.viewAll = dagNode.findPlug("x3dViewAll", False).asBool()
        except:
            print("No 'viewAll' X3D Field Found")
    
    def processBasicLightFields(self, x3dNode, dagNode, depNode):
        # X3D AmbientIntensity - Maya Directional Light does not have an Amb Intensity attribute,
        # skipping this X3D Field
        
        # X3D Color
        nColor = depNode.findPlug("color", False)
        rc = nColor.child(0).asFloat()
        gc = nColor.child(1).asFloat()
        bc = nColor.child(2).asFloat()
        strCol = "r: " + str(rc) + ", g: " + str(gc) + ", b: " + str(bc)
        print(strCol)
        x3dNode.color = (rc, gc, bc)
        
        # X3D Global
        # Always set to True until I can figure out a way to set it to False, probably a custom attribute
        #x3dNode.global_ = True
        #print(dir(x3dNode))
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
    
    def processMayaTransformNode(self, dagNode):
        print("processMayaTransformNode")
        isTransform = True
        tName = dagNode.name()
        depNode = aom.MFnDependencyNode(dagNode.object())
        
        x3dTypeAttr = None
        xta = ""
        try: 
            x3dTypeAttr = depNode.findPlug("x3dNodeType", False)
            xta = x3dTypeAttr.asString()
            print("x3dNodeType exists!")
        except:
            print("x3dNodeType does not exist")
        
        if xta != "":
            print("xta items")
            xtv = x3dTypeAttr.asString()
            if xtv == "Anchor":
                isTransform = False
                self.processX3DAnchor(dagNode)
            elif xtv == "Billboard":
                isTransform = False
                self.processX3DBillboard(dagNode)
            elif xtv == "Collision":
                isTransform = False
                self.processX3DCollision(dagNode)
            elif xtv == "Group":
                isTransform = False
                self.processX3DGroup(dagNode)
            elif xtv == "Switch":
                isTransform = False
                self.processX3DSwitch(dagNode)
            elif xtv == "ViewpointGroup":
                isTransform = False
                self.processX3DViewpointGroup(dagNode)
            elif xtv == "HAnimHumanoid":
                isTransform = False
                x3dPF = self.getX3DParentAndContainerField(dagNode)
                if x3dPF[0] == None:
                    print("Parent Not Found: " + tName)
                else:
                    self.processHAnimAvatar(depNode, x3dPF[0], x3dPF[1])
            elif xtv == "Transform":
                isTransform = True
            
        if isTransform == True:
            hasJoints = False
            hasLight  = False
            hasCamera = False
            skipTrans = False
            
            for index in range(dagNode.childCount()):
                cNode = aom.MFnDependencyNode(dagNode.child(index))
                if cNode.typeName == "camera" and index == 0:
                    hasCamera = True
                    skipTrans = True
                if cNode.typeName.find("Light") > -1 and index == 0:
                    hasLight  = True
                    skipTrans = True
                if cNode.typeName == "joint":
                    hasJoints = True
                    skipTrans = True
                    
            x3dPF = self.getX3DParentAndContainerField(dagNode)
            if x3dPF[0] == None:
                print("Parent Not Found: " + tName)
            else:
                if hasCamera == True:
                    self.processX3DViewpoint(dagNode, x3dPF) #TODO fix the problem.
                elif hasLight  == True:
                    self.processX3DLighting(dagNode, x3dPF)
                elif hasJoints == True:
                    self.processHAnimAvatar(depNode, x3dPF[0], x3dPF[1])
                elif skipTrans == False:
                    self.processX3DTransform(depNode, x3dPF[0], x3dPF[1])
    
    def processMayaJointGrouplessAvatar(self, jObject, x3dParentNode, x3dFieldName):
        pass
        
    def processMayaMesh(self, mObject, x3dParentNode, x3dFieldName):
        pass
    
    # New to Python Version - to replace writeLeafNode
    def processLeafNode(self, lObject, x3dParentNode, x3dFieldName):
        pass
        
    def writeRoutes(self):
        pass
    
    # New to Python Version - To replace processChildNode
    def processCNode(self):
        dagNode = aom.MFnDagNode(self.itDag.getPath())
        
        if dagNode.typeName != "transform":
            return
        
        print("CNode called")
        #depNode = aom.MFnDependencyNode(nObject)
        nodeName = dagNode.name()
        
        if self.rkio.checkIfIgnored(nodeName) == False:
            
            print("CNode - Not ignored: " + dagNode.typeName + "NodeName: " + nodeName)
            
            if dagNode.typeName == "transform":
                self.processMayaTransformNode(dagNode)
            elif dagNode.typeName == "joint":           # Code Won't reach this
                self.processMayaJointHeadless(dagNode)
            elif dagNode.typeName == "mesh":            # Code Won't reach this
                self.processMayaMesh(dagNode)
            elif dagNode.typeName == "lodGroup":        # Code Won't reach this
                self.processX3DLOD(dagNode)
            else:
                self.processLeafNode(dagNode)           # Code Won't reach this
    
    def exportSelected(self):
        
        # Grab the selected Transforms
        activeList = aom.MGlobal.getActiveSelectionList()
        iterGP = aom.MItSelectionList( activeList, aom.MFn.kDagNode )
        itDag  = aom.MItDag(aom.MItDag.kDepthFirst, aom.MFn.kTransform)
        
        childObjList = []
        
        while iterGP.isDone() != False:
            hidObj = iterGP.getDependNode()
            if self.showHiddenForTrees(hidObj) != True and self.isTreeBuilding == True:
                dagPath = iterGP.getDagPath()
                if dagPath != None:
                    itDag.reset(dagPath, aom.MItDag.kDepthFirst, aom.MFn.kTransform)
                    topNode = itDag.root()
                    #processChildNode(topNode, 0)
                    childObjList.append(aom.MFnDependencyNode(topNode.object()))
            iterGP.next()
            
        self.processSelectedBranches(childObjList)

    def processBranchNode(self, mObject, cfChoice):
        # cfChoice value is the int that selects the "cointainerField" choice for that node. 
        dagFn = aom.MFnDagNode(mObject)
        cNumb = dagFn.childCount()
        
        for index in range(cNumb):
            aChild = dagFn.child(index)
            self.processChildNode(aom.MFnDependencyNode(aChild).object(), chChoice)
        
    def processChildNode(self, chObject, cfChoice):
        # cfChoice value is the int that selects the "cointainerField" choice for that node. 
        self.processChildNode(chObject, cfChoice, "")
        
    def processChildNode(self, chObject, cfChoice, cfString):
        # cfChoice value is the int that selects the "cointainerField" choice for that node. 
        # C++ Lines: 2746 - 3052
        dagNode = aom.MFnDagNode(chObject)
        
        if self.hasPassed == False:
            self.hasPassed = self.isTreeBuilding
            nVal = 0
            tName = dagNode.name()
            
            while dagNode.hasUniqueName() != True:
                nVal    = nVal-1
                nValStr = str(nVal)
                
                ntName = tName
                ntName += nValStr
                dagNode.setName(ntName);
        
        childName = dagNode.name()
        
        contFieldName = cfString
        if contFieldName == "":
            contFieldName = self.getCFValue(cfChoice)
        
        '''
		There are certain specific nodes that we don't want exported. If okUse == 1, then the dagNode
		object is used for export. If okUse == False, the dagNode newDagFn is not.
        '''
        okUse = True

		# In the C++ version of this code, two MStringArrays are used for setting up node fields. grArray1 is used for field names.
        grArray1 = []

		# grArray2 is used for field values
        grArray2 = []
        
        # TODO - This will be changed for the Python code to use a single Python list where the even index values will be a string
        # containing the field name, and the odd index will contain the field value
        # It'll be an 'X3D Object Attributes' list
        x3dObjAtt = []
        
        # This tells us what type of Maya node the newDagFn object is.
        childType = newDagFn.typeName

		# Skip all nodes that have an okUse value of 0
        if self.evalIntermediacy(childName)    == True: okUse = False
        if self.rkio.checkIfIgnored(childName) == True: okUse = False
        if self.isInHiddenLayer(childName)     == True: okUse = False
        
        if okUse == True:
            print("Ok to use.")
			# Retrieves the field names for a transform node and stores them as MStrings in the MStringArray
			# named grArray1 using a MEL procedure found in the x3d_exporter_procedures.mel file.
            #################################################################
            # Node having comparable python code... referenced here just so I 
            # can keep the C++ to Python conversion straight in my head
            #################################################################
			# if(!isTreeBuilding) grArray1 = web3dem.getX3DFields(newDagFn, 0);
			# grArray1.append(MString("containerField"));

			# Retrieves the field values for this transform node and stores 
            # them as MStrings in the MStringArray named grArray2 using a MEL 
            # procedure found in the x3d_exporter_procedures.mel file. Length 
            # of grArray2 is now equal to the length of grArray1 - 1.
            #################################################################
            # Referenced here so I can keep the code straight during the 
            # conversion.
            #
            # if(!isTreeBuilding) grArray2 = web3dem.getX3DFieldValues(newDagFn, 0);
            if self.isTreeBuilding != True:
                x3dObjAtt = self.rkint.getX3DFieldsAndValues(dagNode, 0)
			# C++ version of the code: grArray2.append(contFieldName)
            x3dObjAtt.append("containerField")
            x3dObjAtt.append(contFieldName)
            
            '''
            We use the node name "childName" to find out whether or not this node has 
            already been written to the file. This is done through the checkIfHasBeen 
            method.
            '''
            if childType == X3D_MESH:
                print("test")
                if self.getCharacterState(dagNode.object()) != True:
                    if self.getRigidBodyState(dagNode.parent(0)) != True:
                        # The C++ version of this fucntion was writeMeshShape
                        self.packageMeshShape(dagNode.object(), contFieldName)
            else:
                ciHasBeen = self.rkio.checkIfHasBeen(childName)
                isAvatar = self.checkForAvatar(dagNode.object())
                if ciHasBeen == False:
                    # User feedback telling the content author that a particular node is being exported.
                    if self.isTreeBuilding != True:
                        print("Exporting node: " + childName)
                    
                    if childType == X3D_TRANS: # X3D_GROUP X3D_SWITCH X3D_LOD X3D_ANCHOR X3D_BILLBOARD X3D_COLLISION (Collision is separate in the C++ code).
                        # unsigned int remNum;
                        # unsigned int remNum1;
                        remNums = self.evalForSyblings(dagNode.object(), contFieldName)

                        isOE = False
                        if remNums[0] > 0:
                            isOE = True
                        
                        hasMeta = self.checkForMetadata(childName);
                        if hasMeta == True:
                            isOE = true;

                        if isAvatar == True and self.exEncoding != VMRL97ENC and exHAnim == TRUE and childType == X3D_TRANS:
                            pass
                        else:
                            # Handling for X3D_COLLISION should be added to this section of the function
                            if remNums[0] > 0:
                                self.processGrouping(dagNode.object(), msEmpty, x3dObjAtt, isOE, remNums[0], hasMeta)
                            elif remNums[1] > 0:
                                if self.useEmpties == True:
                                    self.processGrouping(dagNode.object(), msEmpty, x3dObjAtt, isOE, remNums[0], hasMeta)
                            else:
                                self.processGrouping(dagNode.object(), msEmpty, x3dObjAtt, isOE, remNums[0], hasMeta)
                                
                    elif childType == X3D_INLINE:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msInline, x3dObjAtt)
                        
                    elif childType == X3D_HANIMJOINT and self.exEncoding != VRML97ENC and self.exHAnim == True and self.isTreeBuilding == True:
                        self.writeHAnimJointForTree(dagNode.object()) # Not sure if the isTreeBuilding value is right
                        
                    elif childType == X3D_TIMESENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msTimeSensor, x3dObjAtt)
                         
                    elif childType == X3D_TOUCHSENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msTouchSensor, x3dObjAtt)
                         
                    elif childType == X3D_GAMEPADSENSOR and self.exEncoding != VRML97ENC and exIODevice == True:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msGamepadSensor, x3dObjAtt)

                    elif childType == X3D_LOADSENSOR and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msLoadSensor, x3dObjAtt)

                    elif childType == X3D_CYLSENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msCylinderSensor, x3dObjAtt)

                    elif childType == X3D_PLANESENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msPlaneSensor, x3dObjAtt)

                    elif childType == X3D_SPHERESENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msSphereSensor, x3dObjAtt)

                    elif childType == X3D_KEYSENSOR and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msKeySensor, x3dObjAtt)

                    elif childType == X3D_STRINGSENSOR and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msStringSensor, x3dObjAtt)

                    elif childType == X3D_PROXSENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msProximitySensor, x3dObjAtt)

                    elif childType == X3D_VISSENSOR:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msVisibilitySensor, x3dObjAtt)

                    elif childType == X3D_NAVIGATION:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msNavigationInfo, x3dObjAtt)

                    elif childType == X3D_WORLDINFO:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msWorldInfo, x3dObjAtt)

                    elif childType == X3D_SOUND:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msSound, x3dObjAtt)

                    elif childType == X3D_POSINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msPositionInterpolator, x3dObjAtt)

                    elif childType == X3D_ORIINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msOrientationInterpolator, x3dObjAtt)

                    elif childType == X3D_COORDINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msCoordinateInterpolator, x3dObjAtt)

                    elif childType == X3D_NORMINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msNormalInterpolator, x3dObjAtt)

                    elif childType == X3D_SCALINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msScalarInterpolator, x3dObjAtt)

                    elif childType == X3D_COLORINTER:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msColorInterpolator, x3dObjAtt)

                    elif childType == X3D_BOOLSEQ and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msBooleanSequencer, x3dObjAtt)

                    elif childType == X3D_INTSEQ and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msIntegerSequencer, x3dObjAtt)

                    elif childType == X3D_BOOLTRIGGER and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msBooleanTrigger, x3dObjAtt)

                    elif childType == X3D_BOOLTOGGLE and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msBooleanToggle, x3dObjAtt)

                    elif childType == X3D_BOOLFILTER and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msBooleanFilter, x3dObjAtt)

                    elif childType == X3D_INTTRIGGER and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msIntegerTrigger, x3dObjAtt)

                    elif childType == X3D_TIMETRIGGER and self.exEncoding != VRML97ENC:
                        self.writeLeafNodes(childName, dagNode.object(), childName, msTimeTrigger, x3dObjAtt)

                    elif childType == X3D_SCRIPT and self.isTreeBuilding == True:
                        # Script is a node to write in XML because it involves getting and writing out URL strings within 
                        # the tag, and writing out CData for local url scripts. It has its own export method.
                        self.writeScript(dagNode.object(), contFieldName)
                        
                    elif childType == X3D_TRANS:
                        if self.getRigidBodyState(dagNode.object()) == False:
                            self.rkio.setAsHasBeen(childName)
                else:
                    # Returns the type of X3D node as an MString based upon the type of Maya node by using
                    # the node's name to request the node type.
                    tempString = self.checkUseType(childName)

                    # Sets the only field name to be used by rkio.useDecl ***WAS: sax3dw.useDecl*** method
                    contField = "containerField"

					# gets the string value to be used for the containerField value
                    contVal = cfString
                    if contVal == "":
                        contVal = self.getCFValue(cfChoice)

                    if childType == X3D_TRANS:
                        remNums = self.evalForSyblings(dagNode.object(), contFieldName);
                        
                        if isAvatar == True and self.exEncoding != VRML97ENC and exHAnim == True and childType == X3D_TRANS:
                            pass
                        else:
                            if remNums[0] > 0:
                                self.processUsedGrouping(dagNode.object(), childName, tempString, contVal, contField)
                            elif remNums[1] > 0:
                                if self.useEmpties == True:
                                        #print("Use Empties 2: " + dagNode.name().asChar())
                                        self.processUsedGrouping(dagNode.object(), childName, tempString, contVal, contField)
                                else:
                                        self.processUsedGrouping(dagNode.object(), childName, tempString, contVal, contField)
                    elif childType == X3D_INLINE:
                        if self.isTreeBuilding == True:
                            self.buildUITreeNode("", "", msInline, "USE", childName)
                        else:
                            # Don't think this is needed any longer --- sax3dw.preWriteField(contVal);
                            self.rkio.useDecl(msInline, childName, "containerField", contVal)

    def writeScript(self, dObject, contFieldName):
        pass

    def writeHAnimJointForTree(self, dObject):
        pass

    def writeLeafNodes(self, mayaName, dObject, x3dName, x3dType, x3dObjAtt):
        pass

    def processGrouping(self, dObject, x3dType, x3dObjAtt, isOE, remNum, hasMeta):
        # For processing the Maya nodes as X3D equivelents
        # transform - Transform - ############ - children - 4
        # transform - Group     - x3dGroup     - children - 4
        # transform - Billboard - x3dBillboard - children - 4
        # transform - Anchor    - x3dAnchor    - children - 4
        # transform - Collision - x3dCollision - children - 4
        # transform - Switch    - x3dSwitch    - choice   - 101
        # lodGroup  - LOD       - ############ - level    - 102
        dagFn = aom.MFnDagNode(dObject)
        
        fv        = len(x3dObjAtt)
        childVal  = 4 # Transform, Group, Billboard, Anchor, Collision
        
        groupType = "transform"
        if dagFn.typeName == "lodGroup" and self.exEncoding == VRML97ENC:
            childVal = 102
            groupType = "lodGroup"
        elif dagFn.typeName == "transform":
            try:
                tNodeType = dagFn.find("x3dGroupType", False)
                groupType = tNodeType.asString()
                if groupType == "x3dSwitch" and self.exEncoding == VRML97ENC:
                    childVal = 101
            except:
                pass
        
        nString = dagFn.name() + "Parent"
        
        if getRigidBodyState(dagFn.object()) == False:
            if self.isTreeBuilding == True:
                #TODO write Tree Building Code
                pass
            else:
                if groupType != "transform":
                    #Need to add a transform above the named maya node to account for Transform values
                    localAtts = self.rkint.getX3DFieldsAndValues(dagFn.object(), msTransform) #getTransFields()
                    localAtts.append("containerField")
                    localAtts.append(x3dObjAtt[fv-1])
                    self.rkio.startNode(msTransform, nString, localAtts, True)
                
                if x3dType != msEmpty:
                    isOE = True
                    
                if groupType != "transform":
                    x3dObjAtt[fv-1] = "children"
                    
                if hasMeta == False and dagFn.typeName == "x3dInline":
                    isOE = False;
                
                if dagFn.typeName != "x3dInline":
                    self.rkio.startNode(checkUseType(dagFn.name()), dagFn.name(), x3dObjAtt, isOE)
                    if hasMeta == True:
                        addMetadataTag(dagFn.name())
                    
                    processBranchNode(dagFn.object(), childVal)
                    
                    ### Not sure what this is needed for, seems it has something to do with a Collision Node
                    #   but the code seems miss placed. TODO: Figure this out
                    # if x3dType != msEmpty:
                    #     writeNodeField(dagFn.object(), x3dType, "proxy")
                    if isOE == True:
                        self.rkio.endNode(checkUseType(dagFn.name()), dagFn.name())
                
                if groupType != "transform":
                    self.rkio.endNode(msTransform, nString)
                    


        # TODO: Handling for X3D_COLLISION should be added to this function

    def processUsedGrouping(self, dObject, childName, useType, contVal, contField):
        # TODO: Handling for X3D_COLLISION should be added to this function
        pass
    
    def evalForSyblings(self, dObject, contFieldName):
        # TODO: Add code to determine the values of remNums
        remNums = [0,0] #remNum and remNum1
        return remNums
        
    def packageMeshShape(self, mObject, contFieldName):
        pass
        
    def checkForMetadata(self, childName):
        # TODO: Add code to determine if the return should be True or False
        return True

    def checkForAvatar(self, mObject):
        # TODO: Add code to determine if the return should be True or False
        return True

    def getCharacterState(self, mObject):
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
        
    def buildUITreeNode(self, mayaType, mayaName, x3dType, x3dUse, x3dName): #buildUITreeNode(MString mayaType, MString mayaName, MString x3dType, MString x3dUse, MString x3dName)
        pass
    
    # TODO: Don't remember what this function is for.
    def showHiddenForTrees(self, hObject):
        depNode = aom.MFnDependencyNode(hObject)
        
        isHidden = False
        tn = depNode.typeName
        
        if tn == "mesh":
            mDag = aom.MFnDagNode(hObject)
            isHidden = self.getRigidBodyState(mDag.parent(0))
            if isHidden == True:
                self.outputCollidableShapes()
        elif tn == "x3dMetadataString" or tn == "x3dMetadataSet" or tn == "x3dMetadataInteger" or tn == "x3dMetadataFloat" or tn == "x3dMetadataDouble":
            self.setUpMetadataNodes()
            isHidden = True
        elif tn == "audio":
            self.outputAudio()
            isHidden = True
        elif tn == "file" or tn == "buldge" or tn == "checker" or tn == "cloth" or tn == "fractal" or tn == "grid" or tn == "mountain" or tn == "movie" or tn == "noise" or tn == "ocean" or tn == "ramp" or tn == "water" or tn == "layeredTexture":
            self.outputFiles()
            isHidden = True
        elif tn == "rigidSolver":
            self.processRigidBody(hObject)
            isHidden = True
            
        return isHidden


    def checkUseType(self, childName):
        typeResult = ""
        
        return typeResult
        
    ##################
    # Do we do file writing here?
    ##################
    #def setFileSax3dWriter(ofstream &stream) #sax3dw.newFile  = &stream;

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
