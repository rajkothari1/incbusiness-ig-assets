"""Instagram AI tools list reel: every tool of one AI Tools category, with its website, on one screen. Music only, no voice.

    python3 ai_list_reel.py build WORK [--checks]   # src/<icon>.png + list.json -> out/reel.mp4, out/cover.jpg, out/check-*.jpg

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

    # music only (no voice): one of 6 styles, fresh per reel; whoosh on each background change
    cuts = [per * k for k in range(1, int(END / per) + 1) if per * k < END - .5]
    m, sfx, info = music(END, cuts, int(R.get('music_seed', 1)))   # style + tune from the seed (list_music.py)
    n = len(m); tt = np.arange(n) / SR
    mix = m * np.interp(tt, [0, END - 1.0, END], [1, 1, 0]) + sfx * .35
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
        checks = {f'bg{k}': round(per * k + 1.5, 2) for k in range(int(END / per)) if per * k + 1.5 < END - .5}
        for name, at in checks.items():
            pg.evaluate(f'render({at})'); pg.screenshot(path=str(out / f'check-{name}.png'))
            Image.open(out / f'check-{name}.png').convert('RGB').resize((1080, 1920), Image.LANCZOS).save(out / f'check-{name}.jpg', quality=90)
            (out / f'check-{name}.png').unlink()
        pg.evaluate('render(4.5)'); pg.screenshot(path=str(out / 'cover.png'))
        if '--checks' in sys.argv:
            br.close(); return
        w = imageio.get_writer(str(out / 'silent.mp4'), fps=FPS, codec='libx264', pixelformat='yuv420p', macro_block_size=8,
                               output_params=['-crf', '8', '-preset', 'veryfast'])
        for f in range(int(FPS * END)):
            pg.evaluate(f'render({f / FPS})')
            w.append_data(imageio.imread(pg.screenshot(type='png'), format='png')[:, :, :3])
        w.close()
        br.close()
    Image.open(out / 'cover.png').convert('RGB').save(out / 'cover.jpg', quality=95); (out / 'cover.png').unlink()
    subprocess.run([ffmpeg(), '-y', '-i', str(out / 'silent.mp4'), '-i', str(out / 'mix.wav'), '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-profile:v', 'high', '-level', '5.1',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', str(out / 'reel.mp4')], check=True, capture_output=True)
    (out / 'silent.mp4').unlink(); (out / 'mix.wav').unlink()
    print(json.dumps({'length': END, 'tools': len(T), 'music': info}))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'build':
        sys.exit(__doc__)
    build(pathlib.Path(sys.argv[2]).resolve())
