#!/usr/bin/env python3
"""Build ep/05/scene5.glb from Scene_05.blend, with Bram working at the table.

Run with Blender:
    Blender --background Scene_05.blend --python build_scene05.py
    .venv/bin/python optimize_scene4_glb.py ep/05/scene5.glb

Scene_05.blend holds the forge room: a table (Sto) and four Tripo props. Bram
himself lives separately in ep/05/hero.glb, already animated (BramHammerArm,
BramHammerWrist, BramHead). This imports him into the room, stands him at the
table at a sensible size, and exports the lot as one file — the same shape as
Episode 4's scene4_final.glb.

Nothing in Scene_05.blend is modified. The .blend is opened read-only and the
result is written to ep/05/scene5.glb.

Everything this script decides is measured from the scene rather than
hard-coded, and printed, so the placement can be judged from the log before
looking at the result.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT_DIR = Path(__file__).resolve().parent
BRAM_GLB = ROOT_DIR / "ep" / "05" / "hero.glb"
GLB_OUT = ROOT_DIR / "ep" / "05" / "scene5.glb"

# --- placement knobs ---------------------------------------------------------
# Bram's height as a multiple of the desk's height. Doubled from 1.35 on request.
BRAM_HEIGHT_VS_TABLE = 2.7
# Where he stands along the fire-pit -> desk line. 0.5 is the midpoint.
BRAM_ALONG = 0.5
# Pushed toward the camera off that line, in Bram-depths, so neither landmark
# overlaps him. He was previously tucked against the desk and half hidden.
BRAM_CLEARANCE = 0.55
# Blender -Y is the camera side of the diorama, matching Episode 4.
FRONT = -1.0
# Leave as None to auto-detect; set to an object name to override.
FIRE_PIT_NAME = None
GROUND_NAME = None
# If he cannot fit at BRAM_HEIGHT_VS_TABLE he is shrunk, but never below this
# fraction of it — better to report a tight fit than to silently deliver a
# miniature beetle.
BRAM_MIN_FRACTION = 0.70
# Bounding boxes touch long before meshes do, so an overlap only counts once it
# is deeper than this fraction of his own footprint.
BRAM_OVERLAP_TOLERANCE = 0.12
# All of Bram's motion is merged into this single clip so the head turn and the
# hammer strike play together instead of as three separate animations.
MERGED_CLIP = "Bram_Work"


def world_bbox(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    low = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    high = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    return low, high


def mesh_objects():
    return [o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices)]


def report_scene(title: str) -> None:
    print(f"\n=== {title} ===")
    total_tris = 0
    rows = []
    for obj in sorted(mesh_objects(), key=lambda o: o.name):
        low, high = world_bbox(obj)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        total_tris += tris
        rows.append((obj.name, tris, low, high))
    for name, tris, low, high in rows:
        print(f"  {name[:44]:44s} {tris:7d} tris   "
              f"x {low.x:+.2f}..{high.x:+.2f}  y {low.y:+.2f}..{high.y:+.2f}  z {low.z:+.2f}..{high.z:+.2f}")
    print(f"  {'TOTAL':44s} {total_tris:7d} tris   "
          f"{len(bpy.data.materials)} materials, {len(bpy.data.images)} images")
    big = [i for i in bpy.data.images if max(i.size) > 512 and i.size[0]]
    if big:
        print(f"  textures over 512px ({len(big)}) — optimize_scene4_glb.py shrinks these after export:")
        for image in sorted(big, key=lambda i: -i.size[0])[:12]:
            print(f"      {image.name[:52]:52s} {image.size[0]}x{image.size[1]}")


def footprint(obj) -> float:
    low, high = world_bbox(obj)
    return (high.x - low.x) * (high.y - low.y)


def volume(obj) -> float:
    low, high = world_bbox(obj)
    return (high.x - low.x) * (high.y - low.y) * max(1e-6, high.z - low.z)


def identify_props():
    """Work out which prop is the ground plate and which is the fire pit.

    The room is a table plus four Tripo imports with UUID names, so nothing can
    be recognised by name. They are told apart by shape instead:

      ground plate  by far the largest footprint, and flat
      tree          the tallest thing in the room
      rock stack    the bulkier of the two remaining props
      fire pit      the smaller one — a low ring of stones

    Both choices are printed, and FIRE_PIT_NAME / GROUND_NAME override them.
    """
    props = [o for o in mesh_objects() if o.name != "Sto"]
    if not props:
        raise RuntimeError("Scene_05.blend has no props besides the table")

    ground = (bpy.data.objects.get(GROUND_NAME) if GROUND_NAME
              else max(props, key=footprint))
    rest = [o for o in props if o is not ground]

    if FIRE_PIT_NAME:
        fire = bpy.data.objects.get(FIRE_PIT_NAME)
        if fire is None:
            raise RuntimeError(f"no object named {FIRE_PIT_NAME!r}")
    elif rest:
        tallest = max(rest, key=lambda o: world_bbox(o)[1].z - world_bbox(o)[0].z)
        candidates = [o for o in rest if o is not tallest] or rest
        fire = min(candidates, key=volume)
    else:
        raise RuntimeError("could not find a fire pit")

    print("\n=== prop identification (by shape — the Tripo names are UUIDs) ===")
    for obj in props:
        low, high = world_bbox(obj)
        role = ("GROUND PLATE" if obj is ground else
                "FIRE PIT" if obj is fire else "")
        print(f"  {obj.name[:44]:44s} footprint {footprint(obj):6.2f}  "
              f"height {high.z - low.z:5.2f}  volume {volume(obj):6.2f}  {role}")
    return ground, fire


def floor_level(table, fire, ground) -> float:
    """Where things in this room actually stand.

    Two earlier attempts got this wrong by measuring the ground plate itself:

      * its bounding-box BOTTOM is the underside of the thick rim, well below
        the surface — Bram sank
      * its bounding-box TOP is the crest of the curled leaf edge, well above
        the flat middle — Bram floated

    The plate is a organic Tripo shape, so no single number off its bounds is
    the walking surface. The reliable answer is the furniture: the desk and the
    fire pit were both authored resting on the floor, so the floor is simply
    where they sit. Their two bottoms should agree closely, and the log prints
    both so a disagreement is obvious.
    """
    table_bottom = world_bbox(table)[0].z
    fire_bottom = world_bbox(fire)[0].z
    g_low, g_high = world_bbox(ground)
    print("\n=== floor level ===")
    print(f"  desk 'Sto' rests at      z {table_bottom:+.4f}")
    print(f"  fire pit rests at        z {fire_bottom:+.4f}"
          f"   (differ by {abs(table_bottom - fire_bottom) * 1000:.1f} mm)")
    print(f"  ground plate bbox        z {g_low.z:+.4f} .. {g_high.z:+.4f}"
          f"   <- neither end is the walking surface")
    floor = min(table_bottom, fire_bottom)
    print(f"  using                    z {floor:+.4f}")
    return floor


def import_bram():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(BRAM_GLB))
    fresh = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in fresh if o.parent is None]
    if not roots:
        raise RuntimeError("nothing imported from hero.glb")
    # glTF import nests everything under one root; if it did not, make one.
    if len(roots) > 1:
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        holder = bpy.context.object
        holder.name = "Bram_Root"
        for obj in roots:
            obj.parent = holder
        roots = [holder]
        fresh.append(holder)
    return roots[0], fresh


def group_bbox(root, members):
    """Bounds of the imported meshes only.

    Ignores `root` on purpose: the glTF importer wraps everything in an empty,
    and an empty's bound_box is eight copies of its own origin. Here that point
    happens to fall inside Bram's own span so it changes nothing, but it would
    silently skew the bounds of any model whose geometry sits entirely above or
    below its root.
    """
    bpy.context.view_layer.update()
    meshes = [o for o in members if o.type == "MESH" and len(o.data.vertices)]
    if not meshes:
        raise RuntimeError("imported Bram has no mesh geometry to measure")
    low = Vector((9e9, 9e9, 9e9))
    high = Vector((-9e9, -9e9, -9e9))
    for child in meshes:
        c_low, c_high = world_bbox(child)
        low = Vector(tuple(min(low[i], c_low[i]) for i in range(3)))
        high = Vector(tuple(max(high[i], c_high[i]) for i in range(3)))
    return low, high


def place_bram(root, members) -> None:
    table = bpy.data.objects.get("Sto")
    if table is None:
        raise RuntimeError("Scene_05.blend has no object named 'Sto' (the table)")

    ground, fire = identify_props()
    floor_z = floor_level(table, fire, ground)

    wanted, factor, attempts, clashes = fit_bram(root, members, table, fire, ground, floor_z)

    low, high = group_bbox(root, members)
    g_low, g_high = world_bbox(ground)
    t_high = world_bbox(table)[1]
    table_height = t_high.z - floor_z

    print("\n=== Bram placement ===")
    if attempts:
        print(f"  asked for {BRAM_HEIGHT_VS_TABLE:.2f} x the desk, but he did not fit between the")
        print(f"  fire pit and the desk while staying on the plate — shrunk {attempts} time(s)")
    print(f"  final size        {wanted:.2f} x the desk height ({table_height * wanted:.2f} units tall)")
    print(f"  occupies          x {low.x:+.2f}..{high.x:+.2f}  y {low.y:+.2f}..{high.y:+.2f}  z {low.z:+.2f}..{high.z:+.2f}")
    print(f"  ground plate      x {g_low.x:+.2f}..{g_high.x:+.2f}  y {g_low.y:+.2f}..{g_high.y:+.2f}")
    on_plate = (low.x >= g_low.x and high.x <= g_high.x
                and low.y >= g_low.y and high.y <= g_high.y)
    print(f"  on the plate      {'yes' if on_plate else 'NO — still hanging over an edge'}")
    print(f"  footprint clash   {', '.join(clashes) if clashes else 'none — clear of the desk and the fire pit'}")
    gap = low.z - floor_z
    print(f"  ground contact    {'feet on the ground' if abs(gap) < 1e-4 else f'off by {gap * 1000:+.1f} mm'}")


def descendants(obj):
    out = [obj]
    for child in obj.children:
        out += descendants(child)
    return out


def fit_bram(root, members, table, fire, ground, floor_z):
    """Size and place Bram so he stands clear of the furniture AND on the plate.

    The previous version pushed him toward the camera until his footprint
    stopped overlapping the desk, with nothing stopping him. At 2.7x the desk
    his footprint is wider than the gap between the fire pit and the desk, so
    "clear of the desk" meant standing off the edge of the diorama entirely.

    Both constraints have to hold at once, and if they cannot, the thing to give
    is his size. So: place him, clamp him onto the plate, and if he still
    overlaps something, shrink him and try again. The log says what he ended up
    at and why.
    """
    g_low, g_high = world_bbox(ground)
    t_low, t_high = world_bbox(table)
    f_low, f_high = world_bbox(fire)
    fire_centre = (f_low + f_high) / 2
    table_centre = (t_low + t_high) / 2
    table_height = t_high.z - floor_z
    edge = 0.04 * max(g_high.x - g_low.x, g_high.y - g_low.y)   # keep off the rim

    base_low, base_high = group_bbox(root, members)
    native_height = max(1e-6, base_high.z - base_low.z)

    wanted = BRAM_HEIGHT_VS_TABLE
    for attempt in range(14):
        factor = (table_height * wanted) / native_height
        root.scale = (factor, factor, factor)
        root.location = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

        low, high = group_bbox(root, members)
        depth = max(1e-6, high.y - low.y)
        half_x = (high.x - low.x) / 2
        half_y = depth / 2

        target_x = fire_centre.x + (table_centre.x - fire_centre.x) * BRAM_ALONG
        target_y = fire_centre.y + (table_centre.y - fire_centre.y) * BRAM_ALONG
        target_y += FRONT * depth * BRAM_CLEARANCE

        # Never let him leave the diorama, whatever the clearance asks for.
        target_x = min(max(target_x, g_low.x + half_x + edge), g_high.x - half_x - edge)
        target_y = min(max(target_y, g_low.y + half_y + edge), g_high.y - half_y - edge)

        root.location.x += target_x - (low.x + high.x) / 2
        root.location.y += target_y - (low.y + high.y) / 2
        root.location.z += floor_z - low.z
        root.rotation_mode = "XYZ"
        root.rotation_euler.z = 0.0 if FRONT < 0 else math.pi
        bpy.context.view_layer.update()

        low, high = group_bbox(root, members)
        # Boxes touch well before meshes do — standing right at the desk is the
        # point. Only count an overlap once it bites into him properly.
        tol = BRAM_OVERLAP_TOLERANCE * min(high.x - low.x, high.y - low.y)
        clashes = []
        for obj in (table, fire):
            o_low, o_high = world_bbox(obj)
            bite_x = min(high.x, o_high.x) - max(low.x, o_low.x)
            bite_y = min(high.y, o_high.y) - max(low.y, o_low.y)
            if bite_x > tol and bite_y > tol:
                clashes.append(f"{obj.name} (by {min(bite_x, bite_y):.2f})")
        if not clashes:
            return wanted, factor, attempt, []
        if wanted * 0.92 < BRAM_HEIGHT_VS_TABLE * BRAM_MIN_FRACTION:
            return wanted, factor, attempt, clashes
        wanted *= 0.92

    return wanted, factor, attempt, clashes


def align_anvil_to_strike(members, scene) -> None:
    """Put the anvil where the hammer actually lands.

    Bram and his anvil are authored together in hero.glb, but the hammer head
    never reaches it — at rest the swing subtree bottoms out at 0.510 while the
    anvil top is at 0.380. Rather than guess, the swing is stepped through frame
    by frame to find the lowest point the hammer head actually reaches and where
    it is horizontally, then the anvil is moved under it.
    """
    swing = next((o for o in members if "HammerSwing" in o.name), None)
    anvil = [o for o in members if "Anvil" in o.name]
    if swing is None or not anvil:
        print("\n=== anvil ===\n  no hammer or anvil found — left alone")
        return

    hammer_meshes = [o for o in descendants(swing)
                     if o.type == "MESH" and len(o.data.vertices)]
    if not hammer_meshes:
        print("\n=== anvil ===\n  hammer has no geometry — left alone")
        return

    frames = set()
    for obj in members:
        anim = obj.animation_data
        if not anim:
            continue
        for track in anim.nla_tracks:
            for strip in track.strips:
                if strip.action:
                    start, end = strip.action.frame_range
                    frames.update(range(int(start), int(end) + 1))
        if anim.action:
            start, end = anim.action.frame_range
            frames.update(range(int(start), int(end) + 1))
    if not frames:
        frames = set(range(scene.frame_start, scene.frame_end + 1))

    best_z, best_xy, best_frame = 9e9, None, None
    for frame in sorted(frames):
        scene.frame_set(frame)
        low = Vector((9e9, 9e9, 9e9))
        high = Vector((-9e9, -9e9, -9e9))
        for mesh in hammer_meshes:
            m_low, m_high = world_bbox(mesh)
            low = Vector(tuple(min(low[i], m_low[i]) for i in range(3)))
            high = Vector(tuple(max(high[i], m_high[i]) for i in range(3)))
        if low.z < best_z:
            best_z = low.z
            best_xy = ((low.x + high.x) / 2, (low.y + high.y) / 2)
            best_frame = frame
    scene.frame_set(scene.frame_start)

    a_low = Vector((9e9, 9e9, 9e9))
    a_high = Vector((-9e9, -9e9, -9e9))
    for obj in anvil:
        if obj.type != "MESH":
            continue
        o_low, o_high = world_bbox(obj)
        a_low = Vector(tuple(min(a_low[i], o_low[i]) for i in range(3)))
        a_high = Vector(tuple(max(a_high[i], o_high[i]) for i in range(3)))

    delta = Vector((
        best_xy[0] - (a_low.x + a_high.x) / 2,
        best_xy[1] - (a_low.y + a_high.y) / 2,
        best_z - a_high.z,
    ))
    for obj in anvil:
        matrix = obj.matrix_world.copy()
        matrix.translation = matrix.translation + delta
        obj.matrix_world = matrix
    bpy.context.view_layer.update()

    print("\n=== anvil ===")
    print(f"  hammer reaches lowest at frame {best_frame}:  "
          f"z {best_z:+.3f}  over x {best_xy[0]:+.3f} y {best_xy[1]:+.3f}")
    print(f"  anvil top was at z {a_high.z:+.3f}, centred x {(a_low.x + a_high.x) / 2:+.3f} "
          f"y {(a_low.y + a_high.y) / 2:+.3f}")
    print(f"  moved by          x {delta.x:+.3f} y {delta.y:+.3f} z {delta.z:+.3f}"
          f"  -> the hammer now lands on it")


def merge_bram_animation(members) -> None:
    """Fold Bram's three clips into one so they play simultaneously.

    hero.glb ships BramHammerArm, BramHammerWrist and BramHead as separate
    animations. The episode happened to start all three at once, but any normal
    glTF viewer plays one clip at a time — so the preview showed him turning his
    head OR swinging, never both.

    The Blender glTF exporter groups NLA strips by TRACK NAME, so putting every
    action on a track with the same name exports them as a single clip carrying
    all the channels. Same trick animate_scene4_final.py uses for the press.
    """
    folded = []
    for obj in members:
        anim = obj.animation_data
        if anim is None:
            continue
        actions = []
        if anim.action:
            actions.append(anim.action)
            anim.action = None
        for track in list(anim.nla_tracks):
            for strip in list(track.strips):
                if strip.action:
                    actions.append(strip.action)
            anim.nla_tracks.remove(track)
        for action in actions:
            track = anim.nla_tracks.new()
            track.name = MERGED_CLIP
            track.strips.new(MERGED_CLIP, 1, action)
            folded.append(f"{obj.name}:{action.name}")

    print(f"\n=== animation ===")
    if folded:
        print(f"  merged into one clip '{MERGED_CLIP}' so the head turn and the "
              f"hammer strike play together:")
        for entry in folded:
            print(f"      {entry}")
    else:
        print("  no animation found on the imported Bram")


def main() -> None:
    report_scene("Scene_05.blend as authored")

    root, members = import_bram()
    place_bram(root, members)
    align_anvil_to_strike(members, bpy.context.scene)
    merge_bram_animation(members)

    # The room's camera and light are Blender-side only. Point lights export in
    # watt-derived candela and blow out the diorama in three.js, exactly as they
    # did in Episode 4, so they are left behind and the page lights the scene.
    GLB_OUT.parent.mkdir(parents=True, exist_ok=True)
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
    size = GLB_OUT.stat().st_size / 1e6
    print(f"\nExported {GLB_OUT.relative_to(ROOT_DIR)}  {size:.1f} MB (Draco on, lights and camera dropped)")
    print("Next: .venv/bin/python optimize_scene4_glb.py ep/05/scene5.glb")
    print("Then open ep/05/preview.html to look at it.")


if __name__ == "__main__":
    main()
