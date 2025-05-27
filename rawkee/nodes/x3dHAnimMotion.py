import maya.api.OpenMaya as aom
import maya.api.OpenMayaUI as aomui
import maya.api.OpenMayaRender as aomr

import maya.cmds as cmds

# This is a Custom Maya node representing the X3D Sound Node
# Purpose is so the content author can add a node to the 
# authored scene, and then use the interaction editor to 
# route X3D events within the scene.
class X3DHAnimMotion(aomui.MPxLocatorNode):
    TYPE_NAME = "x3dHAnimMotion"
    
    # This TYPE_ID was registered with Autodesk in 2024 for the 
    # RawKee PE plugin.
    TYPE_ID = aom.MTypeId(0x0013fe40)

    x3d_channels        = None
    x3d_channelsEnabled = None
    x3d_description     = None
    x3d_enabled         = None
    x3d_endFrame        = None
    x3d_frameDuration   = None
    x3d_frameIncrement  = None
    x3d_frameIndex      = None
    x3d_joints          = None
    x3d_loa             = None
    x3d_loop            = None
    x3d_name            = None
    x3d_startFrame      = None
    x3d_values          = None
    x3d_aBoolean        = None
    x3d_aFloat          = None
    
    #rk_keyFrameStep     = None
    rk_mStartFrame      = None
    rk_mStopFrame       = None
    #rk_fps              = None

    rk_animPkg          = None


    def __init__(self):
        super(X3DHAnimMotion, self).__init__()
        
    @classmethod
    def creator(cls):
        return X3DHAnimMotion()
        
    @classmethod
    def initialize(cls):
        typFn = aom.MFnTypedAttribute()
        numFn = aom.MFnNumericAttribute()
        cmpFn = aom.MFnCompoundAttribute()
        
        cls.x3d_channels    = typFn.create("channels",    "x3dChnls", aom.MFnData.kString)
        cls.x3d_description = typFn.create("description", "x3dDesc",  aom.MFnData.kString)
        cls.x3d_joints      = typFn.create("joints",      "x3dJnts",  aom.MFnData.kString)
        cls.x3d_name        = typFn.create("name",        "x3dName",  aom.MFnData.kString)
        
#        cls.x3d_channelsEnabled = cmpFn.create("channelsEnabled", "x3dChnlsEn") #Booleans
#        cls.x3d_aBoolean        = numFn.create("chEnabled0",      "x3dche0", aom.MFnNumericData.kBoolean, True)
#        cls.x3d_channelsEnabled.addChild(cls.x3d_aBoolean)
        
#        cls.x3d_values          = cmpFn.create("values",          "x3dVals")    #Floats
#        cls.x3d_aFloat          = numFn.create("values0",         "x3dVal0", aom.MFnNumericData.kFloat, 0)
#        cls.x3d_values.addChild(cls.x3d_aFloat)
        
        cls.x3d_enabled         = numFn.create("enabled",         "x3dEna", aom.MFnNumericData.kBoolean, True)
        cls.x3d_loop            = numFn.create("loop",            "x3dLp", aom.MFnNumericData.kBoolean, False)
        
        cls.x3d_startFrame      = numFn.create("startFrame",      "x3dSF", aom.MFnNumericData.kInt, 0)
        cls.x3d_endFrame        = numFn.create("endFrame",        "x3dEF", aom.MFnNumericData.kInt, 0)
        
        cls.x3d_loa             = numFn.create("loa",             "x3dLoa",  aom.MFnNumericData.kInt, -1)
        cls.x3d_frameIncrement  = numFn.create("frameIncrement",  "x3dFI",   aom.MFnNumericData.kInt, 1)
        cls.x3d_frameIndex      = numFn.create("frameIndex",      "x3dFIdx", aom.MFnNumericData.kInt, 0)
        
        cls.x3d_frameDuration   = numFn.create("frameDuration",   "x3dFDur", aom.MFnNumericData.kDouble, 0.1)

        cls.rk_mStartFrame      = numFn.create("timelineStartFrame", "rkMTSF", aom.MFnNumericData.kInt, 0)
        cls.rk_mStopFrame       = numFn.create("timelineStopFrame",  "rkMTSP", aom.MFnNumericData.kInt, 0)
        
        cls.rk_animPkg          = typFn.create("animationPackage", "animPkg", aom.MFnData.kString)
        
        cls.addAttribute(cls.x3d_channels)
#        cls.addAttribute(cls.x3d_channelsEnabled)
        cls.addAttribute(cls.x3d_description)
        cls.addAttribute(cls.x3d_enabled)
        cls.addAttribute(cls.x3d_endFrame)
        cls.addAttribute(cls.x3d_frameDuration)
        cls.addAttribute(cls.x3d_frameIncrement)
        cls.addAttribute(cls.x3d_frameIndex)
        cls.addAttribute(cls.x3d_joints)
        cls.addAttribute(cls.x3d_loa)
        cls.addAttribute(cls.x3d_loop)
        cls.addAttribute(cls.x3d_name)
        cls.addAttribute(cls.x3d_startFrame)
#        cls.addAttribute(cls.x3d_values)
        cls.addAttribute(cls.rk_mStartFrame)
        cls.addAttribute(cls.rk_mStopFrame)
        cls.addAttribute(cls.rk_animPkg)

#    def postConstructor(self):
#        pass