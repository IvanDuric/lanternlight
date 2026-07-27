#!/usr/bin/env python3
"""Add normal and malfunction animation sets to Presse.blend.

Run with Blender:
  Blender --background Presse.blend --python animate_presse.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy


ROOT_DIR = Path(__file__).resolve().parent
BLEND_OUT = ROOT_DIR / "Presse_Animated.blend"
GLB_OUT = ROOT_DIR / "ep" / "04" / "presse.glb"

FPS = 30
NORMAL_END = 120
MALFUNCTION_END = 60
MALFUNCTION_PREVIEW_START = 151
MAIN_TRAVEL = 0.14
HANDLE_PIVOT = (0.22, 0.214, 0.466)


def new_action(obj, name: str):
    obj.animation_data_create()
    obj.animation_data.action = None
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    obj.animation_data.action = action
    return action


def action_fcurves(action):
    """Yield F-curves from Blender 4/5 layered Actions."""
    if hasattr(action, "fcurves"):
        yield from action.fcurves
        return
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def finish_action(obj, action, interpolation: str):
    for curve in action_fcurves(action):
        for point in curve.keyframe_points:
            point.interpolation = interpolation
    obj.animation_data.action = None


def key_handle(obj, frame: int, degrees: float):
    obj.rotation_euler[1] = math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)


def key_main(obj, frame: int, base_z: float, travel: float):
    obj.location.z = base_z + travel
    obj.keyframe_insert(data_path="location", index=2, frame=frame)


def key_shake(obj, frame: int, x: float, y: float, angle: float):
    obj.location.x = x
    obj.location.y = y
    obj.rotation_euler[2] = math.radians(angle)
    obj.keyframe_insert(data_path="location", index=0, frame=frame)
    obj.keyframe_insert(data_path="location", index=1, frame=frame)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)


def add_nla_strip(obj, track_name: str, action, start: int):
    animation = obj.animation_data_create()
    track = animation.nla_tracks.new()
    track.name = track_name
    strip = track.strips.new(track_name, start, action)
    strip.blend_type = "REPLACE"
    strip.extrapolation = "NOTHING"
    return strip


def build():
    scene = bpy.context.scene
    scene.render.fps = FPS

    root = bpy.data.objects.get("ROOT")
    main = bpy.data.objects.get("Main")
    handle = bpy.data.objects.get("handle")
    body = bpy.data.objects.get("Body")
    if not all((root, main, handle, body)):
        raise RuntimeError("Expected ROOT, Main, handle and Body objects in Presse.blend")

    # Remove only prior animation data; mesh geometry and materials remain intact.
    for obj in (root, main, handle):
        obj.animation_data_clear()

    main_base = main.location.copy()
    root_base = root.location.copy()
    root_rotation = root.rotation_euler.copy()

    # The lever rotates around its mounting point on the right side of the frame.
    scene.cursor.location = HANDLE_PIVOT
    bpy.context.view_layer.objects.active = handle
    handle.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    handle.select_set(False)
    handle.rotation_mode = "XYZ"
    root.rotation_mode = "XYZ"

    # NORMAL: lever is deliberately pushed before each platen movement.
    normal_handle = new_action(handle, "Presse_Normal_Handle")
    for frame, degrees in (
        (1, -35), (8, 42), (14, -35),
        (32, -35), (58, -35), (65, 42), (72, -35),
        (90, -35), (120, -35),
    ):
        key_handle(handle, frame, degrees)
    finish_action(handle, normal_handle, "BEZIER")

    normal_main = new_action(main, "Presse_Normal_Main")
    for frame, travel in (
        (1, 0.0), (14, 0.0), (32, MAIN_TRAVEL),
        (58, MAIN_TRAVEL), (72, MAIN_TRAVEL), (90, 0.0), (120, 0.0),
    ):
        key_main(main, frame, main_base.z, travel)
    finish_action(main, normal_main, "BEZIER")

    # MALFUNCTION: rapid lever/platen cycling with a deterministic machine shake.
    bad_handle = new_action(handle, "Presse_Malfunction_Handle")
    for frame in range(1, 57, 5):
        key_handle(handle, frame, -46 if ((frame - 1) // 5) % 2 == 0 else 48)
    key_handle(handle, MALFUNCTION_END, -46)
    finish_action(handle, bad_handle, "LINEAR")

    bad_main = new_action(main, "Presse_Malfunction_Main")
    key_main(main, 1, main_base.z, 0.0)
    for index, frame in enumerate(range(8, 59, 5)):
        key_main(main, frame, main_base.z, MAIN_TRAVEL if index % 2 == 0 else 0.0)
    key_main(main, MALFUNCTION_END, main_base.z, 0.0)
    finish_action(main, bad_main, "LINEAR")

    bad_shake = new_action(root, "Presse_Malfunction_Shake")
    shake_pattern = (
        (0.008, -0.004, 1.15), (-0.006, 0.006, -1.0),
        (0.004, -0.007, 0.75), (-0.009, 0.003, -1.25),
    )
    key_shake(root, 1, root_base.x, root_base.y, math.degrees(root_rotation.z))
    for index, frame in enumerate(range(3, MALFUNCTION_END, 2)):
        dx, dy, angle = shake_pattern[index % len(shake_pattern)]
        key_shake(root, frame, root_base.x + dx, root_base.y + dy, angle)
    key_shake(root, MALFUNCTION_END, root_base.x, root_base.y, math.degrees(root_rotation.z))
    finish_action(root, bad_shake, "LINEAR")

    # Timeline demo: normal cycle at 1–120, malfunction at 151–210.
    add_nla_strip(handle, "Presse_Normal", normal_handle, 1)
    add_nla_strip(main, "Presse_Normal", normal_main, 1)
    add_nla_strip(handle, "Presse_Malfunction", bad_handle, MALFUNCTION_PREVIEW_START)
    add_nla_strip(main, "Presse_Malfunction", bad_main, MALFUNCTION_PREVIEW_START)
    add_nla_strip(root, "Presse_Malfunction", bad_shake, MALFUNCTION_PREVIEW_START)

    scene.frame_start = 1
    scene.frame_end = MALFUNCTION_PREVIEW_START + MALFUNCTION_END - 1
    scene.timeline_markers.clear()
    scene.timeline_markers.new("NORMAL PRESS", frame=1)
    scene.timeline_markers.new("MALFUNCTION", frame=MALFUNCTION_PREVIEW_START)
    scene["animation_normal"] = "Presse_Normal_*"
    scene["animation_malfunction"] = "Presse_Malfunction_*"
    scene["normal_preview_frames"] = "1-120"
    scene["malfunction_preview_frames"] = "151-210"
    scene.frame_set(1)

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUT),
        export_format="GLB",
        export_animations=True,
        export_force_sampling=True,
        export_nla_strips=True,
        export_frame_range=False,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Saved: {BLEND_OUT}")
    print(f"Exported: {GLB_OUT}")
    print("Normal preview: frames 1-120")
    print("Malfunction preview: frames 151-210")
    print("Normal platen travel: 0.140 m; measured clearance: about 0.145 m")


if __name__ == "__main__":
    build()
