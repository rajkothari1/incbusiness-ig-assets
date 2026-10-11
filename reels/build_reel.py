"""Build a 9:16 "Top N news in 60s" reel: anchor intro/outro, one card per story,
punch-zoom cuts, word-by-word captions, news music bed (ducked under the voice) and whooshes.

Usage: python3 reels/build_reel.py reels/2026-10-11
The day folder needs voice.mp3 and segments.json (from make_voice.py). Optional intro.mp4 and
outro.mp4 are lip-synced anchor clips (Higgsfield MiniMax H3) played for the first and last line;
without them the anchor photo gets a slow push-in.
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from check_sync import MIN_MATCH, find_offset

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
FPS = 30
SR = 44100
ACCENT = (255, 184, 28)
NAVY = (12, 20, 46)
WHITE = (255, 255, 255)
CARD_W = 760
# Instagram draws the username/"AI content" label over the top ~150 px and the caption, buttons
# and audio row over the bottom ~440 px (plus the right-hand button column), so everything we
# need people to read stays between these lines.
SAFE_TOP = 170
SAFE_BOTTOM = H - 440
SAFE_SIDE = 150
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
_fonts = {}


def font(weight, size):
    key = (weight, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(FONT_DIR / f"Inter-{weight}.otf"), size)
    return _fonts[key]


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def cover(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def ken_burns(img, p, zoom=0.10, drift=(0, 0)):
    """img is pre-scaled to (W, H) * (1 + zoom); crop a window that shrinks as p goes 0 -> 1."""
    z = 1 + zoom * (1 - p)
    cw, ch = img.width / z, img.height / z
    cx = min(max(img.width / 2 + drift[0] * p, cw / 2), img.width - cw / 2)
    cy = min(max(img.height / 2 + drift[1] * p, ch / 2), img.height - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=box)


def gradient_overlay():
    g = np.zeros((H, W, 4), dtype=np.uint8)
    g[..., :3] = NAVY
    ys = np.linspace(0, 1, H)
    alpha = 120 + 110 * (np.abs(ys - 0.42) / 0.58) ** 1.2
    g[..., 3] = np.clip(alpha, 0, 235)[:, None].astype(np.uint8)
    return Image.fromarray(g, "RGBA")


def text_image(text, fnt, fill, stroke=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - l, 4 - t), text, font=fnt, fill=fill, stroke_width=stroke,
                             stroke_fill=(0, 0, 0, 160))
    return img


def fit_font(text, weight, size, max_w):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while size > 30 and d.textlength(text, font=font(weight, size)) > max_w:
        size -= 4
    return font(weight, size)


def paste_scaled(frame, img, cx, cy, scale, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.BILINEAR)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: round(v * alpha))
        im.putalpha(a)
    frame.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


class Reel:
    def __init__(self, day):
        self.day = day
        self.data = json.loads((day / "segments.json").read_text())
        self.voice = day / "voice.mp3"
        self.dur = float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(self.voice)]))
        anchor = Image.open(ROOT / "anchor" / "anchor.jpg").convert("RGB")
        # Drop the bottom strip so the image generator's corner watermark never shows.
        anchor = anchor.crop((0, 0, anchor.width, int(anchor.height * 0.88)))
        self.anchor_full = cover(anchor, int(W * 1.12), int(H * 1.12))
        self.shade = gradient_overlay()
        self.bgs = {}
        for item in self.data["items"]:
            if "card" in item:
                card = Image.open(self.day / "cards" / item["card"]).convert("RGB")
                item["card_img"] = card.resize((CARD_W, round(card.height * CARD_W / card.width)), Image.LANCZOS)
                # Blurred, darkened copy of the card fills the frame behind it.
                blur = cover(card, int(W * 1.14), int(H * 1.14)).filter(ImageFilter.GaussianBlur(40))
                item["bg_img"] = Image.blend(blur, Image.new("RGB", blur.size, NAVY), 0.55)
            else:
                if item["bg"] not in self.bgs:
                    img = Image.open(ROOT / "backgrounds" / item["bg"]).convert("RGB")
                    self.bgs[item["bg"]] = cover(img, int(W * 1.14), int(H * 1.14))
                item["bg_img"] = self.bgs[item["bg"]]
        self.prepare_cards()
        self.intro_frames = self.extract_clip("intro.mp4", "intro_frames", self.data["intro"])
        self.outro_frames = self.extract_clip("outro.mp4", "outro_frames", self.data["outro"])

    def extract_clip(self, name, folder, seg):
        """Optional lip-synced anchor clip (<day>/intro.mp4 or outro.mp4) for the matching line.

        The clip's own audio is matched against our voice line so any silent lead-in the
        generator added is skipped; a clip that is not speaking our line stops the build.
        """
        clip = self.day / name
        if not clip.exists():
            return []
        lead, match = find_offset(clip, self.voice, seg["start"], min(seg["end"], self.dur))
        if lead is None or match < MIN_MATCH:
            raise SystemExit(f"{name}: lips do not match our voice line (match {match:.2f}); regenerate it")
        print(f"{name}: skipping {lead:.2f}s lead-in, match {match:.2f}")
        out = self.day / "build" / folder
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.jpg"):
            old.unlink()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(lead, 0):.3f}", "-i", str(clip), "-vf",
                        f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                        "-q:v", "2", str(out / "%05d.jpg")], check=True)
        return sorted(out.glob("*.jpg"))

    def make_badge(self, n):
        size = 150
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, size - 1, size - 1], fill=ACCENT, outline=WHITE, width=6)
        f = font("Black", 84)
        tw = d.textlength(str(n), font=f)
        d.text(((size - tw) / 2, 18), str(n), font=f, fill=NAVY)
        return img

    def prepare_cards(self):
        for i, item in enumerate(self.data["items"]):
            item["num_img"] = text_image(f"#{i + 1}", font("Black", 150), ACCENT)
            item["badge_img"] = self.make_badge(item.get("num", i + 1))
            item["words"] = item["caption"].split()
            if "card" in item:
                continue
            item["name_img"] = text_image(item["name"], fit_font(item["name"], "Black", 104, W - 120), WHITE)
            item["stat_img"] = text_image(item["stat"], fit_font(item["stat"], "Black", 200, W - 100), ACCENT)
            item["label_img"] = text_image(item["label"], fit_font(item["label"], "SemiBold", 52, W - 120), WHITE)
        for key in ("intro", "outro"):
            seg = self.data[key]
            seg["title_img"] = text_image(seg["title"], fit_font(seg["title"], "Black", 200, W - 2 * SAFE_SIDE), ACCENT)
            seg["sub_img"] = text_image(seg["subtitle"], fit_font(seg["subtitle"], "Black", 96, W - 2 * SAFE_SIDE), WHITE)
            seg["tag_img"] = text_image(seg["tagline"], fit_font(seg["tagline"], "SemiBold", 50, W - 2 * SAFE_SIDE), WHITE)

    # ---- frame rendering ----
    def segment_at(self, t):
        for item in self.data["items"]:
            if item["start"] <= t < item["end"]:
                return "item", item
        if t < self.data["items"][0]["start"]:
            return "intro", self.data["intro"]
        return "outro", self.data["outro"]

    def draw_progress(self, frame, t):
        d = ImageDraw.Draw(frame)
        n = len(self.data["items"])
        gap, x0, y = 8, SAFE_SIDE - 60, SAFE_TOP - 30
        seg_w = (W - 2 * x0 - gap * (n - 1)) / n
        for i, item in enumerate(self.data["items"]):
            x = x0 + i * (seg_w + gap)
            d.rounded_rectangle([x, y, x + seg_w, y + 12], radius=6, fill=(255, 255, 255, 70))
            p = (t - item["start"]) / (item["end"] - item["start"])
            p = min(max(p, 0), 1)
            if p > 0:
                d.rounded_rectangle([x, y, x + max(12, seg_w * p), y + 12], radius=6, fill=ACCENT)

    def draw_caption(self, frame, item, t, y=1330):
        words = item["words"]
        span = item["end"] - item["start"]
        reveal = min(span * 0.65, 0.42 * len(words))
        t0 = item["start"] + 0.35
        shown = int((t - t0) / reveal * len(words)) + 1 if t >= t0 else 0
        shown = min(shown, len(words))
        if shown == 0:
            return
        d = ImageDraw.Draw(frame)
        f = font("ExtraBold", 56)
        lines, cur, cur_w = [], [], 0
        space = d.textlength(" ", font=f)
        for idx, w in enumerate(words):
            ww = d.textlength(w, font=f)
            if cur and cur_w + space + ww > W - 2 * SAFE_SIDE:
                lines.append(cur)
                cur, cur_w = [], 0
            cur.append((idx, w, ww))
            cur_w += (space if len(cur) > 1 else 0) + ww
        lines.append(cur)
        for line in lines:
            lw = sum(ww for _, _, ww in line) + space * (len(line) - 1)
            x = (W - lw) / 2
            for idx, w, ww in line:
                if idx < shown:
                    pop = ease_back((t - (t0 + idx * reveal / len(words))) / 0.18)
                    if idx == shown - 1:
                        d.rounded_rectangle([x - 10, y - 6, x + ww + 10, y + 72], radius=12, fill=ACCENT)
                        colour = NAVY
                    else:
                        colour = WHITE
                    dy = (1 - pop) * 30
                    d.text((x, y + dy), w, font=f, fill=colour, stroke_width=0 if colour == NAVY else 3,
                           stroke_fill=(0, 0, 0))
                x += ww + space
            y += 84

    def render_card(self, item, t):
        local = t - item["start"]
        p = local / (item["end"] - item["start"])
        frame = ken_burns(item["bg_img"], p, zoom=0.12, drift=(20, -20)).convert("RGBA")
        card = item["card_img"]
        # Card slides up and punches in on the cut, then keeps a slow push-in.
        scale = (1 + 0.10 * (1 - ease_out(local / 0.35))) * (1 + 0.035 * p)
        cy = SAFE_TOP + 70 + card.height / 2 + 140 * (1 - ease_out(local / 0.35))
        cw, ch = round(card.width * scale), round(card.height * scale)
        shadow = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([40, 50, cw + 40, ch + 50], radius=30, fill=(0, 0, 0, 150))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        frame.alpha_composite(shadow, (round(W / 2 - cw / 2 - 40), round(cy - ch / 2 - 40)))
        frame.paste(card.resize((cw, ch), Image.BILINEAR), (round(W / 2 - cw / 2), round(cy - ch / 2)))
        paste_scaled(frame, item["badge_img"], W / 2 - card.width / 2 + 20, SAFE_TOP + 90,
                     0.8 * ease_back((local - 0.1) / 0.35))
        self.draw_caption(frame, item, t, y=SAFE_TOP + 70 + card.height + 40)
        return frame, local

    def render_item(self, item, t):
        if "card" in item:
            return self.render_card(item, t)
        local = t - item["start"]
        span = item["end"] - item["start"]
        p = local / span
        bg = ken_burns(item["bg_img"], p, zoom=0.12, drift=(30, -20))
        frame = bg.convert("RGBA")
        frame.alpha_composite(self.shade)
        # Punch-in on the cut.
        punch = 1 + 0.12 * (1 - ease_out(local / 0.3))
        paste_scaled(frame, item["num_img"], 150 - 120 * (1 - ease_out(local / 0.35)), 300, 1.0)
        paste_scaled(frame, item["name_img"], W / 2, 520, punch, ease_out(local / 0.2))
        paste_scaled(frame, item["stat_img"], W / 2, 760, ease_back((local - 0.15) / 0.4))
        paste_scaled(frame, item["label_img"], W / 2, 960, 1.0, ease_out((local - 0.45) / 0.3))
        d = ImageDraw.Draw(frame)
        bar = ease_out((local - 0.3) / 0.4)
        d.rectangle([W / 2 - 180 * bar, 1050, W / 2 + 180 * bar, 1058], fill=ACCENT)
        self.draw_caption(frame, item, t)
        return frame, local

    def render_bookend(self, seg, t):
        local = t - seg["start"]
        p = local / (seg["end"] - seg["start"])
        clip = self.intro_frames if seg is self.data["intro"] else self.outro_frames
        if clip:
            frame = Image.open(clip[min(int(local * FPS), len(clip) - 1)]).convert("RGBA")
        else:
            frame = ken_burns(self.anchor_full, p, zoom=0.12, drift=(0, -40)).convert("RGBA")
        top = SAFE_BOTTOM - 440
        panel = Image.new("RGBA", (W, H - top), (*NAVY, 0))
        pd = ImageDraw.Draw(panel)
        for yy in range(H - top):
            pd.line([(0, yy), (W, yy)], fill=(*NAVY, min(225, int(yy * 0.9))))
        frame.alpha_composite(panel, (0, top))
        # Big hook text lands in the first frames so a scrolling viewer sees it instantly.
        paste_scaled(frame, seg["title_img"], W / 2, SAFE_BOTTOM - 270, ease_back(local / 0.25 + 0.4))
        paste_scaled(frame, seg["sub_img"], W / 2, SAFE_BOTTOM - 130, 1.0, ease_out((local - 0.15) / 0.25))
        paste_scaled(frame, seg["tag_img"], W / 2, SAFE_BOTTOM - 50, 1.0, ease_out((local - 0.4) / 0.3))
        return frame, local

    def frame_at(self, t):
        kind, seg = self.segment_at(t)
        if kind == "item":
            frame, local = self.render_item(seg, t)
        else:
            frame, local = self.render_bookend(seg, t)
        self.draw_progress(frame, t)
        if local < 0.12 and t > 0.1:
            flash = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - local / 0.12))))
            frame.alpha_composite(flash)
        return frame.convert("RGB")

    # ---- audio ----
    def cut_times(self):
        return [it["start"] for it in self.data["items"]] + [self.data["outro"]["start"]]

    def make_audio(self, path):
        """News-style music bed (make_music.py, royalty-free synth) plus a whoosh on every cut."""
        n = int((self.dur + 0.5) * SR)
        rng = np.random.default_rng(7)
        bed = self.day / "build" / "news_music.wav"
        variant = self.data.get("music_variant", sum(map(ord, self.data["date"])) % 10)
        subprocess.run([sys.executable, str(Path(__file__).with_name("make_music.py")), str(bed),
                        f"{self.dur + 0.5:.2f}", "news", str(variant)], check=True)
        with wave.open(str(bed)) as wf:
            frames = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)
            if wf.getnchannels() == 2:
                frames = frames.reshape(-1, 2).mean(1)
            if wf.getframerate() != SR:
                raise SystemExit("make_music.py sample rate changed")
        music = np.zeros(n)
        music[:min(n, len(frames))] = frames[:n] / 32768.0
        music *= 0.5 / (np.max(np.abs(music)) + 1e-9)
        # Whoosh: band-swept noise on every cut.
        wl = int(0.45 * SR)
        wt = np.arange(wl) / SR
        noise = rng.standard_normal(wl)
        sweep = np.zeros(wl)
        acc = 0.0
        for i in range(wl):  # one-pole low-pass with rising cutoff
            a = 0.02 + 0.5 * (i / wl)
            acc += a * (noise[i] - acc)
            sweep[i] = acc
        whoosh = sweep * np.sin(np.pi * wt / wt[-1]) ** 2
        whoosh = 0.35 * whoosh / (np.max(np.abs(whoosh)) + 1e-9)
        for c in self.cut_times():
            s = max(0, int((c - 0.3) * SR))
            e = min(n, s + wl)
            music[s:e] += whoosh[: e - s]
        pcm = (np.clip(music, -1, 1) * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm.tobytes())

    def build(self):
        build = self.day / "build"
        build.mkdir(exist_ok=True)
        bed = build / "bed.wav"
        self.make_audio(bed)
        out = self.day / "reel.mp4"
        frames = int(self.dur * FPS)
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-i", str(self.voice), "-i", str(bed),
             "-filter_complex", "[1:a]asplit=2[v][key];[2:a][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[m];"
             "[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
             "-map", "0:v", "-map", "[a]", "-t", f"{self.dur:.2f}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE)
        for i in range(frames):
            proc.stdin.write(self.frame_at(i / FPS).tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise SystemExit("ffmpeg failed")
        print(out)


if __name__ == "__main__":
    Reel(Path(sys.argv[1]).resolve()).build()
