# Lanternlight — Card 1 (Episodes 1–5): Characters, Scenes & Mechanics

*One card, five episodes. One card art + one AR target (done). Each episode swaps the 3D scene, the creature, and the game. Below: the 3D model prompt, the scene build (from your existing asset kit), and a unique mechanic for each.*

**Model settings for every character (same as Fenn & Momo):** storybook papercraft / cut-paper collage style, low-poly, single baked texture, standing/base pose, **origin at the feet**, ~1 unit tall, export **GLB**. Keep the look consistent with the fox and Momo.

---

## The five mechanics at a glance (all different, all tactile)

| Ep | Character | Task / mechanic | Interaction |
|----|-----------|-----------------|-------------|
| 1 | Fenn the Foxlight | **Light & Catch** — light the lantern, catch the Glimmerlings | tap |
| 2 | Momo the moth-bear | **Breathe** — press & hold to help Momo breathe out its worries | press-and-hold |
| 3 | Tuck & Tally, ink-otters | **Connect the Map** — drag two torn map halves together | drag |
| 4 | Silva the owl | **Re-ink the Almanac** — swipe to reveal hidden words on blank pages | swipe / rub |
| 5 | Bram the beetle | **Forge the Sparkstone** — tap in rhythm with the bellows to grow the fire | rhythm / timing |

---

## Episode 3 — "Mapmakers of the Ink River" (Tuck & Tally)

**3D model prompt (Tripo):**
> Two small playful river otters sitting together, storybook papercraft cut-paper style, glossy wet-look fur, big friendly eyes, one holding a rolled paper map, warm earthy browns with ink-black accents, low-poly stylized, matching a hand-cut collage children's-book aesthetic. Single connected model, base at the feet.

**Scene — "The Ink River":** the **wooden raft/platform** as the centerpiece, a flat **river plane** (I'll add a simple flowing blue-ink surface in code), **reeds/bushes** along the bank, one **tree**. Cooler blue-green light with ink-black water.

**Mechanic — Connect the Map (drag):** two torn map halves float on screen; the child **drags them together with a finger**; when they meet, the map completes and the glowing river route appears — then a tap sends the otters gliding downstream. *Fun because it's hands-on and puzzle-like.*

---

## Episode 4 — "The Almanac of Forgotten Things" (Silva)

**3D model prompt (Tripo):**
> A wise, round, fluffy old owl librarian with big round spectacles, perched and holding an open glowing book, storybook papercraft cut-paper style, soft browns and cream, gentle oversized eyes, low-poly stylized, matching a hand-cut collage children's-book look. Base at the feet.

**Scene — "The Almanac Tree":** the **treehouse** asset as Silva's library, **trees** around it, a warm glow spilling from the treehouse window. Cozy, amber-lit, secret-library mood.

**Mechanic — Re-ink the Almanac (swipe/rub):** the Almanac's pages are blank and grey; the child **swipes/rubs a finger across them** to "re-ink" the hidden words and little pictures (like a scratch-off), revealing the true story of the night the Bridge went dark. *Fun because reveal-by-touch is satisfying and full of discovery.*

---

## Episode 5 — "The Firefly Forge" (Bram)

**3D model prompt (Tripo):**
> A friendly stout beetle blacksmith with a shiny dark shell, wearing a tiny leather apron, holding a small glowing hammer beside a little anvil, storybook papercraft cut-paper style, warm ember tones, big kind eyes, low-poly stylized, matching a hand-cut collage children's-book aesthetic. Base at the feet.

**Scene — "The Firefly Forge":** the **stone campfire / fire pit** as the forge, **rocks** and a couple **trees** around it, caged-firefly lanterns. Warm ember/orange light, glowing and toasty.

**Mechanic — Forge the Sparkstone (rhythm tap):** the bellows pulse with a glowing beat; the child **taps in time** with them — good timing grows the forge fire, bad timing lets it dip. Fill the fire meter to forge a fresh Sparkstone. *Fun because it's a rhythm/timing game with immediate feedback.*

---

## Scene variety for the two already-built episodes

- **Ep 1 — Fenn:** the lantern forest (trees + ground + hanging lantern). ✓ done.
- **Ep 2 — Momo:** re-dress the same forest into a **cozy hollow** — pull **bushes + rocks** to the foreground as a little nook, soften and warm the light. (Currently reuses the Ep 1 forest; a small rearranged export makes it feel like its own place.)

**How to make each scene:** in Blender, arrange the relevant kit pieces into a small diorama and export each as its own `scene.glb` (Draco, 1024px textures, under ~5 MB), the same way you did for Episode 1. I'll wire each into its episode.

---

## Build order

1. You generate the **3 character GLBs** (otters, Silva, Bram) with the prompts above.
2. You export **scene variants** for Ep 2–5 (or reuse Ep 1's forest to start; we can upgrade scenes later).
3. I build **Episodes 3–5** with their unique mechanics, and **upgrade Ep 2** to the press-and-hold "breathe" mechanic so all five feel different.
4. We chain them 1 → 5 with the Continue button (all on the one card).

*Narration: optional per episode — captions carry the story for now; I can script voice-over for any/all when you want to record them.*
