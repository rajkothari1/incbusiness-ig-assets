"""Synthesizes a short royalty-free instrumental bed for the reels (no samples, no licensing).

Usage: python3 generator/make-music.py <out.wav> [seconds]

Chill corporate feel: C - Am - F - G pad chords, a plucked arpeggio, soft kick and hi-hat,
at 96 BPM, with a fade in and fade out.
"""
import sys
import wave

import numpy as np

out = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
SR = 44100
BPM = 96
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
