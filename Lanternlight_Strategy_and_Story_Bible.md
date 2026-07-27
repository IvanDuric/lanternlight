# LANTERNLIGHT — NFC-Triggered AR Story Cards
### Full strategy: software stack · production pipeline · story world · first 10 episodes

*Working series title: **LANTERNLIGHT: Tales from the Underglow**. Kids 6–12, wonder/adventure. Each NFC card = one creature + one episode. Visual style: the collage / halftone / papercraft "Vox explainer" look from your reference video.*

---

## PART 1 — HOW IT WORKS (the one-paragraph version)

A child taps a printed card on their phone. The phone's NFC reader opens a web link — **no app to install**. That link is a WebAR page: the phone camera turns on, recognizes the card's artwork, and a glowing "portal" grows out of the card. A little creature climbs out, and a short (45–75 second) narrated, animated scene plays in the collage/halftone style. At the end the child "collects" the creature and gets a hook to the next card. Every card is a separate episode; collecting them relights a story-world.

The whole thing is buildable with **free tools** and hosted for **free**. Below is exactly what to use and how.

---

## PART 2 — SOFTWARE STRATEGY (free + easy)

### 2.1 The recommended stack (this is the "just do this" path)

| Layer | Tool | Cost | Why |
|---|---|---|---|
| WebAR engine | **MindAR + A-Frame** | Free, open-source | Image tracking + no app. ~10 lines to start. The only actively maintained free WebAR SDK with commercial-grade features. |
| Hosting (must be HTTPS) | **GitHub Pages** or **Cloudflare Pages** or **Netlify** | Free | Camera access requires HTTPS; all three give it automatically. |
| NFC hardware | **NTAG213 / NTAG215** blank stickers or cards | ~€0.20–0.50 each | Cheapest reliable NDEF tags. 215 holds more if you ever need it. |
| NFC writing | **NFC Tools** app (iOS/Android) | Free | Write a "URL" record to each tag in 30 seconds. |
| The animated scene | AI image + AI motion + TTS + free music (see Part 3) | Free tiers | Produces the vox-style clip that plays inside AR. |

**Why not the famous paid platforms?** As of **Feb 28, 2026** the hosted **8th Wall** platform was retired by Niantic and the engine was released **free and open-source** (Niantic Studio). It's powerful but now expects you to self-host, which is *more* setup than MindAR, not less. So: start on MindAR; only graduate to Niantic Studio if you later need advanced world-tracking/SLAM.

### 2.2 If you'd rather NOT touch code (no-code alternative)

Use a hosted WebAR builder with a drag-and-drop editor and a free tier: **MyWebAR** or **Zappar / ZapWorks**. Trade-offs: a watermark and monthly view/project limits on the free tier, and you're renting their hosting. Good for a fast prototype; MindAR is better for a real product you own. You can start no-code to validate the idea this week, then move to MindAR.

### 2.3 How NFC → AR actually connects (the important mental model)

The NFC card does **one dumb, reliable thing**: it stores a URL and hands it to the phone. All the "smarts" live on the web page at that URL.

```
[Tap card] → phone reads NFC URL → opens browser
   → WebAR page loads → camera on
   → page recognizes the CARD ART as a tracking image
   → portal + creature + narrated scene appear anchored to the card
```

Two design consequences:
- **The card artwork does double duty**: it's both the collectible and the AR tracking target. Design each card with a busy, high-contrast, asymmetric illustration (great for tracking) rather than flat/symmetric art.
- **Each card's URL points to that episode's page** (e.g. `.../ep/01`, `.../ep/02`). One tiny page per episode. To change/fix an episode later you edit the page — you never re-write the cards.

---

## PART 3 — PRODUCTION PIPELINE (making the vox-style clip, for free)

Your reference video is a **collage / halftone / torn-paper / sepia** motion-graphics style with a documentary narrator, a red accent, and chapter numbers. Here's a free pipeline that reproduces that look and drops it into AR.

**Step A — Script & narration beats.** Already done for you in Part 5 (each episode has narration lines).

**Step B — Art (stills) in the collage/halftone style.** Free AI image tools: **Microsoft/Bing Image Creator** (DALL·E, free), **Leonardo.ai** (free daily credits), **Krea** (free tier), or **Stable Diffusion via ComfyUI** (free, local, unlimited). Prompt seed to match your video:
> *"1950s educational collage, torn craft-paper cutouts, halftone newsprint texture, sepia and cream tones, single red accent, screenprint grain, hand-cut paper characters, flat lighting, vintage explainer illustration"*

**Step C — Motion.** Two easy routes, both free-tier:
- **2.5D parallax (cheapest, on-style):** turn a still into a depth-animated shot with **Immersity AI** (formerly LeiaPix) or a CapCut depth/parallax effect. This "paper layers sliding" look matches your reference perfectly.
- **AI video:** animate stills or text with **Luma Dream Machine**, **Kling**, **Hailuo/MiniMax**, or **Pika** free credits for short creature movements.

**Step D — Voice.** Free TTS for the narrator: **ElevenLabs** free tier (best quality), or free alternatives **TTSMaker** / **Edge Read-Aloud** / **PlayHT** free. Pick one warm, friendly narrator voice and keep it consistent across all episodes.

**Step E — Music & SFX (free, licensed).** **Pixabay Music**, **YouTube Audio Library**, **Incompetech** (Kevin MacLeod, credit required) for music; **Freesound** for sparkle/whoosh SFX. Keep one musical theme; vary tempo per episode.

**Step F — Assemble.** **CapCut** (free) or **DaVinci Resolve** (free). Add the red-accent captions, chapter number (01/10…), halftone overlay, and export **portrait 1080×1920, MP4 (H.264), under ~10–15 MB** so it loads fast on phones over mobile data. Loop-friendly ending.

**Step G — Drop into AR.** The MindAR page (Part 4) plays this MP4 on a plane inside the portal, plus one tap-reactive creature. Done.

> **Effort-saving recommendation for the AR moment (your "mix / recommend" answer):** Don't build heavy interactive 3D. Use a **video-portal + one interactive creature**: the narrated MP4 is your "vox scene," and a single lightweight 3D or 2.5D creature the child can tap for a reaction. This keeps every episode cheap to make, on-style, and fast on phones — while still feeling like true AR.

---

## PART 4 — COMPLETE WORKING CODE (copy-paste, deploy free)

This is a full, single-file MindAR + A-Frame WebAR page. It: tracks the card art, shows a glowing portal, plays the episode video, and shows a creature that reacts when tapped. Repeat this file once per episode (swap the video, image target, and text).

### 4.1 Step-by-step to go live

1. Create a free **GitHub** account → new repository named `lanternlight` → enable **Settings → Pages → Deploy from branch → main**. Your site will be `https://<you>.github.io/lanternlight/`.
2. **Compile your card art into a tracking file.** Go to the MindAR image-target compiler: `https://hiukim.github.io/mind-ar-js-doc/tools/compile`. Upload the card's artwork (a clean PNG/JPG of the front). Download the resulting **`targets.mind`** file.
3. Put these in the repo, per episode, e.g. in `/ep/01/`: `index.html` (below), `targets.mind`, `episode.mp4`, and optionally `creature.glb`.
4. Commit/push. Visit `https://<you>.github.io/lanternlight/ep/01/` on your phone to test (allow camera). Point the camera at the printed card.
5. Write that URL onto the NFC card (Part 4.3).

### 4.2 `index.html` (one per episode)

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <title>Lanternlight — Episode 01</title>
  <!-- A-Frame + MindAR (image tracking). Pinned versions for stability. -->
  <script src="https://aframe.io/releases/1.5.0/aframe.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mind-ar@1.2.5/dist/mindar-image-aframe.prod.js"></script>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; }
    /* Simple tap-to-start gate: iOS needs a user gesture before audio/video can play */
    #start {
      position: fixed; inset: 0; z-index: 9999;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      background: #1a1512; color: #ece7e1; text-align: center; padding: 24px;
    }
    #start h1 { font-size: 22px; letter-spacing: 1px; }
    #start p  { max-width: 300px; opacity: .85; line-height: 1.4; }
    #start button {
      margin-top: 20px; padding: 14px 28px; font-size: 18px; font-weight: 700;
      border: none; border-radius: 12px; background: #d64b3a; color: white;
    }
    #hint {
      position: fixed; bottom: 18px; left: 0; right: 0; z-index: 50;
      text-align: center; color: #fff; text-shadow: 0 1px 4px #000;
      font-size: 15px; pointer-events: none;
    }
  </style>
</head>
<body>
  <!-- Start gate -->
  <div id="start">
    <h1>LANTERNLIGHT · 01/10</h1>
    <p>Point your camera at your Sparkstone card to wake the creature inside.</p>
    <button id="startBtn">Tap to begin</button>
  </div>

  <div id="hint" style="display:none;">Aim at your card ✨</div>

  <a-scene
    mindar-image="imageTargetSrc: ./targets.mind; autoStart: false; uiScanning: no; uiLoading: no;"
    color-space="sRGB" renderer="colorManagement: true, physicallyCorrectLights"
    vr-mode-ui="enabled: false" device-orientation-permission-ui="enabled: false">

    <a-assets>
      <video id="epVideo" src="./episode.mp4" loop="false" playsinline webkit-playsinline
             crossorigin="anonymous" preload="auto"></video>
      <!-- Optional 3D creature. If you don't have a GLB yet, the video plane alone works. -->
      <!-- <a-asset-item id="creatureModel" src="./creature.glb"></a-asset-item> -->
    </a-assets>

    <a-camera position="0 0 0" look-controls="enabled: false"></a-camera>

    <!-- Everything here is anchored to the card (target index 0) -->
    <a-entity mindar-image-target="targetIndex: 0">

      <!-- Glowing "portal" behind the video -->
      <a-circle radius="0.85" color="#ffcf6b" opacity="0.35"
                position="0 0 -0.02"
                animation="property: scale; from: 0.2 0.2 0.2; to: 1 1 1; dur: 600; easing: easeOutBack">
      </a-circle>

      <!-- The narrated vox-style episode video, playing on a plane above the card -->
      <a-video id="epPlane" src="#epVideo"
               width="1" height="1.777" position="0 0.2 0"
               animation="property: position; from: 0 0.2 -0.3; to: 0 0.2 0; dur: 700; easing: easeOutCubic">
      </a-video>

      <!-- Optional interactive creature (uncomment asset above + this block once you have a GLB) -->
      <!--
      <a-gltf-model id="creature" src="#creatureModel"
                    position="0 0.05 0.05" scale="0.25 0.25 0.25"
                    class="clickable"
                    animation__idle="property: position; dir: alternate; loop: true; to: 0 0.1 0.05; dur: 1400; easing: easeInOutSine">
      </a-gltf-model>
      -->

      <!-- "Collected!" label appears when the video ends -->
      <a-text id="collected" value="Collected! Find card 02 →" align="center"
              color="#ffffff" position="0 -0.7 0" width="2.4" visible="false"></a-text>
    </a-entity>
  </a-scene>

  <script>
    const sceneEl   = document.querySelector('a-scene');
    const startEl   = document.getElementById('start');
    const startBtn  = document.getElementById('startBtn');
    const hintEl    = document.getElementById('hint');
    const video     = document.getElementById('epVideo');
    const collected = document.getElementById('collected');
    const targetEl  = document.querySelector('[mindar-image-target]');

    // Start AR only after a tap (required for camera + iOS video/audio autoplay)
    startBtn.addEventListener('click', async () => {
      startEl.style.display = 'none';
      hintEl.style.display  = 'block';
      const mindar = sceneEl.systems['mindar-image-system'];
      await mindar.start();               // turns on camera + tracking
    });

    // Play the episode when the card is found; pause if it leaves the frame
    targetEl.addEventListener('targetFound', () => {
      hintEl.style.display = 'none';
      video.play().catch(() => {});
    });
    targetEl.addEventListener('targetLost', () => {
      video.pause();
    });

    // Show the "collected" hook at the end
    video.addEventListener('ended', () => { collected.setAttribute('visible', true); });

    // Tap the creature → little reaction (works once you enable the GLB block)
    sceneEl.addEventListener('click', (e) => {
      const c = document.getElementById('creature');
      if (!c) return;
      c.setAttribute('animation__tap',
        'property: rotation; from: 0 0 0; to: 0 360 0; dur: 600; easing: easeOutQuad');
    });
  </script>
</body>
</html>
```

**Notes that will save you pain:**
- **HTTPS is mandatory** for the camera — that's why GitHub/Cloudflare/Netlify Pages (not opening the file locally) is the host.
- **iOS needs a tap** before video/audio can start — that's what the "Tap to begin" gate is for. Don't remove it.
- Keep `episode.mp4` small (**≤10–15 MB**, portrait, H.264) so it streams fast on mobile data.
- If you don't have a 3D creature yet, ship with just the **video portal** — it already looks great. Add the GLB later.

### 4.3 Writing the NFC card (per card)

1. Buy blank **NTAG213** stickers/cards.
2. Install **NFC Tools** (free, iOS/Android).
3. In NFC Tools: **Write → Add a record → URL/URI →** enter that episode's page, e.g. `https://<you>.github.io/lanternlight/ep/01/` → **Write** → hold the tag to the phone until it confirms.
4. (Optional) **Lock** the tag in NFC Tools so the URL can't be overwritten.
5. Tap to test: the phone should show a notification that opens the page. On iPhone 7+/iOS 11+ and most Androids this works with **no app installed**.

> Tip: put the printed artwork on the front of the card and the NFC sticker on the back, aligned so "tap the card, then look at the card" is one smooth motion.

---

## PART 5 — THE STORY WORLD

### 5.1 The pitch

Long ago the world had **two layers**: the Everyday (ours) and the **Underglow** — a hidden, glowing world made of *the small wonders people forget*: lost mittens, half-remembered songs, the shapes you see in clouds. A great **Bridge of Lanterns** connected the two, kept lit by the **Lanternkeepers**. One night the Bridge went dark. Now the Underglow is fading into grey — its creatures, the **Glimmerlings**, are losing their colors and their memories to a slow, sad quiet called **the Hush**.

But a few fragments of the old Bridge survived as glowing stones — **Sparkstones**. Whoever holds one and lets its light in becomes the newest Lanternkeeper. *That's the child.* Each **card is a Sparkstone**: tapping it wakes one Glimmerling, reveals one episode, and relights one more lantern. Collect the cards → relight the Bridge → bring the color back.

**Why this works for your format:** it's built for collectibility (each card = one creature to rescue + one lantern relit), it's second-person and empowering ("*you* are the Keeper"), the "hidden world beneath the ordinary" premise matches the Vox-documentary tone, and the papercraft/collage art style *is literally in-world* — the Underglow looks like torn paper and lantern-light.

### 5.2 The look (matches your reference video)

Warm sepia + cream base, deep ink shadows, a single glowing accent (lantern-gold, with the red accent reserved for the Hush/danger). Torn craft-paper cutouts, halftone newsprint grain, hand-cut characters, flat storybook lighting. Environments: **mushroom-lantern forests**, the **Night Market** (floating paper stalls), the **Ink River** (where stories flow like water), **the Dim** (drained, colorless zone the Hush has taken), and the broken **Bridge of Lanterns**.

### 5.3 The cast (each is a collectible card)

- **Fenn** — a small fox with a lantern for a tail ("Foxlight"). The narrator's on-screen buddy; warm, quick, a little mischievous. The child's guide. *(Card 01.)*
- **Momo** — a round moth-bear who gently eats worries and puffs them out as fireflies. Theme: courage/calm. *(Card 02.)*
- **Tuck & Tally** — twin ink-otters, chaotic mapmakers of the Ink River. Theme: curiosity/teamwork. *(Card 03.)*
- **Silva** — an old owl who keeps the **Almanac**, the book of everything the Underglow is trying not to forget. Theme: memory. *(Card 04.)*
- **Bram** — a beetle blacksmith who forges Sparkstones in a firefly forge. Theme: patience/craft. *(Card 05.)*
- **The Grumble** — a huge, shy stone golem guarding the Bridge's first gate; not mean, just lonely. Theme: kindness to the grumpy. *(Card 06.)*
- **Wisp** — a Dimling (a grey, forgotten creature) who wants to remember its color. Theme: nobody is beyond saving. *(Card 07.)*
- **Lox** — the *last* Lanternkeeper before the dark night; now scattered as a constellation, speaking in riddles of light. Theme: legacy/hope. *(Card 09.)*
- **The Hush** — not a monster but a *quiet* — the slow forgetting that greys the world. It has no face; it's fog, silence, and things left behind. Redeemable, not destroyable: you don't beat the Hush, you *remember loudly* until the light comes back. *(Central to 08 & 10.)*

### 5.4 Season 1 arc (across the 10 cards)

Wake up as a Keeper → gather friends and relight small lanterns → learn what happened to the Bridge → cross the Dim → face the Hush at the dark Bridge → relight the Bridge of Lanterns (finale) → a new fragment falls in the Everyday world, teasing Season 2. Gentle stakes, one warm lesson per episode, a running "collect to relight" meter.

---

## PART 6 — THE FIRST 10 EPISODES

*Each episode is ~45–75s in AR. Format per entry: the hook, the beat-by-beat scene, sample narrator lines in your vox style, the AR interaction, the collectible reward, and the cliffhanger to the next card.*

---

### Episode 01 — "The Light in Your Pocket"
**Card:** Fenn the Foxlight · **Theme:** you are enough to begin.
**Scene:** A grey, quiet forest of unlit paper lanterns. The child's Sparkstone glows; a tiny fox with a dim lantern-tail peeks out, sneezes a single spark, and the nearest lantern flickers awake — a bloom of gold in all the grey.
**Narrator (vox style):** *"Every light starts the same way. Small. Uncertain. Yours."* … *"This is Fenn. His lantern went out a long time ago. He's been waiting — not for a hero. For you."*
**AR interaction:** Tap Fenn → he lights his tail from your Sparkstone; the portal brightens one notch. First lantern on the "relight meter" fills.
**Reward:** Fenn joins you. Keeper badge: *Lantern 1 of 10.*
**Cliffhanger:** Fenn hears something crying softly in the dark trees. *"Come on — someone's scared out there."*

---

### Episode 02 — "The Bear Who Ate Worries"
**Card:** Momo the moth-bear · **Theme:** courage is being scared and staying kind.
**Scene:** In a hollow, a round moth-bear hides, trembling; the Hush-fog creeps at the edges. Momo is so full of other people's worries it can't glow. The child helps it breathe out — worries leave as fireflies that relight three lanterns.
**Narrator:** *"Momo carries everyone's worries so they don't have to. But nobody ever carried Momo's."* … *"Turns out, the bravest thing in the Underglow is a deep breath."*
**AR interaction:** Tap-and-hold Momo to "breathe with it" — each hold puffs out a firefly; fill three lanterns.
**Reward:** Momo joins. *Lantern 2 of 10.* Unlocks the "calm breath" that clears small Hush-fog later.
**Cliffhanger:** The fireflies drift toward a rushing sound — water, and laughter. *"That'll be the otters. Hold onto something."*

---

### Episode 03 — "Mapmakers of the Ink River"
**Card:** Tuck & Tally, the ink-otters · **Theme:** curiosity + teamwork.
**Scene:** Two otters ride a river made of flowing ink, painting a map as they go — but the map to the Bridge is torn in half, one piece with each otter, and they won't share. The child gets them to combine halves; the full map lights up.
**Narrator:** *"Tuck knew where the Bridge was. So did Tally. Neither would admit the other was right."* … *"A map's just a story about where you're brave enough to go."*
**AR interaction:** Drag the two torn map halves together on screen → full map glows, revealing the route to the Bridge of Lanterns.
**Reward:** The twins join; you unlock the **Map** (shows your progress toward the Bridge). *Lantern 3 of 10.*
**Cliffhanger:** The map's center is a blank, grey smudge. *"That's the Dim. Nobody remembers what's there anymore. Silva might."*

---

### Episode 04 — "The Almanac of Forgotten Things"
**Card:** Silva the owl · **Theme:** memory is worth keeping.
**Scene:** A crooked library of floating pages. Silva guards the **Almanac** — the book of everything the Underglow is trying not to forget — but its pages are going blank as the Hush spreads. The child helps re-ink one page: the true story of the night the Bridge went dark.
**Narrator:** *"The Hush doesn't roar. It erases. Quietly. A song here. A name there."* … *"Silva has stayed awake for a hundred years so one book would remember. Tonight, it needs a Keeper to turn the page."*
**AR interaction:** Tap the glowing words to "re-ink" them; the page fills and reveals the backstory (first reveal of the Bridge and Lox).
**Reward:** Silva joins; the **Almanac** unlocks (a card-collection log in-world). *Lantern 4 of 10.*
**Cliffhanger:** The page names one more thing you'll need: a new Sparkstone. *"Only Bram still knows how to forge them."*

---

### Episode 05 — "The Firefly Forge"
**Card:** Bram the beetle blacksmith · **Theme:** good things take patience.
**Scene:** A workshop lit by caged fireflies. Bram forges Sparkstones but his forge-fire has dwindled to one ember. The child helps him relight it — slowly, carefully, not rushing — and together they forge a fresh Sparkstone.
**Narrator:** *"You can't hurry a light into being. Bram learned that the hard way, a thousand sparks ago."* … *"Slow is not the same as stopped."*
**AR interaction:** A timing mini-beat — tap in rhythm with the bellows to grow the ember; too fast and it gutters. Forge one Sparkstone.
**Reward:** Bram joins; you gain a spare **Sparkstone** (used at the Bridge). *Lantern 5 of 10.* Halfway meter celebration.
**Cliffhanger:** The road to the Bridge is blocked by something enormous and unmoving. It sighs. *"Oh no. Not the Grumble."*

---

### Episode 06 — "The Grumble at the Gate"
**Card:** The Grumble, stone golem · **Theme:** grumpy usually means lonely.
**Scene:** A giant stone golem blocks the first gate of the Bridge, growling at everyone to go away. But the child notices the Grumble is covered in unlit lanterns — it's been guarding them in the dark, alone, for a century, afraid it failed. Kindness, not force, opens the gate.
**Narrator:** *"Everyone ran from the Grumble. So the Grumble decided it was something to run from."* … *"It had been holding the gate shut to keep the dark in — not knowing it was keeping the light out."*
**AR interaction:** Instead of "fighting," tap each lantern on the Grumble to light it; when the last lights, the golem smiles and steps aside.
**Reward:** The Grumble joins (now your gentle giant). *Lantern 6 of 10.* The Bridge is in sight.
**Cliffhanger:** Beyond the gate: the **Dim** — colorless, silent, full of grey shapes watching. One shape steps forward. *"…is someone there? I think… I used to be blue."*

---

### Episode 07 — "The Dimling Who Wanted Its Color"
**Card:** Wisp the Dimling · **Theme:** no one is beyond saving.
**Scene:** In the grey Dim, the child meets Wisp — a Dimling, one of the "forgotten" creatures the Hush drained. Everyone's afraid of Dimlings. But Wisp isn't scary; it's just sad and can't remember its own color. The child helps it remember — and Wisp blooms blue.
**Narrator:** *"They said the Dimlings were monsters. They were only creatures the world stopped looking at."* … *"Color, it turns out, is just being remembered by someone who cares."*
**AR interaction:** Hold your Sparkstone light on Wisp and tap the memories that float up (a kite, a song, the sea) until the right one turns it blue.
**Reward:** Wisp joins — your first *rescued* Dimling, proof the Hush can be undone. *Lantern 7 of 10.*
**Cliffhanger:** Wisp remembers something terrible and wonderful: *"The Bridge isn't broken. Someone put it out on purpose. And it's still up there… in the Hush."*

---

### Episode 08 — "Into the Hush"
**Card:** *(Special "event" card — the Hush)* · **Theme:** remember loudly.
**Scene:** The child, Fenn, and friends step into the thickest Hush — where sound and color vanish and it's tempting to just… stop, and forget, and rest. The Hush isn't a monster; it's a soft grey nothing that makes you sleepy. The child keeps everyone awake by making noise, light, memory — refusing to be quiet.
**Narrator:** *"The Hush never shouts. It whispers, 'shhh… it's easier to forget… just close your eyes.'"* … *"So the Keeper did the bravest, loudest thing in the world. They remembered — out loud."*
**AR interaction:** The screen dims and mutes; the child taps rapidly / makes the creatures "call out," each tap punching a hole of color and sound in the grey until the path clears.
**Reward:** You pass through the Hush (no defeat — you *outshine* it). *Lantern 8 of 10.* The dark Bridge appears ahead.
**Cliffhanger:** On the Bridge stands a figure made of dead lantern-light. *"A Keeper? After all this time?" It knows your name. "I'm the one who put the lights out. I'm Lox."*

---

### Episode 09 — "The Last Keeper's Riddle"
**Card:** Lox, the fallen Keeper · **Theme:** even heroes get scared — and get second chances.
**Scene:** Lox — the *last* Lanternkeeper — didn't fall to the Hush; Lox put the Bridge out **on purpose**, to "protect" the Everyday from the Hush by cutting it off, and has regretted it for a hundred lonely years. Now a constellation of guttering light, Lox tests the child with a riddle about what a Keeper really protects. The child answers with everything they've learned: you don't protect people by putting out the light — you teach them to carry their own.
**Narrator:** *"The greatest Keeper who ever lived made the greatest mistake — out of love, and out of fear."* … *"Lox had been waiting a century for someone to prove the light was worth relighting. Not to win. To forgive."*
**AR interaction:** Solve a light-riddle: arrange your collected creatures' glows (from cards 01–07) in the constellation to spell the answer — *"together."*
**Reward:** Lox is forgiven and rejoins the light, handing you the **Keeper's Lantern**. *Lantern 9 of 10.*
**Cliffhanger:** *"The Bridge will relight for a true Keeper. But only all at once — every light you saved, together. Are you ready?"*

---

### Episode 10 — "The Bridge of Lanterns" *(Season 1 finale)*
**Card:** The Bridge of Lanterns (foil/special finale card) · **Theme:** what we relight together stays lit.
**Scene:** The child stands at the dark Bridge with every creature they've saved. One by one, then all together, the lanterns relight — Fenn, Momo, the otters, Silva, Bram, the Grumble, Wisp, Lox — until the whole Bridge blazes gold and the Underglow floods back with color. The Hush doesn't die; it just… quiets, pushed to the edges, waiting. But tonight, the light wins.
**Narrator:** *"One light is a start. Ten lights are a bridge."* … *"The Keeper didn't chase the dark away forever. Nobody can. They just made sure the world remembered how to glow — and taught it to do so again, and again, and again."*
**AR interaction:** A big finale beat — sweep your phone along the card and each rescued creature's lantern ignites in sequence; the full Bridge lights and the color-meter hits 10/10 with a celebration.
**Reward:** **Master Lanternkeeper** badge; the full collection (cards 01–10) glows as a set. *Bridge relit: 10 of 10.*
**Cliffhanger (Season 2 seed):** Back in the Everyday world, on the child's windowsill, a **new Sparkstone** falls from the sky — a color no one in the Underglow has ever seen. Fenn's eyes go wide. *"…that's not one of ours. Keeper — where did* that *come from?"* **To be continued.**

---

## PART 7 — SUGGESTED BUILD ORDER (so you ship, not stall)

1. **This week:** Make **Episode 01** end-to-end as a vertical slice — one card, one video, one MindAR page on GitHub Pages, one written NFC tag. Prove the tap→AR loop on a real phone.
2. **Next:** Lock the art style and the narrator voice on Ep 01; reuse them for all 10.
3. **Then:** Batch-produce Eps 02–10 (same template, swap video + target + text).
4. **Later (optional):** Add the interactive 3D creature (GLB), a shared "relight meter" across episodes, and a Season 2.

---

### Sources
- MindAR (free, open-source WebAR — image tracking, no app): https://github.com/hiukim/mind-ar-js · docs https://hiukim.github.io/mind-ar-js-doc/
- AR.js (alternative free WebAR): https://github.com/AR-js-org/AR.js/
- 8th Wall / Niantic Studio now free & open-source (hosted platform retired Feb 28, 2026): https://roadtovr.com/niantic-webar-platform-8th-wall-open-source/ · https://www.8thwall.com/products/niantic-studio
- Writing NFC tags to open a URL with no app: https://nfc.cool/blog/write-nfc-tags-iphone/ · https://www.rfidlabel.com/how-to-make-an-nfc-tag-open-a-url/ · NFC Tools app https://apps.apple.com/us/app/nfc-tools/id1252962749
