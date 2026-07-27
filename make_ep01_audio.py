#!/usr/bin/env python3
"""Give Episode 1 the music that was rendered into the prologue video.

ep/01/intro.mp4 was exported without an audio track, so the fox video played
silent. The music exists in ep/01/prologue.mp4, where it was rendered together
with the picture.

This does two things:

  1. Muxes the prologue's audio onto intro.mp4, video stream copied untouched.
     Muxing rather than playing a separate file keeps the music in the exact
     sync it was rendered in.

  2. Builds ep/01/music.mp3 as a seamless loop of the same cue, so when the
     video ends the bed simply carries on instead of switching to a different
     theme.

The loop is made by crossfading the clip's tail onto its own head, which makes
the end flow into the beginning, then repeating that unit. Level is left exactly
as rendered so there is no jump in volume when the video hands over to the loop.

Usage:
    .venv/bin/python make_ep01_audio.py      (needs numpy + ffmpeg)
"""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ep" / "01" / "prologue.mp4"
INTRO = ROOT / "ep" / "01" / "intro.mp4"
OUT_MP3 = ROOT / "ep" / "01" / "music.mp3"

SR = 44100
CROSSFADE = 0.8      # seconds of tail folded back onto the head
REPEATS = 4          # a longer file reaches its own loop point less often


def decode(path: Path) -> np.ndarray:
    """Stereo float samples at SR."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR),
         "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def seamless_loop(audio: np.ndarray) -> np.ndarray:
    """Fold the tail onto the head so the end runs into the beginning."""
    fade = int(CROSSFADE * SR)
    if len(audio) <= fade * 2:
        return audio
    body = audio[:len(audio) - fade].copy()
    tail = audio[len(audio) - fade:]
    t = np.linspace(0.0, 1.0, fade)[:, None]
    # Equal-power, so the crossfade does not dip in the middle.
    body[:fade] = tail * np.cos(t * np.pi / 2) + body[:fade] * np.sin(t * np.pi / 2)
    return body


def mux_audio_onto_intro() -> None:
    """Attach the prologue's audio to intro.mp4 without touching its video."""
    temp = INTRO.with_suffix(".muxed.mp4")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-i", str(INTRO),          # video (and whatever else) from the intro
         "-i", str(SOURCE),         # audio from the prologue render
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy",            # no re-encode: quality and size unchanged
         "-c:a", "aac", "-b:a", "128k",
         "-shortest",
         str(temp)],
        check=True,
    )
    shutil.move(str(temp), str(INTRO))


def probe(path: Path) -> str:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name",
         "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    return ", ".join(out)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing {SOURCE}")

    audio = decode(SOURCE)
    natural_rms = float(np.sqrt((audio ** 2).mean()))

    loop = seamless_loop(audio)
    stacked = np.tile(loop, (REPEATS, 1))

    temp_wav = OUT_MP3.with_name("_ep01_tmp.wav")
    with wave.open(str(temp_wav), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes((np.clip(stacked, -1, 1) * 32767).astype("<i2").tobytes())
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(temp_wav),
         "-codec:a", "libmp3lame", "-b:a", "96k", str(OUT_MP3)],
        check=True,
    )
    temp_wav.unlink()

    mux_audio_onto_intro()

    print(f"source      {SOURCE.relative_to(ROOT)}  {len(audio) / SR:.2f}s  "
          f"{natural_rms:.4f} RMS (level left as rendered)")
    print(f"loop unit   {len(loop) / SR:.2f}s seamless "
          f"({CROSSFADE:.1f}s tail folded onto the head)")
    print(f"wrote       {OUT_MP3.relative_to(ROOT)}  "
          f"{OUT_MP3.stat().st_size / 1024:.0f} KB  {len(stacked) / SR:.1f}s")
    print(f"wrote       {INTRO.relative_to(ROOT)}  -> {probe(INTRO)}")


if __name__ == "__main__":
    main()
