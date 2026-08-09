"""
RawKee Blender — Export Options PropertyGroup and panel.

Maya equivalent  : rawkee/maya/RKFOptsDialog.py  (QDialog loaded from
                   RKGeneralExportOptions.ui, reads/writes cmds.optionVar)

Blender approach : A bpy.types.PropertyGroup (RKExportOptionsProperties) is
                   registered on bpy.types.Scene.  A collapsible Panel in the
                   RawKee N-panel sidebar exposes every option.  An Operator
                   (RAWKEE_OT_ResetExportOptions) restores defaults.

                   All options are referenced in RKOrganizerBlender by reading
                   context.scene.rk_export_opts.<field>.
"""

import bpy
import json
import os
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty)
from bpy.types import PropertyGroup


# ---------------------------------------------------------------------------
#  Persistent defaults — JSON config (mirrors Maya optionVar behaviour)
# ---------------------------------------------------------------------------

# Keys that are saved/restored across sessions
_PERSISTENT_KEYS = [
    'prj_dir',
    'image_path', 'audio_path', 'inline_path', 'matx_path',
    'use_hanim_sites', 'skin_influence',
    'adj_tex_size', 'tex_width', 'tex_height',
    'consolidate', 'convert_hdr_to_ktx2', 'max_cube_map_face_size',
    'proc_tex_type', 'proc_tex_format', 'file_tex_type', 'file_tex_format',
    'movie_tex_type', 'audio_clip_type',
    'normal_opts', 'crease_angle', 'color_opts', 'is_triangles',
    'decimal_limit', 'export_tangents', 'export_empties',
    'export_metadata', 'export_animations', 'launch_ext',
]


def _config_path():
    return os.path.join(bpy.utils.user_resource('CONFIG'), "rawkee_export_opts.json")


def _save_opts(props):
    data = {k: getattr(props, k) for k in _PERSISTENT_KEYS}
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def _load_opts(props):
    path = _config_path()
    if not os.path.isfile(path):
        return
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        for k, v in data.items():
            if k in _PERSISTENT_KEYS:
                try:
                    setattr(props, k, v)
                except Exception:
                    pass
    except Exception as e:
        print(f"[RawKee] Could not load export defaults: {e}")


@bpy.app.handlers.persistent
def _restore_opts_on_load(dummy):
    """Restore saved export defaults whenever a file is loaded."""
    try:
        _load_opts(bpy.context.scene.rk_export_opts)
    except Exception:
        pass


# ---------------------------------------------------------------------------
#  Enum choices — mirrors the combo-box choices from RKGeneralExportOptions.ui
# ---------------------------------------------------------------------------

PROC_TEX_ITEMS = [
    ('0', "Skip Procedural Textures",         "Do not export procedural textures"),
    ('1', "Bake to File",                     "Bake procedural textures to image files"),
    ('2', "As Pixel Texture (inline)",        "Embed baked texture data as X3D PixelTexture"),
]

FILE_TEX_ITEMS = [
    ('0', "Keep Original Format",             "Export textures in their source format"),
    ('1', "Convert to PNG",                   "Convert all textures to PNG"),
    ('2', "Convert to JPEG",                  "Convert all textures to JPEG"),
    ('3', "Convert to GIF",                   "Convert all textures to GIF"),
    ('4', "As Pixel Texture (inline)",        "Embed image data as X3D PixelTexture"),
]

MOVIE_TEX_ITEMS = [
    ('0', "Keep Original",                    "Keep video file as-is and reference by URL"),
    ('1', "Skip",                             "Do not export movie textures"),
]

AUDIO_CLIP_ITEMS = [
    ('0', "Keep Original",                    "Keep audio file as-is and reference by URL"),
    ('1', "Skip",                             "Do not export audio clips"),
]

NORMAL_OPT_ITEMS = [
    ('0', "Per-Vertex Normals (auto)",        "Export per-vertex normals from mesh data"),
    ('1', "Crease Angle only",                "Export a single crease angle; let viewer compute normals"),
    ('2', "No Normals",                       "Omit normal data entirely"),
]

COLOR_OPT_ITEMS = [
    ('0', "No Color Per Vertex",              "Do not export vertex colors"),
    ('1', "Export Vertex Colors",             "Export vertex color layer as X3D ColorPerVertex"),
]

SKIN_INF_ITEMS = [
    ('0', "All Influences",                   "Export all non-zero skin weights"),
    ('1', "Top 4 Influences",                 "Cap at 4 influences per vertex"),
    ('2', "Top 2 Influences",                 "Cap at 2 influences per vertex"),
    ('3', "Top 1 Influence",                  "Only the strongest influence per vertex"),
]


# ---------------------------------------------------------------------------
#  Property Group
# ---------------------------------------------------------------------------

class RKExportOptionsProperties(PropertyGroup):
    """All RawKee export options, stored on the active Scene."""

    # Directories / paths
    prj_dir: StringProperty(
        name="Project Directory",
        description="Root directory for X3D export output",
        default="",
        subtype='DIR_PATH',
    )
    image_path: StringProperty(
        name="Image Sub-path",
        description="Sub-directory (relative to project dir) for exported textures",
        default="images/",
    )
    audio_path: StringProperty(
        name="Audio Sub-path",
        description="Sub-directory (relative to project dir) for exported audio",
        default="audio/",
    )
    inline_path: StringProperty(
        name="Inline Sub-path",
        description="Sub-directory (relative to project dir) for X3D Inline files",
        default="inline/",
    )
    matx_path: StringProperty(
        name="MaterialX Sub-path",
        description="Sub-directory (relative to project dir) for MaterialX documents",
        default="mtlx/",
    )

    # HAnim
    use_hanim_sites: BoolProperty(
        name="Export HAnimSite Nodes",
        description="Include X3D HAnimSite nodes in HAnim humanoid exports",
        default=False,
    )
    skin_influence: EnumProperty(
        name="Skin Influence Limit",
        description="Maximum number of joint influences per vertex",
        items=SKIN_INF_ITEMS,
        default='0',
    )

    # Texture options
    adj_tex_size: BoolProperty(
        name="Resize Textures",
        description="Resize exported textures to the specified dimensions",
        default=False,
    )
    tex_width: IntProperty(
        name="Width",
        description="Target texture width when resizing",
        default=256, min=1, max=8192,
    )
    tex_height: IntProperty(
        name="Height",
        description="Target texture height when resizing",
        default=256, min=1, max=8192,
    )
    consolidate: BoolProperty(
        name="Consolidate Media",
        description="Copy textures/audio into the project sub-directories",
        default=True,
    )
    convert_hdr_to_ktx2: BoolProperty(
        name="Convert HDR/EXR to KTX2",
        description="Convert HDR and EXR environment images to KTX2 cube map files on export",
        default=True,
    )
    max_cube_map_face_size: IntProperty(
        name="Max Cube Map Face Size",
        description="Maximum face resolution (pixels) for KTX2 cube map conversion",
        default=4096, min=64, max=16384,
    )
    proc_tex_type: EnumProperty(
        name="Procedural Texture",
        items=PROC_TEX_ITEMS,
        default='0',
    )
    proc_tex_format: EnumProperty(
        name="Procedural Format",
        items=[('0',"PNG",""),('1',"JPEG",""),('2',"GIF","")],
        default='0',
    )
    file_tex_type: EnumProperty(
        name="File Texture",
        items=FILE_TEX_ITEMS,
        default='0',
    )
    file_tex_format: EnumProperty(
        name="Consolidate Format",
        items=[('0',"Original",""),('1',"PNG",""),('2',"JPEG",""),('3',"GIF","")],
        default='0',
    )
    movie_tex_type: EnumProperty(
        name="Movie Texture",
        items=MOVIE_TEX_ITEMS,
        default='0',
    )
    audio_clip_type: EnumProperty(
        name="Audio Clip",
        items=AUDIO_CLIP_ITEMS,
        default='0',
    )

    # Geometry / normals / color
    normal_opts: EnumProperty(
        name="Normal Export",
        items=NORMAL_OPT_ITEMS,
        default='0',
    )
    crease_angle: FloatProperty(
        name="Crease Angle",
        description="Global crease angle in radians (X3D IndexedFaceSet.creaseAngle)",
        default=0.0, min=0.0, max=3.1416,
    )
    color_opts: EnumProperty(
        name="Vertex Color",
        items=COLOR_OPT_ITEMS,
        default='0',
    )
    is_triangles: BoolProperty(
        name="Force Triangles",
        description="Triangulate all meshes before export",
        default=False,
    )
    decimal_limit: IntProperty(
        name="Decimal Precision",
        description="Number of decimal places written to numeric fields",
        default=6, min=1, max=16,
    )
    export_tangents: BoolProperty(
        name="Export Tangents",
        description="Include tangent vectors in mesh export",
        default=False,
    )
    export_empties: BoolProperty(
        name="Export Empty Groups",
        description="Include X3D Group nodes for Blender empties and empty collections",
        default=True,
    )
    export_metadata: BoolProperty(
        name="Export Metadata",
        description="Write X3D MetadataString / MetadataFloat nodes",
        default=True,
    )
    export_animations: BoolProperty(
        name="Export Animations",
        description="Export Blender actions / NLA strips as X3D interpolators",
        default=True,
    )
    launch_ext: BoolProperty(
        name="Launch Viewer After Export",
        description="Open the exported file in the default X3D viewer after saving",
        default=False,
    )


# ---------------------------------------------------------------------------
#  Shared draw helper — used by the popup dialog
# ---------------------------------------------------------------------------

def _draw_export_options_layout(layout, opts):
    box = layout.box()
    box.label(text="Paths", icon='FILE_FOLDER')
    col = box.column(align=True)
    col.prop(opts, "prj_dir")
    col.prop(opts, "image_path")
    col.prop(opts, "audio_path")
    col.prop(opts, "inline_path")
    col.prop(opts, "matx_path")

    box = layout.box()
    box.label(text="HAnim / Skinning", icon='ARMATURE_DATA')
    col = box.column(align=True)
    col.prop(opts, "use_hanim_sites")
    col.prop(opts, "skin_influence")

    box = layout.box()
    box.label(text="Textures", icon='IMAGE_DATA')
    col = box.column(align=True)
    col.prop(opts, "adj_tex_size")
    if opts.adj_tex_size:
        row = col.row(align=True)
        row.prop(opts, "tex_width")
        row.prop(opts, "tex_height")
    col.prop(opts, "consolidate")
    col.prop(opts, "convert_hdr_to_ktx2")
    if opts.convert_hdr_to_ktx2:
        col.prop(opts, "max_cube_map_face_size")
    col.prop(opts, "proc_tex_type")
    if opts.proc_tex_type != '0':
        col.prop(opts, "proc_tex_format")
    col.prop(opts, "file_tex_type")
    if opts.file_tex_type not in ('0',):
        col.prop(opts, "file_tex_format")
    col.prop(opts, "movie_tex_type")
    col.prop(opts, "audio_clip_type")

    box = layout.box()
    box.label(text="Geometry & Output", icon='MESH_DATA')
    col = box.column(align=True)
    col.prop(opts, "normal_opts")
    col.prop(opts, "crease_angle")
    col.prop(opts, "color_opts")
    col.prop(opts, "is_triangles")
    col.prop(opts, "export_tangents")
    col.prop(opts, "decimal_limit")

    box = layout.box()
    box.label(text="Misc", icon='SETTINGS')
    col = box.column(align=True)
    col.prop(opts, "export_empties")
    col.prop(opts, "export_metadata")
    col.prop(opts, "export_animations")
    col.prop(opts, "launch_ext")


# ---------------------------------------------------------------------------
#  Operator — export options popup dialog
# ---------------------------------------------------------------------------

class RAWKEE_OT_ExportOptionsDialog(bpy.types.Operator):
    """Open the RawKee X3D export options dialog"""
    bl_idname  = "rawkee.export_options_dialog"
    bl_label   = "Save Options & Close"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(
            self, width=520, title="RawKee X3D Export Options"
        )

    def draw(self, context):
        layout = self.layout
        opts   = context.scene.rk_export_opts
        _draw_export_options_layout(layout, opts)
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("rawkee.export_save_and_export_all",      text="Save Options & Export All",      icon='EXPORT')
        row.operator("rawkee.export_save_and_export_selected", text="Save Options & Export Selected", icon='EXPORT')
        layout.separator()
        layout.operator("rawkee.reset_export_options", text="Reset to Defaults", icon='LOOP_BACK')

    def execute(self, context):
        _save_opts(context.scene.rk_export_opts)
        return {'FINISHED'}


class RAWKEE_OT_ExportSaveAndExportAll(bpy.types.Operator):
    """Save export options then open the file browser to export all objects"""
    bl_idname  = "rawkee.export_save_and_export_all"
    bl_label   = "Save Options & Export All"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _save_opts(context.scene.rk_export_opts)
        # Defer so this operator finishes (closing the dialog) before the file browser opens
        bpy.app.timers.register(
            lambda: bpy.ops.rawkee.export_x3d_all('INVOKE_DEFAULT') and None,
            first_interval=0.01,
        )
        return {'FINISHED'}


class RAWKEE_OT_ExportSaveAndExportSelected(bpy.types.Operator):
    """Save export options then open the file browser to export selected objects"""
    bl_idname  = "rawkee.export_save_and_export_selected"
    bl_label   = "Save Options & Export Selected"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _save_opts(context.scene.rk_export_opts)
        # Defer so this operator finishes (closing the dialog) before the file browser opens
        bpy.app.timers.register(
            lambda: bpy.ops.rawkee.export_x3d_selected('INVOKE_DEFAULT') and None,
            first_interval=0.01,
        )
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Operator — reset to defaults
# ---------------------------------------------------------------------------

class RAWKEE_OT_ResetExportOptions(bpy.types.Operator):
    """Reset all RawKee export options to their default values"""
    bl_idname  = "rawkee.reset_export_options"
    bl_label   = "Reset to Defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.rk_export_opts
        props.prj_dir             = ""
        props.image_path          = "images/"
        props.audio_path          = "audio/"
        props.inline_path         = "inline/"
        props.matx_path           = "mtlx/"
        props.use_hanim_sites     = False
        props.skin_influence      = '0'
        props.adj_tex_size        = False
        props.tex_width           = 256
        props.tex_height          = 256
        props.consolidate         = True
        props.convert_hdr_to_ktx2    = True
        props.max_cube_map_face_size = 4096
        props.proc_tex_type       = '0'
        props.proc_tex_format     = '0'
        props.file_tex_type       = '0'
        props.file_tex_format     = '0'
        props.movie_tex_type      = '0'
        props.audio_clip_type     = '0'
        props.normal_opts         = '0'
        props.crease_angle        = 0.0
        props.color_opts          = '0'
        props.is_triangles        = False
        props.decimal_limit       = 6
        props.export_tangents     = False
        props.export_empties      = True
        props.export_metadata     = True
        props.export_animations   = True
        props.launch_ext          = False
        self.report({'INFO'}, "Export options reset to defaults")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RKExportOptionsProperties,
    RAWKEE_OT_ExportOptionsDialog,
    RAWKEE_OT_ExportSaveAndExportAll,
    RAWKEE_OT_ExportSaveAndExportSelected,
    RAWKEE_OT_ResetExportOptions,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rk_export_opts = bpy.props.PointerProperty(
        type=RKExportOptionsProperties
    )
    bpy.app.handlers.load_post.append(_restore_opts_on_load)
    try:
        _load_opts(bpy.context.scene.rk_export_opts)
    except Exception:
        pass


def unregister():
    if _restore_opts_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_restore_opts_on_load)
    del bpy.types.Scene.rk_export_opts
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
