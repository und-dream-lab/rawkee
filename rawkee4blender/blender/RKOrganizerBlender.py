"""
RawKee Blender — Core scene-traversal / export engine.

Maya equivalent  : rawkee/maya/RKOrganizer.py

Blender approach : Traverses Blender's collection hierarchy and object graph,
                   maps each Blender object type to an X3D node, and populates
                   the RKx3d object tree consumed by RKSceneTraversal.

Supported object mappings
--------------------------
MESH            → Transform > Shape > IndexedFaceSet (+ Appearance/Material)
ARMATURE        → HAnimHumanoid + HAnimJoint chain (when rk_hanim_humanoid=True)
                  or Transform > Group for plain armatures
LIGHT           → DirectionalLight / PointLight / SpotLight
CAMERA          → Viewpoint
SPEAKER         → Sound > AudioClip
EMPTY           → Group (or Sound / AnimPack if custom property present)
Collections     → Group nodes (hierarchy preserved)

Coordinate conversion
----------------------
Blender uses a Z-up, right-handed coordinate system.
X3D  uses a Y-up, right-handed coordinate system.
The global axis-conversion matrix _AX is applied to every world-space matrix
so that exported coordinates are correct in the X3D viewer.
"""

import bpy
import math
import mathutils
import os
import sys
import shutil

from rawkee.io.RKSceneTraversal import RKSceneTraversal
from rawkee.io.RKx3d import *
from rawkee.tools.RKTools         import RKTools

# ---------------------------------------------------------------------------
#  Axis-conversion matrix  Blender Z-up → X3D Y-up
# ---------------------------------------------------------------------------
_AX = mathutils.Matrix((
    (1,  0,  0,  0),
    (0,  0,  1,  0),
    (0, -1,  0,  0),
    (0,  0,  0,  1),
))

_ZERO_VEC = (0.0, 0.0, 0.0)
_ONE_VEC  = (1.0, 1.0, 1.0)
_IDENTITY_ROT = (0.0, 0.0, 1.0, 0.0)

# Camera correction matrix: R_x(-90°)
# Calibration: Blender rotation R_x(+90°) is visually equivalent to the
# default X3D Viewpoint orientation (0 0 1 0).  Therefore the correction
# must satisfy  _CAM_CORR @ R_x(90°) = I  →  _CAM_CORR = R_x(-90°).
_CAM_CORR = mathutils.Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))


def _world_mat(obj):
    """Return the world matrix of obj converted to X3D (Y-up) space."""
    return _AX @ obj.matrix_world


def _local_mat(obj):
    """Local matrix relative to parent, already in X3D space if parent converted."""
    if obj.parent is None:
        return _world_mat(obj)
    return obj.matrix_local


def _decompose(mat):
    """Return (translation, axis_angle_rotation, scale) from a 4x4 matrix."""
    loc, rot, sca = mat.decompose()
    ax, ang = rot.to_axis_angle()
    if ax.length < 1e-8:
        ax  = mathutils.Vector((0.0, 0.0, 1.0))
        ang = 0.0
    return (
        (loc.x, loc.y, loc.z),
        (ax.x, ax.y, ax.z, ang),
        (sca.x, sca.y, sca.z),
    )


def _safe_name(name):
    """Return an X3D-legal DEF name from a Blender object name."""
    return name.replace(' ', '_').replace('.', '_').replace(':', '_')


def _rk_log(msg):
    print(msg)


# ---------------------------------------------------------------------------
#  Main class
# ---------------------------------------------------------------------------

class RKOrganizerBlender:
    """
    Blender counterpart to RKOrganizer (Maya).  Drives RKSceneTraversal to
    produce an X3D document tree from the active Blender scene.
    """

    def __init__(self):
        self.trv = RKSceneTraversal()

        # Export option mirrors (loaded from scene.rk_export_opts in prepForSceneTraversal)
        self.rkPrjDir        = ""
        self.rkImagePath     = "images/"
        self.rkAudioPath     = "audio/"
        self.rkInlinePath    = "inline/"
        self.rkMatXPath      = "mtlx/"
        self.rkUseHAnimSites = False
        self.rkSkinInfluence = 0
        self.rkAdjTexSize    = False
        self.rkDefTexWidth   = 256
        self.rkDefTexHeight  = 256
        self.rkConsolidate         = True
        self.rkConvertHDRToKTX2   = True
        self.rkMaxCubeMapFaceSize  = 4096
        self.rkProcTexType         = 0
        self.rkProcTexFormat = 0
        self.rkFileTexType   = 0
        self.rkFileTexFormat = 0
        self.rkMovieTexType  = 0
        self.rkAudioClipType = 0
        self.rkNormalOpts    = 0
        self.rkCreaseAngle   = 0.0
        self.rkColorOpts     = 0
        self.rkIsTriangles   = False
        self.rkFDecimalLimit = 6
        self.rkExportTangents = False
        self.rkExportEmpties = True
        self.rkExportMetadata = True
        self.rkExportAnimations = True
        self.exEncoding      = "x3d"

        # Internal state
        self.haveBeenObjects = {}
        self.animation_data  = []   # list of (x3d_timer, x3d_interps, routes)
        self.imageMoveDir    = ""
        self.audioMoveDir    = ""
        self.fullPath        = ""
        self.exportedTextures = {}  # src_path → dest_relative_url


    # -----------------------------------------------------------------------
    #  Option loading  (mirrors RKOrganizer.loadRawKeeOptions)
    # -----------------------------------------------------------------------

    def prepForSceneTraversal(self, context=None):
        """Load export options from the active scene's PropertyGroup."""
        if context is None:
            context = bpy.context
        opts = context.scene.rk_export_opts

        self.rkPrjDir        = opts.prj_dir
        # Normalize sub-paths: replace backslashes with forward slashes
        self.rkImagePath  = opts.image_path.replace('\\', '/')
        self.rkAudioPath  = opts.audio_path.replace('\\', '/')
        self.rkInlinePath = opts.inline_path.replace('\\', '/')
        self.rkMatXPath   = opts.matx_path.replace('\\', '/')
        self.rkUseHAnimSites = opts.use_hanim_sites
        self.rkSkinInfluence = int(opts.skin_influence)
        self.rkAdjTexSize    = opts.adj_tex_size
        self.rkDefTexWidth   = opts.tex_width
        self.rkDefTexHeight  = opts.tex_height
        self.rkConsolidate        = opts.consolidate
        self.rkConvertHDRToKTX2  = opts.convert_hdr_to_ktx2
        self.rkMaxCubeMapFaceSize = opts.max_cube_map_face_size
        self.rkProcTexType        = int(opts.proc_tex_type)
        self.rkProcTexFormat = int(opts.proc_tex_format)
        self.rkFileTexType   = int(opts.file_tex_type)
        self.rkFileTexFormat = int(opts.file_tex_format)
        self.rkMovieTexType  = int(opts.movie_tex_type)
        self.rkAudioClipType = int(opts.audio_clip_type)
        self.rkNormalOpts    = int(opts.normal_opts)
        self.rkCreaseAngle   = opts.crease_angle
        self.rkColorOpts     = int(opts.color_opts)
        self.rkIsTriangles   = opts.is_triangles
        self.rkFDecimalLimit = opts.decimal_limit
        self.rkExportTangents = opts.export_tangents
        self.rkExportEmpties  = opts.export_empties
        self.rkExportMetadata = opts.export_metadata
        self.rkExportAnimations = opts.export_animations

        self.trv.setDecimalPlaces(self.rkFDecimalLimit)


    # -----------------------------------------------------------------------
    #  Helpers
    # -----------------------------------------------------------------------

    def checkSubDirs(self, fullPath):
        """Create sub-directories for consolidated media next to the output file."""
        base = os.path.dirname(fullPath)
        self.imageMoveDir = os.path.normpath(os.path.join(base, self.rkImagePath))
        self.audioMoveDir = os.path.normpath(os.path.join(base, self.rkAudioPath))
        if self.rkConsolidate:
            os.makedirs(self.imageMoveDir, exist_ok=True)
            os.makedirs(self.audioMoveDir, exist_ok=True)


    def _copy_texture(self, src_abs, base_dir):
        """Copy a texture to the image sub-dir and return the relative URL."""
        if src_abs in self.exportedTextures:
            return self.exportedTextures[src_abs]
        if not os.path.isfile(src_abs):
            return src_abs
        fname   = os.path.basename(src_abs)
        dst_abs = os.path.join(self.imageMoveDir, fname)
        if src_abs != dst_abs:
            try:
                shutil.copy2(src_abs, dst_abs)
            except Exception as e:
                print(f"RKOrganizerBlender: texture copy failed: {e}")
        rel_url = self.rkImagePath + fname  # rkImagePath is already normalised, e.g. "images/"
        self.exportedTextures[src_abs] = rel_url
        return rel_url


    # -----------------------------------------------------------------------
    #  Entry points
    # -----------------------------------------------------------------------

    def blender2x3d(self, x3dScene, context, fullPath, exEncoding):
        """
        Main conversion method.  Mirrors RKOrganizer.maya2x3d().
        Traverses the Blender scene, populates x3dScene, then collects
        animation data.
        """
        self.exEncoding = exEncoding
        self.fullPath   = fullPath
        self.checkSubDirs(fullPath)
        self.haveBeenObjects.clear()
        self.animation_data.clear()
        self.exportedTextures.clear()

        # Reset the in-Blender log for this export run
        try:
            if _RK_LOG_NAME in bpy.data.texts:
                bpy.data.texts[_RK_LOG_NAME].clear()
            else:
                bpy.data.texts.new(_RK_LOG_NAME)
        except Exception:
            pass

        # Mark pseudo-root
        self.trv.setAsHasBeen("BlenderScene", x3dScene)

        # World environment texture → EnvironmentLight
        self._process_world_environment(x3dScene, context)

        # Traverse scene collection hierarchy
        self._traverse_collection(x3dScene, context.scene.collection, context, is_root=True)

        # Collect all object-level animations after geometry
        if self.rkExportAnimations:
            self._collect_animation_data(x3dScene, context)

        # Generator metatag
        self.trv.x3dVersion = "4.1"
        self.trv.metatags.append({
            "name": "generator",
            "content": (
                "RawKee X3D Exporter for Blender 5 [Python Edition], "
                "https://github.com/und-dream-lab/rawkee/"
            )
        })

        # Profile / component selection
        compLen = len(self.trv.profDict)
        if   compLen >= 36: self.trv.evaluateForFull()
        elif compLen >= 20: self.trv.evaluateForImmersive()
        elif compLen >= 16: self.trv.evaluateForInteractive()
        elif compLen >= 14: self.trv.evaluateForMP4Interactive()
        elif compLen >= 12: self.trv.evaluateForInterchange()
        elif compLen >= 10: self.trv.evaluateForCADInterchange()
        else:               self.trv.evaluateForCore()
        self.trv.setAdditionalComponents()


    def blender2x3d_selected(self, x3dScene, context, fullPath, exEncoding):
        """Export only selected objects."""
        self.exEncoding = exEncoding
        self.fullPath   = fullPath
        self.checkSubDirs(fullPath)
        self.haveBeenObjects.clear()
        self.animation_data.clear()
        self.exportedTextures.clear()

        # Reset the in-Blender log for this export run
        try:
            if _RK_LOG_NAME in bpy.data.texts:
                bpy.data.texts[_RK_LOG_NAME].clear()
            else:
                bpy.data.texts.new(_RK_LOG_NAME)
        except Exception:
            pass
        self.trv.setAsHasBeen("BlenderScene", x3dScene)

        for obj in context.selected_objects:
            if obj.parent is None or obj.parent not in context.selected_objects:
                self._process_object(x3dScene, obj, context, is_root=True)

        if self.rkExportAnimations:
            self._collect_animation_data(x3dScene, context)

        self.trv.x3dVersion = "4.1"
        self.trv.metatags.append({
            "name": "generator",
            "content": (
                "RawKee X3D Exporter for Blender 5 [Python Edition] (selected), "
                "https://github.com/und-dream-lab/rawkee/"
            )
        })
        compLen = len(self.trv.profDict)
        if   compLen >= 36: self.trv.evaluateForFull()
        elif compLen >= 20: self.trv.evaluateForImmersive()
        elif compLen >= 12: self.trv.evaluateForInterchange()
        else:               self.trv.evaluateForCore()
        self.trv.setAdditionalComponents()


    # -----------------------------------------------------------------------
    #  Collection traversal
    # -----------------------------------------------------------------------

    def _traverse_collection(self, x3dParent, collection, context, is_root=False):
        """Recursively export a Blender collection as an X3D Group."""
        # The scene root collection itself is not exported as a Group node
        if not is_root:
            grp = self.trv.processBasicNodeAddition(
                x3dParent, "children", "Group", _safe_name(collection.name)
            )
            if grp is None:
                return
            x3dTarget = grp
        else:
            x3dTarget = x3dParent

        # Objects directly inside this collection (only those without parents
        # reversed() matches the outliner top-to-bottom display order
        for obj in reversed(list(collection.objects)):
            if obj.parent is None or obj.parent not in collection.objects:
                self._process_object(x3dTarget, obj, context, is_root=is_root)

        # Recurse into child collections
        for child_col in collection.children:
            self._traverse_collection(x3dTarget, child_col, context, is_root=False)


    # -----------------------------------------------------------------------
    #  Object dispatch
    # -----------------------------------------------------------------------

    def _process_object(self, x3dParent, obj, context, is_root=False):
        """Dispatch an object to the correct handler based on type and flags."""
        if obj.hide_render:
            return
        if obj.name in self.haveBeenObjects:
            # Instanced — emit a USE reference
            usedNode = self.trv.getGeneratedX3DAsUsed(_safe_name(obj.name))
            if usedNode is not None:
                nodeField = getattr(x3dParent, "children")
                if isinstance(nodeField, list):
                    nodeField.append(usedNode)
            return

        # ---- Custom-node approximations ----
        if obj.get("rk_x3d_type") == "Sound":
            self._process_x3d_sound(x3dParent, obj, context)
            return
        if bool(obj.get("rk_anim_pack")):
            self._process_anim_pack(x3dParent, obj, context)
            return

        # ---- Standard Blender types ----
        if obj.type == 'MESH':
            self._process_mesh(x3dParent, obj, context, is_root)
        elif obj.type == 'ARMATURE':
            if obj.get("rk_hanim_humanoid"):
                self._process_hanim_humanoid(x3dParent, obj, context, is_root)
            else:
                self._process_empty(x3dParent, obj, context, is_root)
        elif obj.type == 'LIGHT':
            self._process_light(x3dParent, obj, context, is_root)
        elif obj.type == 'CAMERA':
            self._process_camera(x3dParent, obj, context, is_root)
        elif obj.type == 'SPEAKER':
            self._process_speaker(x3dParent, obj, context, is_root)
        elif obj.type == 'EMPTY':
            self._process_empty(x3dParent, obj, context, is_root)
        # Other types (curves, metaballs, etc.) are skipped for now


    # -----------------------------------------------------------------------
    #  Transform wrapper helper
    # -----------------------------------------------------------------------

    def _make_transform(self, x3dParent, obj, is_root):
        """Create an X3D Transform from obj's matrix, converted to X3D Y-up."""
        # Use world matrix for root objects, local matrix for children
        mat_blender = obj.matrix_world if is_root else obj.matrix_local
        # Conjugate by _AX to convert Blender Z-up to X3D Y-up:
        #   _AX @ M @ _AX_inv  preserves composition:  _b(A)@_b(B) == _b(A@B)
        mat_x3d = _AX @ mat_blender @ _AX.inverted()
        loc, rot, sca = _decompose(mat_x3d)
        defName = _safe_name(obj.name)
        tfm = self.trv.processBasicNodeAddition(
            x3dParent, "children", "Transform", defName
        )
        if tfm is None:
            return None
        self.haveBeenObjects[obj.name] = True
        tfm.translation = loc
        tfm.rotation    = rot
        tfm.scale       = sca
        return tfm


    # -----------------------------------------------------------------------
    #  MESH handler
    # -----------------------------------------------------------------------

    def _process_mesh(self, x3dParent, obj, context, is_root):
        tfm = self._make_transform(x3dParent, obj, is_root)
        if tfm is None:
            return

        # Children of this object
        for child in obj.children:
            self._process_object(tfm, child, context, is_root=False)

        # Evaluate mesh (apply modifiers)
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval  = obj.evaluated_get(depsgraph)
        mesh      = obj_eval.to_mesh()
        if mesh is None:
            return

        # Triangulate if requested
        if self.rkIsTriangles:
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            bm.to_mesh(mesh)
            bm.free()

        mesh.calc_loop_triangles()
        # calc_normals_split() was removed in Blender 4.1; loop normals are
        # always available on mesh.loops[i].normal in 4.1+.
        if hasattr(mesh, 'calc_normals_split'):
            mesh.calc_normals_split()

        # One Shape per material slot (or one if no materials)
        mats = mesh.materials if mesh.materials else [None]
        n_mats = max(len(mats), 1)

        for mat_idx in range(n_mats):
            shape_name = _safe_name(obj.name) + "_Shape" + (
                "" if n_mats == 1 else f"_{mat_idx}"
            )
            shape = self.trv.processBasicNodeAddition(
                tfm, "children", "Shape", shape_name
            )
            if shape is None:
                continue

            mat = mats[mat_idx] if mat_idx < len(mats) else None
            self._process_material(shape, mat, obj)
            self._build_ifs(shape, mesh, mat_idx, n_mats, obj)

        obj_eval.to_mesh_clear()


    def _build_ifs(self, x3dShape, mesh, mat_idx, n_mats, obj):
        """Build an IndexedFaceSet from mesh data for a given material slot."""
        # Collect faces for this material
        poly_indices = []
        for poly in mesh.polygons:
            if n_mats <= 1 or poly.material_index == mat_idx:
                poly_indices.append(poly.index)

        if not poly_indices:
            return

        # Vertices – convert Blender Z-up (x,y,z) to X3D Y-up (x,z,−y)
        verts = [(v.co.x, v.co.z, -v.co.y) for v in mesh.vertices]

        # Build coordIndex
        coordIndex = []
        for pi in poly_indices:
            poly = mesh.polygons[pi]
            for vi in poly.vertices:
                coordIndex.append(vi)
            coordIndex.append(-1)

        ifs_name = _safe_name(obj.name) + "_IFS" + (
            "" if n_mats <= 1 else f"_{mat_idx}"
        )
        ifs = self.trv.processBasicNodeAddition(
            x3dShape, "geometry", "IndexedFaceSet", ifs_name
        )
        if ifs is None:
            return

        ifs.coordIndex   = coordIndex
        ifs.creaseAngle  = self.rkCreaseAngle
        ifs.solid        = False

        # Coordinate node
        coord = self.trv.processBasicNodeAddition(
            ifs, "coord", "Coordinate", ifs_name + "_Coord"
        )
        if coord:
            coord.point = verts

        # Normals
        if self.rkNormalOpts == 0:
            normal_vecs = []
            normalIndex = []
            loop_idx    = 0
            for pi in poly_indices:
                poly = mesh.polygons[pi]
                for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    ln = mesh.loops[li].normal
                    # Normals: same Z-up → Y-up remapping as vertex positions
                    normal_vecs.append((ln.x, ln.z, -ln.y))
                    normalIndex.append(loop_idx)
                    loop_idx += 1
                normalIndex.append(-1)
            norm = self.trv.processBasicNodeAddition(
                ifs, "normal", "Normal", ifs_name + "_Normal"
            )
            if norm:
                norm.vector = normal_vecs
            ifs.normalIndex = normalIndex
            ifs.normalPerVertex = True

        # UV coordinates
        if mesh.uv_layers.active:
            uv_vecs  = []
            texIndex = []
            uv_layer = mesh.uv_layers.active.data
            loop_idx = 0
            for pi in poly_indices:
                poly = mesh.polygons[pi]
                for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    uv = uv_layer[li].uv
                    uv_vecs.append((uv.x, uv.y))
                    texIndex.append(loop_idx)
                    loop_idx += 1
                texIndex.append(-1)
            tc = self.trv.processBasicNodeAddition(
                ifs, "texCoord", "TextureCoordinate", ifs_name + "_TexCoord"
            )
            if tc:
                tc.point = uv_vecs
            ifs.texCoordIndex = texIndex

        # Vertex colors
        if self.rkColorOpts == 1 and mesh.color_attributes.active_color:
            col_attr = mesh.color_attributes.active_color.data
            colors   = []
            colIndex = []
            loop_idx = 0
            for pi in poly_indices:
                poly = mesh.polygons[pi]
                for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    c = col_attr[li].color
                    colors.append((c[0], c[1], c[2]))
                    colIndex.append(loop_idx)
                    loop_idx += 1
                colIndex.append(-1)
            color_node = self.trv.processBasicNodeAddition(
                ifs, "color", "Color", ifs_name + "_Color"
            )
            if color_node:
                color_node.color = colors
            ifs.colorIndex = colIndex
            ifs.colorPerVertex = True


    # -----------------------------------------------------------------------
    #  Material / Appearance handler
    # -----------------------------------------------------------------------

    def _process_material(self, x3dShape, mat, obj):
        """Build Appearance > PhysicalMaterial (or Material) + ImageTexture."""
        app_name = _safe_name(obj.name) + "_App" + (
            ("_" + _safe_name(mat.name)) if mat else ""
        )
        app = self.trv.processBasicNodeAddition(
            x3dShape, "appearance", "Appearance", app_name
        )
        if app is None:
            return
        if mat is None:
            # Default grey material
            pm = self.trv.processBasicNodeAddition(
                app, "material", "Material", app_name + "_DefaultMat"
            )
            if pm:
                pm.diffuseColor = (0.8, 0.8, 0.8)
            return

        # Try to detect a Principled BSDF node, then fall back to the
        # glTF Metallic Roughness node group (same PhysicalMaterial output).
        pbsdf    = None
        gltf_mr  = None
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    pbsdf = node
                elif (node.type == 'GROUP'
                      and node.node_tree is not None
                      and node.node_tree.name == 'glTF Metallic Roughness'):
                    gltf_mr = node

        # Prefer Principled BSDF; fall back to glTF MR; then legacy Material.
        shader_node   = pbsdf or gltf_mr
        as_x3d_shader = bool(mat.get("rk_as_x3d_shader", False))
        if shader_node is not None:
            if as_x3d_shader:
                self._build_packaged_composed_shader(app, mat, shader_node, app_name,
                                                     is_gltf_mr=(pbsdf is None))
            else:
                self._build_physical_material_ext(app, mat, shader_node, app_name,
                                                  is_gltf_mr=(pbsdf is None))
        else:
            # Fallback: use diffuse colour directly
            pm = self.trv.processBasicNodeAddition(
                app, "material", "Material", app_name + "_Mat"
            )
            if pm:
                dc = mat.diffuse_color
                pm.diffuseColor = (dc[0], dc[1], dc[2])


    def _get_pbsdf_input_value(self, pbsdf, socket_name):
        """Return the default_value of a Principled BSDF socket, or None."""
        sock = pbsdf.inputs.get(socket_name)
        if sock is None:
            return None
        return sock.default_value


    def _find_image_texture(self, node_tree, socket_name, pbsdf):
        """Trace the link on pbsdf's socket_name back to an Image Texture node."""
        sock = pbsdf.inputs.get(socket_name)
        if sock is None or not sock.links:
            return None
        link = sock.links[0]
        from_node = link.from_node
        if from_node.type == 'TEX_IMAGE':
            return from_node
        # One level deeper (e.g. through a NormalMap node)
        for inp in from_node.inputs:
            if inp.links:
                n2 = inp.links[0].from_node
                if n2.type == 'TEX_IMAGE':
                    return n2
        return None


    def _build_physical_material_ext(self, x3dApp, mat, pbsdf, base_name,
                                      is_gltf_mr=False):
        """Map Principled BSDF or glTF MR inputs to X3D PhysicalMaterialExt + glTF extensions."""
        pm = self.trv.processBasicNodeAddition(
            x3dApp, "material", "PhysicalMaterialExt", base_name + "_PhysMatExt"
        )
        if pm is None:
            return

        # glTF MR group uses different socket names from Principled BSDF
        base_col_sock = "BaseColorFactor"  if is_gltf_mr else "Base Color"
        metal_sock    = "MetallicFactor"   if is_gltf_mr else "Metallic"
        rough_sock    = "RoughnessFactor"  if is_gltf_mr else "Roughness"

        # Base color
        base_col = self._get_pbsdf_input_value(pbsdf, base_col_sock)
        if base_col:
            pm.baseColor = (base_col[0], base_col[1], base_col[2])

        # Metallic / roughness scalars
        metal = self._get_pbsdf_input_value(pbsdf, metal_sock)
        if metal is not None:
            pm.metallic = float(metal)

        rough = self._get_pbsdf_input_value(pbsdf, rough_sock)
        if rough is not None:
            pm.roughness = float(rough)

        # Emissive color — do NOT pre-multiply by strength; extension handles that
        if is_gltf_mr:
            em_col = self._get_pbsdf_input_value(pbsdf, "Emissive")
            if em_col:
                pm.emissiveColor = (float(em_col[0]), float(em_col[1]), float(em_col[2]))
        else:
            # 4.x renamed "Emission" → "Emission Color"
            em_sock = pbsdf.inputs.get("Emission Color") or pbsdf.inputs.get("Emission")
            if em_sock:
                ec = em_sock.default_value
                em_c = (float(ec[0]), float(ec[1]), float(ec[2]))
                if any(v > 0.001 for v in em_c):
                    pm.emissiveColor = em_c

        # Transparency
        alpha = self._get_pbsdf_input_value(pbsdf, "Alpha")
        if alpha is not None and float(alpha) < 0.999:
            pm.transparency = 1.0 - float(alpha)

        # ---- Textures ------------------------------------------------
        print(f"[RawKee] _build_physical_material_ext: shader='{pbsdf.name}' "
              f"type={pbsdf.type} is_gltf_mr={is_gltf_mr}")
        for s in pbsdf.inputs:
            linked = len(s.links) > 0
            from_t = s.links[0].from_node.type if linked else 'none'
            _rk_log(f"[RawKee]   socket '{s.name}': linked={linked} from_type={from_t}")

        # Base color texture (glTF MR: "BaseColor"; Principled BSDF: "Base Color")
        base_tex_sock = "BaseColor" if is_gltf_mr else "Base Color"
        img = self._find_image_texture(mat.node_tree, base_tex_sock, pbsdf)
        _rk_log(f"[RawKee]   _find_image_texture({base_tex_sock!r}) -> {img}")
        if img and img.image:
            _rk_log(f"[RawKee]   image.name={img.image.name!r}  filepath={img.image.filepath!r}"
                  f"  packed={img.image.packed_file is not None}")
            self._make_image_texture(pm, "baseTexture", img.image, base_name + "_BaseTex")

        # Metallic-roughness texture
        if is_gltf_mr:
            mr = self._find_image_texture(mat.node_tree, "MetallicRoughness", pbsdf)
        else:
            mr = (self._find_image_texture(mat.node_tree, "Metallic", pbsdf) or
                  self._find_image_texture(mat.node_tree, "Roughness", pbsdf))
        if mr and mr.image:
            self._make_image_texture(pm, "metallicRoughnessTexture", mr.image,
                                     base_name + "_MRTex")

        # Normal map
        nm = self._find_image_texture(mat.node_tree, "Normal", pbsdf)
        if nm and nm.image:
            self._make_image_texture(pm, "normalTexture", nm.image, base_name + "_NormTex")

        # Emissive texture — override emissiveColor to white when a texture is present
        em_tex_sock = ("Emissive" if is_gltf_mr
                       else ("Emission Color" if pbsdf.inputs.get("Emission Color") else "Emission"))
        em_tex = self._find_image_texture(mat.node_tree, em_tex_sock, pbsdf)
        if em_tex and em_tex.image:
            pm.emissiveColor = (1.0, 1.0, 1.0)
            self._make_image_texture(pm, "emissiveTexture", em_tex.image, base_name + "_EmissTex")

        # Occlusion texture
        occ = self._find_image_texture(mat.node_tree, "Occlusion", pbsdf)
        if occ and occ.image:
            self._make_image_texture(pm, "occlusionTexture", occ.image, base_name + "_OccTex")

        # ---- glTF material extensions (Principled BSDF only) ---------
        if is_gltf_mr:
            return

        # IOR (KHR_materials_ior) — only when not the default 1.5
        ior_val = self._get_pbsdf_input_value(pbsdf, "IOR")
        if ior_val is not None and abs(float(ior_val) - 1.5) > 0.001:
            ior_ext = self.trv.processBasicNodeAddition(
                pm, "extensions", "IORMaterialExtension", base_name + "_IORME")
            if ior_ext:
                ior_ext.indexOfRefraction = float(ior_val)

        # Emissive strength (KHR_materials_emissive_strength) — only when != 1.0
        em_str_sock = pbsdf.inputs.get("Emission Strength")
        if em_str_sock:
            es = float(em_str_sock.default_value)
            if abs(es - 1.0) > 0.001:
                es_ext = self.trv.processBasicNodeAddition(
                    pm, "extensions", "EmissiveStrengthMaterialExtension", base_name + "_ESME")
                if es_ext:
                    es_ext.emissiveStrength = es

        # Transmission (KHR_materials_transmission)
        trans_sock = (pbsdf.inputs.get("Transmission Weight") or  # 4.x
                      pbsdf.inputs.get("Transmission"))           # 3.x
        if trans_sock:
            tv = float(trans_sock.default_value)
            if tv > 0.001:
                tr_ext = self.trv.processBasicNodeAddition(
                    pm, "extensions", "TransmissionMaterialExtension", base_name + "_TRME")
                if tr_ext:
                    tr_ext.transmission = tv
                    tr_tex = (self._find_image_texture(mat.node_tree, "Transmission Weight", pbsdf) or
                              self._find_image_texture(mat.node_tree, "Transmission",        pbsdf))
                    if tr_tex and tr_tex.image:
                        self._make_image_texture(tr_ext, "transmissionTexture",
                                                  tr_tex.image, base_name + "_TransTex")

        # Clearcoat (KHR_materials_clearcoat)
        coat_sock = (pbsdf.inputs.get("Coat Weight") or  # 4.x
                     pbsdf.inputs.get("Clearcoat"))      # 3.x
        if coat_sock:
            cv = float(coat_sock.default_value)
            if cv > 0.001:
                coat_ext = self.trv.processBasicNodeAddition(
                    pm, "extensions", "ClearcoatMaterialExtension", base_name + "_CoatME")
                if coat_ext:
                    coat_ext.clearcoat = cv
                    coat_rough = (pbsdf.inputs.get("Coat Roughness") or
                                  pbsdf.inputs.get("Clearcoat Roughness"))
                    if coat_rough:
                        coat_ext.clearcoatRoughness = float(coat_rough.default_value)
                    coat_nm = (self._find_image_texture(mat.node_tree, "Coat Normal",      pbsdf) or
                               self._find_image_texture(mat.node_tree, "Clearcoat Normal", pbsdf))
                    if coat_nm and coat_nm.image:
                        self._make_image_texture(coat_ext, "clearcoatNormalTexture",
                                                  coat_nm.image, base_name + "_CoatNormTex")

        # Sheen (KHR_materials_sheen)
        sheen_sock = (pbsdf.inputs.get("Sheen Weight") or  # 4.x
                      pbsdf.inputs.get("Sheen"))           # 3.x
        if sheen_sock:
            sv = float(sheen_sock.default_value)
            if sv > 0.001:
                sheen_ext = self.trv.processBasicNodeAddition(
                    pm, "extensions", "SheenMaterialExtension", base_name + "_SheenME")
                if sheen_ext:
                    tint = pbsdf.inputs.get("Sheen Tint")
                    if tint:
                        sc = tint.default_value
                        if hasattr(sc, '__len__') and len(sc) >= 3:  # 4.x: color
                            sheen_ext.sheenColor = (float(sc[0]) * sv,
                                                     float(sc[1]) * sv,
                                                     float(sc[2]) * sv)
                        else:                                         # 3.x: float
                            sheen_ext.sheenColor = (sv, sv, sv)
                    sheen_rough = pbsdf.inputs.get("Sheen Roughness")
                    if sheen_rough:
                        sheen_ext.sheenRoughness = float(sheen_rough.default_value)

        # Anisotropy (KHR_materials_anisotropy)
        ani_sock = pbsdf.inputs.get("Anisotropic")
        if ani_sock:
            av = float(ani_sock.default_value)
            if abs(av) > 0.001:
                ani_ext = self.trv.processBasicNodeAddition(
                    pm, "extensions", "AnisotropyMaterialExtension", base_name + "_AniME")
                if ani_ext:
                    ani_ext.anisotropyStrength = av
                    ani_rot = pbsdf.inputs.get("Anisotropic Rotation")
                    if ani_rot:
                        ani_ext.anisotropyRotation = float(ani_rot.default_value)


    def _build_packaged_composed_shader(self, x3dApp, mat, pbsdf, base_name,
                                        is_gltf_mr=False):
        """Export as PackagedShader (MTLX) + ComposedShader (GLSL).
        Falls back to PhysicalMaterialExt when MaterialX is unavailable or
        the shader is a glTF MR group (no direct MTLX equivalent)."""
        try:
            import MaterialX as mx
            import MaterialX.PyMaterialXGenShader as mx_gen
            import MaterialX.PyMaterialXGenGlsl   as mx_glsl
        except ImportError:
            print(f"[RawKee] MaterialX Python package not found — "
                  f"falling back to PhysicalMaterialExt for '{mat.name}'.")
            self._build_physical_material_ext(x3dApp, mat, pbsdf, base_name,
                                              is_gltf_mr=is_gltf_mr)
            return

        if is_gltf_mr:
            print(f"[RawKee] glTF MR group has no MTLX equivalent — "
                  f"falling back to PhysicalMaterialExt for '{mat.name}'.")
            self._build_physical_material_ext(x3dApp, mat, pbsdf, base_name,
                                              is_gltf_mr=True)
            return

        export_base = os.path.join(os.path.dirname(self.fullPath),
                                   self.rkMatXPath.lstrip('/\\'))
        os.makedirs(export_base, exist_ok=True)

        mtlx_path, mat_node_name = self._build_mtlx_document(mat, pbsdf, base_name,
                                                               export_base)
        if not mtlx_path:
            print(f"[RawKee] MaterialX document build failed for '{mat.name}' — "
                  f"falling back to PhysicalMaterialExt.")
            self._build_physical_material_ext(x3dApp, mat, pbsdf, base_name)
            return

        frag_path = os.path.join(export_base, base_name + ".frag")
        vert_path = os.path.join(export_base, base_name + ".vert")

        ok = self._generate_glsl_from_mtlx(mtlx_path, mat_node_name, frag_path, vert_path)
        if not ok:
            print(f"[RawKee] GLSL generation failed for '{mat.name}' — "
                  f"falling back to PhysicalMaterialExt.")
            self._build_physical_material_ext(x3dApp, mat, pbsdf, base_name)
            return

        rel_base  = self.rkMatXPath.rstrip('/') + '/' + base_name
        mtlx_rel  = rel_base + ".mtlx"
        frag_rel  = rel_base + ".frag"
        vert_rel  = rel_base + ".vert"

        # PackagedShader — MaterialX document
        pkg = self.trv.processBasicNodeAddition(x3dApp, "shaders", "PackagedShader",
                                                 base_name + "_PkSdr")
        if pkg:
            pkg.language = "MTLX"
            pkg.url = [mtlx_rel]

        # ComposedShader — GLSL frag + vert
        cmp = self.trv.processBasicNodeAddition(x3dApp, "shaders", "ComposedShader",
                                                 base_name + "_CpSdr")
        if cmp:
            cmp.language = "GLSL"
            frag = self.trv.processBasicNodeAddition(cmp, "parts", "ShaderPart",
                                                      base_name + "_CpSdr_Frag")
            if frag:
                frag.url  = [frag_rel]
                frag.type = "FRAGMENT"
            vert = self.trv.processBasicNodeAddition(cmp, "parts", "ShaderPart",
                                                      base_name + "_CpSdr_Vert")
            if vert:
                vert.url = [vert_rel]


    def _build_mtlx_document(self, mat, pbsdf, base_name, export_dir):
        """Build a minimal MaterialX gltf_pbr document from Principled BSDF inputs.
        Returns (mtlx_path, material_node_name) or (None, None) on failure."""
        import MaterialX as mx

        safe    = mx.createValidName(base_name)
        ng_name = f"NG_{safe}"
        sr_name = f"SR_{safe}"
        m_name  = f"M_{safe}"

        doc = mx.createDocument()
        ng  = doc.addNodeGraph(ng_name)

        def _add_image_node(sock_name, mx_type, out_suffix):
            """Add an image node to the nodegraph for the texture on sock_name.
            Returns the output name, or None if no texture is found."""
            img_node = self._find_image_texture(mat.node_tree, sock_name, pbsdf)
            blender_img = img_node.image if img_node else None
            if not blender_img:
                return None

            src = bpy.path.abspath(blender_img.filepath) if blender_img.filepath else ''
            if not os.path.isfile(src) and blender_img.packed_file:
                fname = os.path.basename(blender_img.name) or blender_img.name
                if not os.path.splitext(fname)[1]:
                    data  = blender_img.packed_file.data
                    fname += '.png' if data[:4] == b'\x89PNG' else '.jpg'
                src = os.path.join(export_dir, fname)
                with open(src, 'wb') as f:
                    f.write(blender_img.packed_file.data)
            if not os.path.isfile(src):
                return None

            url = (self._copy_texture(src, os.path.dirname(self.fullPath))
                   if self.rkConsolidate else src)

            node_name = f"img_{out_suffix}"
            out_name  = f"{out_suffix}_out"
            img_mx    = ng.addNode("image", node_name, mx_type)
            file_inp  = img_mx.addInput("file", "filename")
            file_inp.setValueString(url)
            out_port  = ng.addOutput(out_name, mx_type)
            out_port.setNodeName(node_name)
            return out_name

        em_sock_name = ("Emission Color" if pbsdf.inputs.get("Emission Color")
                        else "Emission")

        base_out = _add_image_node("Base Color",  "color3",  "base_color")
        mr_out   = (_add_image_node("Metallic",   "color3",  "metallic_roughness") or
                    _add_image_node("Roughness",  "color3",  "roughness"))
        norm_out = _add_image_node("Normal",      "vector3", "normal")
        emis_out = _add_image_node(em_sock_name,  "color3",  "emissive")
        occ_out  = _add_image_node("Occlusion",   "float",   "occlusion")

        # gltf_pbr surface shader
        sr = doc.addNode("gltf_pbr", sr_name, "surfaceshader")

        def _sr_inp_ng(name, mx_type, ng_out):
            inp = sr.addInput(name, mx_type)
            inp.setNodeGraphString(ng_name)
            inp.setOutputString(ng_out)

        def _sr_inp_val(name, mx_type, val):
            inp = sr.addInput(name, mx_type)
            if hasattr(val, '__len__'):
                inp.setValueString(', '.join(f"{v:.6f}" for v in val))
            else:
                inp.setValueString(f"{val:.6f}")

        base_col_raw = self._get_pbsdf_input_value(pbsdf, "Base Color")
        if base_out:
            _sr_inp_ng("base_color", "color3", base_out)
        elif base_col_raw:
            _sr_inp_val("base_color", "color3",
                        (base_col_raw[0], base_col_raw[1], base_col_raw[2]))

        if mr_out:
            _sr_inp_ng("metallic_roughness", "color3", mr_out)
        else:
            metal_val = self._get_pbsdf_input_value(pbsdf, "Metallic")
            rough_val = self._get_pbsdf_input_value(pbsdf, "Roughness")
            if metal_val is not None:
                _sr_inp_val("metallic",  "float", float(metal_val))
            if rough_val is not None:
                _sr_inp_val("roughness", "float", float(rough_val))

        if norm_out:
            _sr_inp_ng("normal", "vector3", norm_out)

        em_sock = pbsdf.inputs.get("Emission Color") or pbsdf.inputs.get("Emission")
        if emis_out:
            _sr_inp_ng("emissive", "color3", emis_out)
        elif em_sock:
            ec = em_sock.default_value
            if any(v > 0.001 for v in (ec[0], ec[1], ec[2])):
                _sr_inp_val("emissive", "color3", (ec[0], ec[1], ec[2]))

        if occ_out:
            _sr_inp_ng("occlusion", "float", occ_out)

        alpha_val = self._get_pbsdf_input_value(pbsdf, "Alpha")
        if alpha_val is not None:
            _sr_inp_val("alpha", "float", float(alpha_val))

        ior_val = self._get_pbsdf_input_value(pbsdf, "IOR")
        if ior_val is not None:
            _sr_inp_val("ior", "float", float(ior_val))

        trans_sock = (pbsdf.inputs.get("Transmission Weight") or
                      pbsdf.inputs.get("Transmission"))
        if trans_sock:
            tv = float(trans_sock.default_value)
            if tv > 0.001:
                _sr_inp_val("transmission", "float", tv)

        # Surface material node
        mat_mx = doc.addNode("surfacematerial", m_name, "material")
        ss_inp = mat_mx.addInput("surfaceshader", "surfaceshader")
        ss_inp.setNodeName(sr_name)

        mtlx_path = os.path.join(export_dir, base_name + ".mtlx")
        try:
            mx.writeToXmlFile(doc, mtlx_path)
            print(f"[RawKee] MaterialX document written: {mtlx_path}")
        except Exception as e:
            print(f"[RawKee] Failed to write MaterialX document: {e}")
            return None, None

        return mtlx_path, m_name


    def _generate_glsl_from_mtlx(self, mtlx_path, mat_name, frag_path, vert_path):
        """Generate GLSL frag/vert from a MaterialX document. Returns True on success."""
        import MaterialX as mx
        import MaterialX.PyMaterialXGenShader as mx_gen
        import MaterialX.PyMaterialXGenGlsl   as mx_glsl

        try:
            doc   = mx.createDocument()
            sPath = mx.FileSearchPath()
            sPath.append(os.path.dirname(mtlx_path))
            sPath.append(mx.getDefaultDataSearchPath())

            for subfolder in ['libraries', 'libraries/stdlib', 'libraries/pbrlib']:
                lib_doc = mx.createDocument()
                mx.loadLibraries([subfolder], sPath.asString(), lib_doc)
                doc.importLibrary(lib_doc)

            mx.readFromXmlFile(doc, mtlx_path, sPath.asString())

            materials = [n for n in doc.getNodes() if n.getCategory() == 'surfacematerial']
            if not materials:
                print(f"[RawKee] No surfacematerial node found in {mtlx_path}")
                return False

            target = next((m for m in materials if m.getName() == mat_name), materials[0])

            gen     = mx_glsl.GlslShaderGenerator.create()
            context = mx_gen.GenContext(gen)
            context.registerSourceCodeSearchPath(sPath)
            context.getOptions().shaderInterfaceType = mx_gen.SHADER_INTERFACE_COMPLETE

            safe_name = mx.createValidName(target.getName())
            shader    = gen.generate(safe_name, target, context)

            v_stage = getattr(mx_gen, 'VERTEX_STAGE', 'vertex')
            p_stage = getattr(mx_gen, 'PIXEL_STAGE',  'pixel')

            with open(vert_path, 'w') as f:
                f.write(shader.getSourceCode(v_stage))
            with open(frag_path, 'w') as f:
                f.write(shader.getSourceCode(p_stage))

            print(f"[RawKee] GLSL files written:\n  {vert_path}\n  {frag_path}")
            return True

        except Exception as e:
            print(f"[RawKee] GLSL generation error: {e}")
            return False


    def _make_image_texture(self, parent_node, field_name, blender_image, def_name,
                             node_type='ImageTexture'):
        """
        Resolve/copy the image file and attach it as parent_node.<field_name>.
        Handles both external files and images packed inside the .blend file.
        node_type can be 'ImageTexture' or 'ImageCubeMapTexture'.
        """
        if not blender_image:
            return None

        src_abs = bpy.path.abspath(blender_image.filepath) if blender_image.filepath else ''

        # Packed image: extract raw bytes to the images directory.
        if (not src_abs or not os.path.isfile(src_abs)) and blender_image.packed_file:
            raw_name = os.path.basename(
                blender_image.name.lstrip('/').lstrip('\\')
            ) or blender_image.name
            fname = raw_name
            if not os.path.splitext(fname)[1]:
                data = blender_image.packed_file.data
                if data[:4] == b'\x89PNG':
                    fname += '.png'
                elif data[:3] == b'\xff\xd8\xff':
                    fname += '.jpg'
                else:
                    fname += '.png'
            os.makedirs(self.imageMoveDir, exist_ok=True)
            dst = os.path.join(self.imageMoveDir, fname)
            try:
                with open(dst, 'wb') as f:
                    f.write(blender_image.packed_file.data)
            except Exception as e:
                print(f"RKOrganizerBlender: packed image extract failed '{fname}': {e}")
                return None
            src_abs = dst

        elif not src_abs or not os.path.isfile(src_abs):
            return None   # no file and not packed — nothing to export

        # Determine output URL.
        # HDR/EXR: "Convert HDR/EXR to KTX2" decides the format; "Consolidate Media"
        # decides where the file lands.  Other formats follow the normal copy logic.
        file_ext = os.path.splitext(src_abs)[1].lower()
        if self.rkConvertHDRToKTX2 and file_ext in ('.hdr', '.exr'):
            import importlib, subprocess as _sp
            # Find pip install locations for KTX2 deps and add to sys.path immediately
            for _pkg in ('numpy', 'imageio', 'cv2', 'scipy'):
                _show = _sp.run([sys.executable, "-m", "pip", "show",
                                  "opencv-python" if _pkg == "cv2" else _pkg],
                                 capture_output=True, text=True)
                for _line in _show.stdout.splitlines():
                    if _line.startswith("Location: "):
                        _loc = os.path.normpath(_line[10:].strip())
                        if _loc not in [os.path.normpath(p) for p in sys.path]:
                            sys.path.insert(0, _loc)
                        break
            importlib.invalidate_caches()
            def _importable(name):
                try:
                    __import__(name)
                    return True
                except Exception as e:
                    _rk_log(f"[RawKee] Cannot import '{name}': {type(e).__name__}: {e}")
                    return False
            _missing = [m for m in ('numpy', 'imageio', 'cv2', 'scipy') if not _importable(m)]
            if _missing:
                _rk_log(f"[RawKee] KTX2 skipped — missing packages: {_missing}\n"
                      f"[RawKee] Fix: run blender_rawkee_install.py to install them.")
                url_list = [src_abs]
            else:
                fname_ktx2 = os.path.splitext(os.path.basename(src_abs))[0] + '.ktx2'
                if self.rkConsolidate:
                    os.makedirs(self.imageMoveDir, exist_ok=True)
                    dst_ktx2 = os.path.join(self.imageMoveDir, fname_ktx2)
                    url_list  = [fname_ktx2, self.rkImagePath + fname_ktx2]
                else:
                    out_dir  = os.path.dirname(self.fullPath)
                    dst_ktx2 = os.path.join(out_dir, fname_ktx2)
                    url_list  = [fname_ktx2]
                try:
                    RKTools.hdri2ktx2(src_abs, dst_ktx2, file_ext == '.exr',
                                      self.rkMaxCubeMapFaceSize)
                    _rk_log(f"[RawKee] KTX2 conversion succeeded: {dst_ktx2}")
                except Exception as e:
                    import traceback
                    _rk_log(f"[RawKee] KTX2 conversion FAILED for '{src_abs}': {e}")
                    traceback.print_exc()
                    url_list = [src_abs]  # fall back to original path on failure

        elif self.rkConsolidate:
            fname    = os.path.basename(src_abs)
            rel_url  = self._copy_texture(src_abs, os.path.dirname(self.fullPath))
            url_list = [fname, rel_url]  # ["texture.jpg", "images/texture.jpg"]

        else:
            url_list = [src_abs]

        tex = self.trv.processBasicNodeAddition(
            parent_node, field_name, node_type, def_name
        )
        if tex:
            tex.url = url_list
        return tex


    def _add_image_texture(self, x3dApp, blender_image, def_name, pm, is_base=False):
        """Legacy wrapper – adds base texture to the Appearance texture slot."""
        self._make_image_texture(pm, "baseTexture", blender_image, def_name)


    # -----------------------------------------------------------------------
    #  World environment → EnvironmentLight
    # -----------------------------------------------------------------------

    def _process_world_environment(self, x3dScene, context):
        """
        If the Blender World uses an Environment Texture node, export it as
        an X3D EnvironmentLight with ImageCubeMapTexture for specular and
        diffuse slots (X_ITE accepts equirectangular images here).
        """
        world = context.scene.world
        if not world or not world.use_nodes:
            return

        env_node = None
        bg_node  = None
        for node in world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT':
                env_node = node
            elif node.type == 'BACKGROUND':
                bg_node = node

        if env_node is None or not env_node.image:
            return

        el = self.trv.processBasicNodeAddition(
            x3dScene, "children", "EnvironmentLight", "WorldEnvironmentLight"
        )
        if el is None:
            return

        el.global_  = True
        if bg_node:
            strength = bg_node.inputs.get("Strength")
            if strength is not None:
                el.intensity = float(strength.default_value)

        # Both specular and diffuse use the same equirectangular image
        self._make_image_texture(el, "specularTexture", env_node.image,
                                  "WorldEnvSpecTex", node_type='ImageCubeMapTexture')
        self._make_image_texture(el, "diffuseTexture",  env_node.image,
                                  "WorldEnvDiffTex",  node_type='ImageCubeMapTexture')


    # -----------------------------------------------------------------------
    #  HAnim Humanoid handler
    # -----------------------------------------------------------------------

    def _process_hanim_humanoid(self, x3dParent, arm_obj, context, is_root):
        """Export an armature tagged rk_hanim_humanoid=True as HAnimHumanoid."""
        mat_blender = arm_obj.matrix_world if is_root else arm_obj.matrix_local
        mat_x3d = _AX @ mat_blender @ _AX.inverted()
        loc, rot, sca = _decompose(mat_x3d)
        def_name = _safe_name(arm_obj.name)

        hh = self.trv.processBasicNodeAddition(
            x3dParent, "children", "HAnimHumanoid", def_name
        )
        if hh is None:
            return
        self.haveBeenObjects[arm_obj.name] = True

        hh.name      = arm_obj.get("rk_hanim_name", arm_obj.name)
        hh.version   = "2.0"
        loa_val      = arm_obj.get("rk_hanim_loa", 0)
        hh.loa        = int(loa_val)
        hh.translation = loc
        hh.rotation    = rot
        hh.scale       = sca

        # Export the skeleton joint hierarchy
        arm    = arm_obj.data
        roots  = [b for b in arm.bones if b.parent is None]
        for root_bone in roots:
            self._process_hanim_joint(hh, arm_obj, root_bone, context)

        # Children objects (meshes parented to this armature → HAnimHumanoid.skin)
        for child in arm_obj.children:
            if child.type == 'MESH':
                self._process_mesh(hh, child, context, is_root=False)


    def _process_hanim_joint(self, x3dParent, arm_obj, bone, context, parent_head=None):
        """Recursively export an armature bone as an HAnimJoint."""
        def_name  = _safe_name(arm_obj.name + "_" + bone.name)
        joint_name = bone.get("rk_hanim_joint_name", bone.name)

        jnt = self.trv.processBasicNodeAddition(
            x3dParent, "children", "HAnimJoint", def_name
        )
        if jnt is None:
            return
        jnt.name = joint_name

        # Center: bone head in armature local space, axis-converted
        head_local = _AX.to_3x3() @ bone.head_local
        if parent_head is not None:
            # Translation relative to parent joint
            trans = head_local - parent_head
            jnt.center      = (round(head_local.x, 6),
                                round(head_local.y, 6),
                                round(head_local.z, 6))
            jnt.translation = (round(trans.x, 6),
                                round(trans.y, 6),
                                round(trans.z, 6))
        else:
            jnt.center      = (round(head_local.x, 6),
                                round(head_local.y, 6),
                                round(head_local.z, 6))
            jnt.translation = _ZERO_VEC

        jnt.rotation = _IDENTITY_ROT

        # HAnim joint skin-influence indices placeholder
        # (detailed deformer export would require skin weights — stubbed)

        # HAnimSite nodes if option set
        if self.rkUseHAnimSites:
            tail_local = _AX.to_3x3() @ bone.tail_local
            site = self.trv.processBasicNodeAddition(
                jnt, "children", "HAnimSite", def_name + "_Site"
            )
            if site:
                site.name        = joint_name + "_pt"
                site.translation = (round(tail_local.x, 6),
                                    round(tail_local.y, 6),
                                    round(tail_local.z, 6))

        for child_bone in bone.children:
            self._process_hanim_joint(jnt, arm_obj, child_bone, context,
                                      parent_head=head_local)


    # -----------------------------------------------------------------------
    #  Light handler
    # -----------------------------------------------------------------------

    def _process_light(self, x3dParent, obj, context, is_root):
        light = obj.data
        mat_blender = obj.matrix_world if is_root else obj.matrix_local
        mat_x3d = _AX @ mat_blender @ _AX.inverted()
        loc, rot, sca = _decompose(mat_x3d)
        def_name = _safe_name(obj.name)
        col = light.color

        if light.type == 'SUN':
            lnode = self.trv.processBasicNodeAddition(
                x3dParent, "children", "DirectionalLight", def_name
            )
            if lnode:
                # Default SUN direction (facing -Z in Blender local space → Y-up)
                dir_world = _AX.to_3x3() @ (obj.matrix_world.to_3x3() @ mathutils.Vector((0, 0, -1)))
                dir_world.normalize()
                lnode.direction = (round(dir_world.x, 6),
                                   round(dir_world.y, 6),
                                   round(dir_world.z, 6))
                lnode.color      = (col.r, col.g, col.b)
                lnode.intensity  = light.energy / 100.0

        elif light.type == 'POINT':
            lnode = self.trv.processBasicNodeAddition(
                x3dParent, "children", "PointLight", def_name
            )
            if lnode:
                lnode.location  = loc
                lnode.color     = (col.r, col.g, col.b)
                lnode.intensity = light.energy / 100.0
                lnode.radius    = light.shadow_soft_size if hasattr(light, 'shadow_soft_size') else 10.0

        elif light.type == 'SPOT':
            lnode = self.trv.processBasicNodeAddition(
                x3dParent, "children", "SpotLight", def_name
            )
            if lnode:
                dir_world = _AX.to_3x3() @ (obj.matrix_world.to_3x3() @ mathutils.Vector((0, 0, -1)))
                dir_world.normalize()
                lnode.location   = loc
                lnode.direction  = (round(dir_world.x, 6),
                                    round(dir_world.y, 6),
                                    round(dir_world.z, 6))
                lnode.color      = (col.r, col.g, col.b)
                lnode.intensity  = light.energy / 100.0
                lnode.cutOffAngle = light.spot_size * 0.5
                lnode.beamWidth  = light.spot_size * light.spot_blend * 0.5

        self.haveBeenObjects[obj.name] = True


    # -----------------------------------------------------------------------
    #  Camera handler
    # -----------------------------------------------------------------------

    def _process_camera(self, x3dParent, obj, context, is_root):
        cam = obj.data
        mat = obj.matrix_world if is_root else obj.matrix_local

        # Position: Blender (X, Y, Z) → X3D (X, Z, −Y)
        t   = mat.to_translation()
        loc = (t.x, t.z, -t.y)

        # Orientation: pre-multiply Blender rotation by _CAM_CORR,
        # then extract axis-angle for the X3D SFRotation field.
        _, rot_q, _ = mat.decompose()
        R_result    = _CAM_CORR @ rot_q.to_matrix()
        ax, ang     = R_result.to_quaternion().to_axis_angle()
        if ax.length < 1e-8:
            ax  = mathutils.Vector((0.0, 0.0, 1.0))
            ang = 0.0
        rot = (ax.x, ax.y, ax.z, ang)
        def_name = _safe_name(obj.name)

        vp = self.trv.processBasicNodeAddition(
            x3dParent, "children", "Viewpoint", def_name
        )
        if vp:
            vp.position     = loc
            vp.orientation  = rot
            vp.fieldOfView  = cam.angle_y if hasattr(cam, 'angle_y') else cam.angle
            vp.description  = obj.name

        self.haveBeenObjects[obj.name] = True


    # -----------------------------------------------------------------------
    #  Speaker → Sound + AudioClip handler
    # -----------------------------------------------------------------------

    def _process_speaker(self, x3dParent, obj, context, is_root):
        spkr = obj.data
        mat_blender = obj.matrix_world if is_root else obj.matrix_local
        mat_x3d = _AX @ mat_blender @ _AX.inverted()
        loc, rot, sca = _decompose(mat_x3d)
        def_name = _safe_name(obj.name)

        snd = self.trv.processBasicNodeAddition(
            x3dParent, "children", "Sound", def_name
        )
        if snd is None:
            self.haveBeenObjects[obj.name] = True
            return
        snd.location   = loc
        snd.maxFront   = spkr.attenuation_max_distance if hasattr(spkr, 'attenuation_max_distance') else 10.0
        snd.maxBack    = snd.maxFront
        snd.minFront   = 1.0
        snd.minBack    = 1.0

        # AudioClip child
        if spkr.sound and spkr.sound.filepath:
            src_abs = bpy.path.abspath(spkr.sound.filepath)
            if self.rkConsolidate:
                url = self.rkAudioPath + os.path.basename(src_abs)
                dst = os.path.join(self.audioMoveDir, os.path.basename(src_abs))
                if os.path.isfile(src_abs) and not os.path.isfile(dst):
                    try:
                        shutil.copy2(src_abs, dst)
                    except Exception as e:
                        print(f"RKOrganizerBlender: audio copy failed: {e}")
            else:
                url = src_abs

            ac = self.trv.processBasicNodeAddition(
                snd, "source", "AudioClip", def_name + "_AudioClip"
            )
            if ac:
                ac.url = [url]

        self.haveBeenObjects[obj.name] = True


    # -----------------------------------------------------------------------
    #  Custom X3D Sound EMPTY handler
    # -----------------------------------------------------------------------

    def _process_x3d_sound(self, x3dParent, obj, context, is_root=False):
        """Export an EMPTY flagged rk_x3d_type='Sound' as a Sound node."""
        mat_blender = obj.matrix_world if is_root else obj.matrix_local
        mat_x3d = _AX @ mat_blender @ _AX.inverted()
        loc, _, _ = _decompose(mat_x3d)
        def_name  = _safe_name(obj.name)
        props     = obj.rk_x3d_sound

        snd = self.trv.processBasicNodeAddition(
            x3dParent, "children", "Sound", def_name
        )
        if snd is None:
            self.haveBeenObjects[obj.name] = True
            return

        snd.location   = loc
        snd.direction  = tuple(props.direction)
        snd.intensity  = props.intensity
        snd.maxFront   = props.maxFront
        snd.maxBack    = props.maxBack
        snd.minFront   = props.minFront
        snd.minBack    = props.minBack
        snd.priority   = props.priority
        snd.spatialize = props.spatialize

        if props.audio_url:
            ac = self.trv.processBasicNodeAddition(
                snd, "source", "AudioClip", def_name + "_AudioClip"
            )
            if ac:
                ac.url = [props.audio_url]

        self.haveBeenObjects[obj.name] = True


    # -----------------------------------------------------------------------
    #  RKAnimPack EMPTY handler
    # -----------------------------------------------------------------------

    def _process_anim_pack(self, x3dParent, obj, context, is_root=False):
        """
        Export an EMPTY flagged rk_anim_pack=True.
        Deferred — the actual TimeSensor / HAnimMotion / AudioClip nodes are
        emitted during _collect_animation_data() at the end of export,
        matching the Maya version's processRKAnimPacks() call.
        The pack object is registered here for later processing.
        """
        if obj.name not in self.haveBeenObjects:
            self.haveBeenObjects[obj.name] = True
            # Store for deferred emission
            self._anim_packs = getattr(self, '_anim_packs', [])
            self._anim_packs.append((x3dParent, obj))


    # -----------------------------------------------------------------------
    #  EMPTY / plain group handler
    # -----------------------------------------------------------------------

    def _process_empty(self, x3dParent, obj, context, is_root):
        if not self.rkExportEmpties and not obj.children:
            return
        tfm = self._make_transform(x3dParent, obj, is_root)
        if tfm is None:
            return
        for child in obj.children:
            self._process_object(tfm, child, context, is_root=False)


    # -----------------------------------------------------------------------
    #  Animation collection  (mirrors collectInterpolatorData / processRKAnimPacks)
    # -----------------------------------------------------------------------

    def _collect_animation_data(self, x3dScene, context):
        """
        After all geometry is exported, walk every object's action and NLA
        strips and emit TimeSensor + Interpolator + ROUTE sets.
        Mirrors Maya's collectInterpolatorData() and processRKAnimPacks().
        """
        fps = context.scene.render.fps
        exported_actions = set()

        for obj in context.scene.objects:
            if obj.hide_render:
                continue
            if obj.animation_data is None:
                continue

            actions = []
            # Current action
            if obj.animation_data.action:
                actions.append(obj.animation_data.action)
            # NLA strips
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action and strip.action not in actions:
                        actions.append(strip.action)

            for action in actions:
                action_key = (obj.name, action.name)
                if action_key in exported_actions:
                    continue
                exported_actions.add(action_key)

                f_start = action.frame_range[0]
                f_end   = action.frame_range[1]
                n_frames = f_end - f_start
                if n_frames <= 0:
                    continue

                cycle_interval = n_frames / fps
                ts_name = _safe_name(obj.name) + "_" + _safe_name(action.name) + "_TS"

                timer = self.trv.processBasicNodeAddition(
                    x3dScene, "children", "TimeSensor", ts_name
                )
                if timer is None:
                    continue
                timer.cycleInterval = round(cycle_interval, 6)
                timer.loop          = False

                # Position Interpolator
                self._emit_position_interp(x3dScene, obj, action,
                                           f_start, f_end, fps, ts_name, cycle_interval)
                # Orientation Interpolator
                self._emit_orientation_interp(x3dScene, obj, action,
                                              f_start, f_end, fps, ts_name, cycle_interval)

        # Deferred AnimPack processing
        for x3dParent, ap_obj in getattr(self, '_anim_packs', []):
            self._emit_anim_pack_nodes(x3dScene, x3dParent, ap_obj, fps)
        self._anim_packs = []


    def _sample_location(self, obj, action, frame, fps):
        """Evaluate obj location at frame for the given action."""
        saved_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(int(frame))
        loc = _AX.to_3x3() @ obj.location.copy()
        bpy.context.scene.frame_set(saved_frame)
        return (loc.x, loc.y, loc.z)


    def _emit_position_interp(self, x3dScene, obj, action,
                               f_start, f_end, fps, ts_name, cycle_interval):
        loc_curves = [fc for fc in action.fcurves
                      if fc.data_path == 'location' and not fc.mute]
        if not loc_curves:
            return

        n_keys   = max(int(f_end - f_start) + 1, 2)
        step     = max(1, int(n_keys / 64))  # Cap at ~64 samples for performance
        frames   = [f_start + i * step for i in range(int((f_end - f_start) / step) + 1)]
        if frames[-1] != f_end:
            frames.append(f_end)

        keys   = []
        values = []
        for fr in frames:
            t = (fr - f_start) / (f_end - f_start)
            keys.append(round(t, 6))
            # Evaluate each curve at this frame
            raw = [0.0, 0.0, 0.0]
            for fc in loc_curves:
                if fc.array_index < 3:
                    raw[fc.array_index] = fc.evaluate(fr)
            # Convert Blender XYZ to X3D YUP
            v = _AX.to_3x3() @ mathutils.Vector(raw)
            values.append((round(v.x, 6), round(v.y, 6), round(v.z, 6)))

        pi_name = ts_name.replace("_TS", "_PosInterp")
        pi = self.trv.processBasicNodeAddition(
            x3dScene, "children", "PositionInterpolator", pi_name
        )
        if pi is None:
            return
        pi.key      = keys
        pi.keyValue = values

        # ROUTEs
        obj_def = _safe_name(obj.name)
        self._add_route(x3dScene, ts_name, "fraction_changed", pi_name, "set_fraction")
        self._add_route(x3dScene, pi_name,  "value_changed",   obj_def, "set_translation")


    def _emit_orientation_interp(self, x3dScene, obj, action,
                                  f_start, f_end, fps, ts_name, cycle_interval):
        rot_curves = [fc for fc in action.fcurves
                      if fc.data_path in ('rotation_euler', 'rotation_quaternion') and not fc.mute]
        if not rot_curves:
            return

        n_keys = max(int(f_end - f_start) + 1, 2)
        step   = max(1, int(n_keys / 64))
        frames = [f_start + i * step for i in range(int((f_end - f_start) / step) + 1)]
        if frames[-1] != f_end:
            frames.append(f_end)

        keys   = []
        values = []
        use_quat = any(fc.data_path == 'rotation_quaternion' for fc in rot_curves)

        for fr in frames:
            t = (fr - f_start) / (f_end - f_start)
            keys.append(round(t, 6))
            if use_quat:
                raw = [1.0, 0.0, 0.0, 0.0]
                for fc in rot_curves:
                    if fc.array_index < 4:
                        raw[fc.array_index] = fc.evaluate(fr)
                q = _AX.to_quaternion() @ mathutils.Quaternion(raw)
            else:
                raw = [0.0, 0.0, 0.0]
                for fc in rot_curves:
                    if fc.array_index < 3:
                        raw[fc.array_index] = fc.evaluate(fr)
                eu = mathutils.Euler(raw, obj.rotation_mode if obj.rotation_mode in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX') else 'XYZ')
                q  = (_AX.to_quaternion() @ eu.to_quaternion())

            ax, ang = q.to_axis_angle()
            if ax.length < 1e-8:
                ax  = mathutils.Vector((0, 0, 1))
                ang = 0.0
            values.append((round(ax.x, 6), round(ax.y, 6), round(ax.z, 6), round(ang, 6)))

        oi_name = ts_name.replace("_TS", "_OriInterp")
        oi = self.trv.processBasicNodeAddition(
            x3dScene, "children", "OrientationInterpolator", oi_name
        )
        if oi is None:
            return
        oi.key      = keys
        oi.keyValue = values

        obj_def = _safe_name(obj.name)
        self._add_route(x3dScene, ts_name, "fraction_changed", oi_name, "set_fraction")
        self._add_route(x3dScene, oi_name,  "value_changed",   obj_def, "set_rotation")


    def _emit_anim_pack_nodes(self, x3dScene, x3dParent, ap_obj, fps):
        """Emit the X3D node corresponding to a deferred RKAnimPack empty."""
        props     = ap_obj.rk_anim_pack
        def_name  = _safe_name(ap_obj.name)
        mt        = props.mimicked_type

        f_start   = props.timeline_start
        f_stop    = props.timeline_stop
        ap_fps    = props.fps if props.fps > 0 else fps
        duration  = (f_stop - f_start) / ap_fps

        if mt == '0':  # TimeSensor
            ci  = props.cycle_interval if props.cycle_interval > 0 else max(duration, 0.001)
            ts  = self.trv.processBasicNodeAddition(
                x3dScene, "children", "TimeSensor", def_name
            )
            if ts:
                ts.cycleInterval = round(ci, 6)
                ts.loop          = props.loop
                ts.enabled       = props.enabled
                ts.description   = props.description

        elif mt == '1':  # AudioClip
            ac = self.trv.processBasicNodeAddition(
                x3dScene, "children", "AudioClip", def_name
            )
            if ac:
                ac.loop        = props.loop
                ac.enabled     = props.enabled
                ac.description = props.description
                ac.pitch       = props.pitch
                ac.gain        = props.gain
                if props.connected_file:
                    ac.url = [props.connected_file]

        elif mt == '2':  # HAnimMotion
            hm = self.trv.processBasicNodeAddition(
                x3dScene, "children", "HAnimMotion", def_name
            )
            if hm:
                hm.enabled       = props.enabled
                hm.loop          = props.loop
                hm.loa           = props.hanim_loa
                hm.description   = props.description
                if props.hanim_joints:
                    hm.joints = props.hanim_joints.split()

        elif mt == '3':  # MovieTexture — inline near the referencing shape
            mt_node = self.trv.processBasicNodeAddition(
                x3dScene, "children", "MovieTexture", def_name
            )
            if mt_node:
                mt_node.loop        = props.loop
                mt_node.enabled     = props.enabled
                mt_node.description = props.description
                if props.connected_file:
                    mt_node.url = [props.connected_file]


    # -----------------------------------------------------------------------
    #  ROUTE helper
    # -----------------------------------------------------------------------

    def _add_route(self, x3dScene, from_node, from_field, to_node, to_field):
        route = self.trv.processBasicNodeAddition(
            x3dScene, "children", "ROUTE", ""
        )
        if route:
            route.fromNode  = from_node
            route.fromField = from_field
            route.toNode    = to_node
            route.toField   = to_field
