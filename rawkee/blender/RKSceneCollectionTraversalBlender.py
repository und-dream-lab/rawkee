"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to travel throught the Scene collections get the names of all the collections and the items in the collecttions.
File Status:
    (In Development)
"""
#Imports
#-------------------------------------
import bpy

#-------------------------------------

class sceneCollectionObjects:
    pass

    #experimenting
    '''   
    def __init__(self):
        self.collections_data = {}
    
    def get_collection_objects(self, collection=None):
        """
        Traverse scene collections and extract object data with attributes.
        
        Args:
            collection: Blender collection to traverse (defaults to scene root)
        
        Returns:
            Dictionary with collection names and object attributes
        """
        if collection is None:
            collection = bpy.context.scene.collection
        
        self.collections_data[collection.name] = self._extract_collection_data(collection)
        return self.collections_data
    
    def _extract_collection_data(self, collection):
        """Extract all objects and their attributes from a collection."""
        collection_info = {
            'objects': {},
            'child_collections': {}
        }
        
        # Process objects in this collection
        for obj in collection.objects:
            collection_info['objects'][obj.name] = self._get_object_attributes(obj)
        
        # Process child collections recursively
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
        
        # Extract mesh data if object is a mesh
        if obj.type == 'MESH' and obj.data:
            obj_data['mesh_data'] = {
                'vertices': len(obj.data.vertices),
                'faces': len(obj.data.polygons),
                'edges': len(obj.data.edges)
            }
        
        # Extract materials
        if obj.data and hasattr(obj.data, 'materials'):
            for idx, material in enumerate(obj.data.materials):
                if material:
                    obj_data['materials'][material.name] = {
                        'use_nodes': material.use_nodes,
                        'diffuse_color': tuple(material.diffuse_color) if hasattr(material, 'diffuse_color') else None
                    }
        
        # Extract world properties
        if bpy.context.scene.world:
            world = bpy.context.scene.world
            obj_data['world_properties'] = {
                'world_name': world.name,
                'use_nodes': world.use_nodes,
                'background_color': tuple(world.use_nodes_get().inputs.get('Background').default_value) if world.use_nodes else None
            }
        
        return obj_data
    '''









#-------------------------------------  
def register():
    bpy.utils.register_class(sceneCollectionObjects)

    #-------------------------------------
    


def unregister():
    bpy.utils.unregister_class(sceneCollectionObjects)

    #-------------------------------------

