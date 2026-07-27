#!/usr/bin/env python3
"""Animate the authored Scene 4 layout without repositioning its objects.

Run with Blender:
  Blender --background Scene4_Final.blend --python animate_scene4_final.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT_DIR = Path(__file__).resolve().parent
BLEND_OUT = ROOT_DIR / "Scene4_Final_Animated.blend"
GLB_OUT = ROOT_DIR / "ep" / "04" / "scene4_final.glb"

FPS = 30
NORMAL_END = 120
MALFUNCTION_END = 60
MALFUNCTION_PREVIEW_START = 151
SCENE_END = MALFUNCTION_PREVIEW_START + MALFUNCTION_END - 1
MAIN_TRAVEL = 0.14
PRESS_FRONT_Y = -0.79
PRESS_FLOOR_Z = 0.0933
PAPER_CLEARANCE = 0.007   # sheet centre above the measured floor top; see floor_top_z
WARM_COLOR = (1.0, 0.48, 0.12, 1.0)


def action_fcurves(action):
    if hasattr(action, "fcurves"):
        yield from action.fcurves
        return
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def new_action(id_block, name: str):
    id_block.animation_data_create()
    id_block.animation_data.action = None
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    id_block.animation_data.action = action
    return action


def finish_action(id_block, action, interpolation: str):
    for curve in action_fcurves(action):
        for point in curve.keyframe_points:
            point.interpolation = interpolation
    id_block.animation_data.action = None


def add_nla_strip(id_block, track_name: str, action, start: int):
    animation = id_block.animation_data_create()
    track = animation.nla_tracks.new()
    track.name = track_name
    strip = track.strips.new(track_name, start, action)
    strip.blend_type = "REPLACE"
    strip.extrapolation = "NOTHING"
    return strip


def set_origin_world(obj, location):
    scene = bpy.context.scene
    scene.cursor.location = location
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    obj.select_set(False)


def floor_top_z(default: float) -> float:
    """Measured top surface of the floor slab.

    PRESS_FLOOR_Z (0.0933) was close but not exact — the real top of 'pod' is
    0.09523, and placing paper relative to the wrong value dropped the pile
    0.93 mm BELOW the floor. Two near-coplanar flat planes z-fight, which on a
    phone reads as a patch of floor flickering. Measure it instead of assuming,
    so moving or rescaling the floor cannot reintroduce this.
    """
    floor = bpy.data.objects.get("pod")
    if floor is None:
        return default
    return max((floor.matrix_world @ Vector(corner)).z for corner in floor.bound_box)


def world_bbox_center(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return (low + high) / 2


def key_handle(obj, frame: int, base_y: float, degrees: float):
    obj.rotation_euler[1] = base_y + math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)


def key_main(obj, frame: int, base_z: float, travel: float):
    obj.location.z = base_z + travel
    obj.keyframe_insert(data_path="location", index=2, frame=frame)


def key_shake(obj, frame: int, dx=0.0, dy=0.0, angle=0.0):
    # Delta transforms layer over the authored placement. Moving Presa anywhere
    # in the scene will no longer be overridden when playback begins.
    obj.delta_location.x = dx
    obj.delta_location.y = dy
    obj.delta_rotation_euler[2] = math.radians(angle)
    obj.keyframe_insert(data_path="delta_location", index=0, frame=frame)
    obj.keyframe_insert(data_path="delta_location", index=1, frame=frame)
    obj.keyframe_insert(data_path="delta_rotation_euler", index=2, frame=frame)


def key_head(obj, frame: int, base_rotation, nod=0.0, turn=0.0):
    obj.rotation_euler[0] = base_rotation.x + math.radians(nod)
    obj.rotation_euler[1] = base_rotation.y
    obj.rotation_euler[2] = base_rotation.z + math.radians(turn)
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def key_globe(obj, frame: int, base_rotation, turns: float):
    obj.rotation_euler[0] = base_rotation.x
    obj.rotation_euler[1] = base_rotation.y
    obj.rotation_euler[2] = base_rotation.z + turns * math.tau
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def key_light(light_data, frame: int, energy: float):
    light_data.energy = energy
    light_data.keyframe_insert(data_path="energy", frame=frame)


def key_emission(shader_input, frame: int, strength: float):
    shader_input.default_value = strength
    shader_input.keyframe_insert(data_path="default_value", frame=frame)


def key_object_transform(obj, frame: int, location=None, rotation=None, scale=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)
    if rotation is not None:
        obj.rotation_euler = rotation
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert(data_path="scale", frame=frame)


def make_simple_material(name: str, color, roughness=0.8):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if "Alpha" in shader.inputs:
        shader.inputs["Alpha"].default_value = color[3]
    if color[3] < 1.0 and hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    return material


def add_paper(name: str, location, material, dimensions=(0.32, 0.42, 0.006)):
    bpy.ops.mesh.primitive_cube_add(location=location)
    paper = bpy.context.object
    paper.name = name
    paper.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = paper.modifiers.new("Soft paper edges", "BEVEL")
    bevel.width = 0.008
    bevel.segments = 2
    paper.data.materials.append(material)
    paper.rotation_mode = "XYZ"
    return paper


def add_smoke_puff(name: str, location, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=location)
    puff = bpy.context.object
    puff.name = name
    puff.data.materials.append(material)
    puff.rotation_mode = "XYZ"
    return puff


def prepare_bulb(obj, label: str, energy: float):
    source = obj.data.materials[0]
    material = source.copy()
    material.name = f"Scene04_{label}_Glow"
    material.use_nodes = True
    obj.data.materials[0] = material
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = WARM_COLOR
    shader.inputs["Emission Color"].default_value = WARM_COLOR
    shader.inputs["Emission Strength"].default_value = 3.5

    center = world_bbox_center(obj)
    light_data = bpy.data.lights.new(f"Scene04_{label}_LightData", type="POINT")
    light_data.color = WARM_COLOR[:3]
    light_data.energy = energy
    light_data.shadow_soft_size = 0.08
    light_obj = bpy.data.objects.new(f"Scene04_{label}_Light", light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = center
    return material, shader.inputs["Emission Strength"], light_data, light_obj


def build():
    scene = bpy.context.scene
    scene.render.fps = FPS

    presa = bpy.data.objects.get("Presa")
    main = bpy.data.objects.get("Main")
    handle = bpy.data.objects.get("handle.001")
    head = bpy.data.objects.get("head")
    globe = bpy.data.objects.get("krug")
    bulbs = [bpy.data.objects.get(name) for name in ("lampa", "sijalica2", "sijalica3")]
    if not all((presa, main, handle, head, globe, *bulbs)):
        raise RuntimeError("Scene4_Final.blend is missing an expected press, owl, globe or bulb object")

    # Generated props are rebuilt deterministically each time this script runs.
    for obj in list(bpy.data.objects):
        if obj.name.startswith(("Scene04_Paper", "Scene04_Smoke")):
            bpy.data.objects.remove(obj, do_unlink=True)

    # The unparented handle is a pixel-identical duplicate at the same transform.
    duplicate_handle = bpy.data.objects.get("handle")
    if duplicate_handle:
        bpy.data.objects.remove(duplicate_handle, do_unlink=True)

    # Remove earlier generated press actions/NLA, then rebuild against this file's
    # authored transforms. No mesh is relocated at the rest frame.
    animated_blocks = [presa, main, handle, head, globe]
    for block in animated_blocks:
        block.animation_data_clear()
    for action in list(bpy.data.actions):
        if action.name.startswith(("Presse_", "Scene04_")):
            bpy.data.actions.remove(action)

    # Recover the intended authored layout: the press stands on the floor in
    # front of the desk. The old absolute-location action had erased this value.
    presa.location.y = PRESS_FRONT_Y
    presa.location.z = PRESS_FLOOR_Z

    # Set physically useful pivots while preserving visible world transforms.
    set_origin_world(head, (0.9854, 0.02, 0.57))
    set_origin_world(globe, world_bbox_center(globe))
    head.rotation_mode = "XYZ"
    globe.rotation_mode = "XYZ"
    handle.rotation_mode = "XYZ"
    presa.rotation_mode = "XYZ"

    main_base = main.location.copy()
    handle_base = handle.rotation_euler.copy()
    head_base = head.rotation_euler.copy()
    globe_base = globe.rotation_euler.copy()
    presa.delta_location = (0.0, 0.0, 0.0)
    presa.delta_rotation_euler = (0.0, 0.0, 0.0)

    # Paper resting on the platen follows Main automatically. A permanent small
    # pile gives the normal cycle somewhere readable to deposit its output.
    paper_material = make_simple_material(
        "Scene04_PaperMaterial", (0.97, 0.965, 0.90, 1.0), roughness=0.92
    )
    paper_local = (-0.124, -0.0165, 0.341)
    feed_paper = add_paper("Scene04_Paper_OnMain", (0.0, 0.0, 0.0), paper_material)
    feed_paper.parent = main
    feed_paper.location = paper_local

    # A sheet is 0.006 thick with its origin at the centre, so its underside is
    # 0.003 below this value. PAPER_CLEARANCE keeps that underside a clear 4 mm
    # above the floor rather than grazing it.
    floor_z = floor_top_z(PRESS_FLOOR_Z + 0.004) + PAPER_CLEARANCE
    # Keep the finished stack clear of the press's right foot and visibly on
    # the owl side of the machine.
    pile_center = (0.76, -1.08, floor_z)
    for index, (dx, dy, dz, angle) in enumerate((
        (0.00, 0.00, 0.000, -8),
        (-0.025, 0.018, 0.007, 4),
        (0.018, -0.012, 0.014, -2),
        (-0.010, 0.010, 0.021, 7),
    ), start=1):
        sheet = add_paper(
            f"Scene04_PaperPile_{index:02d}",
            (pile_center[0] + dx, pile_center[1] + dy, pile_center[2] + dz),
            paper_material,
        )
        sheet.rotation_euler.z = math.radians(angle)

    platen_world = (-0.124, PRESS_FRONT_Y - 0.0165, PRESS_FLOOR_Z + 0.341)
    normal_output = add_paper(
        "Scene04_Paper_Normal_Output", platen_world, paper_material
    )
    normal_output.scale = (0.0, 0.0, 0.0)
    normal_paper_action = new_action(normal_output, "Scene04_Normal_PaperOutput")
    key_object_transform(normal_output, 1, platen_world, (0, 0, 0), (0, 0, 0))
    key_object_transform(normal_output, 89, platen_world, (0, 0, 0), (0, 0, 0))
    key_object_transform(normal_output, 90, platen_world, (0, 0, 0), (1, 1, 1))
    key_object_transform(
        normal_output, 101,
        (0.02, -1.08, floor_z + 0.16),
        (math.radians(14), math.radians(-8), math.radians(-5)),
        (1, 1, 1),
    )
    key_object_transform(
        normal_output, 113,
        (pile_center[0] - 0.015, pile_center[1], floor_z + 0.029),
        (0, 0, math.radians(-6)), (1, 1, 1),
    )
    key_object_transform(
        normal_output, NORMAL_END,
        (pile_center[0] - 0.015, pile_center[1], floor_z + 0.029),
        (0, 0, math.radians(-6)), (1, 1, 1),
    )
    finish_action(normal_output, normal_paper_action, "BEZIER")
    normal_output.location = platen_world
    normal_output.rotation_euler = (0, 0, 0)
    normal_output.scale = (0, 0, 0)

    # During malfunction, a new sheet is ejected at every downstroke. Each one
    # has a distinct deterministic trajectory and lands elsewhere on the floor.
    #
    # Every sheet has to land somewhere the child can both SEE and SWEEP, which
    # in this room is a smaller area than it looks. Measured footprints (Blender
    # coords, -Y is the camera side); each target keeps 0.16 clearance, which is
    # half a sheet:
    #
    #   floor plate     x -1.59..1.59   y -1.35..1.35
    #   desk            x -0.66..0.34   y -0.35..0.37
    #   small shelf     x -1.25..-0.20  y  0.37..1.10
    #   large shelf     x  0.28..1.26   y  0.64..1.06
    #   press           x -0.50..0.50   y -1.18..-0.40
    #   owl             x  0.50..1.47   y -0.50..0.50
    #   finished pile   (0.76, -1.08)
    #
    # That leaves three open pockets, two sheets each. Sheets dropped straight in
    # front of the press or beside the owl read as "stuck under the furniture"
    # even when they are technically clear, so nothing lands there.
    scatter_targets = (
        (-1.35, -0.72, -28),   # front-left pocket
        (-0.90, -1.15, 41),    # front-left pocket, nearer the camera
        (1.40, -0.82, -15),    # front-right pocket, outside the owl
        (1.12, -1.15, 33),     # front-right pocket, clear of the pile
        (-1.30, 0.05, 57),     # left-middle pocket, beside the desk
        (-0.98, -0.42, -9),    # left-middle pocket, nearer the camera
    )
    scatter_actions = []
    for index, (spawn, target) in enumerate(zip((2, 14, 24, 34, 44, 54), scatter_targets), start=1):
        target_x, target_y, target_angle = target
        paper = add_paper(f"Scene04_PaperScatter_{index:02d}", platen_world, paper_material)
        paper.scale = (0.0, 0.0, 0.0)
        action = new_action(paper, f"Scene04_Malfunction_PaperScatter{index:02d}")
        hidden_frame = max(1, spawn - 1)
        key_object_transform(paper, 1, platen_world, (0, 0, 0), (0, 0, 0))
        key_object_transform(paper, hidden_frame, platen_world, (0, 0, 0), (0, 0, 0))
        key_object_transform(paper, spawn, platen_world, (0, 0, 0), (1, 1, 1))
        arc_frame = min(MALFUNCTION_END, spawn + 5)
        land_frame = min(MALFUNCTION_END, spawn + 11)
        key_object_transform(
            paper, arc_frame,
            ((platen_world[0] + target_x) * 0.5,
             (platen_world[1] + target_y) * 0.5,
             floor_z + 0.30 + 0.035 * index),
            (math.radians(25 + index * 9), math.radians(-18 + index * 7),
             math.radians(target_angle * 0.5)),
            (1, 1, 1),
        )
        key_object_transform(
            paper, land_frame,
            (target_x, target_y, floor_z + 0.004 + index * 0.002),
            (0, 0, math.radians(target_angle)), (1, 1, 1),
        )
        if land_frame < MALFUNCTION_END:
            key_object_transform(
                paper, MALFUNCTION_END,
                (target_x, target_y, floor_z + 0.004 + index * 0.002),
                (0, 0, math.radians(target_angle)), (1, 1, 1),
            )
        finish_action(paper, action, "LINEAR")
        paper.location = platen_world
        paper.rotation_euler = (0, 0, 0)
        paper.scale = (0, 0, 0)
        scatter_actions.append((paper, action))

    # Stylized smoke puffs appear only in the malfunction state. Animated mesh
    # puffs export reliably to GLB, unlike a Blender fluid-volume simulation.
    smoke_material = make_simple_material(
        "Scene04_SmokeMaterial", (0.38, 0.40, 0.42, 0.32), roughness=1.0
    )
    smoke_actions = []
    smoke_origin = (-0.08, PRESS_FRONT_Y - 0.02, PRESS_FLOOR_Z + 0.78)
    for index, start in enumerate((1, 10, 20, 30, 40, 50), start=1):
        puff = add_smoke_puff(f"Scene04_Smoke_{index:02d}", smoke_origin, smoke_material)
        puff.scale = (0.0, 0.0, 0.0)
        action = new_action(puff, f"Scene04_Malfunction_Smoke{index:02d}")
        drift_x = (-0.08, 0.06, -0.03, 0.10, -0.11, 0.04)[index - 1]
        drift_y = (0.02, -0.03, 0.05, 0.00, -0.04, 0.03)[index - 1]
        key_object_transform(puff, 1, smoke_origin, (0, 0, 0), (0, 0, 0))
        key_object_transform(puff, max(1, start - 1), smoke_origin, (0, 0, 0), (0, 0, 0))
        key_object_transform(puff, start, smoke_origin, (0, 0, 0), (0.035, 0.035, 0.045))
        middle = min(MALFUNCTION_END, start + 5)
        end = min(MALFUNCTION_END, start + 10)
        key_object_transform(
            puff, middle,
            (smoke_origin[0] + drift_x * 0.45, smoke_origin[1] + drift_y * 0.45,
             smoke_origin[2] + 0.16),
            (0, math.radians(index * 11), math.radians(index * 17)),
            (0.11, 0.09, 0.14),
        )
        key_object_transform(
            puff, end,
            (smoke_origin[0] + drift_x, smoke_origin[1] + drift_y,
             smoke_origin[2] + 0.34),
            (math.radians(index * 8), math.radians(index * 17), math.radians(index * 29)),
            (0, 0, 0),
        )
        key_object_transform(
            puff, MALFUNCTION_END,
            (smoke_origin[0] + drift_x, smoke_origin[1] + drift_y,
             smoke_origin[2] + 0.34),
            (math.radians(index * 8), math.radians(index * 17), math.radians(index * 29)),
            (0, 0, 0),
        )
        finish_action(puff, action, "BEZIER")
        puff.location = smoke_origin
        puff.rotation_euler = (0, 0, 0)
        puff.scale = (0, 0, 0)
        smoke_actions.append((puff, action))

    # Blender evaluates an animated scale channel against its RNA default of
    # (1,1,1) outside an NLA strip. A low-priority base strip keeps generated
    # props dormant; the state-specific strips placed above it override this.
    hidden_actions = []
    for index, obj in enumerate(
        [normal_output] + [item[0] for item in scatter_actions + smoke_actions], start=1
    ):
        hidden = new_action(obj, f"Scene04_BaseHidden_{index:02d}")
        key_object_transform(obj, 1, scale=(0, 0, 0))
        key_object_transform(obj, SCENE_END, scale=(0, 0, 0))
        finish_action(obj, hidden, "CONSTANT")
        hidden_actions.append((obj, hidden))

    # NORMAL PRESS: current handle pose -> push down -> return -> platen moves.
    normal_handle = new_action(handle, "Scene04_Normal_PressHandle")
    for frame, degrees in (
        (1, 0), (8, 55), (14, 0),
        (32, 0), (58, 0), (65, 55), (72, 0),
        (90, 0), (120, 0),
    ):
        key_handle(handle, frame, handle_base.y, degrees)
    finish_action(handle, normal_handle, "BEZIER")

    normal_main = new_action(main, "Scene04_Normal_PressMain")
    for frame, travel in (
        (1, 0.0), (14, 0.0), (32, MAIN_TRAVEL),
        (58, MAIN_TRAVEL), (72, MAIN_TRAVEL), (90, 0.0), (120, 0.0),
    ):
        key_main(main, frame, main_base.z, travel)
    finish_action(main, normal_main, "BEZIER")

    # Silva calmly surveys the room and occasionally looks down at the book.
    normal_head = new_action(head, "Scene04_Normal_OwlHead")
    for frame, nod, turn in (
        (1, 0, 0), (20, 1, 7), (38, 0, 0),
        (54, 1, -9), (73, 0, 0),
        (88, 8, 2), (102, 0, 0), (120, 0, 0),
    ):
        key_head(head, frame, head_base, nod=nod, turn=turn)
    finish_action(head, normal_head, "BEZIER")

    # MALFUNCTION PRESS: rapid cycling and a small, readable machine shake.
    bad_handle = new_action(handle, "Scene04_Malfunction_PressHandle")
    for index, frame in enumerate(range(1, 57, 5)):
        key_handle(handle, frame, handle_base.y, 0 if index % 2 == 0 else 58)
    key_handle(handle, MALFUNCTION_END, handle_base.y, 0)
    finish_action(handle, bad_handle, "LINEAR")

    bad_main = new_action(main, "Scene04_Malfunction_PressMain")
    key_main(main, 1, main_base.z, 0.0)
    for index, frame in enumerate(range(8, 59, 5)):
        key_main(main, frame, main_base.z, MAIN_TRAVEL if index % 2 == 0 else 0.0)
    key_main(main, MALFUNCTION_END, main_base.z, 0.0)
    finish_action(main, bad_main, "LINEAR")

    bad_shake = new_action(presa, "Scene04_Malfunction_PressShake")
    shake_pattern = (
        (0.008, -0.004, 1.1), (-0.006, 0.006, -1.0),
        (0.004, -0.007, 0.8), (-0.009, 0.003, -1.2),
    )
    key_shake(presa, 1)
    for index, frame in enumerate(range(3, MALFUNCTION_END, 2)):
        dx, dy, angle = shake_pattern[index % len(shake_pattern)]
        key_shake(presa, frame, dx, dy, angle)
    key_shake(presa, MALFUNCTION_END)
    finish_action(presa, bad_shake, "LINEAR")

    # Silva reacts more quickly to the malfunction, including repeated downward looks.
    bad_head = new_action(head, "Scene04_Malfunction_OwlHead")
    for frame, nod, turn in (
        (1, 0, 0), (6, 2, 10), (12, 4, -12),
        (18, 10, 0), (24, 1, 9), (30, 7, -10),
        (36, 0, 0), (42, 3, 12), (48, 8, -11),
        (54, 2, 6), (60, 0, 0),
    ):
        key_head(head, frame, head_base, nod=nod, turn=turn)
    finish_action(head, bad_head, "BEZIER")

    # The globe turns gently during normal operation, then accelerates sharply
    # when the press malfunctions.
    normal_globe = new_action(globe, "Scene04_Normal_GlobeSpin")
    key_globe(globe, 1, globe_base, 0.0)
    key_globe(globe, NORMAL_END, globe_base, 2.0)
    finish_action(globe, normal_globe, "LINEAR")

    bad_globe = new_action(globe, "Scene04_Malfunction_GlobeSpinFast")
    key_globe(globe, 1, globe_base, 0.0)
    key_globe(globe, MALFUNCTION_END, globe_base, 4.0)
    finish_action(globe, bad_globe, "LINEAR")

    # All bulbs glow continuously. During malfunction, emission and nearby point
    # lights blink in sync with the rapid press cycle.
    bulb_actions = []
    for index, (bulb, energy) in enumerate(zip(bulbs, (24.0, 18.0, 18.0)), start=1):
        material, emission_input, light_data, _ = prepare_bulb(bulb, f"Bulb{index}", energy)
        material.node_tree.animation_data_clear()
        light_data.animation_data_clear()

        always_emission = new_action(material.node_tree, f"Scene04_Always_Bulb{index}Emission")
        key_emission(emission_input, 1, 3.5)
        key_emission(emission_input, SCENE_END, 3.5)
        finish_action(material.node_tree, always_emission, "CONSTANT")
        always_light = new_action(light_data, f"Scene04_Always_Bulb{index}Light")
        key_light(light_data, 1, energy)
        key_light(light_data, SCENE_END, energy)
        finish_action(light_data, always_light, "CONSTANT")

        emission_action = new_action(material.node_tree, f"Scene04_Malfunction_Bulb{index}Emission")
        light_action = new_action(light_data, f"Scene04_Malfunction_Bulb{index}Light")
        for blink_index, frame in enumerate(range(1, MALFUNCTION_END, 3)):
            on = blink_index % 2 == 0
            key_emission(emission_input, frame, 4.5 if on else 0.02)
            key_light(light_data, frame, energy * 1.4 if on else 0.0)
        key_emission(emission_input, MALFUNCTION_END, 3.5)
        key_light(light_data, MALFUNCTION_END, energy)
        finish_action(material.node_tree, emission_action, "CONSTANT")
        finish_action(light_data, light_action, "CONSTANT")
        emission_input.default_value = 3.5
        light_data.energy = energy
        bulb_actions.append((
            material.node_tree, always_emission, emission_action,
            light_data, always_light, light_action, index,
        ))

    # NLA timeline preview. Prefixes are also the future web state selectors.
    for obj, action in hidden_actions:
        add_nla_strip(obj, action.name, action, 1)
    for obj, action in ((handle, normal_handle), (main, normal_main), (head, normal_head)):
        add_nla_strip(obj, action.name, action, 1)
    add_nla_strip(normal_output, normal_paper_action.name, normal_paper_action, 1)
    for obj, action in (
        (handle, bad_handle), (main, bad_main), (presa, bad_shake), (head, bad_head),
    ):
        add_nla_strip(obj, action.name, action, MALFUNCTION_PREVIEW_START)
    for obj, action in scatter_actions + smoke_actions:
        add_nla_strip(obj, action.name, action, MALFUNCTION_PREVIEW_START)
    add_nla_strip(globe, normal_globe.name, normal_globe, 1)
    add_nla_strip(globe, bad_globe.name, bad_globe, MALFUNCTION_PREVIEW_START)
    for node_tree, always_emission, emission_action, light_data, always_light, light_action, _ in bulb_actions:
        add_nla_strip(node_tree, always_emission.name, always_emission, 1)
        add_nla_strip(light_data, always_light.name, always_light, 1)
        add_nla_strip(node_tree, emission_action.name, emission_action, MALFUNCTION_PREVIEW_START)
        add_nla_strip(light_data, light_action.name, light_action, MALFUNCTION_PREVIEW_START)

    scene.frame_start = 1
    scene.frame_end = SCENE_END
    scene.timeline_markers.clear()
    scene.timeline_markers.new("NORMAL SCENE", frame=1)
    scene.timeline_markers.new("MALFUNCTION", frame=MALFUNCTION_PREVIEW_START)
    scene["normal_state_prefix"] = "Scene04_Normal_"
    scene["malfunction_state_prefix"] = "Scene04_Malfunction_"
    scene["always_state_prefix"] = "Scene04_Always_"
    scene["normal_preview_frames"] = "1-120"
    scene["malfunction_preview_frames"] = "151-210"
    scene.frame_set(1)

    # Set the unanimated basis after NLA construction. Blender otherwise keeps
    # the primitive creation scale (1,1,1) outside strips, revealing dormant
    # smoke and scatter props in the calm state.
    normal_output.scale = (0.0, 0.0, 0.0)
    for obj, _ in scatter_actions + smoke_actions:
        obj.scale = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))

    # export_lights is deliberately OFF. Blender point lights export in watt-derived
    # candela (the room light came out at ~54000), which blows out the whole diorama
    # once three.js renders it with physicallyCorrectLights inside the AR rig. The
    # web scene lights the diorama itself and drives the bulb flicker in JS, so the
    # baked lights are pure payload. Draco is on to keep the file inside the <6 MB
    # budget from Lanternlight_Scene_Build_Guide.md; run optimize_scene4_glb.py
    # afterwards to shrink the textures, which are the bulk of the remaining size.
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUT),
        export_format="GLB",
        export_animations=True,
        export_force_sampling=True,
        export_nla_strips=True,
        export_frame_range=False,
        export_cameras=False,
        export_lights=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )
    print(f"Saved: {BLEND_OUT}")
    print(f"Exported: {GLB_OUT}")
    print("Normal preview: 1-120; malfunction preview: 151-210")
    print("Next: .venv/bin/python optimize_scene4_glb.py")


if __name__ == "__main__":
    build()
