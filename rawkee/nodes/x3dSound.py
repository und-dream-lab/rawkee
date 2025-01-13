import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaRender as omr

import maya.cmds as cmds

# This is a Custom Maya node representing the X3D Sound Node
# Purpose is so the content author can add a node to the 
# authored scene, and then use the interaction editor to 
# route X3D events within the scene.
class X3DSound(omui.MPxLocatorNode):

    kPluginNodeName = "Sound"
    
    # This TYPE_ID was registered with Alias in the early 
    # 2000s and was used in the C++ version of RawKee for 
    # versions of Maya - Maya 6 through Maya 8.5, and Maya 2019+.
    kPluginNodeId = om.MTypeId(0x00108F66)
    
    # Class Variables requried for Custom Draw Override
    DRAW_CLASSIFICATION = "drawdb/geometry/x3dSound"
    DRAW_REGISTRANT_ID = "X3DSound"

    x3dDirection  = None
    x3dIntensity  = None
    x3dLocation   = None
    x3dMaxBack    = None
    x3dMaxFront   = None
    x3dMinBack    = None
    x3dMinFront   = None
    x3dPriority   = None
    x3dSpatialize = None
    
    
    
    def __init__(self):
        super(X3DSound, self).__init__()
        
    @classmethod
    def creator(cls):
        return X3DSound()
        
    @classmethod
    def initialize(cls):
        numFn = om.MFnNumericAttribute()
        
        cls.x3dDirection = numFn.create("direction", "dir", om.MFnNumericData.k3Double, 0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dDirection)

        cls.x3dIntensity = numFn.create("intensity", "intense", om.MFnNumericData.kFloat, 1)
        numFn.setMin(0.0)
        numFn.setMax(1.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dIntensity)

        cls.x3dLocation = numFn.create("location", "loc", om.MFnNumericData.k3Double, 0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dLocation)

        cls.x3dMaxBack = numFn.create("maxBack", "maxB", om.MFnNumericData.kFloat, 10)
        numFn.setMin(0.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dMaxBack)

        cls.x3dMaxFront = numFn.create("maxFront", "maxF", om.MFnNumericData.kFloat, 10)
        numFn.setMin(0.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dMaxFront)

        cls.x3dMinBack = numFn.create("minBack", "minB", om.MFnNumericData.kFloat, 1)
        numFn.setMin(0.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dMinBack)

        cls.x3dMinFront = numFn.create("minFront", "minF", om.MFnNumericData.kFloat, 1)
        numFn.setMin(0.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dMinFront)

        cls.x3dPriority = numFn.create("priority", "prior", om.MFnNumericData.kFloat, 0)
        numFn.setMin(0.0)
        numFn.setMax(1.0)
        numFn.keyable = True
        cls.addAttribute(cls.x3dPriority)

        cls.x3dSpatialize = numFn.create("spatialize", "spat", om.MFnNumericData.kBoolean, True)
        cls.addAttribute(cls.x3dSpatialize)


    def postConstructor(self):
        
        # The default direction[2] value is set to 1, because the X3D spec states that the
        # default value for the Sound node's "direction" field is (0.0 0.0 1.0) 
        om.MPlug(self.thisMObject(), self.x3dDirection).child(2).setDouble(1)


# TODO: Add more values to the custom MUserData object to support rendering of the locator.
class X3DSoundUserData(om.MUserData):
    
    def __init(self, deleteAfterUse=False):
        super(X3DSoundUserData,self).__init__(deleteAfterUse)
        
        # Wireframe State Color
        self.wireframeColor = om.MColor(1.0, 1.0, 1.0)
        
        # Direction Attribute kDouble3
        self.dir_0 = 0
        self.dir_1 = 0
        
        # The default dir_2 (direction[2]) value is set to 1, because the X3D spec states that the
        # default value for the Sound node's "direction" field is (0.0 0.0 1.0) 
        self.dir_2 = 1
        
        # Location Attribute kDouble3
        self.loc_0 = 0
        self.loc_1 = 0
        self.loc_2 = 0

# This is the Maya Class that allows the X3D Sound node's attributes to be visualized within Maya
class X3DSoundDrawOverride(omr.MPxDrawOverride):

    NAME = "X3DSoundDrawOverride"
    

    def __init__(self, obj):
        super(X3DSoundDrawOverride, self).__init__(obj, None, False) #obj - MObject, None - Geometry Draw Override Callback, bool - isAlwaysDirty flag - True override is always updated without checking dirty state of obj
        
    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices
        
    def hasUIDrawables(self):
        return True
    
    # TODO: Update for TODO changes in the X3DSoundUserData object.
    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data): #old_data / data MUserData objects
        data = old_data
    
        if not data:
            data = X3DSoundUserData()

        locatorNode  = obj_path.node()
        depNode      = om.MFnDependencyNode(locatorNode)
        
        dir          = depNode.findPlug("direction", False)
        data.dir_0   = dir.child(0).asDouble()
        data.dir_1   = dir.child(1).asDouble()
        data.dir_2   = dir.child(2).asDouble()
        
        loc          = depNode.findPlug("location", False)
        data.loc_0   = loc.child(0).asDouble()
        data.loc_1   = loc.child(1).asDouble()
        data.loc_2   = loc.child(2).asDouble()
        
        # Change color of the X3DSound locator graphics based on selection status
        displayStatus = omr.MGeometryUtilities.displayStatus(obj_path)
        if displayStatus == omr.MGeometryUtilities.kDormant:
            data.wireframColor = om.MColor((0.0, 0.1, 0.0))
        else:
            data.wireframeColor = omr.MGeometryUtilities.wireframeColor(obj_path)
        
        return data
        
    # TODO: Add additional draw fetures. And customize attribute editor to create a sphereical drag interface 
    # for node direction value.
    def addUIDrawables(self, obj_path, draw_manager, frame_context, data): # Path to the object being drawn, simple geo and text, some globa info for current render frame, stores the data caced in prepareForDraw
        draw_manager.beginDrawable()
        
        #Set draw color based on selection state
        draw_manager.setColor(data.wireframeColor)
        
        draw_manager.circle(om.MPoint(data.loc_0, data.loc_1, data.loc_2), om.MVector(             data.dir_0,              data.dir_1,              data.dir_2), 1, False)

        # Always set the pointer color to bright red
        brightRed = om.MColor((1.0, 0.0, 0.0))
        draw_manager.setColor(brightRed)
        draw_manager.line(  om.MPoint(data.loc_0, data.loc_1, data.loc_2), om.MPoint( data.dir_0 + data.loc_0, data.dir_1 + data.loc_1, data.dir_2 + data.loc_2))
#        draw_manager.line(om.MPoint(-0.5,0.0,0.0), om.MPoint(0.5,0.0,0.0))
#        draw_manager.line(om.MPoint(0.0,-0.5,0.0), om.MPoint(0.0,0.5,0.0))
        
        draw_manager.endDrawable()
        
    @classmethod
    def creator(cls, obj):
        return X3DSoundDrawOverride(obj)
        
