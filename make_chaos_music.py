#!/usr/bin/env python3
"""Generate ep/04/chaos.mp3 — the runaway-press cue.

The calm loop in ep/04/music.mp3 analyses as E minor at roughly 130 BPM. This
cue stays in E minor so the crossfade is not a key change, but pushes to 150 BPM
and swaps the gentle bed for clockwork: ticking sixteenths, a driving bass pulse,
a manic arpeggio and a metal clank on every bar.

It is meant to read as a comic machine losing control, not as danger — this is a
children's picture book. Nothing dissonant, nothing sudden and loud, and the
whole thing sits low enough to talk over.

Twelve bars (19.2s) so it rarely reaches its loop point during a play session.
The page loops it through WebAudio rather than <audio loop>, because MP3 encoder
padding makes an <audio> loop audibly gap.

Usage:
    .venv/bin/python make_chaos_music.py        (only needs numpy + ffmpeg)
"""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT_MP3 = ROOT / "ep" / "04" / "chaos.mp3"
OUT_WAV = ROOT / "ep" / "04" / "_chaos_tmp.wav"

SR = 44100
BPM = 150.0
BEAT = 60.0 / BPM          # 0.40 s
BAR = BEAT * 4             # 1.60 s
BARS = 12
LENGTH = BAR * BARS        # 19.2 s

# E natural minor, the key of the calm loop.
NOTE = {
    "E1": 41.20, "E2": 82.41, "G2": 98.00, "B2": 123.47,
    "D3": 146.83, "E3": 164.81, "F#3": 185.00, "G3": 196.00,
    "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63,
}


def buffer() -> np.ndarray:
    return np.zeros(int(LENGTH * SR) + SR, dtype=np.float64)


def env(n: int, attack: float, decay: float) -> np.ndarray:
    a = max(1, int(attack * SR))
    d = max(1, n - a)
    return np.concatenate([
        np.linspace(0.0, 1.0, a),
        np.exp(-np.linspace(0.0, 1.0, d) * decay),
    ])[:n]


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """One-pole lowpass — enough to take the fizz off a saw."""
    a = np.exp(-2.0 * np.pi * cutoff / SR)
    out = np.empty_like(x)
    acc = 0.0
    for i, sample in enumerate(x):
        acc = (1.0 - a) * sample + a * acc
        out[i] = acc
    return out


def place(track: np.ndarray, at: float, block: np.ndarray, gain: float = 1.0) -> None:
    start = int(at * SR)
    end = min(len(track), start + len(block))
    if end > start:
        track[start:end] += block[:end - start] * gain


def saw(freq: float, dur: float, detune: float = 0.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    wave_ = 2.0 * ((t * freq) % 1.0) - 1.0
    if detune:
        wave_ += 2.0 * ((t * freq * (1 + detune)) % 1.0) - 1.0
        wave_ *= 0.5
    return wave_


def pluck(freq: float, dur: float, decay: float = 7.0) -> np.ndarray:
    """Bright square-ish pluck with a touch of second harmonic."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sign(np.sin(2 * np.pi * freq * t)) * 0.45
    tone += np.sin(2 * np.pi * freq * 2 * t) * 0.3
    tone += np.sin(2 * np.pi * freq * t) * 0.55
    return tone * env(n, 0.002, decay)


def tick(dur: float = 0.035, bright: float = 5200.0) -> np.ndarray:
    n = int(dur * SR)
    noise = np.random.default_rng(7).normal(0, 1, n)
    t = np.arange(n) / SR
    click = noise * np.exp(-t * 260.0)
    click += np.sin(2 * np.pi * bright * t) * np.exp(-t * 320.0) * 0.6
    return click


def clank(dur: float = 0.55) -> np.ndarray:
    """Struck metal: a few inharmonic partials, fast attack, long-ish ring."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for freq, amp, dec in ((523.0, 1.0, 9.0), (781.0, 0.7, 11.0),
                           (1197.0, 0.5, 13.0), (1613.0, 0.3, 16.0)):
        out += np.sin(2 * np.pi * freq * t) * np.exp(-t * dec) * amp
    rng = np.random.default_rng(11)
    out += rng.normal(0, 1, n) * np.exp(-t * 90.0) * 0.5
    return out / 2.4


def build() -> np.ndarray:
    left, right = buffer(), buffer()
    sixteenth = BEAT / 4

    # --- clockwork: sixteenth-note ticks, alternating across the stereo field.
    total_sixteenths = int(BARS * 16)
    for i in range(total_sixteenths):
        at = i * sixteenth
        bar = i // 16
        # Thins out in the turnaround bar so the loop point breathes.
        if bar == BARS - 1 and i % 16 >= 8:
            continue
        accent = 1.0 if i % 4 == 0 else 0.55
        block = tick(bright=5200 if i % 2 == 0 else 6400)
        place(left if i % 2 == 0 else right, at, block, 0.16 * accent)
        place(right if i % 2 == 0 else left, at, block, 0.07 * accent)

    # --- bass pulse: eighth notes on E, dropping to D and C for movement.
    bass_plan = ["E1", "E1", "E1", "E1", "D3", "D3", "E1", "E1",
                 "C4", "C4", "E1", "E1"]
    for bar in range(BARS):
        root = NOTE[bass_plan[bar % len(bass_plan)]]
        if root > 100:                      # keep everything in the same octave
            root /= 4.0
        for eighth in range(8):
            at = bar * BAR + eighth * (BEAT / 2)
            dur = BEAT / 2 * 0.9
            tone = lowpass(saw(root, dur, detune=0.008), 220.0)
            tone *= env(len(tone), 0.004, 5.0)
            gain = 0.5 if eighth % 2 == 0 else 0.32
            place(left, at, tone, gain)
            place(right, at, tone, gain)

    # --- manic arpeggio, entering at bar 4 and doubling from bar 8.
    arp = ["E3", "G3", "B3", "D4", "E4", "D4", "B3", "G3"]
    slip = ["F#3", "A3", "C4", "E4"]        # the machine mistiming itself
    for bar in range(BARS):
        if bar < 4:
            continue
        density = 8 if bar < 8 else 16
        step = BAR / density
        for i in range(density):
            at = bar * BAR + i * step
            # Every fourth bar the pattern stumbles onto the slip notes.
            source = slip if (bar % 4 == 3 and i % 4 == 3) else arp
            freq = NOTE[source[i % len(source)]]
            tone = pluck(freq, min(step * 1.6, 0.34), decay=8.0)
            gain = 0.2 if bar < 8 else 0.26
            pan = 0.5 + 0.32 * np.sin(i * 1.1)
            place(left, at, tone, gain * pan)
            place(right, at, tone, gain * (1.0 - pan))

    # --- clank on beat 1 of every bar; two in the turnaround.
    for bar in range(BARS):
        place(left, bar * BAR, clank(), 0.30)
        place(right, bar * BAR, clank(), 0.26)
    place(left, (BARS - 1) * BAR + BEAT * 2, clank(0.4), 0.24)
    place(right, (BARS - 1) * BAR + BEAT * 2, clank(0.4), 0.28)

    # Trim to exactly BARS bars. Everything above decays inside the loop, so the
    # seam lands on near-silence rather than a cut tail.
    n = int(LENGTH * SR)
    stereo = np.stack([left[:n], right[:n]], axis=1)

    peak = np.abs(stereo).max()
    stereo = stereo / peak * 0.72               # headroom: this plays under speech
    ramp = int(0.004 * SR)                      # 4 ms de-click at the seam
    stereo[:ramp] *= np.linspace(0, 1, ramp)[:, None]
    stereo[-ramp:] *= np.linspace(1, 0, ramp)[:, None]
    return stereo


def main() -> None:
    stereo = build()
    with wave.open(str(OUT_WAV), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes((stereo * 32767).astype("<i2").tobytes())

    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(OUT_WAV),
         "-codec:a", "libmp3lame", "-b:a", "96k", str(OUT_MP3)],
        check=True,
    )
    OUT_WAV.unlink()
    print(f"Wrote {OUT_MP3.relative_to(ROOT)}  "
          f"{OUT_MP3.stat().st_size / 1024:.0f} KB  "
          f"{LENGTH:.1f}s  {BARS} bars @ {BPM:.0f} BPM, E minor")


if __name__ == "__main__":
    main()
