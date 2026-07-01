"""
File Author: Thomaz Diaz, UND Dream Lab
Description: Blender RawKee PE X3D Export addon entry point.
             Contains bl_info and delegates all registration to
             rawkee.blender.RKWeb3DBlenderUI.
"""

import bpy
import sys
import os

bl_info = {
    "name"        : "BlenderRawKeeX3DExport",
    "author"      : "UND Dream Lab",
    "version"     : (0, 1, 0),
    "blender"     : (5, 0, 1),
    "location"    : "File > Export / Sidebar N-panel 'RawKee (.X3D)'",
    "description" : "RawKee PE X3D export plugin for Blender 5",
    "doc_url"     : "https://github.com/und-dream-lab/rawkee/",
    "category"    : "Import-Export",
}

# Make sure the addon directory (the folder containing this file) is on
# sys.path so that the 'rawkee' sub-package can be imported.
_addon_dir = os.path.dirname(__file__)
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)


def register():
    from rawkee.blender import RKWeb3DBlenderUI
    RKWeb3DBlenderUI.register()


def unregister():
    from rawkee.blender import RKWeb3DBlenderUI
    RKWeb3DBlenderUI.unregister()


if __name__ == "__main__":
    register()
