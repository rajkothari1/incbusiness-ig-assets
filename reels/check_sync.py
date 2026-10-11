"""Find where our voice line starts inside a lip-synced clip, and check it really is our line.

Usage: python3 reels/check_sync.py <clip.mp4> <voice.mp3> [start end]
MiniMax H3 bakes the reference audio into its output but may pad silence before it (we have
seen 0 s and 1.1 s), so the lips only match if we skip that lead-in. Comparing loudness
envelopes gives the lead-in; a weak match means the clip is not speaking our line at all.
build_reel.py imports find_offset() and skips the lead-in automatically.
"""
import subprocess
import sys

import numpy as np

RATE = 8000
HOP = 80  # 10 ms
MAX_LEAD = 3.0  # seconds of lead-in we search for
MIN_MATCH = 0.6


def envelope(path, start=None, end=None):
    cmd = ["ffmpeg", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}", "-to", f"{end:.3f}"]
    cmd += ["-i", str(path), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"]
    x = np.abs(np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(float))
    x = x[: len(x) // HOP * HOP].reshape(-1, HOP).mean(1)
    return (x - x.mean()) / (x.std() + 1e-9)


def find_offset(clip, voice, start=None, end=None):
    """Return (lead_in_seconds, match) where our line begins inside the clip's own audio."""
    a, b = envelope(clip), envelope(voice, start, end)
    if not len(a):
        return None, 0.0
    best_lag, best = 0, -1.0
    steps = int(MAX_LEAD * RATE / HOP)
    for lag in range(-steps // 6, steps + 1):  # mostly a lead-in, allow a little early start
        x = a[lag:] if lag >= 0 else a
        y = b if lag >= 0 else b[-lag:]
        n = min(len(x), len(y))
        if n < 100:
            continue
        c = float(np.corrcoef(x[:n], y[:n])[0, 1])
        if c > best:
            best_lag, best = lag, c
    return best_lag * HOP / RATE, best


def main():
    clip, voice = sys.argv[1], sys.argv[2]
    span = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (None, None)
    lead, match = find_offset(clip, voice, *span)
    if lead is None:
        sys.exit(f"{clip}: no audio track, cannot verify sync")
    ok = match >= MIN_MATCH
    print(f"{clip}: our line starts at {lead:+.2f}s in the clip, match {match:.2f} -> {'OK' if ok else 'MISMATCH'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
