#!/usr/bin/env python3
"""Render every image of a Business Models post (1200px wide, house style) from one JSON spec.

Usage:
    python3 scripts/business-models/bm_graphics.py spec.json OUT_DIR

spec.json:
    {"company": "Zepto", "logo": "logo.svg", "color": "#8a1fd6" (optional: taken from the logo when left out),
     "cover": {"title": "How Zepto Makes Money", "kicker": "Quick commerce in minutes"},
     "graphics": [
       {"type": "donut", "file": "revenue-mix", "title": "...", "subtitle": "...", "center": "Rs 22,624 cr",
        "items": [{"label": "Sale of products", "value": 17588}, ...], "source": "Source: ..."},
       {"type": "bars", "file": "revenue-vs-loss", "title": "...", "subtitle": "...", "unit": "Rs cr",
        "categories": ["FY24", "FY25", "FY26"],
        "series": [{"name": "Revenue", "values": [4455, 11110, 22624]},
                   {"name": "Net loss", "values": [1215, 4700, 5905], "tone": "loss"}], "source": "..."},
       {"type": "split", "file": "every-100", "title": "...", "subtitle": "...",
        "items": [{"label": "Buying the products it sells", "value": 80.4}, ...],
        "earned": 100, "summary": "Spent Rs 128 for every Rs 100 earned", "source": "..."},
       {"type": "canvas", "file": "canvas", "title": "...",
        "blocks": {"partners": [...], "activities": [...], "resources": [...], "value": [...],
                   "relationships": [...], "channels": [...], "segments": [...], "costs": [...], "revenue": [...]}},
       {"type": "timeline", "file": "timeline", "title": "...", "items": [{"when": "2021", "what": "..."}], "source": "..."}
     ]}

Writes OUT_DIR/cover.jpg plus one .jpg per graphic. Every number on an image must also be
in the post's fact check: these images are part of what readers see. No text-only cover:
"logo" is required (the company's own logo, from its own site).
"""
import html
import json
import os
import re
import shutil
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_here, os.path.join(_here, "..", "ai-tools"), os.path.join(_here, "..", "news")]
from shoot import find_chrome, screenshot  # noqa: E402
from funding_cover import fetch_assets  # noqa: E402

NAVY, GOLD, MUTED, LOSS = "#16213d", "#c9971a", "#6b7385", "#e0584a"
E = html.escape


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend colour a towards b by t (0..1): mix(accent, "#ffffff", .8) is a light tint."""
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))


def _lum(h):
    c = [v / 255 for v in _rgb(h)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def readable(h):
    """The brand colour for text: a light one (Blinkit yellow, say) is darkened, same hue, until it reads on white (3:1+)."""
    import colorsys
    hh, ll, ss = colorsys.rgb_to_hls(*[v / 255 for v in _rgb(h)])
    while 1.05 / (_lum(h) + .05) < 3 and ll > .05:
        ll -= .03
        h = "#%02x%02x%02x" % tuple(round(v * 255) for v in colorsys.hls_to_rgb(hh, ll, ss))
    return h


def logo_color(path):
    """The logo's main brand colour: the most used saturated colour, ignoring white, black and greys."""
    from collections import Counter
    import colorsys
    import re
    counts = Counter()
    if path.lower().endswith(".svg"):
        txt = open(path, encoding="utf-8", errors="ignore").read()
        for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", txt):
            h = h if len(h) == 6 else "".join(c * 2 for c in h)
            counts["#" + h.lower()] += 1
        for r, g, b in re.findall(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", txt):
            counts["#%02x%02x%02x" % (int(r), int(g), int(b))] += 1
    else:
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        im.thumbnail((200, 200))
        for r, g, b, a in im.getdata():
            if a > 200:
                counts["#%02x%02x%02x" % (r // 8 * 8, g // 8 * 8, b // 8 * 8)] += 1
    for h, _ in counts.most_common():
        hh, ll, ss = colorsys.rgb_to_hls(*[v / 255 for v in _rgb(h)])
        if ss > .25 and .12 < ll < .9:
            return h
    return None


def money(v):
    """17588 -> '17,588'; 136.15 stays 136.15 (never rounds away a reported decimal)."""
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}".rstrip("0").rstrip(".")


def page(body, height, accent, extra_css=""):
    font = "".join(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(poppins-{w}.woff2)}}" for w in (500, 600, 700))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:{height}px;overflow:hidden;font-family:Poppins,sans-serif;color:{NAVY};position:relative;
background:linear-gradient(160deg,#ffffff 0%,{mix(accent, "#ffffff", .95)} 60%,{mix(accent, "#ffffff", .9)} 100%)}}
.rings{{position:absolute;right:-260px;top:-300px;width:760px;height:760px;border-radius:50%;
background:repeating-radial-gradient(circle,transparent 0 44px,{mix(accent, "#ffffff", .8)} 44px 45.5px)}}
.head{{position:absolute;left:64px;top:52px;right:64px}}
.kick{{font-size:15px;font-weight:600;letter-spacing:2.4px;text-transform:uppercase;color:{mix(accent, NAVY, .3)}}}
h1{{font-size:38px;font-weight:700;line-height:1.18;letter-spacing:-.6px;margin-top:8px}}
.sub{{font-size:18px;font-weight:500;color:{MUTED};margin-top:6px}}
.src{{position:absolute;left:64px;bottom:30px;font-size:13px;font-weight:500;color:#8b93a6}}
.brand{{position:absolute;right:64px;bottom:26px;height:22px}}
{extra_css}</style></head><body><div class="rings"></div>{body}
<img class="brand" src="incbusiness-logo-dark.png" alt=""></body></html>"""


def header(g, company):
    sub = f'<div class="sub">{E(g["subtitle"])}</div>' if g.get("subtitle") else ""
    return f'<div class="head"><div class="kick">{E(company)} business model</div><h1>{E(g["title"])}</h1>{sub}</div>'


def footer(g):
    return f'<div class="src">{E(g["source"])}</div>' if g.get("source") else ""


def cover(spec, accent, logo):
    """1200 x 630 cover (link previews and the listing cards): big title, kicker and label on the left,
    the company's logo card on the right. Type is large because the cover is mostly seen as a small card."""
    c = spec["cover"]
    size = 86 if len(c["title"]) <= 24 else 76
    css = f""".cv-l{{position:absolute;left:64px;top:30px;bottom:110px;width:660px;display:flex;flex-direction:column;justify-content:center}}
.cv-k{{font-size:26px;font-weight:700;letter-spacing:3.5px;text-transform:uppercase;color:{mix(accent, NAVY, .3)}}}
.cv-t{{font-size:{size}px;font-weight:700;line-height:1.04;letter-spacing:-2px;margin-top:14px}}
.cv-t em{{font-style:normal;color:{readable(accent)}}}
.cv-s{{font-size:32px;font-weight:500;line-height:1.3;color:#4d5568;margin-top:20px}}
.cv-card{{position:absolute;right:56px;top:150px;width:370px;height:290px;border-radius:32px;background:#fff;
display:flex;align-items:center;justify-content:center;border:1.5px solid {mix(accent, "#ffffff", .55)};
box-shadow:0 30px 70px rgba(22,33,61,.12)}}
.cv-card img{{width:74%;max-height:52%;object-fit:contain}}
.brand{{left:64px;right:auto;bottom:46px;height:36px}}"""
    words = E(c["title"]).replace(E(spec["company"]), f'<em>{E(spec["company"])}</em>', 1)
    body = (f'<div class="cv-l"><div class="cv-k">Business model</div><div class="cv-t">{words}</div>'
            f'<div class="cv-s">{E(c.get("kicker", ""))}</div></div><div class="cv-card"><img src="{logo}" alt=""></div>')
    return page(body, 630, accent, css)


# ---------------------------------------------------------------------------------------------
# Charts are portrait, 1080 px wide (4:5 and taller), with big type, so they fill a phone screen
# and stay readable there. The cover stays 1200 x 630 for link previews and the listing cards.
# Every chart is a flex column: header, chart area (flex: 1), source and logo.
# ---------------------------------------------------------------------------------------------
W = 1080
CW = 936  # content width inside the 72 px side padding
MIN_AUTO = 600  # text pages (AUTO_HEIGHT) are as tall as their text: no stretching, no empty bands


def vpage(g, company, accent, inner, extra_css="", height=1350):
    font = "".join(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(poppins-{w}.woff2)}}" for w in (500, 600, 700))
    sub = f'<div class="sub">{E(g["subtitle"])}</div>' if g.get("subtitle") else ""
    unit = f'<div class="unit">{E(g["unit"])}</div>' if g.get("unit") else ""
    src = f'<div class="src">{E(g["source"])}</div>' if g.get("source") else "<div></div>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{background:#fff}}/* else the body gradient paints the whole window and trim_blank() can't find the end */
body{{width:{W}px;{f"height:{height}px" if height else f"min-height:{MIN_AUTO}px"};overflow:hidden;font-family:Poppins,sans-serif;color:{NAVY};position:relative;
background:linear-gradient(170deg,#ffffff 0%,{mix(accent, "#ffffff", .95)} 55%,{mix(accent, "#ffffff", .9)} 100%)}}
.rings{{position:absolute;right:-300px;top:-330px;width:760px;height:760px;border-radius:50%;
background:repeating-radial-gradient(circle,transparent 0 44px,{mix(accent, "#ffffff", .8)} 44px 45.5px)}}
.wrap{{position:relative;{"height:100%" if height else f"min-height:{MIN_AUTO}px"};display:flex;flex-direction:column;padding:78px 72px 58px}}
.kick{{font-size:22px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:{mix(accent, NAVY, .3)}}}
h1{{font-size:60px;font-weight:700;line-height:1.12;letter-spacing:-1px;margin-top:12px}}
.sub{{font-size:30px;font-weight:500;color:{MUTED};margin-top:12px;line-height:1.35}}
.unit{{font-size:24px;font-weight:600;color:#8b93a6;text-transform:uppercase;letter-spacing:1.5px;margin-top:30px}}
.area{{flex:1;min-height:0;margin-top:36px;position:relative;display:flex;flex-direction:column}}
.area svg.fill{{flex:1;width:100%;min-height:0}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;margin-top:30px}}
.src{{font-size:21px;font-weight:500;color:#8b93a6;line-height:1.4;max-width:700px}}
.brand{{height:34px;flex:none}}
.legend{{display:flex;flex-wrap:wrap;gap:12px 30px;font-size:28px;font-weight:600;margin-bottom:18px}}
.lg{{display:flex;align-items:center;gap:10px}}.lg i{{width:26px;height:26px;border-radius:6px;display:inline-block}}
{extra_css}</style></head><body><div class="rings"></div><div class="wrap">
<div class="head"><div class="kick">{E(company)} business model</div><h1>{E(g["title"])}</h1>{sub}</div>{unit}
<div class="area">{inner}</div>
<div class="foot">{src}<img class="brand" src="incbusiness-logo-dark.png" alt=""></div></div></body></html>"""


def _affix(g, default_pre=""):
    """Prefix and suffix that put the unit right on every value ("Rs 22,624 cr", "$450 mn", "12%"), taken
    from "prefix"/"suffix" when the spec sets them, otherwise read from "unit" ("Rs crore", "$ million", "%")."""
    u = (g.get("unit") or "").lower()
    pre = "Rs " if ("rs" in u.split() or "rupee" in u or "\u20b9" in u) else ("$" if ("$" in u or "usd" in u or "dollar" in u) else default_pre)
    suf = next((v for k, v in (("lakh crore", " lakh cr"), ("lakh cr", " lakh cr"), ("crore", " cr"), ("million", " mn"), ("billion", " bn"),
                                ("lakh", " lakh"), ("%", "%"), ("per cent", "%")) if k in u), "")
    if not suf and "cr" in u.split():
        suf = " cr"
    return g.get("prefix", pre), g.get("suffix", suf)


def val(g, v, default_pre=""):
    pre, suf = _affix(g, default_pre)
    if pre.strip() == "Rs":
        pre = "\u20b9"  # the rupee sign keeps labels short enough to stay big on a phone
    return E(pre) + money(v) + E(suf)


def _fit(text, room, size):
    """Shrink a label's font so it fits in `room` px (Poppins bold is about 0.6 em per character)."""
    return int(max(20, min(size, room / (0.6 * max(len(text), 1)))))


def _palette(accent):
    return [accent, mix(accent, NAVY, .5), mix(accent, "#ffffff", .45), "#2f4b8f", mix(accent, "#ffffff", .7), "#9aa3b5", "#d9dee8"]


def _legend(series, accent):
    pal = _palette(accent)
    col = lambda s, n: LOSS if s.get("tone") == "loss" else pal[n % len(pal)]
    return ('<div class="legend">' + "".join(f'<span class="lg"><i style="background:{col(s, n)}"></i>{E(s["name"])}</span>'
                                             for n, s in enumerate(series)) + "</div>") if len(series) > 1 else ""


def _ring(items, accent, kind, center=None, note=None, g=None):
    g = g or {}
    """Donut or pie with the legend underneath, sized for a portrait page."""
    import math
    total = sum(i["value"] for i in items)
    pal = _palette(accent)
    cx = cy = 250
    svg, a0 = "", -math.pi / 2
    for n, it in enumerate(items):
        frac = it["value"] / total
        a1 = a0 + frac * 2 * math.pi
        if kind == "pie":
            x0, y0, x1, y1 = cx + 240 * math.cos(a0), cy + 240 * math.sin(a0), cx + 240 * math.cos(a1), cy + 240 * math.sin(a1)
            svg += f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A240,240 0 {1 if frac > .5 else 0} 1 {x1:.1f},{y1:.1f} Z" fill="{pal[n % len(pal)]}" stroke="#fff" stroke-width="5"/>'
            if frac >= .07:
                am = (a0 + a1) / 2
                svg += f'<text x="{cx + 150 * math.cos(am):.1f}" y="{cy + 150 * math.sin(am) + 11:.1f}" text-anchor="middle" font-size="40" font-weight="700" fill="#fff">{frac * 100:.0f}%</text>'
        else:
            r, circ = 205, 2 * math.pi * 205
            svg += (f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="none" stroke="{pal[n % len(pal)]}" stroke-width="68" '
                    f'stroke-dasharray="{circ * frac:.2f} {circ:.2f}" stroke-dashoffset="{-circ * (a0 + math.pi / 2) / (2 * math.pi):.2f}" transform="rotate(-90 {cx} {cy})"/>')
        a0 = a1
    mid = (f'<div class="ctr"><b>{E(center)}</b><span>{E(note or "total")}</span></div>' if kind == "donut" else "")
    legend = "".join(
        f'<div class="rl"><i style="background:{pal[n % len(pal)]}"></i><span class="rn">{E(it["label"])}</span>'
        f'<b>{val(g, it["value"])}</b><em>{it["value"] / total * 100:.1f}%</em></div>' for n, it in enumerate(items))
    css = """.rg{position:relative;width:500px;height:500px;margin:0 auto 30px}.rg svg{width:500px;height:500px}
.ctr{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.ctr b{font-size:44px;font-weight:700;letter-spacing:-1px}.ctr span{font-size:26px;color:#6b7385;font-weight:500}
.rl{display:flex;align-items:center;gap:18px;padding:16px 0;border-bottom:1.5px solid #e3e7ef;font-size:28px}
.rl i{width:28px;height:28px;border-radius:7px;flex:none}.rn{flex:1;font-weight:500;line-height:1.25}.rl b{font-weight:700;font-size:34px}
.rl em{font-style:normal;width:120px;font-size:28px;text-align:right;color:#6b7385;font-weight:600}"""
    return f'<div class="rg"><svg viewBox="0 0 500 500">{svg}</svg>{mid}</div><div>{legend}</div>', css


def donut(g, company, accent):
    inner, css = _ring(g["items"], accent, "donut", g.get("center", money(sum(i["value"] for i in g["items"]))), g.get("center_note"), g)
    return vpage(g, company, accent, inner, css, ring_height(g))


def pie(g, company, accent):
    inner, css = _ring(g["items"], accent, "pie", g=g)
    return vpage(g, company, accent, inner, css, ring_height(g))


def ring_height(g):
    """Room for the ring plus one legend row per item (long labels take two lines)."""
    rows = sum(2 if len(i["label"]) > 26 else 1 for i in g["items"])
    return max(HEIGHTS[g["type"]], 1180 + 62 * rows + (60 if len(g.get("title", "")) > 52 else 0))


def _columns(g, accent, stacked=False):
    """Vertical bars (grouped or stacked) drawn in a 936 x 760 viewBox that fills the chart area."""
    cats, series = g["categories"], g["series"]
    pal = _palette(accent)
    vw, vh, base, top = CW, 760, 680, 70
    h = base - top
    gw = vw / len(cats)
    pre = E(g.get("prefix", ""))
    svg = ""
    if stacked:
        totals = [sum((s["values"][i] or 0) for s in series) for i in range(len(cats))]
        vmax = max(totals) or 1
        bw = min(200, gw * .58)
        for ci, cat in enumerate(cats):
            x, y = ci * gw + (gw - bw) / 2, base
            for si, s in enumerate(series):
                v = s["values"][ci] or 0
                bh = h * v / vmax
                svg += f'<rect x="{x:.1f}" y="{y - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{pal[si % len(pal)]}" stroke="#fff" stroke-width="3"/>'
                if bh > 46:
                    svg += f'<text x="{x + bw / 2:.1f}" y="{y - bh / 2 + 10:.1f}" text-anchor="middle" font-size="{_fit(val(g, v), bw - 12, 28)}" font-weight="700" fill="#fff">{val(g, v)}</text>'
                y -= bh
            svg += f'<text x="{x + bw / 2:.1f}" y="{y - 18:.1f}" text-anchor="middle" font-size="{_fit(val(g, totals[ci]), gw - 10, 40)}" font-weight="700" fill="{NAVY}">{val(g, totals[ci])}</text>'
            svg += f'<text x="{x + bw / 2:.1f}" y="{base + 56}" text-anchor="middle" font-size="32" font-weight="600" fill="{MUTED}">{E(cat)}</text>'
    else:
        vmax = max(v for s in series for v in s["values"] if v is not None) or 1
        n = len(series)
        gap = 14
        bw = min(170, (gw * .78 - gap * (n - 1)) / n)
        for ci, cat in enumerate(cats):
            gx = ci * gw + (gw - (bw * n + gap * (n - 1))) / 2
            for si, s in enumerate(series):
                v = s["values"][ci]
                if v is None:
                    continue
                bh = h * v / vmax
                x = gx + si * (bw + gap)
                col = LOSS if s.get("tone") == "loss" else pal[si % len(pal)]
                svg += f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="12" fill="{col}"/>'
                svg += f'<text x="{x + bw / 2:.1f}" y="{base - bh - 16:.1f}" text-anchor="middle" font-size="{_fit(val(g, v), gw / n - 6, 40)}" font-weight="700" fill="{NAVY}">{val(g, v)}</text>'
            svg += f'<text x="{ci * gw + gw / 2:.1f}" y="{base + 56}" text-anchor="middle" font-size="32" font-weight="600" fill="{MUTED}">{E(cat)}</text>'
    svg += f'<line x1="0" x2="{vw}" y1="{base}" y2="{base}" stroke="#cfd5e2" stroke-width="3"/>'
    return _legend(series, accent) + f'<svg class="fill" viewBox="0 0 {vw} {vh}" preserveAspectRatio="xMidYMax meet">{svg}</svg>'


def bars(g, company, accent):
    """Columns when every value label fits over its own bar at a readable size; otherwise (several series,
    long labels like "₹11,110 cr") horizontal bars grouped by period, each value at the end of its bar."""
    cats, series = g["categories"], g["series"]
    slot = CW / len(cats) / len(series) - 6
    if all(_fit(val(g, v), slot, 40) >= 32 for s in series for v in s["values"] if v is not None):
        return vpage(g, company, accent, _columns(g, accent))
    pal = _palette(accent)
    vmax = max(v for s in series for v in s["values"] if v is not None) or 1
    blocks = ""
    for ci, cat in enumerate(cats):
        rows = ""
        for si, s in enumerate(series):
            v = s["values"][ci]
            if v is None:
                continue
            col = LOSS if s.get("tone") == "loss" else pal[si % len(pal)]
            rows += f'<div class="hg"><span class="ht"><i style="width:{max(v / vmax * 100, 1):.1f}%;background:{col}"></i></span><b>{val(g, v)}</b></div>'
        blocks += f'<div class="hc"><div class="hn">{E(cat)}</div>{rows}</div>'
    css = """.hgs{flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px}
.hn{font-size:30px;font-weight:700;color:#6b7385;margin-bottom:10px}.hg{display:flex;align-items:center;gap:18px;margin-bottom:12px}
.ht{flex:1;height:50px;background:#eef1f7;border-radius:12px;overflow:hidden}.ht i{display:block;height:100%;border-radius:12px}
.hg b{width:230px;text-align:right;font-size:38px;font-weight:700;white-space:nowrap}"""
    return vpage(g, company, accent, _legend(series, accent) + f'<div class="hgs">{blocks}</div>', css)


def stacked(g, company, accent):
    return vpage(g, company, accent, _columns(g, accent, stacked=True))


def line(g, company, accent):
    """Trend over time; "area": true shades under the first series."""
    cats, series = g["categories"], g["series"]
    pal = _palette(accent)
    vw, vh, base, top, pad = CW, 760, 680, 90, 60
    vmax = max(v for s in series for v in s["values"] if v is not None) or 1
    step = (vw - 2 * pad) / max(len(cats) - 1, 1)
    pre = E(g.get("prefix", ""))
    svg = "".join(f'<line x1="0" x2="{vw}" y1="{base - (base - top) * k / 4:.1f}" y2="{base - (base - top) * k / 4:.1f}" stroke="#e6e9f0" stroke-width="2"/>' for k in range(1, 5))
    for si, s in enumerate(series):
        col = LOSS if s.get("tone") == "loss" else pal[si % len(pal)]
        pts = [(pad + i * step, base - (base - top) * v / vmax, v) for i, v in enumerate(s["values"]) if v is not None]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
        if g.get("area") and si == 0:
            svg += f'<polygon points="{pts[0][0]:.1f},{base} {path} {pts[-1][0]:.1f},{base}" fill="{col}" opacity=".15"/>'
        svg += f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/>'
        for x, y, v in pts:
            svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="#fff" stroke="{col}" stroke-width="7"/>'
            fs = _fit(val(g, v), step * .95, 42)
            half = .6 * fs * len(val(g, v)) / 2
            svg += f'<text x="{min(max(x, half), vw - half):.1f}" y="{y - 32:.1f}" text-anchor="middle" font-size="{fs}" font-weight="700" fill="{NAVY}">{val(g, v)}</text>'
    for i, c in enumerate(cats):
        svg += f'<text x="{pad + i * step:.1f}" y="{base + 56}" text-anchor="middle" font-size="32" font-weight="600" fill="{MUTED}">{E(c)}</text>'
    svg += f'<line x1="0" x2="{vw}" y1="{base}" y2="{base}" stroke="#cfd5e2" stroke-width="3"/>'
    return vpage(g, company, accent, _legend(series, accent) + f'<svg class="fill" viewBox="0 0 {vw} {vh}" preserveAspectRatio="xMidYMax meet">{svg}</svg>')


ROW_CSS = """.rows{display:flex;flex-direction:column;justify-content:center;flex:1;gap:26px}
.row .top{display:flex;justify-content:space-between;align-items:baseline;gap:20px;font-size:31px;margin-bottom:10px}
.row .top span{font-weight:500;line-height:1.25}.row .top b{font-weight:700;white-space:nowrap;font-size:40px}
.track{position:relative;height:48px;background:#eef1f7;border-radius:12px;overflow:hidden}
.track i{position:absolute;top:0;bottom:0;border-radius:12px}"""


def _rows(items, fmt):
    return '<div class="rows">' + "".join(
        f'<div class="row"><div class="top"><span>{E(it["label"])}</span><b>{fmt(it)}</b></div>'
        f'<div class="track"><i style="left:{it["_l"]:.2f}%;width:{max(it["_w"], .8):.2f}%;background:{it["_c"]}"></i></div></div>'
        for it in items) + "</div>"


def hbars(g, company, accent):
    """Ranking: label and value above each full-width bar, largest first."""
    items = sorted(g["items"], key=lambda i: -i["value"]) if g.get("sort", True) else list(g["items"])
    vmax = max(i["value"] for i in items) or 1
    for n, it in enumerate(items):
        it.update(_l=0, _w=it["value"] / vmax * 100, _c=mix(accent, "#ffffff", min(n * .14, .55)))
    pre, suf = g.get("prefix", ""), g.get("suffix", "")
    return vpage(g, company, accent, _rows(items, lambda it: val(g, it["value"])), ROW_CSS)


def split(g, company, accent):
    """Costs per Rs 100 as bars, with a summary line underneath."""
    items = [dict(i) for i in g["items"]]
    vmax = max(max(i["value"] for i in items), g.get("earned", 100))
    for it in items:
        it.update(_l=0, _w=it["value"] / vmax * 100, _c=LOSS if it.get("tone") == "loss" else accent)
    css = ROW_CSS + f""".sum{{margin-top:30px;padding:24px 28px;border-radius:18px;background:#fff;border:2px solid {mix(accent, "#ffffff", .55)};font-size:31px;font-weight:600;line-height:1.35}}"""
    inner = _rows(items, lambda it: val(g, it["value"], "Rs ")) + (f'<div class="sum">{E(g["summary"])}</div>' if g.get("summary") else "")
    return vpage(g, company, accent, inner, css, 1350)


def waterfall(g, company, accent):
    """Start amount, each step adds (+) or takes away (-), ending at the result. One row each, every bar
    starting at the left edge with its length = the amount, so the sizes compare at a glance on a phone."""
    steps = [{"label": g["start"]["label"], "value": g["start"]["value"], "kind": "total"}] + [dict(s, kind="step") for s in g["steps"]]
    end = g["start"]["value"] + sum(s["value"] for s in g["steps"])
    steps.append({"label": g.get("end_label", "Result"), "value": end, "kind": "total"})
    vmax = max(abs(s["value"]) for s in steps) or 1
    pre = g.get("prefix", "")
    items = []
    for s in steps:
        neg = s["value"] < 0
        col = (accent if not neg else LOSS) if s["kind"] == "total" else (mix(accent, "#ffffff", .3) if not neg else mix(LOSS, "#ffffff", .2))
        sign = "-" if neg else ("+" if s["kind"] == "step" else "")
        items.append(dict(label=s["label"], _l=0, _w=abs(s["value"]) / vmax * 100, _c=col, _v=sign + val(g, abs(s["value"]))))
    css = ROW_CSS + ".rows{gap:20px}"
    return vpage(g, company, accent, _rows(items, lambda it: it["_v"]), css, HEIGHTS["waterfall"])


def kpis(g, company, accent):
    """3 to 6 big numbers as cards: {"value", "label", "note"}."""
    note = lambda it: "<em>" + E(it["note"]) + "</em>" if it.get("note") else ""
    cards = "".join(f'<div class="kp"><b>{E(it["value"])}</b><span>{E(it["label"])}</span>{note(it)}</div>' for it in g["items"])
    css = f""".kg{{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:22px;align-content:center}}
.kp{{background:#fff;border:2px solid #e1e5ee;border-radius:22px;padding:32px 30px 28px;border-top:8px solid {accent}}}
.kp b{{display:block;font-size:70px;font-weight:700;letter-spacing:-1.5px;line-height:1.05;color:{readable(accent)}}}
.kp span{{display:block;font-size:30px;font-weight:600;margin-top:12px;line-height:1.25}}.kp em{{display:block;font-style:normal;font-size:24px;color:{MUTED};margin-top:6px}}"""
    return vpage(g, company, accent, f'<div class="kg">{cards}</div>', css, 1350)


def fromto(g, company, accent):
    """Then and now, one card per metric: {"label", "from", "from_label", "to", "to_label", "change"}."""
    chg = lambda it: '<span class="fc">' + E(it["change"]) + "</span>" if it.get("change") else ""
    big = lambda t: f' style="font-size:{_fit(t, 370, 78)}px"'  # long values ("₹5.4 lakh cr") shrink to stay on one line
    cards = "".join(
        f'<div class="ft"><div class="fh"><span class="fl">{E(it["label"])}</span>{chg(it)}</div><div class="fr">'
        f'<div class="fv"><b class="a"{big(it["from"])}>{E(it["from"])}</b><span>{E(it["from_label"])}</span></div><div class="ar">&rarr;</div>'
        f'<div class="fv"><b class="z"{big(it["to"])}>{E(it["to"])}</b><span>{E(it["to_label"])}</span></div></div></div>' for it in g["items"])
    css = f""".fts{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px}}
.ft{{background:#fff;border:2px solid #e1e5ee;border-left:8px solid {accent};border-radius:20px;padding:28px 34px}}
.fh{{display:flex;justify-content:space-between;align-items:center}}.fl{{font-size:28px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:{MUTED}}}
.fr{{display:flex;align-items:center;gap:30px;margin-top:16px}}.fv b{{display:block;font-size:78px;font-weight:700;letter-spacing:-1.5px;line-height:1.05;white-space:nowrap}}
.fv .a{{color:#9aa3b5}}.fv .z{{color:{readable(accent)}}}.fv span{{font-size:25px;color:{MUTED};font-weight:600}}.ar{{font-size:56px;color:{accent}}}
.fc{{padding:8px 20px;border-radius:999px;background:{mix(accent, "#ffffff", .85)};color:{readable(accent)};font-weight:700;font-size:31px}}"""
    return vpage(g, company, accent, f'<div class="fts">{cards}</div>', css, 1350)


def canvas(g, company, accent):
    """The nine blocks, two per row (the ninth full width), numbered in reading order."""
    b = g["blocks"]
    order = [("segments", "Customer segments"), ("value", "Value proposition"), ("channels", "Channels"),
             ("relationships", "Customer relationships"), ("revenue", "Revenue streams"), ("resources", "Key resources"),
             ("activities", "Key activities"), ("partners", "Key partners"), ("costs", "Cost structure")]
    boxes = "".join(
        f'<div class="bx"><div class="bt"><span>{i}</span>{E(label)}</div>'
        f'<ul>{"".join(f"<li>{E(x)}</li>" for x in b.get(key, []))}</ul></div>'
        for i, (key, label) in enumerate(order, 1))
    css = f""".cv{{flex:1;display:grid;gap:16px;grid-template-columns:1fr 1fr;align-content:start}}.cv .bx:last-child{{grid-column:1/3}}
.bx{{background:#fff;border:2px solid #e1e5ee;border-radius:18px;padding:20px 22px 12px}}
.bt{{display:flex;align-items:center;gap:10px;font-size:21px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:{readable(accent)};margin-bottom:10px}}
.bt span{{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:{readable(accent)};color:#fff;font-size:16px;letter-spacing:0;flex:none}}
ul{{padding-left:24px}}li{{font-size:24px;line-height:1.35;font-weight:500;margin-bottom:8px}}"""
    return vpage(g, company, accent, f'<div class="cv">{boxes}</div>', css, None)



def timeline(g, company, accent):
    """Vertical timeline: dates down the left, events as cards, latest last."""
    rows = "".join(f'<div class="ti"><span class="dot"></span><div class="tc"><b>{E(it["when"])}</b><p>{E(it["what"])}</p></div></div>' for it in g["items"])
    css = f""".tl{{flex:1;position:relative;display:flex;flex-direction:column;justify-content:space-around;padding-left:56px}}
.tl:before{{content:"";position:absolute;left:17px;top:20px;bottom:20px;width:6px;border-radius:3px;background:linear-gradient({accent},{mix(accent, "#ffffff", .5)})}}
.ti{{position:relative}}.dot{{position:absolute;left:-54px;top:50%;margin-top:-17px;width:34px;height:34px;border-radius:50%;background:#fff;border:8px solid {accent}}}
.tc{{background:#fff;border:2px solid #e1e5ee;border-radius:18px;padding:18px 26px}}.tc b{{display:block;font-size:32px;color:{readable(accent)}}}
.tc p{{font-size:28px;line-height:1.35;font-weight:500;margin-top:4px}}"""
    return vpage(g, company, accent, f'<div class="tl">{rows}</div>', css, HEIGHTS["timeline"])


def bullets(g, company, accent):
    """Numbered points, big type: key takeaways, competitors, challenges. {"items": ["...", ...]}"""
    rows = "".join(f'<div class="bl"><span>{i}</span><p>{E(t)}</p></div>' for i, t in enumerate(g["items"], 1))
    css = f""".bls{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:20px}}
.bl{{display:flex;gap:22px;align-items:flex-start;background:#fff;border:2px solid #e1e5ee;border-radius:20px;padding:24px 28px}}
.bl span{{flex:none;width:52px;height:52px;border-radius:50%;background:{readable(accent)};color:#fff;font-size:26px;font-weight:700;display:grid;place-items:center}}
.bl p{{font-size:31px;font-weight:500;line-height:1.32}}"""
    return vpage(g, company, accent, f'<div class="bls">{rows}</div>', css, None)


def glance(g, company, accent):
    """At a glance: one row per fact, label above value. {"rows": [{"label": "Founders", "value": "..."}]}"""
    rows = "".join(f'<div class="gr"><span>{E(r["label"])}</span><b>{E(r["value"])}</b></div>' for r in g["rows"])
    css = f""".grs{{flex:1;display:flex;flex-direction:column;justify-content:center;background:#fff;border:2px solid #e1e5ee;border-radius:22px;padding:8px 30px}}
.gr{{padding:16px 0;border-bottom:2px solid #eef1f7}}.gr:last-child{{border-bottom:0}}
.gr span{{display:block;font-size:21px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{readable(accent)}}}
.gr b{{display:block;font-size:30px;font-weight:600;line-height:1.3;margin-top:4px}}"""
    return vpage(g, company, accent, f'<div class="grs">{rows}</div>', css, None)


def flow(g, company, accent):
    """How it works, step by step with arrows: {"steps": [{"title": "...", "text": "..."}]}"""
    steps = "".join(f'<div class="fs"><span>{i}</span><div><b>{E(st["title"])}</b><p>{E(st.get("text", ""))}</p></div></div>'
                    + ('<div class="fa">&darr;</div>' if i < len(g["steps"]) else "") for i, st in enumerate(g["steps"], 1))
    css = f""".fl2{{flex:1;display:flex;flex-direction:column;justify-content:center}}
.fs{{display:flex;gap:22px;align-items:center;background:#fff;border:2px solid #e1e5ee;border-left:8px solid {accent};border-radius:20px;padding:22px 28px}}
.fs span{{flex:none;width:56px;height:56px;border-radius:16px;background:{mix(accent, "#ffffff", .85)};color:{readable(accent)};font-size:28px;font-weight:700;display:grid;place-items:center}}
.fs b{{display:block;font-size:32px;font-weight:700;line-height:1.2}}.fs p{{font-size:25px;font-weight:500;color:#4d5568;line-height:1.3;margin-top:4px}}
.fa{{text-align:center;font-size:40px;line-height:1;color:{accent};margin:6px 0}}"""
    return vpage(g, company, accent, f'<div class="fl2">{steps}</div>', css, None)


def summary(g, company, accent):
    """A short summary in large type (the conclusion): {"paragraphs": ["...", "..."]}"""
    paras = "".join(f"<p>{E(t)}</p>" for t in g["paragraphs"])
    css = f""".sm{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:26px;border-left:10px solid {accent};padding-left:34px}}
.sm p{{font-size:34px;font-weight:500;line-height:1.42}}.sm p:first-child{{font-weight:600}}"""
    return vpage(g, company, accent, f'<div class="sm">{paras}</div>', css, None)


RENDER = {"donut": donut, "bars": bars, "split": split, "canvas": canvas, "timeline": timeline,
          "line": line, "pie": pie, "stacked": stacked, "waterfall": waterfall, "kpis": kpis, "hbars": hbars, "fromto": fromto,
          "bullets": bullets, "glance": glance, "flow": flow, "summary": summary}
HEIGHTS = {k: 1350 for k in RENDER} | {"canvas": 1800, "timeline": 1550, "waterfall": 1600, "donut": 1500, "pie": 1500}


def measure_height(chrome, page_path):
    """Full height of a page that grows with its text: Chrome writes document height into the DOM, we read it back."""
    import subprocess
    probe = page_path.replace(".html", ".probe.html")
    html_ = open(page_path, encoding="utf-8").read().replace(
        "</body>", '<script>window.onload=function(){document.body.setAttribute("data-h",Math.ceil(document.documentElement.scrollHeight));}</script></body>')
    open(probe, "w", encoding="utf-8").write(html_)
    out = subprocess.run([chrome, "--headless=new", "--disable-gpu", f"--window-size={W},1350", "--virtual-time-budget=3000",
                          "--dump-dom", "file://" + probe], capture_output=True, text=True, timeout=60).stdout
    m = re.search(r'data-h="(\d+)"', out)
    return max(MIN_AUTO, int(m.group(1))) if m else 3000  # unmeasured: render tall, trim_blank() cuts the rest


def _jpeg(png, jpg, quality=88):
    """PNG to JPEG at the size it was rendered (shoot.to_jpeg caps the longest side, which would shrink portrait charts)."""
    try:
        from PIL import Image
        Image.open(png).convert("RGB").save(jpg, "JPEG", quality=quality)
    except ImportError:
        import subprocess
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality), png, "--out", jpg],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


AUTO_HEIGHT = {"bullets", "glance", "flow", "summary", "canvas"}  # sized to their text by measure_height(), then trim_blank()


def trim_blank(png):
    """Cuts the plain white strip below a text page's design (a height measured too tall, or a failed
    measurement), so no image ends in empty space. The design itself always has a tinted background."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    px = im.load()
    w, h = im.size
    bottom = h
    while bottom > MIN_AUTO and all(px[x, bottom - 1] == (255, 255, 255) for x in range(0, w, 6)):
        bottom -= 1
    if bottom < h:
        im.crop((0, 0, w, bottom)).save(png)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    if not spec.get("logo"):
        sys.exit("No logo: a business model cover needs the company's official logo, from its own site.")
    out = os.path.abspath(sys.argv[2])
    work = os.path.join(out, "_html")
    fetch_assets(work)
    logo = "logo" + os.path.splitext(spec["logo"])[1]
    shutil.copy(spec["logo"], os.path.join(work, logo))
    # Every image takes the company's own colour: "color" if the spec sets it, else read from the logo
    accent = spec.get("color") or logo_color(spec["logo"]) or "#2f4b8f"
    print("Theme colour", accent)
    chrome = find_chrome()
    jobs = [("cover", cover(spec, accent, logo), 1200, 630)]
    for g in spec.get("graphics", []):
        jobs.append((g["file"], RENDER[g["type"]](g, spec["company"], accent), W,
                     ring_height(g) if g["type"] in ("donut", "pie") else
                     None if g["type"] in AUTO_HEIGHT else HEIGHTS[g["type"]]))
    auto = {g["file"] for g in spec.get("graphics", []) if g["type"] in AUTO_HEIGHT}
    for name, doc, width, height in jobs:
        page_path = os.path.join(work, name + ".html")
        open(page_path, "w", encoding="utf-8").write(doc)
        png = os.path.join(work, name + ".png")
        if height is None:
            height = measure_height(chrome, page_path)
        if not screenshot(chrome, "file://" + page_path, png, width=width, height=height, wait_ms=3000):
            sys.exit(f"Render failed: {name}")
        if name in auto:
            trim_blank(png)
        _jpeg(png, os.path.join(out, name + ".jpg"))
        print("OK   ", os.path.join(out, name + ".jpg"))


if __name__ == "__main__":
    main()
