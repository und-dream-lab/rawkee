import maya.api.OpenMaya as aom

class X3DViewpointCamera(aom.MPxNode):
    kPluginNodeName = "Viewpoint"
    kPluginNodeId   = aom.MTypeId(0x00108F7B)  # Assign a unique ID

    # Attributes
    aFocalLength = aom.MObject()
    aCenterOfInterest = aom.MObject()
    aOutputCamera = aom.MObject()

    def __init__(self):
        aom.MPxNode.__init__(self)

    @classmethod
    def creator(cls):
        return X3DViewpointCamera()

    @classmethod
    def initialize(cls):
        nAttr = aom.MFnNumericAttribute()

        # Focal Length
        cls.aFocalLength = nAttr.create("focalLength", "fl", aom.MFnNumericData.kDouble, 35.0)
        nAttr.setMin(1.0)
        nAttr.setMax(200.0)
        cls.addAttribute(cls.aFocalLength)

        # Center of Interest
        cls.aCenterOfInterest = nAttr.create("centerOfInterest", "coi", aom.MFnNumericData.kDouble, 100.0)
        nAttr.setMin(1.0)
        cls.addAttribute(cls.aCenterOfInterest)

        # Output Camera
        cls.aOutputCamera = nAttr.create("outputCamera", "outCam", aom.MFnNumericData.kString)
        cls.addAttribute(cls.aOutputCamera)

        # Attribute Affections
        cls.attributeAffects(cls.aFocalLength, cls.aOutputCamera)
        cls.attributeAffects(cls.aCenterOfInterest, cls.aOutputCamera)

    def compute(self, plug, data):
        if plug == self.aOutputCamera:
            # Get input values
            focalLength = data.inputValue(self.aFocalLength).asDouble()
            centerOfInterest = data.inputValue(self.aCenterOfInterest).asDouble()

            # Create a new camera using MFnCamera
            camera = aom.MFnCamera()
            camera.create()
            camera.setFocalLength(focalLength)
            camera.setCenterOfInterest(centerOfInterest)

            # Set output value
            outputHandle = data.outputValue(self.aOutputCamera)
            outputHandle.setString(camera.fullPathName())
            data.setClean(plug)

