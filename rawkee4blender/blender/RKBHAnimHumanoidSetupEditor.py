"""
RawKee Blender — HAnim Humanoid Setup Editor.

Maya equivalent  : rawkee/maya/RKHAnimHumanoidSetupEditor.py
                   (MayaQWidgetDockableMixin + QUiLoader panel)

Blender approach : N-panel sidebar sub-panel (parent: RAWKEE_PT_MainPanel).
                   Operators create / configure the rk_hanim_humanoid flag and
                   associated custom properties on the selected armature.
"""

import bpy
from bpy.types import Panel, Operator
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty

LOA_ITEMS = [
    ('0', "LOA 0 — Core",       "Minimal joint set"),
    ('1', "LOA 1 — Basic",      "Basic motion joint set"),
    ('2', "LOA 2 — Intermediate","Intermediate joint set"),
    ('3', "LOA 3 — Complete",   "Full joint set"),
    ('4', "LOA 4 — Extended",   "Extended / custom joint set"),
]

SKEL_CONF_ITEMS = [
    ('BASIC',   "BASIC",   "ISO-standard HAnim 2.0 skeleton configuration"),
    ('RAWKEE',  "RAWKEE",  "RawKee extended skeleton configuration"),
    ('GENERIC', "GENERIC", "User-defined generic skeleton"),
]


# ---------------------------------------------------------------------------
#  Operator — Mark selected armature as HAnimHumanoid
# ---------------------------------------------------------------------------

class RAWKEE_OT_MakeHAnimHumanoid(Operator):
    """Tag the selected armature as an HAnimHumanoid for X3D export"""
    bl_idname  = "rawkee.make_hanim_humanoid"
    bl_label   = "Make HAnimHumanoid"
    bl_options = {'REGISTER', 'UNDO'}

    hanim_name: StringProperty(
        name="Humanoid Name",
        description="Value written to HAnimHumanoid.name",
        default="HumanoidRoot",
    )
    loa: EnumProperty(
        name="Level of Articulation",
        items=LOA_ITEMS,
        default='0',
    )
    skel_conf: EnumProperty(
        name="Skeletal Configuration",
        items=SKEL_CONF_ITEMS,
        default='BASIC',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "hanim_name")
        layout.prop(self, "loa")
        layout.prop(self, "skel_conf")

    def execute(self, context):
        obj = context.active_object
        obj["rk_hanim_humanoid"] = True
        obj["rk_hanim_name"]     = self.hanim_name
        obj["rk_hanim_loa"]      = int(self.loa)
        obj["rk_hanim_skel_conf"]= self.skel_conf
        self.report({'INFO'},
            f"Armature '{obj.name}' marked as HAnimHumanoid LOA={self.loa}")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Operator — Clear HAnimHumanoid flag
# ---------------------------------------------------------------------------

class RAWKEE_OT_ClearHAnimHumanoid(Operator):
    """Remove the HAnimHumanoid tag from the selected armature"""
    bl_idname  = "rawkee.clear_hanim_humanoid"
    bl_label   = "Clear HAnimHumanoid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE' and bool(obj.get("rk_hanim_humanoid"))

    def execute(self, context):
        obj = context.active_object
        for key in ("rk_hanim_humanoid", "rk_hanim_name", "rk_hanim_loa", "rk_hanim_skel_conf"):
            if key in obj:
                del obj[key]
        self.report({'INFO'}, f"HAnimHumanoid tag removed from '{obj.name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Operator — Tag selected bone as a named HAnim joint
# ---------------------------------------------------------------------------

class RAWKEE_OT_TagHAnimJoint(Operator):
    """Tag the active pose bone with an HAnim joint name"""
    bl_idname  = "rawkee.tag_hanim_joint"
    bl_label   = "Tag HAnim Joint"
    bl_options = {'REGISTER', 'UNDO'}

    joint_name: StringProperty(
        name="HAnim Joint Name",
        description="Canonical HAnim 2.0 joint name (e.g. l_hip, r_knee)",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None
                and context.active_object.type == 'ARMATURE'
                and context.active_object.mode == 'POSE'
                and context.active_pose_bone is not None)

    def invoke(self, context, event):
        pb = context.active_pose_bone
        self.joint_name = pb.bone.get("rk_hanim_joint_name", pb.name)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        pb = context.active_pose_bone
        pb.bone["rk_hanim_joint_name"] = self.joint_name
        self.report({'INFO'}, f"Bone '{pb.name}' → HAnim joint '{self.joint_name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

class RAWKEE_PT_HAnimHumanoidSetupEditor(Panel):
    """RawKee HAnimHumanoid Setup Editor sidebar panel"""
    bl_label       = "HAnimHumanoid Setup"
    bl_idname      = "RAWKEE_PT_HAnimHumanoidSetupEditor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if obj is None or obj.type != 'ARMATURE':
            layout.label(text="Select an armature", icon='INFO')
            return

        is_hanim = bool(obj.get("rk_hanim_humanoid"))

        box = layout.box()
        if is_hanim:
            box.label(text="Status: HAnimHumanoid", icon='CHECKMARK')
            col = box.column(align=True)
            col.label(text=f"Name: {obj.get('rk_hanim_name', '—')}")
            col.label(text=f"LOA:  {obj.get('rk_hanim_loa', '—')}")
            col.label(text=f"Conf: {obj.get('rk_hanim_skel_conf', '—')}")
            box.operator("rawkee.make_hanim_humanoid", text="Edit Setup", icon='GREASEPENCIL')
            box.operator("rawkee.clear_hanim_humanoid", icon='X')
        else:
            box.label(text="Not tagged as HAnimHumanoid", icon='ERROR')
            box.operator("rawkee.make_hanim_humanoid", icon='ARMATURE_DATA')

        layout.separator()
        if obj.mode == 'POSE' and context.active_pose_bone:
            pb = context.active_pose_bone
            jn = pb.bone.get("rk_hanim_joint_name", "")
            box2 = layout.box()
            box2.label(text=f"Active bone: {pb.name}")
            if jn:
                box2.label(text=f"HAnim name: {jn}", icon='CHECKMARK')
            else:
                box2.label(text="No HAnim joint name set", icon='DOT')
            box2.operator("rawkee.tag_hanim_joint", icon='BONE_DATA')
        else:
            layout.label(text="Enter Pose mode to tag joints", icon='INFO')


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RAWKEE_OT_MakeHAnimHumanoid,
    RAWKEE_OT_ClearHAnimHumanoid,
    RAWKEE_OT_TagHAnimJoint,
    RAWKEE_PT_HAnimHumanoidSetupEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
