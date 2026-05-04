"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    The start of the addon to be able to run with the multiple files, and import register and unregister them.
    To be able to export to .X3D file format.
Addon Status:
    (In Development) Tasks: work on the geometry for now, and worry about materials, textures, and animation later.
        Learn about the Blender Node Scene Graph
"""
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
#Imports
#-------------------------------------
from . rawkee.blender import RKWeb3DBlender #imports the rawkee folder and the blender folder inside of it to the RKWeb3DBlender script for the UI.

#-------------------------------------
import sys
import importlib
if "RKWeb3DBlender" in locals():
    importlib.reload(RKWeb3DBlender)
    print("reloaded")



#Blender register & unregister for the Imports.
#-------------------------------------
def register():
    RKWeb3DBlender.register()
def unregister():
    RKWeb3DBlender.unregister()
#-------------------------------------



# for test to update and not having to reinstall every time.
if __name__ == "__main__":
     register()