"""Instagram AI tools reel: 5 to 12 tools of one AI Resources post -> a 30-60 s (REEL_MAX_LEN, default 60) 1080x1920 MP4 + its cover.

    python3 ai_reel.py lines WORK   # prints the 7 voice lines for text-to-speech (intro, 5 tools, outro)
    python3 ai_reel.py build WORK   # voice/*.mp3 + src/*.jpg + reel.json -> out/reel.mp4, out/cover.jpg, out/check-*.jpg

WORK/reel.json:
 {"topic": "Video Editing", "badge": "All 5 have a free plan", "music_seed": 1,
  "end_title": "All 12 <span class=y>Video Editing</span> tools", "end_link": "incbusiness.in/ai-tools/video-editing",
  "cover": {"title": "...", "label": "AI Video Editing"},
  "intro_say": "...", "outro_say": "...",
  "tools": [{"img": "descript", "name": "Descript", "domain": "descript.com", "short": "Edit video by its transcript",
             "free": "100 one-time AI credits", "feats": ["Transcript editing", ...],
             "say": ["what it does (spoken)", "the free plan (spoken)"]}]}
Every fact on screen and in the voice comes from the tool's live page on the site. Shares the voice timing
with news_reel.py (same voice, speed-up and 0.5 s breath after each tool); the music has no glass break.
"""
import json, pathlib, shutil, subprocess, sys, urllib.request, wave
import numpy as np

import os
os.environ.setdefault('REEL_MAX_LEN', '60')
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from news_reel import ffmpeg, plan, syllables, SR, FPS, SCALE, V0, LOGO

KIT = pathlib.Path(__file__).parent


def lines(R):
    return [R['intro_say']] + [' '.join(t['say']) for t in R['tools']] + [R['outro_say']]


def music(total, cuts, pops, seed):
    """Light tech bed, fresh per seed: plucked arp, soft kick and hats, a riser and hit into tool 1, whooshes on cuts."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    def env(L, a=.004, d=.2):
        x = np.arange(int(L * SR)) / SR; return np.minimum(x / a, 1) * np.exp(-x / d)
    def add(buf, sig, at):
        i = int(at * SR); j = min(n, i + len(sig))
        if 0 <= i < n: buf[i:j] += sig[:j - i].astype(np.float32)
    def tone(f, L, harm=4):
        x = np.arange(int(L * SR)) / SR; return sum(np.sin(2 * np.pi * f * k * x) / k ** 1.6 for k in range(1, harm + 1))
    def whoosh(L=.5):
        m = int(L * SR); x = np.linspace(0, 1, m); a = .02 + .5 * x ** 2
        y = np.zeros(m); s = 0.; noise = rng.standard_normal(m)
        for i in range(m): s += a[i] * (noise[i] - s); y[i] = s
        y *= np.sin(np.pi * x) ** 1.5; return y / np.abs(y).max()

    tr = 2 ** (int(rng.integers(-3, 4)) / 12)
    progs = [[(261.63, 329.63, 392.0, 493.88), (220.0, 261.63, 329.63, 392.0), (174.61, 220.0, 261.63, 329.63), (196.0, 246.94, 293.66, 392.0)],   # Cmaj7 Am7 Fmaj7 G
             [(293.66, 349.23, 440.0, 523.25), (233.08, 293.66, 349.23, 440.0), (261.63, 329.63, 392.0, 466.16), (220.0, 277.18, 329.63, 392.0)]]  # Dm7 Bbmaj7 C7 A7
    chords = [tuple(f * tr for f in c) for c in progs[int(rng.integers(len(progs)))]]
    bpm = int(rng.choice([110, 115, 120])); beat = 60 / bpm
    pat = [[0, 2, 1, 3, 2, 1, 3, 2], [0, 1, 2, 3, 2, 3, 1, 2], [3, 2, 1, 0, 1, 2, 3, 1]][int(rng.integers(3))]

    m = np.zeros(n, np.float32)
    k, st = 0, .2
    while st + k * beat / 2 < total - 1.0:
        at = st + k * beat / 2; ch = chords[(k // 8) % 4]
        add(m, tone(ch[pat[k % 8]] * 2, .35) * env(.35, d=.12) * .09, at)                       # pluck arp, eighths
        if k % 2 == 0 and at > cuts[0] - .1:
            x = np.arange(int(.22 * SR)) / SR
            add(m, np.sin(2 * np.pi * (48 + 90 * np.exp(-x * 30)) * x) * np.exp(-x * 13) * .55, at)   # kick on beats once the tools start
        if k % 2 == 1:
            h = np.diff(rng.standard_normal(int(.025 * SR)) * env(.025, a=.001, d=.008), prepend=0)
            add(m, h * .08, at)
        if k % 8 == 0:
            add(m, tone(ch[0] / 2, beat * 4, 3) * env(beat * 4, a=.05, d=1.2) * .1, at)             # soft pad root per bar
        k += 1
    L = cuts[0] - .2                                                                                  # riser into tool 1
    x = np.arange(int(L * SR)) / SR
    add(m, np.sin(2 * np.pi * (200 * x + 300 * x ** 2 / L)) * (x / L) ** 2 * .05, .2)
    x = np.arange(int(.6 * SR)) / SR
    add(m, np.sin(2 * np.pi * (45 + 120 * np.exp(-x * 25)) * x) * np.exp(-x * 6) * .9, cuts[0])      # hit
    add(m, sum(tone(f, 1.6) for f in chords[0]) * env(1.6, d=.6) * .12, cuts[-1])                     # end-card chord

    sfx = np.zeros(n, np.float32)
    for c in cuts:
        add(sfx, whoosh(.45), c - .3)
    for p in pops:
        x = np.arange(int(.09 * SR)) / SR
        add(sfx, np.sin(2 * np.pi * (500 + 9000 * x) * x) * np.exp(-x * 45) * .3, p)
    return m, sfx, dict(bpm=bpm)


def build(work):
    R = json.loads((work / 'reel.json').read_text())
    T = R['tools']
    if not 5 <= len(T) <= 12:
        sys.exit('A reel needs 5 to 12 tools.')
    N = len(T)
    for t in T:
        if not (work / 'src' / f"{t['img']}.jpg").exists():
            sys.exit(f"Missing src/{t['img']}.jpg")
    out = work / 'out'; out.mkdir(exist_ok=True)
    (work / 'assets').mkdir(exist_ok=True)
    if not (work / 'assets' / 'logo-light.png').exists():
        req = urllib.request.Request(LOGO, headers={'User-Agent': 'Mozilla/5.0 (incbusiness reel kit)'})
        (work / 'assets' / 'logo-light.png').write_bytes(urllib.request.urlopen(req).read())
    shutil.copy(KIT / 'ai-reel.html', work / 'reel.html')
    shutil.copy(KIT / 'cover.html', work / 'cover.html')

    tempo, parts, starts, chunks, total, lens = plan(work, {'stories': T})
    S = [0.0] + [round(x, 3) for x in starts[1:]]
    END = round(total, 3)
    tools = []
    for t in T:
        a, b = syllables(t['say'][0]), syllables(t['say'][1])
        tools.append({k: t[k] for k in ('img', 'name', 'domain', 'short', 'free', 'feats')} | {'freeAt': round(a / (a + b), 3), 'featAt': .3})
    page = {k: R[k] for k in ('topic', 'badge', 'end_title', 'end_link')} | {'tools': tools, 'S': S, 'END': END,
            'intro_big': R.get('intro_big'), 'intro_for': R.get('intro_for')}

    pops = [1.25] + [S[i] + .3 for i in range(1, N + 1)] + [S[i] + tools[i - 1]['freeAt'] * (S[i + 1] - S[i] - .5) for i in range(1, N + 1)] + [S[N + 1] + .6]
    m, sfx, info = music(total, S[1:], pops, R.get('music_seed', 1))
    n = len(m); tt = np.arange(n) / SR
    voice = np.zeros(n, np.float32)
    for at, p in chunks:
        i = int(at * SR); voice[i:i + len(p)] = p[:max(0, n - i)]
    vend = chunks[-1][0] + len(chunks[-1][1]) / SR
    g = np.interp(tt, [0, V0 - .1, V0 + .15, vend, vend + .3, total - 1.0, total], [1, 1, .35, .35, .7, .7, 0])
    mix = m * g + sfx * .5 + voice * 1.25
    mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / np.abs(mix).max() * .93
    with wave.open(str(out / 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.repeat((mix * 32767).astype(np.int16)[:, None], 2, axis=1).tobytes())

    import imageio.v2 as imageio
    from playwright.sync_api import sync_playwright
    from PIL import Image
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(channel='chrome')
        except Exception:
            br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=SCALE)
        pg.goto((work / 'reel.html').as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(1500)
        pg.evaluate(f'setup({json.dumps(page)})')
        checks = {'intro': round(S[1] - .3, 2)} | {f'tool{i}': round(S[i] + (S[i + 1] - S[i]) * .85, 2) for i in range(1, N + 1)} | {'end': round(END - .8, 2)}
        for name, at in checks.items():
            pg.evaluate(f'render({at})'); pg.screenshot(path=str(out / f'check-{name}.png'))
            Image.open(out / f'check-{name}.png').convert('RGB').resize((1080, 1920), Image.LANCZOS).save(out / f'check-{name}.jpg', quality=90)
            (out / f'check-{name}.png').unlink()
        if '--checks' in sys.argv:
            br.close(); return
        w = imageio.get_writer(str(out / 'silent.mp4'), fps=FPS, codec='libx264', pixelformat='yuv420p', macro_block_size=8,
                               output_params=['-crf', '8', '-preset', 'veryfast'])
        for f in range(int(FPS * END)):
            pg.evaluate(f'render({f / FPS})')
            w.append_data(imageio.imread(pg.screenshot(type='png'), format='png')[:, :, :3])
        w.close()
        pg.goto((work / 'cover.html').as_uri()); pg.evaluate('document.fonts.ready')
        cov = {'shots': [[t['img'] + '.jpg', t['domain']] for t in T[:3]], 'title': R['cover']['title'], 'label': R['cover']['label']}
        pg.evaluate(f'setG({json.dumps(cov)})')
        pg.wait_for_timeout(1200); pg.screenshot(path=str(out / 'cover.png'))
        br.close()
    Image.open(out / 'cover.png').convert('RGB').save(out / 'cover.jpg', quality=95)
    subprocess.run([ffmpeg(), '-y', '-i', str(out / 'silent.mp4'), '-i', str(out / 'mix.wav'), '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-profile:v', 'high', '-level', '5.1',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(out / 'reel.mp4')], check=True, capture_output=True)
    (out / 'silent.mp4').unlink(); (out / 'mix.wav').unlink()
    timing = {'length': END, 'tempo': tempo, 'cuts': S, 'music': info, 'part_lengths': [round(x, 2) for x in lens]}
    (out / 'timing.json').write_text(json.dumps(timing, indent=1))
    print(json.dumps(timing))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('lines', 'build'):
        sys.exit(__doc__)
    work = pathlib.Path(sys.argv[2]).resolve()
    if sys.argv[1] == 'lines':
        print(json.dumps(lines(json.loads((work / 'reel.json').read_text())), ensure_ascii=False, indent=1))
    else:
        build(work)
