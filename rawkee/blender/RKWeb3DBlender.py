"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the GUI setup for the Blender Version of the RawKee X3D Export Plugin
    Current name RKWeb3DBlender.py but can be changed later. Current name was set to avoid confustion with editing the Maya RKWeb3D (RKWeb3D.py), 
    for the Maya GUI Version of the RawKee X3D Export Plugin.
File Status:
    (In Development)
    Tasks: work on the GUI for the Blender Version of RawKee X3D Export Plugin.
    & self note: make it similar to the maya layout for easy of use for users who are acotomed to the maya version, if possible. -Thomaz Diaz
"""
#Adding the RawKee (.X3D) Export option to the File>Export Dropdown menu in Blender, where the other export options are listed.

class X3D_DropDownMenu(bpy.types.Operator):
    bl_idname = "RawKeeBlender.ExportDropDownMenu"
    bl_label = "RawKee X3D (.x3d)"
    bl_description = "Exports scene as X3D file"

    def execute(self,context):
        #Nothing is happening here at the moment.    <===== left off here, - Thomaz Diaz
        #¿task to open the export menu, or to export on the current settings? TBD Later.

        return {'FINISHED'}

#Blender Adds to Menu Layout
    #def menu_func_import(self, context):
    #    self.layout.operator(X3D_DropDownMenu.bl_idname, text="RawKee X3D (.x3d)")
    # ^ not worrying about imports at the moment, but will readd the import dropdown option later.

def menu_func_export(self, context):
    self.layout.operator(X3D_DropDownMenu.bl_idname, text="RawKee X3D (.x3d)")

#Blender Register and Unregister (adds properties and or menu items)
def register():
    bpy.utils.register_class(X3D_DropDownMenu)

    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # 
def unregister():
    #
    #bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(X3D_DropDownMenu)  
if __name__ == "__main__":
     register()
