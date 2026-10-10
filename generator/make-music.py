"""Synthesizes a short royalty-free instrumental bed for the reels (no samples, no licensing).

Usage: python3 generator/make-music.py <out.wav> [seconds] [style]
  style: "news" (default) or "chill"

news:  TV-news bed at 120 BPM in D minor with a ticking pulse, stabs and a boom on each bar.
chill: C - Am - F - G pads, plucked arpeggio, soft kick and hi-hat at 96 BPM.
Both fade in and out.
"""
import sys
import wave

import numpy as np

out = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
STYLE = sys.argv[3] if len(sys.argv) > 3 else 'news'
SR = 44100
BPM = 96  # chill style tempo
beat = 60 / BPM
t_all = np.arange(int(SR * DUR)) / SR
mix = np.zeros_like(t_all)

def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)

def add(sig, start):
    i = int(start * SR)
    if i >= len(mix):
        return
    n = min(len(sig), len(mix) - i)
    mix[i:i + n] += sig[:n]

def news():
    """TV-news bed: 120 BPM, D minor (Dm-Bb-F-C), 16th-note ticking pulse,
    staccato synth stabs, low boom on each bar, opening riser."""
    bpm = 120
    b = 60 / bpm
    bar_len = 4 * b
    prog = [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]]
    for bi in range(int(np.ceil(DUR / bar_len))):
        ch = prog[bi % 4]
        start = bi * bar_len
        t = np.arange(int(SR * bar_len)) / SR
        env = np.minimum(1, t / 0.05) * np.minimum(1, (bar_len - t) / 0.2)
        pad = sum(np.sin(2 * np.pi * note(m) * t) for m in ch)
        add(0.05 * env * pad, start)
        # low boom on the downbeat
        tt = np.arange(int(SR * 0.9)) / SR
        f = 70 * np.exp(-tt * 6) + 38
        add(0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4), start)
        # 16th-note staccato pulse on the root (saw-ish via harmonics)
        step = b / 4
        for k in range(16):
            tt = np.arange(int(SR * step)) / SR
            fr = note(ch[0] + 12)
            saw = sum(np.sin(2 * np.pi * fr * h * tt) / h for h in range(1, 6))
            acc = 1.0 if k % 4 == 0 else 0.55
            add(0.05 * acc * saw * np.exp(-tt * 28), start + k * step)
        # ticking clock: bright click on every 8th
        for k in range(8):
            n = np.random.default_rng(bi * 8 + k).standard_normal(int(SR * 0.02))
            n = np.diff(n, prepend=0) * np.exp(-np.arange(len(n)) / SR * 220)
            add((0.06 if k % 2 == 0 else 0.035) * n, start + k * b / 2)
        # stab on beat 3
        tt = np.arange(int(SR * 0.18)) / SR
        stab = sum(np.sin(2 * np.pi * note(m + 12) * tt) + 0.4 * np.sin(2 * np.pi * 2 * note(m + 12) * tt) for m in ch)
        add(0.05 * stab * np.exp(-tt * 14), start + 2 * b)
    # opening riser
    tt = np.arange(int(SR * 0.6)) / SR
    noise = np.random.default_rng(99).standard_normal(len(tt))
    add(0.08 * noise * (tt / 0.6) ** 2, 0)

if STYLE == 'news':
    news()

if STYLE == 'chill':
    # chords: C, Am, F, G (root, third, fifth, octave)
    chords = [[48, 52, 55, 60], [45, 48, 52, 57], [41, 45, 48, 53], [43, 47, 50, 55]]
    bar = 4 * beat
    chord_len = DUR / 4 if DUR < 4 * bar else bar
    for ci in range(int(np.ceil(DUR / chord_len))):
        ch = chords[ci % 4]
        t = np.arange(int(SR * chord_len)) / SR
        env = np.minimum(1, t / 0.25) * np.minimum(1, (chord_len - t) / 0.3)
        pad = sum(np.sin(2 * np.pi * note(m) * t) + 0.3 * np.sin(2 * np.pi * 2 * note(m) * t) for m in ch)
        add(0.06 * env * pad, ci * chord_len)
        # bass
        add(0.12 * env * np.sin(2 * np.pi * note(ch[0] - 12) * t), ci * chord_len)
        # arpeggio pluck on eighth notes
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12]
        step = beat / 2
        for k in range(int(chord_len / step)):
            tt = np.arange(int(SR * step * 1.5)) / SR
            pl = np.sin(2 * np.pi * note(arp[k % len(arp)]) * tt) * np.exp(-tt * 9)
            add(0.07 * pl, ci * chord_len + k * step)

    # drums
    for b in range(int(DUR / beat) + 1):
        tt = np.arange(int(SR * 0.25)) / SR
        if b % 2 == 0:  # kick on 1 and 3
            f = 110 * np.exp(-tt * 18) + 45
            add(0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12), b * beat)
        hh = np.random.default_rng(b).standard_normal(int(SR * 0.05))
        hh = np.diff(hh, prepend=0) * np.exp(-np.arange(len(hh)) / SR * 70)
        add(0.03 * hh, b * beat + beat / 2)

fade = np.minimum(1, t_all / 0.4) * np.minimum(1, (DUR - t_all) / 0.8)
mix = mix * fade
mix = mix / (np.abs(mix).max() + 1e-9) * 0.8
stereo = np.stack([mix, mix], axis=1)
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
print('wrote', out)
