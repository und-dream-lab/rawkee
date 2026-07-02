dcc = 0  # standalone Python

try:
    import maya.cmds
    dcc = 1  # Maya
except ImportError:
    try:
        import bpy
        dcc = 2  # Blender
    except ImportError:
        pass

if dcc == 1:
    from . import editor
    from . import io
    print("rawkee: Maya environment detected.")
elif dcc == 2:
    from . import io
    print("rawkee: Blender environment detected.")
else:
    from . import editor
    from . import io
    print("rawkee: Standalone Python environment detected.")
