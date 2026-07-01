"""
RawKee Blender — Character Animation Clip Editor.

Maya equivalent  : rawkee/maya/RKCharacterAnimationClipEditor.py
                   (MayaQWidgetDockableMixin + QUiLoader from
                   RKCharacterAnimationClipEditorFrame.ui)

Blender approach : N-panel sidebar sub-panel that lists NLA tracks / strips on
                   the selected armature as exportable animation clips.
                   Operators let the user tag individual NLA strips for X3D
                   export and configure per-clip settings (frame range, type).
"""

import bpy
from bpy.types  import Panel, Operator, UIList, PropertyGroup
from bpy.props  import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatProperty


# ---------------------------------------------------------------------------
#  Export-type choices for a clip
# ---------------------------------------------------------------------------

CLIP_TYPE_ITEMS = [
    ('HANIM_MOTION',   "HAnimMotion",              "Export as X3D HAnimMotion node"),
    ('INTERPOLATORS',  "TimeSensor + Interpolators","Export as TimeSensor driving interpolators"),
    ('SKIP',           "Skip",                     "Do not export this clip"),
]


# ---------------------------------------------------------------------------
#  PropertyGroup on NLA strips (stored as id property on the strip via owner)
#  Because bpy.types.NlaStrip doesn't support PropertyGroup registration, we
#  fall back to storing strip export settings as JSON on the armature object.
#  The UI fetches / saves from arm_obj["rk_clip_settings"][strip.name].
# ---------------------------------------------------------------------------

import json


def _get_clip_settings(arm_obj):
    raw = arm_obj.get("rk_clip_settings", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _save_clip_settings(arm_obj, settings):
    arm_obj["rk_clip_settings"] = json.dumps(settings)


def _get_clip(arm_obj, strip_name):
    s = _get_clip_settings(arm_obj)
    return s.get(strip_name, {
        "export_type": "INTERPOLATORS",
        "enabled":     True,
        "frame_start": 0,
        "frame_end":   0,
        "fps":         30.0,
        "clip_label":  strip_name,
    })


def _save_clip(arm_obj, strip_name, clip_data):
    s = _get_clip_settings(arm_obj)
    s[strip_name] = clip_data
    _save_clip_settings(arm_obj, s)


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _get_arm_obj(context):
    obj = context.active_object
    if obj and obj.type == 'ARMATURE':
        return obj
    return None


def _get_all_strips(arm_obj):
    strips = []
    if arm_obj.animation_data:
        for track in arm_obj.animation_data.nla_tracks:
            for strip in track.strips:
                strips.append(strip)
    return strips


# ---------------------------------------------------------------------------
#  Operators
# ---------------------------------------------------------------------------

class RAWKEE_OT_TagClipForExport(Operator):
    """Configure an NLA strip for X3D export"""
    bl_idname  = "rawkee.tag_clip_export"
    bl_label   = "Configure Clip Export"
    bl_options = {'REGISTER', 'UNDO'}

    strip_name: StringProperty(default="")

    export_type: EnumProperty(
        name="Export Type",
        items=CLIP_TYPE_ITEMS,
        default='INTERPOLATORS',
    )
    enabled: BoolProperty(name="Enable Export", default=True)
    clip_label: StringProperty(name="X3D Clip Label", default="")
    fps: FloatProperty(name="FPS Override (0 = scene fps)", default=0.0, min=0.0)

    @classmethod
    def poll(cls, context):
        return _get_arm_obj(context) is not None

    def invoke(self, context, event):
        arm_obj = _get_arm_obj(context)
        if arm_obj and self.strip_name:
            cd = _get_clip(arm_obj, self.strip_name)
            self.export_type = cd.get("export_type", "INTERPOLATORS")
            self.enabled     = cd.get("enabled",     True)
            self.clip_label  = cd.get("clip_label",  self.strip_name)
            self.fps         = cd.get("fps",          0.0)
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Strip: {self.strip_name}")
        layout.prop(self, "export_type")
        layout.prop(self, "enabled")
        layout.prop(self, "clip_label")
        layout.prop(self, "fps")

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        if arm_obj is None:
            return {'CANCELLED'}
        strips = _get_all_strips(arm_obj)
        matching = [s for s in strips if s.name == self.strip_name]
        if not matching:
            self.report({'ERROR'}, f"Strip '{self.strip_name}' not found")
            return {'CANCELLED'}
        s = matching[0]
        cd = {
            "export_type": self.export_type,
            "enabled":     self.enabled,
            "clip_label":  self.clip_label if self.clip_label else self.strip_name,
            "frame_start": s.frame_start,
            "frame_end":   s.frame_end,
            "fps":         self.fps,
        }
        _save_clip(arm_obj, self.strip_name, cd)
        self.report({'INFO'}, f"Clip '{self.strip_name}' configured for export")
        return {'FINISHED'}


class RAWKEE_OT_EnableAllClips(Operator):
    """Enable all NLA strips for X3D export"""
    bl_idname  = "rawkee.enable_all_clips"
    bl_label   = "Enable All Clips"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _get_arm_obj(context) is not None

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        s = _get_clip_settings(arm_obj)
        for strip in _get_all_strips(arm_obj):
            if strip.name not in s:
                s[strip.name] = _get_clip(arm_obj, strip.name)
            s[strip.name]["enabled"] = True
        _save_clip_settings(arm_obj, s)
        return {'FINISHED'}


class RAWKEE_OT_DisableAllClips(Operator):
    """Disable all NLA strips from X3D export"""
    bl_idname  = "rawkee.disable_all_clips"
    bl_label   = "Disable All Clips"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _get_arm_obj(context) is not None

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        s = _get_clip_settings(arm_obj)
        for strip in _get_all_strips(arm_obj):
            if strip.name not in s:
                s[strip.name] = _get_clip(arm_obj, strip.name)
            s[strip.name]["enabled"] = False
        _save_clip_settings(arm_obj, s)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

class RAWKEE_PT_CharacterAnimationClipEditor(Panel):
    """RawKee Character Animation Clip Editor sidebar panel"""
    bl_label       = "Animation Clip Editor"
    bl_idname      = "RAWKEE_PT_CharacterAnimationClipEditor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout  = self.layout
        arm_obj = _get_arm_obj(context)

        if arm_obj is None:
            layout.label(text="Select an armature", icon='INFO')
            return

        strips = _get_all_strips(arm_obj)
        if not strips:
            layout.label(text="No NLA strips found", icon='INFO')
            layout.label(text="Add animation in the NLA Editor", icon='DOT')
            return

        row = layout.row(align=True)
        row.operator("rawkee.enable_all_clips",  text="Enable All",  icon='PLAY')
        row.operator("rawkee.disable_all_clips", text="Disable All", icon='PAUSE')
        layout.separator()

        for strip in strips:
            cd    = _get_clip(arm_obj, strip.name)
            color = 'SUCCESS' if cd.get("enabled", True) else 'ERROR'

            box = layout.box()
            row = box.row()
            status_icon = 'CHECKMARK' if cd.get("enabled", True) else 'X'
            row.label(
                text=f"{cd.get('clip_label', strip.name)}",
                icon=status_icon
            )
            op = row.operator("rawkee.tag_clip_export", text="", icon='SETTINGS')
            op.strip_name = strip.name

            sub = box.column(align=True)
            sub.scale_y = 0.8
            sub.label(text=f"Type: {cd.get('export_type','INTERPOLATORS')}")
            sub.label(text=f"Frames: {int(strip.frame_start)} – {int(strip.frame_end)}")
            if cd.get('fps', 0.0) > 0:
                sub.label(text=f"FPS override: {cd['fps']}")


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RAWKEE_OT_TagClipForExport,
    RAWKEE_OT_EnableAllClips,
    RAWKEE_OT_DisableAllClips,
    RAWKEE_PT_CharacterAnimationClipEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
