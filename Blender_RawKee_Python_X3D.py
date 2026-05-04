"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the starting file for the Blender Version of the RawKee X3D Export Plugin,
    Contains the Plugin Information for Blender,
    and the file imports for running the plugin. 

    & Also at the moment adds the export drop down in the File>Export & UI panel

    
"""
#Blender Plugin Information 
bl_info = {
    "name" : "BlenderRawKeeX3DExport",
    "author" : "UND Dream Lab, etc...", 
    "version" : (0, 0, 2),
    "blender" : (5, 0, 1),
    "location" : "File > Import-Export",
    "description" : "Rawkee X3D export plugin for Blender",
    #"warnings" : "This is Plugin is Under Development", #Warning this is still under Development
    #"doc_url" : "https://github.com/und-dream-lab/rawkee/blob/main/README.md", #Github Read Me File for now.
    "category" : "Import-Export", #only Export for now,
}
#Blender Imports
import bpy
#from rawkee.io.RKSceneTraversal import *
#blender imrpots of the root so it can be multi files. 
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
        #print out the mesh dict of scen objects.
        data = sceneObjectsData()
        data.getSceneObjectMeshData()

        return {'FINISHED'}

#-------------------------------------
#scene objects mesh data to a dictionary. for storage for .x3d file format.

class sceneObjectsData:
    def getSceneObjectMeshData(self):
        self.sceneObjectsDict = {}
        depsgraph = bpy.context.evaluated_depsgraph_get()

        # cycles through thr objects in the scene.
        #¿len(bpy.context.scene.objects)?
        # its a Collection type not a list
        for obj in bpy.context.scene.objects:
            print(f"Checking object: {obj.name}, Type: {obj.type}, Hide Render: {obj.hide_render}")

            if obj.type != 'MESH' or obj.hide_render:
                continue

            try:
                obj_eval = obj.evaluated_get(depsgraph)
                mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

                if mesh and len(mesh.vertices) > 0:
                    vertices = []
                    for v in mesh.vertices:
                        global_pos = obj.matrix_world @ v.co
                        vertices.append((global_pos.x, global_pos.y, global_pos.z))

                    faces = [list(poly.vertices) for poly in mesh.polygons]

                    self.sceneObjectsDict[obj.name] = {
                        "vertices": vertices,
                        "faces": faces
                    }

                    print(f"Added {obj.name}: {len(vertices)} verts, {len(faces)} faces")

                else:
                    print(f"Skipped {obj.name}: no mesh data")

            except Exception as e:
                print(f"ERROR processing {obj.name}: {e}")

            finally:
                try:
                    obj_eval.to_mesh_clear()
                except:
                    pass

        print(f"Collected {len(self.sceneObjectsDict)} objects")

        return self.sceneObjectsDict



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
    ##bpy.utils.register_class(sceneObjectsData)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(X3D_FileDropDown)  
    #-------------------------------------
    bpy.utils.unregister_class(RKMainPanel)

    bpy.utils.unregister_class(RKSubPanel1)
    bpy.utils.unregister_class(RKSubPanel2)
    bpy.utils.unregister_class(RKSubPanel3)
    #-------------------------------------
    ##bpy.utils.unregister_class(sceneObjectsData)


if __name__ == "__main__":
     register()
