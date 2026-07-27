#!/usr/bin/env python3
"""Generate the Episode 01 narration and place each line on its caption cue."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ep" / "01" / "narration.mp3"
WORK = ROOT / "ep" / "01" / ".voiceover_parts"
VOICE = "en-US-EmmaMultilingualNeural"
TOTAL_SECONDS = 24.0

# Separate synthesis gives each beat its own emotional shape. Punctuation is
# intentionally performance-oriented; it does not change the displayed copy.
LINES = [
    (0.0, 6.0, "Every light starts the same way. Small... uncertain... yours.", "-8%", "-2Hz"),
    (6.0, 11.0, "This is Fenn. His lantern went out... a long time ago.", "-5%", "-4Hz"),
    (11.0, 16.0, "He's been waiting. Not for a hero... for you.", "-8%", "+1Hz"),
    (16.0, 20.0, "So, light it. Go on...", "-12%", "+1Hz"),
    (20.0, 24.0, "The whole world's been holding its breath for this.", "-2%", "-2Hz"),
]


def probe_duration(ffmpeg: str, path: Path) -> float:
    result = subprocess.run(
        [ffmpeg, "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration for {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def atempo_chain(speed: float) -> str:
    """Build a legal ffmpeg atempo chain for any positive speed."""
    values: list[float] = []
    while speed > 2.0:
        values.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        values.append(0.5)
        speed /= 0.5
    values.append(speed)
    return ",".join(f"atempo={value:.6f}" for value in values)


async def synthesize() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    for index, (_, _, text, rate, pitch) in enumerate(LINES):
        part = WORK / f"line_{index + 1}.mp3"
        communicate = edge_tts.Communicate(
            text,
            VOICE,
            rate=rate,
            pitch=pitch,
            volume="-2%",
        )
        await communicate.save(str(part))


def assemble() -> list[dict[str, float | str]]:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    parts = [WORK / f"line_{i + 1}.mp3" for i in range(len(LINES))]
    filters: list[str] = []
    report: list[dict[str, float | str]] = []

    for i, (start, end, text, _, _) in enumerate(LINES):
        raw_duration = probe_duration(ffmpeg, parts[i])
        available = end - start - 0.18
        speed = max(1.0, raw_duration / available)
        tempo = atempo_chain(speed)
        delay_ms = round(start * 1000)
        filters.append(
            f"[{i}:a]{tempo},adelay={delay_ms}|{delay_ms},volume=1.0[a{i}]"
        )
        report.append(
            {
                "start": start,
                "text": text,
                "raw_duration": round(raw_duration, 3),
                "placed_duration": round(raw_duration / speed, 3),
            }
        )

    labels = "".join(f"[a{i}]" for i in range(len(parts))) + "[bed]"
    filters.append(
        f"anullsrc=r=48000:cl=stereo,atrim=0:{TOTAL_SECONDS}[bed]"
    )
    filters.append(
        f"{labels}amix=inputs={len(parts) + 1}:duration=longest:normalize=0,"
        f"atrim=0:{TOTAL_SECONDS},alimiter=limit=0.93[out]"
    )

    cmd = [ffmpeg, "-y"]
    for part in parts:
        cmd.extend(["-i", str(part)])
    cmd.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(OUT),
        ]
    )
    subprocess.run(cmd, check=True, capture_output=True)
    report.append({"final_duration": round(probe_duration(ffmpeg, OUT), 3)})
    return report


def main() -> None:
    asyncio.run(synthesize())
    report = assemble()
    print(json.dumps({"voice": VOICE, "output": str(OUT), "timing": report}, indent=2))


if __name__ == "__main__":
    main()
