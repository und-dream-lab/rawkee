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

textTypes = ["file", "movie", "envChrome", "envCube", "envBall", "envSphere"]


type_map = {
    "float": "SFFloat", "integer": "SFInt32", "bool": "SFBool",
    "vector2": "SFVec2f", "vector3": "SFVec3f", "vector4": "SFVec4f", "string": "SFString",
    "color3": "SFColor", "color4": "SFColorRGBA", "matrix33": "SFMatrix3f", "matrix44": "SFMatrix4f",
    "filename": "SFNode", "sampler2D": "SFNode", "sampler3D": "SFNode", "samplerCube": "SFNode"
}

alphaModes = {0:"OPAQUE", 1:"MASK", 2:"BLEND"}


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


def getAlphaMode(index):
    return alphaModes.get(index, "AUTO")


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
#
def makeImagePathsRelative(matXDocPath, imagePath):
    pattern  = r'value="([^"]+)"'
    
    # 1. Read all lines from the file
    with open(filename, 'r') as f:
        lines = f.readlines()

    # 2. Alter the lines in memory
    altered_lines = []
    for line in lines:
        # Example alteration: replace a specific word in each line
        altered_lines.append(line)
        if 'type="filename"' in line:
            ovMatch = re.search(pattern, line)
            if ovMatch:
                oldPath = ovMatch.group(1)
                head, tail = os.path.split(oldPath)
                newPath = imagePath + tail
                result = re.sub(pattern, 'value="' + newPath + '"', line)
                altered_lines.append(result)
            else:
                altered_lines.append(line)
        else:
            altered_lines.append(line)

    # 3. Write the altered content back to the same file, which overwrites it
    with open(filename, 'w') as f:
        f.writelines(altered_lines)


def getMatXSurfaceInfo(matXShaderName):
    matXSurfacePath = cmds.getAttr(maXShaderName + ".ufePath")
    surfacePathString = ufe.PathString.path(matXSurfacePath)
    surfItem = ufe.Hierarchy.createItem(surfacePathString)

    return surfItem, surfacePathString

def getMatXSurfaceAttr(surfaceItem):
    attr_handler = ufe.Attributes.attributes(surfaceItem)
    surfAttr = attr_handler.attribute("surfaceshader")
    
    return surfAttr


def getUFEAttribute(matXItem, attrName, asSource=False, connected=False):
    if connected == True:
        itemPath = matXItem.path()
        cHandler = ufe.RunTimeMgr.instance().connectionHandler(itemPath.runTimeId())
        conns    = cHandler.sourceConnections(matXItem).allConnections()
        for conn in conns:
            if asSource == True:
                srcName = "outputs:" + attrName
                if itemPath == conn.src.path and srcName == conn.src.name:
                    return conn
            else:
                dstName = "inputs:" + attrName
                if itemPath == conn.dst.path and dstName == conn.dst.name:
                    return conn
                    
        return None

    else:
        attrHandler = ufe.Attributes.attributes(matXItem)
        itemAttr = attrHandler.attribute(attrName)

    return None


def getUFEConnectedTexture(matXItem, attrName):
    connection = getUFEAttribute(matXItem, attrName, connected=True)
    ufeItem = ufe.Hierarchy.createItem(connection.src.path)
    
    if "image" in ufeItem.nodeType().lower():
        return ufeItem

    return None

def getMatXAttribute(matXItem, attrName, grasp=False):
    itemAttr = None
    
    attrHandler = ufe.Attributes.attributes(matXItem)
    try:
        itemAttr = attrHandler.attribute(attrName)
    except:
        if grasp == True:
            for name in attrHandler.attributeNames:
                if attrName in name:
                    return attrHandler.attribute(name)
    
    return itemAttr


def getMatXCompoundItem(surfItem, surfPath, surfAttr):
    cHandler = ufe.RunTimeMgr.instance().connectionHandler(surfPath.runTimeId())
    conns = cHandler.sourceConnections(surfItem).allConnections()

    sCompound = None
    for conn in conns:
        if "inputs:surfaceshader" == conn.dst.name:
            print(conn.src.path)
            sCompound = ufe.Hierarchy.createItem(conn.src.path)

    if sCompound:
        #cmpAttrs = ufe.Attributes.attributes(sCompound)
        #if cmpAttrs:
        #    for name in cmpAttrs.attributeNames:
        #        print(name)
        return sCompound
        
    else:
        return None


def getX3DFieldsAndGLSLInjectionDefinitions(surfComp):
    hier = ufe.Hierarchy.hierarchy(surfComp)
    children = hier.children()
    
    defines   = {}
    x3dFields = {}
    if children:
        for child in children:
            cHandler = ufe.RunTimeMgr.instance().connectionHandler(child.path().runTimeId())
            cConns = cHandler.sourceConnections(child).allConnections()
    
            for cConn in cConns:
                if str(cConn.src.path) == str(scPath):
                    dstName = cConn.dst.name.removeprefix("inputs:")
                    srcName = cConn.src.name.removeprefix("inputs:")
                    dstCompare = child.nodeName() + "_" + dstName

                    x3dFields[srcName] = dstCompare
                    if dstCompare != srcName:
                        defines[srcName] = dstCompare

    return defines, x3dFields
    
    
def getX3DShaderFieldNames(mayaMatXSSName):
    surfItem = None
    surfPath = None
    surfAttr = None
    
    surfItem, surfPath = getMatXSurfaceItem(mayaMatXSSName)
    if surfItem:
        surfAttr = getMatXSurfaceAttr(surfItem)
    else:
        return None
    
    if surfAttr:
        surfComp = getMatXCompoundItem(surfItem, surfPath, surfComp)
    else:
        return None
        
    if surfComp:
        defines, x3dFields = getX3DFieldsAndGLSLInjectionDefinitions(surfComp)
        return defines, x3dFields, surfComp
    else:
        return None


def saveMaterialXDocuments(activePrj, matXPath, imagePath):
    matXDocs = []
    localPath = activePrj + "/" + matXPath
    
    matXSS = cmds.ls(type='materialXStackShape')
    
    if matXSS:
        for mxss in matXSS:
            matXdPath       = mcmds.ls(mass, long=True)[0]
            stackPathString = ufe.PathString.path(matXdPath)
            stackItem       = ufe.Hierarchy.createItem(stackPathString)
            
            stackHierarchy  = ufe.Hierarchy.hierarchy(stackItem)
            children        = stackHierarchy.children()
            
            if children:
                for child in children:
                    docItem     = child
                    contextOps  = ufe.ContextOps.contextOps(docItem)
                    
                    document    = docItem.path().back()

                    tempPath    = os.path.join(localPath, document + ".mtlx").replace("\\", "/")
                    #baseDir     = os.path.dirname(tempPath)
                    #fullPath    = os.path.join(baseDir, "temp_lookdevx.mtlx")
                    #long_path   = str(Path(fullPath).resolve())
                    #tempPath    = long_path.replace("\\", "/")
                    contextOps.doOp(['MxExportDocument', tempPath])
                    
                    makeImagePathsRelative(tempPath, imagePath)
                    
                    docDict = {}
                    docDict["name"]    = document
                    docDict["content"] = "./" + matXPath + document + ".mtlx"
                    matXDoc.append(docDict)
    
    return matXDocs


def saveGLSLFiles(glslFragPath, glslVertPath, matXFilePaths, ufeShaderPath, defines, x3dFields):
    #|materialXStack1|materialXStackShape1,%dHelmetMatXDoc%DamagedHelmetShader
    x3dFieldTypes = {}
    pathChop      = ufeShaderPath.split('%')
    matXDocName   = pathChop[1]
    searchDocFile = matXDocName + ".mtlx"
    matXShader    = pathChop[2]
    
    # Setup Library Loads
    doc = mx.createDocument()
    sPath = mx.FileSearchPath()
    
    for fPath in matXFilePaths:
        if search in fPath:
            sPath.append(fPath)
            break

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
        
        for material in materials:
            shaderName = getattr(material, 'name', 'shader')
            if shaderName == matXShader:
                safeName   = mx.createValidName(shaderName)
                
                shader = gen.generate(safeName, material, context)
                
                # Write out GLSL VERTEX file
                v_stage = getattr(mx_gen, 'VERTEX_STAGE', 'vertex')
                vText   = shader.getSourceCode(v_stage)
                vpubuni = shader.getStage('vertex').getUniformBlock('PublicUniforms')
                for key, value in defines:
                    for port in vpubuni:
                        if value == port.getName():
                            inject = "#define " + key + " " + value + "\n"
                            vText  = inject + vText
                            break
                        
                with open(glslVertPath, "w") as vfile:
                    vfile.write(vText)
                
                # Write out GLSL FRAGMENT (pixel) file
                p_stage = getattr(mx_gen, 'PIXEL_STAGE', 'pixel')
                pText   = shader.getSourceCode(p_stage)
                ppubuni = shader.getStage('pixel').getUniformBlock('PublicUniforms')
                for key, value in defines:
                    for port in ppubuni:
                        if value == port.getName():
                            inject = "#define " + key + " " + value + "\n"
                            pText  = inject + pText
                            break
                            
                with open(glslFragPath, "w") as pfile:
                    pfile.write(pText)

                # Gather 3D Field Types from
                for key, value in x3dFields:
                    for port in vpubuni:
                        if value == port.getName():
                            x3dFieldTypes[key] = type_map.get(port.getType().getName(), "SFNode")
                            break

                for key, value in x3dFields:
                    for port in ppubuni:
                        if value == port.getName():
                            x3dFieldTypes[key] = type_map.get(port.getType().getName(), "SFNode")
                            break
                            
                return x3dFieldTypes, matXDocName, matXShader
        return None
    return None
                            
                            
def getUFETextureNode(surfComp, nodeName):
    chy      = ufe.Hierarchy.hierarchy(surfComp)
    children = chy.children()
    for child in children:
        if child.nodeName() == nodeName:
            return child
    
    return None

# TODO
def getMayaPlace2dFromUFETexture(textureItem):
    mayaPlace2d = None
    
    return mayaPlace2d
    
    
#def extract_x3d_fields(file_path):
def getShaderFieldTags(fTags, x3dFields, x3dFileTypes, surfComp):
    for key, value in x3dFields:
        childNode = x3dFields[key]
        cParts = childNode.split("_")
        cpLen = len(cParts)
        if cpLen > 1:
            childNode = childNode.removesuffix("_" + cParts[cpLen-1])

        fName  = key
        fType  = x3dFieldValues[key]
        faType = "inputOutput"
        fValue = ""

        attrs = ufe.Attributes.attributes(surfComp)
        attribute = attrs.attribute(key)
        fVal  = attribute.get()
        if   fType == "SFNode":
            fValue = childNode + "," + fVal
        elif fType == "SFString":
            fValue = fVal
        elif fType == "SFBool":
            if fVal == True:
                fValue = "true"
            else:
                fValue = "false"
        elif fType == "SFFloat":
            try:
                fValue = str(fVal)
            except:
                fValue = "0.0"
        elif fType == "SFVec2f":
            try:
                fValue = str(fVal[0]) + " " + str(fVal[1])
            except:
                fValue = "0.0 0.0"
        elif fType == "SFVec3f":
            try:
                fValue = str(fVal[0]) + " " + str(fVal[1]) + " " + str(fVal[2])
            except:
                fValue = "0.0 0.0 0.0"
        elif fType == "SFVec4f":
            try:
                fValue = str(fVal[0]) + " " + str(fVal[1]) + " " + str(fVal[2]) + " " + str(fVal[3])
            except:
                fValue = "0.0 0.0 0.0 0.0"
        elif fType == "SFInt32":
            try:
                fValue = str(int(fVal))
            except:
                fValue = "0"
        elif fType == "SFColor":
            try:
                fValue = str(fVal[0]) + " " + str(fVal[1]) + " " + str(fVal[2])
            except:
                fValue = "1.0 1.0 1.0"
        elif fType == "SFColorRGBA":
            try:
                fValue = str(fVal[0]) + " " + str(fVal[1]) + " " + str(fVal[2]) + " " + str(fVal[3])
            except:
                fValue = "1.0 1.0 1.0 1.0"
        elif fType == "SFMatrix3f":
            try:
                fValue =                str(value.matrix[0][0]) + " " + str(value.matrix[0][1]) + " " + str(value.matrix[0][2])
                fValue = fValue + " " + str(value.matrix[1][0]) + " " + str(value.matrix[1][1]) + " " + str(value.matrix[1][2])
                fValue = fValue + " " + str(value.matrix[2][0]) + " " + str(value.matrix[2][1]) + " " + str(value.matrix[2][2])
            except:
                fValue = "1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0"
        elif fType == "SFMatrix3f":
            try:
                fValue =                str(value.matrix[0][0]) + " " + str(value.matrix[0][1]) + " " + str(value.matrix[0][2]) + " " + str(value.matrix[0][3])
                fValue = fValue + " " + str(value.matrix[1][0]) + " " + str(value.matrix[1][1]) + " " + str(value.matrix[1][2]) + " " + str(value.matrix[1][3])
                fValue = fValue + " " + str(value.matrix[2][0]) + " " + str(value.matrix[2][1]) + " " + str(value.matrix[2][2]) + " " + str(value.matrix[2][3])
                fValue = fValue + " " + str(value.matrix[3][0]) + " " + str(value.matrix[3][1]) + " " + str(value.matrix[3][2]) + " " + str(value.matrix[3][3])
            except:
                fValue = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"
        
        fTags[key] = fType + "," + faType + "," + fValue


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
            #colorTexture = searchForNodeByApiType(inputConn1, maom.MFn.kTexture2d)
            colorTexture = searchForNodeByNameType(inputConn1, textTypes)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            inputConn2   = multiply.findPlug("input2", True)
            #occlTexture  = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
            occlTexture  = searchForNodeByNameType(inputConn2, textTypes)
            if occlTexture:
                hasOcclTexture = True
                colorStore["occlusionTexture"] = occlTexture
            else:
                plugName = "input2R"
                if multiply.typeName == "multiplyDivide":
                    plugName = "input2X"
                    
                inputConn2 = multiply.findPlug(plugName, True)
                #occlTexture2R = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
                occlTexture2R = searchForNodeByNameType(inputConn2, textTypes)
                if occlTexture2R:
                    hasOcclTexture = True
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
            if aiImage:
                colorStore["baseTexture"] = aiImage
                multiConn = aiImage.findPlug("multiply", True)
                #occlTexture  = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                occlTexture  = searchForNodeByNameType(multiConn, textTypes)
                if occlTexture:
                    hasOcclTexture = True
                    colorStore["occlusionTexture"] = occlTexture
                else:
                    multiConn = aiImage.findPlug("multiplyR", True)
                    #occlTexture2R = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                    occlTexture2R = searchForNodeByNameType(multiConn, textTypes)
                    if occlTexture2R:
                        hasOcclTexture = True
                        colorStore["occlusionTexture"] = occlTexture2R
            else:
                #colorTexture = searchForNodeByApiType(colorConn, maom.MFn.kTexture2d)
                colorTexture = searchForNodeByNameType(colorConn, textTypes)
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
            #colorTexture = searchForNodeByApiType(inputConn1, maom.MFn.kTexture2d)
            colorTexture = searchForNodeByNameType(inputConn1, textTypes)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            inputConn2   = multiply.findPlug("input2", True)
            #occlTexture  = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
            occlTexture  = searchForNodeByNameType(inputConn2, textTypes)
            if occlTexture:
                colorStore["occlusionTexture"] = occlTexture
            else:
                inputConn2 = multiply.findPlug("input2R", True)
                #occlTexture2R = searchForNodeByApiType(inputConn2, maom.MFn.kTexture2d)
                occlTexture2R = searchForNodeByNameType(inputConn2, textTypes)
                if occlTexture2R:
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
            if aiImage:
                colorStore["baseTexture"] = aiImage
                multiConn = aiImage.findPlug("multiply", True)
                #occlTexture  = searchForNodeByApiType(multiConn, maom.MFn.kTexture2d)
                occlTexture  = searchForNodeByNameType(multiConn, textTypes)
                if occlTexture:
                    colorStore["occlusionTexture"] = occlTexture
                else:
                    multiConn = aiImage.findPlug("multiplyR", True)
                    occlTexture2R = searchForNodeByNameType(multiConn, textTypes)
                    if occlTexture2R:
                        colorStore["occlusionTexture"] = occlTexture2R
            else:
                #colorTexture = searchForNodeByApiType(colorConn, maom.MFn.kTexture2d)
                colorTexture = searchForNodeByNameType(colorConn, textTypes)
                
                if colorTexture:
                    colorStore["baseTexture"] = colorTexture
                
                #occlTexture  = searchForNodeByApiType(baseConn, maom.MFn.kTexture2d)
                #if occlTexture:
                #    colorTex["occlusionTexture"] = occlTexture
                
    elif advMat == 3:
        dColorConn = material.findPlug("diffuseColor", True)
        #colorTexture = searchForNodeByApiType(dColorConn, maom.MFn.kTexture2d)
        colorTexture = searchForNodeByNameType(dColorConn, textTypes)
        if colorTexture:
            colorStore  ["baseTexture" ] = colorTexture
        
        occlConn    = material.findPlug("occlusion", True)
        #occlTexture = searchForNodeByApiType(occlConn, maom.MFn.kTexture2d)
        occlTexture = searchForNodeByNameType(occlConn, textTypes)
        if occlTexture:
            colorStore  ["occlussionTexture"] = occlTexture
            
    elif advMat == 4:
        tColorConn = material.findPlug("TEX_color_map", True)
        tOcclConn  = material.findPlug("TEX_ao_map",    True)

        #colorTexture = searchForNodeByApiType(tColorConn, maom.MFn.kTexture2d)
        colorTexture = searchForNodeByNameType(tColorConn, textTypes)
        if colorTexture:
            colorStore  ["baseTexture"  ] = colorTexture
        
        #occlTexture = searchForNodeByApiType(tOcclConn, maom.MFn.kTexture2d)
        occlTexture = searchForNodeByNameType(tOcclConn, textTypes)
        if occlTexture:
            colorStore  ["occlussionTexture"] = occlTexture


def attachMatXTextureTransforms(trv, rkint, textureTransforms, x3dAppearance):
    ttLen = len(textureTransforms)
    x3dParent = x3dAppearance
    
    if ttLen > 1:
        mtt = trv.processBasicNodeAddition(x3dParent, "textureTransform", "MultiTextureTransform", "")
        if mtt[0] == False:
            x3dParent = mtt[1]
    
    if ttLen > 0:
        for tt in textureTransforms:
            nodeName = tt[0].name()
            tTrans = trv.processBasicNodeAddition(x3dParent, "textureTransform", "TextureTransform", nodeName)
            if  tTrans[0] == False:
                tTrans[1].mapping = tt[1]
                
                tTrans[1].center      =                  getUFEAttribute(tt[0], "pivot" ).get()
                tTrans[1].rotation    = rkint.getDeg2Rad(getUFEAttribute(tt[0], "rotate").get())
                tTrans[1].translation =                  getUFEAttribute(tt[0], "offset").get()
                tTrans[1].scale       =                  getUFEAttribute(tt[0], "scale" ).get()
    else:
        tTrans = trv.processBasicNodeAddition(x3dParent, "textureTransform", "TextureTransform", x3dParent.DEF + "_TT")
    

def attachTextureTransforms(trv, rkint, textureTransforms, x3dAppearance):
    ttLen = len(textureTransforms)
    x3dParent = x3dAppearance
    
    if ttLen > 1:
        mtt = trv.processBasicNodeAddition(x3dParent, "textureTransform", "MultiTextureTransform", "")
        if mtt[0] == False:
            x3dParent = mtt[1]

    if ttLen > 0:
        for tt in textureTransforms:
            nodeName = tt[0].name()
            tTrans = trv.processBasicNodeAddition(x3dParent, "textureTransform", "TextureTransform", nodeName)
            if  tTrans[0] == False:
                tTrans[1].mapping = tt[1]
                
                tTrans[1].center      =                  cmds.getAttr(nodeName + ".offset"        )[0]
                tTrans[1].rotation    = rkint.getDeg2Rad(cmds.getAttr(nodeName + ".rotateFrame"   ))
                tTrans[1].translation =                  cmds.getAttr(nodeName + ".translateFrame")[0]
                ru = cmds.getAttr(nodeName + ".repeatU")
                cu = cmds.getAttr(nodeName + ".coverageU")
                rv = cmds.getAttr(nodeName + ".repeatV")
                cv = cmds.getAttr(nodeName + ".coverageV")
                if ru <= 0.0:
                    ru = 0.0001
                if rv <= 0.0:
                    rv = 0.0001
                if cu <= 0.0:
                    cu = 0.0001
                if cv <= 0.0:
                    cv = 0.0001
                tTrans[1].scale = (ru/cu, rv/cv)
    else:
        tTrans = trv.processBasicNodeAddition(x3dParent, "textureTransform", "TextureTransform", x3dParent.DEF + "_TT")


def getMatXSurfaceMaterialSceneItem(ufePath):
    ssPath = ufe.PathString.path(ufePath)
    ssItem = ufe.Hierarchy.createItem(ssPath)
    
    return ssItem
    
def getMatXSurfaceShaderSceneItem(smSceneItem, smPath):
    connection    = getUFEAttribute(smSceneItem, "surfaceshader", connected=True)
    surfaceshader = ufe.Hierarchy.createItem(connection.src.path)
    if surfaceshader.nodeType() == "nodegraph":
        hy = ufe.Hierarchy.hierarchy(surfaceshader)

        children = hy.children()
        if children:
            for child in children:
                if "_surfaceshader" in child.nodeType():
                    return child
    else:
        return surfaceshader


def get_all_dependencies(node, tracked_nodes):
    if not node or node in tracked_nodes:
        return
    
    tracked_nodes.add(node)
    
    # 1. Standard Upstream Connections
    for input_ptr in node.getInputs():
        upstream_node = input_ptr.getConnectedNode()
        if upstream_node:
            get_all_dependencies(upstream_node, tracked_nodes)
            
        # 2. Interface Connections
        interface_name = input_ptr.getInterfaceName()
        if interface_name:
            parent_graph = node.getParent()
            if parent_graph and parent_graph.isA(mx.NodeGraph):
                get_all_dependencies(parent_graph, tracked_nodes)

    # 3. NodeGraph Internal Outputs
    if node.isA(mx.NodeGraph):
        for output in node.getOutputs():
            internal_node = output.getConnectedNode()
            if internal_node:
                get_all_dependencies(internal_node, tracked_nodes)


def surgical_mtlx_export(maya_node, final_destination):
    # --- 1. IDENTIFY TARGET ---
    ufe_path_str = mcmds.getAttr(f"{maya_node}.ufePath")
    u_path = ufe.PathString.path(ufe_path_str)
    
    target_name = u_path.back()
    doc_path = u_path.pop()
    doc_item = ufe.Hierarchy.createItem(doc_path)
    
    # --- 2. SILENT EXPORT TO RAW ---
    context_ops = ufe.ContextOps.contextOps(doc_item)
    temp_path = os.path.join(tempfile.gettempdir(), "temp_raw_export.mtlx")
    resolved_temp = str(Path(temp_path).resolve()).replace("\\", "/")
    context_ops.doOp(['MxExportDocument', resolved_temp])
    
    # --- 3. CRAWL & PRUNE ---
    doc = mx.createDocument()
    mx.readFromXmlFile(doc, resolved_temp)
    
    tracked_nodes = set()
    target_node = doc.getChild(target_name)
    
    if not target_node:
        mcmds.warning(f"Target {target_name} not found in exported file.")
        return

    get_all_dependencies(target_node, tracked_nodes)
            
    for elem in doc.getChildren():
        if elem.isA(mx.Node) or elem.isA(mx.NodeGraph):
            if elem not in tracked_nodes:
                doc.removeChild(elem.getName())
        elif elem.isA(mx.Look) or elem.isA(mx.MaterialAssign):
            doc.removeChild(elem.getName())
                
    # --- 4. VALIDATION ---
    success, errors = doc.validate()
    if not success:
        print(f"Warning: Exported document has validation issues: {errors}")
    else:
        print("MaterialX Validation: Passed.")

    # --- 5. SAVE & CLEANUP ---
    mx.writeToXmlFile(doc, final_destination)
    if os.path.exists(resolved_temp):
        os.remove(resolved_temp)
        
    print(f"Surgical Export Success: {target_name} -> {final_destination}")

# Example Usage:
# surgical_mtlx_export("myStandardSurface", "C:/temp/final_export.mtlx")