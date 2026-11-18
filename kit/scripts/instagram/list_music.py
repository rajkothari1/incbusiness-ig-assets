"""Music for the list reel: 6 styles, synthesised fresh for every reel (nothing downloaded, no copyright).

music(total, cuts, seed) -> (music, sfx, info). The seed picks the style (seed % 6) and, inside it, the key,
tempo, chords and pattern, so two reels in a row never share a style and no two reels sound the same.
Styles: tech, lofi, pop, house, corporate, cinematic.
"""
import numpy as np

SR = 44100
STYLES = ['tech', 'lofi', 'pop', 'house', 'corporate', 'cinematic']


def music(total, cuts, seed):
    rng = np.random.default_rng(seed)
    style = STYLES[seed % len(STYLES)]
    n = int(total * SR)
    t_ = lambda L: np.arange(int(L * SR)) / SR

    def env(L, a=.004, d=.2):
        x = t_(L); return np.minimum(x / a, 1) * np.exp(-x / d)

    def add(buf, sig, at, g=1.0):
        i = int(at * SR); j = min(n, i + len(sig))
        if 0 <= i < n: buf[i:j] += (sig[:j - i] * g).astype(np.float32)

    def tone(f, L, harm=4, roll=1.6):
        x = t_(L); return sum(np.sin(2 * np.pi * f * k * x) / k ** roll for k in range(1, harm + 1))

    def saw(f, L, det=0.0):
        x = t_(L); s = sum(np.sin(2 * np.pi * f * k * x) / k for k in range(1, 10))
        if det: s += sum(np.sin(2 * np.pi * f * (1 + det) * k * x) / k for k in range(1, 10))
        return s * .5

    def lowpass(sig, fc):
        F = np.fft.rfft(sig); f = np.fft.rfftfreq(len(sig), 1 / SR)
        return np.fft.irfft(F / np.sqrt(1 + (f / fc) ** 4), len(sig))

    def kick(L=.3, f0=48, sweep=110, d=11):
        x = t_(L); return np.sin(2 * np.pi * (f0 + sweep * np.exp(-x * 30)) * x) * np.exp(-x * d)

    def noise(L, a=.001, d=.05):
        return rng.standard_normal(int(L * SR)) * env(L, a, d)

    def hat(L=.04, d=.01):
        return np.diff(noise(L, .001, d), prepend=0)

    def whoosh(L=.45):
        m = int(L * SR); x = np.linspace(0, 1, m)
        y = lowpass(rng.standard_normal(m), 2500) * np.sin(np.pi * x) ** 1.5 * (.3 + x)
        return y / (np.abs(y).max() + 1e-9)

    tr = 2 ** (int(rng.integers(-3, 3)) / 12)
    C = lambda *fs: tuple(f * tr for f in fs)
    m = np.zeros(n, np.float32)

    if style == 'tech':
        bpm = int(rng.choice([110, 115, 120])); b = 60 / bpm
        ch = [C(261.63, 329.63, 392.0, 493.88), C(220.0, 261.63, 329.63, 392.0), C(174.61, 220.0, 261.63, 329.63), C(196.0, 246.94, 293.66, 392.0)]
        pat = [[0, 2, 1, 3, 2, 1, 3, 2], [0, 1, 2, 3, 2, 3, 1, 2]][int(rng.integers(2))]
        k = 0
        while k * b / 2 < total - 1:
            at = .1 + k * b / 2; c = ch[(k // 8) % 4]
            add(m, tone(c[pat[k % 8]] * 2, .35) * env(.35, d=.12), at, .09)
            if k % 2 == 0 and at > .9: add(m, kick(.22), at, .5)
            if k % 2 == 1: add(m, hat(), at, .08)
            if k % 8 == 0: add(m, tone(c[0] / 2, b * 4, 3) * env(b * 4, a=.05, d=1.2), at, .1)
            k += 1

    elif style == 'lofi':
        bpm = int(rng.choice([78, 82, 86])); b = 60 / bpm
        ch = [C(146.83, 174.61, 220.0, 261.63, 329.63), C(196.0, 246.94, 293.66, 349.23, 440.0),
              C(130.81, 164.81, 196.0, 246.94, 293.66), C(220.0, 261.63, 329.63, 392.0, 493.88)]   # Dm9 G9 Cmaj9 Am9
        bar = 0
        while bar * b * 4 < total - 1:
            at = .05 + bar * b * 4; c = ch[bar % 4]
            for i, f in enumerate(c):   # soft electric piano, slightly strummed
                add(m, (tone(f, b * 4, 3, 2.2) + .3 * tone(f * 1.003, b * 4, 2)) * env(b * 4, a=.01, d=1.6), at + i * .025, .05)
            add(m, tone(c[0] / 2, b * 2, 2) * env(b * 2, d=.8), at, .16)
            add(m, tone(c[0] / 2, b * 2, 2) * env(b * 2, d=.8), at + b * 2.5, .12)
            for q in range(4):
                bt = at + q * b
                if q in (0, 2): add(m, kick(.3, 45, 70, 9), bt, .45)
                if q in (1, 3): add(m, lowpass(noise(.25, .002, .07), 3000), bt, .3)
                for e in (0, .58):   # swung hats
                    add(m, hat(.05, .015), bt + e * b, .05)
            bar += 1
        m = lowpass(m, 5200).astype(np.float32)
        crackle = np.zeros(n); idx = rng.integers(0, n, int(total * 25)); crackle[idx] = rng.standard_normal(len(idx))
        m += (lowpass(crackle, 4000) * .06).astype(np.float32)

    elif style == 'pop':
        bpm = int(rng.choice([118, 122, 126])); b = 60 / bpm
        ch = [C(261.63, 329.63, 392.0), C(196.0, 246.94, 293.66), C(220.0, 261.63, 329.63), C(174.61, 220.0, 261.63)]   # C G Am F
        k = 0
        while k * b / 4 < total - 1:
            at = .1 + k * b / 4; c = ch[(k // 16) % 4]
            if k % 4 == 0: add(m, kick(), at, .55)
            if k % 8 == 4: add(m, lowpass(noise(.18, .001, .05), 6000), at, .3)    # clap
            if k % 2 == 1: add(m, hat(), at, .07)
            add(m, saw(c[[0, 1, 2, 1][k % 4]] * 2, .15) * env(.15, d=.05), at, .035)  # 16th pluck arp
            if k % 2 == 0: add(m, tone(c[0] / 2, b / 2, 3) * env(b / 2, d=.15), at, .2)   # bass eighths
            if k % 16 == 0: add(m, lowpass(sum(saw(f, b * 4, .004) for f in c), 2500) * env(b * 4, a=.1, d=2), at, .04)
            k += 1

    elif style == 'house':
        bpm = int(rng.choice([120, 123, 125])); b = 60 / bpm
        ch = [C(220.0, 261.63, 329.63, 392.0), C(174.61, 220.0, 261.63, 329.63), C(196.0, 246.94, 293.66, 349.23), C(164.81, 196.0, 246.94, 293.66)]
        k = 0
        while k * b / 2 < total - 1:
            at = .1 + k * b / 2; c = ch[(k // 8) % 4]
            if k % 2 == 0: add(m, kick(.28, 50, 120, 10), at, .6)
            else:
                add(m, lowpass(noise(.12, .001, .04), 9000), at, .08)               # offbeat open hat
                add(m, lowpass(sum(saw(f, .2) for f in c), 1800) * env(.2, d=.08), at, .07)   # chord stab
                add(m, tone(c[0] / 2, .2, 3) * env(.2, d=.1), at, .22)               # offbeat bass
            if k % 4 == 2: add(m, lowpass(noise(.15, .001, .05), 5000), at, .2)
            k += 1

    elif style == 'corporate':
        bpm = int(rng.choice([100, 104, 108])); b = 60 / bpm
        ch = [C(261.63, 329.63, 392.0), C(220.0, 261.63, 329.63), C(174.61, 220.0, 261.63), C(196.0, 246.94, 293.66)]   # C Am F G
        k = 0
        while k * b / 2 < total - 1:
            at = .1 + k * b / 2; c = ch[(k // 8) % 4]
            add(m, tone(c[[0, 1, 2, 1, 2, 0, 1, 2][k % 8]] * 2, .6, 5, 1.3) * env(.6, d=.3), at, .07)   # piano-ish eighths
            if k % 8 == 0:
                add(m, lowpass(sum(saw(f, b * 4, .003) for f in c), 1500) * env(b * 4, a=.4, d=3), at, .05)
                add(m, tone(c[0] / 2, b * 4, 3) * env(b * 4, a=.02, d=1.5), at, .15)
            if k % 4 == 0 and at > 1.5: add(m, kick(.25, 50, 80, 12), at, .4)
            if k % 4 == 2 and at > 1.5: add(m, lowpass(noise(.15, .001, .04), 7000), at, .18)
            if k % 2 == 1 and at > 3: add(m, hat(), at, .05)
            k += 1

    else:   # cinematic
        bpm = int(rng.choice([86, 90, 94])); b = 60 / bpm
        ch = [C(110.0, 130.81, 164.81), C(87.31, 110.0, 130.81), C(130.81, 164.81, 196.0), C(98.0, 123.47, 146.83)]   # Am F C G, low
        bar = 0
        while bar * b * 4 < total - 1:
            at = .05 + bar * b * 4; c = ch[bar % 4]
            pad = sum(saw(f, b * 4 + .5, .006) + saw(f * 2, b * 4 + .5, .004) * .5 for f in c)
            add(m, lowpass(pad, 900 + bar * 250) * env(b * 4 + .5, a=.6, d=4), at, .035)
            for q in range(4):
                add(m, kick(.5, 70, 60, 6), at + q * b, .35 if q % 2 == 0 else .2)   # toms
                for e in (0, .5): add(m, tone(c[2] * 4, .12, 2) * env(.12, d=.04), at + (q + e) * b, .03)   # ostinato
            bar += 1
        for c_ in cuts: add(m, kick(1.2, 38, 50, 3), c_, .5)   # low boom on each change

    m = m * np.interp(np.arange(n) / SR, [0, .3, total - 1.0, total], [0, 1, 1, 0]).astype(np.float32)
    sfx = np.zeros(n, np.float32)
    for c_ in cuts: add(sfx, whoosh(), c_ - .3, .8)
    return m, sfx, {'style': style, 'bpm': bpm}
