"""
RawKee Blender — Bind Pose Editor.

Maya equivalent  : rawkee/maya/RKBindPoseEditor.py
                   (MayaQWidgetDockableMixin + QUiLoader panel)
                   Stores named dagPose nodes on the rig, lets user create,
                   restore, and delete them.

Blender approach : Named poses are stored as JSON inside a custom property
                   rk_bind_poses on the armature object.  Each entry records
                   the local matrix of every pose bone.  Operators create,
                   restore, and delete these stored poses.  A UIList + panel
                   exposes the pose list.
"""

import bpy
import json
import mathutils
from bpy.types  import Panel, Operator, UIList, PropertyGroup
from bpy.props  import StringProperty, CollectionProperty, IntProperty


# ---------------------------------------------------------------------------
#  PropertyGroup — one entry in the list
# ---------------------------------------------------------------------------

class RKBindPoseItem(PropertyGroup):
    pose_name: StringProperty(name="Pose Name", default="")


# ---------------------------------------------------------------------------
#  UIList renderer
# ---------------------------------------------------------------------------

class RAWKEE_UL_BindPoseList(UIList):
    bl_idname = "RAWKEE_UL_BindPoseList"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        layout.label(text=item.pose_name, icon='POSE_HLT')


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _get_arm_obj(context):
    obj = context.active_object
    if obj and obj.type == 'ARMATURE':
        return obj
    return None


def _store_pose(arm_obj, name):
    """Snapshot current pose matrices into arm_obj["rk_bp_data"] JSON dict."""
    data = {}
    if arm_obj.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    for pb in arm_obj.pose.bones:
        m = pb.matrix_basis
        data[pb.name] = [list(row) for row in m]
    raw = json.loads(arm_obj.get("rk_bp_data", "{}"))
    raw[name] = data
    arm_obj["rk_bp_data"] = json.dumps(raw)


def _restore_pose(arm_obj, name):
    """Restore pose matrices for a named snapshot."""
    raw = json.loads(arm_obj.get("rk_bp_data", "{}"))
    data = raw.get(name, None)
    if data is None:
        return False
    prev_mode = arm_obj.mode
    if arm_obj.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    for pb in arm_obj.pose.bones:
        if pb.name in data:
            m = mathutils.Matrix(data[pb.name])
            pb.matrix_basis = m
    bpy.ops.pose.visual_transform_apply()
    return True


def _delete_pose(arm_obj, name):
    raw = json.loads(arm_obj.get("rk_bp_data", "{}"))
    if name in raw:
        del raw[name]
    arm_obj["rk_bp_data"] = json.dumps(raw)


def _sync_list(arm_obj):
    """Sync the PropertyGroup list from the JSON store."""
    raw = json.loads(arm_obj.get("rk_bp_data", "{}"))
    poses = arm_obj.rk_bind_pose_list
    poses.clear()
    for name in raw.keys():
        item = poses.add()
        item.pose_name = name


# ---------------------------------------------------------------------------
#  Operators
# ---------------------------------------------------------------------------

class RAWKEE_OT_CreateBindPose(Operator):
    """Snapshot the current pose as a named RawKee bind pose"""
    bl_idname  = "rawkee.create_bind_pose"
    bl_label   = "Create Bind Pose"
    bl_options = {'REGISTER', 'UNDO'}

    pose_name: StringProperty(
        name="Pose Name",
        description="A unique name for this bind pose (no spaces or underscores)",
        default="BindPose",
    )

    @classmethod
    def poll(cls, context):
        return _get_arm_obj(context) is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        if not self.pose_name:
            self.report({'ERROR'}, "Pose name cannot be empty")
            return {'CANCELLED'}
        _store_pose(arm_obj, self.pose_name)
        _sync_list(arm_obj)
        self.report({'INFO'}, f"Bind pose '{self.pose_name}' created on '{arm_obj.name}'")
        return {'FINISHED'}


class RAWKEE_OT_RestoreBindPose(Operator):
    """Restore the selected bind pose on the active armature"""
    bl_idname  = "rawkee.restore_bind_pose"
    bl_label   = "Restore Bind Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm_obj = _get_arm_obj(context)
        if arm_obj is None:
            return False
        return arm_obj.rk_bind_pose_index < len(arm_obj.rk_bind_pose_list)

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        idx     = arm_obj.rk_bind_pose_index
        poses   = arm_obj.rk_bind_pose_list
        if idx >= len(poses):
            self.report({'ERROR'}, "No pose selected")
            return {'CANCELLED'}
        name = poses[idx].pose_name
        ok   = _restore_pose(arm_obj, name)
        if ok:
            self.report({'INFO'}, f"Restored bind pose '{name}'")
        else:
            self.report({'ERROR'}, f"Bind pose '{name}' not found in stored data")
        return {'FINISHED'} if ok else {'CANCELLED'}


class RAWKEE_OT_DeleteBindPose(Operator):
    """Delete the selected bind pose"""
    bl_idname  = "rawkee.delete_bind_pose"
    bl_label   = "Delete Bind Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm_obj = _get_arm_obj(context)
        if arm_obj is None:
            return False
        return arm_obj.rk_bind_pose_index < len(arm_obj.rk_bind_pose_list)

    def execute(self, context):
        arm_obj = _get_arm_obj(context)
        idx     = arm_obj.rk_bind_pose_index
        poses   = arm_obj.rk_bind_pose_list
        if idx >= len(poses):
            return {'CANCELLED'}
        name = poses[idx].pose_name
        _delete_pose(arm_obj, name)
        _sync_list(arm_obj)
        self.report({'INFO'}, f"Deleted bind pose '{name}'")
        return {'FINISHED'}


class RAWKEE_OT_RefreshBindPoseList(Operator):
    """Refresh the bind pose list from stored data"""
    bl_idname  = "rawkee.refresh_bind_pose_list"
    bl_label   = "Refresh List"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _get_arm_obj(context) is not None

    def execute(self, context):
        _sync_list(_get_arm_obj(context))
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

class RAWKEE_PT_BindPoseEditor(Panel):
    """RawKee Bind Pose Editor sidebar panel"""
    bl_label       = "Bind Pose Editor"
    bl_idname      = "RAWKEE_PT_BindPoseEditor"
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

        row = layout.row()
        row.template_list(
            "RAWKEE_UL_BindPoseList", "",
            arm_obj, "rk_bind_pose_list",
            arm_obj, "rk_bind_pose_index",
            rows=4,
        )

        col = row.column(align=True)
        col.operator("rawkee.create_bind_pose",      icon='ADD',      text="")
        col.operator("rawkee.delete_bind_pose",      icon='REMOVE',   text="")
        col.separator()
        col.operator("rawkee.refresh_bind_pose_list", icon='FILE_REFRESH', text="")

        layout.operator("rawkee.restore_bind_pose",  icon='POSE_HLT')


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RKBindPoseItem,
    RAWKEE_UL_BindPoseList,
    RAWKEE_OT_CreateBindPose,
    RAWKEE_OT_RestoreBindPose,
    RAWKEE_OT_DeleteBindPose,
    RAWKEE_OT_RefreshBindPoseList,
    RAWKEE_PT_BindPoseEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.rk_bind_pose_list  = bpy.props.CollectionProperty(type=RKBindPoseItem)
    bpy.types.Object.rk_bind_pose_index = bpy.props.IntProperty(name="Active Bind Pose", default=0)


def unregister():
    del bpy.types.Object.rk_bind_pose_index
    del bpy.types.Object.rk_bind_pose_list
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
