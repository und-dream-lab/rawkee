"""
RawKee Blender — MaterialX Export Type Editor.

Maya equivalent  : rawkee/maya/RKMaterialXEditor.py
                   (MayaQWidgetDockableMixin + QTreeWidget listing
                   MaterialXSurfaceShader nodes, each tagged asX3DShader)

Blender approach : N-panel sidebar sub-panel that lists every material in the
                   active scene.  Each material can be tagged with a custom
                   property rk_as_x3d_shader = True/False to control whether
                   it exports as an X3D PackagedShader/ComposedShader pair
                   (True) or as a PhysicalMaterial/Material node (False).
"""

import bpy
from bpy.types  import Panel, Operator, UIList, PropertyGroup
from bpy.props  import BoolProperty, StringProperty


# ---------------------------------------------------------------------------
#  UIList — one row per material
# ---------------------------------------------------------------------------

class RAWKEE_UL_MaterialXList(UIList):
    bl_idname = "RAWKEE_UL_MaterialXList"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        mat = item
        if mat is None:
            return
        is_shader = bool(mat.get("rk_as_x3d_shader", False))
        row = layout.row(align=True)
        row.label(text=mat.name, icon='MATERIAL')
        row.label(
            text="PackagedShader" if is_shader else "PhysicalMaterial",
            icon='CHECKMARK' if is_shader else 'DOT'
        )


# ---------------------------------------------------------------------------
#  Operators
# ---------------------------------------------------------------------------

class RAWKEE_OT_SetMaterialAsShader(Operator):
    """Mark the selected material for export as an X3D PackagedShader/ComposedShader"""
    bl_idname  = "rawkee.set_material_as_shader"
    bl_label   = "Set as X3D Shader"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.rk_mtlx_active_index < len(bpy.data.materials)

    def execute(self, context):
        idx = context.scene.rk_mtlx_active_index
        mats = list(bpy.data.materials)
        if idx < len(mats):
            mats[idx]["rk_as_x3d_shader"] = True
            self.report({'INFO'}, f"'{mats[idx].name}' → PackagedShader/ComposedShader")
        return {'FINISHED'}


class RAWKEE_OT_SetMaterialAsMaterial(Operator):
    """Mark the selected material for export as an X3D PhysicalMaterial/Material"""
    bl_idname  = "rawkee.set_material_as_material"
    bl_label   = "Set as X3D Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.rk_mtlx_active_index < len(bpy.data.materials)

    def execute(self, context):
        idx = context.scene.rk_mtlx_active_index
        mats = list(bpy.data.materials)
        if idx < len(mats):
            mats[idx]["rk_as_x3d_shader"] = False
            self.report({'INFO'}, f"'{mats[idx].name}' → PhysicalMaterial/Material")
        return {'FINISHED'}


class RAWKEE_OT_SetAllMaterialsAsShader(Operator):
    """Mark all scene materials as X3D PackagedShader"""
    bl_idname  = "rawkee.set_all_materials_shader"
    bl_label   = "Set All as Shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mat in bpy.data.materials:
            mat["rk_as_x3d_shader"] = True
        self.report({'INFO'}, "All materials set to PackagedShader/ComposedShader")
        return {'FINISHED'}


class RAWKEE_OT_SetAllMaterialsAsMaterial(Operator):
    """Mark all scene materials as X3D PhysicalMaterial"""
    bl_idname  = "rawkee.set_all_materials_material"
    bl_label   = "Set All as Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mat in bpy.data.materials:
            mat["rk_as_x3d_shader"] = False
        self.report({'INFO'}, "All materials set to PhysicalMaterial/Material")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel
# ---------------------------------------------------------------------------

class RAWKEE_PT_MaterialXEditor(Panel):
    """RawKee MaterialX Export Type Editor — Experimental"""
    bl_label       = "MaterialX Export Type (Exp.)"
    bl_idname      = "RAWKEE_PT_MaterialXEditor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'RawKee (.X3D)'
    bl_parent_id   = 'RAWKEE_PT_MainPanel'
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        mats   = list(bpy.data.materials)

        if not mats:
            layout.label(text="No materials in file", icon='INFO')
            return

        row = layout.row()
        # We use bpy.data.materials as the collection for template_list
        row.template_list(
            "RAWKEE_UL_MaterialXList", "",
            bpy.data, "materials",
            context.scene, "rk_mtlx_active_index",
            rows=6,
        )

        col = layout.column(align=True)
        col.operator("rawkee.set_material_as_shader",   icon='NODE_MATERIAL')
        col.operator("rawkee.set_material_as_material", icon='MATERIAL')
        col.separator()
        col.operator("rawkee.set_all_materials_shader",   text="All → Shader",   icon='NODE_MATERIAL')
        col.operator("rawkee.set_all_materials_material", text="All → Material",  icon='MATERIAL')

        # Summary
        n_shader = sum(1 for m in mats if m.get("rk_as_x3d_shader", False))
        n_mat    = len(mats) - n_shader
        layout.separator()
        layout.label(text=f"Shaders: {n_shader}  |  Materials: {n_mat}", icon='INFO')


# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

classes = [
    RAWKEE_UL_MaterialXList,
    RAWKEE_OT_SetMaterialAsShader,
    RAWKEE_OT_SetMaterialAsMaterial,
    RAWKEE_OT_SetAllMaterialsAsShader,
    RAWKEE_OT_SetAllMaterialsAsMaterial,
    RAWKEE_PT_MaterialXEditor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rk_mtlx_active_index = bpy.props.IntProperty(
        name="Active Material Index", default=0
    )


def unregister():
    del bpy.types.Scene.rk_mtlx_active_index
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
