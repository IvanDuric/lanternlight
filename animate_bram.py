#!/usr/bin/env python3
"""Build Bram's synchronized hammer animation and export it for Episode 05.

Run with Blender:
  Blender --background --factory-startup --python animate_bram.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent
SOURCE = Path("/Users/itiamo/Downloads/stylized beetle 3d model.glb")
BLEND_OUT = ROOT / "Bram_Hammer_Animated.blend"
GLB_OUT = ROOT / "ep" / "05" / "hero.glb"

FPS = 30
LOOP_SECONDS = 4.62
# Transient peaks measured from ep/05/music.mp3.
HAMMER_HITS = (0.34, 1.37, 1.96, 2.62, 3.26, 3.93)


def make_material(name: str, color: tuple[float, float, float, float], metallic=0.0, roughness=0.5):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.metallic = metallic
    material.roughness = roughness
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def add_beveled_cube(name: str, location, scale, material, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("Soft edges", "BEVEL")
    modifier.width = bevel
    modifier.segments = 2
    obj.data.materials.append(material)
    return obj


def parent_keep_transform(child, parent):
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = world


def frame_at(seconds: float) -> int:
    return max(1, round(seconds * FPS) + 1)


def key_rotation(obj, seconds: float, degrees: float):
    obj.rotation_euler[0] = math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=0, frame=frame_at(seconds))


def key_head(obj, seconds: float, nod: float = 0.0, tilt: float = 0.0):
    obj.rotation_euler[0] = math.radians(nod)
    obj.rotation_euler[2] = math.radians(tilt)
    obj.keyframe_insert(data_path="rotation_euler", frame=frame_at(seconds))


def build():
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing source model: {SOURCE}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))

    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = frame_at(LOOP_SECONDS)

    left_arm = bpy.data.objects.get("tripo_part_4")
    right_arm = bpy.data.objects.get("tripo_part_2")
    if not left_arm or not right_arm:
        raise RuntimeError("Expected separated arm meshes were not found")

    # Move each arm's origin to its shoulder so rotations behave like a simple rig.
    for arm, pivot in (
        (left_arm, (-0.168, -0.029, 0.554)),
        (right_arm, (0.148, -0.029, 0.554)),
    ):
        scene.cursor.location = pivot
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
        arm.select_set(False)
        arm.rotation_mode = "XYZ"

    left_arm.name = "Bram_LeftArm_Hammer"
    right_arm.name = "Bram_RightArm"
    right_arm.rotation_euler[1] = math.radians(58)

    # Two-control rigid rig: the child control aims the arm toward the anvil,
    # while the parent control performs the up/down strike on Blender's X axis.
    shoulder = (-0.168, -0.029, 0.554)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=shoulder)
    hammer_swing = bpy.context.object
    hammer_swing.name = "Bram_HammerSwing_X"
    hammer_swing.rotation_mode = "XYZ"
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=shoulder)
    arm_pose = bpy.context.object
    arm_pose.name = "Bram_HammerArm_ForegroundPose"
    arm_pose.rotation_mode = "XYZ"
    parent_keep_transform(arm_pose, hammer_swing)
    parent_keep_transform(left_arm, arm_pose)

    # Counter/restore controls keep the wrist's local X aligned to world X even
    # though the arm is pre-aimed around Z. The grip remains at one shared pivot.
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-0.50, -0.029, 0.554))
    wrist_counter = bpy.context.object
    wrist_counter.name = "Bram_HammerWrist_AxisCounter"
    wrist_counter.rotation_mode = "XYZ"
    parent_keep_transform(wrist_counter, arm_pose)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-0.50, -0.029, 0.554))
    hammer_wrist = bpy.context.object
    hammer_wrist.name = "Bram_HammerWrist_X"
    hammer_wrist.rotation_mode = "XYZ"
    parent_keep_transform(hammer_wrist, wrist_counter)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-0.50, -0.029, 0.554))
    wrist_restore = bpy.context.object
    wrist_restore.name = "Bram_HammerWrist_AxisRestore"
    wrist_restore.rotation_mode = "XYZ"
    parent_keep_transform(wrist_restore, hammer_wrist)
    wrist_counter.rotation_euler[2] = math.radians(-80)
    wrist_restore.rotation_euler[2] = math.radians(80)

    # Group the head, face and eyes around the neck for small expressive motions.
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.0, 0.59))
    head_rig = bpy.context.object
    head_rig.name = "Bram_HeadRig"
    head_rig.rotation_mode = "XYZ"
    for part_name in ("tripo_part_1", "tripo_part_7", "tripo_part_9", "tripo_part_10"):
        part = bpy.data.objects.get(part_name)
        if part:
            parent_keep_transform(part, head_rig)

    wood = make_material("Hammer wood", (0.19, 0.075, 0.025, 1), roughness=0.62)
    iron = make_material("Hammer iron", (0.16, 0.12, 0.085, 1), metallic=0.72, roughness=0.3)
    anvil_mat = make_material("Anvil iron", (0.12, 0.13, 0.14, 1), metallic=0.68, roughness=0.38)

    # Build the hammer directly through Bram's hand. Arm and hammer are children
    # of the same foreground-pose control, so the grip remains connected.
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.018, depth=0.28, location=(-0.50, -0.029, 0.67))
    handle = bpy.context.object
    handle.name = "Bram_Hammer_Handle"
    handle.data.materials.append(wood)
    head = add_beveled_cube(
        "Bram_Hammer_Head", (-0.50, -0.029, 0.82), (0.105, 0.055, 0.06), iron, bevel=0.018
    )
    # A slightly tapered-looking striking face.
    face = add_beveled_cube(
        "Bram_Hammer_Face", (-0.605, -0.029, 0.82), (0.035, 0.062, 0.07), iron, bevel=0.012
    )
    for piece in (handle, head, face):
        parent_keep_transform(piece, wrist_restore)

    # Aim the connected arm/hammer assembly diagonally into the foreground.
    arm_pose.rotation_euler[2] = math.radians(80)

    # Compact anvil positioned under the impact pose.
    anvil_base = add_beveled_cube(
        "Bram_Anvil_Base", (-0.23, -0.60, 0.105), (0.16, 0.12, 0.07), anvil_mat, bevel=0.025
    )
    anvil_stem = add_beveled_cube(
        "Bram_Anvil_Stem", (-0.23, -0.60, 0.22), (0.095, 0.09, 0.075), anvil_mat, bevel=0.02
    )
    anvil_top = add_beveled_cube(
        "Bram_Anvil_Top", (-0.23, -0.60, 0.335), (0.22, 0.115, 0.045), anvil_mat, bevel=0.018
    )

    # Raised preparation pose is also the loop boundary. The strike rotates on
    # Blender's X axis, moving the arm and hammer forward/down onto the anvil.
    key_rotation(hammer_swing, 0.0, -50)
    key_rotation(hammer_wrist, 0.0, 0)
    for hit in HAMMER_HITS:
        key_rotation(hammer_swing, max(0.0, hit - 0.23), -55) # hand lifts
        key_rotation(hammer_wrist, max(0.0, hit - 0.23), 0)
        key_rotation(hammer_swing, max(0.0, hit - 0.075), 2)  # arm drives down
        key_rotation(hammer_wrist, max(0.0, hit - 0.075), 55)
        key_rotation(hammer_swing, hit, 15)                   # lowered hand
        key_rotation(hammer_wrist, hit, 85)                   # hammer-head impact
        key_rotation(hammer_swing, hit + 0.08, 8)             # rebound
        key_rotation(hammer_wrist, hit + 0.08, 68)
        key_rotation(hammer_swing, hit + 0.22, -50)           # recover
        key_rotation(hammer_wrist, hit + 0.22, 0)
    key_rotation(hammer_swing, LOOP_SECONDS, -50)
    key_rotation(hammer_wrist, LOOP_SECONDS, 0)

    hammer_swing.animation_data.action.name = "BramHammerArm"
    hammer_wrist.animation_data.action.name = "BramHammerWrist"

    # Occasional, restrained head gestures keep Bram alive without competing
    # with the hammer rhythm.
    key_head(head_rig, 0.0)
    key_head(head_rig, 0.82, nod=1.0, tilt=-4.0)
    key_head(head_rig, 1.18)
    key_head(head_rig, 2.35, nod=5.0, tilt=1.0)
    key_head(head_rig, 2.72, nod=-2.0)
    key_head(head_rig, 3.02)
    key_head(head_rig, 4.05, nod=1.0, tilt=3.0)
    key_head(head_rig, LOOP_SECONDS)
    head_rig.animation_data.action.name = "BramHead"

    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUT),
        export_format="GLB",
        export_animations=True,
        export_frame_range=True,
        export_force_sampling=True,
        export_nla_strips=False,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Saved Blender project: {BLEND_OUT}")
    print(f"Exported animated GLB: {GLB_OUT}")
    print(f"Animations: BramHammerArm + BramHammerWrist + BramHead, {LOOP_SECONDS:.2f}s loop, hits={HAMMER_HITS}")


if __name__ == "__main__":
    build()
