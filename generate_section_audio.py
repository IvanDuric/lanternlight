#!/usr/bin/env python3
"""Generate natural Emma narration for the marked Lanternlight sections."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
VOICE = "en-US-EmmaMultilingualNeural"
WORK = ROOT / ".narration_parts"


@dataclass(frozen=True)
class Beat:
    start: float
    text: str
    rate: str = "-7%"
    pitch: str = "-2Hz"


@dataclass(frozen=True)
class Section:
    name: str
    output: Path
    minimum_duration: float
    beats: tuple[Beat, ...]


SECTIONS = (
    Section(
        "prologue",
        ROOT / "prologue.mp3",
        20.0,
        (
            Beat(0, "Long ago... the world had two layers.", "-10%", "-4Hz"),
            Beat(4, "The one you know... and the Underglow.", "-8%", "+1Hz"),
            Beat(8, "A hidden world of small, forgotten wonders.", "-8%", "+1Hz"),
            Beat(12, "But its lanterns went dark...", "-12%", "-5Hz"),
            Beat(15, "And it began to fade.", "-12%", "-6Hz"),
            Beat(18, "Now... only you can bring the light back.", "-8%", "+1Hz"),
        ),
    ),
    Section(
        "episode_02_momo",
        ROOT / "ep" / "02" / "narration.mp3",
        18.0,
        (
            Beat(0, "This is Momo...", "-12%", "-1Hz"),
            Beat(2, "The little bear who swallows everyone's worries,", "-5%", "-1Hz"),
            Beat(6, "so no one else has to.", "-10%", "-2Hz"),
            Beat(9, "But nobody ever carries Momo's...", "-10%", "-5Hz"),
            Beat(13, "Give it a gentle tap...", "-9%", "+1Hz"),
            Beat(15, "and help it breathe them out.", "-13%", "-2Hz"),
        ),
    ),
    Section(
        "episode_03_tuck_and_tally",
        ROOT / "ep" / "03" / "narration.mp3",
        18.0,
        (
            Beat(0, "Meet Tuck and Tally,", "-5%", "+2Hz"),
            Beat(3, "the ink otters who know every bend of the river.", "-3%", "+2Hz"),
            Beat(8, "But their map is torn in two...", "-7%", "+1Hz"),
            Beat(11, "and neither one will share.", "-8%", "-1Hz"),
            Beat(14, "Tap them...", "-10%", "+2Hz"),
            Beat(16, "and help them put the pieces together.", "-5%", "+1Hz"),
        ),
    ),
    Section(
        "episode_04_silva",
        ROOT / "ep" / "04" / "narration.mp3",
        22.0,
        (
            Beat(0, "This is Silva,", "-12%", "-3Hz"),
            Beat(2, "keeper of the Almanac...", "-11%", "-1Hz"),
            Beat(5, "the book of everything we're trying not to forget.", "-6%", "-2Hz"),
            Beat(10, "But its pages are going blank...", "-10%", "-5Hz"),
            Beat(13, "The Hush doesn't roar... it erases. Quietly.", "-8%", "-6Hz"),
            Beat(18, "Tap Silva...", "-11%", "+1Hz"),
            Beat(20, "and help her remember.", "-10%", "+2Hz"),
        ),
    ),
    Section(
        "episode_05_bram",
        ROOT / "ep" / "05" / "narration.mp3",
        20.0,
        (
            Beat(0, "And here is Bram,", "-7%", "-1Hz"),
            Beat(2, "who forges the Sparkstones that carry the light.", "-4%", "+1Hz"),
            Beat(7, "But his fire has burned down to a single ember...", "-7%", "-5Hz"),
            Beat(12, "You can't hurry a light into being...", "-11%", "-3Hz"),
            Beat(16, "so give Bram a tap,", "-7%", "+1Hz"),
            Beat(18, "and help the forge roar back to life.", "-3%", "+3Hz"),
        ),
    ),
)


def duration(ffmpeg: str, path: Path) -> float:
    result = subprocess.run(
        [ffmpeg, "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


async def synthesize() -> None:
    WORK.mkdir(exist_ok=True)
    for section in SECTIONS:
        folder = WORK / section.name
        folder.mkdir(exist_ok=True)
        for index, beat in enumerate(section.beats, 1):
            await edge_tts.Communicate(
                beat.text,
                VOICE,
                rate=beat.rate,
                pitch=beat.pitch,
                volume="-2%",
            ).save(str(folder / f"{index:02d}.mp3"))


def tempo_filter(speed: float) -> str:
    return f"atempo={speed:.6f}" if speed > 1.001 else "anull"


def assemble(section: Section, ffmpeg: str) -> dict:
    section.output.parent.mkdir(parents=True, exist_ok=True)
    parts = [WORK / section.name / f"{i:02d}.mp3" for i in range(1, len(section.beats) + 1)]
    raw = [duration(ffmpeg, part) for part in parts]
    filters: list[str] = []
    placed: list[float] = []

    for i, beat in enumerate(section.beats):
        # Preserve the authored cue points. Only accelerate a line when it would
        # run into the next one; otherwise retain Emma's natural cadence.
        if i + 1 < len(section.beats):
            room = section.beats[i + 1].start - beat.start - 0.12
            speed = max(1.0, raw[i] / room)
        else:
            speed = 1.0
        placed_duration = raw[i] / speed
        placed.append(placed_duration)
        delay = round(beat.start * 1000)
        filters.append(
            f"[{i}:a]{tempo_filter(speed)},adelay={delay}|{delay},volume=1.0[a{i}]"
        )

    final_duration = max(
        section.minimum_duration,
        section.beats[-1].start + placed[-1] + 0.35,
    )
    filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{final_duration:.3f}[bed]")
    labels = "".join(f"[a{i}]" for i in range(len(parts))) + "[bed]"
    filters.append(
        f"{labels}amix=inputs={len(parts) + 1}:duration=longest:normalize=0,"
        f"atrim=0:{final_duration:.3f},alimiter=limit=0.93[out]"
    )

    cmd = [ffmpeg, "-y"]
    for part in parts:
        cmd.extend(["-i", str(part)])
    cmd.extend(
        [
            "-filter_complex", ";".join(filters),
            "-map", "[out]", "-ar", "48000", "-ac", "2",
            "-codec:a", "libmp3lame", "-b:a", "192k", str(section.output),
        ]
    )
    subprocess.run(cmd, check=True, capture_output=True)
    return {
        "section": section.name,
        "output": str(section.output),
        "duration": round(duration(ffmpeg, section.output), 2),
        "cues": [beat.start for beat in section.beats],
    }


def main() -> None:
    expected_parts = [
        WORK / section.name / f"{i:02d}.mp3"
        for section in SECTIONS
        for i in range(1, len(section.beats) + 1)
    ]
    if not all(part.is_file() and part.stat().st_size > 0 for part in expected_parts):
        asyncio.run(synthesize())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    report = [assemble(section, ffmpeg) for section in SECTIONS]
    print(json.dumps({"voice": VOICE, "files": report}, indent=2))


if __name__ == "__main__":
    main()
