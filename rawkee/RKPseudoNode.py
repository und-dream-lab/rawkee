import sys

import rawkee.x3d as rkx3d

class RKTestShader(rkx3d._X3DShaderNode):
    """
    ComposedShader can contain field declarations, but no CDATA section of plain-text source code, since programs are composed from child ShaderPart nodes.
    """
    # immutable constant functions have getter but no setter - - - - - - - - - -
    @classmethod
    def NAME(cls):
        """ Name of this X3D Node class. """
        return 'RKTestShader'
    @classmethod
    def SPECIFICATION_URL(cls):
        """ Extensible 3D (X3D) Graphics International Standard governs X3D architecture for all file formats and programming languages. """
        return 'https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/shaders.html#ComposedShader'
    @classmethod
    def TOOLTIP_URL(cls):
        """ X3D Tooltips provide authoring tips, hints and warnings for each node and field in X3D. """
        return 'https://www.web3d.org/x3d/tooltips/X3dTooltips.html#ComposedShader'
    @classmethod
    def FIELD_DECLARATIONS(cls):
        """ Field declarations for this node: name, defaultValue, type, accessType, inheritedFrom """
        return [
        ('DEF',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('USE',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('class_',     '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('id_',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('style_',     '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('IS',       None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('metadata', None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('language',   '', rkx3d.FieldType.SFString, rkx3d.AccessType.initializeOnly, 'X3DShaderNode')]
    def __init__(self, DEF='', USE='', class_='', id_='', style_='', IS=None, metadata=None, language=''):
        super().__init__(DEF, USE, class_, id_, style_, IS, metadata) # fields for _X3DNode only
        self.language = language
        
    @property # getter - - - - - - - - - -
    def language(self):
        """The language field indicates to the X3D player which shading language is used."""
        return self.__language
    @language.setter
    def language(self, language):
        if  language is None:
            language = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(language)
        self.__language = language
        
    @property # getter - - - - - - - - - -
    def id_(self):
        """ id_ attribute is a unique identifier for use within HTML pages. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__id_
    @id_.setter
    def id_(self, id_):
        if  id_ is None:
            id_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(id_)
        self.__id_ = id_
    @property # getter - - - - - - - - - -
    def style_(self):
        """ Space-separated list of classes, reserved for use by CSS cascading style_sheets. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__style_
    @style_.setter
    def style_(self, style_):
        if  style_ is None:
            style_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(style_)
        self.__style_ = style_
        
    # hasChild() function - - - - - - - - - -
    def hasChild(self):
        """ Whether or not this node has any child node or statement """
        return self.IS or self.metadata or (len(self.field) > 0) or (len(self.parts) > 0)
    # output function - - - - - - - - - -

'''
class X3DOMCommonSurfaceShader(rkx3d._X3DShaderNode):
    """
    CommonSurfaceShader is an X3DOM-only shader node.
    """
    # immutable constant functions have getter but no setter - - - - - - - - - -
    @classmethod
    def NAME(cls):
        """ Name of this X3D Node class. """
        return 'CommonSurfaceShader'
    @classmethod
    def SPECIFICATION_URL(cls):
        """ Extensible 3D (X3D) Graphics International Standard governs X3D architecture for all file formats and programming languages. """
        return 'https://doc.x3dom.org/author/Shaders/CommonSurfaceShader.html'
    @classmethod
    def TOOLTIP_URL(cls):
        """ X3D Tooltips provide authoring tips, hints and warnings for each node and field in X3D. """
        return 'https://doc.x3dom.org/tutorials/lighting/commonSurfaceShaderNode/index.html'
    @classmethod
    def FIELD_DECLARATIONS(cls):
        """ Field declarations for this node: name, defaultValue, type, accessType, inheritedFrom """
        return [
        ('DEF',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('USE',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('class_',     '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('id_',        '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('style_',     '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('IS',       None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('metadata', None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        
        ('language',              '', rkx3d.FieldType.SFString, rkx3d.AccessType.initializeOnly, 'X3DShaderNode'),
        
        ('alphaFactor',          1.0, rkx3d.FieldType.SFFloat, rkx3d.AccessType.inputOutput, 'CommonSurfaceShader'),
        ('transmissionTextureId', -1, rkx3d.FieldType.SFInt32, rkx3d.AccessType.inputOutput, 'CommonSurfaceShader')]
    """
    alphaTexture, SFNode, None 
    alphaTextureChannelMask, SFString, 'a' 
    alphaTextureCoordinatesId, SFInt32, 0 
    alphaTextureId, SFInt32, -1 
    ambientFactor, SFVec3f, '0.2, 0.2, 0.2' 
    ambientTexture, SFNode, None 
    ambientTextureChannelMask, SFString, 'rgb' 
    ambientTextureCoordinatesId, SFInt32, 0 
    ambientTextureId, SFInt32, -1 
    binormalTextureCoordinatesId, SFInt32, -1 
    diffuseDisplacementTexture, SFNode, None 
    diffuseFactor, SFVec3f, '0.8, 0.8, 0.8' 
    diffuseTexture, SFNode, None 
    diffuseTextureChannelMask, SFString, 'rgb' 
    diffuseTextureCoordinatesId, SFInt32, 0 
    diffuseTextureId, SFInt32, -1 
    displacementAxis, SFString, 'y' 
    displacementFactor, SFFloat, 255 
    displacementTexture, SFNode, None 
    displacementTextureCoordinatesId, SFInt32, 0 
    displacementTextureId, SFInt32, -1 
    emissiveFactor, SFVec3f, '0, 0, 0' 
    emissiveTexture, SFNode, None 
    emissiveTextureChannelMask, SFString, 'rgb' 
    emissiveTextureCoordinatesId, SFInt32, 0 
    emissiveTextureId, SFInt32, -1 
    environmentFactor, SFVec3f, '1, 1, 1' 
    environmentTexture, SFNode, None 
    environmentTextureChannelMask, SFString, 'rgb' 
    environmentTextureCoordinatesId, SFInt32, 0 
    environmentTextureId, SFInt32, -1 
    fresnelBlend, SFFloat, 0 
    invertAlphaTexture, SFBool, FALSE 
    language, SFString, '', #["Cg"|"GLSL"|"HLSL"|...]
    metadata, SFNode, None 
    normalBias, SFVec3f, '-1, -1, 1' 
    normalFormat, SFString, 'UNORM' 
    normalScale, SFVec3f, '2, 2, 2' 
    normalSpace, SFString, 'TANGENT' 
    normalTexture, SFNode, None 
    normalTextureChannelMask, SFString, 'rgb' 
    normalTextureCoordinatesId, SFInt32, 0 
    normalTextureId, SFInt32, -1 
    reflectionFactor, SFVec3f, '0, 0, 0' 
    reflectionTexture, SFNode, None 
    reflectionTextureChannelMask, SFString, 'rgb' 
    reflectionTextureCoordinatesId, SFInt32, 0 
    reflectionTextureId, SFInt32, -1 
    relativeIndexOfRefraction, SFFloat, 1 
    shininessFactor, SFFloat, 0.2 
    shininessTexture, SFNode, None 
    shininessTextureChannelMask, SFString, 'a' 
    shininessTextureCoordinatesId, SFInt32, 0 
    shininessTextureId, SFInt32, -1 
    specularFactor, SFVec3f, '0, 0, 0' 
    specularTexture, SFNode, None 
    specularTextureChannelMask, SFString, 'rgb' 
    specularTextureCoordinatesId, SFInt32, 0 
    specularTextureId, SFInt32, -1 
    tangentTextureCoordinatesId, SFInt32, -1 
    transmissionFactor, SFVec3f, '0, 0, 0' 
    transmissionTexture, SFNode, None 
    transmissionTextureChannelMask, SFString, 'rgb' 
    transmissionTextureCoordinatesId, SFInt32, 0 
    """
    def __init__(self,
        DEF='',
        USE='',
        class_='',
        id_='', 
        style_='',
        IS=None,
        metadata=None,
        language='',
        alphaFactor=1.0, transmissionTextureId=-1):

        super().__init__(DEF, USE, class_, id_, style_, IS, metadata) # fields for _X3DNode only
        self.language = language
        
        self.alphaFactor           = alphaFactor
        self.transmissionTextureId = transmissionTextureId
        
    @property # getter - - - - - - - - - -
    def id_(self):
        """ id_ attribute is a unique identifier for use within HTML pages. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__id_
    @id_.setter
    def id_(self, id_):
        if  id_ is None:
            id_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(id_)
        self.__id_ = id_
        
    @property # getter - - - - - - - - - -
    def style_(self):
        """ Space-separated list of classes, reserved for use by CSS cascading style_sheets. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__style_
    @style_.setter
    def style_(self, style_):
        if  style_ is None:
            style_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(style_)
        self.__style_ = style_

    @property # getter - - - - - - - - - -
    def language(self):
        """The language field indicates to the X3D player which shading language is used."""
        return self.__language
    @language.setter
    def language(self, language):
        if  language is None:
            language = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(language)
        self.__language = language
        
    @property # getter - - - - - - - - - -
    def alphaFactor(self):
        """[0.0,1.0] alphaFactor"""
        return self.__alphaFactor
    @alphaFactor.setter
    def alphaFactor(self, alphaFactor):
        if  alphaFactor is None:
            alphaFactor = 1.0  # default
        rkx3d.assertValidSFFloat(alphaFactor)
        rkx3d.assertNonNegative('alphaFactor', alphaFactor)
        rkx3d.assertGreaterThanEquals('alphaFactor', alphaFactor, 0.0)
        rkx3d.assertLessThanEquals('alphaFactor', alphaFactor, 1.0)
        self.__alphaFactor = alphaFactor

    #######################################
    # Last Field in Node
    #######################################
    @property # getter - - - - - - - - - -
    def transmissionTextureId(self):
        """[-1,+infinity) colorIndex values define the order in which Color|ColorRGBA values are applied to polygons (or vertices), interspersed by -1 if colorlPerVertex=true."""
        return self.__transmissionTextureId
    @transmissionTextureId.setter
    def transmissionTextureId(self, transmissionTextureId):
        if  transmissionTextureId is None:
            transmissionTextureId = -1
        rkx3d.assertValidSFInt32(transmissionTextureId)
        rkx3d.assertGreaterThanEquals('transmissionTextureId', transmissionTextureId, -1)
        self.__transmissionTextureId = transmissionTextureId

    # hasChild() function - - - - - - - - - -
    def hasChild(self):
        """ Whether or not this node has any child node or statement """
        return self.IS or self.metadata or (len(self.field) > 0) or (len(self.parts) > 0)
    # output function - - - - - - - - - -
'''        

class CGESkin(rkx3d._X3DChildNode):
    """
    Skin defines Castle Game Engine character.
    """
    # immutable constant functions have getter but no setter - - - - - - - - - -
    @classmethod
    def NAME(cls):
        """ Name of this X3D Node class. """
        return 'Skin'
    @classmethod
    def SPECIFICATION_URL(cls):
        """ Extensible 3D (X3D) Graphics International Standard governs X3D architecture for all file formats and programming languages. """
        return 'https://castle-engine.io/skin'
    @classmethod
    def TOOLTIP_URL(cls):
        """ X3D Tooltips provide authoring tips, hints and warnings for each node and field in X3D. """
        return 'https://castle-engine.io/skin'
    @classmethod
    def FIELD_DECLARATIONS(cls):
        """ Field declarations for this node: name, defaultValue, type, accessType, inheritedFrom """
        return [
        ('inverseBindMatrices', [], rkx3d.FieldType.MFMatrix4f, rkx3d.AccessType.initializeOnly, 'CGESkin'),
        ('shapes',              [], rkx3d.FieldType.MFNode,     rkx3d.AccessType.initializeOnly, 'CGESkin'),
        ('skeleton',          None, rkx3d.FieldType.SFNode,     rkx3d.AccessType.inputOutput,    'CGESkin'),
        ('joints',              [], rkx3d.FieldType.MFNode,     rkx3d.AccessType.initializeOnly, 'CGESkin'),
        ('DEF',                 '', rkx3d.FieldType.SFString,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('USE',                 '', rkx3d.FieldType.SFString,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('class_',              '', rkx3d.FieldType.SFString,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('id_',                 '', rkx3d.FieldType.SFString,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('style_',              '', rkx3d.FieldType.SFString,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('IS',                None, rkx3d.FieldType.SFNode,     rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('metadata',          None, rkx3d.FieldType.SFNode,     rkx3d.AccessType.inputOutput, 'X3DNode')]
        
    def __init__(self, DEF='', USE='', class_='', id_='', style_='', IS=None, metadata=None, inverseBindMatrices=None, shapes=None, skeleton=None, joints=None):
        # fields for _X3DNode only
        super().__init__(DEF, USE, class_, id_, style_, IS, metadata)
        self.inverseBindMatrices = inverseBindMatrices
        self.shapes   = shapes
        self.skeleton = skeleton
        self.joints   = joints
    
    @property # getter - - - - - - - - - -
    def id_(self):
        """ id_ attribute is a unique identifier for use within HTML pages. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__id_
    @id_.setter
    def id_(self, id_):
        if  id_ is None:
            id_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(id_)
        self.__id_ = id_
        
    @property # getter - - - - - - - - - -
    def style_(self):
        """ Space-separated list of classes, reserved for use by CSS cascading style_sheets. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__style_
    @style_.setter
    def style_(self, style_):
        if  style_ is None:
            style_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(style_)
        self.__style_ = style_
        
    @property # getter - - - - - - - - - -
    def inverseBindMatrices(self):
        """inverseBindMatrices specifies an arbitrary collection of matrix inverseBindMatricess that will be passed to the shader as per-vertex information."""
        return self.__inverseBindMatrices
    @inverseBindMatrices.setter
    def inverseBindMatrices(self, inverseBindMatrices):
        if  inverseBindMatrices is None:
            inverseBindMatrices = rkx3d.MFMatrix4f.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set inverseBindMatrices to .DEFAULT_VALUE()=' + str(MFMatrix4f.DEFAULT_VALUE()))
        rkx3d.assertValidMFMatrix4f(inverseBindMatrices)
        self.__inverseBindMatrices = inverseBindMatrices

    @property # getter - - - - - - - - - -
    def shapes(self):
        """[Shapes] Multiple Shape nodes that serve as the Chracter meshes."""
        return self.__shapes
    @shapes.setter
    def shapes(self, shapes):
        if  shapes is None:
            shapes = rkx3d.MFNode.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFNode.DEFAULT_VALUE()))
        rkx3d.assertValidMFNode(shapes)
        self.__shapes = shapes

    @property # getter - - - - - - - - - -
    def skeleton(self):
        """[X3DGroupingNode] Single grouping node (Transform or HAnimJoint)"""
        return self.__skeleton
    @skeleton.setter
    def skeleton(self, skeleton):
        if  skeleton is None:
            skeleton = None  # default
        rkx3d.assertValidSFNode(skeleton)
        if not skeleton is None and not isinstance(skeleton, (rkx3d.Transform, rkx3d.HAnimJoint, rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(skeleton) + ' does not match required node type (Transform,HAnimJoint,ProtoInstance) and is invalid')
        self.__skeleton = skeleton

    @property # getter - - - - - - - - - -
    def joints(self):
        """[Transform/HAnimJoint nodes] list of joint nodes found in the decendents of Character's skeleton field."""
        return self.__joints
    @joints.setter
    def joints(self, joints):
        if  joints is None:
            joints = rkx3d.MFNode.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFNode.DEFAULT_VALUE()))
        rkx3d.assertValidMFNode(joints)
        self.__joints = joints

    # hasChild() function - - - - - - - - - -
    def hasChild(self):
        """ Whether or not this node has any child node or statement """
        return self.shapes or self.skeleton or self.joints or self.IS or self.metadata


class CGEIndexedFaceSet(rkx3d._X3DComposedGeometryNode):
    """
    IndexedFaceSet defines polygons using index lists corresponding to vertex coordinates.
    """
    # immutable constant functions have getter but no setter - - - - - - - - - -
    @classmethod
    def NAME(cls):
        """ Name of this X3D Node class. """
        return 'IndexedFaceSet'
    @classmethod
    def SPECIFICATION_URL(cls):
        """ Extensible 3D (X3D) Graphics International Standard governs X3D architecture for all file formats and programming languages. """
        return 'https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#IndexedFaceSet'
    @classmethod
    def TOOLTIP_URL(cls):
        """ X3D Tooltips provide authoring tips, hints and warnings for each node and field in X3D. """
        return 'https://www.web3d.org/x3d/tooltips/X3dTooltips.html#IndexedFaceSet'
    @classmethod
    def FIELD_DECLARATIONS(cls):
        """ Field declarations for this node: name, defaultValue, type, accessType, inheritedFrom """
        return [
        ('DEF',               '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('USE',               '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('class_',            '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('id_',               '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('style_',            '', rkx3d.FieldType.SFString, rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('IS',              None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        ('metadata',        None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput, 'X3DNode'),
        
        ('ccw',             True, rkx3d.FieldType.SFBool,   rkx3d.AccessType.initializeOnly, 'X3DComposedGeometryNode'),
        ('colorIndex',        [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('colorPerVertex',  True, rkx3d.FieldType.SFBool,   rkx3d.AccessType.initializeOnly, 'X3DComposedGeometryNode'),
        ('convex',          True, rkx3d.FieldType.SFBool,   rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('coordIndex',        [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('creaseAngle',        0, rkx3d.FieldType.SFFloat,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('normalIndex',       [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('normalPerVertex', True, rkx3d.FieldType.SFBool,   rkx3d.AccessType.initializeOnly, 'X3DComposedGeometryNode'),
        ('solid',           True, rkx3d.FieldType.SFBool,   rkx3d.AccessType.initializeOnly, 'X3DComposedGeometryNode'),
        ('texCoordIndex',     [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('color',           None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('coord',           None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('fogCoord',        None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('normal',          None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('texCoord',        None, rkx3d.FieldType.SFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('attrib',            [], rkx3d.FieldType.MFNode,   rkx3d.AccessType.inputOutput,    'X3DComposedGeometryNode'),
        ('skinJoints0',       [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('skinJoints1',       [], rkx3d.FieldType.MFInt32,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('skinWeights0',      [], rkx3d.FieldType.MFVec4f,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet'),
        ('skinWeights1',      [], rkx3d.FieldType.MFVec4f,  rkx3d.AccessType.initializeOnly, 'IndexedFaceSet')]
    def __init__(self,
        DEF='',
        USE='',
        class_='',
        id_='',
        style_='',
        IS=None,
        metadata=None,
        ccw=True,
        colorIndex=None,
        colorPerVertex=True,
        convex=True,
        coordIndex=None,
        creaseAngle=0,
        normalIndex=None,
        normalPerVertex=True,
        solid=True,
        texCoordIndex=None,
        color=None,
        coord=None,
        fogCoord=None,
        normal=None,
        texCoord=None,
        attrib=None,
        skinJoints0=None,
        skinJoints1=None,
        skinWeights0=None,
        skinWeights1=None):
        # if _DEBUG: print('...DEBUG... in ConcreteNode IndexedFaceSet __init__ calling super.__init__(' + str(DEF) + ',' + str(USE) + ',' + str(class_) + ',' + str(id_) + ',' + str(style_) + ',' + str(metadata) + ',' + str(IS) + ')', flush=True)
        super().__init__(DEF, USE, class_, id_, style_, IS, metadata) # fields for _X3DNode only
        self.ccw = ccw
        self.colorIndex = colorIndex
        self.colorPerVertex = colorPerVertex
        self.convex = convex
        self.coordIndex = coordIndex
        self.creaseAngle = creaseAngle
        self.normalIndex = normalIndex
        self.normalPerVertex = normalPerVertex
        self.solid = solid
        self.texCoordIndex = texCoordIndex
        self.color = color
        self.coord = coord
        self.fogCoord = fogCoord
        self.normal = normal
        self.texCoord = texCoord
        self.attrib = attrib
        self.id_ = id_
        self.style_ = style_
        self.skinJoints0 = skinJoints0
        self.skinJoints1 = skinJoints1
        self.skinWeights0 = skinWeights0
        self.skinWeights1 = skinWeights1
        
    @property # getter - - - - - - - - - -
    def ccw(self):
        """ccw defines clockwise/counterclockwise ordering of vertex coordinates, which in turn defines front/back orientation of polygon normals according to Right-Hand Rule (RHR)."""
        return self.__ccw
    @ccw.setter
    def ccw(self, ccw):
        if  ccw is None:
            ccw = True  # default
        rkx3d.assertValidSFBool(ccw)
        self.__ccw = ccw
    @property # getter - - - - - - - - - -
    def colorIndex(self):
        """[-1,+infinity) colorIndex values define the order in which Color|ColorRGBA values are applied to polygons (or vertices), interspersed by -1 if colorlPerVertex=true."""
        return self.__colorIndex
    @colorIndex.setter
    def colorIndex(self, colorIndex):
        if  colorIndex is None:
            colorIndex = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(colorIndex)
        rkx3d.assertGreaterThanEquals('colorIndex', colorIndex, -1)
        self.__colorIndex = colorIndex
    @property # getter - - - - - - - - - -
    def colorPerVertex(self):
        """Whether Color|ColorRGBA values are applied to each point vertex (true) or to each polygon face (false)."""
        return self.__colorPerVertex
    @colorPerVertex.setter
    def colorPerVertex(self, colorPerVertex):
        if  colorPerVertex is None:
            colorPerVertex = True  # default
        rkx3d.assertValidSFBool(colorPerVertex)
        self.__colorPerVertex = colorPerVertex
    @property # getter - - - - - - - - - -
    def convex(self):
        """The convex field is a hint to renderers whether all polygons in a shape are convex (true), or possibly concave (false)."""
        return self.__convex
    @convex.setter
    def convex(self, convex):
        if  convex is None:
            convex = True  # default
        rkx3d.assertValidSFBool(convex)
        self.__convex = convex
    @property # getter - - - - - - - - - -
    def coordIndex(self):
        """[-1,+infinity) coordIndex indices provide the order in which coordinates are applied to construct each polygon face."""
        return self.__coordIndex
    @coordIndex.setter
    def coordIndex(self, coordIndex):
        if  coordIndex is None:
            coordIndex = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(coordIndex)
        rkx3d.assertGreaterThanEquals('coordIndex', coordIndex, -1)
        self.__coordIndex = coordIndex
    @property # getter - - - - - - - - - -
    def creaseAngle(self):
        """[0,+infinity) creaseAngle defines angle (in radians) for determining whether adjacent polygons are drawn with sharp edges or smooth shading."""
        return self.__creaseAngle
    @creaseAngle.setter
    def creaseAngle(self, creaseAngle):
        if  creaseAngle is None:
            creaseAngle = 0  # default
        rkx3d.assertValidSFFloat(creaseAngle)
        rkx3d.assertNonNegative('creaseAngle', creaseAngle)
        self.__creaseAngle = creaseAngle
    @property # getter - - - - - - - - - -
    def normalIndex(self):
        """[-1,+infinity) normalIndex values define the order in which normal vectors are applied to polygons (or vertices), interspersed by -1 if normalPerVertex=true."""
        return self.__normalIndex
    @normalIndex.setter
    def normalIndex(self, normalIndex):
        if  normalIndex is None:
            normalIndex = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(normalIndex)
        rkx3d.assertGreaterThanEquals('normalIndex', normalIndex, -1)
        self.__normalIndex = normalIndex
    @property # getter - - - - - - - - - -
    def normalPerVertex(self):
        """Whether Normal node vector values are applied to each point vertex (true) or to each polygon face (false)."""
        return self.__normalPerVertex
    @normalPerVertex.setter
    def normalPerVertex(self, normalPerVertex):
        if  normalPerVertex is None:
            normalPerVertex = True  # default
        rkx3d.assertValidSFBool(normalPerVertex)
        self.__normalPerVertex = normalPerVertex
    @property # getter - - - - - - - - - -
    def solid(self):
        """Setting solid true means draw only one side of polygons (backface culling on), setting solid false means draw both sides of polygons (backface culling off)."""
        return self.__solid
    @solid.setter
    def solid(self, solid):
        if  solid is None:
            solid = True  # default
        rkx3d.assertValidSFBool(solid)
        self.__solid = solid
    @property # getter - - - - - - - - - -
    def texCoordIndex(self):
        """[-1,+infinity) List of texture-coordinate indices mapping attached texture to corresponding coordinates."""
        return self.__texCoordIndex
    @texCoordIndex.setter
    def texCoordIndex(self, texCoordIndex):
        if  texCoordIndex is None:
            texCoordIndex = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(texCoordIndex)
        rkx3d.assertGreaterThanEquals('texCoordIndex', texCoordIndex, -1)
        self.__texCoordIndex = texCoordIndex
    @property # getter - - - - - - - - - -
    def color(self):
        """[X3DColorNode] Single contained Color or ColorRGBA node that can specify color values applied to corresponding vertices according to colorIndex and colorPerVertex fields."""
        return self.__color
    @color.setter
    def color(self, color):
        if  color is None:
            color = None  # default
        rkx3d.assertValidSFNode(color)
        if not color is None and not isinstance(color,(rkx3d._X3DColorNode,rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(color) + ' does not match required node type (_X3DColorNode,ProtoInstance) and is invalid')
        self.__color = color
    @property # getter - - - - - - - - - -
    def coord(self):
        """[X3DCoordinateNode] Single contained Coordinate or CoordinateDouble node that can specify a list of vertex values."""
        return self.__coord
    @coord.setter
    def coord(self, coord):
        if  coord is None:
            coord = None  # default
        rkx3d.assertValidSFNode(coord)
        if not coord is None and not isinstance(coord,(rkx3d._X3DCoordinateNode,rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(coord) + ' does not match required node type (_X3DCoordinateNode,ProtoInstance) and is invalid')
        self.__coord = coord
    @property # getter - - - - - - - - - -
    def fogCoord(self):
        """[FogCoordinate] Single contained FogCoordinate node that can specify depth parameters for fog in corresponding geometry."""
        return self.__fogCoord
    @fogCoord.setter
    def fogCoord(self, fogCoord):
        if  fogCoord is None:
            fogCoord = None  # default
        rkx3d.assertValidSFNode(fogCoord)
        if not fogCoord is None and not isinstance(fogCoord,(rkx3d.FogCoordinate,rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(fogCoord) + ' does not match required node type (FogCoordinate,ProtoInstance) and is invalid')
        self.__fogCoord = fogCoord
    @property # getter - - - - - - - - - -
    def normal(self):
        """[X3DNormalNode] Single contained Normal node that can specify perpendicular vectors for corresponding vertices to support rendering computations, applied according to the normalPerVertex field."""
        return self.__normal
    @normal.setter
    def normal(self, normal):
        if  normal is None:
            normal = None  # default
        rkx3d.assertValidSFNode(normal)
        if not normal is None and not isinstance(normal,(rkx3d._X3DNormalNode,rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(normal) + ' does not match required node type (_X3DNormalNode,ProtoInstance) and is invalid')
        self.__normal = normal
    @property # getter - - - - - - - - - -
    def texCoord(self):
        """[X3DTextureCoordinateNode] Single contained TextureCoordinate, TextureCoordinateGenerator or MultiTextureCoordinate node that can specify coordinates for texture mapping onto corresponding geometry."""
        return self.__texCoord
    @texCoord.setter
    def texCoord(self, texCoord):
        if  texCoord is None:
            texCoord = None  # default
        rkx3d.assertValidSFNode(texCoord)
        if not texCoord is None and not isinstance(texCoord,(rkx3d._X3DSingleTextureCoordinateNode,rkx3d.MultiTextureCoordinate,rkx3d.ProtoInstance)):
            # print(flush=True)
            raise rkx3d.X3DTypeError(str(texCoord) + ' does not match required node type (_X3DSingleTextureCoordinateNode,MultiTextureCoordinate,ProtoInstance) and is invalid')
        self.__texCoord = texCoord
    @property # getter - - - - - - - - - -
    def attrib(self):
        """[X3DVertexAttributeNode] Single contained FloatVertexAttribute node that can specify list of per-vertex attribute information for programmable shaders."""
        return self.__attrib
    @attrib.setter
    def attrib(self, attrib):
        if  attrib is None:
            attrib = rkx3d.MFNode.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFNode.DEFAULT_VALUE()))
        rkx3d.assertValidMFNode(attrib)
        self.__attrib = attrib
    @property # getter - - - - - - - - - -
    def id_(self):
        """ id_ attribute is a unique identifier for use within HTML pages. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__id_
    @id_.setter
    def id_(self, id_):
        if  id_ is None:
            id_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(id_)
        self.__id_ = id_
    @property # getter - - - - - - - - - -
    def style_(self):
        """ Space-separated list of classes, reserved for use by CSS cascading style_sheets. Appended underscore to field name to avoid naming collision with Python reserved word. """
        return self.__style_
    @style_.setter
    def style_(self, style_):
        if  style_ is None:
            style_ = rkx3d.SFString.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(SFString.DEFAULT_VALUE()))
        rkx3d.assertValidSFString(style_)
        self.__style_ = style_

    @property # getter - - - - - - - - - -
    def skinJoints0(self):
        """[0,+infinity) coordIndex indices provide the order in which coordinates are applied to construct each polygon face."""
        return self.__skinJoints0
    @skinJoints0.setter
    def skinJoints0(self, skinJoints0):
        if  skinJoints0 is None:
            skinJoints0 = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(skinJoints0)
        rkx3d.assertGreaterThanEquals('skinJoints0', skinJoints0, 0)
        self.__skinJoints0 = skinJoints0
    @property # getter - - - - - - - - - -
    def skinJoints1(self):
        """[0,+infinity) coordIndex indices provide the order in which coordinates are applied to construct each polygon face."""
        return self.__skinJoints1
    @skinJoints1.setter
    def skinJoints1(self, skinJoints1):
        if  skinJoints1 is None:
            skinJoints1 = rkx3d.MFInt32.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFInt32(skinJoints1)
        rkx3d.assertGreaterThanEquals('skinJoints1', skinJoints1, 0)
        self.__skinJoints1 = skinJoints1
    @property # getter - - - - - - - - - -
    def skinWeights0(self):
        """[0,1.0) coordIndex indices provide the order in which coordinates are applied to construct each polygon face."""
        return self.__skinWeights0
    @skinWeights0.setter
    def skinWeights0(self, skinWeights0):
        if  skinWeights0 is None:
            skinWeights0 = rkx3d.MFVec4f.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFVec4f(skinWeights0)
        rkx3d.assertGreaterThanEquals('skinWeights0', skinWeights0, 0.0)
        rkx3d.assertLessThanEquals('skinWeights0', skinWeights0, 1.0)
        self.__skinWeights0 = skinWeights0
    @property # getter - - - - - - - - - -
    def skinWeights1(self):
        """[0,1.0) coordIndex indices provide the order in which coordinates are applied to construct each polygon face."""
        return self.__skinWeights1
    @skinWeights0.setter
    def skinWeights1(self, skinWeights1):
        if  skinWeights1 is None:
            skinWeights1 = rkx3d.MFVec4f.DEFAULT_VALUE()
            # if _DEBUG: print('...DEBUG... set value to .DEFAULT_VALUE()=' + str(MFInt32.DEFAULT_VALUE()))
        rkx3d.assertValidMFVec4f(skinWeights1)
        rkx3d.assertGreaterThanEquals('skinWeights1', skinWeights1, 0.0)
        rkx3d.assertLessThanEquals('skinWeights1', skinWeights1, 1.0)
        self.__skinWeights1 = skinWeights1

    # hasChild() function - - - - - - - - - -
    def hasChild(self):
        """ Whether or not this node has any child node or statement """
        return self.color or self.coord or self.fogCoord or self.IS or self.metadata or self.normal or self.texCoord or (len(self.attrib) > 0)



#Only for code development
if __name__ == "__main__":
    cssNode = rkx3d.IndexedFaceSet()
    print(vars(cssNode))
    cssNode = CGEIndexedFaceSet()
    print(vars(cssNode))
    cssNode = CGESkin()
    print(vars(cssNode))
    cssNode = RKTestShader()
    print(vars(cssNode))
    cssNode = rkx3d.Background()
    print(vars(cssNode))
#    cssNode = X3DOMCommonSurfaceShader()
#    print(vars(cssNode))


"""
self.alphaFactor                  = 1.0             # transparency     0.0              # transparency            0.0           # transparency = 1 - alphaFactor;
self.alphaTexture                 = None            # -----------NA------------         # -----------NA------------
self.alphaTextureChannelMask      = 'a'
self.alphaTextureCoordinatesId    = 0
self.alphaTextureId               = -1

self.ambientFactor                = (0.2, 0.2, 0.2) # ambientIntensity 0.2              # ambientIntensity        0.2
self.ambientTexture               = None            # -----------NA------------         # ambientTexture          None
self.ambientTextureChannelMask    = 'rgb'
self.ambientTextureCoordinatesId  = 0               # -----------NA------------         # ambientTextureMapping   ''
self.ambientTextureId             = -1

self.binormalTextureCoordinatesId = -1

self.diffuseDisplacementTexture   = None

self.diffuseFactor                = (0.8, 0.8, 0.8) # diffuseColor     0.8 0.8 0.8      # diffuseColor            0.8 0.8 0.8
self.diffuseTexture               = None            # -----------NA------------         # diffuseTexture          None
self.diffuseTextureChannelMask    = 'rgb'
self.diffuseTextureCoordinatesId  = 0               # -----------NA------------         # diffuseTextureMapping   ''
self.diffuseTextureId             = -1

self.displacementAxis             = 'y'
self.displacementFactor           = 255.0
self.displacementTexture          = None
self.displacementTextureCoordinatesId = 0
self.displacementTextureId        = 0

self.emissiveFactor               = (0.0, 0.0, 0.0) # emissiveColor    0.0 0.0 0.0      # emissiveColor           0.0 0.0 0.0
self.emissiveTexture              = None            # -----------NA------------         # emissiveTexture         None
self.emissiveTextureChannelMask   = 'rgb'
self.emissiveTextureCoordinatesId = 0               # -----------NA------------         # emissiveTextureMapping  ''
self.emissiveTextureId            = -1

self.environmentFactor            = (1.0, 1.0, 1.0)
self.environmentTexture           = None
self.environmentTextureChannelMask = 'rgb'
self.environmentTextureCoordinatesId = 0
self.environmentTextureId         = -1

self.fresnelBlend                 = 0

self.invertAlphaTexture           = False

self.language                     = ''

self.metadata                     = None            # metadata         None             # metadata                None

self.normalBias                   = (-1.0, -1.0, -1.0)
self.normalFormat                 = 'UNORM'
self.normalScale                  = (2.0, 2.0, 2.0) # -----------NA------------         # normalScale             1.0
self.normalSpace                  = 'TANGENT'
self.normalTexture                = None            # -----------NA------------         # normalTexture           None
self.normalTextureChannelMask     = 'rgb'
self.normalTextureCoordinatesId   = 0               # -----------NA------------         # normalTextureMapping    ''
#            normalTextureCoordinatesId
self.normalTextureId              = -1

self.reflectionFactor             = (0.0, 0.0, 0.0)
self.reflectionTexture            = None
self.reflectionTextureChannelMask = 'rgb'
self.reflectionTextureCoordinatesId = 0
self.reflectionTextureId          = -1

self.relativeIndexOfRefraction    = 1

# -----------NA------------                         # -----------NA------------         # occlusionStrength       1.0
# -----------NA------------                         # -----------NA------------         # occlusionTexture        None
# -----------NA------------                         # -----------NA------------         # occulsionTextureMapping ''

self.shininessFactor              = 0.2             # shininess        0.2              # shininess               0.2
self.shininessTexture             = None            # -----------NA------------         # shininessTexture        None
self.shininessTextureChannelMask  = 'a'
self.shininessTextureCoordinatesId = 0               # -----------NA------------         # shininessTextureMapping ''
self.shininessTextureId           = -1

self.specularFactor               = (0.0, 0.0, 0.0) # specularColor    0.0 0.0 0.0      # specularColor           0.0 0.0 0.0
self.specularTexture              = None            # -----------NA------------         # specularTexture         None
self.specularTextureChannelMask   = 'rgb'
self.specularTextureCoordinatesId = 0               # -----------NA------------         # specularTextureMapping  ''
#            specularTextureCoordinatesId
self.specularTextureId            = -1

self.tangentTextureCoordinatesId  = -1

self.transmissionFactor           = (0.0, 0.0, 0.0)
self.transmissionTexture          = None
self.transmissionTextureChannelMask = 'rgb'
self.transmissionTextureCoordinatesId = 0
self.transmissionTextureId        = -1
"""
