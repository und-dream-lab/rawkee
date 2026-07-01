"""
RawKee Blender — RKAnimPack custom-node approximation.

Maya equivalent  : rawkee/maya/nodes/rkAnimPack.py  (MPxLocatorNode RKAnimPack)

Blender approach : A Blender EMPTY object carries all RKAnimPack fields via a
                   registered PropertyGroup (RKAnimPackProperties).  The object
                   is identified by the custom property rk_anim_pack = True.

                   RKAnimPack in Maya acts as a proxy that tells the exporter
                   which X3D animation container type to produce and wires up
                   the X3D timing and value fields.  The same behaviour is
                   reproduced here by storing those configuration values on the
                   PropertyGroup and reading them in RKOrganizerBlender.

Registration     : Call register() / unregister() from the addon entry point.
"""

import bpy
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty, StringProperty, EnumProperty
)
from bpy.types import PropertyGroup


# ---------------------------------------------------------------------------
#  Mimicked-type choices (mirrors rkAnimPack.x3d_mimickedNode: 0-4)
# ---------------------------------------------------------------------------

MIMICKED_TYPE_ITEMS = [
    ('0', "TimeSensor",   "Export as X3D TimeSensor driving interpolators"),
    ('1', "AudioClip",    "Export as X3D AudioClip for spatialized sound"),
    ('2', "HAnimMotion",  "Export as X3D HAnimMotion for character animation"),
    ('3', "MovieTexture", "Export as X3D MovieTexture"),
    ('4', "Generic",      "Generic / not yet assigned"),
]


# ---------------------------------------------------------------------------
#  Property Group  (mirrors RKAnimPack attribute set)
# ---------------------------------------------------------------------------

class RKAnimPackProperties(PropertyGroup):
    """All RKAnimPack node fields stored on bpy.types.Object."""

    # --- Maya timeline / Blender action binding ---
    mimicked_type: EnumProperty(
        name="Node Type",
        description="Which X3D animation-container node this pack exports as",
        items=MIMICKED_TYPE_ITEMS,
        default='0',
    )
    keyframe_step: IntProperty(
        name="Keyframe Step",
        description="Sample every N frames when baking non-keyed curves",
        default=1, min=1,
    )
    timeline_start: IntProperty(
        name="Start Frame",
        description="First frame of the animation range to export",
        default=0,
    )
    timeline_stop: IntProperty(
        name="Stop Frame",
        description="Last frame of the animation range to export",
        default=0,
    )
    fps: FloatProperty(
        name="FPS",
        description="Frames per second used to compute X3D timing fields",
        default=30.0, min=1.0,
    )
    export_as_splines: BoolProperty(
        name="Export as Splines",
        description="Use cubic spline interpolators instead of linear",
        default=False,
    )
    animation_package: StringProperty(
        name="Animation Package",
        description="Identifier label written to the X3D animPkg field",
        default="",
    )

    # --- Shared X3D fields (AudioClip / MovieTexture / TimeSensor) ---
    description: StringProperty(
        name="Description",
        description="X3D description field",
        default="",
    )
    enabled: BoolProperty(
        name="Enabled",
        description="X3D enabled field",
        default=True,
    )
    loop: BoolProperty(
        name="Loop",
        description="X3D loop field",
        default=False,
    )
    start_time: FloatProperty(
        name="Start Time",
        description="X3D startTime field (seconds)",
        default=0.0,
    )
    stop_time: FloatProperty(
        name="Stop Time",
        description="X3D stopTime field (seconds)",
        default=0.0,
    )
    pause_time: FloatProperty(
        name="Pause Time",
        description="X3D pauseTime field",
        default=0.0,
    )
    resume_time: FloatProperty(
        name="Resume Time",
        description="X3D resumeTime field",
        default=0.0,
    )

    # --- TimeSensor specific ---
    cycle_interval: FloatProperty(
        name="Cycle Interval",
        description="X3D cycleInterval field (seconds) — auto-computed if 0",
        default=0.0, min=0.0,
    )

    # --- AudioClip / MovieTexture specific ---
    pitch: FloatProperty(
        name="Pitch",
        description="X3D pitch field",
        default=1.0, min=0.0001,
    )
    gain: FloatProperty(
        name="Gain",
        description="X3D gain field",
        default=1.0,
    )
    connected_file: StringProperty(
        name="Connected File",
        description="URL of the audio/video file for AudioClip or MovieTexture",
        default="",
        subtype='FILE_PATH',
    )

    # --- HAnimMotion specific ---
    hanim_loa: IntProperty(
        name="LOA",
        description="HAnimMotion level-of-articulation",
        default=0, min=0, max=4,
    )
    hanim_joints: StringProperty(
        name="HAnim Joints",
        description="Space-separated HAnim joint name list for HAnimMotion.joints",
        default="",
    )


# ---------------------------------------------------------------------------
#  Operator — add an RKAnimPack object to the scene
# ---------------------------------------------------------------------------

class RAWKEE_OT_AddAnimPack(bpy.types.Operator):
    """Add a RawKee AnimPack object to the scene (Empty with anim-pack properties)"""
    bl_idname  = "rawkee.add_anim_pack"
    bl_label   = "Add RK AnimPack"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=context.scene.cursor.location)
        obj = context.active_object
        obj.name = "RKAnimPack"
        obj["rk_anim_pack"] = True
        obj.empty_display_size = 0.15

        # Default: sync start/stop from scene timeline
        props = obj.rk_anim_pack
        props.timeline_start = context.scene.frame_start
        props.timeline_stop  = context.scene.frame_end
        props.fps            = context.scene.render.fps

        self.report({'INFO'}, "RKAnimPack node added: " + obj.name)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel — displayed in Object Properties when the selected object is flagged
# ---------------------------------------------------------------------------

class RAWKEE_PT_AnimPackProperties(bpy.types.Panel):
    """RKAnimPack configuration panel (shown for objects with rk_anim_pack=True)"""
    bl_label       = "RawKee AnimPack"
    bl_idname      = "RAWKEE_PT_AnimPackProperties"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get("rk_anim_pack"))

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object
        props  = obj.rk_anim_pack

        col = layout.column(align=True)
        col.prop(props, "mimicked_type")
        col.separator()
        col.label(text="Timeline / Timing:")
        row = col.row(align=True)
        row.prop(props, "timeline_start")
        row.prop(props, "timeline_stop")
        col.prop(props, "fps")
        col.prop(props, "keyframe_step")
        col.prop(props, "export_as_splines")
        col.prop(props, "animation_package")
        col.separator()

        col.label(text="Shared X3D Fields:")
        col.prop(props, "description")
        col.prop(props, "enabled")
        col.prop(props, "loop")
        row = col.row(align=True)
        row.prop(props, "start_time")
        row.prop(props, "stop_time")

        mt = props.mimicked_type
        if mt == '0':   # TimeSensor
            col.separator()
            col.label(text="TimeSensor Fields:")
            col.prop(props, "cycle_interval")
        elif mt in ('1', '3'):  # AudioClip / MovieTexture
            col.separator()
            col.label(text="AudioClip / MovieTexture Fields:")
            col.prop(props, "pitch")
            col.prop(props, "gain")
            col.prop(props, "connected_file")
        elif mt == '2':  # HAnimMotion
            col.separator()
            col.label(text="HAnimMotion Fields:")
            col.prop(props, "hanim_loa")
            col.prop(props, "hanim_joints")


# ---------------------------------------------------------------------------
#  Registration helpers
# ---------------------------------------------------------------------------

def register():
    bpy.utils.register_class(RKAnimPackProperties)
    bpy.types.Object.rk_anim_pack = bpy.props.PointerProperty(type=RKAnimPackProperties)

    bpy.utils.register_class(RAWKEE_OT_AddAnimPack)
    bpy.utils.register_class(RAWKEE_PT_AnimPackProperties)


def unregister():
    bpy.utils.unregister_class(RAWKEE_PT_AnimPackProperties)
    bpy.utils.unregister_class(RAWKEE_OT_AddAnimPack)

    del bpy.types.Object.rk_anim_pack
    bpy.utils.unregister_class(RKAnimPackProperties)
