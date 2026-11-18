"""Data for the AI Tools list reel (docs/list-reel-playbook.md): which category today, and its tools from the live site.

    python3 list_reel_data.py pick YYYY-MM-DD noon|evening [SKIP]   # today's category slug (2 a day, rotating); SKIP=1,2.. takes the next ones
    python3 list_reel_data.py fetch SLUG WORK                # WORK/list.json + WORK/src/<icon>.png, all from https://incbusiness.in
    python3 list_reel_data.py cover YYYY-MM-DD noon|evening WORK   # WORK/cover.json: colour world, layout, number and 3D prop set;
                                                                   # you only write its "lines" (the title), see the playbook

Everything comes from the live category page (/ai-tools/SLUG) and each tool's page (/ai-tool/...), where the
official website link is read. Nothing is typed in by hand.
"""
import datetime, html, json, pathlib, re, sys, urllib.request

SITE = 'https://incbusiness.in'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; incbusiness reel kit)'}   # the server refuses requests without a browser-like agent
START = datetime.date(2026, 11, 19)
SLOTS = {'noon': 0, 'evening': 1}
# rotation order (the category list on the site, marketing first); new categories on the site are added at the end
ORDER = ('marketing sales e-commerce email seo social-media design logo-branding video-editing voice-audio writing customer-support '
         'hr-hiring finance-accounting productivity meetings-notes coding website-builders research presentations chatbots image-generation '
         'photo-editing transcription translation ai-agents automation data-analysis spreadsheets project-management crm lead-generation ads '
         'content-repurposing ai-avatars music podcasting youtube thumbnails resume legal education note-taking scheduling chatbot-builders '
         'whatsapp voice-agents ai-search pdf forms-surveys app-builders ux-ui-design 3d interior-design real-estate healthcare restaurants '
         'tax-gst cybersecurity ai-detection grammar storytelling influencer-marketing reviews inventory').split()


def get(url, binary=False):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    return data if binary else data.decode('utf-8', 'replace')


def categories():
    page = get(f'{SITE}/ai-tools/marketing')
    live = list(dict.fromkeys(re.findall(r'href="(?:https://incbusiness\.in)?/ai-tools/([a-z0-9-]+)"', page)))
    return [c for c in ORDER if c in live] + [c for c in live if c not in ORDER]


def index(day, slot):
    return (datetime.date.fromisoformat(day) - START).days * 2 + SLOTS[slot]


def pick(day, slot, skip=0):
    cats = categories()
    return cats[(index(day, slot) + skip) % len(cats)]


# the 3D prop on each category's cover (cover3d/engine.html PROPS)
PROP = {'marketing': 'mega', 'sales': 'chart', 'e-commerce': 'cart', 'email': 'envelope', 'seo': 'magnifier', 'social-media': 'at',
        'design': 'palette', 'logo-branding': 'star', 'video-editing': 'clapper', 'voice-audio': 'mic', 'writing': 'pencil',
        'customer-support': 'headphones', 'hr-hiring': 'person', 'finance-accounting': 'coin', 'productivity': 'rocket',
        'meetings-notes': 'calendar', 'coding': 'code', 'website-builders': 'browser', 'research': 'magnifier', 'presentations': 'bulb',
        'chatbots': 'bubble', 'image-generation': 'camera', 'photo-editing': 'camera', 'transcription': 'paper', 'translation': 'bubble',
        'ai-agents': 'robot', 'automation': 'gear', 'data-analysis': 'chart', 'spreadsheets': 'sheet', 'project-management': 'calendar',
        'crm': 'person', 'lead-generation': 'magnifier', 'ads': 'mega', 'content-repurposing': 'gear', 'ai-avatars': 'robot', 'music': 'note',
        'podcasting': 'mic', 'youtube': 'play', 'thumbnails': 'camera', 'resume': 'paper', 'legal': 'scales', 'education': 'bulb',
        'note-taking': 'pencil', 'scheduling': 'calendar', 'chatbot-builders': 'robot', 'whatsapp': 'phone', 'voice-agents': 'headphones',
        'ai-search': 'magnifier', 'pdf': 'paper', 'forms-surveys': 'sheet', 'app-builders': 'phone', 'ux-ui-design': 'palette', '3d': 'box',
        'interior-design': 'armchair', 'real-estate': 'house', 'healthcare': 'cross', 'restaurants': 'cup', 'tax-gst': 'coin',
        'cybersecurity': 'shield', 'ai-detection': 'magnifier', 'grammar': 'pencil', 'storytelling': 'books', 'influencer-marketing': 'star',
        'reviews': 'star', 'inventory': 'box'}


def cover(day, slot, work):
    work = pathlib.Path(work)
    L = json.loads((work / 'list.json').read_text())
    pals = json.loads((pathlib.Path(__file__).parent / 'cover3d' / 'palettes.json').read_text())
    i = index(day, slot)
    P = pals[(i * 7) % len(pals)]          # step 7 through 15 palettes: neighbours never share a colour world
    accent = P['accent'] if P['accent'].lower() != P['mat']['c'].lower() else P['text']
    cfg = {'layout': 'L1' if i % 2 == 0 else 'L2', 'bg': P['bg'], 'grid': P['grid'], 'logo': P['logo'], 'rim': P['rim'],
           'lines': [{'t': 'WRITE ME', 's': 150, 'c': P['text']}, {'t': 'WRITE ME', 's': 170, 'c': P['accent'], 'i': 1}],
           'num': str(len(L['tools'])), 'mat': P['mat'],
           'prop': {'kind': PROP.get(L['category'], 'rocket'), 'a': accent, 'b': P['prop_b']}}
    if cfg['layout'] == 'L1':
        cfg['extra'] = {'t': 'tools', 'c': P['text']}
    (work / 'cover.json').write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
    shapes = ['"Your <topic> stack" (2 lines)', 'a short question ("Still writing ads by hand?")', '"<verb> <result> faster" ("Close deals faster")',
              '"Not just <famous tool>"', '"<topic>, sorted" or "<topic>, done"', 'a promise from the blurb in 3-5 words ("Ask your docs anything")']
    print(json.dumps({'title_shape': shapes[i % len(shapes)], 'blurb': L.get('blurb', ''), 'layout': cfg['layout'], 'palette': P['name'], 'prop': cfg['prop']['kind'], 'title_colour': P['text'], 'accent_colour': P['accent']}))


def fetch(slug, work):
    work = pathlib.Path(work); (work / 'src').mkdir(parents=True, exist_ok=True)
    page = get(f'{SITE}/ai-tools/{slug}')
    m = re.search(r'<title>Best AI (.+?) Tools', page)
    name = html.unescape(m.group(1)) if m else slug.replace('-', ' ').title()
    b = re.search(r'</h1>\s*<p[^>]*>(.*?)</p>', page, re.S)
    blurb = html.unescape(re.sub('<[^>]+>', '', b.group(1))).strip() if b else ''
    rows = re.findall(r'<a href="(https://incbusiness\.in/ai-tool/[^"]+)">(.*?)</a>\s*</li>', page, re.S)
    tools = []
    for url, body in rows:
        nm = re.search(r'<h2>\s*\d+\.\s*(.*?)</h2>', body, re.S)
        if not nm:
            continue
        tname = html.unescape(re.sub('<[^>]+>', '', nm.group(1))).strip()
        icon = re.search(r'/storage/tool-icons/([^"]+)\.png', body)
        tp = get(url)
        ext = [x for x in dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', tp))
               if not re.search(r'incbusiness\.in|//(chat\.)?whatsapp\.com|//wa\.me|//(www\.)?(instagram|facebook|linkedin|twitter|x)\.com|fonts\.googleapis|fonts\.gstatic|//cdn', x)]
        if not ext:
            print(f'skip {tname}: no website link on its page', file=sys.stderr)
            continue
        link = re.sub(r'^https?://(www\.)?', '', ext[0]).split('?')[0].rstrip('/')
        key = icon.group(1) if icon else re.sub(r'[^a-z0-9.]+', '-', tname.lower())
        dest = work / 'src' / f'{key}.png'
        try:
            if not icon:
                raise ValueError
            dest.write_bytes(get(f'{SITE}/storage/tool-icons/{key}.png', binary=True))
        except Exception:
            from PIL import Image, ImageDraw, ImageFont   # no logo saved on the site: a plain letter tile
            im = Image.new('RGB', (64, 64), '#EDB516'); d = ImageDraw.Draw(im)
            try:
                f = ImageFont.truetype('DejaVuSans-Bold.ttf', 36)
            except Exception:
                f = ImageFont.load_default()
            d.text((32, 32), tname[0].upper(), fill='#000', font=f, anchor='mm'); im.save(dest)
        tools.append({'name': tname, 'icon': key, 'link': link})
    tools = tools[:20]
    n = len(tools)
    out = {'category': slug, 'category_name': name, 'blurb': blurb, 'url': f'{SITE}/ai-tools/{slug}',
           'pill': f'AI {name.upper()} TOOLS', 'title': f'{n} AI tools for <span class=y>{html.escape(name)}</span>',
           'sub': 'With website links. <span class=y>Save this list</span>',
           'foot': f'Prices and details: <span class=y>incbusiness.in/ai-tools/{slug}</span>',
           'length': 16, 'tools': tools}
    (work / 'list.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({'category': slug, 'name': name, 'tools': n}))
    if n < 8:
        sys.exit(f'Only {n} tools in {slug}: too few for a list reel (needs 8). Use the next category in the rotation.')


if __name__ == '__main__':
    if len(sys.argv) in (4, 5) and sys.argv[1] == 'pick':
        print(pick(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) == 5 else 0))
    elif len(sys.argv) == 5 and sys.argv[1] == 'cover':
        cover(sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 4 and sys.argv[1] == 'fetch':
        fetch(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
