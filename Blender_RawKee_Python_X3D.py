"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the starting file for the Blender Version of the RawKee X3D Export Plugin,
    Contains the Plugin Information for Blender,
    and the file imports for running the plugin. 

    & Also at the moment adds the export drop down in the File>Export & UI panel

File Status:
    (In Development)
    Tasks: work on the geometry for now, and worry about materials, textures, and animation later.
        Learn about the Blender Node Scene Graph
"""
#Blender Plugin Information 
bl_info = {
    "name" : "Blender RawKee X3D Export Plugin",
    "author" : "UND Dream Lab, etc...", 
    "version" : (0, 0, 2),
    "blender" : (5, 0, 1),
    "location" : "File > Import-Export",
    "description" : "Rawkee X3D export plugin for Blender",
    "warnings" : "This is Plugin is Under Development", #Warning this is still under Development
    "doc_url" : "https://github.com/und-dream-lab/rawkee/blob/main/README.md", #Github Read Me File for now.
    "category" : "Import-Export", #only Export for now,
}
#Blender Imports
import bpy

#-------------------------------------
#menu panel UI. (RKWeb3D) (no functionality added yet.)
class RKMainPanel(bpy.types.Panel):
    bl_label = "RawKee (.X3D)"
    bl_idname = "PT_RAWKEE_Main_Panel"
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
    bl_idname = "PT_RAWKEE_Sub_Panel1"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'PT_RAWKEE_Main_Panel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#X3D Character and Animation Editor
class RKSubPanel2(bpy.types.Panel):
    bl_label = "X3D Character and Animation Editor"
    bl_idname = "PT_RAWKEE_Sub_Panel2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'PT_RAWKEE_Main_Panel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#X3D General Animation Editor
class RKSubPanel3(bpy.types.Panel):
    bl_label = "X3D Character and Animation Editor"
    bl_idname = "PT_RAWKEE_Sub_Panel3"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'
    bl_parent_id = 'PT_RAWKEE_Main_Panel'

    def draw(self,context):
        layout = self.layout
        rowPanel = layout.row()

        rowPanel.label(text = 'controls/pop-up windows here')

#-------------------------------------
#File>Export dropdown UI. (RKWeb3D) (no functionality added yet.)
class X3D_FileDropDown(bpy.types.Operator):
    bl_idname = "rawkee_blender_scene_export.x3d"
    bl_label = "RawKee X3D (.x3d)"
    bl_description = "Exports scene as X3D file"

#process when the export is executed.
    def execute(self,context):
        #Nothing is happening here at the moment. <===== left off here, - Thomaz Diaz (April 14th 2026)

        return {'FINISHED'}

#-------------------------------------
#
def menu_func_export(self, context):
    self.layout.operator(X3D_FileDropDown.bl_idname, text="RawKee X3D (.x3d)")




#-------------------------------------  
# register and unregister
def register():
    bpy.utils.register_class(X3D_FileDropDown)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    #-------------------------------------
    bpy.utils.register_class(RKMainPanel)

    bpy.utils.register_class(RKSubPanel1)
    bpy.utils.register_class(RKSubPanel2)
    bpy.utils.register_class(RKSubPanel3)
    #-------------------------------------

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(X3D_FileDropDown)  
    #-------------------------------------
    bpy.utils.unregister_class(RKMainPanel)

    bpy.utils.unregister_class(RKSubPanel1)
    bpy.utils.unregister_class(RKSubPanel2)
    bpy.utils.unregister_class(RKSubPanel3)
    #-------------------------------------


if __name__ == "__main__":
     register()
