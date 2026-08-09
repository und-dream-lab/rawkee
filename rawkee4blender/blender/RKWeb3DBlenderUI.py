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
from rawkee4blender.blender.RKOrganizerBlender import RKOrganizerBlender
from rawkee4blender.blender import (RKBExportOptions, RKBHAnimHumanoidSetupEditor, RKBBindPoseEditor, RKBCharacterEditor, RKBCharacterAnimationClipEditor, RKBRigifySetupEditor, RKBMaterialXEditor)
from rawkee4blender.blender.nodes import rkBX3DSound, rkBAnimPack


# ---------------------------------------------------------------------------
# Qt co-pump state — one QApplication and one editor window shared across calls.
_qt_app      = None
_editor_win  = None
_timer_live  = False


def _pump_qt_events():
    """Blender timer callback: keep Qt responsive. Returns next interval or None to stop."""
    global _editor_win, _timer_live, _qt_app
    try:
        if _qt_app is None or _editor_win is None or not _editor_win.isVisible():
            _editor_win = None
            _timer_live = False
            return None  # unregisters the timer
        _qt_app.processEvents()
    except Exception:
        _editor_win = None
        _timer_live = False
        return None
    return 0.016 if bpy.app.version >= (5, 0, 0) else 0.05  # 60fps on 5+, 20fps on 4.x


class RAWKEE_OT_OpenSceneEditor(bpy.types.Operator):
    """Launch the RawKee X3D Interaction Editor alongside Blender"""
    bl_idname  = "rawkee.open_scene_editor"
    bl_label   = "RawKee X3D Interaction Editor"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _qt_app, _editor_win, _timer_live
        if bpy.app.version < (5, 0, 0):
            self.report({'WARNING'},
                "The X3D Interaction Editor requires Blender 5.0 or later. "
                "Use the standalone RawKee PE application instead.")
            return {'CANCELLED'}
        # Ensure PySide6's Qt DLLs are on the Windows DLL search path
        try:
            import importlib.util, os as _os
            _spec = importlib.util.find_spec('PySide6')
            if _spec and _spec.origin and hasattr(_os, 'add_dll_directory'):
                _os.add_dll_directory(_os.path.dirname(_spec.origin))
        except Exception:
            pass
        try:
            from PySide6.QtWidgets import QApplication
            from rawkee.editor.RKSceneEditor import RKSceneEditor
        except Exception as e:
            self.report({'ERROR'},
                f"Cannot open X3D Interaction Editor: {type(e).__name__}: {e}. "
                "Run blender_rawkee_install.py, then restart Blender.")
            return {'CANCELLED'}

        if _qt_app is None:
            _qt_app = QApplication.instance() or QApplication([])
            from rawkee.editor.RKSceneEditor import apply_dark_palette
            apply_dark_palette(_qt_app)

        if _editor_win is not None and _editor_win.isVisible():
            _editor_win.raise_()
            _editor_win.activateWindow()
        else:
            _editor_win = RKSceneEditor()
            try:
                from PySide6.QtWidgets import QFileIconProvider
                from PySide6.QtCore import QFileInfo
                _editor_win.setWindowIcon(
                    QFileIconProvider().icon(QFileInfo(bpy.app.binary_path)))
            except Exception:
                pass
            _editor_win.show()

        if not _timer_live:
            bpy.app.timers.register(_pump_qt_events, first_interval=0.016)
            _timer_live = True

        return {'FINISHED'}

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
        operator.report({'INFO'}, f"X3D export complete: {filepath}  |  Log: Scripting workspace → Text Editor → 'RawKee Export Log'")
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
    def invoke(self, context, event):
        prj = context.scene.rk_export_opts.prj_dir
        if prj:
            self.filepath = prj
        return ExportHelper.invoke(self, context, event)
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
    def invoke(self, context, event):
        prj = context.scene.rk_export_opts.prj_dir
        if prj:
            self.filepath = prj
        return ExportHelper.invoke(self, context, event)
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
    bl_label       = "RawKee X3D for Blender"
    bl_idname      = "RAWKEE_PT_MainPanel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator("rawkee.export_options_dialog", icon='PREFERENCES', text="X3D Export Options")
        layout.separator()
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator("rawkee.open_scene_editor",     icon='WINDOW',       text="X3D Interaction Editor")


class RAWKEE_PT_SubPanel_AddNodes(bpy.types.Panel):
    """Add RawKee custom nodes"""
    bl_label       = "Add Custom Nodes"
    bl_idname      = "RAWKEE_PT_SubPanel_AddNodes"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("rawkee.add_x3d_sound", icon='SPEAKER', text="Add X3D Sound")


class RAWKEE_PT_SubPanel_Links(bpy.types.Panel):
    """X3D external websites"""
    bl_label       = "X3D External Websites"
    bl_idname      = "RAWKEE_PT_SubPanel_Links"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        pass


class RAWKEE_PT_ExternalWebsites_Viewers(bpy.types.Panel):
    bl_label       = "X3D Viewers"
    bl_idname      = "RAWKEE_PT_ExternalWebsites_Viewers"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    bl_parent_id   = 'RAWKEE_PT_SubPanel_Links'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("rawkee.show_x_ite",  icon='URL')
        col.operator("rawkee.show_cge",    icon='URL')
        col.operator("rawkee.show_x3dom",  icon='URL')


class RAWKEE_PT_ExternalWebsites_Editors(bpy.types.Panel):
    bl_label       = "X3D Editors"
    bl_idname      = "RAWKEE_PT_ExternalWebsites_Editors"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    bl_parent_id   = 'RAWKEE_PT_SubPanel_Links'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        self.layout.operator("rawkee.show_sunrize", icon='URL')


class RAWKEE_PT_ExternalWebsites_Resources(bpy.types.Panel):
    bl_label       = "Resources"
    bl_idname      = "RAWKEE_PT_ExternalWebsites_Resources"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee X3D for Blender'
    bl_parent_id   = 'RAWKEE_PT_SubPanel_Links'
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        col = self.layout.column(align=True)
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
    self.layout.operator(
        "rawkee.export_options_dialog",
        text="RawKee X3D - Export Options",
        icon='PREFERENCES',
    )


_own_classes = [
    RAWKEE_OT_OpenSceneEditor,
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
    RAWKEE_PT_SubPanel_AddNodes,
    RAWKEE_PT_SubPanel_Links,
    RAWKEE_PT_ExternalWebsites_Viewers,
    RAWKEE_PT_ExternalWebsites_Editors,
    RAWKEE_PT_ExternalWebsites_Resources,
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


def _setup_pip_paths():
    """Ensure user site-packages is on sys.path at addon startup."""
    import importlib, os as _os
    try:
        import site as _site
        user_site = _os.path.normpath(_site.getusersitepackages())
        if user_site not in [_os.path.normpath(p) for p in sys.path]:
            sys.path.insert(0, user_site)
            importlib.invalidate_caches()
    except Exception as e:
        print(f"[RawKee] _setup_pip_paths failed: {e}")


def register():
    _setup_pip_paths()
    for cls in _own_classes:
        bpy.utils.register_class(cls)

    for mod in _sub_modules:
        try:
            mod.register()
        except Exception as exc:
            import traceback
            print(f"[RawKee] WARNING: could not register sub-module "
                  f"'{getattr(mod, '__name__', mod)}': {exc}")
            traceback.print_exc()

    bpy.types.TOPBAR_MT_file_export.append(_menu_export)
    print("[RawKee] Addon registered. "
          "In the 3D Viewport press N and select the 'RawKee X3D for Blender' tab. "
          "File > Export also has a 'RawKee X3D' entry.")


def unregister():
    global _editor_win, _timer_live
    if _editor_win is not None:
        try:
            _editor_win.close()
        except Exception:
            pass
        _editor_win = None
    if _timer_live:
        try:
            bpy.app.timers.unregister(_pump_qt_events)
        except Exception:
            pass
        _timer_live = False
    bpy.types.TOPBAR_MT_file_export.remove(_menu_export)

    for mod in reversed(_sub_modules):
        try:
            mod.unregister()
        except Exception as exc:
            print(f"[RawKee] WARNING: could not unregister sub-module "
                  f"'{getattr(mod, '__name__', mod)}': {exc}")

    for cls in reversed(_own_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as exc:
            print(f"[RawKee] WARNING: could not unregister class "
                  f"'{cls.__name__}': {exc}")
