"""
RawKee Blender — X3D Sound custom-node approximation.

Maya equivalent  : rawkee/maya/nodes/x3dSound.py  (MPxLocatorNode X3DSound +
                   MPxDrawOverride X3DSoundDrawOverride)

Blender approach : A Blender EMPTY object flagged with the custom property
                   rk_x3d_type = "Sound" carries all X3D Sound fields via a
                   registered PropertyGroup (RKX3DSoundProperties).
                   A persistent SpaceView3D draw-callback renders the
                   directional indicator (circle + direction arrow) that the
                   Maya version produced with addUIDrawables / draw_manager.

Registration     : Call register() / unregister() from the addon's register /
                   unregister hooks (done in Blender_RawKee_Python_X3D.py).
"""

import bpy
import gpu
import mathutils
from bpy.props import (
    FloatVectorProperty, FloatProperty, BoolProperty, StringProperty
)
from bpy.types import PropertyGroup
from gpu_extras.batch import batch_for_shader


# ---------------------------------------------------------------------------
#  Property Group  (mirrors X3DSound MPxLocatorNode attribute set)
# ---------------------------------------------------------------------------

class RKX3DSoundProperties(PropertyGroup):
    """All X3D Sound-node fields stored on bpy.types.Object."""

    direction: FloatVectorProperty(
        name="Direction",
        description="Sound-emission direction vector (X3D Sound.direction)",
        default=(0.0, 0.0, 1.0),
        size=3,
        subtype='DIRECTION',
    )
    intensity: FloatProperty(
        name="Intensity",
        description="Overall gain factor (X3D Sound.intensity)",
        default=1.0, min=0.0, max=1.0,
    )
    location: FloatVectorProperty(
        name="Location",
        description="Sound source position offset (X3D Sound.location)",
        default=(0.0, 0.0, 0.0),
        size=3,
        subtype='TRANSLATION',
    )
    maxBack: FloatProperty(
        name="Max Back",
        description="Rear maximum attenuation radius (X3D Sound.maxBack)",
        default=10.0, min=0.0,
    )
    maxFront: FloatProperty(
        name="Max Front",
        description="Front maximum attenuation radius (X3D Sound.maxFront)",
        default=10.0, min=0.0,
    )
    minBack: FloatProperty(
        name="Min Back",
        description="Rear minimum radius (X3D Sound.minBack)",
        default=1.0, min=0.0,
    )
    minFront: FloatProperty(
        name="Min Front",
        description="Front minimum radius (X3D Sound.minFront)",
        default=1.0, min=0.0,
    )
    priority: FloatProperty(
        name="Priority",
        description="Rendering priority hint (X3D Sound.priority)",
        default=0.0, min=0.0, max=1.0,
    )
    spatialize: BoolProperty(
        name="Spatialize",
        description="Enable 3-D spatialization (X3D Sound.spatialize)",
        default=True,
    )
    audio_url: StringProperty(
        name="Audio URL",
        description="Relative or absolute URL of the audio file for the child AudioClip",
        default="",
        subtype='FILE_PATH',
    )


# ---------------------------------------------------------------------------
#  Operator — add an X3D Sound object to the scene
# ---------------------------------------------------------------------------

class RAWKEE_OT_AddX3DSound(bpy.types.Operator):
    """Add a RawKee X3D Sound object to the scene (Empty with Sound properties)"""
    bl_idname  = "rawkee.add_x3d_sound"
    bl_label   = "Add X3D Sound"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.empty_add(type='SPHERE', location=context.scene.cursor.location)
        obj = context.active_object
        obj.name = "X3DSoundNode"
        obj["rk_x3d_type"] = "Sound"
        # Optionally reduce display size so it's clear it's a helper
        obj.empty_display_size = 0.25
        self.report({'INFO'}, "X3D Sound node added: " + obj.name)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel — displayed in Object Properties when the selected object is flagged
# ---------------------------------------------------------------------------

class RAWKEE_PT_X3DSoundProperties(bpy.types.Panel):
    """X3D Sound node properties panel (shown for objects with rk_x3d_type='Sound')"""
    bl_label      = "RawKee X3D Sound"
    bl_idname     = "RAWKEE_PT_X3DSoundProperties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context    = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.get("rk_x3d_type") == "Sound"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object
        props  = obj.rk_x3d_sound

        col = layout.column(align=True)
        col.prop(props, "direction")
        col.prop(props, "location")
        col.separator()
        col.prop(props, "intensity")
        col.prop(props, "priority")
        col.prop(props, "spatialize")
        col.separator()
        col.label(text="Attenuation radii:")
        row = col.row(align=True)
        row.prop(props, "minFront")
        row.prop(props, "maxFront")
        row = col.row(align=True)
        row.prop(props, "minBack")
        row.prop(props, "maxBack")
        col.separator()
        col.prop(props, "audio_url")


# ---------------------------------------------------------------------------
#  Viewport draw callback — mirrors X3DSoundDrawOverride.addUIDrawables()
#  Draws a circle at the sound origin and a red arrow in the direction field.
# ---------------------------------------------------------------------------

_draw_handle = None  # module-level handle so we can remove it on unregister


def _draw_x3d_sound_callback():
    """SpaceView3D draw callback — renders X3D Sound gizmo for flagged empties."""
    context = bpy.context
    if context.mode != 'OBJECT':
        return

    uniform_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    uniform_shader.bind()

    for obj in context.scene.objects:
        if obj.get("rk_x3d_type") != "Sound":
            continue

        props = obj.rk_x3d_sound
        mat   = obj.matrix_world

        # World-space origin
        origin = mat.translation

        # Localised direction from the stored Sound.direction field
        dir_local = mathutils.Vector(props.direction)
        if dir_local.length < 1e-6:
            dir_local = mathutils.Vector((0.0, 0.0, 1.0))
        dir_local.normalize()

        # Convert direction to world space using object rotation only
        dir_world = mat.to_3x3() @ dir_local
        dir_world.normalize()

        # Build a ring perpendicular to the direction (using maxFront radius)
        SEGMENTS = 32
        radius   = max(props.maxFront, 0.01)
        tang     = dir_world.orthogonal().normalized()
        bitan    = dir_world.cross(tang).normalized()

        ring_verts = []
        import math
        for i in range(SEGMENTS + 1):
            a = 2.0 * math.pi * i / SEGMENTS
            p = origin + radius * (math.cos(a) * tang + math.sin(a) * bitan)
            ring_verts.append((p.x, p.y, p.z))

        # Dormant green, selected cyan
        is_selected = (obj in context.selected_objects)
        color = (0.0, 0.8, 0.8, 1.0) if is_selected else (0.0, 0.4, 0.0, 1.0)
        uniform_shader.uniform_float("color", color)

        batch = batch_for_shader(uniform_shader, 'LINE_STRIP', {"pos": ring_verts})
        batch.draw(uniform_shader)

        # Red direction arrow
        tip = origin + dir_world * radius
        arrow_verts = [(origin.x, origin.y, origin.z), (tip.x, tip.y, tip.z)]
        uniform_shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
        batch_arrow = batch_for_shader(uniform_shader, 'LINES', {"pos": arrow_verts})
        batch_arrow.draw(uniform_shader)


# ---------------------------------------------------------------------------
#  Registration helpers
# ---------------------------------------------------------------------------

def register():
    bpy.utils.register_class(RKX3DSoundProperties)
    bpy.types.Object.rk_x3d_sound = bpy.props.PointerProperty(type=RKX3DSoundProperties)

    bpy.utils.register_class(RAWKEE_OT_AddX3DSound)
    bpy.utils.register_class(RAWKEE_PT_X3DSoundProperties)

    global _draw_handle
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        _draw_x3d_sound_callback, (), 'WINDOW', 'POST_VIEW'
    )


def unregister():
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None

    bpy.utils.unregister_class(RAWKEE_PT_X3DSoundProperties)
    bpy.utils.unregister_class(RAWKEE_OT_AddX3DSound)

    del bpy.types.Object.rk_x3d_sound
    bpy.utils.unregister_class(RKX3DSoundProperties)
