"""
RawKee Blender - Main UI wiring (RKWeb3D Blender equivalent).

Maya equivalent  : rawkee/maya/RKWeb3D.py
Blender approach : File > Export entry + N-panel sidebar tab 'RawKee (.X3D)'
"""

import bpy
import os
import sys
import webbrowser

_addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)

from bpy_extras.io_utils import ExportHelper
from bpy.props           import StringProperty, EnumProperty

from rawkee.io.RKSceneTraversal        import RKSceneTraversal
from rawkee.blender.RKOrganizerBlender import RKOrganizerBlender
from rawkee.blender import (
    RKBExportOptions,
    RKBHAnimHumanoidSetupEditor,
    RKBBindPoseEditor,
    RKBCharacterEditor,
    RKBCharacterAnimationClipEditor,
    RKBRigifySetupEditor,
    RKBMaterialXEditor,
)
from rawkee.blender.nodes import rkBX3DSound, rkBAnimPack


# ---------------------------------------------------------------------------
ENCODING_ITEMS = [
    ('x3d',  "X3D XML (.x3d)",      "X3D 4.1 XML encoding"),
    ('x3dv', "X3D Classic (.x3dv)", "X3D 4.1 Classic VRML-style encoding"),
    ('x3dj', "X3D JSON (.x3dj)",    "X3D 4.1 JSON encoding"),
    ('json', "JSON (.json)",        "X3D 4.1 JSON (alternate extension)"),
]


def _run_export(operator, context, filepath, encoding, selected_only):
    try:
        rko = RKOrganizerBlender()
        rko.prepForSceneTraversal(context)
        x3dDoc       = rko.trv.getX3DObject()
        x3dDoc.Scene = rko.trv.getSceneObject()
        bkNode = rko.trv.processBasicNodeAddition(
            x3dDoc.Scene, "children", "Background", "DefaultBackground")
        if bkNode and context.scene.world:
            c = context.scene.world.color
            bkNode.skyColor[0] = (c.r, c.g, c.b)
        fext = os.path.splitext(filepath)[1].lstrip('.')
        enc  = fext if fext in ('x3d','x3dv','x3dj','json') else encoding
        if selected_only:
            rko.blender2x3d_selected(x3dDoc.Scene, context, filepath, enc)
        else:
            rko.blender2x3d(x3dDoc.Scene, context, filepath, enc)
        rko.trv.x3d2disk(x3dDoc, filepath, enc)
        if context.scene.rk_export_opts.launch_ext:
            try:
                webbrowser.open(filepath)
            except Exception:
                pass
        del x3dDoc, rko
        operator.report({'INFO'}, f"X3D export complete: {filepath}")
        return {'FINISHED'}
    except Exception as e:
        import traceback; traceback.print_exc()
        operator.report({'ERROR'}, f"X3D export failed: {str(e)}")
        return {'CANCELLED'}


# ---------------------------------------------------------------------------
class RAWKEE_OT_ExportX3DAll(bpy.types.Operator, ExportHelper):
    """Export the entire Blender scene as an X3D file"""
    bl_idname = "rawkee.export_x3d_all"
    bl_label  = "RawKee -- Export All X3D"
    bl_options = {'REGISTER'}
    filename_ext = ".x3d"
    filter_glob: StringProperty(default="*.x3d;*.x3dv;*.x3dj;*.json", options={'HIDDEN'})
    encoding: EnumProperty(name="Encoding", items=ENCODING_ITEMS, default='x3d')
    def execute(self, context):
        return _run_export(self, context, self.filepath, self.encoding, False)
    def draw(self, context):
        self.layout.prop(self, "encoding")


class RAWKEE_OT_ExportX3DSelected(bpy.types.Operator, ExportHelper):
    """Export only selected objects as an X3D file"""
    bl_idname = "rawkee.export_x3d_selected"
    bl_label  = "RawKee -- Export Selected X3D"
    bl_options = {'REGISTER'}
    filename_ext = ".x3d"
    filter_glob: StringProperty(default="*.x3d;*.x3dv;*.x3dj;*.json", options={'HIDDEN'})
    encoding: EnumProperty(name="Encoding", items=ENCODING_ITEMS, default='x3d')
    def execute(self, context):
        return _run_export(self, context, self.filepath, self.encoding, True)
    def draw(self, context):
        self.layout.prop(self, "encoding")


class RAWKEE_OT_SetProject(bpy.types.Operator):
    """Set the RawKee project directory"""
    bl_idname = "rawkee.set_project"
    bl_label  = "Set RawKee Project"
    directory: StringProperty(subtype='DIR_PATH')
    def execute(self, context):
        context.scene.rk_export_opts.prj_dir = self.directory
        self.report({'INFO'}, f"Project dir: {self.directory}")
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ---------------------------------------------------------------------------
class RAWKEE_OT_ShowHelpWiki(bpy.types.Operator):
    bl_idname = "rawkee.show_help_wiki"; bl_label = "RawKee Help (GitHub)"
    def execute(self, _): webbrowser.open("https://github.com/und-dream-lab/rawkee/"); return {'FINISHED'}

class RAWKEE_OT_ShowX_ITE(bpy.types.Operator):
    bl_idname = "rawkee.show_x_ite"; bl_label = "X_ITE X3D Browser"
    def execute(self, _): webbrowser.open("https://create3000.github.io/x_ite/"); return {'FINISHED'}

class RAWKEE_OT_ShowSunrize(bpy.types.Operator):
    bl_idname = "rawkee.show_sunrize"; bl_label = "Sunrize X3D Editor"
    def execute(self, _): webbrowser.open("https://create3000.github.io/sunrize/"); return {'FINISHED'}

class RAWKEE_OT_ShowCGE(bpy.types.Operator):
    bl_idname = "rawkee.show_cge"; bl_label = "Castle Game Engine"
    def execute(self, _): webbrowser.open("https://castle-engine.io/"); return {'FINISHED'}

class RAWKEE_OT_ShowX3DOM(bpy.types.Operator):
    bl_idname = "rawkee.show_x3dom"; bl_label = "X3DOM"
    def execute(self, _): webbrowser.open("https://www.x3dom.org/"); return {'FINISHED'}

class RAWKEE_OT_ShowDreamLab(bpy.types.Operator):
    bl_idname = "rawkee.show_dream_lab"; bl_label = "UND DREAM Lab"
    def execute(self, _): webbrowser.open("https://arts-sciences.und.edu/academics/digital-media-production/labs.html"); return {'FINISHED'}

class RAWKEE_OT_ShowWeb3D(bpy.types.Operator):
    bl_idname = "rawkee.show_web3d"; bl_label = "Web3D Consortium"
    def execute(self, _): webbrowser.open("https://www.web3d.org/"); return {'FINISHED'}

class RAWKEE_OT_ShowMSF(bpy.types.Operator):
    bl_idname = "rawkee.show_msf"; bl_label = "Metaverse Standards Forum"
    def execute(self, _): webbrowser.open("https://metaverse-standards.org/"); return {'FINISHED'}


# ---------------------------------------------------------------------------
class RKMainPanel(bpy.types.Panel):
    """RawKee PE (X3D) main sidebar panel"""
    bl_label       = "RawKee (.X3D)"
    bl_idname      = "RAWKEE_PT_MainPanel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    def draw(self, context):
        self.layout.label(text="RawKee PE (X3D) v0.1 - Blender 5", icon='WORLD')


class RAWKEE_PT_SubPanel_Export(bpy.types.Panel):
    """File Import / Export actions"""
    bl_label       = "File - Import / Export"
    bl_idname      = "RAWKEE_PT_SubPanel_Export"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("rawkee.export_x3d_all",      icon='EXPORT', text="Export All X3D")
        col.operator("rawkee.export_x3d_selected", icon='EXPORT', text="Export Selected X3D")
        col.separator()
        col.operator("rawkee.set_project", icon='FILE_FOLDER', text="Set RawKee Project")


class RAWKEE_PT_SubPanel_AddNodes(bpy.types.Panel):
    """Add RawKee custom nodes"""
    bl_label       = "Add Custom Nodes"
    bl_idname      = "RAWKEE_PT_SubPanel_AddNodes"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("rawkee.add_x3d_sound", icon='SPEAKER', text="Add X3D Sound")
        col.operator("rawkee.add_anim_pack",  icon='ACTION',  text="Add RK AnimPack")


class RAWKEE_PT_SubPanel_Links(bpy.types.Panel):
    """3rd party X3D tools and viewers"""
    bl_label       = "3rd Party Tools & Viewers"
    bl_idname      = "RAWKEE_PT_SubPanel_Links"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="X3D Viewers:", icon='WORLD_DATA')
        col.operator("rawkee.show_x_ite",   icon='URL')
        col.operator("rawkee.show_cge",     icon='URL')
        col.operator("rawkee.show_x3dom",   icon='URL')
        col.separator()
        col.label(text="X3D Editors:", icon='NODE_COMPOSITING')
        col.operator("rawkee.show_sunrize", icon='URL')
        col.separator()
        col.label(text="Resources:", icon='BOOKMARKS')
        col.operator("rawkee.show_help_wiki",  icon='URL')
        col.operator("rawkee.show_dream_lab",  icon='URL')
        col.operator("rawkee.show_web3d",      icon='URL')
        col.operator("rawkee.show_msf",        icon='URL')


# ---------------------------------------------------------------------------
def _menu_export(self, context):
    self.layout.operator(
        RAWKEE_OT_ExportX3DAll.bl_idname,
        text="RawKee X3D (.x3d / .x3dv / .x3dj)",
        icon='WORLD_DATA',
    )


_own_classes = [
    RAWKEE_OT_ExportX3DAll,
    RAWKEE_OT_ExportX3DSelected,
    RAWKEE_OT_SetProject,
    RAWKEE_OT_ShowHelpWiki,
    RAWKEE_OT_ShowX_ITE,
    RAWKEE_OT_ShowSunrize,
    RAWKEE_OT_ShowCGE,
    RAWKEE_OT_ShowX3DOM,
    RAWKEE_OT_ShowDreamLab,
    RAWKEE_OT_ShowWeb3D,
    RAWKEE_OT_ShowMSF,
    RKMainPanel,
    RAWKEE_PT_SubPanel_Export,
    RAWKEE_PT_SubPanel_AddNodes,
    RAWKEE_PT_SubPanel_Links,
]

_sub_modules = [
    rkBX3DSound,
    rkBAnimPack,
    RKBExportOptions,
    RKBHAnimHumanoidSetupEditor,
    RKBBindPoseEditor,
    RKBCharacterEditor,
    RKBCharacterAnimationClipEditor,
    RKBRigifySetupEditor,
    RKBMaterialXEditor,
]


def register():
    for mod in _sub_modules:
        mod.register()
    for cls in _own_classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(_menu_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(_menu_export)
    for cls in reversed(_own_classes):
        bpy.utils.unregister_class(cls)
    for mod in reversed(_sub_modules):
        mod.unregister()
