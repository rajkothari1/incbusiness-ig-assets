# Synthesizes a royalty-free upbeat background track for the reels (120 BPM, Am-F-C-G).
# The track sits low under the voice and builds up towards the end card.
# Usage: python3 reels/music.py <out.wav> <duration_s> <build_start_s> <drop_s>
import sys
import wave
import numpy as np

SR = 44100
out, DUR, BUILD, DROP = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
BEAT = 0.5
n = int(DUR * SR)
mix = np.zeros(n)
rng = np.random.default_rng(7)

def place(sig, t, gain=1.0):
    i = int(t * SR)
    if i >= n:
        return
    j = min(n, i + len(sig))
    mix[i:j] += sig[: j - i] * gain

def env(length, attack, decay):
    t = np.arange(int(length * SR)) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)

def note(freq, length, attack, decay, harmonics=(1,), detune=0.0):
    t = np.arange(int(length * SR)) / SR
    s = sum(np.sin(2 * np.pi * freq * h * t * (1 + detune * k)) / h for k, h in enumerate(harmonics))
    return s * env(length, attack, decay)

def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)

kick_t = np.arange(int(0.35 * SR)) / SR
KICK = np.sin(2 * np.pi * (48 * kick_t + 90 * (1 - np.exp(-kick_t * 30)) / 30)) * np.exp(-kick_t * 9)
noise = rng.standard_normal(int(0.25 * SR))
HAT = np.diff(np.diff(noise, prepend=0), prepend=0)[: int(0.06 * SR)] * env(0.06, 0.001, 0.015) * 0.25
CLAP = np.diff(noise, prepend=0)[: int(0.2 * SR)] * env(0.2, 0.002, 0.05) * 0.5

# Am, F, C, G (root midi + triad)
CHORDS = [(57, [69, 72, 76]), (53, [65, 69, 72]), (48, [64, 67, 72]), (55, [62, 67, 71])]

bar = 0
t = 0.0
while t < DUR:
    root, triad = CHORDS[bar % 4]
    intro = t < 3.6
    # pad
    for m in triad:
        place(note(hz(m), 2.2, 0.3, 1.6, (1, 2, 3), 0.002), t, 0.07)
    for b in range(4):
        bt = t + b * BEAT
        if not intro:
            place(KICK, bt, 0.9)
            if b in (1, 3):
                place(CLAP, bt, 0.55)
        place(HAT, bt + BEAT / 2, 0.7)
        # bass on eighths
        for e in range(2):
            place(note(hz(root - 12), 0.24, 0.005, 0.12, (1, 2, 3, 4)), bt + e * BEAT / 2, 0.22 if not intro else 0.1)
        # arpeggio pluck on eighths
        for e in range(2):
            m = triad[(b * 2 + e) % 3] + 12
            place(note(hz(m), 0.2, 0.002, 0.08, (1, 2)), bt + e * BEAT / 2, 0.06)
    bar += 1
    t += 4 * BEAT

# volume curve: low bed, rising build, full at the drop
time = np.arange(n) / SR
gain = np.full(n, 0.45)
build = (time >= BUILD) & (time < DROP)
gain[build] = 0.45 + 0.4 * ((time[build] - BUILD) / (DROP - BUILD)) ** 2
gain[time >= DROP] = 1.0
gain *= np.minimum(1, (DUR - time) / 0.6)  # fade at the very end
mix *= gain
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.9

st = np.stack([mix, np.roll(mix, 220)], axis=1)  # tiny stereo widening
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())
