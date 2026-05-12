"""
File Author: 
    Thomaz Diaz, UND Dream Lab
Description: 
    This file is ment to be the GUI setup for the Blender Version of the RawKee X3D Export Plugin with execution
File Status:
    (In Development)
"""
#Imports
#-------------------------------------
import bpy

#-------------------------------------generated code vvv 
import sys
import os
# Add the parent directory to sys.path to allow importing rawkee package
_addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
from bpy_extras.io_utils import ExportHelper  # Enables file browser dialog for export operations
from bpy.props import StringProperty  # Allows defining string properties for UI elements
from rawkee.io.RKSceneTraversal import RKSceneTraversal  # Imports RawKee X3D scene creation and export

#-------------------------------------



#UI Panels 
#-------------------------------------
#menu panel UI. (RKWeb3D) (no functionality added yet.)
class RKMainPanel(bpy.types.Panel):
    bl_label = "RawKee (.X3D)"
    bl_idname = "RAWKEE_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RawKee (.X3D)'

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
#File>Export dropdown UI. (RKWeb3D) (half functional) -Thomas Diaz[12 Mayo, 2026]
class X3D_FileDropDown(bpy.types.Operator, ExportHelper):  # Operator class that inherits ExportHelper for file browser support
    bl_idname = "export.x3d"
    bl_label = "RawKee X3D (.x3d)"
    bl_description = "Exports scene as X3D file"




    #-------------------------------------generated code to understand the Example.py more. vvv (I think I understnad now I think)

    filename_ext = ".x3d"  # Sets default file extension to .x3d
    filter_glob: StringProperty(  # Creates file filter for the browser
        default="*.x3d",  # Shows only .x3d files in file browser
        options={'HIDDEN'}  # Hides the filter option from user selection
    )

    #process when the export is executed.
    def execute(self, context):
        try:  # Begin error handling block
            # Create RKSceneTraversal object
            trv = RKSceneTraversal()  # Initialize RawKee traversal object for X3D operations
            
            # Create the X3D Document
            x3dDoc = trv.getX3DObject()  # Create an empty X3D document (root container)
            
            # Create the Scene of the X3D Document
            x3dDoc.Scene = trv.getSceneObject()  # Create and assign a Scene node to hold all content
            
            # Get the active Blender scene
            blender_scene = context.scene  # Get reference to the currently active Blender scene
            
            # Get all mesh objects from the Blender scene
            for obj in blender_scene.objects:  # Loop through each object in the Blender scene
                if obj.type == 'MESH':  # Filter to process only mesh objects (skip lights, cameras, etc.)
                    # Create a Transform node for each object
                    transform = trv.processBasicNodeAddition(  # Create X3D Transform node to position the object
                        x3dDoc.Scene,  # Add it to the X3D Scene
                        "children",  # Add as a child element
                        "Transform",  # Node type for positioning
                        obj.name  # Use Blender object name as the node name
                    )
                    
                    if transform:  # Check if Transform was successfully created
                        # Set transform position from Blender object location
                        loc = obj.location  # Get the Blender object's position coordinates
                        transform.translation = (loc.x, loc.y, loc.z)  # Apply the position to the X3D Transform node
                        
                        # Create Shape node
                        shape = trv.processBasicNodeAddition(  # Create X3D Shape node to hold geometry and appearance
                            transform,  # Add it as a child of the Transform
                            "children",  # Add as a child element
                            "Shape",  # Node type for shapes
                            obj.name + "_Shape"  # Give it a descriptive name
                        )
                        
                        if shape:  # Check if Shape was successfully created
                            # Create geometry for the Shape (Box primitive)
                            geometry = trv.processBasicNodeAddition(  # Create X3D geometry node
                                shape,  # Add it as a child of the Shape
                                "geometry",  # Geometry is a specific field of Shape
                                "Box",  # Node type for box geometry
                                obj.name + "_Geometry"  # Give it a descriptive name
                            )
                            
                            # Create Appearance and Material
                            appearance = trv.processBasicNodeAddition(  # Create X3D Appearance node for material properties
                                shape,  # Add it as a child of the Shape
                                "appearance",  # Appearance is a specific field of Shape
                                "Appearance",  # Node type for appearance
                                obj.name + "_Appearance"  # Give it a descriptive name
                            )
                            
                            if appearance:  # Check if Appearance was successfully created
                                material = trv.processBasicNodeAddition(  # Create X3D Material node for color and shading
                                    appearance,  # Add it as a child of the Appearance
                                    "material",  # Material is a specific field of Appearance
                                    "Material",  # Node type for materials
                                    obj.name + "_Material"  # Give it a descriptive name
                                )
                                
                                if material:  # Check if Material was successfully created
                                    # Set default material color to white
                                    material.diffuseColor = (1.0, 1.0, 1.0)  # Set RGB to white (1=100% for each channel)
            
            # Create a default Viewpoint (camera)
            viewpoint = trv.processBasicNodeAddition(  # Create X3D Viewpoint node to act as camera
                x3dDoc.Scene,  # Add it to the X3D Scene
                "children",  # Add as a child element
                "Viewpoint",  # Node type for camera/viewpoint
                "DefaultViewpoint"  # Name for the viewpoint
            )
            if viewpoint:  # Check if Viewpoint was successfully created
                viewpoint.position = (0.0, 0.0, 20.0)  # Position camera 20 units away on Z-axis to view the scene
            
            # Create a DirectionalLight
            directionalLight = trv.processBasicNodeAddition(  # Create X3D DirectionalLight for scene illumination
                x3dDoc.Scene,  # Add it to the X3D Scene
                "children",  # Add as a child element
                "DirectionalLight",  # Node type for directional lighting (like sunlight)
                "DefaultLight"  # Name for the light
            )
            if directionalLight:  # Check if DirectionalLight was successfully created
                directionalLight.direction = (-1.0, 0.0, -1.0)  # Set light direction from upper-left
            
            # Export the X3D document to the selected file path
            trv.x3d2disk(x3dDoc, self.filepath, "x3d")  # Save the X3D document to the user-selected file path in XML format
            
            self.report({'INFO'}, f"Successfully exported X3D file to: {self.filepath}")  # Display success message to user
            return {'FINISHED'}  # Signal to Blender that the operation completed successfully
            
        except Exception as e:  # Catch any errors that occur during export
            self.report({'ERROR'}, f"Export failed: {str(e)}")  # Display error message to user
            import traceback  # Import traceback module for detailed error logging
            traceback.print_exc()  # Print full error stack trace to console for debugging
            return {'CANCELLED'}  # Signal to Blender that the operation was cancelled
    
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

