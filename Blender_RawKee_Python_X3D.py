"""
File Author: 
    UND Dream Lab, Thomaz Diaz, etc...
Description: 
    This file is ment to be the starting file for the Blender Version of the RawKee X3D Export Plugin,
    Contains the Plugin Information for Blender,
    and the file imports for running the plugin.
File Status:
    (In Development)
    Tasks: work on the geometry for now, and worry about materials, textures, and animation later.
        Learn about the Blender Node Scene Graph
"""
#Blender Plugin Information 
bl_info = {
    "name" : "Blender RawKee X3D Export Plugin",
    "author" : "UND Dream Lab, etc...", 
    "version" : (0, 0, 1),
    "blender" : (5, 0, 1),
    "location" : "File > Import-Export",
    "description" : "Rawkee X3D export plugin for Blender",
    "warnings" : "This is Plugin is Under Development", #Warning this is still under Development
    "doc_url" : "https://github.com/und-dream-lab/rawkee/blob/main/README.md", #Github Read Me File for now.
    "category" : "Export", #Using a Custom Category. the closest standard catagory is "Import-Export", but at the moment we are not worrying about Imports at the moment.
}
#dev note: in blender the plugin will not work by only running this file by its self in the blender text editor. so it has to be installed as an addon when a plugin is a multi file plugin.
    # so the relevtive imports will work  
    #I have not tested it yet. will do later - Thomaz Diaz 

#Plugin Blender GUI 
from rawkee.blender.RKWeb3DBlender import *
#Import etc.



def register():
    RKWeb3DBlender.register()
def unregister():
    RKWeb3DBlender.unregister()

if __name__ == "__main__":
     register()
