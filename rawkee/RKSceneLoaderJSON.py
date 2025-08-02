import sys
import os
import rawkee.x3d
import json
import io

import maya.cmds as cmds
import maya.mel  as mel

import maya.api.OpenMaya as aom
import maya.api.OpenMayaAnim as aoma
import rawkee.nodes.sticker    as stk

from   maya.api.OpenMaya import MFn as rkfn

from   rawkee.x3d import *
from   rawkee.RKPseudoNode import *

from   typing import Final

#Notes
#mm-m: 0.001
#cm-m: 0.01
#dm-m: 0.1
#in-m: 0.0254
#ft-m: 0.3048
#yd-m: 0.9144

class RKSceneLoaderJSON():
    def __init__(self):
        # worldText is probably not needed
        self.worldText = "|!!!!!_!!!!!|world"
        self.unitConvDn = [0.001, 0.01, 0.1,  0.0254,  0.3048, 0.9144 ]
        self.unitConvUp = [1000,   100,  10, 39.3701, 3.28084, 1.09361]

    ####################################################################
    # Read in JSON file and return resulting data
    ####################################################################
    def loadX3DJSON(self, fullPath):
        with open(fullPath, 'r') as file:
            data = json.load(file)
            
        return data
        

    #####################################################################
    # Function that checks to see if the X3D field exists within the JSON
    # object and then processes the child object to be added to the 
    # Maya DAG.
    #
    # Have a 4D float list here in case there has to be some offset data 
    # that needs to be passed from parent to child. Currently only used
    # by the HAnimJoint / Maya Joint nodes.
    #####################################################################
    def processBranchForMaya(self, x3dNode, parentName="", x3dField="-children", offset=[0.0, 0.0, 0.0, 0.0]):
        proceed = False
        
        try:
            fieldBranch = x3dNode[x3dField]
            proceed = True
        except Exception as e:
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")                            

        if proceed == True:
            for child in x3dNode[x3dField]:
                self.processChildForMaya(child, parentName, offset=offset)

    #########################################################################
    # Function that chooses how the child should be processed.
    #########################################################################
    def processChildForMaya(self, child, parentName="", offset=[0.0, 0.0, 0.0, 0.0]):
        nType = list(child.keys())[0]
        
        if nType == "Transform":
            # Creates a standard Maya 'transform' node.
            self.processTransformForMaya(child[nType], parentName)
        elif nType == "HAnimHumanoid":
            # Creates a Maya 'transform' node with RawKee HAnim attributes
            self.processHAnimHumanoidForMaya(child[nType], parentName)
        elif nType == "HAnimJoint":
            # Creates a Maya 'joint' node.
            self.processHAnimJointForMaya(child[nType], parentName, offset=offset)
            
    
    #####################################################################
    # Creates a Maya 'joint' node with default (identity) transform 
    # values. The X3D 'center' field of the HAnimJoint node is combined 
    # with the function 'offset' argument to set the Maya 'joint' node's 
    # 'offsetParentMatrix' translation values (aka index values of 
    # 12, 13, and 14 of an identity matrix). This gives visual and 
    # spatial structure to the Maya skeleton, while still allowing for an
    # HAnimJoint-like center.
    #
    # Essentially, this 'HAnimJoint' node's center is represented in the 
    # translate values of the 'offsetParentMatrix' by subtracting this
    # node's parent 'center' value from its own 'center' value.
    #
    # Then, this node's 'center' data is passed as 'nOffset' (aka the 
    # new offset) to its child HAnimJoint nodes as a 4D list. Index
    # 3 of the list always has a value of zero (0) and is ignored by
    # this function.
    #####################################################################
    def processHAnimJointForMaya(self, x3dNode, parentName="", offset=[0.0, 0.0, 0.0, 0.0]):
        # Creates node and return's the node's name
        
        addJoint = False
        full   = False
        left   = True
        right  = False
        jSide  = 0
        jType  = 0
        jOType = ""
        
        jointLabel = x3dNode["@name"]
        jlParts    = jointLabel.split('_')
        jlpLen = len(jlParts)
        
        if jlpLen == 1:
            addJoint = True
            jType    = 18
            jOType   = jointLabel
        elif jlParts[0] == 'humanoid':
            addJoint = True
            jType    = 18
            jOType   = jointLabel
        elif jlParts[0] == 'l' and (full == True or left == True):
            addJoint = True
            jSide    = 1
            jType    = 18
            jOType   = jointLabel.removeprefix("l_")
        elif jlParts[0] == 'r' and (full == True or right == True):
            addJoint = True
            jSide    = 2
            jType    = 18
            jOType   = jointLabel.removeprefix("r_")
        else:
            pass
        #    cmds.setAttr(mayaNodeName + '.side', 3)
        #    cmds.setAttr(mayaNodeName + '.type', 0)
        #    cmds.setAttr(mayaNodeName + '.otherType', "", type="string")

        if addJoint == False:
            return
        
        mayaNodeName = self.createMayaDagNode('joint', x3dNode, parentName)

        if mayaNodeName != None:
            # Set's the nodes major transform values
            self.setMainMayaTransformValues(x3dNode, mayaNodeName)
            
            # Sets the 'offsetParentMatrix' attribute of the Maya 'joint' node that mimics
            # the HAnimJoint 'center' field.
            pivot   = [0.0, 0.0, 0.0, 0.0]
            nOffset = [0.0, 0.0, 0.0, 0.0]
            try:
                cData = x3dNode["@center"]
                cData[0] = cData[0] * offset[3]
                cData[1] = cData[1] * offset[3]
                cData[2] = cData[2] * offset[3]

                pivot[0] = cData[0] - offset[0]
                pivot[1] = cData[1] - offset[1]
                pivot[2] = cData[2] - offset[2]
                
                nOffset[0] = cData[0]
                nOffset[1] = cData[1]
                nOffset[2] = cData[2]
                nOffset[3] = offset[3]
            except:
                print("No Center Found")
                
            cmds.setAttr(mayaNodeName + '.offsetParentMatrix', 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, pivot[0], pivot[1], pivot[2], 1.0, type='matrix')
            cmds.setAttr(mayaNodeName + '.radius', offset[3])
            
#            jointLabel = x3dNode["@name"]
#            jlParts    = jointLabel.split('_')
#            jlpLen = len(jlParts)
            
#            if jlpLen == 1:
#                cmds.setAttr(mayaNodeName + '.side', 0)
#                cmds.setAttr(mayaNodeName + '.type', 18)
#                cmds.setAttr(mayaNodeName + '.otherType', jointLabel, type="string")
#            elif jlParts[0] == 'humanoid':
#                cmds.setAttr(mayaNodeName + '.side', 0)
#                cmds.setAttr(mayaNodeName + '.type', 18)
#                cmds.setAttr(mayaNodeName + '.otherType', jointLabel, type="string")
#            elif jlParts[0] == 'l':
#                cmds.setAttr(mayaNodeName + '.side', 1)
#                cmds.setAttr(mayaNodeName + '.type', 18)
#                cmds.setAttr(mayaNodeName + '.otherType', jointLabel.removeprefix("l_"), type="string")
#            elif jlParts[0] == 'r':
#                cmds.setAttr(mayaNodeName + '.side', 2)
#                cmds.setAttr(mayaNodeName + '.type', 18)
#                cmds.setAttr(mayaNodeName + '.otherType', jointLabel.removeprefix("r_"), type="string")
#            else:
#                cmds.setAttr(mayaNodeName + '.side', 3)
#                cmds.setAttr(mayaNodeName + '.type', 0)
#                cmds.setAttr(mayaNodeName + '.otherType', "", type="string")

            cmds.setAttr(mayaNodeName + '.side', jSide)
            cmds.setAttr(mayaNodeName + '.type', jType)
            cmds.setAttr(mayaNodeName + '.otherType', jOType, type="string")
            cmds.setAttr(mayaNodeName + '.drawLabel', True)
                
            
            # Processes nodes found in the X3D 'HAnimJoint' node's 'children' field. Currently does not process
            # 'HAnimSegment' X3D nodes. Child nodes that are 'HAnimSegment' nodes are ignored.
            self.processBranchForMaya(x3dNode, mayaNodeName, offset=nOffset)


    ########################################################################
    # Function to create a Maya 'transform' node.
    ########################################################################
    def processTransformForMaya(self, x3dNode, parentName=""):
        # Creates node and return's the node's name
        mayaNodeName = self.createMayaDagNode('transform', x3dNode, parentName)
        
        if mayaNodeName != None:
            # Set's the nodes major transform values
            self.setMainMayaTransformValues(x3dNode, mayaNodeName)
            
            # Processes nodes found in the X3D 'Transform' node's 'children' field.
            self.processBranchForMaya(x3dNode, mayaNodeName)
        
        
    ########################################################################
    # Function to create a Maya 'transform' node, but customize it with 
    # additional Maya node attributes to identify it as an HAnimHumanoid
    # node to the RawKee exporter.
    ########################################################################
    def processHAnimHumanoidForMaya(self, x3dNode, parentName=""):
        # Creates node and return's the node's name
        mayaNodeName = self.createMayaDagNode('transform', x3dNode, parentName)

        if mayaNodeName != None:
            # Set's the nodes major transform values
            #self.setMainMayaTransformValues(x3dNode, mayaNodeName)

            # Adds a custom string attribute to this transform identifying it as an HAnimHumanoid 
            # node at time of export instead of a Transform node.
            cmds.select(mayaNodeName)
            cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
            cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

            # Adds X3D fields as custom Maya attributes to this transform, which are later used
            # by RawKee for X3D export.
            loaVal = -1
            try:
                loaVal = x3dNode["@loa"]
            except:
                print("No LOA Found")
            cmds.addAttr(longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
            cmds.setAttr(mayaNodeName + '.LOA', loaVal)

            skConfig = "BASIC"
            try:
                skConfig = x3dNode["@skeletalConfiguration"]
            except:
                print("No skeletalConfiguration Found")
            cmds.addAttr(longName="skeletalConfiguration", dataType="string")
            cmds.setAttr(mayaNodeName + ".skeletalConfiguration", skConfig, type="string")
            
            # This uses the 'sticker' script to update the Maya node's image in the Outliner. 
            # This just gives it a visual queue to the content author that this Maya 'transform'
            # node is not a typical transform node and will be exported as an HAnimNode.
            try:
                stk.put(mayaNodeName, "x3dHAnimHumanoid.png")
            except Exception as e:
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")                            
                print("Oops... Node Sticker Didn't work.")
            
            adjWkUnit = 0
            wUnit = cmds.currentUnit( query=True, linear=True )
            wuMulti = 1.0

            if   wUnit == "mm" and adjWkUnit == 1:
                wuMulti = self.unitConvUp[0]
            elif wUnit == "cm" and adjWkUnit == 1:
                wuMulti = self.unitConvUp[1]
            elif wUnit == "in" and adjWkUnit == 1:
                wuMulti = self.unitConvUp[3]
            elif wUnit == "ft" and adjWkUnit == 1:
                wuMulti = self.unitConvUp[4]
            elif wUnit == "yd" and adjWkUnit == 1:
                wuMulti = self.unitConvUp[5]
            elif wUnit == "mm" and adjWkUnit == 2:
                wuMulti = self.unitConvDn[0]
            elif wUnit == "cm" and adjWkUnit == 2:
                wuMulti = self.unitConvDn[1]
            elif wUnit == "in" and adjWkUnit == 2:
                wuMulti = self.unitConvDn[3]
            elif wUnit == "ft" and adjWkUnit == 2:
                wuMulti = self.unitConvDn[4]
            elif wUnit == "yd" and adjWkUnit == 2:
                wuMulti = self.unitConvDn[5]
                
            scValue    = x3dNode["@scale"]
            scValue[0] = scValue[0] * wuMulti
            
            # Process the X3D nodes that are found in this HAnimHumanoid's skeleton field.
            self.processBranchForMaya(x3dNode, mayaNodeName, x3dField="-skeleton", offset=[ 0.0, 0.0, 0.0, scValue[0] ])


    ############################################################
    # Function that sets the major attributes of the Maya 
    # 'transform' node.
    #
    # It is a work in progress
    ############################################################
    def setMainMayaTransformValues(self, x3dNode, mayaNodeName):
        trlBool = False
        rotBool = False
        sclBool = False
        trl = [0.0, 0.0, 0.0]
        rot = [0.0, 0.0, 1.0, 0.0]
        scl = [1.0, 1.0, 1.0]
        try:
            trl = x3dNode["@translation"]
            trlBool = True
        except Exception as e:
            print("translation fail")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")
            
        if trlBool == True:
            cmds.setAttr(mayaNodeName + ".translateX", trl[0])
            cmds.setAttr(mayaNodeName + ".translateY", trl[1])
            cmds.setAttr(mayaNodeName + ".translateZ", trl[2])


        # TODO
        # The X3d 'rotation' field is not processed correctly.
        # I need to write an AxisAngle4D-to-EulerAngle3D function
        # to convert the rotation values properly. Currently 
        # sets all Euler Angles to 0.
        try:
            rot = x3dNode["@rotation"]
            rotBool = True
        except Exception as e:
            print("rotation fail")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")
            
        if rotBool == True:
            r = [0.0, 0.0, 0.0]
            cmds.setAttr(mayaNodeName + ".rotateX", r[0])
            cmds.setAttr(mayaNodeName + ".rotateY", r[1])
            cmds.setAttr(mayaNodeName + ".rotateZ", r[2])


        try:
            scl = x3dNode["@scale"]
            sclBool = True
            print("Scale is True")
        except Exception as e:
            print("scale fail")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")
            
        if sclBool == True:
            cmds.setAttr(mayaNodeName + ".scaleX", scl[0])
            cmds.setAttr(mayaNodeName + ".scaleY", scl[1])
            cmds.setAttr(mayaNodeName + ".scaleZ", scl[2])


        
    ########################################################################
    # Creates new Maya DAG nodes Serves a similar purpose, and works in a 
    # similar manner to the 'processBasicNodeAddition' function of the 
    # RKOrganizer object. In that it creates a new node that doesn't exist,
    # but if it does exists, it returns a 'None' (unlike the 
    # 'processBasicNodeAddition, which returns a 'False').
    ########################################################################
    def createMayaDagNode(self, mayaType, x3dNode, parentName):
        defName = ""
        useName = ""

        # Figure out if this is a DEF'd X3D node or a USE'd X3D node.
        try:
            defName = x3dNode["@DEF"]
            print(defName)
        except:
            print("No")
        try:
            useName = x3dNode["@USE"]
            print(useName)
        except:
            print("No USE Name")
        
        if useName != "":
            # TODO
            # Currently not processing 'USE' nodes from the X3D file.
            # However, once implemented this part of the function will create an 
            # instance of a Maya node already created. Because Maya shoves
            # every instance into it's own transform node, I am not certain how 
            # this should work. So For now, I am not devoting any brain power 
            # to it.
            #
            # However, once properly implemented, I expect it to still return a 
            # 'None' value.
            return None
            
        else:
            createdName = None
            
            if defName != "" and parentName != "":
                # Create a Maya node with 'name' set to the X3D node's DEF (defined) field 
                # value as a child of an existing Maya DAG node.
                createdName = cmds.createNode(mayaType, n=defName, p=parentName, ss=False)
                
            elif defName != "":
                # Create a Maya node with 'name' set to the X3D node's DEF (defined) field 
                # value at the world level (aka no parent).
                createdName = cmds.createNode(mayaType, n=defName, ss=False)
            
            elif parentName != "":
                # Create a Maya node at the world level (aka no parent) and let Maya pick 
                # the 'name' for the DAG node as this X3D node has no DEF (defined) field
                # value.
                createdName = cmds.createNode(mayaType, p=parentName, ss=False)
                
            else:
                # Create a Maya node and let Maya pick a 'name' as this X3D node has 
                # no DEF (defined) field value.
                createdName = cmds.createNode(mayaType, ss=False)

            return createdName

    
    #############################################################
    # JSON to x3d.py
    #############################################################
    def jsonToX3DPython(self, data):
        x3dDoc = X3D()
        self.processKeysForX3DObject(data, x3dDoc)
        
        return x3dDoc


    #############################################################
    # JSON to x3d.py
    #
    # Process X3D Object Keys
    #############################################################
    def processKeysForX3DObject(self, data, x3dDoc):
        x3dKeys = data["X3D"].keys()
        
        for key in x3dKeys:
            if key == "Scene":
                x3dDoc.Scene = Scene()
                self.processSceneObject(x3dDoc.Scene, data["X3D"][key])
            #elif key == "encoding":
            #    x3dDoc.encoding = data["X3D"][key]
            elif key == "@profile":
                x3dDoc.profile = data["X3D"][key.removeprefix("@")]
            elif key == "@version":
                x3dDoc.version = data["X3D"][key.removeprefix("@")]
            #elif key == "@xsd:noNamespaceSchemaLocation":
            #    x3dDoc.xsd = data["X3D"][key.removeprefix("@")]
            #elif key == "JSON schema":
            #    x3dDoc.id_ = data["X3D"][key]
            elif key == "head":
                pass


    #############################################################
    # JSON to x3d.py
    #
    # Process Scene Object
    #############################################################
    def processSceneObject(self, scene, jScene):
        x3dKeys = jScene.keys()
        brokenKeys = []
        
        for key in x3dKeys:
            if key == "-children":
                self.processBranchField(scene.children, scene, jScene[key])
            else:
                brokenKeys.append(key)
        
        self.processMisplacedNodeObject(jScene, scene.children, brokenKeys)
        
    #############################################################
    # JSON to x3d.py
    #
    # Process Python Branch Field Object
    #############################################################
    def processBranchField(self, pBranchField, parentNode, jField):
        pass


    #############################################################
    # JSON to x3d.py
    #
    # Process Python Field Object
    #############################################################
    def processFieldObject(self, x3dField, pjNode, pxNode):
        nField = x3dField.removeprefix("-")
        aField = x3dField.removeprefix("@")
        if nField != x3dField:
            tempField = getattr(pxNode, nField)
            if isinstance(tempField, list):
                self.processBranchField(tempField, pxNode, pjNode[x3dField])
            else:
                self.processNodeField(  tempField, pxNode, pjNode[x3dField])
        elif aField != x3dField:
            pass
            


    #############################################################
    # JSON to x3d.py
    #
    # Process Python Node Object
    #############################################################
    def processNodeObject(self, x3dNode, jNode):
        x3dKeys = jNode.keys()
        
        for key in x3dKeys:
            #Check to see if this is an SFNode/MFNode field
            #mKey = key.removeprefix("-")
            #if mKey != key:
            #    tempField = getattr(x3dNode, mKey)
            #    if isinstance(nodeField, list):
            #        self.processBranchObject(tempField, jNode[key])
            #    else:
            #        pass
            #else:
            #    pass
            pass


    #############################################################
    # JSON to x3d.py
    #
    # Process Misplaced Node Objects
    #############################################################
    def processMisplacedNodeObject(self, jsonNode, nodeFieldList, brokenKeys):

        for bKey in brokenKeys:
            testNode = None

            try:
                testNode = self.createNodeFromString(bKey)
            except:
                print("Node Not Found")
            
            if testNode != None:
                nodeFieldList.append(testNode)
                self.processNodeObject(testNode, jsonNode[bKey])


    #############################################################
    #############################################################
    #############################################################
    # XML to X3D.py
    #############################################################
    def xmlToX3DPython(self, data):
        pass


    #############################################################
    # This is here for creating X3D node in x3d.py. Future 
    # versions of this class may load JSON as X3D python objects.
    #############################################################
    def createNodeFromString(self, x3dType):
        x3dNodeMapping = {
            ####################################### A
            'AcousticProperties':AcousticProperties,
            'Analyser':Analyser,
            'Anchor':Anchor,
            'Appearance':Appearance,
            'Arc2D':Arc2D,
            'ArcClose2D':ArcClose2D,
            'AudioClip':AudioClip,
            'AudioDestination':AudioDestination,
            ####################################### B
            'Background':Background,
            'BallJoint':BallJoint,
            'Billboard':Billboard,
            'BiquadFilter':BiquadFilter,
            'BlendedVolumeStyle':BlendedVolumeStyle,
            'BooleanFilter':BooleanFilter,
            'BooleanSequencer':BooleanSequencer,
            'BooleanToggle':BooleanToggle,
            'BooleanTrigger':BooleanTrigger,
            'BoundaryEnhancementVolumeStyle':BoundaryEnhancementVolumeStyle,
            'BoundedPhysicsModel':BoundedPhysicsModel,
            'Box':Box,
            'BufferAudioSource':BufferAudioSource,
            ####################################### C
            'CADAssembly':CADAssembly,
            'CADFace':CADFace,
            'CADLayer':CADLayer,
            'CADPart':CADPart,
            'CartoonVolumeStyle':CartoonVolumeStyle,
            'ChannelMerger':ChannelMerger,
            'ChannelSelector':ChannelSelector,
            'ChannelSplitter':ChannelSplitter,
            'Circle2D':Circle2D,
            'ClipPlane':ClipPlane,
            'CollidableOffset':CollidableOffset,
            'CollidableShape':CollidableShape,
            'Collision':Collision,
            'CollisionCollection':CollisionCollection,
            'CollisionSensor':CollisionSensor,
            'CollisionSpace':CollisionSpace,
            'Color':Color,
            'ColorChaser':ColorChaser,
            'ColorDamper':ColorDamper,
            'ColorInterpolator':ColorInterpolator,
            'ColorRGBA':ColorRGBA,
            'CommonSurfaceShader':CommonSurfaceShader,#             From rawkee.RKPseudoNode, not x3d.py
            'ComposedCubeMapTexture':ComposedCubeMapTexture,
            'ComposedShader':ComposedShader,
            'ComposedTexture3D':ComposedTexture3D,
            'ComposedVolumeStyle':ComposedVolumeStyle,
            'Cone':Cone,
            'ConeEmitter':ConeEmitter,
            'Contact':Contact,
            'Contour2D':Contour2D,
            'ContourPolyline2D':ContourPolyline2D,
            'Convolver':Convolver,
            'Coordinate':Coordinate,
            'CoordinateChaser':CoordinateChaser,
            'CoordinateDamper':CoordinateDamper,
            'CoordinateDouble':CoordinateDouble,
            'CoordinateInterpolator':CoordinateInterpolator,
            'CoordinateInterpolator2D':CoordinateInterpolator2D,
            'Cylinder':Cylinder,
            'CylinderSensor':CylinderSensor,
            ####################################### D
            'Delay':Delay,
            'DirectionalLight':DirectionalLight,
            'DISEntityManager':DISEntityManager,
            'DISEntityTypeMapping':DISEntityTypeMapping,
            'Disk2D':Disk2D,
            'DoubleAxisHingeJoint':DoubleAxisHingeJoint,
            'DynamicsCompressor':DynamicsCompressor,
            ####################################### E
            'EaseInEaseOut':EaseInEaseOut,
            'EdgeEnhancementVolumeStyle':EdgeEnhancementVolumeStyle,
            'ElevationGrid':ElevationGrid,
            'EspduTransform':EspduTransform,
            'ExplosionEmitter':ExplosionEmitter,
            'Extrusion':Extrusion,
            ####################################### F
            'FillProperties':FillProperties,
            'FloatVertexAttribute':FloatVertexAttribute,
            'Fog':Fog,
            'FogCoordinate':FogCoordinate,
            'FontStyle':FontStyle,
            'ForcePhysicsModel':ForcePhysicsModel,
            ####################################### G
            'Gain':Gain,
            'GeneratedCubeMapTexture':GeneratedCubeMapTexture,
            'GeoCoordinate':GeoCoordinate,
            'GeoElevationGrid':GeoElevationGrid,
            'GeoLocation':GeoLocation,
            'GeoLOD':GeoLOD,
            'GeoMetadata':GeoMetadata,
            'GeoOrigin':GeoOrigin,
            'GeoPositionInterpolator':GeoPositionInterpolator,
            'GeoProximitySensor':GeoProximitySensor,
            'GeoTouchSensor':GeoTouchSensor,
            'GeoTransform':GeoTransform,
            'GeoViewpoint':GeoViewpoint,
            'Group':Group,
            ####################################### H
            'HAnimDisplacer':HAnimDisplacer,
            'HAnimHumanoid':HAnimHumanoid,
            'HAnimJoint':HAnimJoint,
            'HAnimMotion':HAnimMotion,
            'HAnimSegment':HAnimSegment,
            'HAnimSite':HAnimSite,
            ####################################### I
            'ImageCubeMapTexture':ImageCubeMapTexture,
            'ImageTexture':ImageTexture,
            'ImageTexture3D':ImageTexture3D,
            'IndexedFaceSet':IndexedFaceSet,
            'IndexedLineSet':IndexedLineSet,
            'IndexedQuadSet':IndexedQuadSet,
            'IndexedTriangleFanSet':IndexedTriangleFanSet,
            'IndexedTriangleSet':IndexedTriangleSet,
            'IndexedTriangleStripSet':IndexedTriangleStripSet,
            'Inline':Inline,
            'IntegerSequencer':IntegerSequencer,
            'IntegerTrigger':IntegerTrigger,
            'IsoSurfaceVolumeData':IsoSurfaceVolumeData,
            ####################################### K
            'KeySensor':KeySensor,
            ####################################### L
            'Layer':Layer,
            'LayerSet':LayerSet,
            'Layout':Layout,
            'LayoutGroup':LayoutGroup,
            'LayoutLayer':LayoutLayer,
            'LinePickSensor':LinePickSensor,
            'LineProperties':LineProperties,
            'LineSet':LineSet,
            'ListenerPointSource':ListenerPointSource,
            'LoadSensor':LoadSensor,
            'LocalFog':LocalFog,
            'LOD':LOD,
            ####################################### M
            'Material':Material,
            'Matrix3VertexAttribute':Matrix3VertexAttribute,
            'Matrix4VertexAttribute':Matrix4VertexAttribute,
            'MetadataBoolean':MetadataBoolean,
            'MetadataDouble':MetadataDouble,
            'MetadataFloat':MetadataFloat,
            'MetadataInteger':MetadataInteger,
            'MetadataSet':MetadataSet,
            'MetadataString':MetadataString,
            'MicrophoneSource':MicrophoneSource,
            'MotorJoint':MotorJoint,
            'MovieTexture':MovieTexture,
            'MultiTexture':MultiTexture,
            'MultiTextureCoordinate':MultiTextureCoordinate,
            'MultiTextureTransform':MultiTextureTransform,
            ####################################### N
            'NavigationInfo':NavigationInfo,
            'Normal':Normal,
            'NormalInterpolator':NormalInterpolator,
            'NurbsCurve':NurbsCurve,
            'NurbsCurve2D':NurbsCurve2D,
            'NurbsOrientationInterpolator':NurbsOrientationInterpolator,
            'NurbsPatchSurface':NurbsPatchSurface,
            'NurbsPositionInterpolator':NurbsPositionInterpolator,
            'NurbsSet':NurbsSet,
            'NurbsSurfaceInterpolator':NurbsSurfaceInterpolator,
            'NurbsSweptSurface':NurbsSweptSurface,
            'NurbsSwungSurface':NurbsSwungSurface,
            'NurbsTextureCoordinate':NurbsTextureCoordinate,
            'NurbsTrimmedSurface':NurbsTrimmedSurface,
            ####################################### O
            'OpacityMapVolumeStyle':OpacityMapVolumeStyle,
            'OrientationChaser':OrientationChaser,
            'OrientationDamper':OrientationDamper,
            'OrientationInterpolator':OrientationInterpolator,
            'OrthoViewpoint':OrthoViewpoint,
            'OscillatorSource':OscillatorSource,
            ####################################### P
            'PackagedShader':PackagedShader,
            'ParticleSystem':ParticleSystem,
            'PeriodicWave':PeriodicWave,
            'PhysicalMaterial':PhysicalMaterial,
            'PickableGroup':PickableGroup,
            'PixelTexture':PixelTexture,
            'PixelTexture3D':PixelTexture3D,
            'PlaneSensor':PlaneSensor,
            'PointEmitter':PointEmitter,
            'PointLight':PointLight,
            'PointPickSensor':PointPickSensor,
            'PointProperties':PointProperties,
            'PointSet':PointSet,
            'Polyline2D':Polyline2D,
            'PolylineEmitter':PolylineEmitter,
            'Polypoint2D':Polypoint2D,
            'PositionChaser':PositionChaser,
            'PositionChaser2D':PositionChaser2D,
            'PositionDamper':PositionDamper,
            'PositionDamper2D':PositionDamper2D,
            'PositionInterpolator':PositionInterpolator,
            'PositionInterpolator2D':PositionInterpolator2D,
            'PrimitivePickSensor':PrimitivePickSensor,
            'ProgramShader':ProgramShader,
            'ProjectionVolumeStyle':ProjectionVolumeStyle,
            'ProximitySensor':ProximitySensor,
            ####################################### Q
            'QuadSet':QuadSet,
            ####################################### R
            'ReceiverPdu':ReceiverPdu,
            'Rectangle2D':Rectangle2D,
            'RigidBody':RigidBody,
            'RigidBodyCollection':RigidBodyCollection,
            ####################################### S
            'ScalarChaser':ScalarChaser,
            'ScalarDamper':ScalarDamper,
            'ScalarInterpolator':ScalarInterpolator,
            'ScreenFontStyle':ScreenFontStyle,
            'ScreenGroup':ScreenGroup,
            'Script':Script,
            'SegmentedVolumeData':SegmentedVolumeData,
            'ShadedVolumeStyle':ShadedVolumeStyle,
            'ShaderPart':ShaderPart,
            'ShaderProgram':ShaderProgram,
            'Shape':Shape,
            'SignalPdu':SignalPdu,
            'SilhouetteEnhancementVolumeStyle':SilhouetteEnhancementVolumeStyle,
            'SingleAxisHingeJoint':SingleAxisHingeJoint,
            'SliderJoint':SliderJoint,
            'Sound':Sound,
            'SpatialSound':SpatialSound,
            'Sphere':Sphere,
            'SphereSensor':SphereSensor,
            'SplinePositionInterpolator':SplinePositionInterpolator,
            'SplinePositionInterpolator2D':SplinePositionInterpolator2D,
            'SplineScalarInterpolator':SplineScalarInterpolator,
            'SpotLight':SpotLight,
            'StaticGroup':StaticGroup,
            'StreamAudioDestination':StreamAudioDestination,
            'StreamAudioSource':StreamAudioSource,
            'StringSensor':StringSensor,
            'SurfaceEmitter':SurfaceEmitter,
            'Switch':Switch,
            ####################################### T
            'TexCoordChaser2D':TexCoordChaser2D,
            'TexCoordDamper2D':TexCoordDamper2D,
            'Text':Text,
            'TextureBackground':TextureBackground,
            'TextureCoordinate':TextureCoordinate,
            'TextureCoordinate3D':TextureCoordinate3D,
            'TextureCoordinate4D':TextureCoordinate4D,
            'TextureCoordinateGenerator':TextureCoordinateGenerator,
            'TextureProjector':TextureProjector,
            'TextureProjectorParallel':TextureProjectorParallel,
            'TextureProperties':TextureProperties,
            'TextureTransform':TextureTransform,
            'TextureTransform3D':TextureTransform3D,
            'TextureTransformMatrix3D':TextureTransformMatrix3D,
            'TimeSensor':TimeSensor,
            'TimeTrigger':TimeTrigger,
            'ToneMappedVolumeStyle':ToneMappedVolumeStyle,
            'TouchSensor':TouchSensor,
            'Transform':Transform,
            'TransformSensor':TransformSensor,
            'TransmitterPdu':TransmitterPdu,
            'TriangleFanSet':TriangleFanSet,
            'TriangleSet':TriangleSet,
            'TriangleSet2D':TriangleSet2D,
            'TriangleStripSet':TriangleStripSet,
            'TwoSidedMaterial':TwoSidedMaterial,
            ####################################### U
            'UniversalJoint':UniversalJoint,
            'UnlitMaterial':UnlitMaterial,
            ####################################### V
            'Viewpoint':Viewpoint,
            'ViewpointGroup':ViewpointGroup,
            'Viewport':Viewport,
            'VisibilitySensor':VisibilitySensor,
            'VolumeData':VolumeData,
            'VolumeEmitter':VolumeEmitter,
            'VolumePickSensor':VolumePickSensor,
            ####################################### W
            'WaveShaper':WaveShaper,
            'WindPhysicsModel':WindPhysicsModel,
            'WorldInfo':WorldInfo
        }
        
        return x3dNodeMapping[x3dType]()


    #############################################################
    # This is here for creating non-standard X3D nodes in x3d.py. 
    # Future versions of this class may load JSON as X3D python 
    # objects.
    #
    # This is here to support X3DOM and Castle Game Engine
    # custom nodes (aka RKPseudoNode.py)
    #############################################################
    def isNonX3D(self, x3dType):
        if x3dType == "CommonSurfaceShader": #             From rawkee.RKPseudoNode, not x3d.py
#            print("Inside isNonX3D (NOT X3D):" + x3dType)
            return True
#        else:
#            print("Inside isNonX3D (IS X3D):" + x3dType)
        
        return False
