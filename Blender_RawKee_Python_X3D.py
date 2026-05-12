"""
File Author: 
    Thomaz Diaz, UND Dream Lab, etc
Description: 
    This file is a single file addon testing file. for Blender RawKee X3D Export Plugin,
    Contains the Plugin Information for Blender,
    and the file imports for running the plugin. 
    & Also at the moment adds the export drop down in the File>Export & UI panel

File Status:
    (Testing file.)
    (not ment to be the final add-on) -Thomas Diaz[12 Mayo, 2026]
    
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
#-------------------------------------generated code vvv
import sys
import os

# Add the parent directory to sys.path to allow importing rawkee package
_addon_dir = os.path.dirname(__file__)
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
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
        #print out the mesh dict of scen objects.
        #data = sceneObjectsData()
        #data.getSceneObjectMeshData()

        return {'FINISHED'}

#-------------------------------------

'''
#scene objects mesh data to a dictionary. for storage for .x3d file format.
class sceneObjectsData:
 #experimenting
    def __init__(self):
        self.collections_data = {}
    def get_collection_objects(self, collection=None):
        """
        Traverse scene collections and extract object data with attributes.
        Args:collection: Blender collection to traverse (defaults to scene root)
        Returns:Dictionary with collection names and object attributes
        """
        if collection is None:
            collection = bpy.context.scene.collection
        self.collections_data[collection.name] = self._extract_collection_data(collection)
        return self.collections_data
    def _extract_collection_data(self, collection):
        """Extract all objects and their attributes from a collection."""
        collection_info = {'objects': {},'child_collections': {}}
        for obj in collection.objects:
            collection_info['objects'][obj.name] = self._get_object_attributes(obj)
        for child_collection in collection.children:
            collection_info['child_collections'][child_collection.name] = self._extract_collection_data(child_collection)
        return collection_info
    def _get_object_attributes(self, obj):
        """Extract mesh data, materials, and world properties from an object."""
        obj_data = {
            'type': obj.type,
            'location': tuple(obj.location),
            'rotation': tuple(obj.rotation_euler),
            'scale': tuple(obj.scale),
            'mesh_data': None,
            'materials': {},
            'world_properties': {}
        }
        if obj.type == 'MESH' and obj.data:
            obj_data['mesh_data'] = {
                'vertices': len(obj.data.vertices),
                'faces': len(obj.data.polygons),
                'edges': len(obj.data.edges)
            }
        if obj.data and hasattr(obj.data, 'materials'):
            for idx, material in enumerate(obj.data.materials):
                if material:
                    obj_data['materials'][material.name] = {
                        'use_nodes': material.use_nodes,
                        'diffuse_color': tuple(material.diffuse_color) if hasattr(material, 'diffuse_color') else None
                    }
        if bpy.context.scene.world:
            world = bpy.context.scene.world
            obj_data['world_properties'] = {
                'world_name': world.name,
                'use_nodes': world.use_nodes,
                'background_color': tuple(world.use_nodes_get().inputs.get('Background').default_value) if world.use_nodes else None
            }
        return obj_data
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
    '''


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
