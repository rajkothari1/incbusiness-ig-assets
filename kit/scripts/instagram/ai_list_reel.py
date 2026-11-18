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


def hook_sfx(n, at, crack=.42, seed=7):
    """Low rumble into the crack (thud + crackle), then a glass break with falling shards at the shatter."""
    rng = np.random.default_rng(seed); out = np.zeros(n, np.float32)
    def add(sig, t0, g):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if 0 <= i < n: out[i:j] += (sig[:j - i] * g).astype(np.float32)
    x = np.arange(int(at * SR)) / SR
    add(np.sin(2 * np.pi * (40 + 25 * x / at) * x) * (x / at) ** 1.5, 0, .35)                       # rumble rising to the break
    x = np.arange(int(.35 * SR)) / SR
    add(np.sin(2 * np.pi * (55 + 120 * np.exp(-x * 30)) * x) * np.exp(-x * 10), crack, .8)          # thud of the impact
    cr = np.diff(rng.standard_normal(int(.25 * SR)), prepend=0) * np.exp(-np.arange(int(.25 * SR)) / SR * 22)
    add(cr, crack, .35)                                                                            # crackle
    L = 1.2; x = np.arange(int(L * SR)) / SR
    add(np.diff(rng.standard_normal(len(x)), prepend=0) * np.exp(-x * 5.5), at, .55)               # glass burst
    add(np.sin(2 * np.pi * (48 + 140 * np.exp(-x * 25)) * x) * np.exp(-x * 6), at, .9)               # boom under it
    for _ in range(26):                                                                            # tinkling shards
        f = 2500 + rng.random() * 6000; t0 = at + .02 + rng.random() * .9; y = np.arange(int(.22 * SR)) / SR
        add(np.sin(2 * np.pi * f * y) * np.exp(-y * 28), t0, .1 + rng.random() * .08)
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
        page |= {'hook': 'hook.jpg', 'hookAt': HOOK}
    TOTAL = END + HOOK

    # music only (no voice): one of 6 styles, fresh per reel; whoosh on each background change
    cuts = [per * k for k in range(1, int(END / per) + 1) if per * k < END - .5]
    m, sfx, info = music(END, cuts, int(R.get('music_seed', 1)))   # style + tune from the seed (list_music.py)
    n = len(m); tt = np.arange(n) / SR
    mix = m * np.interp(tt, [0, END - 1.0, END], [1, 1, 0]) + sfx * .35
    if HOOK:   # the music drops in at the shatter; before it: a low rumble, the crack, then breaking glass
        mix = np.concatenate([np.zeros(int(HOOK * SR), np.float32), mix.astype(np.float32)])
        mix += hook_sfx(len(mix), HOOK)
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
    print(json.dumps({'length': round(TOTAL, 2), 'hook': bool(HOOK), 'tools': len(T), 'music': info}))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'build':
        sys.exit(__doc__)
    build(pathlib.Path(sys.argv[2]).resolve())
