"""Instagram news reel: 5 live news posts -> a 30-33 s 1080x1920 MP4 + its cover (docs/news-reel-playbook.md).

    python3 news_reel.py lines WORK   # prints the 7 voice lines to send to text-to-speech (intro, 5 stories, outro)
    python3 news_reel.py build WORK   # voice/*.mp3 + src/*.jpg + reel.json -> out/reel.mp4, out/cover.jpg, out/check-*.jpg

WORK holds reel.json (see the playbook), voice/0.mp3 ... voice/6.mp3 (intro, stories 1-5, outro, in that order)
and src/<img>.jpg (each story's site cover). Needs: pip install playwright imageio imageio-ffmpeg numpy pillow
and a Chromium for Playwright (python3 -m playwright install chromium).
"""
import datetime, json, os, pathlib, re, shutil, subprocess, sys, urllib.request, wave
import numpy as np

KIT = pathlib.Path(__file__).parent
SR, FPS, SCALE = 44100, 30, 2   # frames are drawn at 2x: the reel and cover are 4K masters (2160x3840)
V0, GAP_INTRO, GAP_STORY, HOLD = 0.3, 0.3, 0.5, 1.6   # voice starts at 0.3 s; breath after the intro and after each story; end card hold
MAX_LEN, TEMPOS = float(os.environ.get('REEL_MAX_LEN', 33.0)), (1.10, 1.12, 1.14, 1.16, 1.18, 1.20, 1.22)
BRIEF = {'morning': ('MORNING BRIEF', 'सुबह'), 'afternoon': ('AFTERNOON BRIEF', 'दोपहर'), 'evening': ('EVENING BRIEF', 'दिन भर')}
LOGO = 'https://incbusiness.in/images/brand/incbusiness-logo-light.png'


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def story_text(s):
    return ' '.join(c['text'] for c in s['say']) + (' ' + s['extra_say'] if s.get('extra_say') else '')


def lines(R):
    return [R['intro_say']] + [story_text(s) for s in R['stories']] + [R['outro_say']]


def syllables(text):
    """Rough syllable count, for placing the karaoke marker: Devanagari letters not killed by a virama, vowel groups in Latin."""
    n = 0
    for tok in text.split():
        if re.search('[ऀ-ॿ]', tok):
            n += sum(1 for i, ch in enumerate(tok) if ('ऄ' <= ch <= 'ह') and not (i + 1 < len(tok) and tok[i + 1] == '्'))
        else:
            n += max(1, len(re.findall(r'[aeiouy]+', tok.lower())) + len(re.findall(r'\d', tok)))
    return max(n, 1)


def load_voice(path, tempo):
    """One spoken part: trim the ends, shorten long pauses, speed up a little (pitch kept)."""
    trim = 'silenceremove=start_periods=1:start_threshold=-40dB'
    af = f'{trim},areverse,{trim},areverse,silenceremove=stop_periods=-1:stop_duration=0.18:stop_threshold=-38dB,atempo={tempo}'
    raw = subprocess.run([ffmpeg(), '-i', str(path), '-af', af, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def plan(work, R):
    files = [work / 'voice' / f'{k}.mp3' for k in range(len(R['stories']) + 2)]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        sys.exit('Missing voice files: ' + ', '.join(missing))
    gaps = [GAP_INTRO] + [GAP_STORY] * len(R['stories'])
    for tempo in TEMPOS:
        parts = [load_voice(f, tempo) for f in files]
        total = V0 + sum(len(p) for p in parts) / SR + sum(gaps) + HOLD
        if total <= MAX_LEN:
            break
    else:
        sys.exit(f'Too long even at {TEMPOS[-1]}x ({total:.1f} s, max {MAX_LEN}). Shorten the spoken lines (drop "लगभग", shorter numbers, or one extra line) and redo the voice.')
    starts, t, chunks = [], V0, []
    for k, p in enumerate(parts):
        starts.append(t); chunks.append((t, p)); t += len(p) / SR
        if k < len(gaps):
            t += gaps[k]
    return tempo, parts, starts, chunks, t + HOLD, [len(p) / SR for p in parts]


def music(total, cuts, first_cut, pops, seed):
    """News bed synthesised fresh for every reel (seeded): key, tempo, chords and arp pattern change per seed."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    def env(L, a=.004, d=.2):
        x = np.arange(int(L * SR)) / SR; return np.minimum(x / a, 1) * np.exp(-x / d)
    def add(buf, sig, at):
        i = int(at * SR); j = min(n, i + len(sig))
        if 0 <= i < n: buf[i:j] += sig[:j - i].astype(np.float32)
    def saw(f, L):
        x = np.arange(int(L * SR)) / SR; return sum(np.sin(2 * np.pi * f * k * x) / k for k in range(1, 8)) * .6
    def whoosh(L=.5):
        m = int(L * SR); x = np.linspace(0, 1, m); a = .02 + .5 * x ** 2
        y = np.zeros(m); s = 0.; noise = rng.standard_normal(m)
        for i in range(m): s += a[i] * (noise[i] - s); y[i] = s
        y *= np.sin(np.pi * x) ** 1.5; return y / np.abs(y).max()

    semis = int(rng.integers(-3, 4)); tr = 2 ** (semis / 12)
    progs = [[(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 164.81, 196.0), (196.0, 246.94, 293.66)],   # Am F C G
             [(196.0, 246.94, 293.66), (164.81, 196.0, 246.94), (130.81, 164.81, 196.0), (146.83, 185.0, 220.0)],     # G Em C D
             [(146.83, 174.61, 220.0), (116.54, 146.83, 174.61), (130.81, 164.81, 196.0), (110.0, 138.59, 164.81)],   # Dm Bb C A
             [(164.81, 196.0, 246.94), (130.81, 164.81, 196.0), (146.83, 185.0, 220.0), (123.47, 155.56, 185.0)]]     # Em C D B
    chords = [tuple(f * tr for f in c) for c in progs[int(rng.integers(len(progs)))]]
    bpm = int(rng.choice([116, 120, 124, 128, 132])); beat = 60 / bpm
    arp = [[0, 1, 2, 1], [0, 2, 1, 2], [2, 1, 0, 1], [0, 1, 2, 2]][int(rng.integers(4))]
    hat_open = rng.random() < .5

    m = np.zeros(n, np.float32)
    add(m, whoosh(.3) * .35, 0)
    for at, f0 in ((.05, 55.0 * tr), (.5, 41.2 * tr)):                   # cinematic "ta-dum"
        x = np.arange(int(1.4 * SR)) / SR
        add(m, np.sin(2 * np.pi * (f0 + 60 * np.exp(-x * 18)) * x) * np.exp(-x * 2.2), at)
        add(m, sum(saw(f0 * k, 1.4) for k in (2, 3, 4, 6)) * env(1.4, a=.02, d=.5) * .07, at)
    k, st = 0, .9
    while st + k * beat / 4 < total - 1.0:
        at = st + k * beat / 4; ch = chords[(k // 16) % 4]
        h = np.diff(rng.standard_normal(int(.03 * SR)) * env(.03, a=.001, d=.01), prepend=0)
        add(m, h * (.13 if k % 2 else (.09 if hat_open else .05)), at)
        if k % 4 == 0:
            x = np.arange(int(.25 * SR)) / SR
            add(m, np.sin(2 * np.pi * (50 + 110 * np.exp(-x * 35)) * x) * np.exp(-x * 11) * .7, at)
        if k % 4 == 2:
            add(m, saw(ch[0] / 4, .18) * env(.18, d=.09) * .35, at)
        if k % 8 == 4:
            add(m, rng.standard_normal(int(.15 * SR)) * env(.15, a=.001, d=.05) * .22, at)
        if k % 2 == 0:
            add(m, saw(ch[arp[(k // 2) % 4]] * 2, .2) * env(.2, d=.06) * .06, at)
        k += 1
    add(m, sum(saw(f, 1.5) for f in chords[0]) * env(1.5, d=.5) * .2, cuts[-1])   # end-card hit
    crash = np.diff(rng.standard_normal(int(.8 * SR)), prepend=0) * env(.8, a=.002, d=.18)   # glass break into story 1
    add(m, crash * .45, first_cut - .02)
    for _ in range(14):
        L = .25; f = 2500 + rng.random() * 4500
        add(m, np.sin(2 * np.pi * f * np.arange(int(L * SR)) / SR) * env(L, a=.001, d=.05) * .12, first_cut + .03 + rng.random() * .45)
    x = np.arange(int(.5 * SR)) / SR
    add(m, np.sin(2 * np.pi * (50 + 150 * np.exp(-x * 25)) * x) * np.exp(-x * 7) * .9, first_cut)

    sfx = np.zeros(n, np.float32)
    for c in cuts:
        add(sfx, whoosh(.45), c - .3)
        x = np.arange(int(.3 * SR)) / SR
        add(sfx, np.sin(2 * np.pi * (60 + 160 * np.exp(-x * 30)) * x) * np.exp(-x * 12) * .6, c)
    for p in pops:
        x = np.arange(int(.09 * SR)) / SR
        add(sfx, np.sin(2 * np.pi * (500 + 9000 * x) * x) * np.exp(-x * 45) * .35, p)
    return m, sfx, dict(semitones=semis, bpm=bpm)


def build(work):
    R = json.loads((work / 'reel.json').read_text())
    if len(R['stories']) != 5:
        sys.exit('A reel needs exactly 5 stories.')
    for s in R['stories']:
        if not (work / 'src' / f"{s['img']}.jpg").exists():
            sys.exit(f"Missing src/{s['img']}.jpg")
    out = work / 'out'; out.mkdir(exist_ok=True)
    (work / 'assets').mkdir(exist_ok=True)
    if not (work / 'assets' / 'logo-light.png').exists():
        req = urllib.request.Request(LOGO, headers={'User-Agent': 'Mozilla/5.0 (incbusiness reel kit)'})  # the host refuses a bare urllib UA
        (work / 'assets' / 'logo-light.png').write_bytes(urllib.request.urlopen(req).read())
    for f in ('reel.html', 'cover.html'):
        shutil.copy(KIT / f, work / f)

    tempo, parts, starts, chunks, total, lens = plan(work, R)
    S = [0.0] + [round(x, 3) for x in starts[1:]]           # scene cuts: intro, stories, end card
    END = round(total, 3)
    stories = []
    for k, s in enumerate(R['stories']):
        tot = syllables(story_text(s)); acc = 0; hi = []
        for c in s['say']:
            if c.get('words'):
                hi.append([c['words'][0], c['words'][1], round(acc / tot, 3)])
            acc += syllables(c['text'])
        st = {'img': s['img'], 'icon': s.get('icon', 'chart'), 'title': s['title'], 'hl': s.get('hl', []), 'hi': hi}
        if s.get('sub'):
            st['sub'] = s['sub']; st['subAt'] = round(acc / tot, 3)
        stories.append(st)
    d = datetime.date.fromisoformat(R['date'])
    brief, _ = BRIEF[R['slot']]
    page = {'date_day': str(d.day), 'date_rest': d.strftime('%B %Y').upper(), 'brief': brief, 'stories': stories, 'S': S, 'END': END}

    # audio: music ducked under the voice, whooshes on the cuts, pops on icons and extra lines
    seed = R.get('music_seed') or int(d.strftime('%Y%m%d')) * 10 + list(BRIEF).index(R['slot'])
    pops = [1.0] + [2.4 + k * .12 for k in range(5)] + [S[i] + .85 for i in range(1, 6)]
    for i, st in enumerate(stories, 1):
        if 'subAt' in st:
            pops.append(S[i] + st['subAt'] * (S[i + 1] - S[i] - .5))
    pops.append(S[6] + .5)
    m, sfx, info = music(total, S[2:], S[1], pops, seed)
    n = len(m); tt = np.arange(n) / SR
    voice = np.zeros(n, np.float32)
    for at, p in chunks:
        i = int(at * SR); voice[i:i + len(p)] = p[:max(0, n - i)]
    vend = chunks[-1][0] + len(chunks[-1][1]) / SR
    g = np.interp(tt, [0, V0 - .1, V0 + .15, vend, vend + .3, total - 1.0, total], [1, 1, .3, .3, .7, .7, 0])
    mix = m * g + sfx * .55 + voice * 1.25
    mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / np.abs(mix).max() * .93
    with wave.open(str(out / 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.repeat((mix * 32767).astype(np.int16)[:, None], 2, axis=1).tobytes())

    # frames -> MP4, then the cover and a few check frames
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
        checks = {'intro': 2.6}
        for i in range(1, 6):
            checks[f'story{i}'] = round(S[i] + (S[i + 1] - S[i]) * .7, 2)
        checks['end'] = round(END - .8, 2)
        for name, at in checks.items():
            pg.evaluate(f'render({at})'); pg.screenshot(path=str(out / f'check-{name}.png'))
            Image.open(out / f'check-{name}.png').convert('RGB').resize((1080, 1920), Image.LANCZOS).save(out / f'check-{name}.jpg', quality=90)  # small, for looking only
            (out / f'check-{name}.png').unlink()
        # near-lossless 4K intermediate; the only real compression is the final encode
        w = imageio.get_writer(str(out / 'silent.mp4'), fps=FPS, codec='libx264', pixelformat='yuv420p', macro_block_size=8,
                               output_params=['-crf', '8', '-preset', 'veryfast'])
        for f in range(int(FPS * END)):
            pg.evaluate(f'render({f / FPS})')
            w.append_data(imageio.imread(pg.screenshot(type='png'), format='png')[:, :, :3])
        w.close()
        pg.goto((work / 'cover.html').as_uri()); pg.evaluate('document.fonts.ready')
        lead = R['stories']
        pg.evaluate(f"setF({json.dumps({'imgs': [s['img'] for s in lead[:3]], 'title': lead[0]['title'], 'date': d.strftime('%-d %b %Y')})})")
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
    if len(sys.argv) != 3 or sys.argv[1] not in ('lines', 'build'):
        sys.exit(__doc__)
    work = pathlib.Path(sys.argv[2]).resolve()
    if sys.argv[1] == 'lines':
        print(json.dumps(lines(json.loads((work / 'reel.json').read_text())), ensure_ascii=False, indent=1))
    else:
        build(work)
