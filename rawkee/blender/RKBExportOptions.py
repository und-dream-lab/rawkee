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
import os
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty
)
from bpy.types import PropertyGroup


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
        default="/images",
    )
    audio_path: StringProperty(
        name="Audio Sub-path",
        description="Sub-directory (relative to project dir) for exported audio",
        default="/audio",
    )
    inline_path: StringProperty(
        name="Inline Sub-path",
        description="Sub-directory (relative to project dir) for X3D Inline files",
        default="/inline",
    )
    matx_path: StringProperty(
        name="MaterialX Sub-path",
        description="Sub-directory (relative to project dir) for MaterialX documents",
        default="/mtlx",
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
#  Operator — reset to defaults
# ---------------------------------------------------------------------------

class RAWKEE_OT_ResetExportOptions(bpy.types.Operator):
    """Reset all RawKee export options to their default values"""
    bl_idname  = "rawkee.reset_export_options"
    bl_label   = "Reset to Defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.rk_export_opts
        # Trigger defaults by re-assigning a fresh PropertyGroup snapshot
        for attr in RKExportOptionsProperties.__annotations__:
            prop_def = RKExportOptionsProperties.__annotations__[attr]
            # Skip complex enums/strings — just tell Blender to reset
        # Simplest approach: explicitly re-set each
        props.prj_dir        = ""
        props.image_path     = "/images"
        props.audio_path     = "/audio"
        props.inline_path    = "/inline"
        props.matx_path      = "/mtlx"
        props.use_hanim_sites = False
        props.skin_influence  = '0'
        props.adj_tex_size    = False
        props.tex_width       = 256
        props.tex_height      = 256
        props.consolidate     = True
        props.proc_tex_type   = '0'
        props.proc_tex_format = '0'
        props.file_tex_type   = '0'
        props.file_tex_format = '0'
        props.movie_tex_type  = '0'
        props.audio_clip_type = '0'
        props.normal_opts     = '0'
        props.crease_angle    = 0.0
        props.color_opts      = '0'
        props.is_triangles    = False
        props.decimal_limit   = 6
        props.export_tangents = False
        props.export_empties  = True
        props.export_metadata = True
        props.export_animations = True
        props.launch_ext      = False
        self.report({'INFO'}, "Export options reset to defaults")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Sidebar Panel — shown in the RawKee N-panel tab
# ---------------------------------------------------------------------------

class RAWKEE_PT_ExportOptions(bpy.types.Panel):
    """RawKee X3D Export Options sidebar panel"""
    bl_label       = "Export Options"
    bl_idname      = "RAWKEE_PT_ExportOptions"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        opts   = context.scene.rk_export_opts

        # -- Paths
        box = layout.box()
        box.label(text="Paths", icon='FILE_FOLDER')
        col = box.column(align=True)
        col.prop(opts, "prj_dir")
        col.prop(opts, "image_path")
        col.prop(opts, "audio_path")
        col.prop(opts, "inline_path")
        col.prop(opts, "matx_path")

        # -- HAnim
        box = layout.box()
        box.label(text="HAnim / Skinning", icon='ARMATURE_DATA')
        col = box.column(align=True)
        col.prop(opts, "use_hanim_sites")
        col.prop(opts, "skin_influence")

        # -- Textures
        box = layout.box()
        box.label(text="Textures", icon='IMAGE_DATA')
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(opts, "adj_tex_size")
        if opts.adj_tex_size:
            row2 = col.row(align=True)
            row2.prop(opts, "tex_width")
            row2.prop(opts, "tex_height")
        col.prop(opts, "consolidate")
        col.prop(opts, "proc_tex_type")
        if opts.proc_tex_type != '0':
            col.prop(opts, "proc_tex_format")
        col.prop(opts, "file_tex_type")
        if opts.file_tex_type not in ('0',):
            col.prop(opts, "file_tex_format")
        col.prop(opts, "movie_tex_type")
        col.prop(opts, "audio_clip_type")

        # -- Geometry
        box = layout.box()
        box.label(text="Geometry & Output", icon='MESH_DATA')
        col = box.column(align=True)
        col.prop(opts, "normal_opts")
        col.prop(opts, "crease_angle")
        col.prop(opts, "color_opts")
        col.prop(opts, "is_triangles")
        col.prop(opts, "export_tangents")
        col.prop(opts, "decimal_limit")

        # -- Misc
        box = layout.box()
        box.label(text="Misc", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(opts, "export_empties")
        col.prop(opts, "export_metadata")
        col.prop(opts, "export_animations")
        col.prop(opts, "launch_ext")

        layout.separator()
        layout.operator("rawkee.reset_export_options", icon='LOOP_BACK')


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RKExportOptionsProperties,
    RAWKEE_OT_ResetExportOptions,
    RAWKEE_PT_ExportOptions,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rk_export_opts = bpy.props.PointerProperty(
        type=RKExportOptionsProperties
    )


def unregister():
    del bpy.types.Scene.rk_export_opts
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
