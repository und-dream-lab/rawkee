dcc=0 # Python

try:
    import maya.cmds
    dcc=1 #Maya
except ImportError:
    try:
        import bpy
        dcc=2 #Blender
        from . import blender
    except ImportError:
        pass

if   dcc == 1:
    from . import maya
    from . import editor
    from . import io
    print("Is Maya - Plugin")
elif dcc == 2:
    from . import blender
    from . import editor
    from . import io
    print("Is Blender - AddOn")
else:
    print("Is neither mayapy or bpy, Plugin/AddOn - Failure to load.")
