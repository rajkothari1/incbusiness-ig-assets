"""Build a 9:16 "Top 10 news in 60s" reel from the anchor photo, a voice track and headlines.

Usage: python3 reels/build_reel.py reels/2026-10-11
The day folder needs: voice.mp3 and segments.json
  segments.json = {"date": "11 OCT 2026", "items": [{"start": 6.7, "end": 13.07, "text": "..."}, ...]}
  item 0 is the intro, the last item is the outro; everything between is numbered 1..10.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
FPS = 30
ACCENT = (255, 184, 28)
NAVY = (12, 20, 46)
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def top_bar(draw, date):
    draw.rectangle([0, 0, W, 150], fill=(*NAVY, 235))
    draw.rectangle([0, 150, W, 158], fill=ACCENT)
    draw.text((48, 38), "TOP 10 BUSINESS NEWS", font=font(FONT_BOLD, 48), fill="white")
    draw.text((48, 98), f"{date}  ·  60 SECONDS", font=font(FONT_SEMI, 30), fill=ACCENT)
    # Instagram asks for realistic AI media to be labelled; keep a visible tag on screen.
    tag = "AI ANCHOR"
    f = font(FONT_SEMI, 24)
    tw = draw.textlength(tag, font=f)
    draw.rounded_rectangle([W - tw - 80, 52, W - 40, 98], radius=10, outline="white", width=2)
    draw.text((W - tw - 60, 60), tag, font=f, fill="white")


def lower_third(draw, number, text):
    # Panel sits low enough to cover the image generator's corner watermark.
    y0 = 1450
    draw.rectangle([0, y0, W, H], fill=(*NAVY, 240))
    draw.rectangle([0, y0, W, y0 + 8], fill=ACCENT)
    x = 48
    if number is not None:
        draw.rounded_rectangle([48, y0 + 50, 208, y0 + 210], radius=24, fill=ACCENT)
        num = str(number)
        nf = font(FONT_BOLD, 100)
        nw = draw.textlength(num, font=nf)
        draw.text((128 - nw / 2, y0 + 68), num, font=nf, fill=NAVY)
        x = 240
    tf = font(FONT_BOLD, 54)
    lines = wrap(draw, text, tf, W - x - 48)
    y = y0 + 60
    for line in lines[:4]:
        draw.text((x, y), line, font=tf, fill="white")
        y += 70
    draw.text((48, H - 90), "@incbusiness", font=font(FONT_SEMI, 32), fill=ACCENT)


def render_overlays(day, data, out_dir):
    items = data["items"]
    paths = []
    for i, item in enumerate(items):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        top_bar(d, data["date"])
        number = None if i in (0, len(items) - 1) else i
        lower_third(d, number, item["text"])
        p = out_dir / f"ov_{i:02d}.png"
        img.save(p)
        paths.append(p)
    return paths


def main():
    day = Path(sys.argv[1]).resolve()
    data = json.loads((day / "segments.json").read_text())
    build = day / "build"
    build.mkdir(exist_ok=True)
    overlays = render_overlays(day, data, build)
    voice = day / "voice.mp3"
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voice)]))
    frames = int(dur * FPS) + FPS

    inputs = ["-loop", "1", "-i", str(ROOT / "anchor" / "anchor.jpg")]
    for p in overlays:
        inputs += ["-i", str(p)]
    inputs += ["-i", str(voice)]

    # Slow push-in on the anchor so the frame never feels static.
    chain = [
        f"[0:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
        f"zoompan=z='min(1+on/{frames}*0.12,1.12)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom*0.35)':"
        f"d={frames}:s={W}x{H}:fps={FPS}[base]"
    ]
    last = "base"
    for i, item in enumerate(data["items"]):
        nxt = f"v{i}"
        chain.append(f"[{last}][{i + 1}:v]overlay=0:0:enable='between(t,{item['start']},{item['end']})'[{nxt}]")
        last = nxt
    # Progress bar across the bottom edge.
    chain.append(f"[{last}]drawbox=x=0:y={H - 12}:w='{W}*t/{dur:.2f}':h=12:color=0xFFB81C:t=fill[out]")

    out = day / "reel.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
         "-map", "[out]", "-map", f"{len(overlays) + 1}:a", "-t", f"{dur:.2f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)],
        check=True)
    print(out)


if __name__ == "__main__":
    main()
