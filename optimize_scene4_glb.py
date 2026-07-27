#!/usr/bin/env python3
"""Shrink the embedded textures in ep/04/scene4_final.glb.

The authored diorama exports ~100 separate 1024px Tripo textures, most of which
are near-flat colour maps or exact duplicates of each other. That is ~10 MB of a
12 MB GLB, well over the <6 MB budget in Lanternlight_Scene_Build_Guide.md, and
it is the single biggest cause of a slow first load on a phone.

This pass is purely lossy-image work on an already-exported GLB:
  * decode every embedded image
  * collapse images whose pixels are identical (content hash)
  * collapse images that are visually a single flat colour down to 8x8
  * downscale anything larger than MAX_SIZE
  * re-encode as JPEG unless the image actually carries alpha

Geometry, animations, materials and node names are left untouched, so it is safe
to run after Blender and it does not care whether Draco compression is on.

Needs Pillow. Homebrew's python3 refuses system-wide installs (PEP 668), so keep
a venv next to the project and call its interpreter directly -- no activation:

    python3 -m venv .venv
    .venv/bin/pip install Pillow

Usage:
    .venv/bin/python optimize_scene4_glb.py [path/to/scene4_final.glb]
"""

from __future__ import annotations

import hashlib
import io
import json
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_GLB = ROOT_DIR / "ep" / "04" / "scene4_final.glb"

MAX_SIZE = 512          # longest edge of any retained texture
JPEG_QUALITY = 82
FLAT_TOLERANCE = 6      # per-channel spread below this counts as a flat colour
FLAT_SIZE = 8           # flat colours collapse to this many pixels square


def read_glb(path: Path):
    data = path.read_bytes()
    magic, _version, _length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        raise ValueError(f"{path} is not a binary glTF file")

    json_chunk = None
    bin_chunk = b""
    offset = 12
    while offset < len(data):
        chunk_len, chunk_type = struct.unpack("<II", data[offset:offset + 8])
        payload = data[offset + 8:offset + 8 + chunk_len]
        if chunk_type == 0x4E4F534A:
            json_chunk = json.loads(payload)
        elif chunk_type == 0x004E4942:
            bin_chunk = payload
        offset += 8 + chunk_len + (-chunk_len % 4)
    if json_chunk is None:
        raise ValueError(f"{path} has no JSON chunk")
    return json_chunk, bytearray(bin_chunk)


def write_glb(path: Path, gltf: dict, buffer: bytes) -> None:
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    bin_bytes = bytes(buffer) + b"\x00" * (-len(buffer) % 4)

    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    out = bytearray()
    out += struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
    out += struct.pack("<II", len(bin_bytes), 0x004E4942) + bin_bytes
    path.write_bytes(bytes(out))


def has_real_alpha(image: Image.Image) -> bool:
    if image.mode not in ("RGBA", "LA", "PA"):
        return False
    alpha = image.getchannel("A")
    return alpha.getextrema()[0] < 250


def is_flat(image: Image.Image) -> bool:
    small = image.convert("RGB").resize((16, 16), Image.BILINEAR)
    for low, high in small.getextrema():
        if high - low > FLAT_TOLERANCE:
            return False
    return True


def reencode(raw: bytes, mime: str) -> tuple[bytes, str, str]:
    """Return (payload, mime_type, note) for one embedded image."""
    image = Image.open(io.BytesIO(raw))
    image.load()
    keep_alpha = has_real_alpha(image)

    # Idempotent: an image this script already processed is left completely
    # alone, so re-running after Blender never stacks JPEG generations.
    if mime == "image/jpeg" and max(image.size) <= MAX_SIZE and not keep_alpha:
        return raw, mime, "already optimized"

    if is_flat(image):
        colour = image.convert("RGBA" if keep_alpha else "RGB").resize((1, 1), Image.BOX)
        image = colour.resize((FLAT_SIZE, FLAT_SIZE), Image.NEAREST)
        note = "flat"
    else:
        if max(image.size) > MAX_SIZE:
            scale = MAX_SIZE / max(image.size)
            size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
            image = image.resize(size, Image.LANCZOS)
        note = f"{image.width}x{image.height}"

    out = io.BytesIO()
    if keep_alpha:
        image.convert("RGBA").save(out, format="PNG", optimize=True)
        return out.getvalue(), "image/png", note + " rgba"
    image.convert("RGB").save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue(), "image/jpeg", note


def optimize(path: Path) -> None:
    gltf, buffer = read_glb(path)
    images = gltf.get("images", [])
    if not images:
        print("No embedded images; nothing to do.")
        return

    views = gltf["bufferViews"]
    before = path.stat().st_size

    # Re-encode each image once, keyed by the bytes it started from, so the many
    # duplicated Tripo maps collapse onto a single shared payload.
    encoded_cache: dict[str, tuple[bytes, str, str]] = {}
    payload_slots: dict[bytes, int] = {}

    new_buffer = bytearray()
    new_views: list[dict] = []

    # Non-image buffer views are copied through verbatim; only their offsets move.
    image_view_ids = {img["bufferView"] for img in images if "bufferView" in img}
    remap: dict[int, int] = {}

    for index, view in enumerate(views):
        if index in image_view_ids:
            continue
        start = view["byteOffset"] if "byteOffset" in view else 0
        chunk = bytes(buffer[start:start + view["byteLength"]])
        while len(new_buffer) % 4:
            new_buffer.append(0)
        copied = dict(view)
        copied["byteOffset"] = len(new_buffer)
        new_buffer += chunk
        remap[index] = len(new_views)
        new_views.append(copied)

    saved_dupes = 0
    for img in images:
        if "bufferView" not in img:
            continue
        view = views[img["bufferView"]]
        start = view.get("byteOffset", 0)
        raw = bytes(buffer[start:start + view["byteLength"]])

        digest = hashlib.sha1(raw).hexdigest()
        if digest not in encoded_cache:
            try:
                encoded_cache[digest] = reencode(raw, img.get("mimeType", ""))
            except Exception as error:  # keep the original if Pillow cannot read it
                print(f"  ! kept {img.get('name', '?')} as-is: {error}")
                encoded_cache[digest] = (raw, img.get("mimeType", "image/png"), "unchanged")
        payload, mime, _note = encoded_cache[digest]

        if payload in payload_slots:
            img["bufferView"] = payload_slots[payload]
            img["mimeType"] = mime
            saved_dupes += 1
            continue

        while len(new_buffer) % 4:
            new_buffer.append(0)
        new_views.append({
            "buffer": 0,
            "byteOffset": len(new_buffer),
            "byteLength": len(payload),
        })
        new_buffer += payload
        slot = len(new_views) - 1
        payload_slots[payload] = slot
        img["bufferView"] = slot
        img["mimeType"] = mime

    # Every accessor / mesh / Draco extension that referenced a buffer view by
    # index has to follow the views to their new positions.
    def repoint(container: dict, key: str) -> None:
        if key in container and container[key] in remap:
            container[key] = remap[container[key]]

    for accessor in gltf.get("accessors", []):
        repoint(accessor, "bufferView")
        if "sparse" in accessor:
            repoint(accessor["sparse"]["indices"], "bufferView")
            repoint(accessor["sparse"]["values"], "bufferView")
    for mesh in gltf.get("meshes", []):
        for primitive in mesh["primitives"]:
            draco = primitive.get("extensions", {}).get("KHR_draco_mesh_compression")
            if draco:
                repoint(draco, "bufferView")

    gltf["bufferViews"] = new_views
    gltf["buffers"] = [{"byteLength": len(new_buffer)}]

    # No backup copy is kept: Scene4_Final.blend + animate_scene4_final.py
    # regenerate this GLB deterministically, and a stale 12 MB twin sitting in
    # ep/04/ is the kind of thing that ends up deployed by accident.
    write_glb(path, gltf, new_buffer)
    after = path.stat().st_size
    print(
        f"{path.name}: {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB "
        f"({len(images)} images, {len(encoded_cache)} unique, {saved_dupes} deduped)"
    )


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GLB
    optimize(target.resolve())
