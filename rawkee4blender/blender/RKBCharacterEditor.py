"""
RawKee Blender — Character and Animation Editor.

Maya equivalent  : rawkee/maya/RKCharacterEditor.py
                   (MayaQWidgetDockableMixin + QTabWidget with multiple
                   QUiLoader panels: HAnim skeleton, Advanced Skeleton,
                   Generic, Animation)

Blender approach : N-panel sidebar sub-panel with:
                   - Bone/joint tree via UIList
                   - Per-bone animation-capture flags stored as custom bone
                     properties (rk_capture_t, rk_capture_r, rk_capture_s)
                   - Operators to add / remove animation-capture flags on
                     selected bones, matching the context-menu actions of the
                     Maya Character Editor tree widget
                   - LOA, humanoid name, rotation order selectors
"""

import bpy
from bpy.types  import Panel, Operator, UIList, PropertyGroup
from bpy.props  import StringProperty, BoolProperty, EnumProperty, IntProperty


# ---------------------------------------------------------------------------
#  Animation capture flag constants (mirror QAction names from Maya version)
# ---------------------------------------------------------------------------
FLAG_T   = "rk_capture_t"
FLAG_R   = "rk_capture_r"
FLAG_S   = "rk_capture_s"


# ---------------------------------------------------------------------------
#  UIList — shows armature bones with capture flags
# ---------------------------------------------------------------------------

class RAWKEE_UL_JointList(UIList):
    bl_idname = "RAWKEE_UL_JointList"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        arm = data
        bone = arm.bones.get(item.name) if isinstance(item, bpy.types.PoseBone) else item
        if bone is None:
            layout.label(text=item.name if hasattr(item,'name') else "?")
            return

        row = layout.row(align=True)
        hanim_name = bone.get("rk_hanim_joint_name", "")
        disp = hanim_name if hanim_name else bone.name
        row.label(text=disp, icon='BONE_DATA')

        # Small indicators for capture flags
        c_t = "T" if bone.get(FLAG_T) else "·"
        c_r = "R" if bone.get(FLAG_R) else "·"
        c_s = "S" if bone.get(FLAG_S) else "·"
        row.label(text=f"{c_t}{c_r}{c_s}")


# ---------------------------------------------------------------------------
#  Operators — capture / release animation channels
# ---------------------------------------------------------------------------

def _selected_bones(context):
    """Return selected pose bones or all pose bones if none selected."""
    obj = context.active_object
    if obj is None or obj.type != 'ARMATURE':
        return []
    if obj.mode == 'POSE':
        sel = [pb.bone for pb in obj.pose.bones if pb.bone.select]
        return sel if sel else [pb.bone for pb in obj.pose.bones]
    return list(obj.data.bones)


class RAWKEE_OT_CaptureT(Operator):
    """Capture Translate animation on selected joints"""
    bl_idname  = "rawkee.capture_translate"
    bl_label   = "Capture Translate"
    bl_options = {'REGISTER', 'UNDO'}

    release: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        for bone in _selected_bones(context):
            if self.release:
                if FLAG_T in bone:
                    del bone[FLAG_T]
            else:
                bone[FLAG_T] = True
        return {'FINISHED'}


class RAWKEE_OT_CaptureR(Operator):
    """Capture Rotate animation on selected joints"""
    bl_idname  = "rawkee.capture_rotate"
    bl_label   = "Capture Rotate"
    bl_options = {'REGISTER', 'UNDO'}

    release: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        for bone in _selected_bones(context):
            if self.release:
                if FLAG_R in bone:
                    del bone[FLAG_R]
            else:
                bone[FLAG_R] = True
        return {'FINISHED'}


class RAWKEE_OT_CaptureS(Operator):
    """Capture Scale animation on selected joints"""
    bl_idname  = "rawkee.capture_scale"
    bl_label   = "Capture Scale"
    bl_options = {'REGISTER', 'UNDO'}

    release: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        for bone in _selected_bones(context):
            if self.release:
                if FLAG_S in bone:
                    del bone[FLAG_S]
            else:
                bone[FLAG_S] = True
        return {'FINISHED'}


class RAWKEE_OT_CaptureTRS(Operator):
    """Capture Translate + Rotate + Scale animation on selected joints"""
    bl_idname  = "rawkee.capture_trs"
    bl_label   = "Capture T/R/S"
    bl_options = {'REGISTER', 'UNDO'}

    release: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        for bone in _selected_bones(context):
            if self.release:
                for flag in (FLAG_T, FLAG_R, FLAG_S):
                    if flag in bone:
                        del bone[flag]
            else:
                bone[FLAG_T] = True
                bone[FLAG_R] = True
                bone[FLAG_S] = True
        return {'FINISHED'}


class RAWKEE_OT_CaptureAllRootTranslateAllRotate(Operator):
    """Capture root translate and all-joints rotate (typical HAnim motion capture)"""
    bl_idname  = "rawkee.capture_root_t_all_r"
    bl_label   = "Root Trans + All Rotates"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        arm = context.active_object.data
        root_bones = [b for b in arm.bones if b.parent is None]
        for bone in arm.bones:
            bone[FLAG_R] = True
            if bone in root_bones:
                bone[FLAG_T] = True
            elif FLAG_T in bone:
                del bone[FLAG_T]
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

ROT_ORDER_ITEMS = [
    ('XYZ', "XYZ", ""),
    ('XZY', "XZY", ""),
    ('YXZ', "YXZ", ""),
    ('YZX', "YZX", ""),
    ('ZXY', "ZXY", ""),
    ('ZYX', "ZYX", ""),
]

LOA_ITEMS = [
    ('0', "LOA 0", ""), ('1', "LOA 1", ""), ('2', "LOA 2", ""),
    ('3', "LOA 3", ""), ('4', "LOA 4", ""),
]


class RAWKEE_PT_CharacterEditor(Panel):
    """RawKee Character and Animation Editor sidebar panel"""
    bl_label       = "Character & Animation Editor"
    bl_idname      = "RAWKEE_PT_CharacterEditor"
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

        arm = obj.data

        # -- Humanoid identity
        box = layout.box()
        box.label(text="Humanoid Identity", icon='ARMATURE_DATA')
        col = box.column(align=True)
        col.label(text=f"Name: {obj.get('rk_hanim_name', obj.name)}")
        col.label(text=f"LOA: {obj.get('rk_hanim_loa', '—')}")

        # -- Bone / joint list
        box2 = layout.box()
        box2.label(text="Skeleton Joints", icon='BONE_DATA')
        row = box2.row()
        row.template_list(
            "RAWKEE_UL_JointList", "",
            arm, "bones",
            arm, "active_bone_index" if hasattr(arm, 'active_bone_index') else "layers",
            rows=6,
        )

        # -- Animation capture
        box3 = layout.box()
        box3.label(text="Animation Capture", icon='ACTION')

        row = box3.row(align=True)
        row.operator("rawkee.capture_translate", text="Cap T").release = False
        row.operator("rawkee.capture_rotate",    text="Cap R").release = False
        row.operator("rawkee.capture_scale",     text="Cap S").release = False

        row2 = box3.row(align=True)
        sub = row2.operator("rawkee.capture_trs", text="Cap T/R/S")
        sub.release = False
        sub2 = row2.operator("rawkee.capture_trs", text="Rel T/R/S")
        sub2.release = True

        box3.operator("rawkee.capture_root_t_all_r", icon='POSE_HLT')

        row3 = box3.row(align=True)
        sub3 = row3.operator("rawkee.capture_translate", text="Rel T")
        sub3.release = True
        sub4 = row3.operator("rawkee.capture_rotate", text="Rel R")
        sub4.release = True
        sub5 = row3.operator("rawkee.capture_scale",  text="Rel S")
        sub5.release = True

        # -- Rotation order hint (informational, export uses Blender's own)
        box4 = layout.box()
        box4.label(text="Rotation Order (scene setting)", icon='ORIENTATION_GIMBAL')
        if obj.mode == 'POSE' and context.active_pose_bone:
            pb = context.active_pose_bone
            box4.label(text=f"Active bone: {pb.rotation_mode}")
        else:
            box4.label(text="Enter Pose mode to inspect")


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RAWKEE_UL_JointList,
    RAWKEE_OT_CaptureT,
    RAWKEE_OT_CaptureR,
    RAWKEE_OT_CaptureS,
    RAWKEE_OT_CaptureTRS,
    RAWKEE_OT_CaptureAllRootTranslateAllRotate,
    RAWKEE_PT_CharacterEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
