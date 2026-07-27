# Lanternlight — Scene Build Guide (one diorama per episode)

You'll build a small diorama per episode in Blender and export it as **`ep/0N/scene.glb`**. The character is separate (`hero.glb`) and stands in the scene — so **leave the front-centre open** for it.

## Rules for every scene (keep these consistent)
- **Don't include the character** — it's loaded separately and placed at the centre.
- **Leave the centre-front clear** (about a third of the footprint) so the creature has room and faces the camera; put the big props at the **back and sides**.
- **Footprint** ≈ your Ep 1 forest (it renders at the same scale). Build it flat-ish and compact, like a tabletop model.
- **Origin at the base centre**, **+Y up**, ground sitting at world 0.
- **Export**: glTF **.glb**, **Draco** compression on, textures **1024**, target **< 6 MB**.
- Same **paper-craft, warm, lantern-lit** look as the front card, so all five feel like one world.
- Tip: you can **reuse the Ep 1 ground + a tree** as a starting base for the others and just swap the hero props — big time-saver.

---

## Ep 1 — Fenn · "The Light in Your Pocket"  → `ep/01/scene.glb` *(already built — keep)*
The lantern forest: ground + two leafy trees + the hanging paper lantern + bushes. This is your existing scene; no change needed. (Fenn's is the only dark scene — the lantern relights it.)

## Ep 2 — Momo · "The Bear Who Ate Worries"  → `ep/02/scene.glb`
**Setting: a cosy hollow.** A soft, safe little nook where a worried bear would curl up.
- **From your kit:** ground patch + the **rock/boulder cluster** arranged as a low horseshoe "nook" behind/around the centre + **bushes** at the sides + **1 leafy tree** leaning over from the back + 1–2 **hanging lanterns**.
- **Layout:** rocks and bush cluster hug the back and sides, open dip in the middle for Momo. Warm and enclosed.
- **New assets:** none needed.

## Ep 3 — Tuck & Tally · "Mapmakers of the Ink River"  → `ep/03/scene.glb`
**Setting: the Ink River bank.** A slow river of black ink with the otters' little raft.
- **From your kit:** ground patch as the **bank** on one side + the **wooden raft/platform** floating at the centre-front + **bushes as reeds** along the edges + **1 tree** at the back + a **lantern** hanging low.
- **New assets to make (2):**
  1. **A water/ink plane** — a flat, slightly wavy plane with a dark blue-black, faintly shimmering texture, filling the lower half as the river. (A simple subdivided plane with a ripple/normal look is enough.)
  2. *(optional)* **a torn map prop** lying on the raft (or keep the map on the otters' model).
- **Layout:** river plane across the front/bottom, raft centre, bank + reeds + tree behind. Otters stand on/beside the raft.

## Ep 4 — Silva · "The Almanac of Forgotten Things"  → `ep/04/scene.glb`
**Setting: the treehouse library.** Cosy, warm, full of paper.
- **From your kit:** the **treehouse** as the centrepiece (back) + **1–2 trees** framing it + ground patch + several **hanging lanterns** + bushes.
- **New assets to make (1, optional but nice):**
  1. **Floating book pages / a small stack of books or an open Almanac** on a little stand near the centre, so there's a clear "book" object the memories drift from. (If Silva's model already holds the book, you can skip this.)
- **Layout:** treehouse and trees at the back, a warm glow from the treehouse window, open space front-centre for Silva.

## Ep 5 — Bram · "The Firefly Forge"  → `ep/05/scene.glb`
**Setting: the firefly forge.** A warm little workshop.
- **From your kit:** the **stone campfire / fire-pit** as the **forge** (centre-back) + **rock cluster** as the workbench/wall + ground + **caged lanterns** (use your hanging lanterns, placed low like firefly cages) + 1 tree at the edge.
- **New assets to make (1–2):**
  1. **An anvil** (small stone or metal block) beside the forge — if Bram's model doesn't already include one.
  2. *(optional)* a couple of **tiny hammer/tool props** for flavour.
- **Layout:** forge/fire-pit and anvil centre-back, rocks and cages around, open front-centre for Bram. Warm ember glow.

---

## Summary of NEW assets to create
- **Ep 3:** an **ink-river water plane** (essential), optional torn-map prop.
- **Ep 4:** a **book/Almanac prop** (optional if the model holds one).
- **Ep 5:** an **anvil** (optional if Bram's model includes one), optional tools.
Everything else reuses your existing kit (ground, trees, bushes, rocks, lanterns, raft, treehouse, campfire).

## What I'll do once you export them
Drop each `scene.glb` into its `ep/0N/` folder and send them. I'll wire each in, tune the character's scale/position and the point where the bugs stream out (so they emerge from the right spot — the raft, the book, the forge, etc.), and adjust the lighting per scene. **Then** we add the unique mechanics.
