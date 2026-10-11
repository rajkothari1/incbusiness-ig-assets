"""Turn a day's script.json into voice.mp3 + segments.json (with exact per-line timings).

Usage: python3 reels/make_voice.py reels/2026-10-11 [--rate +15%]
Uses Microsoft Edge's free neural TTS (hi-IN-SwaraNeural). Each line is synthesised on its
own so every card switches exactly when its line starts.
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import certifi

# The sandbox proxy re-signs TLS; point edge-tts at its CA bundle when present.
_CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(_CA):
    certifi.where = lambda: _CA
import edge_tts  # noqa: E402

VOICE = "hi-IN-SwaraNeural"
GAP = 0.18  # silence between lines, seconds


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


async def synth(text, out, rate):
    await edge_tts.Communicate(text, VOICE, rate=rate).save(str(out))


def main():
    day = Path(sys.argv[1]).resolve()
    rate = sys.argv[sys.argv.index("--rate") + 1] if "--rate" in sys.argv else "+15%"
    script = json.loads((day / "script.json").read_text())
    build = day / "build"
    build.mkdir(exist_ok=True)
    lines = [script["intro"]] + script["items"] + [script["outro"]]
    parts, t = [], 0.0
    for i, line in enumerate(lines):
        mp3 = build / f"line_{i:02d}.mp3"
        asyncio.run(synth(line["say"], mp3, rate))
        wav = build / f"line_{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-af",
                        f"apad=pad_dur={GAP}", "-ar", "44100", "-ac", "1", str(wav)], check=True)
        d = duration(wav)
        line["start"], line["end"] = round(t, 3), round(t + d, 3)
        t += d
        parts.append(wav)
    concat = build / "concat.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(day / "voice.mp3")], check=True)
    script["outro"]["end"] = round(t + 1.0, 3)
    (day / "segments.json").write_text(json.dumps(script, ensure_ascii=False, indent=2))
    print(f"voice.mp3: {t:.1f}s")


if __name__ == "__main__":
    main()
