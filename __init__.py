"""
File Author: 
    Thomaz Diaz, UND Dream Lab
Description: 
    The start of the addon to be able to run with the multiple files, and import register and unregister them.
    To be able to export to .X3D file format.
Addon Status:
    (In Development) 
        Notes: to make the add-on zip file make a copy of the files and the __init__ file in lower the rawkee folder comment out the try & excempt,
        and zip up the file to be able to install on blender. Edit > Preferences > Install from Disk (top right dropdown arrow) 

        The Add-on UI is not commplete to be refined later when theexporting gemotry is completed. -Thomas Diaz[12 Mayo, 2026]


        So far the addon runs sucsessfully and can export to a .x3d file, but the gemotry is just cubes of the objects in the collections. 
        the objects names and where there and stored are all correct however. 
        
        (file to fix: RKWeb3DBlenderUI.py)
"""

bl_info = {
    "name" : "BlenderRawKeeX3DExport",
    "author" : "UND Dream Lab, etc...", 
    "version" : (0, 0, 2),
    "blender" : (5, 0, 1),
    "location" : "File > Import-Export",
    "description" : "Rawkee X3D export plugin for Blender",
    "warnings" : "This is Plugin is Under Development",
    "wiki_url" : "https://github.com/und-dream-lab/rawkee/blob/main/README.md", #Github Read Me File for now. the Github Page Wiki is empty at the moment.
    "tracker_url" : "https://github.com/und-dream-lab/rawkee/issues", #for the moment the Github Issues for the bug report link.
    "category" : "Import-Export", #only Export for now,
    }
#Imports
#-------------------------------------
from .rawkee.blender import RKWeb3DBlenderUI #imports the rawkee folder and the blender folder inside of it to the RKWeb3DBlender script for the UI.

#-------------------------------------


#Blender register & unregister for the Imports.
#-------------------------------------
def register():
    RKWeb3DBlenderUI.register()
def unregister():
    RKWeb3DBlenderUI.unregister()
#-------------------------------------



# for test to update and not having to reinstall every time.
if __name__ == "__main__":
     register()