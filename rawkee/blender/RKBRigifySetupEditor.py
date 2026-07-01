"""
RawKee Blender — Rigify Setup Editor.

Maya equivalent  : rawkee/maya/RKmGearSetupEditor.py
                   (MayaQWidgetDockableMixin + QUiLoader from
                   RKmGearSetupEditor.ui — mGear rig → RawKee skeleton)

Blender substitute: Rigify is Blender's built-in procedural rigging framework
                    and serves the same role as mGear in Maya.  This panel:
                      - Detects Rigify-generated armatures in the scene
                      - Lets the user select the source Rigify rig
                      - Creates a clean RawKee export armature (duplicate with
                        identity transforms, no Rigify control bones)
                      - Links the RawKee bones to follow their Rigify
                        counterparts via Copy Transforms constraints
                      - Transfers skin weights from the Rigify deform rig to
                        the RawKee armature
                      - Sets the HAnim / export configuration on the result

Reference: Blender 5.x bpy API — armature, pose-bone constraints, rigiify.
"""

import bpy
import json
from bpy.types  import Panel, Operator
from bpy.props  import StringProperty, EnumProperty, IntProperty, BoolProperty


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

EXPORT_TYPE_ITEMS = [
    ('0', "HAnimHumanoid (BASIC)",   "Create a BASIC HAnim 2.0 export armature"),
    ('1', "HAnimHumanoid (RAWKEE)",  "Create a RAWKEE-configured export armature"),
    ('2', "Generic Skeleton",        "Create a generic (no HAnim tagging) export armature"),
]

LOA_ITEMS = [
    ('0', "LOA 0 — Core",        ""),
    ('1', "LOA 1 — Basic",       ""),
    ('2', "LOA 2 — Intermediate",""),
    ('3', "LOA 3 — Complete",    ""),
    ('4', "LOA 4 — Extended",    ""),
]


def _is_rigify_rig(obj):
    """Heuristic: Rigify-generated armatures have rigify_type attributes or 'DEF-' bones."""
    if obj.type != 'ARMATURE':
        return False
    arm = obj.data
    for bone in arm.bones:
        if bone.name.startswith("DEF-") or bone.name.startswith("ORG-"):
            return True
    # Also check for rigify_layers property
    if hasattr(arm, "rigify_layers"):
        return True
    return False


def _get_deform_bones(arm_obj):
    """Return only DEF- (deform) bones from a Rigify rig."""
    return [b for b in arm_obj.data.bones if b.name.startswith("DEF-")]


def _get_rigify_rigs(scene):
    """Return all Rigify-generated armatures in the scene."""
    return [o for o in scene.objects if _is_rigify_rig(o)]


# ---------------------------------------------------------------------------
#  Operators
# ---------------------------------------------------------------------------

class RAWKEE_OT_DetectRigifyRig(Operator):
    """Scan the scene for Rigify rigs and store the first found name"""
    bl_idname  = "rawkee.detect_rigify_rig"
    bl_label   = "Detect Rigify Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rigs = _get_rigify_rigs(context.scene)
        if rigs:
            context.scene["rk_rigify_source"] = rigs[0].name
            self.report({'INFO'}, f"Rigify rig found: {rigs[0].name}")
        else:
            self.report({'WARNING'}, "No Rigify rig detected in scene")
        return {'FINISHED'}


class RAWKEE_OT_CreateRawKeeFromRigify(Operator):
    """Create a clean RawKee export armature from the selected Rigify rig"""
    bl_idname  = "rawkee.create_rawkee_from_rigify"
    bl_label   = "Create RawKee Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    export_type: EnumProperty(
        name="Export Type",
        items=EXPORT_TYPE_ITEMS,
        default='0',
    )
    loa: EnumProperty(
        name="LOA",
        items=LOA_ITEMS,
        default='0',
    )

    @classmethod
    def poll(cls, context):
        src_name = context.scene.get("rk_rigify_source", "")
        return bool(src_name) and src_name in context.scene.objects

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_type")
        layout.prop(self, "loa")

    def execute(self, context):
        src_name = context.scene.get("rk_rigify_source", "")
        src_obj  = context.scene.objects.get(src_name)
        if src_obj is None:
            self.report({'ERROR'}, f"Source Rigify rig '{src_name}' not found")
            return {'CANCELLED'}

        # Select and duplicate
        bpy.ops.object.select_all(action='DESELECT')
        src_obj.select_set(True)
        context.view_layer.objects.active = src_obj
        bpy.ops.object.duplicate()
        dup_obj = context.active_object
        dup_obj.name = src_obj.name + "_RawKee"

        # Remove all non-DEF bones from duplicate (for Rigify rigs)
        if _is_rigify_rig(src_obj):
            bpy.ops.object.mode_set(mode='EDIT')
            arm_edit = dup_obj.data
            bones_to_remove = [b for b in arm_edit.edit_bones
                                if not b.name.startswith("DEF-")]
            for b in bones_to_remove:
                arm_edit.edit_bones.remove(b)
            # Rename DEF- bones to strip prefix
            for b in arm_edit.edit_bones:
                if b.name.startswith("DEF-"):
                    b.name = b.name[4:]
            bpy.ops.object.mode_set(mode='OBJECT')

        # Apply all transforms
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Tag as HAnimHumanoid if appropriate
        et = int(self.export_type)
        if et in (0, 1):
            dup_obj["rk_hanim_humanoid"] = True
            dup_obj["rk_hanim_loa"]      = int(self.loa)
            dup_obj["rk_hanim_name"]     = dup_obj.name
            dup_obj["rk_hanim_skel_conf"] = "BASIC" if et == 0 else "RAWKEE"

        # Store a link back to source for weight transfer
        dup_obj["rk_rigify_source"]  = src_obj.name

        context.scene["rk_rawkee_arm"] = dup_obj.name
        self.report({'INFO'}, f"RawKee skeleton '{dup_obj.name}' created")
        return {'FINISHED'}


class RAWKEE_OT_LinkRigifyToRawKee(Operator):
    """
    Add Copy Transforms constraints on the RawKee rig bones so they
    follow the Rigify DEF bones during scene animation.
    """
    bl_idname  = "rawkee.link_rigify_to_rawkee"
    bl_label   = "Link Rigify → RawKee"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        src = context.scene.get("rk_rigify_source", "")
        dst = context.scene.get("rk_rawkee_arm",    "")
        return bool(src) and bool(dst)

    def execute(self, context):
        src_name = context.scene.get("rk_rigify_source", "")
        dst_name = context.scene.get("rk_rawkee_arm",    "")
        src_obj  = context.scene.objects.get(src_name)
        dst_obj  = context.scene.objects.get(dst_name)
        if not src_obj or not dst_obj:
            self.report({'ERROR'}, "Source or destination armature not found")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        dst_obj.select_set(True)
        context.view_layer.objects.active = dst_obj
        bpy.ops.object.mode_set(mode='POSE')

        n_linked = 0
        for pb in dst_obj.pose.bones:
            # Corresponding DEF bone name in Rigify
            def_name = "DEF-" + pb.name
            if def_name in src_obj.pose.bones:
                ct = pb.constraints.new('COPY_TRANSFORMS')
                ct.name   = "RK_Follow_Rigify"
                ct.target = src_obj
                ct.subtarget = def_name
                n_linked += 1

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},
            f"Linked {n_linked} RawKee bones to Rigify DEF bones")
        return {'FINISHED'}


class RAWKEE_OT_TransferWeightsRigifyToRawKee(Operator):
    """
    Transfer skin weights from the Rigify DEF rig to the RawKee armature.
    Iterates all mesh objects, swaps the Armature modifier target,
    and renames vertex groups DEF-X → X.
    """
    bl_idname  = "rawkee.transfer_weights_rigify"
    bl_label   = "Transfer Skin Weights"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        src = context.scene.get("rk_rigify_source", "")
        dst = context.scene.get("rk_rawkee_arm",    "")
        return bool(src) and bool(dst)

    def execute(self, context):
        src_name = context.scene.get("rk_rigify_source", "")
        dst_name = context.scene.get("rk_rawkee_arm",    "")
        src_obj  = context.scene.objects.get(src_name)
        dst_obj  = context.scene.objects.get(dst_name)
        if not src_obj or not dst_obj:
            self.report({'ERROR'}, "Source or destination armature not found")
            return {'CANCELLED'}

        n_meshes = 0
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object == src_obj:
                    mod.object = dst_obj
                    # Rename DEF-X vertex groups to X
                    for vg in obj.vertex_groups:
                        if vg.name.startswith("DEF-"):
                            vg.name = vg.name[4:]
                    n_meshes += 1

        self.report({'INFO'},
            f"Weights transferred for {n_meshes} mesh(es)")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

class RAWKEE_PT_RigifySetupEditor(Panel):
    """RawKee Rigify Setup Editor — Blender replacement for mGear Setup Editor"""
    bl_label       = "Rigify Setup"
    bl_idname      = "RAWKEE_PT_RigifySetupEditor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout   = self.layout
        src_name = context.scene.get("rk_rigify_source", "")
        dst_name = context.scene.get("rk_rawkee_arm",    "")

        box = layout.box()
        box.label(text="1. Source Rigify Rig", icon='ARMATURE_DATA')
        if src_name:
            box.label(text=f"Selected: {src_name}", icon='CHECKMARK')
        else:
            box.label(text="None detected", icon='DOT')
        row = box.row(align=True)
        row.operator("rawkee.detect_rigify_rig", icon='VIEWZOOM')
        # Manual assignment via active object
        op_man = row.operator("rawkee.set_rigify_source_from_active",
                              icon='OBJECT_DATA', text="Use Active")

        box2 = layout.box()
        box2.label(text="2. Create RawKee Skeleton", icon='CON_ARMATURE')
        box2.operator("rawkee.create_rawkee_from_rigify", icon='DUPLICATE')

        if dst_name:
            box2.label(text=f"RawKee arm: {dst_name}", icon='CHECKMARK')

        box3 = layout.box()
        box3.label(text="3. Link + Transfer", icon='LINKED')
        box3.operator("rawkee.link_rigify_to_rawkee",           icon='CONSTRAINT_BONE')
        box3.operator("rawkee.transfer_weights_rigify",         icon='GROUP_VERTEX')


# ---------------------------------------------------------------------------
#  Small helper operator — assign active object as rigify source
# ---------------------------------------------------------------------------

class RAWKEE_OT_SetRigifySourceFromActive(Operator):
    """Use the active armature as the Rigify source rig"""
    bl_idname  = "rawkee.set_rigify_source_from_active"
    bl_label   = "Use Active as Rigify Source"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None
                and context.active_object.type == 'ARMATURE')

    def execute(self, context):
        context.scene["rk_rigify_source"] = context.active_object.name
        self.report({'INFO'},
            f"Rigify source set to '{context.active_object.name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RAWKEE_OT_DetectRigifyRig,
    RAWKEE_OT_CreateRawKeeFromRigify,
    RAWKEE_OT_LinkRigifyToRawKee,
    RAWKEE_OT_TransferWeightsRigifyToRawKee,
    RAWKEE_OT_SetRigifySourceFromActive,
    RAWKEE_PT_RigifySetupEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
