"""Build a 9:16 "Top 10 news in 60s" reel: anchor intro/outro, one photo card per story,
punch-zoom cuts, word-by-word captions, synthesized music bed and whoosh SFX.

Usage: python3 reels/build_reel.py reels/2026-10-11
The day folder needs voice.mp3 and segments.json (see reels/2026-10-11/segments.json).
Everything here is free: Unsplash backgrounds from backgrounds/, audio is generated in code.
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
FPS = 30
SR = 44100
ACCENT = (255, 184, 28)
NAVY = (12, 20, 46)
WHITE = (255, 255, 255)
CARD_W = 920
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
        self.pip = self.make_pip(anchor)
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
        self.chrome = self.make_chrome()
        self.intro_frames = self.extract_intro()
        self.talking_pip = self.make_talking_pip()

    def make_talking_pip(self):
        """Animate the corner anchor with faces from the lip-synced intro clip.

        The clip only advances while the voice track is loud, so the mouth moves when she
        talks and rests in the pauses between stories. Free: reuses the intro clip.
        """
        if not self.intro_frames:
            return None
        size = self.pip.width - 16
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size * 4, size * 4], fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        faces = []
        for f in self.intro_frames:
            face = Image.open(f).convert("RGB").crop((240, 480, 840, 1080)).resize((size, size), Image.LANCZOS)
            pip = Image.new("RGBA", self.pip.size, (0, 0, 0, 0))
            ImageDraw.Draw(pip).ellipse([0, 0, self.pip.width - 1, self.pip.height - 1], fill=ACCENT)
            pip.paste(face, (8, 8), mask)
            faces.append(pip)
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(self.voice), "-ac", "1", "-ar", "16000",
                              "-f", "s16le", "-"], capture_output=True, check=True).stdout
        pcm = np.abs(np.frombuffer(raw, np.int16).astype(np.float32))
        hop = 16000 // FPS
        env = np.array([pcm[i * hop:(i + 1) * hop].mean() for i in range(len(pcm) // hop)])
        talking = env > max(env.max() * 0.08, 1)
        seq, pos, step = [], 0, 1
        for flag in talking:
            if flag:  # ping-pong through the clip so there is never a jump cut
                pos += step
                if pos >= len(faces) - 1 or pos <= 0:
                    step = -step
                    pos = min(max(pos, 0), len(faces) - 1)
            seq.append(pos)
        return faces, seq

    def extract_intro(self):
        """Optional lip-synced anchor clip (<day>/intro.mp4) played during the intro line."""
        clip = self.day / "intro.mp4"
        if not clip.exists():
            return []
        out = self.day / "build" / "intro_frames"
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.jpg"):
            old.unlink()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip), "-vf",
                        f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                        "-q:v", "2", str(out / "%05d.jpg")], check=True)
        return sorted(out.glob("*.jpg"))

    def make_pip(self, anchor):
        size = 230
        face = anchor.crop((300, 520, 820, 1040)).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size * 4, size * 4], fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        pip = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
        ImageDraw.Draw(pip).ellipse([0, 0, size + 15, size + 15], fill=ACCENT)
        pip.paste(face, (8, 8), mask)
        return pip

    def make_badge(self, n):
        size = 150
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, size - 1, size - 1], fill=ACCENT, outline=WHITE, width=6)
        f = font("Black", 84)
        tw = d.textlength(str(n), font=f)
        d.text(((size - tw) / 2, 18), str(n), font=f, fill=NAVY)
        return img

    def make_chrome(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 132], fill=(*NAVY, 225))
        d.rectangle([0, 132, W, 138], fill=ACCENT)
        d.text((44, 30), f"TOP {len(self.data['items'])} BUSINESS NEWS", font=font("ExtraBold", 42), fill=WHITE)
        d.text((44, 84), f"{self.data['date']}  ·  @incbusiness.official", font=font("SemiBold", 28), fill=ACCENT)
        # Instagram asks creators to label realistic AI media; keep a visible tag on screen.
        tag, f = "AI ANCHOR", font("SemiBold", 22)
        tw = d.textlength(tag, font=f)
        d.rounded_rectangle([W - tw - 76, 46, W - 40, 90], radius=10, outline=WHITE, width=2)
        d.text((W - tw - 58, 54), tag, font=f, fill=WHITE)
        return img

    def prepare_cards(self):
        for i, item in enumerate(self.data["items"]):
            item["num_img"] = text_image(f"#{i + 1}", font("Black", 150), ACCENT)
            item["badge_img"] = self.make_badge(i + 1)
            item["words"] = item["caption"].split()
            if "card" in item:
                continue
            item["name_img"] = text_image(item["name"], fit_font(item["name"], "Black", 104, W - 120), WHITE)
            item["stat_img"] = text_image(item["stat"], fit_font(item["stat"], "Black", 200, W - 100), ACCENT)
            item["label_img"] = text_image(item["label"], fit_font(item["label"], "SemiBold", 52, W - 120), WHITE)
        for key in ("intro", "outro"):
            seg = self.data[key]
            seg["title_img"] = text_image(seg["title"], font("Black", 230), ACCENT)
            seg["sub_img"] = text_image(seg["subtitle"], fit_font(seg["subtitle"], "Black", 110, W - 100), WHITE)
            seg["tag_img"] = text_image(seg["tagline"], font("SemiBold", 54), WHITE)

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
        gap, x0, y = 8, 40, H - 40
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
        f = font("ExtraBold", 66)
        lines, cur, cur_w = [], [], 0
        space = d.textlength(" ", font=f)
        for idx, w in enumerate(words):
            ww = d.textlength(w, font=f)
            if cur and cur_w + space + ww > W - 140:
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
                        d.rounded_rectangle([x - 12, y - 6, x + ww + 12, y + 84], radius=14, fill=ACCENT)
                        colour = NAVY
                    else:
                        colour = WHITE
                    dy = (1 - pop) * 30
                    d.text((x, y + dy), w, font=f, fill=colour, stroke_width=0 if colour == NAVY else 3,
                           stroke_fill=(0, 0, 0))
                x += ww + space
            y += 100

    def render_card(self, item, t):
        local = t - item["start"]
        p = local / (item["end"] - item["start"])
        frame = ken_burns(item["bg_img"], p, zoom=0.12, drift=(20, -20)).convert("RGBA")
        card = item["card_img"]
        # Card slides up and punches in on the cut, then keeps a slow push-in.
        scale = (1 + 0.10 * (1 - ease_out(local / 0.35))) * (1 + 0.035 * p)
        cy = 170 + card.height / 2 + 140 * (1 - ease_out(local / 0.35))
        cw, ch = round(card.width * scale), round(card.height * scale)
        shadow = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([40, 50, cw + 40, ch + 50], radius=30, fill=(0, 0, 0, 150))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        frame.alpha_composite(shadow, (round(W / 2 - cw / 2 - 40), round(cy - ch / 2 - 40)))
        frame.paste(card.resize((cw, ch), Image.BILINEAR), (round(W / 2 - cw / 2), round(cy - ch / 2)))
        paste_scaled(frame, item["badge_img"], 110, 230, ease_back((local - 0.1) / 0.35))
        self.draw_caption(frame, item, t, y=1490)
        bob = math.sin(t * 2.2) * 4
        frame.alpha_composite(self.pip_at(t), (W - self.pip.width - 30, 160 + round(bob)))
        return frame, local

    def pip_at(self, t):
        if not self.talking_pip:
            return self.pip
        faces, seq = self.talking_pip
        return faces[seq[min(int(t * FPS), len(seq) - 1)]]

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
        # Anchor stays on screen as a picture-in-picture.
        bob = math.sin(t * 2.2) * 4
        frame.alpha_composite(self.pip_at(t), (W - self.pip.width - 40, 170 + round(bob)))
        return frame, local

    def render_bookend(self, seg, t):
        local = t - seg["start"]
        p = local / (seg["end"] - seg["start"])
        if seg is self.data["intro"] and self.intro_frames:
            idx = min(int(local * FPS), len(self.intro_frames) - 1)
            frame = Image.open(self.intro_frames[idx]).convert("RGBA")
        elif self.talking_pip:
            # Outro: same voice-driven trick as the corner face, full screen.
            _, seq = self.talking_pip
            frame = Image.open(self.intro_frames[seq[min(int(t * FPS), len(seq) - 1)]]).convert("RGBA")
        else:
            frame = ken_burns(self.anchor_full, p, zoom=0.12, drift=(0, -40)).convert("RGBA")
        panel = Image.new("RGBA", (W, 640), (*NAVY, 0))
        pd = ImageDraw.Draw(panel)
        for yy in range(640):
            pd.line([(0, yy), (W, yy)], fill=(*NAVY, min(235, int(yy * 0.9))))
        frame.alpha_composite(panel, (0, H - 640))
        paste_scaled(frame, seg["title_img"], W / 2, 1460, ease_back(local / 0.45))
        paste_scaled(frame, seg["sub_img"], W / 2, 1640, 1.0, ease_out((local - 0.35) / 0.3))
        paste_scaled(frame, seg["tag_img"], W / 2, 1760, 1.0, ease_out((local - 0.7) / 0.3))
        return frame, local

    def frame_at(self, t):
        kind, seg = self.segment_at(t)
        if kind == "item":
            frame, local = self.render_item(seg, t)
        else:
            frame, local = self.render_bookend(seg, t)
        frame.alpha_composite(self.chrome)
        self.draw_progress(frame, t)
        if local < 0.12 and t > 0.1:
            flash = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - local / 0.12))))
            frame.alpha_composite(flash)
        return frame.convert("RGB")

    # ---- audio ----
    def cut_times(self):
        return [it["start"] for it in self.data["items"]] + [self.data["outro"]["start"]]

    def make_audio(self, path):
        n = int((self.dur + 0.5) * SR)
        t = np.arange(n) / SR
        music = np.zeros(n)
        bpm = 112
        beat = 60 / bpm
        rng = np.random.default_rng(7)
        # Kick on every beat, hi-hat on off-beats.
        kick_len = int(0.25 * SR)
        kt = np.arange(kick_len) / SR
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 14)
        hat_len = int(0.05 * SR)
        hat = rng.standard_normal(hat_len) * np.exp(-np.arange(hat_len) / SR * 90)
        hat = np.diff(hat, prepend=0)
        b = 0
        while b * beat < self.dur:
            s = int(b * beat * SR)
            e = min(n, s + kick_len)
            music[s:e] += 0.9 * kick[: e - s]
            hs = int((b + 0.5) * beat * SR)
            he = min(n, hs + hat_len)
            if hs < n:
                music[hs:he] += 0.25 * hat[: he - hs]
            b += 1
        # Bass + soft pad following an Am-F-C-G loop, one chord per bar.
        roots = [110.0, 87.31, 130.81, 98.0]
        bar = 4 * beat
        for k in range(int(self.dur / bar) + 1):
            s, e = int(k * bar * SR), min(n, int((k + 1) * bar * SR))
            if s >= n:
                break
            tt = t[s:e] - t[s]
            f = roots[k % 4]
            env = np.minimum(1, tt * 8) * np.exp(-tt * 0.4)
            music[s:e] += 0.35 * np.sin(2 * np.pi * f * tt) * env
            for mult in (2, 2.5, 3):
                music[s:e] += 0.07 * np.sin(2 * np.pi * f * mult * tt) * np.minimum(1, tt * 2)
        music /= np.max(np.abs(music)) + 1e-9
        music *= 0.11
        fade = int(1.5 * SR)
        music[-fade:] *= np.linspace(1, 0, fade)
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
             "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=1.0[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]",
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
