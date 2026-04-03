try:
    from . import maya
    from . import editor
    from . import io
    print("Is Maya - Plugin")
except:
    from . import blender
    from . import editor
    from . import io
    print("Is Blender - AddOn")
