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
        
        
        self.comments = []
        self.commentNames = []
        self.additionalComps = []
        self.additionalCompsLevels = []
        self.ignoredNodes = []
        self.haveBeenNodes = []
        self.generatedX3D = []
        
        self.fullPath = ""
        
        self.x3dDoc = None
        
        self.isVerbose = False
        
        self.debugging = True
        
        self.x3d_scene = None


    # Function that writes to disk.
    def x3d2disk(self, x3dDoc, fullPath, exEncoding):
        self.fullPath   = fullPath
        self.exEncoding = exEncoding
        
        print(self.fullPath)
        print(self.exEncoding)
        
        if   self.exEncoding == X3DXENC:
            print(x3dDoc.XML())
        elif self.exEncoding == X3DVENC:
            print(x3dDoc.VRML())
        elif self.exEncoding == X3DJENC:
            print(json.dumps(xmltodict.parse(x3dDoc.XML()), indent=4))

        #with open(fullPath, "w") as self.exFile:
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
