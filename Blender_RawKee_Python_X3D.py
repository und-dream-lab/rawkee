"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the starting file for the Blender Version of the RawKee X3D Export Plugin,
    Contains the Plugin Information for Blender,
    and the file imports for running the plugin. 

    & Also at the moment adds the export drop down in the File>Export

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

#Adds the File>Export>RawKee X3D (.x3d) and File>Import>RawKee X3D (.x3d) dropdowns
class X3D_FileDropDown(bpy.types.Operator):
    bl_idname = "rawkee_blender_scene_export.x3d"
    bl_label = "RawKee X3D (.x3d)"
    bl_description = "Exports scene as X3D file"

#process when the export is exicuted.
    def execute(self,context):
        #Nothing is happening here at the moment. <===== left off here, - Thomaz Diaz (April 14th 2026)

        return {'FINISHED'}

#Blender options.
def menu_func_export(self, context):
    self.layout.operator(X3D_FileDropDown.bl_idname, text="RawKee X3D (.x3d)")
    
#Blender Register and Unregister
def register():
    bpy.utils.register_class(X3D_FileDropDown)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # 
def unregister():
    #
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(X3D_FileDropDown)  
if __name__ == "__main__":
     register()
