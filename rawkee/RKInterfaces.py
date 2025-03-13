import sys
import maya.cmds as cmds
import maya.mel  as mel

import numpy as np
import array
from typing import Final

# Needed for Data URIs
import base64
import mimetypes
import os

# Needed for PixelImages
import ctypes

# Needed for Video / Audio format conversion
import ffmpeg

# Needed for WebP Images
import PIL as pil

import maya.api.OpenMaya as aom

import ntpath

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


    # Method converts Maya procedural texture nodes, including layeredTexture nodes to "File" texture nodes
    def proc2fileNode(self, textureNode, imgExt, imagePath, imgFormat, width, height):
        fileNodeName = textureNode.name() + "_rkConvertedProcedural"
        
        rkAdjTexSize       = cmds.optionVar( q='rkAdjTexSize'  )
        
        if rkAdjTexSize == True:
            width  = cmds.optionVar( q='rkDefTexWidth' )
            height = cmds.optionVar( q='rkDefTexHeight')
            
        fileName = imagePath
        if fileName == "":
            fileName = fileNodeName + "." + imgExt
        else:
            fileName = imagePath + "/" + fileNodeName + "." + imgExt
            
        return cmds.convertSolidTx( name=fileNodeName, samplePlane=True, antiAlias=True, force=True, fillTextureSeams=True, shadows=False, fileImageName=fileName, alpha=True, resolutionX=width, resolutionY=height, fileFormat=imgFormat)

    
    # Method converts Maya textureNode colorRGB(a) to an image file.
    def proc2file(self, textureObj, outPath, imgFormat):
        try:
            fImage = aom.MImage.readFromTextureNode(textureObj)
            w, h = fImage.getSize()
            
            rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

            if rkAdjTexSize == True:
                w = cmds.optionVar( q='rkDefTexWidth' )
                h = cmds.optionVar( q='rkDefTexHeight')

                fImage.resize(w, h, False)
                
            fImage.writeToFile(outPath, imgFormat)
            
            return True
            
        except:
            return False
        

    # Convert image file from one fomat to another.
    def fileFormatConvert( self, inPath, outPath, newFormat):
        try:
            fImage = aom.MImage.readFromFile(inPath)
            w, h = fImage.getSize()
            
            rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

            if rkAdjTexSize == True:
                w = cmds.optionVar( q='rkDefTexWidth' )
                h = cmds.optionVar( q='rkDefTexHeight')

                fImage.resize(w, h, False)
                
            fImage.writeToFile(outPath, newFormat)
            
            return True
            
        except:
            return False
            
    
    def fileConvertToWebP ( self, inPath, outPath):
        try:
            image = pil.Image.open(inPath).convert("RGB")
            
            rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

            if rkAdjTexSize == True:
                w = cmds.optionVar( q='rkDefTexWidth' )
                h = cmds.optionVar( q='rkDefTexHeight')

                image.resize((w, h))

            image.save(outPath, "webp")
            return True
            
        except:
            return False
        

    # Use FFmpeg to convert the audio file to a new format
    def audioFormatConvert(self, inPath, outPath, newFormat):
        try:
            media = ffmpeg.input(inPath)
            if   newFormat == "MP3":
                media.output(outPath, acodec='mp3'       ).run()
            elif newFormat == "MP4":
                media.output(outPath, acodec='libfdk_aac').run()
            elif newFormat == "OGA":
                media.output(outPath, acodec='libvorbis' ).run()
            elif newFormat == "WAV":
                media.output(outPath, acodec='pcm_s16le' ).run()
        except:
            return False
        
        return True

    # Use FFmpeg to convert the video/audio file to a new format
    def movieFormatConvert(self, inPath, outPath, newFormat):
        try:
            probe = probe = ffmpeg.probe(inPath)
            vStream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            nW = 1
            nH = 1
            if vStream:
                nW = vStream['width']
                nH = vStream['height']
            
            rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

            if rkAdjTexSize == True:
                nW = cmds.optionVar( q='rkDefTexWidth' )
                nH = cmds.optionVar( q='rkDefTexHeight')

            media = ffmpeg.input(inPath)

            if   newFormat == "MP4":
                media.filter('scale', nW, nH).output(outpath, vcodec='libx264',    acodec='libfdk_aac').run()
            elif newFormat == "MOV":
                media.filter('scale', nW, nH).output(outpath, vcodec='mpeg4',      acodec='alac'      ).run()
            elif newFormat == "OGG":
                media.filter('scale', nW, nH).output(outPath, vcodec='libtheora',  acodec='libvorbis' ).run()
            elif newFormat == "WEBM":
                media.filter('scale', nW, nH).output(outPath, vcodec='libvpx-vp9', acodec='libopus'   ).run()
            elif newFormat == "AVI":
                media.filter('scale', nW, nH).output(outPath, vcodec='libxvid',    acodec='pcm_s16le' ).run()
                
        except:
            pass
            #return False
            
        #return True

    
    def image2pixel(self, imgPath):
        pixelData = ()
        
        fImage = aom.MImage()
        fImage = fImage.readFromFile(imgPath)
        
        w, h = fImage.getSize()

        rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

        if rkAdjTexSize == True:
            w = cmds.optionVar( q='rkDefTexWidth' )
            h = cmds.optionVar( q='rkDefTexHeight')

            fImage.resize(w, h, False)
            
        pPtr      = fImage.pixels()
        pDepth    = fImage.depth()
        
        nPix      = w * h
        nBytes    = nPix * pDepth
        pixArray  = ctypes.cast(pPtr, ctypes.POINTER(ctypes.c_ubyte * nBytes)).contents
        pixelData = pixelData + (w, h, pDepth)
        print("Width: " + str(w) + ", Height: " + str(h) + ", Depth: " + str(pDepth) + ", Pixels: " + str(nPix) + ", Array Length: " + str(nBytes))

        pIdx = 0
        while pIdx < nBytes:
            pixNum     = pixArray[pIdx]     # r
            
            if pDepth > 1:
                pixNum = pixNum << 8
                newNum = pixArray[pIdx + 1] # g
                pixNum = pixNum + newNum
                
            if pDepth > 2:
                pixNum = pixNum << 8
                newNum = pixArray[pIdx + 2] # b
                pixNum = pixNum + newNum
                
            if pDepth > 3:
                pixNum = pixNum << 8
                newNum = pixArray[pIdx + 3] # a
                pixNum = pixNum + newNum

            pixelData = pixelData + (hex(pixNum),)
            pIdx += pDepth

            if (pIdx // pDepth) // 50000 == (pIdx // pDepth) / 50000:
                print("Pixel IDX: " +  str(pIdx // pDepth) + " out of " + str(nPix))
                
        fImage.release()
        
        return pixelData

        
    # Creating a Data URI from any file type.
    def media2uri(self, filePath):
        dataURI = ""
        
        mimeType, toss = mimetypes.guess_type(filePath)
        
        if mimeType is None:
            mimeType = 'application/octet-stream'

        try:
            with open(filePath, 'rb') as mediaFile:
                mediaData  = mediaFile.read()
                base64Data = base64.b64encode(mediaData).decode('utf-8')
                dataURI = "data:" + mimeType + ";charset=UTF-8;base64," + base64Data
        except:
            pass
                
        return dataURI

    def copyFile(self, inPath, outPath):
        print(inPath)
        print(outPath)
        try:
            with open(inPath, 'rb') as inFile, open(outPath, 'wb') as outFile:
                while True:
                    chunk = inFile.read(4096)
                    if not chunk:
                        break
                    outFile.write(chunk)
        except FileNotFoundError:
            print("Input File not Found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def getFileName(self, inPath):
        head, tail = ntpath.split(inPath)
        return tail














