import sys
import maya.api.OpenMaya as maom
import maya.cmds         as mcmds
import maya.mel          as mmel
import ctypes            as ctp
import numpy             as np
import struct

import ufe
import MaterialX as mx
import MaterialX.PyMaterialXGenShader as mx_gen
import MaterialX.PyMaterialXGenGlsl as mx_glsl
import xml.etree.ElementTree as ET
import os
import re
import tempfile

from pathlib import Path

#advMat = 0
#    material.typeName == aiStandardSurface
#if   material.typeName == "standardSurface":
#    advMat = 1
#elif material.typeName == "openPBRSurface":
#    advMat = 2
#elif material.typeName == "usdPreviewSurface":
#    advMat = 3
#elif material.typeName == "StringrayPBS":
#    advMat = 4
#            |   aiStandardSurface  |    standardSurface    |    openPBRSurface     | usdPreviewSurface |    StingrayPBS     |
#tColorList = [           "baseColor",            "baseColor",            "baseColor",     "diffuseColor",     "TEX_color_map"]
#colorList  = [           "baseColor",            "baseColor",            "baseColor",     "diffuseColor",         "baseColor"]
#dRoughList = ["baseDiffuseRoughness", "baseDiffuseRoughness", "baseDiffuseRoughness",                 "",                  ""]

# This can also be done through a multiply node - see https://www.youtube.com/watch?v=Zy0dYnHMRPY
# for aiStandardSurface, standardSurface, and openPBRSurface, but not for usdPreviewSurface, and StringrayPBS

#tOcclList  = [          "baseWeight",           "baseWeight",           "baseWeight",        "occlusion",        "TEX_oa_map"]
#occlList   = [          "baseWeight",           "baseWeight",           "baseWeight",        "occlusion",                  ""]
#tEmisList  = [       "emissionColor",        "emissionColor",        "emissionColor",    "emissiveColor",  "TEX_emissive_map"]
#sEmisList  = [      "emissionWeight",       "emissionWeight",    "emissionLuminance",                 "", "emissiveIntensity"]
#emisList   = [       "emissionColor",        "emissionColor",        "emissionColor",    "emissiveColor",          "emissive"]
#tNormList  = [        "normalCamera",         "normalCamera",         "normalCamera",           "normal",    "TEX_normal_map"]
#tMetalList = [       "baseMetalness",        "baseMetalness",        "baseMetalness",         "metallic",  "TEX_metallic_map"]
#metalList  = [       "baseMetalness",        "baseMetalness",        "baseMetalness",         "metallic",          "metallic"]
#roughList  = [   "specularRoughness",    "specularRoughness",    "specularRoughness",        "roughness",         "roughness"]
#tRoughList = [   "specularRoughness",    "specularRoughness",    "specularRoughness",        "roughness", "TEX_roughness_map"]
#iorList    = [         "specularIOR",          "specularIOR",          "specularIOR",              "ior",                  ""]
#dispList   = ["transmissionDispersion", "transmissionDispersion", "transmissionDispersionAbbeNumber", "",                  ""]
#coatNoList = [          "coatNormal",           "coatNormal",   "geometryCoatNormal",                 "",                  ""]
#fuzzList   = [         "sheenWeight",          "sheenWeight",           "fuzzWeight",                 "",                  ""]
#fColList   = [          "sheenColor",           "sheenColor",            "fuzzColor",                 "",                  ""]
#fRouList   = [      "sheenRoughness",       "sheenRoughness",        "fuzzRoughness",                 "",                  ""]
#tWallList  = [          "thinWalled",           "thinWalled",   "geometryThinWalled",                 "",                  ""]

def searchForNodeByNameType(plug, nodeTypes):
    for nType in nodeTypes:
        dgIter = maom.MItDependencyGraph(plug, filter=maom.MFn.kInvalid, direction=maom.MItDependencyGraph.kUpstream, level=maom.MItDependencyGraph.kNodeLevel, traversal=maom.MItDependencyGraph.kDepthFirst)
        while not dgIter.isDone():
            cDepNode = maom.MFnDependencyNode(dgIter.currentNode())
            if cDepNode.typeName == nType:#"multiplyDivide" or cDepNode.typeName == "aiMultiply":
                return cDepNode
            dgIter.next()
    return None


#def searchForNodeByApiType(plug, apiTypes):
def searchForNodeByApiType(plug, apiType):
    #for apiType in apiTypes:
    print("The API One")
    dgIter = maom.MItDependencyGraph(plug, filter=apiType, direction=maom.MItDependencyGraph.kUpstream, level=maom.MItDependencyGraph.kNodeLevel, traversal=maom.MItDependencyGraph.kDepthFirst    )
    print("After the API One")
    while not dgIter.isDone():
        return maom.MFnDependencyNode(dgIter.currentNode())
        dgIter.next()
            
    return None


def getTextureTransform(textureObj):
    return searchForNodeByNameType(textureObj, ["place2dTexture"])


def connectTextureTransformToTexture(ttName, texName):
    print("B4 Connect: " + ttName + " to " + texName)
    connections = [
        (          'outUV', 'uvCoord'        ),
        ('outUvFilterSize', 'uvFilterSize'   ),
        (       'coverage', 'coverage'       ),
        ( 'translateFrame', 'translateFrame' ),
        (    'rotateFrame', 'rotateFrame'    ),
        (        'mirrorU', 'mirrorU'        ),
        (        'mirrorV', 'mirrorV'        ),
        (        'stagger', 'stagger'        ),
        (          'wrapU', 'wrapU'          ),
        (          'wrapV', 'wrapV'          ),
        (       'repeatUV', 'repeatUV'       ),
        (         'offset', 'offset'         ),
        (        'noiseUV', 'noiseUV'        ),
        (       'rotateUV', 'rotateUV'       ),
        (    'vertexUvOne', 'vertexUvOne'    ),
        (    'vertexUvTwo', 'vertexUvTwo'    ),
        (  'vertexUvThree', 'vertexUvThree'  ),
        ('vertexCameraOne', 'vertexCameraOne')
    ]
    print("AA Connect: " + ttName + " to " + texName)
    
    for ttAttr, flAttr in connections:
        mcmds.connectAttr(ttName + '.' + ttAttr, texName + '.' + flAttr, force=True)

# Assumes all images are the same size
'''
def generateMROImage(mroDict, rOption):
    if len(mroDict) == 0:
        return None
        
    channels  = []
    depths    = []
    pixPtrs   = []
    mroWidth  = 1
    mroHeight = 1
    mroDepth  = 4
    mroImage  = maom.MImage()
    hasAlpha  = False
    
    for key in mroDict:
        img = mroDict[key]
        mroWidth, mroHeight = img.getSize()
        pixPtrs.append(img.floatPixels())
        depths.append(img.depth())
        if key == "red":
            channels.append(0)
        elif key == "green":
            channels.append(1)
        elif key == "blue":
            channels.append(2)
        else:
            hasAlpha = True
            channels.append(3)

    pixNum = mroWidth * mroHeight
    newPix = maom.MFloatArray()
    newPix.setLength(pixNum * mroDepth)
    
    cLen = len(channels)
    for i in range(cLen):
        c = channels[i]
        d = 4#depths[i]
        p = pixPtrs[i]
        s = mroWidth * mroHeight * d
        
        pxl = ctp.cast(p, ctp.POINTER(ctp.c_float * s)).contents
        #bType = (ctp.c_float * s)
        #rBuffer = bType.from_address(p)
        #pxl = np.frombuffer(rBuffer, dtype=np.float32)
        #pxl = npArray.reshape((mroHeight, mroWidth, d))
        
        for j in range(pixNum):
            nIdx = (j * mroDepth) + c
            pIdx = (j * d) + c
            newPix[nIdx] = pxl[pIdx]
            
    if hasAlpha == False:
        for i in range(pixNum):
            nIdx = (i * mroDepth) + 3
            newPix[nIdx] = 1.0
    #pixel_buffer = struct.pack(f'{len(newPix)}f', *newPix)
    mroImage.create(mroWidth, mroHeight, mroDepth, maom.MImage.kFloat)
    #mroImage.setFloatPixels(pixel_buffer, mroWidth, mroHeight)
    mroImage.setFloatPixels(newPix, mroWidth, mroHeight)

    return mroImage
    '''

def generateMROImage(mroDict, rOption):
    """
    Swizzles multiple source images into a single MRO (Metalness/Roughness/Occlusion)
    image while maintaining memory stability in Maya.
    """
    if not mroDict:
        return None
        
    # 1. VALIDATION & ANCHORING
    # Anchor images to prevent Maya from freeing memory during pointer access
    src_images = list(mroDict.values())
    w, h = src_images[0].getSize()
    
    # Ensure all images are the same size
    for key, img in mroDict.items():
        if img.getSize() != (w, h):
            img.resize(w, h, False)
            #maom.MGlobal.displayError(f"MRO Error: '{key}' size mismatch. Expected {w}x{h}.")
            #return None

    # 2. BUFFER INITIALIZATION
    # Create an RGBA buffer (Height, Width, 4) initialized with Alpha = 1.0
    mro_buffer = np.zeros((h, w, 4), dtype=np.float32)
    mro_buffer[:, :, 3] = 1.0 

    channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}

    # 3. CHANNEL SWIZZLING
    for key, img in mroDict.items():
        if key not in channel_map:
            continue
            
        ptr = img.floatPixels() # Returns long (memory pointer)
        if ptr == 0:
            continue
            
        # depth() returns bytes; for float data, 4 bytes = 1 channel
        d = img.depth() // 4 
        float_count = w * h * d
        
        # Safely wrap the long pointer into a NumPy view
        raw_ptr = (ctp.c_float * float_count).from_address(ptr)
        src_np = np.frombuffer(raw_ptr, dtype=np.float32).reshape(h, w, d)
        
        # Extract the channel: use channel 0 for grayscale or specific index for RGBA
        src_ch = channel_map[key] if d == 4 else 0
        mro_buffer[:, :, channel_map[key]] = src_np[:, :, src_ch]

    # 4. RESOLVING TYPEERROR: Native Maya Array Handshake
    new_mro = maom.MImage()
    new_mro.create(w, h, 4, maom.MImage.kFloat) #
    
    # Flatten the NumPy buffer
    flat_data = mro_buffer.flatten()
    
    # Use MFloatArray to avoid: TypeError: string or unicode object... expected
    # This is the stable bridge between Python and Maya's C++ core
    pixel_array = maom.MFloatArray(flat_data.tolist())
    
    # Final assignment
    new_mro.setFloatPixels(pixel_array, w, h) #

    return new_mro
    
    
#def generateMRO_TheMayaWay(texDict, red_path, green_path, blue_path, res=(2048, 2048)):
def generateMRO_TheMayaWay(texDict, wh=(2048, 2048)):
    res = list(wh)
    # 1. Create a PlusMinusAverage node to hold our specific channels
    # This node is pure math and won't "blend" or "pre-multiply" your data
    combiner = mcmds.shadingNode('plusMinusAverage', asTexture=True, name='MRO_Combiner')
    
    # We use three file nodes
    #inputs = [
    #    (red_path, '.outColorR', '.input3D[0].input3Dx'), # Red Path -> R channel -> X slot
    #    (green_path, '.outColorG', '.input3D[0].input3Dy'), # Green Path -> G channel -> Y slot
    #    (blue_path, '.outColorB', '.input3D[0].input3Dz')  # Blue Path -> B channel -> Z slot
    #]
    
    #file_nodes = []
    #for path, out_attr, in_attr in inputs:
    #    f_node = mcmds.shadingNode('file', asTexture=True)
    #    mcmds.setAttr(f_node + '.fileTextureName', path, type='string')
    #    file_nodes.append(f_node)
        
    #    # Connect ONLY the specific channel we want to its specific slot
    #    mcmds.connectAttr(f_node + out_attr, combiner + in_attr)
    
    usingArgForSize = True
    for key in texDict:
        texture = texDict[key]
        tName   = texture.name()
        try:
            width  = mcmds.getAttr(tName + ".outSizeX")
            height = mcmds.getAttr(tName + ".outSizeY")
            if usingArgForSize == True:
                res[0] = width
                res[1] = height
                usingArgForSize = False
            else:
                if width > res[0]:
                    res[0] = width
                if height > res[1]:
                    res[1] = height
        except:
            print(tName + " is not a File Texture")
            
        mcmds.connectAttr(tName + '.outColor' + key[0], combiner + '.input3D[0].input3D' + key[1])

    # 1. Force the node to evaluate its output attribute
    # This 'wakes up' the plusMinusAverage node so there is data to read
    mcmds.getAttr(combiner + ".output3D")

    # 2. Extract the combined result
    mro_image = maom.MImage()
    sel = maom.MSelectionList()
    sel.add(combiner)
    mro_obj = sel.getDependNode(0)
    
    # This triggers Maya to calculate that 3D input as a single color/image
    mro_image.readFromTextureNode(mro_obj, maom.MImage.kFloat)
    
    # 3. Cleanup
    #mcmds.delete(combiner, *file_nodes)
    mcmds.delete(combiner)
    
    mro_image.resize(res[0], res[1], False)
    mro_image.verticalFlip()
    
    return mro_image


def generateMRO_Stable(texDict, wh=(2048, 2048)):
    """
    Swizzles multiple textures into a single MRO (Metallic, Roughness, Occlusion) map.
    Uses direct bytearray manipulation to avoid non-existent MImage methods.
    """
    res = list(wh)

    # Determine resolution based on input textures
    usingArgForSize = True
    for key in texDict:
        texture = texDict[key]
        tName = texture.name()
        try:
            width = int(mcmds.getAttr(tName + ".outSizeX"))
            height = int(mcmds.getAttr(tName + ".outSizeY"))
            if usingArgForSize:
                res[0], res[1] = width, height
                usingArgForSize = False
            else:
                res[0] = max(res[0], width)
                res[1] = max(res[1], height)
        except Exception:
            print(f"{tName} resolution query failed. Using default {wh}")

    # 1. Create a blank RGBA buffer
    # Every 4 bytes represents [R, G, B, A]
    total_pixels = res[0] * res[1]
    mro_buffer = bytearray([0, 0, 0, 255] * total_pixels)

    # Mapping keys to byte offsets (RGBA)
    # red=0, green=1, blue=2
    channel_offsets = {"red": 0, "green": 1, "blue": 2}

    for key, texture in texDict.items():
        tName = texture.name()
        target_offset = channel_offsets.get(key.lower())
        
        if target_offset is None:
            continue
            
        temp_img = maom.MImage()
        try:
            # Load and resize source image
            path = mcmds.getAttr(tName + ".fileTextureName")
            temp_img.readFromFile(path)
            temp_img.resize(res[0], res[1])
            
            # Access raw pixels via pointer
            # Convert to bytearray for index-based access in Python
            pixel_ptr = temp_img.pixels()
            source_bytes = bytearray(pixel_ptr)
            
            # Swizzle: Extract the Red channel (Index 0) from the source
            # and inject it into our target_offset slot in the master buffer
            for i in range(total_pixels):
                # source_bytes is [R, G, B, A, R, G, B, A...]
                # We assume the data we want is in the R channel (index 0)
                val = source_bytes[i * 4]
                mro_buffer[i * 4 + target_offset] = val
                
        except Exception as e:
            print(f"Failed to process {tName}: {e}")

    # 2. Finalize MImage
    final_mro = maom.MImage()
    # create(width, height, channels, type)
    final_mro.create(res[0], res[1], 4)
    # setPixels(unsigned char*, width, height)
    final_mro.setPixels(mro_buffer, res[0], res[1])
    
    # Correct the orientation for Maya's UV space
    final_mro.verticalFlip()

    return final_mro
  

#########################################################################
# Functions to write the MaterialX XML Document to disk and return the 
# file path by gathering information from the MaterialXSurfaceShader node
#
# matX : MaterialXSurfaceShader
#########################################################################
def resolve_mtlx_path(match, base_dir):
    """Callback to turn relative values into absolute ones."""
    attr_type  = match.group(1)
    path_value = match.group(2)
    
    if attr_type == "filename":
        if not os.path.isabs(path_value):
            # Resolve to absolute and swap backslashes for forward slashes
            full_path = os.path.join(base_dir, path_value)
            long_path = str(Path(full_path).resolve())
            
            return 'type="filename" value="' + long_path.replace("\\", "/") + '"'
    
    return match.group(0)


def makeFilePathsAbsolute(tempPath):
    baseDir = os.path.dirname(tempPath)

    with open(tempPath, 'r') as f:
        content = f.read()

    pattern = r'type="([^"]+)"\s+value="([^"]+)"'
    
    # Use a lambda to pass the base_dir context to the standalone function
    clean_content = re.sub(
        pattern, 
        lambda m: resolve_mtlx_path(m, baseDir), 
        content
    )

    with open(tempPath, 'w') as f:
        f.write(clean_content)


def saveMaterialXDataToFile(matXName):
    matXStack = mcmds.listConnections(matXName + ".stack", shapes=True)[0]
    matXdPath = mcmds.ls(matXStack, long=True)[0]
    
    stackPathString = ufe.PathString.path(matXdPath)
    stackItem       = ufe.Hierarchy.createItem(stackPathString)
    
    stackHierarchy  = ufe.Hierarchy.hierarchy(stackItem)
    children        = stackHierarchy.children()
    
    if children:
        docItem     = children[0]
        contextOps  = ufe.ContextOps.contextOps(docItem)

        tempPath    = os.path.join(tempfile.gettempdir(), "temp_lookdevx.mtlx").replace("\\", "/")
        baseDir     = os.path.dirname(tempPath)
        fullPath    = os.path.join(baseDir, "temp_lookdevx.mtlx")
        long_path   = str(Path(fullPath).resolve())
        tempPath    = long_path.replace("\\", "/")
        contextOps.doOp(['MxExportDocument', tempPath])
        
        makeFilePathsAbsolute(tempPath)

        return tempPath
        
    else:
        return ""                                               #
                                                                #
#################################################################


def applyExportSettingsToMaterialXDataFile(matXFilePath, reldir):
    # 1. Parse the MaterialX (XML) file
    tree = ET.parse(matXFilePath)
    root = tree.getroot()

    # 2. Iterate through every element in the file
    for elem in root.iter():
        # MaterialX typically stores paths in 'value' or 'file' attributes
        # depending on the node type (e.g., <input name="file" value="path/to/tex.png">)
        if 'value' in elem.attrib:
            original_value = elem.attrib['value']
            
            # Check if the value looks like a file path (has an extension)
            if "." in original_value and "/" in original_value or "\\" in original_value:
                filename      = os.path.basename(original_value)
                tReldir       = reldir.replace("\\", "/")
                new_full_path = "../" + tReldir + filename
                
                elem.set('value', new_full_path)
                print(f"Updated: {filename} -> {new_full_path}")

    # 3. Write the modified XML back to disk
    tree.write(matXFilePath, encoding="utf-8", xml_declaration=True)


def saveGLSLFiles(glslFragPath, glslVertPath, matXFilePath):
    # Setup Library Loads
    doc = mx.createDocument()
    sPath = mx.FileSearchPath()
    sPath.append(os.path.dirname(matXFilePath))

    bPath = mx.getDefaultDataSearchPath()
    sPath.append(bPath)

    libFolders = ['libraries', 'libraries/stdlib', 'libraries/pbrlib']

    for subfolder in libFolders:
        libDoc = mx.createDocument()
        mx.loadLibraries([subfolder], sPath.asString(), libDoc)
        doc.importLibrary(libDoc)
        
    mx.readFromXmlFile(doc, matFile, sPath.asString())

    materials = [n for n in doc.getNodes() if n.getCategory() == 'surfacematerial']

    if materials:
        gen = mx_glsl.GlslShaderGenerator.create()
        context = mx_gen.GenContext(gen)
        
        context.registerSourceCodeSearchPath(sPath)
        
        options = context.getOptions()
        options.shaderInterfaceType = mx_gen.SHADER_INTERFACE_COMPLETE
        
        shaderName = getattr(materials[0], 'name', 'shader')
        safeName   = mx.createValidName(shaderName)
        
        shader = gen.generate(safeName, materials[0], context)
        
        v_stage = getattr(mx_gen, 'VERTEX_STAGE', 'vertex')
        with open(glslVertPath, "w") as vfile:
            vfile.write(shader.getSourceCode(v_stage))
        
        p_stage = getattr(mx_gen, 'PIXEL_STAGE', 'pixel')
        with open(glslFragPath, "w") as ffile:
            ffile.write(shader.getSourceCode(p_stage))


def getDefaultValue(glslType):
    defaults = {
        'float': '0.0', 'int': '0', 'bool': 'true',
        'vec2': '0 0', 'vec3': '0 0 0', 'vec4': '0 0 0 0',
        'mat3': '1 0 0 0 1 0 0 0 1',
        'mat4': '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1',
        'sampler2D': '', 'samplerCube': ''
    }
    return defaults.get(glslType, "")

#def extract_x3d_fields(file_path):
def getShaderFieldTags(fTags, filePaths):

    typeMap = {
        'float': 'SFFloat', 'int': 'SFInt32', 'bool': 'SFBool',
        'vec2': 'SFVec2f', 'vec3': 'SFVec3f', 'vec4': 'SFVec4f',
        'mat3': 'SFMatrix3f', 'mat4': 'SFMatrix4f',
        'sampler2D': 'SFNode', 'samplerCube': 'SFNode'
    }

    # Regex captures type and the entire name string (including commas/arrays)
    uniformPattern = re.compile(r'uniform\s+(?:(?:lowp|mediump|highp)\s+)?(\w+)\s+([^;]+);')

    for path in filePaths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    match = uniformPattern.search(line)
                    if match:
                        glslType, namesRaw = match.groups()
                        if glslType in typeMap:
                            names = [n.strip() for n in namesRaw.split(',')]
                            for name in names:
                                # Strip array brackets if present: lightPos[4] -> lightPos
                                fieldName = re.sub(r'\[.*?\]', '', name)
                                
                                x3dType = type_map[glslType]
                                defaultVal = getDefaultValue(glslType)
                                
                                #valAttr = f' value="{defaultVal}"' if defaultVal else ""
                                valAttr = defaultVal
                                #fields.append(f'<field name="{fieldName}" type="{x3dType}" accessType="inputOutput"{valAttr}/>')
                                
                                hasTag = fTags.get(fieldName, None)
                                if not hasTag:
                                    fTags[fieldName] = (x3dType, valAttr)


def getUnknownBaseColorAndOcclusionTextures(material, colorStore, colorAttr):
    # Color Plug
    colorConn = material.findPlug(colorAttr, True)
    
    # Search for multiply node
    # Get baseTexture and occlusionTexture
    multiply = searchForNodeByNameType(colorConn, ["multiplyDivide", "aiMultiply"])
    if multiply:
        inputConn1   = multiply.findPlug("input1", True)
        colorTexture = searchForNodeByApiType(inputConn1, maom.MFn.kTexture2d)
        if colorTexture:
            colorStore["baseTexture"] = colorTexture
        
        inputConn2   = multiply.findPlug("input2", True)
        occlTexture  = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
        if occlTexture:
            colorStore["occlusionTexture"] = occlTexture
        else:
            inputConn2 = multiply.findPlug("input2R", True)
            occlTexture2R = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
            if occlTexture2R:
                colorStore["occlusionTexture"] = occlTexture2R
    else:
        aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
        if aiImage:
            colorStore["baseTexture"] = aiImage
            multiConn = aiImage.findPlug("multiply", True)
            occlTexture  = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
            if occlTexture:
                colorStore["occlusionTexture"] = occlTexture
            else:
                multiConn = aiImage.findPlug("multiplyR", True)
                occlTexture2R = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                if occlTexture2R:
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            colorTexture = searchForNodeByApiType(colorConn, maom.MFn.kTexture2d)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            occlTexture  = searchForNodeByApiType(baseConn, maom.MFn.kTexture2d)
            if occlTexture:
                colorTex["occlusionTexture"] = occlTexture


def getLegacyBaseColorAndOcclusionTextures(material, colorStore):
    hasOcclTexture = False
    
    # Color Plug
    colorConn = None
    try:
        colorConn = material.findPlug("KdColor", True)
    except:
        colorConn = material.findPlug("color", True)

    if colorConn:
        multiply = searchForNodeByNameType(colorConn, ["multiplyDivide", "aiMultiply"])
        if multiply:
            inputConn1   = multiply.findPlug("input1", True)
            colorTexture = searchForNodeByApiType(inputConn1, maom.MFn.kTexture2d)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            inputConn2   = multiply.findPlug("input2", True)
            occlTexture  = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
            if occlTexture:
                hasOcclTexture = True
                colorStore["occlusionTexture"] = occlTexture
            else:
                plugName = "input2R"
                if multiply.typeName == "multiplyDivide":
                    plugName = "input2X"
                    
                inputConn2 = multiply.findPlug(plugName, True)
                occlTexture2R = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
                if occlTexture2R:
                    hasOcclTexture = True
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
            if aiImage:
                colorStore["baseTexture"] = aiImage
                multiConn = aiImage.findPlug("multiply", True)
                occlTexture  = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                if occlTexture:
                    hasOcclTexture = True
                    colorStore["occlusionTexture"] = occlTexture
                else:
                    multiConn = aiImage.findPlug("multiplyR", True)
                    occlTexture2R = searchForNodeByApiType(multiConn.asMObject(), maom.MFn.kTexture2d)
                    if occlTexture2R:
                        hasOcclTexture = True
                        colorStore["occlusionTexture"] = occlTexture2R
            else:
                colorTexture = searchForNodeByApiType(colorConn, maom.MFn.kTexture2d)
                if colorTexture:
                    colorStore["baseTexture"] = colorTexture


def getAdvBaseColorAndOcclusionTextures(material, colorStore, advMat):
    if advMat < 3:
        # Color Plugs
        colorConn = material.findPlug("baseColor", True)
        baseAttr  = "baseWeight"
        
        bwExists  = False
        bwExists  = mcmds.objExists(material.name() + ".baseWeight")
        if bwExists == False:
            baseAttr = "base"
        
        baseConn  = material.findPlug(baseAttr, True)

        # Search for multiply node
        # Get baseTexture and occlusionTexture
        multiply = searchForNodeByNameType(colorConn, ["multiplyDivide", "aiMultiply"])
        if multiply:
            inputConn1   = multiply.findPlug("input1", True)
            colorTexture = searchForNodeByApiType(inputConn1, maom.MFn.kTexture2d)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            inputConn2   = multiply.findPlug("input2", True)
            occlTexture  = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
            if occlTexture:
                colorStore["occlusionTexture"] = occlTexture
            else:
                inputConn2 = multiply.findPlug("input2R", True)
                occlTexture2R = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
                if occlTexture2R:
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
            if aiImage:
                colorStore["baseTexture"] = aiImage
                multiConn = aiImage.findPlug("multiply", True)
                occlTexture  = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                if occlTexture:
                    colorStore["occlusionTexture"] = occlTexture
                else:
                    multiConn = aiImage.findPlug("multiplyR", True)
                    occlTexture2R = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                    if occlTexture2R:
                        colorStore["occlusionTexture"] = occlTexture2R
            else:
                colorTexture = searchForNodeByApiType(colorConn, maom.MFn.kTexture2d)
                if colorTexture:
                    colorStore["baseTexture"] = colorTexture
                
                #occlTexture  = searchForNodeByApiType(baseConn, maom.MFn.kTexture2d)
                #if occlTexture:
                #    colorTex["occlusionTexture"] = occlTexture
                
    elif advMat == 3:
        dColorConn = material.findPlug("diffuseColor", True)
        colorTexture = searchForNodeByApiType(dColorConn, maom.MFn.kTexture2d)
        if colorTexture:
            colorStore  ["baseTexture" ] = colorTexture
        
        occlConn    = material.findPlug("occlusion", True)
        occlTexture = searchForNodeByApiType(occlConn, maom.MFn.kTexture2d)
        if occlTexture:
            colorStore  ["occlussionTexture"] = occlTexture
            
    elif advMat == 4:
        tColorConn = material.findPlug("TEX_color_map", True)
        tOcclConn  = material.findPlug("TEX_ao_map",    True)

        colorTexture = searchForNodeByApiType(tColorConn, maom.MFn.kTexture2d)
        if colorTexture:
            colorStore  ["baseTexture"  ] = colorTexture
        
        occlTexture = searchForNodeByApiType(tOcclConn, maom.MFn.kTexture2d)
        if occlTexture:
            colorStore  ["occlussionTexture"] = occlTexture

