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
import shutil

from rawkee.io.RKSceneTraversal import RKSceneTraversal
from rawkee.io.RKx3d import *

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
        self.rkImagePath     = "/images"
        self.rkAudioPath     = "/audio"
        self.rkInlinePath    = "/inline"
        self.rkMatXPath      = "/mtlx"
        self.rkUseHAnimSites = False
        self.rkSkinInfluence = 0
        self.rkAdjTexSize    = False
        self.rkDefTexWidth   = 256
        self.rkDefTexHeight  = 256
        self.rkConsolidate   = True
        self.rkProcTexType   = 0
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
        self.rkImagePath     = opts.image_path
        self.rkAudioPath     = opts.audio_path
        self.rkMatXPath      = opts.matx_path
        self.rkUseHAnimSites = opts.use_hanim_sites
        self.rkSkinInfluence = int(opts.skin_influence)
        self.rkAdjTexSize    = opts.adj_tex_size
        self.rkDefTexWidth   = opts.tex_width
        self.rkDefTexHeight  = opts.tex_height
        self.rkConsolidate   = opts.consolidate
        self.rkProcTexType   = int(opts.proc_tex_type)
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
        self.imageMoveDir = base + self.rkImagePath
        self.audioMoveDir = base + self.rkAudioPath
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
        try:
            shutil.copy2(src_abs, dst_abs)
        except Exception as e:
            print(f"RKOrganizerBlender: texture copy failed: {e}")
        rel_url = self.rkImagePath.lstrip('/') + '/' + fname
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

        # Mark pseudo-root
        self.trv.setAsHasBeen("BlenderScene", x3dScene)

        # Background from world colour
        world = context.scene.world
        bkNode = self.trv.processBasicNodeAddition(
            x3dScene, "children", "Background", "DefaultBackground"
        )
        if bkNode and world:
            c = world.color
            bkNode.skyColor[0] = (c.r, c.g, c.b)

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
        self.trv.setAsHasBeen("BlenderScene", x3dScene)

        world = context.scene.world
        bkNode = self.trv.processBasicNodeAddition(
            x3dScene, "children", "Background", "DefaultBackground"
        )
        if bkNode and world:
            c = world.color
            bkNode.skyColor[0] = (c.r, c.g, c.b)

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
        # in the same collection so we don't double-export)
        for obj in collection.objects:
            if obj.parent is None or obj.parent.name not in collection.objects:
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
        """Create an X3D Transform from obj's matrix and return it."""
        mat = _world_mat(obj) if is_root else obj.matrix_local
        loc, rot, sca = _decompose(mat)
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

        # Vertices
        verts = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]

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
                    normal_vecs.append((ln.x, ln.y, ln.z))
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

        # Try to detect a Principled BSDF node
        pbsdf = None
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    pbsdf = node
                    break

        if pbsdf is not None:
            self._build_physical_material(app, mat, pbsdf, app_name)
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


    def _build_physical_material(self, x3dApp, mat, pbsdf, base_name):
        """Map Principled BSDF inputs to X3D PhysicalMaterial."""
        pm = self.trv.processBasicNodeAddition(
            x3dApp, "material", "PhysicalMaterial", base_name + "_PhysMat"
        )
        if pm is None:
            return

        # Base color
        base_col = self._get_pbsdf_input_value(pbsdf, "Base Color")
        if base_col:
            pm.baseColor = (base_col[0], base_col[1], base_col[2])

        # Metallic / roughness
        metal = self._get_pbsdf_input_value(pbsdf, "Metallic")
        if metal is not None:
            pm.metalness = float(metal)

        rough = self._get_pbsdf_input_value(pbsdf, "Roughness")
        if rough is not None:
            pm.roughnessFactor = float(rough)

        # Emissive
        em_sock = pbsdf.inputs.get("Emission")
        em_str  = pbsdf.inputs.get("Emission Strength")
        if em_sock and em_str:
            ec = em_sock.default_value
            es = float(em_str.default_value)
            pm.emissiveColor = (ec[0] * es, ec[1] * es, ec[2] * es)

        # Transparency (alpha)
        alpha = self._get_pbsdf_input_value(pbsdf, "Alpha")
        if alpha is not None and float(alpha) < 0.999:
            pm.transparency = 1.0 - float(alpha)

        # Base-color image texture
        img_node = self._find_image_texture(mat.node_tree, "Base Color", pbsdf)
        if img_node and img_node.image:
            self._add_image_texture(x3dApp, img_node.image, base_name + "_BaseColorTex",
                                    pm, is_base=True)

        # Normal map
        norm_node = self._find_image_texture(mat.node_tree, "Normal", pbsdf)
        if norm_node and norm_node.image:
            pass   # TODO: NormalMapTexture / TextureTransform


    def _add_image_texture(self, x3dApp, blender_image, def_name, pm, is_base=False):
        """Add an ImageTexture node to the Appearance and set its URL."""
        if not blender_image.filepath:
            return
        src_abs = bpy.path.abspath(blender_image.filepath)
        if self.rkConsolidate:
            url = self.rkImagePath.lstrip('/') + '/' + os.path.basename(src_abs)
            base_dir = os.path.dirname(self.fullPath)
            self._copy_texture(src_abs, base_dir)
        else:
            url = bpy.path.abspath(blender_image.filepath)

        tex = self.trv.processBasicNodeAddition(
            x3dApp, "texture", "ImageTexture", def_name
        )
        if tex:
            tex.url = [url]


    # -----------------------------------------------------------------------
    #  HAnim Humanoid handler
    # -----------------------------------------------------------------------

    def _process_hanim_humanoid(self, x3dParent, arm_obj, context, is_root):
        """Export an armature tagged rk_hanim_humanoid=True as HAnimHumanoid."""
        mat   = _world_mat(arm_obj) if is_root else arm_obj.matrix_local
        loc, rot, sca = _decompose(mat)
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
        mat   = _world_mat(obj) if is_root else obj.matrix_local
        loc, rot, sca = _decompose(mat)
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
        mat = _world_mat(obj) if is_root else obj.matrix_local
        loc, rot, sca = _decompose(mat)
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
        mat  = _world_mat(obj) if is_root else obj.matrix_local
        loc, rot, sca = _decompose(mat)
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
                url = self.rkAudioPath.lstrip('/') + '/' + os.path.basename(src_abs)
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
        mat = _world_mat(obj) if is_root else obj.matrix_local
        loc, _, _ = _decompose(mat)
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
