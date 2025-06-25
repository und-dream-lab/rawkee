import maya.api.OpenMaya as aom
import maya.api.OpenMayaUI as aomui
import maya.api.OpenMayaRender as aomr

import maya.cmds as cmds

# This is a Custom Maya node representing the X3D Sound Node
# Purpose is so the content author can add a node to the 
# authored scene, and then use the interaction editor to 
# route X3D events within the scene.
class RKAnimPack(aomui.MPxLocatorNode):
    TYPE_NAME = "rkAnimPack"
    
    # This TYPE_ID was registered with Autodesk in 2024 for the 
    # RawKee PE plugin.
    TYPE_ID = aom.MTypeId(0x0013fe41)
    
    #---------------------------------------------
    # Maya Node and Maya timeline attributes
    x3d_mimickedNode     = None
    #x3d_oldMimickedValue = None
    
    rk_keyFrameStep = None
    rk_mStartFrame  = None
    rk_mStopFrame   = None
    rk_fps          = None
    
    rk_asSplines    = None
    rk_animPkg      = None

    #--------------------------------------------
    # Shared X3D Fields
    x3d_autoRefresh          = None # AudioClip, MovieTexture
    x3d_autoRefreshTimeLimit = None # AudioClip, MovieTexture
    x3d_description          = None # All
    x3d_enabled              = None # All
    x3d_gain                 = None # AudioClip, MovieTexture
    x3d_load                 = None # AudioClip, MovieTexture
    x3d_loop                 = None # All
    x3d_pauseTime            = None # AudioClip, MovieTexture, TimeSensor
    x3d_pitch                = None # AudioClip, MovieTexture
    x3d_resumeTime           = None # AudioClip, MovieTexture, TimeSensor
    x3d_startTime            = None # AudioClip, MovieTexture, TimeSensor
    x3d_stopTime             = None # AudioClip, MovieTexture, TimeSensor
    
    #---------------------------------------------
    # Attribute for connecting Maya 'movie' and 
    # 'audio' nodes as helpler nodes to fill in
    # the information for X3D MovieTexture and 
    # AudioClip export.
    x3d_connectedFile = None
    
    #---------------------------------------------
    # Attributes for the AudioClip Option
    #x3d_autoRefresh          = None #SFTime   [in,out] autoRefresh          0.0   [0,∞)
    #x3d_autoRefreshTimeLimit = None #SFTime   [in,out] autoRefreshTimeLimit 3600.0   [0,∞)
    #SFString [in,out] description          ""
    #SFBool   [in,out] enabled              TRUE
    #SFFloat  [in,out] gain                 1     (-∞,∞)
    #SFBool   [in,out] load                 TRUE
    #SFBool   [in,out] loop                 FALSE
    #SFTime   [in,out] pauseTime            0     (-∞,∞)
    #SFFloat  [in,out] pitch                1.0   (0,∞)
    #SFTime   [in,out] resumeTime           0     (-∞,∞)
    #SFTime   [in,out] startTime            0     (-∞,∞)
    #SFTime   [in,out] stopTime             0     (-∞,∞)
    #### #MFString [in,out] url                  []    [URI]    

    #---------------------------------------------
    # Attributes for the HAnimMotion Option
    x3d_channels        = None
    x3d_channelsEnabled = None
    #x3d_description     = None
    #x3d_enabled         = None
    x3d_endFrame        = None
    x3d_frameDuration   = None
    x3d_frameIncrement  = None
    x3d_frameIndex      = None
    x3d_joints          = None
    x3d_loa             = None
    #x3d_loop            = None
    x3d_name            = None
    x3d_startFrame      = None
    x3d_values          = None
    #### x3d_aBoolean        = None
    #### x3d_aFloat          = None
    
    #---------------------------------------------
    # Attributes for the MovieTexture Option
    #SFTime   [in,out] autoRefresh          0.0    [0,∞)
    #SFTime   [in,out] autoRefreshTimeLimit 3600.0 [0,∞)
    #SFString [in,out] description          ""
    #SFBool   [in,out] enabled              TRUE
    #SFInt32  [in,out] gain                 1      [-∞,∞)
    #SFBool   [in,out] load                 TRUE
    #SFBool   [in,out] loop                 FALSE
    #SFTime   [in,out] pauseTime            0      (-∞,∞)
    #SFFloat  [in,out] pitch                1.0    (0,∞)
    #SFTime   [in,out] resumeTime           0      (-∞,∞)
    x3d_speed = None #SFFloat  [in,out] speed                1.0    (-∞,∞)
    #SFTime   [in,out] startTime            0      (-∞,∞)
    #SFTime   [in,out] stopTime             0      (-∞,∞)
    #MFString [in,out] url                  []     [URI]
    #SFTime   [out]    duration_changed   
    #SFTime   [out]    elapsedTime   
    #SFBool   [out]    isActive   
    #SFBool   [out]    isPaused   
    #SFBool   []       repeatS              TRUE
    #SFBool   []       repeatT              TRUE
    #SFNode   []       textureProperties    NULL   [TextureProperties]    

    #---------------------------------------------
    # Attributes for the TimeSensor Option
    x3d_cycleInterval = None #SFTime   [in,out] cycleInterval    1     (0,∞)
    #x3d_description   = None #SFString [in,out] description      ""
    #x3d_enabled       = None #SFBool   [in,out] enabled          TRUE
    #x3d_loop          = None #SFBool   [in,out] loop             FALSE
    #x3d_pauseTime     = None #SFTime   [in,out] pauseTime        0     (-∞,∞)
    #x3d_resumeTime    = None #SFTime   [in,out] resumeTime       0
    #x3d_startTime     = None #SFTime   [in,out] startTime        0     (-∞,∞)
    #x3d_stopTime      = None #SFTime   [in,out] stopTime         0     (-∞,∞)
    
    #---------------------------------------------
    # Dynamic Attributes added via MEL to manage animation connections
    # select '(rkAnimPack name)';
    # With an IF statment check to see if 'animationConnections' compound attribute exists, if it doesn't then create it.
    #      addAttr -ln animationConnections -sn animConn -nc 1 -at compound;
    # With an IF statement check to see if it already exists, and if not add a new connection for the animation type...
    #      addAttr -ln (nodename)_(x3d-interpolator-type) -at message -parent animConn
    # With an IF statement check to see if a connection exists
    #      isConnected (nodename).message (rkAnimPack name).(nodename)_(x3d-interpolator-type)
    # If false then make the connection
    #      connectAttr (nodename).message (rkAnimPack name).(nodename)_(x3d-interpolator-type)
    

    def __init__(self):
        super(RKAnimPack, self).__init__()
        
    @classmethod
    def creator(cls):
        return RKAnimPack()
        
    @classmethod
    def initialize(cls):
        
        numFn = aom.MFnNumericAttribute()
        typFn = aom.MFnTypedAttribute()
        
        cls.x3d_mimickedNode  = numFn.create("mimickedType", "mimType", aom.MFnNumericData.kInt, 0)
        numFn.setObject(cls.x3d_mimickedNode)
        numFn.setMin(0)
        numFn.setMax(4)

        #cls.x3d_oldMimickedValue  = numFn.create("oldMimickedValue", "oldMimType", aom.MFnNumericData.kInt, 0)
        #numFn.setObject(cls.x3d_oldMimickedValue)
        #numFn.setMin(0)
        #numFn.setMax(4)

        cls.x3d_connectedFile = typFn.create("connectedFile", "conFile", aom.MFnData.kString)
        typFn.setObject(cls.x3d_connectedFile)
        typFn.connectable = True
        
        cls.rk_keyFrameStep = numFn.create("keyFrameStep", "kfs", aom.MFnNumericData.kInt, 1)
        cls.rk_mStartFrame  = numFn.create("timelineStartFrame", "tStartFrame", aom.MFnNumericData.kInt, 0)
        cls.rk_mStopFrame   = numFn.create("timelineStopFrame", "tStopFrame", aom.MFnNumericData.kInt, 0)
        cls.rk_fps          = numFn.create("framesPerSecond", "fps", aom.MFnNumericData.kFloat, 30.0)
        numFn.setObject(cls.rk_fps)
        numFn.setMin(1.0)
        
        cls.rk_asSplines    = numFn.create("exportAsSplines", "eaSplines", aom.MFnNumericData.kBoolean, False)
        cls.rk_animPkg      = typFn.create("animationPackage", "animPkg", aom.MFnData.kString)
        
        #cls.x3d_channels = typFn.create("channels", "chnls", aom.MFnData.kString)
        
        #cls.x3d_channelsEnabled

        #cls.x3d_cycleInterval = numFn.create("cycleInterval", "cInt", aom.MFnNumericData.kFloat, 1)
        #numFn.setObject(cls.x3d_cycleInterval)
        #numFn.setMin(0.0)

        #cls.x3d_autoRefresh = numFn.create("autoRefresh", "aRefresh", aom.MFnNumericData.kFloat, 0.0)
        #numFn.setObject(cls.x3d_autoRefresh)
        #numFn.setMin(0.0)

        #cls.x3d_autoRefreshTimeLimit = numFn.create("autoRefreshTimeLimit", "arTimeLimit", aom.MFnNumericData.kFloat, 3600.0)
        #numFn.setObject(cls.x3d_autoRefreshTimeLimit)
        #numFn.setMin(0.0)

        cls.x3d_description = typFn.create("description", "desc", aom.MFnData.kString)

        cls.x3d_enabled = numFn.create("enabled", "ena", aom.MFnNumericData.kBoolean, True)
        
        #cls.x3d_gain = numFn.create("gain", "gn", aom.MFnNumericData.kFloat, 1)

        #cls.x3d_load = numFn.create("load", "ld", aom.MFnNumericData.kBoolean, True)
        
        #cls.x3d_endFrame = numFn.create("endFrame", "dFrame", aom.MFnNumericData.kInt, 0)
        #numFn.setObject(cls.x3d_endFrame)
        #numFn.setMin(0)

        #cls.x3d_frameDuration = numFn.create("frameDuration", "frDuration", aom.MFnNumericData.kFloat, 0.1)
        #numFn.setObject(cls.x3d_frameDuration)
        #numFn.setMin(0)

        #cls.x3d_frameIncrement = numFn.create("frameIncrement", "frInc", aom.MFnNumericData.kInt, 1)

        #cls.x3d_frameIndex = numFn.create("frameIndex", "frIdx", aom.MFnNumericData.kInt, 0)
        #numFn.setObject(cls.x3d_frameIndex)
        #numFn.setMin(0)

        #cls.x3d_joints = typFn.create("joints", "jnts", aom.MFnData.kString)
        
        #cls.x3d_loa = numFn.create("levelOfArticulation", "loa", aom.MFnNumericData.kInt, -1)
        #numFn.setObject(cls.x3d_loa)
        #numFn.setMin(-1)
        #numFn.setMax(4)

        cls.x3d_loop = numFn.create("loop", "xlp", aom.MFnNumericData.kBoolean, False)
        
        #cls.x3d_name = typFn.create("name", "ne", aom.MFnData.kString)

        #cls.x3d_startFrame = numFn.create("startFrame", "staFrame", aom.MFnNumericData.kInt, 0)
        #numFn.setObject(cls.x3d_startFrame)
        #numFn.setMin(0)
        
        #cls.x3d_values

        #cls.x3d_pauseTime = numFn.create("pauseTime", "paTime", aom.MFnNumericData.kFloat, 0.0)

        #cls.x3d_pitch = numFn.create("pitch", "ptch", aom.MFnNumericData.kFloat, 1.0)
        #numFn.setObject(cls.x3d_pitch)
        #numFn.setMin(0.0)

        #cls.x3d_resumeTime = numFn.create("resumeTime", "reTime", aom.MFnNumericData.kFloat, 0.0)

        #cls.x3d_speed = numFn.create("speed", "spd", aom.MFnNumericData.kFloat, 1.0)

        #cls.x3d_startTime = numFn.create("startTime", "staTime", aom.MFnNumericData.kFloat, 0.0)

        #cls.x3d_stopTime = numFn.create("stopTime", "stoTime", aom.MFnNumericData.kFloat, 0.0)

        cls.addAttribute(cls.x3d_mimickedNode)
        #cls.addAttribute(cls.x3d_oldMimickedValue)
        cls.addAttribute(cls.x3d_connectedFile)
        cls.addAttribute(cls.rk_keyFrameStep)
        cls.addAttribute(cls.rk_mStartFrame)
        cls.addAttribute(cls.rk_mStopFrame)
        cls.addAttribute(cls.rk_fps)
        cls.addAttribute(cls.rk_asSplines)
        cls.addAttribute(cls.rk_animPkg)

        #cls.addAttribute(cls.x3d_autoRefresh)
        #cls.addAttribute(cls.x3d_autoRefreshTimeLimit)
        #cls.addAttribute(cls.x3d_channels)
        #cls.addAttribute(cls.x3d_cycleInterval)
        cls.addAttribute(cls.x3d_description)
        cls.addAttribute(cls.x3d_enabled)
        #cls.addAttribute(cls.x3d_gain)
        
        #cls.addAttribute(cls.x3d_load)
        #cls.addAttribute(cls.x3d_endFrame)

        #cls.addAttribute(cls.x3d_frameDuration)
        #cls.addAttribute(cls.x3d_frameIncrement)
        #cls.addAttribute(cls.x3d_frameIndex)
        #cls.addAttribute(cls.x3d_joints)
        #cls.addAttribute(cls.x3d_loa)
        cls.addAttribute(cls.x3d_loop)
        #cls.addAttribute(cls.x3d_name)
        #cls.addAttribute(cls.x3d_startFrame)

        #cls.x3d_values

        #cls.addAttribute(cls.x3d_pitch)
        #cls.addAttribute(cls.x3d_speed)
        #cls.addAttribute(cls.x3d_pauseTime)
        #cls.addAttribute(cls.x3d_resumeTime)
        #cls.addAttribute(cls.x3d_startTime)
        #cls.addAttribute(cls.x3d_stopTime)
        
