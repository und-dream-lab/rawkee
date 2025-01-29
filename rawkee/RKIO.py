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
import xmltodict
import json
import io
from x3d import *                                    ###
########################################################

msEmpty:    Final[str] = ""

msBox:      Final[str] = "Box"
msCone:     Final[str] = "Cone"
msCylinder: Final[str] = "Cylinder"
msSphere:   Final[str] = "Sphere"

msIndexedFaceSet: Final[str] = "IndexedFaceSet"

msColor:                  Final[str] = "Color"
msColorRGBA:              Final[str] = "ColorRGBA"
msCoordinate:             Final[str] = "Coordinate"
msMultiTextureCoordinate: Final[str] = "MultiTextureCoordinate"
msNormal:                 Final[str] = "Normal"
msTextureCoordinate:      Final[str] = "TextureCoordinate"

msAnchor:    Final[str] = "Anchor"
msInline:    Final[str] = "Inline"
msCollision: Final[str] = "Collision"
msGroup:     Final[str] = "Group"
msLOD:       Final[str] = "LOD"
msSwitch:    Final[str] = "Switch"
msTransform: Final[str] = "Transform"
msBillboard: Final[str] = "Billboard"

msShape:      Final[str] = "Shape"
msAppearance: Final[str] = "Appearance"
msMaterial:   Final[str] = "Material"

msNavigationInfo: Final[str] = "NavigationInfo"
msWorldInfo:      Final[str] = "WorldInfo"
msViewpoint:      Final[str] = "Viewpoint"

msDirectionalLight: Final[str] = "DirectionalLight"
msSpotLight:        Final[str] = "SpotLight"
msPointLight:       Final[str] = "PointLight"

msColorInterpolator:       Final[str] = "ColorInterpolator"
msOrientationInterpolator: Final[str] = "OrientationInterpolator"
msPositionInterpolator:    Final[str] = "PositionInterpolator"
msScalarInterpolator:      Final[str] = "ScalarInterpolator"

msCoordinateInterpolator: Final[str] = "CoordinateInterpolator"
msNormalInterpolator:     Final[str] = "NormalInterpolator"

msBooleanSequencer: Final[str] = "BooleanSequencer"
msIntegerSequencer: Final[str] = "IntegerSequencer"

msBooleanTrigger: Final[str] = "BooleanTrigger"
msBooleanToggle:  Final[str] = "BooleanToggle"
msBooleanFilter:  Final[str] = "BooleanFilter"
msIntegerTrigger: Final[str] = "IntegerTrigger"
msTimeTrigger:    Final[str] = "TimeTrigger"

msCylinderSensor:   Final[str] = "CylinderSensor"
msKeySensor:        Final[str] = "KeySensor"
msLoadSensor:       Final[str] = "LoadSensor"
msPlaneSensor:      Final[str] = "PlaneSensor"
msProximitySensor:  Final[str] = "ProximitySensor"
msSphereSensor:     Final[str] = "SphereSensor"
msStringSensor:     Final[str] = "StringSensor"
msTimeSensor:       Final[str] = "TimeSensor"
msTouchSensor:      Final[str] = "TouchSensor"
msVisibilitySensor: Final[str] = "VisibilitySensor"

msImageTexture:          Final[str] = "ImageTexture"
msPixelTexture:          Final[str] = "PixelTexture"
msMovieTexture:          Final[str] = "MovieTexture"
msMultiTexture:          Final[str] = "MultiTexture"
msTextureTransform:      Final[str] = "TextureTransform"
msMultiTextureTransform: Final[str] = "MultiTextureTransform"

msAudioClip: Final[str] = "AudioClip"
msSound:     Final[str] = "Sound"

msScript:    Final[str] = "Script"

msMetaD:  Final[str] = "MetadataDouble"
msMetaF:  Final[str] = "MetadataFloat"
msMetaI:  Final[str] = "MetadataInteger"
msMetaSe: Final[str] = "MetadataSet"
msMetaSt: Final[str] = "MetadataString"

# RigidBody Phyisics Component: 2
msColShape:            Final[str] = "CollidableShape"
msRigidBodyCollection: Final[str] = "RigidBodyCollection"
msRigidBody:           Final[str] = "RigidBody"
msCollisionCollection: Final[str] = "CollisionCollection"
msCollisionSpace:      Final[str] = "CollisionSpace"
msCollisionSensor:     Final[str] = "CollisionSensor"

# H-Anim Component: 1
msHAnimDisplacer: Final[str] = "HAnimDisplacer"
msHAnimHumanoid:  Final[str] = "HAnimHumanoid"
msHAnimJoint:     Final[str] = "HAnimJoint"
msHAnimSegment:   Final[str] = "HAnimSegment"
msHAnimSite:      Final[str] = "HAnimSite"

# IODevice Component: 2
msGamepadSensor:  Final[str] = "GamepadSensor"

msRoute:          Final[str] = "ROUTE"

msfield:          Final[str] = "field"

ftSFNode:         Final[str] = "SFNode"
ftMFNode:         Final[str] = "MFNode"

# --define-- defValue "------"

X3DENC:    Final[int] = 0
X3DVENC:   Final[int] = 1
VRML97ENC: Final[int] = 2
X3DBENC:   Final[int] = 3
X3DJSON:   Final[int] = 4

class RKIO():
    def __init__(self):
        print("RKIO")
        
        self.exEncoding = X3DENC
        
        self.profileType = "Full"
        self.x3dVersion  = "4.0"
        
        self.comments = []
        self.commentNames = []
        self.ignoredNodes = []
        self.haveBeenNodes = []
        self.generatedX3D = []
        
        self.fullPath = ""
        
        self.x3dDoc = None
        
        self.isVerbose = False
        
        self.debugging = True
        
        self.x3d_scene = None


    # Function that writes to disk.
    def x3d2disk(self, x3dDoc, fullPath):
        print(fullPath)
        #print(x3dDoc.XML())
        #print(x3dDoc.VRML())
        print(json.dumps(xmltodict.parse(x3dDoc.XML()), indent=4))
        #print(x3dDoc.JSON())


    ########################################################################
    ########################################################################
    # Custom IO Functions not needed if x3d.py I/O Functions work properly #
    ########################################################################
    ########################################################################
    def startDocument(self):                                               #
        pass                                                               #
                                                                           #
    def endDocument(self):
        pass
        
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
        pass
        
    def writeTabs(self):
        pass
        
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
        hasBeen = False
        hbLength = len(self.haveBeenNodes)
        i = 0

        while i < hbLength and hasBeen == False:
            if nodeName == self.haveBeenNodes[i]:
                hasBeen = True
            i = i + 1
            
        return hasBeen
    
    def useDecl(self, x3dNode, nodeName, x3dParentNode, x3dFieldName):
        x3dNode.USE = nodeName
        
        nodeField = getattr(x3dParentNode, x3dFieldName)
        if isinstance(nodeField, list):
            nodeField.append(x3dNode)
        else:
            nodeField = x3dNode
            
    def createNodeFromString(self, x3dType):
        x3dNodeMapping = {
            'AcousticProperties':AcousticProperties,
            'Analyser':Analyser,
            'Anchor':Anchor,
            'Appearance':Appearance,
            'Arc2D':Arc2D,
            'ArcClose2D':ArcClose2D,
            'AudioClip':AudioClip,
            'AudioDestination':AudioDestination,
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
            'Delay':Delay,
            'DirectionalLight':DirectionalLight,
            'DISEntityManager':DISEntityManager,
            'DISEntityTypeMapping':DISEntityTypeMapping,
            'Disk2D':Disk2D,
            'DoubleAxisHingeJoint':DoubleAxisHingeJoint,
            'DynamicsCompressor':DynamicsCompressor,
            'EaseInEaseOut':EaseInEaseOut,
            'EdgeEnhancementVolumeStyle':EdgeEnhancementVolumeStyle,
            'ElevationGrid':ElevationGrid,
            'EspduTransform':EspduTransform,
            'ExplosionEmitter':ExplosionEmitter,
            'Extrusion':Extrusion,
            'FillProperties':FillProperties,
            'FloatVertexAttribute':FloatVertexAttribute,
            'Fog':Fog,
            'FogCoordinate':FogCoordinate,
            'FontStyle':FontStyle,
            'ForcePhysicsModel':ForcePhysicsModel,
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
            'HAnimDisplacer':HAnimDisplacer,
            'HAnimHumanoid':HAnimHumanoid,
            'HAnimJoint':HAnimJoint,
            'HAnimMotion':HAnimMotion,
            'HAnimSegment':HAnimSegment,
            'HAnimSite':HAnimSite,
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
            'KeySensor':KeySensor,
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
            'LOD':LOD,
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
            'OpacityMapVolumeStyle':OpacityMapVolumeStyle,
            'OrientationChaser':OrientationChaser,
            'OrientationDamper':OrientationDamper,
            'OrientationInterpolator':OrientationInterpolator,
            'OrthoViewpoint':OrthoViewpoint,
            'OscillatorSource':OscillatorSource,
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
            'ProtoInstance':ProtoInstance,
            'ProximitySensor':ProximitySensor,
            'QuadSet':QuadSet,
            'ReceiverPdu':ReceiverPdu,
            'Rectangle2D':Rectangle2D,
            'RigidBody':RigidBody,
            'RigidBodyCollection':RigidBodyCollection,
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
            'UniversalJoint':UniversalJoint,
            'UnlitMaterial':UnlitMaterial,
            'Viewpoint':Viewpoint,
            'ViewpointGroup':ViewpointGroup,
            'Viewport':Viewport,
            'VisibilitySensor':VisibilitySensor,
            'VolumeData':VolumeData,
            'VolumeEmitter':VolumeEmitter,
            'VolumePickSensor':VolumePickSensor,
            'WaveShaper':WaveShaper,
            'WindPhysicsModel':WindPhysicsModel,
            'WorldInfo':WorldInfo
        }
        
        return x3dNodeMapping[x3dType]()
