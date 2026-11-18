"""Instagram AI tools list reel: every tool of one AI Tools category, with its website, on one screen. Music only, no voice.

    python3 ai_list_reel.py build WORK [--checks]   # src/<icon>.png + list.json -> out/reel.mp4, out/check-*.jpg (the cover is made by cover3d/cover3d.py)

WORK/list.json (made by list_reel_data.py fetch):
 {"title": "AI tools for <span class=y>Marketing</span>", "part": "Part 1 of 2", "start": 1,
  "length": 16, "music_seed": 202611190,
  "tools": [{"name": "Jasper", "icon": "jasper.ai", "link": "jasper.ai"}, ...]}   # 6 to 12 tools (6 rows a column at most)
The list never moves, so the links stay readable the whole reel; the background changes every few seconds behind it.
"""
import json, pathlib, shutil, subprocess, sys, urllib.request, wave
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from news_reel import ffmpeg, SR, FPS, SCALE, LOGO
from list_music import music

KIT = pathlib.Path(__file__).parent


HOOKS = ['shatter', 'glitch', 'slice', 'punch', 'rip', 'pixel', 'flip', 'doors', 'fly', 'melt']


def hook_style(seed):
    """Noon and evening always differ, and the order shifts every day (seed = YYYYMMDD + 0 noon / 1 evening): 10 hooks over 5 days."""
    return HOOKS[((seed // 10) * 3 + seed % 10) % len(HOOKS)]


def hook_sfx(n, at, style='shatter', seed=7):
    """The hook's sound, before the music drops in at `at` seconds."""
    rng = np.random.default_rng(seed); out = np.zeros(n, np.float32)
    def add(sig, t0, g):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if 0 <= i < n: out[i:j] += (sig[:j - i] * g).astype(np.float32)
    def boom(t0, g=.9, f0=48, d=6):
        x = np.arange(int(1.0 * SR)) / SR; add(np.sin(2 * np.pi * (f0 + 140 * np.exp(-x * 25)) * x) * np.exp(-x * d), t0, g)
    def hiss(L, d):
        x = np.arange(int(L * SR)) / SR; return np.diff(rng.standard_normal(len(x)), prepend=0) * np.exp(-x * d)
    x = np.arange(int(at * SR)) / SR
    add(np.sin(2 * np.pi * (40 + 25 * x / at) * x) * (x / at) ** 1.5, 0, .3)                         # low rumble into the hit
    if style == 'shatter':
        y = np.arange(int(.35 * SR)) / SR
        add(np.sin(2 * np.pi * (55 + 120 * np.exp(-y * 30)) * y) * np.exp(-y * 10), .42, .8)
        add(hiss(.25, 22), .42, .35)
        add(hiss(1.2, 5.5), at, .55); boom(at)
        for _ in range(26):
            f = 2500 + rng.random() * 6000; t0 = at + .02 + rng.random() * .9; y = np.arange(int(.22 * SR)) / SR
            add(np.sin(2 * np.pi * f * y) * np.exp(-y * 28), t0, .1 + rng.random() * .08)
    elif style == 'glitch':
        for k in range(14):                                                                       # digital bursts, denser toward the snap
            t0 = .3 + (at - .3) * (k / 14) ** .7; L = .03 + rng.random() * .05; y = np.arange(int(L * SR)) / SR
            add(np.sign(np.sin(2 * np.pi * (200 + rng.random() * 1800) * y)) * .5, t0, .25)
        add(hiss(.12, 30), at, .6); boom(at, .8, 60, 9)
    elif style == 'slice':
        for k in range(8):                                                                        # one swish per strip
            y = np.arange(int(.35 * SR)) / SR; sw = rng.standard_normal(len(y)) * np.sin(np.pi * y / .35) ** 2
            add(np.convolve(sw, np.ones(12) / 12, 'same'), at + abs(k - 3.5) * .035, .22)
        y = np.arange(int(.1 * SR)) / SR; add(np.sin(2 * np.pi * 1800 * y) * np.exp(-y * 40), .45, .2)   # blade tick
        boom(at, .7)
    elif style == 'punch':
        y = np.arange(int(at * SR)) / SR                                                         # riser
        add(np.sin(2 * np.pi * (300 * y + 900 * y ** 2 / at)) * (y / at) ** 2, 0, .12)
        add(hiss(.6, 4) * np.linspace(1, 0, int(.6 * SR)), at, .35); boom(at, 1.0, 42, 5)
    elif style == 'rip':
        y = np.arange(int(.45 * SR)) / SR                                                        # zip along the line
        zp = rng.standard_normal(len(y)) * (np.sin(2 * np.pi * 70 * y) > 0) * np.linspace(.3, 1, len(y))
        add(zp, .35, .25)
        add(hiss(.5, 7), at, .5); boom(at, .9)
    elif style == 'pixel':
        for k in range(16):                                                                       # 8-bit blips falling in pitch
            y = np.arange(int(.06 * SR)) / SR; f = 1600 * 2 ** (-k / 6)
            add(np.sign(np.sin(2 * np.pi * f * y)) * np.exp(-y * 30), at + k * .045, .14)
        boom(at, .7, 55, 8)
    elif style == 'flip':
        y = np.arange(int(.4 * SR)) / SR; sw = rng.standard_normal(len(y)) * np.sin(np.pi * y / .4) ** 2
        add(np.convolve(sw, np.ones(20) / 20, 'same'), at - .05, .5); boom(at + .3, .8, 50, 9)
    elif style == 'doors':
        y = np.arange(int(.3 * SR)) / SR; add(np.sin(2 * np.pi * (900 + 600 * y) * y) * (y / .3), .45, .08)   # light hum on the seam
        y = np.arange(int(.8 * SR)) / SR; add(np.convolve(rng.standard_normal(len(y)), np.ones(60) / 60, 'same') * np.exp(-y * 3), at, 1.2)
        boom(at, .9, 40, 5)
    elif style == 'fly':
        y = np.arange(int(.8 * SR)) / SR                                                         # whoosh away, pitch dropping
        add(np.sin(2 * np.pi * (700 - 500 * y) * y) * np.exp(-y * 3) * .4 + np.convolve(rng.standard_normal(len(y)), np.ones(15) / 15, 'same') * np.sin(np.pi * y / .8), at, .35)
        boom(at, .6, 60, 9)
    elif style == 'melt':
        y = np.arange(int(1.0 * SR)) / SR                                                        # descending wobble
        add(np.sin(2 * np.pi * (520 * np.exp(-y * 1.6)) * y + 3 * np.sin(2 * np.pi * 7 * y)) * np.exp(-y * 2), at, .22)
        for k in range(10):
            z = np.arange(int(.12 * SR)) / SR; add(np.sin(2 * np.pi * (900 - 2500 * z) * z) * np.exp(-z * 25), at + .05 + k * .07, .12)   # drips
        boom(at, .7)
    return out


def build(work):
    R = json.loads((work / 'list.json').read_text())
    T = R['tools']
    if not 6 <= len(T) <= 12:
        sys.exit('A list reel needs 6 to 12 tools (split bigger categories into parts).')
    for t in T:
        if not (work / 'src' / f"{t['icon']}.png").exists():
            sys.exit(f"Missing src/{t['icon']}.png")
    out = work / 'out'; out.mkdir(exist_ok=True)
    (work / 'assets').mkdir(exist_ok=True)
    if not (work / 'assets' / 'logo-light.png').exists():
        req = urllib.request.Request(LOGO, headers={'User-Agent': 'Mozilla/5.0 (incbusiness reel kit)'})
        (work / 'assets' / 'logo-light.png').write_bytes(urllib.request.urlopen(req).read())
    shutil.copy(KIT / 'ai-list-reel.html', work / 'reel.html')

    END = float(R.get('length', 16)); per = 3.0
    hl_start = 2.4; hl_step = (END - 1.2 - hl_start) / len(T)
    page = {'title': R['title'], 'part': R.get('part', ''), 'start': R.get('start', 1)} | {'tools': T, 'END': END, 'per': per, 'hlStart': hl_start, 'hlStep': hl_step}
    # hook: when the 3D cover is already rendered (out/cover.jpg), the reel opens on it, it cracks and shatters into the list
    HOOK = 0.0
    if (out / 'cover.jpg').exists() and '--no-hook' not in sys.argv:
        from PIL import Image
        Image.open(out / 'cover.jpg').convert('RGB').resize((1080, 1920), Image.LANCZOS).save(work / 'hook.jpg', quality=92)
        HOOK = 0.9
        style = R.get('hook_style') or hook_style(int(R.get('music_seed', 1)))
        page |= {'hook': 'hook.jpg', 'hookAt': HOOK, 'hookStyle': style}
    TOTAL = END + HOOK

    # music only (no voice): one of 6 styles, fresh per reel; whoosh on each background change
    cuts = [per * k for k in range(1, int(END / per) + 1) if per * k < END - .5]
    m, sfx, info = music(END, cuts, int(R.get('music_seed', 1)))   # style + tune from the seed (list_music.py)
    n = len(m); tt = np.arange(n) / SR
    mix = m * np.interp(tt, [0, END - 1.0, END], [1, 1, 0]) + sfx * .35
    if HOOK:   # the music drops in at the shatter; before it: a low rumble, the crack, then breaking glass
        mix = np.concatenate([np.zeros(int(HOOK * SR), np.float32), mix.astype(np.float32)])
        mix += hook_sfx(len(mix), HOOK, page['hookStyle'])
    mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix = mix / np.abs(mix).max() * .9
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
        pg.evaluate('render(5)'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(800); pg.evaluate('document.fonts.ready.then(fit)')
        checks = {f'bg{k}': round(HOOK + per * k + 1.5, 2) for k in range(int(END / per)) if per * k + 1.5 < END - .5}
        if HOOK:
            checks |= {'hook-crack': .7, 'hook-shatter': round(HOOK + .25, 2)}
        for name, at in checks.items():
            pg.evaluate(f'render({at})'); pg.screenshot(path=str(out / f'check-{name}.png'))
            Image.open(out / f'check-{name}.png').convert('RGB').resize((1080, 1920), Image.LANCZOS).save(out / f'check-{name}.jpg', quality=90)
            (out / f'check-{name}.png').unlink()
        if '--checks' in sys.argv:
            br.close(); return
        w = imageio.get_writer(str(out / 'silent.mp4'), fps=FPS, codec='libx264', pixelformat='yuv420p', macro_block_size=8,
                               output_params=['-crf', '8', '-preset', 'veryfast'])
        for f in range(int(FPS * TOTAL)):
            pg.evaluate(f'render({f / FPS})')
            w.append_data(imageio.imread(pg.screenshot(type='png'), format='png')[:, :, :3])
        w.close()
        br.close()
    subprocess.run([ffmpeg(), '-y', '-i', str(out / 'silent.mp4'), '-i', str(out / 'mix.wav'), '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-profile:v', 'high', '-level', '5.1',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', str(out / 'reel.mp4')], check=True, capture_output=True)
    (out / 'silent.mp4').unlink(); (out / 'mix.wav').unlink()
    print(json.dumps({'length': round(TOTAL, 2), 'hook': page.get('hookStyle', False), 'tools': len(T), 'music': info}))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'build':
        sys.exit(__doc__)
    build(pathlib.Path(sys.argv[2]).resolve())
