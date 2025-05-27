import maya.api.OpenMaya as aom
import maya.api.OpenMayaUI as aomui
import maya.api.OpenMayaRender as aomr

import maya.cmds as cmds

import maya.OpenMaya as om

from rawkee.nodes import x3dTimeSensor

# This is a Custom Maya node representing the X3D Sound Node
# Purpose is so the content author can add a node to the 
# authored scene, and then use the interaction editor to 
# route X3D events within the scene.
class X3DTimeSensor(aomui.MPxLocatorNode):
    TYPE_NAME = "x3dTimeSensor"
    
    # This TYPE_ID was registered with Alias in the early 
    # 2000s and was used in the C++ version of RawKee for 
    # versions of Maya - Maya 6 through Maya 8.5, and Maya 2019+.
    TYPE_ID = aom.MTypeId(0x00108F72)
    
    x3d_cycleInterval = None #SFTime   [in,out] cycleInterval    1     (0,∞)
    x3d_description   = None #SFString [in,out] description      ""
    x3d_enabled       = None #SFBool   [in,out] enabled          TRUE
    x3d_loop          = None #SFBool   [in,out] loop             FALSE
    #SFNode   [in,out] metadata         NULL  [X3DMetadataObject]
    x3d_pauseTime     = None #SFTime   [in,out] pauseTime        0     (-∞,∞)
    x3d_resumeTime    = None #SFTime   [in,out] resumeTime       0
    x3d_startTime     = None #SFTime   [in,out] startTime        0     (-∞,∞)
    x3d_stopTime      = None #SFTime   [in,out] stopTime         0     (-∞,∞)

    rk_keyFrameStep   = None
    rk_startFrame     = None
    rk_stopFrame      = None
    rk_fps            = None
    
    rk_asSplines      = None
    rk_animPkg        = None
    

    def __init__(self):
        super(X3DTimeSensor, self).__init__()

        
    @classmethod
    def creator(cls):
        return X3DTimeSensor()

        
    @classmethod
    def initialize(cls):
        typFn = aom.MFnTypedAttribute()
        cls.x3d_description = typFn.create("description", "x3dDesc", aom.MFnData.kString)

        numFn = aom.MFnNumericAttribute()
        cls.rk_keyFrameStep = numFn.create("keyFrameStep", "rkKFStep", aom.MFnNumericData.kInt, 1)
        numFn.setObject(cls.rk_keyFrameStep)
        numFn.setMin(1)
        numFn.setMax(100)

        cls.rk_startFrame = numFn.create("startFrame", "rkStaF", aom.MFnNumericData.kInt, 0)
        cls.rk_stopFrame = numFn.create("stopFrame", "rkStoF", aom.MFnNumericData.kInt, 0)
        cls.rk_fps = numFn.create("framesPerSecond", "rkFPS", aom.MFnNumericData.kInt, 30)
        numFn.setObject(cls.rk_fps)
        numFn.setMin(1)
        numFn.setMax(60)

        cls.x3d_cycleInterval = numFn.create("cycleInterval", "x3dCInt", aom.MFnNumericData.kFloat, 1)
        numFn.setObject(cls.x3d_cycleInterval)
        numFn.setMin(0.0)

        cls.x3d_enabled = numFn.create("enabled", "x3dEna", aom.MFnNumericData.kBoolean, True)
        cls.x3d_loop = numFn.create("loop", "x3dLp", aom.MFnNumericData.kBoolean, False)

        cls.x3d_pauseTime = numFn.create("pauseTime", "x3dPT", aom.MFnNumericData.kFloat, 0.0)
        cls.x3d_resumeTime = numFn.create("resumeTime", "x3dRT", aom.MFnNumericData.kFloat, 0.0)
        cls.x3d_startTime = numFn.create("startTime", "x3dStaT", aom.MFnNumericData.kFloat, 0.0)
        cls.x3d_stopTime = numFn.create("stopTime", "x3dStoT", aom.MFnNumericData.kFloat, 0.0)

        cls.rk_asSplines = numFn.create("exportAsSplines", "x3dSpl", aom.MFnNumericData.kBoolean, False)

        cls.rk_animPkg = typFn.create("animationPackage", "animPkg", aom.MFnData.kString)

        cls.addAttribute(cls.x3d_cycleInterval)
        cls.addAttribute(cls.x3d_description)
        cls.addAttribute(cls.x3d_enabled)
        cls.addAttribute(cls.x3d_loop)
        cls.addAttribute(cls.x3d_pauseTime)
        cls.addAttribute(cls.x3d_resumeTime)
        cls.addAttribute(cls.x3d_startTime)
        cls.addAttribute(cls.x3d_stopTime)
        cls.addAttribute(cls.rk_keyFrameStep)
        cls.addAttribute(cls.rk_startFrame)
        cls.addAttribute(cls.rk_stopFrame)
        cls.addAttribute(cls.rk_fps)
        cls.addAttribute(cls.rk_asSplines)
        cls.addAttribute(cls.rk_animPkg)

    #def postConstructor(self):
        #tNode = aom.MFnDependencyNode(self.thisMObject())
        #tNode.setIcon("x3dTimeSensor.png")
        #tName = tNode.name()
        #omSel = om.MSelectionList()
        #omSel.add(tName)
        #mobj = om.MObject()
        #omSel.getDependNode(0, mobj)
        #omNode = om.MFnDependencyNode(mobj)
        #omNode.setIcon(x3dTimeSensor.__file__.replace("\\", "/").rsplit("/", 1)[0] + "/icons/x3dTimeSensor.png")
        #pass