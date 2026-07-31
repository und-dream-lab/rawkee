import sys
import maya.cmds as cmds
import maya.mel  as mel
import ufe

import numpy as np
import cv2
import imageio.v3 as iio
#import py360convert

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
try:
    import PIL as pil
except ImportError:
    pass

import maya.api.OpenMaya as aom


class RKInterfaces():
    def __init__(self):
        print("RKInterfaces")
        
    def __del__(self):
        pass
        

    def getDeg2Rad(self, deg):
        return np.deg2rad(deg)


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
        if v[0] > -0.0000000001 and v[0] < 0.0000000001:
            v[0] = 0.0
        if v[1] > -0.0000000001 and v[1] < 0.0000000001:
            v[1] = 0.0
        if v[2] > -0.0000000001 and v[2] < 0.0000000001:
            v[2] = 0.0
        return (v[0], v[1], v[2])
        
    def getSFVec3fFromList(self, l):
        return (l[0], l[1], l[2])
    
    #############################################################################
    # q - tForm.rotation(maya.api.OpenMaya.MSpace.kTransform, True).asAxisAngle()
    # 
    # Because of this, rotation order doesn't matter.
    # .asAxisAngle() returns a tuple (MVector, float) getSFRotation returns a tuple (x, y, z, w)
    #############################################################################
    def getSFRotation(self, q):
        x = q[0][0]
        if x > -0.0000000001 and x < 0.0000000001:
            x = 0.0
        y = q[0][1]
        if y > -0.0000000001 and y < 0.0000000001:
            y = 0.0
        z = q[0][2]
        if z > -0.0000000001 and z < 0.0000000001:
            z = 0.0
        w = q[1]
        if w > -0.0000000001 and w < 0.0000000001:
            w = 0.0

        return (x, y, z, w)

    #######################################################################
    # This function is broken and not currently being used.
    #######################################################################
    def getSFRotationFromEuler(self, euler, degrees=True, order=0):
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
            width  = cmds.optionVar( q='rkTextureWidth' )
            height = cmds.optionVar( q='rkTextureHeight')
            
        fileName = imagePath
        if fileName == "":
            fileName = fileNodeName + "." + imgExt
        else:
            fileName = imagePath + "/" + fileNodeName + "." + imgExt
            
        return cmds.convertSolidTx( name=fileNodeName, samplePlane=True, antiAlias=True, force=True, fillTextureSeams=True, shadows=False, fileImageName=fileName, alpha=True, resolutionX=width, resolutionY=height, fileFormat=imgFormat)


    def getUserDefinedMaxImageDimension(self):
        width  = cmds.optionVar( q='rkTextureWidth' )
        height = cmds.optionVar( q='rkTextureHeight')

        if width >= height:
            return width
        
        return height
        
    
    # Method converts Maya textureNode colorRGB(a) to an image file.
    def proc2file(self, textureObj, outPath, imgFormat):
        try:
            fImage = aom.MImage.readFromTextureNode(textureObj)
            w, h = fImage.getSize()
            
            rkAdjTexSize   = cmds.optionVar( q='rkAdjTexSize'  )

            if rkAdjTexSize == True:
                w = cmds.optionVar( q='rkTextureWidth' )
                h = cmds.optionVar( q='rkTextureHeight')

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
                w = cmds.optionVar( q='rkTextureWidth' )
                h = cmds.optionVar( q='rkTextureHeight')

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
                w = cmds.optionVar( q='rkTextureWidth' )
                h = cmds.optionVar( q='rkTextureHeight')

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
                nW = cmds.optionVar( q='rkTextureWidth' )
                nH = cmds.optionVar( q='rkTextureHeight')

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
            w = cmds.optionVar( q='rkTextureWidth' )
            h = cmds.optionVar( q='rkTextureHeight')

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


#    def create_x3d_single_hdr(self, input_path, output_path, face_size=1024):
#       # 1. Load the 32-bit HDR
#        print(f"Loading {input_path}...")
#        sphere_hdr = imageio.imread(input_path)
#
#        # 2. Convert to a Horizontal Cross layout
#        # This creates a single image with a 4:3 aspect ratio
#        print("Converting to horizontal cross...")
#        cross_hdr = py360convert.e2c(sphere_hdr, face_w=face_size, cube_format='horizon')

#        # 3. Save as a single HDR file
#        # Ensure it's float32 to maintain the tree reflections' brightness
#        imageio.imwrite(output_path, cross_hdr.astype(np.float32))
#        print(f"Successfully saved single cubemap: {output_path}")

#    def hdri2png(self, inputPath, outputPath):
#        # 1. Load the HDRI image
#        # This returns a float32 array where values typically range from 0.0 to +inf
#        hdriImage = iio.imread(inputPath)
#
#        # 2. Prepare the data for 16-bit PNG
#        # PNG does not support float32 directly; it uses uint16 (0 to 65535)
#        # We must scale the float values to the 16-bit integer range.
#        # Note: If your HDR has values > 1.0, you may need to 'tone map' or normalize first.
#        hdriNormalized = np.clip(hdriImage, 0, 1)  # Optional: Clamping to 0-1 range
#        hdri16bit = (hdriNormalized * 65535).astype(np.uint16)
#
#        # 3. Save as a 16-bit PNG
#        # Use the 'PNG-FI' (FreeImage) or 'PIL' plugin to ensure 16-bit support
#        iio.imwrite(outputPath, hdri16bit, extension='.png')


    def _hdri_equirect_to_faces(self, eq_img, face_size):
        """
        Convert an equirectangular (panoramic) HDR image to 6 cubemap face images.
        Returns a list of 6 float32 arrays, each (face_size, face_size, C).
        Face order follows the Vulkan/KTX2 standard: +X, -X, +Y, -Y, +Z, -Z.
        Bilinear interpolation via scipy.ndimage.map_coordinates.
        Longitude wraps correctly (mode='wrap') for seamless east-west edges.
        """
        from scipy.ndimage import map_coordinates

        h, w, C = eq_img.shape

        # Normalised grid for one face: s = horizontal [-1,1], t = vertical [-1,1 downward]
        s_vals = (np.arange(face_size, dtype=np.float32) + 0.5) / face_size * 2.0 - 1.0
        t_vals = (np.arange(face_size, dtype=np.float32) + 0.5) / face_size * 2.0 - 1.0
        s_grid, t_grid = np.meshgrid(s_vals, t_vals)   # (face_size, face_size)
        one = np.ones_like(s_grid)

        # Direction vectors per face (Vulkan cubemap convention, right-handed +Y up)
        # s increases left→right, t increases top→bottom
        face_vecs = [
            np.stack([ one,    -t_grid, -s_grid], axis=-1),  # +X
            np.stack([-one,    -t_grid,  s_grid], axis=-1),  # -X
            np.stack([ s_grid,  one,     t_grid], axis=-1),  # +Y
            np.stack([ s_grid, -one,    -t_grid], axis=-1),  # -Y
            np.stack([ s_grid, -t_grid,  one],    axis=-1),  # +Z
            np.stack([-s_grid, -t_grid, -one],    axis=-1),  # -Z
        ]

        faces = []
        for vecs in face_vecs:
            norms = np.sqrt((vecs ** 2).sum(axis=-1, keepdims=True))
            vecs  = vecs / norms
            x, y, z = vecs[..., 0], vecs[..., 1], vecs[..., 2]

            # Equirectangular UV: longitude φ = atan2(x, -z) maps -Z→u=0.5 (front),
            # +X→u=0.75 (right), matching the standard Maya/X3D -Z-forward convention.
            lon = np.arctan2(x, -z)                  # [-π, π]
            lat = np.arcsin(np.clip(y, -1.0, 1.0))   # [-π/2, π/2]
            u   = (lon + np.pi) / (2.0 * np.pi)      # [0, 1]  left=0, right=1
            v   = 0.5 - lat / np.pi                   # [0, 1]  top=0 (+Y), bottom=1 (-Y)

            px = (u * w - 0.5).ravel()
            py = (v * h - 0.5).ravel()

            face = np.empty((face_size, face_size, C), dtype=np.float32)
            for c in range(C):
                face[..., c] = map_coordinates(
                    eq_img[..., c], [py, px],
                    order=1, mode='wrap', cval=0.0
                ).reshape(face_size, face_size)

            face = np.clip(np.nan_to_num(face, nan=0.0, posinf=65504.0, neginf=0.0),
                           0.0, 65504.0)
            faces.append(face)

        return faces


    def hdri2ktx2(self, hdr_path, ktx2_path):
        """Converts an equirectangular HDRI to a KTX2 TEXTURE_CUBE_MAP (faceCount=6).

        Output is VK_FORMAT_R16G16B16A16_SFLOAT, full mip chain, HDR preserved.
        Face order follows Vulkan spec: +X(0) -X(1) +Y(2) -Y(3) +Z(4) -Z(5).
        Face size is auto-determined as input_width/4 rounded to nearest power of 2.
        """
        import struct
        from scipy.ndimage import map_coordinates

        # Vulkan cubemap face order: +X(0) -X(1) +Y(2) -Y(3) +Z(4) -Z(5)
        _FACES = [
            ('+X', ( 1,  0,  0), ( 0,  0, -1), ( 0,  1,  0)),
            ('-X', (-1,  0,  0), ( 0,  0,  1), ( 0,  1,  0)),
            ('+Y', ( 0,  1,  0), ( 1,  0,  0), ( 0,  0, -1)),
            ('-Y', ( 0, -1,  0), ( 1,  0,  0), ( 0,  0,  1)),
            ('+Z', ( 0,  0,  1), ( 1,  0,  0), ( 0,  1,  0)),
            ('-Z', ( 0,  0, -1), (-1,  0,  0), ( 0,  1,  0)),
        ]
        _KTX2_ID  = bytes([0xAB,0x4B,0x54,0x58,0x20,0x32,0x30,0xBB,0x0D,0x0A,0x1A,0x0A])
        _DFD_SIZE = 92

        # 1. Load equirectangular HDR (RGB float32)
        hdr = iio.imread(hdr_path).astype(np.float32)
        if hdr is None or hdr.size == 0:
            print(f"Error: Could not read {hdr_path}")
            return
        if hdr.ndim == 2:
            hdr = np.stack([hdr, hdr, hdr], axis=-1)
        elif hdr.shape[2] == 4:
            hdr = hdr[:, :, :3]
        hdr = np.clip(np.nan_to_num(hdr, nan=0.0, posinf=65504.0, neginf=0.0), 0.0, 65504.0)
        H, W = hdr.shape[:2]

        # Scale to mid-grey key (~0.18), then clip at 5.0 to prevent overexposure
        lum    = 0.2126*hdr[:,:,0] + 0.7152*hdr[:,:,1] + 0.0722*hdr[:,:,2]
        lw_bar = float(np.exp(np.mean(np.log(lum + 1e-6))))
        hdr    = np.clip(hdr * (0.18 / max(lw_bar, 1e-6)), 0.0, 5.0)

        # Auto-determine face size: width/4 rounded to nearest power of 2
        ideal = W / 4
        TILE  = 1
        while TILE * 2 <= ideal:
            TILE *= 2
        if (ideal - TILE) > (TILE * 2 - ideal):
            TILE *= 2
        print(f"  source: {W}x{H}  →  face: {TILE}x{TILE}")

        # 2. Build coordinate grids — computed once, shared across all faces
        idx = np.arange(TILE, dtype=np.float32)
        px_grid, py_grid = np.meshgrid(idx, idx)
        s = (2.0 * px_grid + 1.0) / TILE - 1.0
        t = 1.0 - (2.0 * py_grid + 1.0) / TILE

        # 3. Sample each face from the equirectangular image
        face_arrays = []
        for label, fwd_t, rgt_t, upd_t in _FACES:
            fwd = np.array(fwd_t, dtype=np.float32)
            rgt = np.array(rgt_t, dtype=np.float32)
            upd = np.array(upd_t, dtype=np.float32)

            x = fwd[0] + s * rgt[0] + t * upd[0]
            y = fwd[1] + s * rgt[1] + t * upd[1]
            z = fwd[2] + s * rgt[2] + t * upd[2]
            r = np.sqrt(x*x + y*y + z*z)
            x /= r;  y /= r;  z /= r

            lon = np.arctan2(x, -z)
            lat = np.arcsin(np.clip(y, -1.0, 1.0))
            u_eq = (lon + np.pi) / (2.0 * np.pi)
            v_eq = 0.5 - lat / np.pi

            src_x = (u_eq * W - 0.5).ravel()
            src_y = (v_eq * H - 0.5).ravel()

            face = np.empty((TILE, TILE, 3), dtype=np.float32)
            for c in range(3):
                face[:, :, c] = map_coordinates(
                    hdr[:, :, c], [src_y, src_x],
                    order=1, mode='wrap', cval=0.0
                ).reshape(TILE, TILE)

            face_arrays.append(np.clip(
                np.nan_to_num(face, nan=0.0, posinf=5.0, neginf=0.0), 0.0, 5.0
            ))
            print(f"  face {label:3s}  sampled")

        # 4. Generate mip chain for each face (box filter in float32 linear space)
        def make_mip_chain(f32):
            mips = [f32]
            while max(mips[-1].shape[:2]) > 1:
                prev = mips[-1]
                nh   = max(1, prev.shape[0] // 2)
                nw   = max(1, prev.shape[1] // 2)
                ph   = nh * 2 if nh * 2 <= prev.shape[0] else prev.shape[0]
                pw   = nw * 2 if nw * 2 <= prev.shape[1] else prev.shape[1]
                down = prev[:ph, :pw].reshape(nh, ph//nh, nw, pw//nw, 3).mean(axis=(1, 3))
                mips.append(down.astype(np.float32))
            return mips

        mip_chains = [make_mip_chain(f) for f in face_arrays]
        num_levels = len(mip_chains[0])

        # 5. Compute KTX2 file layout
        LEVEL_IDX_SIZE = num_levels * 24
        HEADER_END     = 80 + LEVEL_IDX_SIZE + _DFD_SIZE
        pad_bytes      = (8 - HEADER_END % 8) % 8
        PIXEL_OFFSET   = HEADER_END + pad_bytes

        level_byte_sizes = [6 * max(1, TILE >> lvl)**2 * 8 for lvl in range(num_levels)]

        level_file_offsets = {}
        cum = 0
        for lvl in range(num_levels - 1, -1, -1):
            level_file_offsets[lvl] = PIXEL_OFFSET + cum
            cum += level_byte_sizes[lvl]

        # 6. KTX2 header (80 bytes)
        hdr_bytes = _KTX2_ID
        hdr_bytes += struct.pack('<I', 97)                    # VK_FORMAT_R16G16B16A16_SFLOAT
        hdr_bytes += struct.pack('<I', 2)                     # typeSize: 2 bytes/component
        hdr_bytes += struct.pack('<I', TILE)                  # pixelWidth
        hdr_bytes += struct.pack('<I', TILE)                  # pixelHeight
        hdr_bytes += struct.pack('<I', 0)                     # pixelDepth: 0 for 2D
        hdr_bytes += struct.pack('<I', 0)                     # layerCount: non-array
        hdr_bytes += struct.pack('<I', 6)                     # faceCount: 6 = TEXTURE_CUBE_MAP
        hdr_bytes += struct.pack('<I', num_levels)
        hdr_bytes += struct.pack('<I', 0)                     # supercompression: none
        hdr_bytes += struct.pack('<I', 80 + LEVEL_IDX_SIZE)   # dfdByteOffset
        hdr_bytes += struct.pack('<I', _DFD_SIZE)
        hdr_bytes += struct.pack('<I', 0)                     # kvdByteOffset
        hdr_bytes += struct.pack('<I', 0)                     # kvdByteLength
        hdr_bytes += struct.pack('<Q', 0)                     # sgdByteOffset
        hdr_bytes += struct.pack('<Q', 0)                     # sgdByteLength

        # 6. Level index (num_levels × 24 bytes, level 0 → N-1)
        level_idx = b''
        for lvl in range(num_levels):
            level_idx += struct.pack('<Q', level_file_offsets[lvl])
            level_idx += struct.pack('<Q', level_byte_sizes[lvl])
            level_idx += struct.pack('<Q', level_byte_sizes[lvl])

        # 8. DFD (92 bytes) — matches verified reference file
        dfd = struct.pack('<I', _DFD_SIZE)                   # dfdTotalSize
        dfd += struct.pack('<I', 0)                           # vendorId=0, descriptorType=0
        dfd += struct.pack('<I', (88 << 16) | 2)             # descriptorBlockSize=88, versionNumber=2
        dfd += struct.pack('<I', (1 << 16) | (1 << 8) | 1)  # RGBSDA, BT709, LINEAR, flags=0
        dfd += struct.pack('<I', 0)                           # texelBlockDimensions
        dfd += bytes([8, 0, 0, 0, 0, 0, 0, 0])              # bytesPlane: plane0=8
        for bit_off, ch_id in [(0, 0), (16, 1), (32, 2), (48, 15)]:  # ch_id 15 = KHR alpha
            dfd += struct.pack('<H', bit_off)
            dfd += struct.pack('<B', 15)                      # bitLength = 16-1
            dfd += struct.pack('<B', ch_id | 0xC0)           # FLOAT|SIGNED, no extra flags
            dfd += bytes(4)                                   # samplePosition[4]
            dfd += struct.pack('<I', 0xBF800000)              # sampleLower: float32(-1.0)
            dfd += struct.pack('<I', 0x3F800000)              # sampleUpper: float32(+1.0)

        # 9. Pixel data (level N-1 first → level 0 last, per KTX2 spec)
        pixel_data = bytearray()
        for lvl in range(num_levels - 1, -1, -1):
            for face_mips in mip_chains:
                mip = face_mips[lvl]
                rgb16 = mip.astype(np.float16)
                alpha = np.full((*mip.shape[:2], 1), np.float16(1.0), dtype=np.float16)
                pixel_data += np.concatenate([rgb16, alpha], axis=-1).tobytes()

        # 10. Write file
        try:
            total_mb = (HEADER_END + pad_bytes + sum(level_byte_sizes)) / 1_048_576
            with open(ktx2_path, 'wb') as f:
                f.write(hdr_bytes)
                f.write(level_idx)
                f.write(dfd)
                f.write(bytes(pad_bytes))
                f.write(bytes(pixel_data))
            print(f"Saved {ktx2_path}  ({TILE}x{TILE} faces × 6, {num_levels} mip levels, "
                  f"{total_mb:.1f} MB, R16G16B16A16_SFLOAT TEXTURE_CUBE_MAP)")
        except Exception as e:
            print(f"Error: Could not write KTX2 file to {ktx2_path}: {e}")


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
        head, tail = os.path.split(inPath)
        return tail


    ################################################################################
    # get URLs for MaterialX and GLSL Files
    ################################################################################
    def getMaterialXDocURLs(self, matXExportPath, relativeDir, matXDocName, matXShader):
        urls = []
        isDataUri = cmds.optionVar( q='rkMtlx2Uri' )
        
        urls.append("meta://" + matXDocName + "#" + matXShader)
        
        return (isDataUri, urls)


    def getFragmentURLs(self, fragPath, relativeDir):
        urls = []
        isDataUri = cmds.optionVar( q='rkMtlx2Uri' )
        
        urls.append(fragPath)
        urls.append(relativeDir + fragPath)
        
        return (isDataUri, urls)

        
    def getVertexURLs(self, vertPath, relativeDir):
        urls = []
        isDataUri = cmds.optionVar( q='rkMtlx2Uri' )
        
        urls.append(vertPath)
        urls.append(relativeDir + vertPath)
        
        return (isDataUri, urls)
        

    ###########################################################################
    # Get an attribute from a MaterialX Graph Editor Node
    ###########################################################################
    def getMaterialXAttribute(self, materialXSurfaceShader, matXGraphEditorNode, matXAttr):
        attribute = None

        document = self.getMatrialXDocument(materialXSurfaceShader)
        if document:
            print(f"Found Doc: {document.nodeName()}")

            dhy = ufe.Hierarchy.hierarchy(document)
            sObject = None
            
            for shader in dhy.children():
                if matXGraphEditorNode == shader.nodeName():
                    sObject = shader
                    break
        
            if sObject:
                attrs     = ufe.Attributes.attributes(sObject)
                attribute = attrs.attribute(matXAttr)
                
        return attribute


    def getUFENode(self, materialXSurfaceShader, nodeName):
        ufeNode = None

        document = self.getMatrialXDocument(materialXSurfaceShader)
        if document:
            print(f"Found Doc: {document.nodeName()}")

            dhy = ufe.Hierarchy.hierarchy(document)
            sObject = None
            
            for shader in dhy.children():
                if nodeName == shader.nodeName():
                    ufeNode = shader
                    break

        x3dType = None
        if ufeNode:
            fileAttr = "filename"
            if "image" in ufeNode.nodeType():
                fileAttr = "fileName"
                if "tiledimage" in ufeNode.nodeType():
                    fileAttr = "file"

                attrs    = ufe.Attributes.attributes(ufeNode)
                fileName = self.getFileName(attrs.attribute(fileAttr).get())
                if ".mov" in fileName.lower() or ".mp4" in fileName.lower() or ".avi" in fileName.lower():
                    x3dType = "MovieTexture"
                else:
                    x3dType = "ImageTexture"
                
        return ufeNode, x3dType


    def getMatrialXDocument(self, materialXSurfaceShader):
        ufeNode = None

        matXStack = cmds.listConnections(materialXSurfaceShader + ".stack", shapes=True)[0]
        matXdPath = cmds.ls(matXStack, long=True)[0]
        
        ufePath = ufe.PathString.path(matXdPath)
        ufeItem = ufe.Hierarchy.createItem(ufePath)
        hy = ufe.Hierarchy.hierarchy(ufeItem)
        
        return hy.children()[0]
        

    ################################################################################
    # Get Skin Space Joint Inverse Bind Matrix
    ################################################################################
    def getJointInverseInSkinSpaceAsSFMatrix4f(self, jName, wssm=aom.MMatrix()):
        # Get the Dag paths for the joint and the Skin Space
        iList = aom.MSelectionList()
        iList.add(jName)
        
        sjsm = iList.getDagPath(0).inclusiveMatrix() * wssm
        
        # Get the MFloatMatrix for the joint. I feel that this will give us
        # the correct decimal rounding.
        imx = aom.MFloatMatrix(sjsm.inverse())
        
        return ( imx[0],  imx[1],  imx[2],  imx[3],
                 imx[4],  imx[5],  imx[6],  imx[7],
                 imx[8],  imx[9], imx[10], imx[11],
                imx[12], imx[13], imx[14], imx[15])


    ################################################################################
    # Get Skin Space Joint Inverse Bind Matrix - TODO
    ################################################################################
    def getJointInverseForHAnim(self, jName, wssm=aom.MMatrix()):
        # Get the Dag paths for the joint and the Skin Space
        iList = aom.MSelectionList()
        iList.add(jName)
        
        sjsm = iList.getDagPath(0).inclusiveMatrix() * wssm
        
        # Get the MFloatMatrix for the joint. I feel that this will give us
        # the correct decimal rounding.
        imx = aom.MFloatMatrix(sjsm.inverse())
        
        return ( imx[0],  imx[1],  imx[2],  imx[3],
                 imx[4],  imx[5],  imx[6],  imx[7],
                 imx[8],  imx[9], imx[10], imx[11],
                imx[12], imx[13], imx[14], imx[15])
