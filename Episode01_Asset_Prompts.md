# EPISODE 01 — "The Light in Your Pocket"
## Concrete production sheet: what to do + exact prompts
*Tools: ChatGPT (stills) → Leonardo AI (animation/video) → ElevenLabs/CapCut (finish) → MindAR page + NFC.*

---

## 0) What Episode 01 needs (the shopping list)
- **1 card artwork** (Fenn) — this is the printed collectible AND the AR tracking image.
- **5 scene stills** — the shots that become the animated video.
- **5 short clips** (~5s each) — animated versions of the stills.
- **1 narration track**, **1 music bed**, **a few SFX**.
- Final export: **`episode.mp4`** (portrait 1080×1920, H.264, ≤10–15 MB).

Two rules:
1. **Card art ≠ video.** The card is a still you print and track; the video is the 5 animated shots. Separate files.
2. **Consistency:** make Fenn once, then reuse him as a reference image everywhere (ChatGPT: attach prior image, say "same fox, same style"; Leonardo: use Image Guidance / Character Reference).

---

## 1) The reusable STYLE BLOCK
Paste this into **every** ChatGPT image prompt so all assets match your reference video:

> Torn craft-paper collage cutout style, 1950s vintage educational illustration, halftone newsprint texture, screen-print grain, sepia-and-cream palette with a single warm lantern-gold glow accent, hand-cut paper shapes with visible torn edges, flat storybook lighting, no text, no border.

---

## 2) ChatGPT prompts

**① STYLE ANCHOR (make first — confirm the look before anything else):**
> A quiet forest of paper lanterns at night, most of them unlit and grey. Hushed, mysterious, gentle mood. [STYLE BLOCK]. Portrait orientation.

**② FENN CARD ART (printed card + AR target — ask for portrait 1024×1536):**
> Collectible card portrait of "Fenn the Foxlight," a small fox with a glowing lantern for a tail. The fox is off-center, mid-step, looking back over its shoulder with a curious expression. Busy layered background of hand-cut paper lanterns and leaves — lots of small distinct shapes, high contrast, asymmetric composition. Tail glows warm gold. [STYLE BLOCK]. Portrait card orientation.

*(The "busy / high-contrast / asymmetric" wording makes the card track reliably in AR. Symmetric, flat art tracks badly.)*

**③–⑦ THE FIVE SCENE STILLS** — do these in ONE ChatGPT thread; attach the Fenn image as reference each time. Ask for portrait framing (9:16 or 2:3):

- **Shot 1 — Grey forest (establishing):** Wide shot of a silent forest of paper lanterns, almost all unlit and grey, faint cold moonlight, drifting fog, lonely mood. [STYLE BLOCK].
- **Shot 2 — Sparkstone wakes:** Close shot of a small glowing stone on the grey forest floor, emitting warm lantern-gold light that pushes back the surrounding grey. [STYLE BLOCK].
- **Shot 3 — Fenn peeks:** The same small fox with a dim lantern tail peeking shyly from behind a grey paper tree, wide curious eyes, a hint of warm gold on its face, looking toward a warm light off-frame. [STYLE BLOCK].
- **Shot 4 — The sneeze:** The same fox sneezing, releasing one bright golden spark from its lantern tail, the spark flying toward a nearby lantern, the grey scene lit by the burst. [STYLE BLOCK].
- **Shot 5 — Lantern blooms (payoff):** A single paper lantern bursting into warm golden light, color spreading into the grey forest, the fox watching happily with its tail now glowing, hopeful and magical. [STYLE BLOCK].

Download all as PNG. Keep the Fenn card as a separate clean file (you'll print it and compile it to `targets.mind`).

---

## 3) Leonardo AI — animate each still (Image → Video)
Upload each still, use **Image to Video / Motion**, paste the motion prompt, keep motion **subtle** (this style breaks if it moves too much). Aim ~5s per clip; trim later.

| Shot | Motion prompt | Motion strength |
|---|---|---|
| 1 | Slow push-in through the foggy lantern forest, drifting fog, faint flicker on distant lanterns, gentle paper-layer parallax. | ~3 (low) |
| 2 | The stone's gold glow pulses and grows brighter, soft light rays shimmer, dust motes drift upward. | ~3 |
| 3 | The fox leans out slowly from behind the tree, ears twitch, eyes blink, tail flickers dimly. | ~4 |
| 4 | The fox sneezes, a bright spark shoots across the frame, quick burst of light, small body motion. | ~6–7 |
| 5 | The lantern ignites and blooms, warm golden glow spreads outward, the fox's tail lights up, gentle celebratory shimmer. | ~5 |

If your Leonardo model has no text box, just set the motion-strength slider as above. Use **Character Reference / Image Guidance** with the Fenn card so he stays on-model.

---

## 4) Narration (the vox voice) — ElevenLabs free tier
Pick ONE warm, friendly narrator voice and reuse it for the whole series. Record these lines (from the story bible), timed to the shots:

- (Over Shots 1–2) *"Every light starts the same way. Small. Uncertain. Yours."*
- (Over Shot 3) *"This is Fenn. His lantern went out a long time ago. He's been waiting — not for a hero. For you."*
- (Over Shots 4–5) *"So light it. Go on. The whole world's been holding its breath for this."*

End-beat text (add in CapCut, not narration): **"Collected! Find card 02 →"**

---

## 5) Music + SFX (free, licensed)
- Music bed: **Pixabay Music** or **YouTube Audio Library** — one gentle, curious theme.
- SFX from **Freesound**: a soft sparkle (Shot 4 spark), a warm "whoomph" glow (Shot 5 bloom), quiet forest ambience under everything.

---

## 6) Assemble in CapCut (free)
1. Drop the 5 clips in order; trim to ~8–12s total feel (aim 45–60s with narration pacing — hold shots, don't rush).
2. Add narration, music (low), SFX.
3. Add a **halftone/grain overlay** (blend: overlay/soft-light) for texture consistency.
4. Add captions in a **red accent** and the chapter marker **"LANTERNLIGHT · 01/10"** top-left.
5. Export: **1080×1920 portrait, MP4 / H.264, ≤10–15 MB**. Name it **`episode.mp4`**.

---

## 7) Wire it up (from the strategy doc)
1. Compile the **Fenn card PNG** → `targets.mind` at https://hiukim.github.io/mind-ar-js-doc/tools/compile
2. Put `index.html` (from the bible), `targets.mind`, `episode.mp4` in `/ep/01/` on **GitHub Pages**.
3. Test on your phone at `https://<you>.github.io/lanternlight/ep/01/` — aim at the printed card.
4. Write that URL to an **NTAG213** tag with the **NFC Tools** app. Tap to confirm the whole loop.

---

## Quick consistency checklist
- [ ] Same STYLE BLOCK on every image
- [ ] Fenn generated once, reused as reference everywhere
- [ ] Grey → gold color logic holds across all 5 shots (start grey, end gold)
- [ ] Card art is busy/asymmetric (tracks well) and saved separately from the video
- [ ] Final MP4 is portrait, small file, named `episode.mp4`
