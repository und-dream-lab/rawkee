import os
import json
import re
import xml.etree.ElementTree as ET
from rawkee.io.RKx3d import *


class RKLoadSceneFromFile:
    """
    Loads an X3D scenegraph from a file into RKx3d.py objects.

    Supported encodings
    -------------------
    *.x3d  - X3D XML encoding
    *.x3dj - X3D JSON encoding
    *.x3dv - X3D Classic VRML encoding
    """

    def __init__(self):
        self._defNodes = {}   # DEF name -> node instance (for USE resolution)
        self._baseDir  = ''   # directory of the file being loaded

    # -----------------------------------------------------------------------
    # Public entry point – mirrors RKSceneTraversal.x3d2disk()
    # -----------------------------------------------------------------------

    def disk2x3d(self, fullPath):
        """
        Load an X3D scenegraph from *fullPath* and return an X3D object.

        The encoding is determined from the file extension:
          *.x3d  - X3D XML     encoding
          *.x3dj - X3D JSON    encoding
          *.x3dv - X3D Classic encoding

        Returns an X3D instance on success, or None on failure.
        """
        ext = os.path.splitext(fullPath)[1].lower()
        self._defNodes.clear()
        self._baseDir = os.path.dirname(os.path.abspath(fullPath))

        try:
            if   ext == '.x3d':
                return self._loadFromXML(fullPath)
            elif ext == '.x3dj' or ext == '.json':
                return self._loadFromJSON(fullPath)
            elif ext == '.x3dv':
                return self._loadFromClassic(fullPath)
            else:
                print(f'RKLoadSceneFromFile: unsupported file extension "{ext}"')
                return None
        except Exception as exc:
            print(f'RKLoadSceneFromFile: error loading "{fullPath}": {exc}')
            return None

    def from_xml_string(self, xml_str: str):
        """Parse an X3D scene from an in-memory XML string. Returns X3D or None."""
        import io as _io
        self._defNodes.clear()
        self._baseDir = ''
        try:
            tree = ET.parse(_io.StringIO(xml_str))
        except ET.ParseError as exc:
            print(f'RKLoadSceneFromFile.from_xml_string: {exc}')
            return None
        root    = tree.getroot()
        tag     = re.sub(r'\{[^}]*\}', '', root.tag)
        if tag != 'X3D':
            return None
        x3dDoc  = X3D()
        profile = root.get('profile')
        version = root.get('version')
        if profile:
            try:    x3dDoc.profile = profile
            except Exception: pass
        if version:
            try:    x3dDoc.version = version
            except Exception: pass
        for child in root:
            childTag = re.sub(r'\{[^}]*\}', '', child.tag)
            if childTag == 'head':
                x3dDoc.head = self._parseXMLHead(child)
            elif childTag == 'Scene':
                sceneNode = Scene()
                for sc in child:
                    node = self._parseXMLNode(sc)
                    if node is not None:
                        sceneNode.children.append(node)
                x3dDoc.Scene = sceneNode
        return x3dDoc

    # =======================================================================
    # Shared helpers
    # =======================================================================

    # Tuple component counts for every MF vector/colour/matrix/rotation type
    _MF_VECTOR_SIZES = {
        'MFVec2f': 2,    'MFVec2d': 2,
        'MFVec3f': 3,    'MFVec3d': 3,    'MFColor': 3,
        'MFVec4f': 4,    'MFVec4d': 4,    'MFRotation': 4,  'MFColorRGBA': 4,
        'MFQuaternion': 4,
        'MFMatrix3f': 9, 'MFMatrix3d': 9,
        'MFMatrix4f': 16,'MFMatrix4d': 16,
    }

    @staticmethod
    def _fieldTypeMap(nodeClass):
        """Return {fieldName: fieldTypeString} for a node class."""
        return {decl[0]: decl[2]() for decl in nodeClass.FIELD_DECLARATIONS()}

    # Classes that share a NAME() but have different field sets, ordered base→extended.
    # The loader pre-scans XML attributes and picks the first class whose field set
    # covers all attributes present in the element.
    _UPGRADE_CHAIN = {
        'PhysicalMaterial':   [PhysicalMaterial, PhysicalMaterialExt, PhysicalMaterial_X3DOM],
        'IndexedFaceSet':     [IndexedFaceSet,    CGEIndexedFaceSet],
        'IndexedTriangleSet': [IndexedTriangleSet, CGEIndexedTriangleSet],
    }

    @classmethod
    def _selectClass(cls, tag, attr_keys, child_container_fields=None):
        """Return an instance of the most appropriate class for *tag* given the
        XML attribute names and child containerField values present.
        Returns None if no upgrade chain exists."""
        chain = cls._UPGRADE_CHAIN.get(tag)
        if not chain:
            return None
        needed = frozenset(
            'global_' if a == 'global' else a
            for a in list(attr_keys) + list(child_container_fields or [])
            if a and a != 'containerField'
        )
        for node_cls in chain:
            known = frozenset(decl[0] for decl in node_cls.FIELD_DECLARATIONS())
            if needed <= known:
                return node_cls()
        return chain[-1]()  # fall back to most capable class

    def _resolveUrls(self, urls):
        """Resolve URL strings to server-relative paths (leading '/'), forward slashes only."""
        if not self._baseDir or not urls:
            return urls
        _ABS = ('http://', 'https://', 'ftp://', 'ftps://', 'data:', 'urn:', '#')
        result = []
        for url in urls:
            s = url.strip()
            if not s or any(s.lower().startswith(p) for p in _ABS):
                result.append(url)
                continue
            # Strip file:// scheme
            sl = s.lower()
            if sl.startswith('file:///'):
                s = s[8:]
            elif sl.startswith('file://'):
                s = s[7:]
            # Resolve relative paths against base directory
            if not os.path.isabs(s):
                s = os.path.normpath(os.path.join(self._baseDir, s))
            # Forward slashes; strip Windows drive letter so result is server-relative
            s = s.replace('\\', '/')
            if len(s) >= 2 and s[1] == ':':
                s = s[2:]
            result.append(s)
        return result

    def _parseStrValue(self, strVal, fType):
        """
        Convert a string representation of an X3D field value to the
        appropriate Python type. Handles both SF and MF types.

        Used by both the XML and Classic parsers.
        """
        strVal = strVal.strip()

        # ---- SFBool --------------------------------------------------------
        if fType == 'SFBool':
            return strVal.lower() in ('true', '1')

        # ---- SFInt32 -------------------------------------------------------
        elif fType == 'SFInt32':
            return int(strVal)

        # ---- SFFloat / SFDouble / SFTime -----------------------------------
        elif fType in ('SFFloat', 'SFDouble', 'SFTime'):
            return float(strVal)

        # ---- SFString ------------------------------------------------------
        elif fType == 'SFString':
            # Classic encoding wraps strings in double-quotes; strip them.
            if strVal.startswith('"') and strVal.endswith('"') and len(strVal) >= 2:
                return strVal[1:-1]
            return strVal

        # ---- SFImage -------------------------------------------------------
        elif fType == 'SFImage':
            parts = strVal.split()
            if len(parts) == 1:
                return int(parts[0], 0)
            return tuple(int(p, 0) for p in parts)

        # ---- SF tuple types ------------------------------------------------
        elif fType in ('SFVec2f', 'SFVec2d'):
            parts = strVal.split()
            return tuple(float(p) for p in parts[:2])

        elif fType in ('SFVec3f', 'SFVec3d', 'SFColor'):
            parts = strVal.split()
            return tuple(float(p) for p in parts[:3])

        elif fType in ('SFVec4f', 'SFVec4d', 'SFRotation', 'SFColorRGBA'):
            parts = strVal.split()
            return tuple(float(p) for p in parts[:4])

        elif fType in ('SFMatrix3f', 'SFMatrix3d'):
            parts = strVal.split()
            return tuple(float(p) for p in parts[:9])

        elif fType in ('SFMatrix4f', 'SFMatrix4d'):
            parts = strVal.split()
            return tuple(float(p) for p in parts[:16])

        # ---- MFBool --------------------------------------------------------
        elif fType == 'MFBool':
            tokens = re.split(r'[\s,]+', strVal)
            return [t.lower() in ('true', '1') for t in tokens if t]

        # ---- MFInt32 -------------------------------------------------------
        elif fType == 'MFInt32':
            tokens = re.split(r'[\s,]+', strVal)
            return [int(t) for t in tokens if t]

        # ---- MFFloat / MFDouble / MFTime -----------------------------------
        elif fType in ('MFFloat', 'MFDouble', 'MFTime'):
            tokens = re.split(r'[\s,]+', strVal)
            return [float(t) for t in tokens if t]

        # ---- MFString ------------------------------------------------------
        elif fType == 'MFString':
            # Each element is delimited by double-quotes: "val1" "val2"
            return re.findall(r'"((?:[^"\\]|\\.)*)"', strVal)

        # ---- MF vector / colour / matrix / rotation ------------------------
        elif fType in self._MF_VECTOR_SIZES:
            n      = self._MF_VECTOR_SIZES[fType]
            tokens = re.split(r'[\s,]+', strVal)
            nums   = [float(t) for t in tokens if t]
            return [tuple(nums[i:i + n]) for i in range(0, len(nums), n)]

        # ---- MFImage -------------------------------------------------------
        elif fType == 'MFImage':
            tokens = re.split(r'[\s,]+', strVal)
            return [int(t, 0) for t in tokens if t]

        else:
            return strVal

    def _parseJSONValue(self, val, fType):
        """
        Convert a value already decoded from JSON (may be bool/int/float/list/str)
        to the appropriate Python type for the given X3D field type.
        """
        # ---- SFBool --------------------------------------------------------
        if fType == 'SFBool':
            if isinstance(val, bool):
                return val
            return str(val).lower() in ('true', '1')

        # ---- Scalar SF types -----------------------------------------------
        elif fType == 'SFInt32':
            return int(val)

        elif fType in ('SFFloat', 'SFDouble', 'SFTime'):
            return float(val)

        elif fType == 'SFString':
            return str(val)

        # ---- SF tuple types ------------------------------------------------
        elif fType in ('SFVec2f', 'SFVec2d',
                       'SFVec3f', 'SFVec3d', 'SFColor',
                       'SFVec4f', 'SFVec4d', 'SFRotation', 'SFColorRGBA',
                       'SFMatrix3f', 'SFMatrix3d',
                       'SFMatrix4f', 'SFMatrix4d'):
            if isinstance(val, list):
                return tuple(float(v) for v in val)
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        # ---- MFBool --------------------------------------------------------
        elif fType == 'MFBool':
            if isinstance(val, list):
                return [bool(v) if isinstance(v, bool) else str(v).lower() == 'true'
                        for v in val]
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        # ---- Flat numeric MF types -----------------------------------------
        elif fType in ('MFFloat', 'MFDouble', 'MFTime'):
            if isinstance(val, list):
                return [float(v) for v in val]
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        elif fType == 'MFInt32':
            if isinstance(val, list):
                return [int(v) for v in val]
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        # ---- MFString ------------------------------------------------------
        elif fType == 'MFString':
            if isinstance(val, list):
                return [str(v) for v in val]
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        # ---- MF vector / colour / matrix / rotation  -----------------------
        elif fType in self._MF_VECTOR_SIZES:
            n = self._MF_VECTOR_SIZES[fType]
            if isinstance(val, list):
                if val and isinstance(val[0], list):
                    # List-of-lists (e.g. from some JSON exporters)
                    return [tuple(float(x) for x in v) for v in val]
                else:
                    # Flat list – group into n-tuples
                    nums = [float(v) for v in val]
                    return [tuple(nums[i:i + n]) for i in range(0, len(nums), n)]
            elif isinstance(val, str):
                return self._parseStrValue(val, fType)
            return val

        else:
            return val

    # =======================================================================
    # XML (*.x3d)
    # =======================================================================

    def _loadFromXML(self, fullPath):
        tree = ET.parse(fullPath)
        root = tree.getroot()

        # Strip any XML namespace prefix from the tag name
        tag = re.sub(r'\{[^}]*\}', '', root.tag)
        if tag != 'X3D':
            print('RKLoadSceneFromFile: XML root element is not <X3D>')
            return None

        x3dDoc  = X3D()
        profile = root.get('profile')
        version = root.get('version')
        if profile:
            try:    x3dDoc.profile = profile
            except Exception: pass
        if version:
            try:    x3dDoc.version = version
            except Exception: pass

        for child in root:
            childTag = re.sub(r'\{[^}]*\}', '', child.tag)
            if childTag == 'head':
                x3dDoc.head = self._parseXMLHead(child)
            elif childTag == 'Scene':
                sceneNode = Scene()
                for sc in child:
                    node = self._parseXMLNode(sc)
                    if node is not None:
                        sceneNode.children.append(node)
                x3dDoc.Scene = sceneNode

        return x3dDoc

    def _parseXMLHead(self, headElem):
        headNode = head()
        for child in headElem:
            childTag = re.sub(r'\{[^}]*\}', '', child.tag)
            if childTag == 'component':
                compNode = component()
                try:    compNode.name  = child.get('name', '')
                except Exception: pass
                try:    compNode.level = int(child.get('level', '1'))
                except Exception: pass
                headNode.children.append(compNode)
            elif childTag == 'meta':
                metaNode = meta()
                for attrName, attrVal in child.attrib.items():
                    try:    setattr(metaNode, attrName, attrVal)
                    except Exception: pass
                headNode.children.append(metaNode)
        return headNode

    def _parseXMLNode(self, elem):
        tag = re.sub(r'\{[^}]*\}', '', elem.tag)

        # ---- ROUTE ---------------------------------------------------------
        if tag == 'ROUTE':
            routeNode = ROUTE()
            for key, val in elem.attrib.items():
                try:    setattr(routeNode, key, val)
                except Exception: pass
            return routeNode

        # ---- Instantiate the node ------------------------------------------
        nodeTuple = instantiateNodeFromString(tag)
        if nodeTuple is None or nodeTuple[0] is None:
            print(f'RKLoadSceneFromFile: unknown XML node type "{tag}", skipping.')
            return None
        tNode = nodeTuple[0]

        # ---- USE shortcut --------------------------------------------------
        useVal = elem.get('USE')
        if useVal:
            tNode.USE = useVal
            return tNode

        # ---- Upgrade to most capable class that supports all present attrs -
        child_cfs = [child.get('containerField', '') for child in elem]
        upgraded = self._selectClass(tag, elem.attrib.keys(), child_cfs)
        if upgraded is not None:
            tNode = upgraded

        # ---- Build field-type lookup for this node -------------------------
        ftMap = self._fieldTypeMap(type(tNode))

        # ---- Map XML attributes to node fields ----------------------------
        for attrName, attrVal in elem.attrib.items():
            if attrName == 'containerField':
                continue
            # 'global' is a Python keyword; RKx3d uses 'global_'
            pName = 'global_' if attrName == 'global' else attrName
            fType = ftMap.get(pName)
            if fType is None or fType in ('SFNode', 'MFNode'):
                continue
            try:
                parsed = self._parseStrValue(attrVal, fType)
                if fType == 'MFString' and pName.lower() == 'url':
                    parsed = self._resolveUrls(parsed)
                setattr(tNode, pName, parsed)
                if attrName == 'DEF':
                    self._defNodes[attrVal] = tNode
            except Exception as exc:
                print(f'RKLoadSceneFromFile: {tag}.{pName}="{attrVal}": {exc}')

        # ---- Recurse into child elements -----------------------------------
        for child in elem:
            childTag       = re.sub(r'\{[^}]*\}', '', child.tag)
            containerField = child.get('containerField', '')
            childNode      = self._parseXMLNode(child)
            if childNode is None:
                continue

            fieldName = containerField if containerField else self._defaultContainerField(childNode, tNode)
            if not fieldName:
                continue
            try:
                existing = getattr(tNode, fieldName)
                if isinstance(existing, list):
                    existing.append(childNode)
                else:
                    setattr(tNode, fieldName, childNode)
            except AttributeError:
                print(f'RKLoadSceneFromFile: {tag} has no field "{fieldName}"')

        return tNode

    # X3D spec-defined default containerField for well-known node types.
    # Keyed by the Python class name (type(node).__name__).
    _DEFAULT_CF = {
        'Appearance':                    'appearance',
        # Material types
        'Material':                      'material',
        'PhysicalMaterial':              'material',
        'PhysicalMaterialExt':           'material',
        'UnlitMaterial':                 'material',
        'TwoSidedMaterial':              'material',
        'PhysicalMaterial_X3DOM':        'material',
        # Texture types
        'ImageTexture':                  'texture',
        'MovieTexture':                  'texture',
        'PixelTexture':                  'texture',
        'ImageTexture3D':                'texture',
        'PixelTexture3D':                'texture',
        'ComposedTexture3D':             'texture',
        'GeneratedCubeMapTexture':       'texture',
        'ComposedCubeMapTexture':        'texture',
        'ImageCubeMapTexture':           'texture',
        'MultiTexture':                  'texture',
        'RenderedTexture':               'texture',
        # TextureTransform
        'TextureTransform':              'textureTransform',
        'TextureTransform3D':            'textureTransform',
        'TextureTransformMatrix3D':      'textureTransform',
        'MultiTextureTransform':         'textureTransform',
        # Coord
        'Coordinate':                    'coord',
        'CoordinateDouble':              'coord',
        'GeoCoordinate':                 'coord',
        # Color / Normal / Tangent / TexCoord / FogCoord
        'Color':                         'color',
        'ColorRGBA':                     'color',
        'Normal':                        'normal',
        'Tangent':                       'tangent',
        'TextureCoordinate':             'texCoord',
        'TextureCoordinate3D':           'texCoord',
        'TextureCoordinate4D':           'texCoord',
        'TextureCoordinateGenerator':    'texCoord',
        'MultiTextureCoordinate':        'texCoord',
        'NurbsTextureCoordinate':        'texCoord',
        'FogCoordinate':                 'fogCoord',
        # FontStyle
        'FontStyle':                     'fontStyle',
        'ScreenFontStyle':               'fontStyle',
        # Geometry
        'Box':                           'geometry',
        'Cone':                          'geometry',
        'Cylinder':                      'geometry',
        'Sphere':                        'geometry',
        'Text':                          'geometry',
        'PointSet':                      'geometry',
        'LineSet':                       'geometry',
        'IndexedLineSet':                'geometry',
        'IndexedFaceSet':                'geometry',
        'IndexedTriangleSet':            'geometry',
        'IndexedTriangleFanSet':         'geometry',
        'IndexedTriangleStripSet':       'geometry',
        'TriangleSet':                   'geometry',
        'TriangleFanSet':                'geometry',
        'TriangleStripSet':              'geometry',
        'QuadSet':                       'geometry',
        'IndexedQuadSet':                'geometry',
        'ElevationGrid':                 'geometry',
        'Extrusion':                     'geometry',
        'GeoElevationGrid':              'geometry',
        'TriangleSet2D':                 'geometry',
        'Polyline2D':                    'geometry',
        'Polypoint2D':                   'geometry',
        'Arc2D':                         'geometry',
        'ArcClose2D':                    'geometry',
        'Circle2D':                      'geometry',
        'Disk2D':                        'geometry',
        'Rectangle2D':                   'geometry',
        'CGEIndexedFaceSet':             'geometry',
        'CGEIndexedTriangleSet':         'geometry',
        'NurbsCurve':                    'geometry',
        'NurbsPatchSurface':             'geometry',
        'NurbsTrimmedSurface':           'geometry',
        'NurbsSweptSurface':             'geometry',
        'NurbsSwungSurface':             'geometry',
        # Sound source
        'AudioClip':                     'source',
    }

    def _defaultContainerField(self, childNode, parentNode):
        """
        Return the default containerField for *childNode* inside *parentNode*
        when no containerField attribute was present in the X3D file.

        Resolution order:
          1. X3D spec lookup table keyed by Python class name
          2. Case-insensitive scan of parent SFNode/MFNode field names
          3. Fall back to 'children' if the parent has that field
        """
        child_cls = type(childNode).__name__

        # 1. Spec table lookup
        cf = self._DEFAULT_CF.get(child_cls)
        if cf and hasattr(parentNode, cf):
            return cf

        # 2. Scan parent SFNode/MFNode fields for a name that matches the child class
        lname = child_cls.lower()
        for decl in type(parentNode).FIELD_DECLARATIONS():
            fname = decl[0]
            try:
                ftype = decl[2]()
            except Exception:
                continue
            if ftype in ('SFNode', 'MFNode') and fname.lower() == lname:
                return fname

        # 3. Fall back to 'children'
        if hasattr(parentNode, 'children'):
            return 'children'
        return ''

    # =======================================================================
    # JSON (*.x3dj)
    # =======================================================================

    def _loadFromJSON(self, fullPath):
        with open(fullPath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'X3D' not in data:
            print('RKLoadSceneFromFile: JSON root key "X3D" not found')
            return None

        x3dData = data['X3D']
        x3dDoc  = X3D()

        profile = x3dData.get('@profile')
        version = x3dData.get('@version')
        if profile:
            try:    x3dDoc.profile = profile
            except Exception: pass
        if version:
            try:    x3dDoc.version = version
            except Exception: pass

        if 'head' in x3dData:
            x3dDoc.head = self._parseJSONHead(x3dData['head'])

        if 'Scene' in x3dData:
            sceneNode = Scene()
            for childData in x3dData['Scene'].get('-children', []):
                node = self._parseJSONNode(childData)
                if node is not None:
                    sceneNode.children.append(node)
            x3dDoc.Scene = sceneNode

        return x3dDoc

    def _parseJSONHead(self, headData):
        headNode = head()
        for metaItem in headData.get('meta', []):
            metaNode = meta()
            for key, val in metaItem.items():
                if key.startswith('@'):
                    try:    setattr(metaNode, key[1:], val)
                    except Exception: pass
            headNode.children.append(metaNode)
        for compItem in headData.get('component', []):
            compNode = component()
            for key, val in compItem.items():
                if key.startswith('@'):
                    attrName = key[1:]
                    try:
                        if attrName == 'level':
                            compNode.level = int(val)
                        else:
                            setattr(compNode, attrName, val)
                    except Exception: pass
            headNode.children.append(compNode)
        return headNode

    def _parseJSONNode(self, nodeData):
        """
        Parse one JSON node object of the form { "NodeType": { ... } }.

        Scalar/vector field attributes are stored as "@fieldName": value.
        Child node fields are stored as  "-fieldName": [node, ...] or
                                         "-fieldName": node.
        """
        # Find the node-type key (first key without @ or - prefix)
        nodeType = None
        nodeBody = None
        for key in nodeData:
            if not key.startswith('@') and not key.startswith('-'):
                nodeType = key
                nodeBody = nodeData[key]
                break
        if nodeType is None:
            return None

        # ---- ROUTE ---------------------------------------------------------
        if nodeType == 'ROUTE':
            routeNode = ROUTE()
            for key, val in nodeBody.items():
                if key.startswith('@'):
                    try:    setattr(routeNode, key[1:], val)
                    except Exception: pass
            return routeNode

        # ---- Instantiate the node ------------------------------------------
        nodeTuple = instantiateNodeFromString(nodeType)
        if nodeTuple is None or nodeTuple[0] is None:
            print(f'RKLoadSceneFromFile: unknown JSON node type "{nodeType}", skipping.')
            return None
        tNode = nodeTuple[0]

        # ---- USE shortcut --------------------------------------------------
        useVal = nodeBody.get('@USE')
        if useVal:
            tNode.USE = useVal
            return tNode

        # ---- Build field-type lookup for this node -------------------------
        ftMap = self._fieldTypeMap(type(tNode))

        for key, val in nodeBody.items():

            # ---- Scalar / vector attributes (@fieldName) -------------------
            if key.startswith('@'):
                attrName = key[1:]
                pName    = 'global_' if attrName == 'global' else attrName
                fType    = ftMap.get(pName)
                if fType is None or fType in ('SFNode', 'MFNode'):
                    continue
                try:
                    parsed = self._parseJSONValue(val, fType)
                    if fType == 'MFString' and pName.lower() == 'url':
                        parsed = self._resolveUrls(parsed)
                    setattr(tNode, pName, parsed)
                    if attrName == 'DEF':
                        self._defNodes[val] = tNode
                except Exception as exc:
                    print(f'RKLoadSceneFromFile: {nodeType}.{pName}: {exc}')

            # ---- Child nodes (-fieldName) ----------------------------------
            elif key.startswith('-'):
                fieldName = key[1:]
                if isinstance(val, list):
                    for childData in val:
                        childNode = self._parseJSONNode(childData)
                        if childNode is None:
                            continue
                        try:
                            existing = getattr(tNode, fieldName)
                            if isinstance(existing, list):
                                existing.append(childNode)
                            else:
                                setattr(tNode, fieldName, childNode)
                        except AttributeError:
                            print(f'RKLoadSceneFromFile: {nodeType} has no field "{fieldName}"')
                elif isinstance(val, dict):
                    childNode = self._parseJSONNode(val)
                    if childNode is not None:
                        try:    setattr(tNode, fieldName, childNode)
                        except AttributeError:
                            print(f'RKLoadSceneFromFile: {nodeType} has no field "{fieldName}"')

        return tNode

    # =======================================================================
    # Classic VRML (*.x3dv)
    # =======================================================================

    def _loadFromClassic(self, fullPath):
        with open(fullPath, 'r', encoding='utf-8') as f:
            text = f.read()

        self._classicTokens = self._tokenizeClassic(text)
        self._classicPos    = 0

        x3dDoc = X3D()

        # --- Parse header statements: PROFILE, COMPONENT, META -------------
        while self._classicPos < len(self._classicTokens):
            tok = self._classicPeek()

            if tok == 'PROFILE':
                self._classicConsume()
                try:    x3dDoc.profile = self._classicConsume()
                except Exception: pass

            elif tok == 'COMPONENT':
                self._classicConsume()
                compTok = self._classicConsume()    # "Name:level" or just "Name"
                # Handle both "Name:level" (no spaces) and "Name : level" (spaces)
                if ':' in compTok:
                    parts = compTok.split(':')
                    compName  = parts[0].strip()
                    compLevel = int(parts[1].strip()) if len(parts) > 1 else 1
                else:
                    compName = compTok
                    if self._classicPeek() == ':':
                        self._classicConsume()      # consume ':'
                    try:    compLevel = int(self._classicConsume())
                    except Exception: compLevel = 1
                compNode = component()
                try:    compNode.name  = compName
                except Exception: pass
                try:    compNode.level = compLevel
                except Exception: pass
                if x3dDoc.head is None:
                    x3dDoc.head = head()
                x3dDoc.head.children.append(compNode)

            elif tok == 'META':
                self._classicConsume()
                mName    = self._classicConsume().strip('"')
                mContent = self._classicConsume().strip('"')
                metaNode = meta()
                metaNode.name    = mName
                metaNode.content = mContent
                if x3dDoc.head is None:
                    x3dDoc.head = head()
                x3dDoc.head.children.append(metaNode)

            else:
                break   # start of scene-graph nodes

        # --- Parse Scene-level nodes ----------------------------------------
        sceneNode      = Scene()
        x3dDoc.Scene   = sceneNode
        while self._classicPos < len(self._classicTokens):
            node = self._parseClassicNode()
            if node is not None:
                sceneNode.children.append(node)

        print('RKLoadSceneFromFile: Classic file loaded.')
        return x3dDoc

    # --- Tokenizer ----------------------------------------------------------

    def _tokenizeClassic(self, text):
        """
        Tokenize an X3D Classic (VRML) source into a flat token list.

        Rules:
          - # to end-of-line is a comment and is discarded.
          - Quoted strings (including their delimiters) become single tokens.
          - Commas and whitespace are discarded.
          - [ ] { } each become individual tokens.
        """
        tokens = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c == '#':                        # line comment
                while i < n and text[i] != '\n':
                    i += 1
            elif c == '"':                      # quoted string (single token)
                j = i + 1
                while j < n:
                    if text[j] == '\\':
                        j += 2
                        continue
                    if text[j] == '"':
                        j += 1
                        break
                    j += 1
                tokens.append(text[i:j])
                i = j
            elif c in ' \t\r\n,':              # whitespace / comma
                i += 1
            elif c in '[]{}':                  # structural characters
                tokens.append(c)
                i += 1
            else:                              # bare identifier or number
                j = i
                while j < n and text[j] not in ' \t\r\n,[]{}#"':
                    j += 1
                tokens.append(text[i:j])
                i = j
        return tokens

    def _classicPeek(self, offset=0):
        idx = self._classicPos + offset
        return self._classicTokens[idx] if idx < len(self._classicTokens) else None

    def _classicConsume(self):
        tok = self._classicTokens[self._classicPos]
        self._classicPos += 1
        return tok

    # --- Node parser --------------------------------------------------------

    def _parseClassicNode(self):
        """Parse one node (DEF/USE/ROUTE/bare) from the token stream."""
        if self._classicPos >= len(self._classicTokens):
            return None

        tok = self._classicPeek()

        # ---- ROUTE ---------------------------------------------------------
        if tok == 'ROUTE':
            return self._parseClassicRoute()

        # ---- DEF -----------------------------------------------------------
        nodeName = ''
        if tok == 'DEF':
            self._classicConsume()          # consume 'DEF'
            # The exporter may write "DEF  NodeType {" when DEF='' (empty).
            # That tokenises identically to "DEF NodeType {".
            # Distinguish by checking whether the next token is a known node
            # type followed immediately by '{'.
            peek1 = self._classicPeek()
            peek2 = self._classicPeek(1)
            testTuple = instantiateNodeFromString(peek1) if peek1 else None
            if testTuple is not None and testTuple[0] is not None and peek2 == '{':
                nodeName = ''               # empty DEF; peek1 is the node type
            else:
                nodeName = self._classicConsume()   # actual DEF name

        # ---- USE -----------------------------------------------------------
        elif tok == 'USE':
            self._classicConsume()          # consume 'USE'
            useTarget = self._classicConsume()
            existing  = self._defNodes.get(useTarget)
            if existing is not None:
                useNode     = instantiateNodeFromString(type(existing).__name__)[0]
                useNode.USE = useTarget
                return useNode
            return None

        # ---- NodeType { ... } ----------------------------------------------
        nodeType  = self._classicConsume()
        if nodeType is None:
            return None

        nodeTuple = instantiateNodeFromString(nodeType)
        if nodeTuple is None or nodeTuple[0] is None:
            print(f'RKLoadSceneFromFile: unknown Classic node type "{nodeType}", skipping.')
            self._skipClassicBlock()
            return None

        tNode = nodeTuple[0]
        if nodeName:
            tNode.DEF = nodeName
            self._defNodes[nodeName] = tNode

        # Expect opening brace
        openBrace = self._classicConsume()
        if openBrace != '{':
            print(f'RKLoadSceneFromFile: expected "{{" after "{nodeType}", got "{openBrace}"')
            return tNode

        ftMap = self._fieldTypeMap(type(tNode))

        # --- Parse field assignments until closing brace -------------------
        while self._classicPos < len(self._classicTokens):
            tok = self._classicPeek()
            if tok == '}':
                self._classicConsume()
                break

            fieldName = self._classicConsume()
            if fieldName is None:
                break
            pName = 'global_' if fieldName == 'global' else fieldName
            fType = ftMap.get(pName)

            if fType is None:
                # Unknown field – skip its value and continue
                self._skipClassicFieldValue()
                continue

            if fType == 'SFNode':
                childNode = self._parseClassicNode()
                if childNode is not None:
                    try:    setattr(tNode, pName, childNode)
                    except Exception as exc:
                        print(f'RKLoadSceneFromFile: {nodeType}.{pName}: {exc}')

            elif fType == 'MFNode':
                if self._classicPeek() == '[':
                    self._classicConsume()  # '['
                    while (self._classicPos < len(self._classicTokens)
                           and self._classicPeek() != ']'):
                        childNode = self._parseClassicNode()
                        if childNode is not None:
                            try:
                                existing = getattr(tNode, pName)
                                if isinstance(existing, list):
                                    existing.append(childNode)
                            except Exception as exc:
                                print(f'RKLoadSceneFromFile: {nodeType}.{pName}: {exc}')
                    if self._classicPeek() == ']':
                        self._classicConsume()
                else:
                    # Single node without brackets
                    childNode = self._parseClassicNode()
                    if childNode is not None:
                        try:
                            existing = getattr(tNode, pName)
                            if isinstance(existing, list):
                                existing.append(childNode)
                        except Exception: pass

            elif fType.startswith('MF'):
                # Collect all raw tokens for this MF value then parse
                rawToks = self._readClassicMFTokens()
                try:
                    setattr(tNode, pName,
                            self._parseStrValue(' '.join(rawToks), fType))
                except Exception as exc:
                    print(f'RKLoadSceneFromFile: {nodeType}.{pName}: {exc}')

            else:
                # SF field – may require multiple consecutive tokens (e.g. SFVec3f)
                rawStr = self._readClassicSFTokens(fType)
                try:
                    setattr(tNode, pName, self._parseStrValue(rawStr, fType))
                except Exception as exc:
                    print(f'RKLoadSceneFromFile: {nodeType}.{pName}: {exc}')

        return tNode

    def _parseClassicRoute(self):
        """Parse  ROUTE fromNode.fromField TO toNode.toField"""
        self._classicConsume()              # 'ROUTE'
        fromPart = self._classicConsume()   # "NodeDEF.fieldName"
        self._classicConsume()              # 'TO'
        toPart   = self._classicConsume()   # "NodeDEF.fieldName"

        routeNode = ROUTE()
        fp = fromPart.split('.')
        tp = toPart.split('.')
        if len(fp) == 2:
            routeNode.fromNode  = fp[0]
            routeNode.fromField = fp[1]
        if len(tp) == 2:
            routeNode.toNode  = tp[0]
            routeNode.toField = tp[1]
        return routeNode

    def _readClassicMFTokens(self):
        """Collect all raw tokens that make up one MF field value."""
        tokens = []
        if self._classicPeek() == '[':
            self._classicConsume()  # '['
            while (self._classicPos < len(self._classicTokens)
                   and self._classicPeek() != ']'):
                tokens.append(self._classicConsume())
            if self._classicPeek() == ']':
                self._classicConsume()
        else:
            # Bare single value (no brackets – unusual but handle it)
            t = self._classicConsume()
            if t is not None:
                tokens.append(t)
        return tokens

    def _readClassicSFTokens(self, fType):
        """
        Read one or more consecutive tokens that together represent a single
        SF value (e.g. three tokens for SFVec3f) and return them joined as a
        single space-separated string.
        """
        _SF_WIDTHS = {
            'SFVec2f':    2, 'SFVec2d':    2,
            'SFVec3f':    3, 'SFVec3d':    3, 'SFColor':     3,
            'SFVec4f':    4, 'SFVec4d':    4, 'SFRotation':  4, 'SFColorRGBA': 4,
            'SFMatrix3f': 9, 'SFMatrix3d': 9,
            'SFMatrix4f': 16,'SFMatrix4d': 16,
        }
        n = _SF_WIDTHS.get(fType, 1)
        parts = []
        for _ in range(n):
            t = self._classicConsume()
            if t is None:
                break
            parts.append(t)
        return ' '.join(parts)

    def _skipClassicBlock(self):
        """Skip past one complete { ... } block (for unknown node types)."""
        depth = 0
        # Consume the opening '{' if it is next
        if self._classicPeek() == '{':
            self._classicConsume()
            depth = 1
        while self._classicPos < len(self._classicTokens):
            tok = self._classicConsume()
            if tok == '{':
                depth += 1
            elif tok == '}':
                depth -= 1
                if depth <= 0:
                    break

    def _skipClassicFieldValue(self):
        """Skip the value tokens of an unrecognised field."""
        tok = self._classicPeek()
        if tok == '[':
            self._classicConsume()
            while (self._classicPos < len(self._classicTokens)
                   and self._classicPeek() != ']'):
                self._classicConsume()
            if self._classicPeek() == ']':
                self._classicConsume()
        else:
            self._classicConsume()
