#!/usr/bin/env python3
"""Build an editable Fenn rig and looping idle animation from Episode 1's fox."""

from __future__ import annotations

import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ep" / "01" / "fox_original_unrigged.glb"
BLEND_OUT = ROOT / "Fenn_Rigged.blend"
GLB_OUT = ROOT / "ep" / "01" / "fox.glb"
FPS = 30
IDLE_END = 180


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(edge0, edge1, value):
    t = clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def add_edit_bone(armature, name, head, tail, parent=None, deform=True):
    bone = armature.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = deform
    if parent is not None:
        bone.parent = parent
    return bone


def key_pose_bone(bone, frame, rotation=(0, 0, 0), scale=(1, 1, 1)):
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = tuple(math.radians(v) for v in rotation)
    bone.scale = scale
    bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    bone.keyframe_insert(data_path="scale", frame=frame)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = IDLE_END

    fenn = next(obj for obj in bpy.data.objects if obj.type == "MESH")
    fenn.name = "Fenn_Mesh"
    fenn.data.name = "Fenn_MeshData"
    fenn["character"] = "Fenn"
    fenn["forward_axis"] = "-Y"

    # A compact control/deformation rig. The lantern-tail hangs behind Fenn on +Y.
    armature_data = bpy.data.armatures.new("Fenn_Armature")
    rig = bpy.data.objects.new("Fenn_Rig", armature_data)
    bpy.context.collection.objects.link(rig)
    rig.show_in_front = True
    rig["idle_clip"] = "Fenn_Idle"

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = add_edit_bone(armature_data, "CTRL_Root", (0, 0, 0.03), (0, 0, 0.20), deform=False)
    body = add_edit_bone(armature_data, "DEF_Body", (0, 0.02, 0.20), (0, -0.01, 0.59), root)
    neck = add_edit_bone(armature_data, "DEF_Neck", (0, -0.01, 0.56), (0, -0.08, 0.71), body)
    add_edit_bone(armature_data, "DEF_Head", (0, -0.08, 0.69), (0, -0.10, 0.88), neck)
    tail_base = add_edit_bone(
        armature_data, "CTRL_TailBase", (0, 0.12, 0.56), (0, 0.23, 0.53), body, deform=False
    )
    add_edit_bone(
        armature_data, "DEF_LanternTail", (0, 0.20, 0.55), (0, 0.40, 0.29), tail_base
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)

    # Coordinate-based weights are safer for this AI-generated mesh because its
    # visible surface consists of many disconnected geometric islands.
    group_names = ("DEF_Body", "DEF_Neck", "DEF_Head", "DEF_LanternTail")
    groups = {name: fenn.vertex_groups.new(name=name) for name in group_names}
    for vertex in fenn.data.vertices:
        x, y, z = vertex.co

        # Lantern and decorative attachment: rigid at the rear, softened only
        # around its connection to the fox's back.
        tail_weight = smoothstep(0.15, 0.29, y)

        # Head/neck are limited to the forward half so the lantern leaves and
        # rear silhouette are never captured by the high-Z head selection.
        forward = clamp((0.14 - y) / 0.22)
        head_weight = (1.0 - tail_weight) * forward * smoothstep(0.61, 0.73, z)
        neck_band = forward * smoothstep(0.49, 0.61, z) * (1.0 - smoothstep(0.67, 0.76, z))
        neck_weight = (1.0 - tail_weight) * (1.0 - head_weight) * neck_band * 0.82
        body_weight = max(0.0, 1.0 - tail_weight - head_weight - neck_weight)

        weights = {
            "DEF_Body": body_weight,
            "DEF_Neck": neck_weight,
            "DEF_Head": head_weight,
            "DEF_LanternTail": tail_weight,
        }
        total = sum(weights.values()) or 1.0
        for name, weight in weights.items():
            if weight > 0.0001:
                groups[name].add([vertex.index], weight / total, "REPLACE")

    modifier = fenn.modifiers.new("Fenn Armature", "ARMATURE")
    modifier.object = rig
    fenn.parent = rig
    fenn.matrix_parent_inverse = rig.matrix_world.inverted()

    # Six-second seamless idle: irregular head glances and delayed, gentle
    # lantern-tail sway. First and final poses match exactly for clean looping.
    rig.animation_data_create()
    action = bpy.data.actions.new("Fenn_Idle")
    action.use_fake_user = True
    rig.animation_data.action = action

    poses = {
        1:   ((0, 0, 0),    (0, 0, 0),      (0, 0, 0),     (0, 0, 0)),
        24:  ((0.4, 0, 0),  (0.5, 0, -2),   (1, 0, -6),    (3.5, 1.2, 0)),
        52:  ((0, 0, 0),    (-0.4, 0, 1.5), (-1, 0, 4),    (-4.5, -1, 0)),
        78:  ((0.3, 0, 0),  (0.8, 0, 2),    (2, -1, 7),    (4.0, 1.4, 0)),
        105: ((0, 0, 0),    (1.5, 0, 0),    (5, 0, 1),     (-3.2, -1, 0)),
        133: ((0.4, 0, 0),  (-0.5, 0, -1.5),(-1, 1, -5),   (4.8, 1.1, 0)),
        158: ((0, 0, 0),    (0.3, 0, 1),    (1, 0, 3),     (-3.6, -1.2, 0)),
        180: ((0, 0, 0),    (0, 0, 0),      (0, 0, 0),     (0, 0, 0)),
    }
    body_bone = rig.pose.bones["DEF_Body"]
    neck_bone = rig.pose.bones["DEF_Neck"]
    head_bone = rig.pose.bones["DEF_Head"]
    tail_bone = rig.pose.bones["CTRL_TailBase"]
    lantern_bone = rig.pose.bones["DEF_LanternTail"]
    for frame, (body_rot, neck_rot, head_rot, tail_rot) in poses.items():
        breath = 1.008 if frame in (24, 78, 133) else 1.0
        key_pose_bone(body_bone, frame, body_rot, (1.0, 1.0, breath))
        key_pose_bone(neck_bone, frame, neck_rot)
        key_pose_bone(head_bone, frame, head_rot)
        key_pose_bone(tail_bone, frame, tail_rot)
        # Secondary motion lags and slightly opposes the tail attachment.
        key_pose_bone(
            lantern_bone, frame,
            (-tail_rot[0] * 0.42, -tail_rot[1] * 0.55, tail_rot[2]),
        )

    # Smooth movement with flattened cyclic endpoints.
    for curve in action.fcurves if hasattr(action, "fcurves") else []:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"

    scene.timeline_markers.new("IDLE START", frame=1)
    scene.timeline_markers.new("IDLE LOOP", frame=IDLE_END)
    scene.frame_set(1)

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUT),
        export_format="GLB",
        export_animations=True,
        export_force_sampling=True,
        export_nla_strips=False,
        export_frame_range=False,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Saved editable rig: {BLEND_OUT}")
    print(f"Exported animated web model: {GLB_OUT}")


if __name__ == "__main__":
    build()
