/* Lanternlight — two ways to play, shared by every episode.
 *
 *   AR mode      MindAR opens the camera and pins the diorama to the printed
 *                Sparkstone card.
 *   screen mode  no camera, no card, no marker. The diorama stands in front of
 *                an ordinary perspective camera and the child drags to turn it.
 *
 * Everything else about an episode — narration, captions, tapping the character,
 * the mini-game, the end card — is untouched, because the episode logic never
 * cared how its rig reached the screen.
 *
 * Each episode page needs three things in its markup:
 *
 *   <a-scene>                    WITHOUT a mindar-image attribute
 *   <a-entity id="anchor">       WITHOUT mindar-image-target
 *   <a-entity id="camPivot"><a-camera ...></a-camera></a-entity>
 *
 * and then calls, once its own revealScene() exists:
 *
 *   LL.install({ targets: '../01/targets.mind?v=2', reveal: revealScene });
 *
 * Both MindAR components are attached at runtime, only in AR mode. That matters:
 * mindar-image-target hides its entity until a marker is found and its init()
 * reaches into the mindar-image system, so leaving it in the markup gives screen
 * mode a permanently invisible, half-initialised rig.
 */
(function () {
  const LL = (window.LL = window.LL || {});
  LL.screenMode = false;

  /* --- audio ---------------------------------------------------------------
     Unlock the media elements inside the click, and WAIT for it. Each element is
     played muted and paused again once that promise resolves, so anything that
     called play() before the promise landed got silenced by the unlock's own
     pause() arriving late. AR never showed this because starting the camera
     takes seconds; screen mode goes straight from the click to the reveal. */
  LL.unlockAudio = function () {
    const media = Array.from(document.querySelectorAll('audio, video'));
    return Promise.all(media.map((a) => {
      a.muted = true;
      const p = a.play();
      if (!p) { a.muted = false; return Promise.resolve(); }
      return p.then(() => { a.pause(); a.currentTime = 0; a.muted = false; })
              .catch(() => { a.muted = false; });
    }));
  };

  /* --- orbit camera --------------------------------------------------------
     Driven by rotating a pivot entity and sliding the camera along its local Z,
     through plain setAttribute calls. Writing to the camera's object3D directly
     fights A-Frame's own position component and loses. */
  const orbit = { yaw: 0, pitch: 22, radius: 6, min: 1, max: 60, cx: 0, cy: 0, cz: 0 };
  LL.orbit = orbit;

  function applyOrbit() {
    const pivot = document.getElementById('camPivot');
    if (!pivot) return;
    const cam = pivot.querySelector('a-camera, [camera]');
    pivot.setAttribute('position', orbit.cx + ' ' + orbit.cy + ' ' + orbit.cz);
    pivot.setAttribute('rotation', orbit.pitch + ' ' + orbit.yaw + ' 0');
    if (cam) cam.setAttribute('position', '0 0 ' + orbit.radius);
  }
  LL.applyOrbit = applyOrbit;

  // Frame on what is actually there. Guessing a distance means guessing the
  // rig's final size, and the rig animates from scale 0.05 to 4 — anything
  // measured too early frames a speck and renders an empty background.
  LL.frameOn = function (el) {
    if (!el || !el.object3D) return false;
    const box = new THREE.Box3().setFromObject(el.object3D);
    if (box.isEmpty()) return false;
    const size = box.getSize(new THREE.Vector3());
    const extent = Math.max(size.x, size.y, size.z);
    if (!(extent > 0.01)) return false;
    const centre = box.getCenter(new THREE.Vector3());
    orbit.cx = centre.x; orbit.cy = centre.y; orbit.cz = centre.z;
    orbit.radius = extent * 1.9;
    orbit.min = extent * 0.6;
    orbit.max = extent * 6;
    applyOrbit();
    return true;
  };

  function bindOrbitInput(sceneEl) {
    const canvas = sceneEl.canvas || document.body;
    let dragging = false, lastX = 0, lastY = 0, pinch = 0, moved = 0;
    const down = (x, y) => { dragging = true; lastX = x; lastY = y; moved = 0; };
    const move = (x, y) => {
      if (!dragging) return;
      moved += Math.abs(x - lastX) + Math.abs(y - lastY);
      orbit.yaw -= (x - lastX) * 0.35;
      orbit.pitch += (y - lastY) * 0.35;
      orbit.pitch = Math.max(-8, Math.min(78, orbit.pitch));
      lastX = x; lastY = y;
      applyOrbit();
    };
    const up = () => { dragging = false; };
    const zoom = (f) => {
      orbit.radius = Math.max(orbit.min, Math.min(orbit.max, orbit.radius * f));
      applyOrbit();
    };
    // A drag is not a tap. Without this, turning the scene also counts as
    // tapping the character underneath the finger.
    LL.wasDrag = () => moved > 8;

    canvas.addEventListener('mousedown', (e) => down(e.clientX, e.clientY));
    window.addEventListener('mousemove', (e) => move(e.clientX, e.clientY));
    window.addEventListener('mouseup', up);
    canvas.addEventListener('wheel', (e) => {
      e.preventDefault(); zoom(1 + Math.sign(e.deltaY) * 0.1);
    }, { passive: false });
    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) down(e.touches[0].clientX, e.touches[0].clientY);
      else if (e.touches.length === 2) pinch = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY);
    }, { passive: true });
    canvas.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1) move(e.touches[0].clientX, e.touches[0].clientY);
      else if (e.touches.length === 2 && pinch) {
        const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX,
                             e.touches[0].clientY - e.touches[1].clientY);
        zoom(pinch / d); pinch = d;
      }
    }, { passive: true });
    canvas.addEventListener('touchend', () => { up(); pinch = 0; }, { passive: true });
  }

  function sceneReady(sceneEl) {
    return new Promise((res) => {
      sceneEl.hasLoaded ? res() : sceneEl.addEventListener('loaded', () => res(), { once: true });
    });
  }

  /* --- the two entry points ------------------------------------------------ */
  LL.install = function (opts) {
    const sceneEl = document.querySelector('a-scene');
    const startEl = document.getElementById('start');
    const startBtn = document.getElementById('startBtn');
    const screenBtn = document.getElementById('screenBtn');
    const errEl = document.getElementById('err');
    const hintEl = document.getElementById('hint');
    const chapterEl = document.getElementById('chapter');
    const anchorEl = document.getElementById('anchor');
    const rigEl = document.getElementById('rig');

    async function startAR() {
      await sceneReady(sceneEl);
      sceneEl.setAttribute('mindar-image',
        'imageTargetSrc: ' + opts.targets + '; autoStart: false; filterMinCF: 0.00005; ' +
        'filterBeta: 5; missTolerance: 5; warmupTolerance: 5;');
      await sceneReady(sceneEl);
      if (anchorEl) anchorEl.setAttribute('mindar-image-target', 'targetIndex: 0');

      const sys = sceneEl.systems['mindar-image-system'];
      if (!sys) throw new Error('MindAR not ready — reload the page.');
      // Retry past the known 'this.ui.showLoading' race so one tap always works.
      let lastErr;
      for (let i = 0; i < 30; i++) {
        try { await sys.start(); return; }
        catch (e) {
          lastErr = e;
          if (/showLoading|ui|undefined/i.test(String((e && e.message) || e))) {
            await new Promise((r) => setTimeout(r, 200)); continue;
          }
          throw e;
        }
      }
      throw lastErr || new Error('MindAR did not become ready');
    }

    async function startScreen() {
      LL.screenMode = true;
      await sceneReady(sceneEl);

      // The anchor never gets the mindar component, so it stays a plain visible
      // holder. Undo the "lie flat on the card" rotation so the scene stands up.
      if (anchorEl) anchorEl.object3D.visible = true;
      if (rigEl) rigEl.setAttribute('rotation', '0 0 0');
      sceneEl.setAttribute('background', 'color: #140f0c');
      bindOrbitInput(sceneEl);
      applyOrbit();

      if (startEl) startEl.style.display = 'none';
      if (chapterEl) chapterEl.style.display = 'block';
      if (hintEl) hintEl.style.display = 'none';

      if (opts.reveal) opts.reveal();      // no card to find

      // Keep re-framing: the rig grows 0.05 -> 4 over 1.4s and the model may
      // still be downloading.
      let framed = false;
      const settle = setInterval(() => { if (LL.frameOn(rigEl)) framed = true; }, 300);
      setTimeout(() => {
        clearInterval(settle);
        if (!framed && errEl) {
          errEl.textContent = 'The scene did not load — check the console.';
          if (startEl) startEl.style.display = 'flex';
        }
      }, 6000);
    }

    if (startBtn) {
      startBtn.addEventListener('click', async () => {
        const label = startBtn.textContent;
        startBtn.textContent = 'Starting…';
        if (errEl) errEl.textContent = '';
        await LL.unlockAudio();
        try {
          await startAR();
          if (startEl) startEl.style.display = 'none';
          if (hintEl) hintEl.style.display = 'block';
          if (chapterEl) chapterEl.style.display = 'block';
        } catch (err) {
          startBtn.textContent = label;
          if (errEl) errEl.textContent = 'Could not start the camera: ' +
            ((err && err.message) || err) + ' — you can still play on screen.';
        }
      });
    }

    if (screenBtn) {
      screenBtn.addEventListener('click', async () => {
        if (errEl) errEl.textContent = '';
        await LL.unlockAudio();
        try { await startScreen(); }
        catch (err) {
          if (errEl) errEl.textContent = 'Could not start: ' + ((err && err.message) || err);
        }
      });
    }
  };
})();
