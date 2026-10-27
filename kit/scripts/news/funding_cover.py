#!/usr/bin/env python3
"""Render a funding-news cover (1200x630 JPG): light, premium, logo-led, no numbers.

Usage:
    python3 scripts/news/funding_cover.py cover.json OUT.jpg

cover.json:
    {"company": "Zepto", "label": "Funding News", "logo": "logos/zepto.svg", "tint": 3,
     "founders": [{"name": "Aadit Palicha", "photo": "photos/aadit.webp"}, ...]}

"founders" (optional, up to 3) are photos from the company's own website, press kit
or official press release, never from news outlets. "photo" (optional) is the
company's own picture of its office, team, store or product, from the same kind of
source; it's used when there's no logo and no founder photo. With founders, the logo card
moves left and the founders sit on the right in gold-ringed circles, named below.

The company's own logo, taken from its official website (never from a news site),
sits large in a white card in the middle of a soft ivory-to-blue background with
fine gold rings; a small gold label ("label": "Funding News", "Tech News", ...) and the IncBusiness logo frame
it. No amounts, rounds or other figures on the image. Without a verified logo, the
script refuses to render: no text-only covers (never initials or a made-up mark either).
Fonts are the site's own Poppins (downloaded once from incbusiness.in).
"""
import html
import json
import os
import re
import shutil
import sys
import urllib.request

# shoot.py lives in scripts/ai-tools in the repo, or next to this file when the routine downloads both
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_here, os.path.join(_here, "..", "ai-tools")]
from shoot import find_chrome, screenshot, to_jpeg  # noqa: E402

SITE = os.environ.get("SITE_URL", "https://incbusiness.in").rstrip("/")


def fetch_assets(folder):
    os.makedirs(folder, exist_ok=True)
    files = {f"poppins-{w}.woff2": f"/vendor/poppins/poppins-{w}-latin.woff2" for w in (500, 600, 700)}
    files["incbusiness-logo-dark.png"] = "/images/brand/incbusiness-logo-dark.png"
    for name, path in files.items():
        dest = os.path.join(folder, name)
        if not os.path.exists(dest):
            req = urllib.request.Request(SITE + path, headers={"User-Agent": "INCBusiness-NewsAgent/1.0"})
            open(dest, "wb").write(urllib.request.urlopen(req, timeout=30).read())


def image_size(path):
    """(width, height) of a PNG/SVG/JPG, or (0, 0) if unknown."""
    head = open(path, "rb").read(4096)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    if path.endswith(".svg"):
        txt = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', txt)
        return (float(m.group(1)), float(m.group(2))) if m else (0, 0)
    try:
        from PIL import Image
        return Image.open(path).size
    except Exception:
        return 0, 0


# Soft background tints, one per post so neighbouring news cards look different
TINTS = [("#fdf3f5", "#f6e1e8"), ("#f2f7ff", "#e1ebfa"), ("#fff6ee", "#fbe6d3"),
         ("#f5f2fe", "#e6e0fb"), ("#effaf4", "#d9f2e5"), ("#eef9fb", "#d6eff3")]


def tint_for(company):
    """Same company -> same tint every time; different companies spread across the six."""
    return TINTS[sum(ord(c) for c in company.lower()) % len(TINTS)]


def page(d, folder):
    # "tint": 0-5 picks a tint in order (the routine passes the post count, so neighbours differ);
    # without it the company name picks one
    mid, edge = TINTS[d["tint"] % len(TINTS)] if isinstance(d.get("tint"), int) else tint_for(d["company"])
    font = "".join(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(poppins-{w}.woff2)}}" for w in (500, 600, 700))
    logo = d.get("logo")
    if logo:
        name = "logo-" + os.path.basename(logo)
        shutil.copy(logo, os.path.join(folder, name))
        w, h = image_size(logo)
        shape = "wide" if (w and h and w / h > 1.6) else "square"
        mark = f'<div class="card {shape}"><img src="{html.escape(name)}" alt=""></div>'
    else:
        size = 84 if len(d["company"]) <= 14 else (68 if len(d["company"]) <= 22 else 54)
        mark = f'<div class="card wide name" style="font-size:{size}px">{html.escape(d["company"])}</div>'
    if not logo and d.get("photo"):
        pic = "company" + os.path.splitext(d["photo"])[1]
        shutil.copy(d["photo"], os.path.join(folder, pic))
        mark = (f'<figure class="photo"><img src="{pic}" alt="">'
                f'<figcaption>{html.escape(d["company"])}</figcaption></figure>')
    founders = d.get("founders") or []
    if founders:
        people = ""
        for i, f in enumerate(founders[:3]):
            pic = f"founder-{i}" + os.path.splitext(f["photo"])[1]
            shutil.copy(f["photo"], os.path.join(folder, pic))
            people += f'<figure><img src="{pic}" alt=""><figcaption>{html.escape(f["name"])}</figcaption></figure>'
        mark = f'<div class="split">{mark}<div class="people">{people}</div></div>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;overflow:hidden;font-family:Poppins,sans-serif;position:relative;
background:radial-gradient(circle at 50% 50%,#ffffff 0%,{mid} 42%,{edge} 100%)}}
.rings{{position:absolute;left:50%;top:50%;width:1500px;height:1500px;transform:translate(-50%,-50%);border-radius:50%;
background:repeating-radial-gradient(circle,transparent 0 58px,rgba(201,151,26,.20) 58px 59.5px)}}
.glow{{position:absolute;left:50%;top:50%;width:760px;height:460px;transform:translate(-50%,-50%);border-radius:50%;
background:radial-gradient(closest-side,rgba(255,255,255,.95),rgba(255,255,255,0))}}
.card{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:#fff;display:flex;align-items:center;justify-content:center;
border:1.5px solid rgba(201,151,26,.55);box-shadow:0 30px 70px rgba(22,33,61,.12),0 6px 18px rgba(22,33,61,.06)}}
.card.square{{width:330px;height:330px;border-radius:50%}}
.card.square img{{max-width:60%;max-height:60%}}
.card.wide{{width:620px;height:290px;border-radius:36px}}
.card.wide img{{max-width:76%;max-height:56%}}
.card.name{{color:#16213d;font-weight:700;letter-spacing:-1px;text-align:center;padding:0 40px;line-height:1.1}}
.tag{{position:absolute;left:50%;top:56px;transform:translateX(-50%);display:inline-flex;align-items:center;gap:10px;
color:#a57a10;font-size:16px;font-weight:600;letter-spacing:.22em}}
.tag:before,.tag:after{{content:"";width:46px;height:1.5px;background:linear-gradient(90deg,transparent,#c9971a)}}
.tag:after{{transform:scaleX(-1)}}
.split{{position:absolute;inset:110px 60px 100px;display:flex;align-items:center;justify-content:center;gap:56px}}
.split .card{{position:static;transform:none;flex-shrink:0}}
.split .card.wide{{width:400px;height:200px}}
.split .card.square{{width:250px;height:250px}}
.people{{display:flex;gap:30px}}
.people figure{{margin:0;text-align:center}}
.people img{{width:200px;height:200px;border-radius:50%;object-fit:cover;background:#f1f1f1;
border:5px solid #fff;box-shadow:0 0 0 2px rgba(201,151,26,.7),0 22px 44px rgba(22,33,61,.14)}}
.people figcaption{{margin-top:16px;font-size:20px;font-weight:600;color:#16213d}}
.photo{{position:absolute;left:50%;top:50%;transform:translate(-50%,-52%);margin:0;text-align:center}}
.photo img{{display:block;width:520px;height:290px;object-fit:cover;border-radius:24px;border:6px solid #fff;
box-shadow:0 0 0 1.5px rgba(201,151,26,.55),0 30px 70px rgba(22,33,61,.14)}}
.photo figcaption{{margin-top:18px;font-size:26px;font-weight:700;color:#16213d;letter-spacing:-.3px}}
.brand{{position:absolute;left:50%;bottom:46px;transform:translateX(-50%);height:26px}}
</style></head><body>
<div class="rings"></div><div class="glow"></div>
<div class="tag">{html.escape(d.get("label") or "Funding News").upper()}</div>
{mark}
<img class="brand" src="incbusiness-logo-dark.png" alt="">
</body></html>"""


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    # No text-only covers: the owner wants the real logo (or the company's own photo) every time
    if not data.get("logo") and not data.get("photo"):
        sys.exit("No logo: a cover needs the company's official logo (or its own photo). Try every way in the "
                 "playbook's cover step; if none works, drop this story and take the next candidate.")
    out = os.path.abspath(sys.argv[2])
    folder = os.path.join(os.path.dirname(out), "cover-assets")
    fetch_assets(folder)
    page_path = os.path.join(folder, os.path.splitext(os.path.basename(out))[0] + ".html")
    open(page_path, "w", encoding="utf-8").write(page(data, folder))
    png = os.path.splitext(out)[0] + ".png"
    if not screenshot(find_chrome(), "file://" + page_path, png, width=1200, height=630, wait_ms=4000):
        sys.exit("Cover render failed.")
    to_jpeg(png, out, width=1200, quality=88)
    os.remove(png)
    print(f"OK    {out} {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
