import sys
import maya.api.OpenMaya as maom
import maya.cmds         as mcmds
import maya.mel          as mmel
import ctypes            as ctp
import numpy             as np

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
        print("printing")
        cmds.connectAttr(ttName + '.' + ttAttr, texName + '.' + flAttr, force=True)


def generateMROImage(mroDict, rOption):
    mroWidth  = 1
    mroHeight = 1
    mroDepth  = 4

    for key in mroDict:
        img = mroDict[key]
        imgW, imgH = img.getSize()
        
        if imgW > mroWidth:
            mroWidth  = imgW
        if imgH > mroHeight:
            mroHeight = imgH
            
    for key in mroDict:
        img = mroDict[key]
        imgW, imgH = img.getSize()
        
        if imgW != mroWidth or imgH != mroHeight:
            img.resize(mroWidth, mroHeight, preserveAspectRatio=False)
    
    mroImage = maom.MImage()
    mroImage.create(mroWidth, mroHeight, mroDepth, maom.MImage.kFloat)

    mroFL    = mroWidth * mroHeight * mroDepth
    mroPtr   = mroImage.floatPixels()
    mroArray = (ctp.c_float * mroFL).from_address(mroPtr)
    for i in range(mroWidth * mroHeight):
        mroArray[mroIdx    ] = 0.0
        mroArray[mroIdx + 1] = 0.0
        mroArray[mroIdx + 2] = 0.0
        mroArray[mroIdx + 3] = 0.0
        
    
    redImage = mroDict.get("red", None)
    if redImage:
        redWidth, redHeight = redImage.getSize()
        redDepth = redImage.depth()
        redFL    = redWidth * redHeight * redDepth
        redPtr   = redImage.floatPixels()
        redArray = (ctp.c_float * redFL).from_address(redPtr)
        
        for i in range(mroWidth * mroHeight):
            mroIdx           = i * mroDepth
            redIdx           = i * redDepth
            mroArray[mroIdx] = redArry[redIdx]

    grnImage = mroDict.get("green", None)
    if grnImage:
        grnWidth, grnHeight = grnImage.getSize()
        grnDepth = grnImage.depth()
        grnFL    = grnWidth * grnHeight * grnDepth
        grnPtr   = grnImage.floatPixels()
        grnArray = (ctp.c_float * grnFL).from_address(grnPtr)
        
        for i in range(mroWidth * mroHeight):
            mroIdx               = i * mroDepth
            redIdx               = i * grnDepth
            if   rOption == 1:
                mroArray[mroIdx + 1] = np.sqrt(   grnArry[grnIdx + 1]   )
            elif rOption == 2:
                mroArray[mroIdx + 1] = np.sqrt(2/(grnArry[grnIdx + 1]+2))
            elif rOption == 3:
                mroArray[mroIdx + 1] = np.sqrt(   grnArry[grnIdx + 1]   )
            else:
                mroArray[mroIdx + 1] =            grnArry[grnIdx + 1]

    bluImage = mroDict.get("blue", None)
    if bluImage:
        bluWidth, bluHeight = bluImage.getSize()
        bluDepth = bluImage.depth()
        bluFL    = bluWidth * bluHeight * bluDepth
        bluPtr   = bluImage.floatPixels()
        bluArray = (ctp.c_float * bluFL).from_address(bluPtr)
        
        for i in range(mroWidth * mroHeight):
            mroIdx               = i * mroDepth
            redIdx               = i * bluDepth
            mroArray[mroIdx + 2] = bluArry[bluIdx + 2]

    return mroImage
    

def getUnknownBaseColorAndOcclusionTextures(material, colorStore, colorAttr):
    # Color Plug
    colorConn = material.findPlug(colorAttr, True)
    
    # Search for multiply node
    # Get baseTexture and occlusionTexture
    multiply = searchForNodeByNameType(colorConn, ["multiplyDivide", "aiMultiply"])
    if multiply:
        inputConn1   = multiply.findPlug("input1", True)
        colorTexture = searchForNodeByApiType(inputConn1.asMObject(), maom.MFn.kTexture2d)
        if colorTexture:
            colorStore["baseTexture"] = colorTexture
        
        inputConn2   = multiply.findPlug("input2", True)
        occlTexture  = searchForNodeByApiType(inputConn2.asMObject(), maom.MFn.kTexture2d)
        if occlTexture:
            colorStore["occlusionTexture"] = occlTexture
        else:
            inputConn2 = multiply.findPlug("input2R", True)
            occlTexture2R = searchForNodeByApiType(inputConn2.asMObject(), maom.MFn.kTexture2d)
            if occlTexture2R:
                colorStore["occlusionTexture"] = occlTexture2R
    else:
        aiImage = searchForNodeByNameType(colorConn, ["aiImage"])
        if aiImage:
            colorStore["baseTexture"] = aiImage
            multiConn = aiImage.findPlug("multiply", True)
            occlTexture  = searchForNodeByApiType(multiConn.asMObject(), maom.MFn.kTexture2d)
            if occlTexture:
                colorStore["occlusionTexture"] = occlTexture
            else:
                multiConn = aiImage.findPlug("multiplyR", True)
                occlTexture2R = searchForNodeByApiType(multiConn.asMObject(), maom.MFn.kTexture2d)
                if occlTexture2R:
                    colorStore["occlusionTexture"] = occlTexture2R
        else:
            colorTexture = searchForNodeByApiType(colorConn.asMObject(), maom.MFn.kTexture2d)
            if colorTexture:
                colorStore["baseTexture"] = colorTexture
            
            occlTexture  = searchForNodeByApiType(baseConn.asMObject(), maom.MFn.kTexture2d)
            if occlTexture:
                colorTex["occlusionTexture"] = occlTexture


def getLegacyBaseColorAndOcclusionTextures(material, colorStore, physMat):
    hasOcclTexture = False
    
    # Color Plug
    colorConn = material.findPlug("color", True)
    
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
            
    # Ambient Color Plug
    if hasOcclTexture == False:
        ambConn   = material.findPlug("ambientColor", True)
        acTexture = searchForNodeByApiType(ambConn, maom.MFn.kTexture2d)
        if acTexture:
            hasOcclTexture = True
            colorStore["occlusionTexture"] = acTexture
    
    if hasOcclTexture == False:
        acColor = mcmds.getAttr(material.name() + ".ambientColor")[0]
        physMat.occlusionStrength = (acColor[0] + acColor[1] + acColor[2]) / 3


def getAdvBaseColorAndOcclusionTextures(material, colorStore, advMat):
    if advMat < 3:
        # Color Plugs
        colorConn = material.findPlug("baseColor", True)
        baseAttr  = "baseWeight"
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
                
                occlTexture  = searchForNodeByApiType(baseConn, maom.MFn.kTexture2d)
                if occlTexture:
                    colorTex["occlusionTexture"] = occlTexture
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
        
        tOcclConn   = material.findPlug("TEX_ao_map", True)
        occlTexture = searchForNodeByApiType(tOcclConn, maom.MFn.kTexture2d)
        if occlTexture:
            colorStore  ["occlussionTexture"] = occlTexture
