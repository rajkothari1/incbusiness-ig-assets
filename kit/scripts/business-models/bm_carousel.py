#!/usr/bin/env python3
"""Render an Instagram carousel for one Business Models post: 8 to 10 slides, 1080 x 1350 (4:5), in the
same house style and company colour as the post's own charts (bm_graphics.py).

Usage:
    python3 scripts/business-models/bm_carousel.py carousel.json OUT_DIR

carousel.json:
    {"company": "Zepto", "logo": "logo.svg", "color": "#950edb", "url": "incbusiness.in/business-models/zepto",
     "slides": [
       {"type": "hook", "title": "How Zepto Makes Money", "text": "Rs 22,624 crore of revenue in FY26 ..."},
       {"type": "about", "title": "What Zepto does", "text": "...", "image": "site.jpg", "domain": "zepto.com"},
       {"type": "kpis" | "donut" | "bars" | "split" | "fromto" | "flow" | "bullets" | "timeline" | ...,
        ...the same fields as that graphic in bm_graphics.py...},
       {"type": "end", "title": "Read the full breakdown", "text": "..."}
     ]}

Writes OUT_DIR/01.jpg, 02.jpg, ... and OUT_DIR/alt.json (one description per slide, for Instagram alt text). Every slide has its number ("3/9"), our logo bottom left and, except the last, a "Swipe" hint bottom right.
Slides must fit 1350 px: keep them short (4 to 5 rows, 5 donut slices). A slide that overflows stops the
render with its name, so nothing gets cut off. Every number must come from the post's fact check.
"""
import json
import os
import shutil
import subprocess
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
import bm_graphics as G  # noqa: E402

H = 1350
BULLET = "\u2022"
E = G.E


def chrome_css(n, total, accent, last):
    """Slide number top right, our logo bottom left and a swipe hint bottom right, laid over any slide."""
    swipe = "" if last else f'<div class="cr-swipe">Swipe <span>&rarr;</span></div>'
    css = f"""<style>body{{height:{H}px!important;min-height:0!important}}.wrap{{height:{H}px!important;min-height:0!important}}
.cr-n{{position:absolute;top:34px;right:40px;z-index:5;font:600 22px Poppins,sans-serif;color:{G.MUTED};background:#fff;border:2px solid #e1e5ee;border-radius:999px;padding:6px 18px}}
/* Bottom row on every slide: our logo bottom left, the swipe hint bottom right */
.brand{{position:absolute!important;left:72px!important;right:auto!important;bottom:52px!important;height:36px!important;width:auto!important;margin:0!important}}
.foot .src{{display:none}}
.cr-swipe{{position:absolute;right:72px;bottom:48px;z-index:5;font:600 22px Poppins,sans-serif;color:{G.readable(accent)};
background:{G.mix(accent, "#ffffff", .88)};border-radius:999px;padding:8px 22px}}.cr-swipe span{{margin-left:6px}}
.rg{{width:420px!important;height:420px!important;margin-bottom:18px!important}}.rg svg{{width:420px!important;height:420px!important}}
.rl{{padding:11px 0!important}}h1{{padding-right:110px}}
/* Text slides: bigger type than on the website, so they fill the 4:5 page and read well on a phone */
.fl2{{gap:0}}.fs{{padding:30px 34px!important}}.fs b{{font-size:42px!important}}.fs p{{font-size:31px!important;margin-top:8px!important}}
.fs span{{width:70px!important;height:70px!important;font-size:34px!important}}.fa{{font-size:48px!important;margin:10px 0!important}}
.kg{{gap:26px!important}}.kp{{padding:44px 34px 38px!important}}.kp b{{font-size:66px!important;white-space:nowrap}}.kp span{{font-size:36px!important}}.kp em{{font-size:28px!important}}
.ft{{padding:40px 38px!important}}.fts{{gap:34px!important}}
.bl p{{font-size:36px!important}}.sum{{font-size:34px!important}}</style>"""
    return css, f'<div class="cr-n">{n}/{total}</div>{swipe}'


def poster(accent, logo, inner, extra=""):
    """Full-bleed slide for the first and last pages: big type, the company's logo card, our logo."""
    font = "".join(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(poppins-{w}.woff2)}}" for w in (500, 600, 700))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{G.W}px;height:{H}px;overflow:hidden;font-family:Poppins,sans-serif;color:{G.NAVY};position:relative;
background:linear-gradient(165deg,#ffffff 0%,{G.mix(accent, "#ffffff", .93)} 55%,{G.mix(accent, "#ffffff", .84)} 100%)}}
.rings{{position:absolute;right:-280px;top:-300px;width:820px;height:820px;border-radius:50%;
background:repeating-radial-gradient(circle,transparent 0 46px,{G.mix(accent, "#ffffff", .78)} 46px 47.5px)}}
.wrap{{position:relative;height:100%;padding:96px 80px 70px;display:flex;flex-direction:column}}
.k{{font-size:26px;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:{G.mix(accent, G.NAVY, .3)}}}
.t{{font-size:104px;font-weight:700;line-height:1.02;letter-spacing:-3px;margin-top:22px}}.t em{{font-style:normal;color:{G.readable(accent)}}}
.x{{font-size:38px;font-weight:500;line-height:1.35;color:#4d5568;margin-top:30px}}
.card{{width:520px;height:360px;border-radius:36px;background:#fff;display:flex;align-items:center;justify-content:center;
border:2px solid {G.mix(accent, "#ffffff", .55)};box-shadow:0 30px 70px rgba(22,33,61,.14)}}.card img{{width:72%;max-height:50%;object-fit:contain}}
.brand{{height:34px;width:auto;align-self:flex-end}}{extra}</style></head><body><div class="rings"></div><div class="wrap">{inner}</div></body></html>"""


def hook(s, spec, accent, logo):
    """The cover. With "stats" ([{"value": "₹23,053 cr", "label": "Revenue, FY26"}, ...], 1 or 2) the numbers
    are the hero and the logo sits small at the top; without, the logo card fills the middle."""
    title = E(s["title"]).replace(E(spec["company"]), f'<em>{E(spec["company"])}</em>', 1)
    if s.get("stats"):
        stats = "".join(f'<div class="st"><b>{E(x["value"])}</b><span>{E(x["label"])}</span></div>' for x in s["stats"][:2])
        inner = (f'<div class="lg"><img src="{logo}" alt=""></div><div class="k" style="margin-top:40px">Business model</div>'
                 f'<div class="t">{title}</div><div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:26px">{stats}</div>'
                 f'<img class="brand" src="incbusiness-logo-dark.png" alt="">')
        css = f""".lg{{width:260px;height:120px;border-radius:24px;background:#fff;display:flex;align-items:center;justify-content:center;
border:2px solid {G.mix(accent, "#ffffff", .55)};box-shadow:0 18px 40px rgba(22,33,61,.12)}}.lg img{{max-width:76%;max-height:62%;object-fit:contain}}
.st{{background:#fff;border-radius:28px;border:2px solid #e6e8ef;border-left:12px solid {accent};padding:30px 38px}}
.st b{{display:block;font-size:104px;font-weight:700;letter-spacing:-3px;line-height:1;color:{G.readable(accent)}}}
.st span{{display:block;font-size:34px;font-weight:600;color:#4d5568;margin-top:10px}}"""
        return poster(accent, logo, inner, css)
    inner = (f'<div class="k">Business model</div><div class="t">{title}</div><div class="x">{E(s.get("text", ""))}</div>'
             f'<div style="flex:1;display:flex;align-items:center"><div class="card"><img src="{logo}" alt=""></div></div>'
             f'<img class="brand" src="incbusiness-logo-dark.png" alt="">')
    return poster(accent, logo, inner)


def about(s, spec, accent, logo):
    """What the company does: 2 or 3 plain lines in big type, then its website screenshot ("image", "domain")
    or, without one, 3 or 4 short facts as icon rows.
    {"title": "What Zepto does", "text": "...", "image": "site.jpg", "domain": "zepto.com"}"""
    facts = "".join(f'<div class="f"><span>{E(f.get("icon", BULLET))}</span><div><em>{E(f["label"])}</em><b>{E(f["value"])}</b></div></div>'
                    for f in s.get("facts", []))
    inner = (f'<div class="k">{E(spec["company"])} business model</div><div class="t" style="font-size:78px">{E(s["title"])}</div>'
             f'<div class="lead">{E(s["text"])}</div>'
             + (f'<div style="flex:1;display:flex;align-items:center">{browser(s)}</div>' if s.get("_img") else f'<div class="fs2">{facts}</div><div style="flex:1"></div>')
             + f'<img class="brand" src="incbusiness-logo-dark.png" alt="">')
    css = f""".lead{{margin-top:34px;font-size:40px;font-weight:500;line-height:1.38;border-left:10px solid {accent};padding-left:30px}}
.fs2{{margin-top:48px;display:flex;flex-direction:column;gap:18px}}
.f{{display:flex;align-items:center;gap:24px;background:#fff;border:2px solid #e1e5ee;border-radius:22px;padding:22px 28px}}
.f span{{flex:none;width:66px;height:66px;border-radius:18px;background:{G.mix(accent, "#ffffff", .86)};display:grid;place-items:center;font-size:34px}}
.f em{{display:block;font-style:normal;font-size:22px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{G.readable(accent)}}}
.f b{{display:block;font-size:32px;font-weight:600;line-height:1.3;margin-top:2px}}""" + browser_css(accent)
    return poster(accent, logo, inner, css)


def browser(s):
    """The company's website screenshot (from the post) in a simple browser frame."""
    return (f'<div class="bw"><div class="bb"><i></i><i></i><i></i><span>{E(s.get("domain", ""))}</span></div>'
            f'<img src="{s["_img"]}" alt=""></div>')


def browser_css(accent):
    return f""".bw{{width:100%;border-radius:22px;overflow:hidden;background:#fff;border:2px solid {G.mix(accent, "#ffffff", .6)};box-shadow:0 30px 70px rgba(22,33,61,.16)}}
.bb{{display:flex;align-items:center;gap:10px;padding:16px 22px;background:#f3f4f8;border-bottom:2px solid #e6e8ef}}
.bb i{{width:16px;height:16px;border-radius:50%;background:#d5d9e3}}.bb span{{margin-left:14px;font-size:22px;font-weight:600;color:#6b7385;background:#fff;border-radius:999px;padding:6px 20px}}
.bw img{{display:block;width:100%;height:auto}}"""


def shot(s, spec, accent, logo):
    """The company's own website on its own slide, with a short caption.
    {"title": "The Zepto website", "image": "site.jpg", "domain": "zepto.com", "text": "..."}"""
    inner = (f'<div class="k">{E(spec["company"])} business model</div><div class="t" style="font-size:78px">{E(s["title"])}</div>'
             f'<div class="x">{E(s.get("text", ""))}</div><div style="flex:1;display:flex;align-items:center">{browser(s)}</div>'
             f'<img class="brand" src="incbusiness-logo-dark.png" alt="">')
    return poster(accent, logo, inner, browser_css(accent))


def end(s, spec, accent, logo):
    rows = "".join(f'<div class="r"><span>{E(a)}</span>{E(b)}</div>' for a, b in s.get("actions", [
        ("↗", "Read the full breakdown with every chart"), ("♡", "Save this post for later"), ("+", "Follow @incbusiness.official")]))
    inner = (f'<div class="k">{E(spec["company"])} business model</div><div class="t" style="font-size:84px">{E(s["title"])}</div>'
             f'<div class="x">{E(s.get("text", ""))}</div><div class="rs">{rows}</div>'
             f'<div class="u">{E(spec["url"])}</div><div style="flex:1"></div><img class="brand" src="incbusiness-logo-dark.png" alt="">')
    css = f""".rs{{margin-top:50px;display:flex;flex-direction:column;gap:18px}}
.r{{display:flex;align-items:center;gap:24px;background:#fff;border:2px solid #e1e5ee;border-radius:22px;padding:24px 30px;font-size:34px;font-weight:600}}
.r span{{flex:none;width:62px;height:62px;border-radius:50%;background:{G.readable(accent)};color:#fff;display:grid;place-items:center;font-size:32px}}
.u{{margin-top:40px;font-size:34px;font-weight:700;color:{G.readable(accent)}}}"""
    return poster(accent, logo, inner, css)


def alt_text(s, spec):
    """A plain description of one slide: its own "alt" when the spec gives one, else built from its content."""
    if s.get("alt"):
        return s["alt"]
    c, t = spec["company"], s.get("title", "")
    money = lambda it: f'{it["label"]} {G.val(s, it["value"])}'.replace("\u20b9", "Rs ")
    if s["type"] == "hook":
        return f"{t}. " + ("; ".join(f'{x["label"]} {x["value"]}' for x in s.get("stats", [])).replace("\u20b9", "Rs ") + "." if s.get("stats") else s.get("text", ""))
    if s["type"] == "about":
        return f"{t}. {s.get('text', '')} With a screenshot of the {s.get('domain', c)} website."
    if s["type"] in ("donut", "pie", "hbars"):
        return f"{t}, {s.get('subtitle', '')}: " + "; ".join(money(it) for it in s["items"]) + "."
    if s["type"] in ("bars", "stacked", "line"):
        rows = [f'{se["name"]} ' + ", ".join(f"{cat} {G.val(s, v)}" for cat, v in zip(s["categories"], se["values"]) if v is not None) for se in s["series"]]
        return (f"{t}, {s.get('subtitle', '')}: " + "; ".join(rows) + ".").replace("\u20b9", "Rs ")
    if s["type"] == "kpis":
        return f"{t}, {s.get('subtitle', '')}: " + "; ".join(f'{it["label"]} {it["value"]}' + (f' ({it["note"]})' if it.get("note") else "") for it in s["items"]).replace("\u20b9", "Rs ") + "."
    if s["type"] == "fromto":
        return f"{t}: " + "; ".join(f'{it["label"]} from {it["from"]} ({it["from_label"]}) to {it["to"]} ({it["to_label"]})' for it in s["items"]).replace("\u20b9", "Rs ") + "."
    if s["type"] == "end":
        return f"{t}. {s.get('text', '')} Read it on {spec['url']} and follow @incbusiness.official."
    return t


def overflow(chrome, page_path):
    """Content height of a slide (scrollHeight), to catch anything that would be cut off."""
    probe = page_path.replace(".html", ".probe.html")
    doc = open(page_path, encoding="utf-8").read().replace(
        "</body>", '<script>window.onload=function(){var w=document.querySelector(".wrap");'
        'document.body.setAttribute("data-h",Math.max(w?w.scrollHeight:0,document.documentElement.scrollHeight));}</script></body>')
    open(probe, "w", encoding="utf-8").write(doc)
    out = subprocess.run([chrome, "--headless=new", "--disable-gpu", f"--window-size={G.W},{H}", "--virtual-time-budget=3000",
                          "--dump-dom", "file://" + probe], capture_output=True, text=True, timeout=60).stdout
    import re
    m = re.search(r'data-h="(\d+)"', out)
    return int(m.group(1)) if m else 0


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = os.path.abspath(sys.argv[2])
    work = os.path.join(out, "_html")
    G.fetch_assets(work)
    logo = "logo" + os.path.splitext(spec["logo"])[1]
    shutil.copy(spec["logo"], os.path.join(work, logo))
    accent = spec.get("color") or G.logo_color(spec["logo"]) or "#2f4b8f"
    chrome = G.find_chrome()
    slides = spec["slides"]
    alts = []
    for n, s in enumerate(slides, 1):
        last = n == len(slides)
        if s["type"] == "hook":
            doc = hook(s, spec, accent, logo)
        elif s["type"] in ("shot", "about"):
            if s.get("image"):  # the website screenshot, copied next to the page
                s = dict(s, _img=f"shot{n}" + os.path.splitext(s["image"])[1])
                shutil.copy(s["image"], os.path.join(work, s["_img"]))
            doc = (shot if s["type"] == "shot" else about)(s, spec, accent, logo)
        elif s["type"] == "end":
            doc = end(s, spec, accent, logo)
        else:
            doc = G.RENDER[s["type"]](dict(s), spec["company"], accent)
        css, over = chrome_css(n, len(slides), accent, last)
        doc = doc.replace("</head>", css + "</head>", 1).replace("</body>", over + "</body>", 1)
        name = f"{n:02d}"
        page_path = os.path.join(work, name + ".html")
        open(page_path, "w", encoding="utf-8").write(doc)
        h = overflow(chrome, page_path)
        if h > H + 2:
            sys.exit(f"Slide {name} ({s['type']}) is {h}px tall, over {H}: shorten it.")
        png = os.path.join(work, name + ".png")
        if not G.screenshot(chrome, "file://" + page_path, png, width=G.W, height=H, wait_ms=3000):
            sys.exit(f"Render failed: {name}")
        G._jpeg(png, os.path.join(out, name + ".jpg"), quality=92)
        alts.append(alt_text(s, spec))
        print("OK   ", os.path.join(out, name + ".jpg"))
    # One description per slide, in order, for Instagram's alt text (Metricool mediaAltText)
    json.dump(alts, open(os.path.join(out, "alt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ALT  ", os.path.join(out, "alt.json"))


if __name__ == "__main__":
    main()
