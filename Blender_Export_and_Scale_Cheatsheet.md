# Blender → WebAR Export & Scale Cheat Sheet
*For Lanternlight AR cards (MindAR + A-Frame). Keep this next to your Blender file.*

---

## A. Before you export (keeps the file small + predictable)

1. **Decimate heavy meshes.** Select each tree / ground → Modifier Properties → Add Modifier → **Decimate** → Ratio ≈ **0.3**. Check it still looks good. (Scanned/AI meshes are wildly high-poly.)
2. **Resize textures to 1024px.** UV/Image Editor → open each texture → Image → Resize → **1024 × 1024**. (Textures usually cause bloat, not polygons.)
3. **Apply transforms.** Select all → Object → Apply → **All Transforms** (Ctrl+A). Makes A-Frame scale behave.
4. **Set origin to the base.** Select ground → Object → Set Origin → **Origin to Geometry**; move the scene so its base sits at world **(0, 0, 0)**.
5. **Keep the fox OUT of this file** — it exports separately as `fox.glb` so it can animate.

## B. Export settings (File → Export → glTF 2.0)

| Setting | Value |
|---|---|
| Format | **glTF Binary (.glb)** |
| Include → Selected Objects | ✓ (select the diorama first) |
| Transform → **+Y Up** | ✓ (required for A-Frame/three.js) |
| Data → Mesh → **Apply Modifiers** | ✓ (bakes in Decimate) |
| Data → **Material** | Export |
| **Compression → Draco mesh compression** | ✓ (default level) |
| Filename | **`scene.glb`** |

## C. After export

- **Check size.** Target `scene.glb` **< 5–6 MB** (fox adds ~2 MB → total under ~8 MB).
- Too big? Decimate to **0.2** or textures to **512px**, re-export.
- Drop `scene.glb` into `ep/01/` next to `index.html` and `fox.glb`.

---

## D. The scale rule (why sizing works the way it does)

**1 A-Frame unit = the printed card's width.** Print the card at **63 mm** wide → `1 unit ≈ 6.3 cm`.

**Formula:** `scale = (desired size in card-widths) ÷ (native size in Blender)`
Find native size: select object → press **N** → **Item** tab → **Dimensions**.

Your fox is ~1.0 native tall, so its scale ≈ card-widths directly → **fox scale = 0.5** (~3.2 cm).

## E. Target sizes (set these proportions in Blender, ⭐ = Episode 1)

| Asset | Target (card-widths) | ≈ cm @63 mm card | Axis |
|---|---|---|---|
| ⭐ Fox (Fenn) | 0.5 tall | 3.2 | height |
| ⭐ Hanging lantern | 0.35 tall | 2.2 | height |
| ⭐ Bushes / shrubs | 0.22 tall | 1.4 | height |
| ⭐ Leafy trees | 1.0 tall | 6.3 | height |
| ⭐ Ground patch | 0.9 wide | 5.7 | width |
| Rock cluster | 0.28 tall | 1.8 | height |
| Palm / fern tree | 0.9 tall | 5.7 | height |
| Campfire pit | 0.4 wide | 2.5 | width |
| Raft / platform | 0.55 wide | 3.5 | width |
| Rope bridge | 1.2 wide | 7.6 | width |
| Treehouse | 1.3 tall | 8.2 | height |

**Shortcut:** if proportions are already right in Blender, you only tune **two** numbers in `index.html` on your phone: `diorama` scale (start 0.2) and `fox` scale (0.5).
