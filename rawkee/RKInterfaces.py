import sys
import maya.cmds as cmds
import maya.mel  as mel

import numpy as np
from typing import Final

import maya.api.OpenMaya as aom

#Python implementation of C++ web3dExportMethods

X3D_TRANS:     Final[str] = "transform"
###########################################
# Versions of the Maya Transform Node     #
###########################################
X3D_GROUP:     Final[str] = "x3dGroup"    #
X3D_SWITCH:    Final[str] = "x3dSwitch"   #
X3D_COLLISION: Final[str] = "x3dCollision"#
X3D_BILLBOARD: Final[str] = "x3dBillboard"#
X3D_ANCHOR:    Final[str] = "x3dAnchor"   #
###########################################

X3D_LOD:       Final[str] = "lodGroup"
X3D_MESH:      Final[str] = "mesh"

X3D_INLINE:    Final[str] = "x3dInline"

X3D_AUDIOCLIP: Final[str] = "audio"
X3D_SOUND:     Final[str] = "x3dSound"
X3D_TEXTTRANS: Final[str] = "place2dTexture"
X3D_MESH:      Final[str] = "mesh"

X3D_PROXSENSOR:      Final[str] = "x3dProximitySensor"
X3D_VISSENSOR:       Final[str] = "x3dVisbilitySensor"
X3D_LOADSENSOR:      Final[str] = "x3dLoadSensor"
X3D_KEYSENSOR:       Final[str] = "x3dKeySensor"
X3D_STRINGSENSOR:    Final[str] = "x3dStringSensor"
X3D_CYLSENSOR:       Final[str] = "x3dCylinderSensor"
X3D_PLANESENSOR:     Final[str] = "x3dPlaneSensor"
X3D_SPHERESENSOR:    Final[str] = "x3dSphereSensor"
X3D_TIMESENSOR:      Final[str] = "x3dTimeSensor"
X3D_TOUCHSENSOR:     Final[str] = "x3dTouchSensor"

X3D_BOOLTRIGGER:      Final[str] = "x3dBooleanTrigger"
X3D_BOOLFILTER:       Final[str] = "x3dBooleanFilter"
X3D_BOOLTOGGLE:       Final[str] = "x3dBooleanToggle"
X3D_INTTRIGGER:       Final[str] = "x3dIntegerTrigger"
X3D_TIMETRIGGER:      Final[str] = "x3dTimeTrigger"

X3D_NAVIGATION:      Final[str] = "x3dNavigationInfo"
X3D_WORLDINFO:       Final[str] = "x3dWorldInfo"

X3D_POSINTER:       Final[str] = "x3dPositionInterpolator"
X3D_ORIINTER:       Final[str] = "x3dOrientationInterpolator"
X3D_COORDINTER:     Final[str] = "x3dCoordinateInterpolator"
X3D_NORMINTER:      Final[str] = "x3dNormalInterpolator"
X3D_COLORINTER:     Final[str] = "x3dColorInterpolator"
X3D_SCALINTER:      Final[str] = "x3dScalarInterpolator"

X3D_BOOLSEQ:      Final[str] = "x3dBooleanSequencer"
X3D_INTSEQ:       Final[str] = "x3dIntegerSequencer"

X3D_SCRIPT:       Final[str] = "x3dScript"

X3D_IFS:       Final[str] = "x3dIndexedFaceSet"
X3D_COL:       Final[str] = "x3dColor"
X3D_COLRGBA:   Final[str] = "x3dColorRGBA"
X3D_NORMAL:    Final[str] = "x3dNormal"
X3D_TEXCOORD:  Final[str] = "x3dTextureCoordinate"
X3D_COORD:     Final[str] = "x3dCoordinate"

X3D_BOX:       Final[str] = "x3dBox"
X3D_SPHERE:    Final[str] = "x3dSphere"
X3D_CONE:      Final[str] = "x3dCone"
X3D_CYL:       Final[str] = "x3dCylinder"

X3D_VIEW:       Final[str] = "camera"
X3D_DIRLIGHT:   Final[str] = "directionalLight"
X3D_SPOTLIGHT:  Final[str] = "spotLight"
X3D_POINTLIGHT: Final[str] = "pointLight"

X3D_AMBLIGHT:   Final[str] = "ambientLight"
X3D_AREALIGHT:  Final[str] = "areaLight"
X3D_VOLLIGHT:   Final[str] = "volumeLight"

X3D_HANIMJOINT:      Final[str] = "joint"
X3D_HANIMSITE:       Final[str] = "transform"
X3D_GAMEPADSENSOR:   Final[str] = "x3dGamepadSensor"

X3DMETAD:  Final[int] = 0
X3DMETAF:  Final[int] = 1
X3DMETAI:  Final[int] = 2
X3DMETASE: Final[int] = 3
X3DMETAST: Final[int] = 4


class RKInterfaces():
    def __init__(self):
        print("RKInterfaces")
        
    def __del__(self):
        pass
        
    def setExportEncoding(self, exEncoding):
        pass
        
    def setConsolidate(self, value):
        pass
        
    def setGlobalNPV(self, value):
        pass
        
    def setGlobalCA(self, value):
        pass
        
    def setUseRelURL(self, value):
        pass
        
    def setUseRelURLW(self, value):
        pass
        
    def setImageDir(self, value):
        pass
        
    def setAudioDir(self, value):
        pass
        
    def setInlineDir(self, value):
        pass
        
    def setBaseUrl(self, value):
        pass
    
    def getDirection(self, euler, point=(0.0, 0.0, -1.0)):
        tMat  = aom.MTransformationMatrix()
        tMat.setRotation(euler)
        mVec  = aom.MVector(aom.MPoint(point))
        rVec  = mVec * tMat.asMatrix()
        
        rPoint = aom.MPoint(rVec)
        
        return (rPoint.x, rPoint.y, rPoint.z)
        
    def getSFVec3fFromMPoint(self, p):
        return (p.x, p.y, p.z)

    def getSFVec3f(self, v):
        return (v[0], v[1], v[2])
        
    def getSFVec3fFromList(self, l):
        return (l[0], l[1], l[2])
        
    def getSFRotation(self, q):
        return (q[0][0], q[0][1], q[0][2], q[1])

    def getSFRotationFromEuler(self, euler):
        cv = ( np.cos(euler[2]/2), np.cos(euler[1]/2), np.cos(euler[0]/2) )
        sv = ( np.sin(euler[2]/2), np.sin(euler[1]/2), np.sin(euler[0]/2) ) 
	
        aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] )
        wVec = 2 * np.arccos( aCosDouble )
        xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]) 
        yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2])
        zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2])

        denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec)    
        xVec1 = 0.0
        yVec1 = 0.0
        zVec1 = 1.0
        wVec1 = 0.0
        
        if denominator != 0:
            dSqrt = np.sqrt(denominator)
            xVec1 = xVec/dSqrt;
            yVec1 = yVec/dSqrt;
            zVec1 = zVec/dSqrt;
            wVec1 = wVec;
        
        return (xVec1, yVec1, zVec1, wVec1)























