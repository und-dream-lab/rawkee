"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the GUI setup for the Blender Version of the RawKee X3D Export Plugin with execution
File Status:
    (In Development)
"""
#Imports
#-------------------------------------
import bpy

#-------------------------------------



#blender imports of the root so it can be multi files. 
#-------------------------------------
#menu panel UI. (RKWeb3D) (no functionality added yet.)
class RKMainPanel(bpy.types.Panel):
    bl_label = "RawKee (.X3D)"
    bl_idname = "RAWKEE_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'

    #draws the contents of the side bar panal.
    def draw(self, context):
        layout = self.layout
        rowPanel = layout.row() #short cut to make rows.

#X3D Interaction Editor
class RKSubPanel1(bpy.types.Panel):
    bl_label = "X3D Interaction Editor"
    bl_idname = "RAWKEE_PT_SubPanel1"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'RAWKEE_PT_MainPanel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#X3D Character and Animation Editor
class RKSubPanel2(bpy.types.Panel):
    bl_label = "X3D Character and Animation Editor"
    bl_idname = "RAWKEE_PT_SubPanel2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'RAWKEE_PT_MainPanel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#X3D General Animation Editor
class RKSubPanel3(bpy.types.Panel):
    bl_label = "X3D General Editor"
    bl_idname = "RAWKEE_PT_SubPanel3"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'RAWKEE_PT_MainPanel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#-------------------------------------
#File>Export dropdown UI. (RKWeb3D) (no functionality added yet.)
class X3D_FileDropDown(bpy.types.Operator):
    bl_idname = "export.x3d"
    bl_label = "RawKee X3D (.x3d)"
    bl_description = "Exports scene as X3D file"

#process when the export is executed.
    def execute(self,context):
        #empty runing from a diffrent file, <-------------------- Left off here.

        return {'FINISHED'}
    

def menu_func_export(self, context):
    self.layout.operator(X3D_FileDropDown.bl_idname, text="RawKee X3D (.x3d)")


#-------------------------------------
def register():
    bpy.utils.register_class(X3D_FileDropDown)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    bpy.utils.register_class(RKMainPanel)

    bpy.utils.register_class(RKSubPanel1)
    bpy.utils.register_class(RKSubPanel2)
    bpy.utils.register_class(RKSubPanel3)
    #-------------------------------------
    

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(X3D_FileDropDown)  
    
    bpy.utils.unregister_class(RKMainPanel)

    bpy.utils.unregister_class(RKSubPanel1)
    bpy.utils.unregister_class(RKSubPanel2)
    bpy.utils.unregister_class(RKSubPanel3)
    #-------------------------------------

