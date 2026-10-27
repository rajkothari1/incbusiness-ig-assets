#!/usr/bin/env python3
"""Screenshot tool websites for an AI Tools post (see docs/ai-tools-playbook.md, step 4).

Usage:
    python3 scripts/ai-tools/shoot.py OUT_DIR looka=https://looka.com/ canva=https://www.canva.com/ ...

For each name=url it saves OUT_DIR/name.jpg (1440x900 page, ~1200px wide JPEG),
or OUT_DIR/name.png when no JPEG converter is available. Runs headless Chrome
with a fixed timeout (pages with background video never "finish loading"),
and flags shots that look blank so they can be retried or the tool swapped.
"""
import os
import shutil
import subprocess
import sys
import tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
BLANK_BYTES = 20_000  # a real homepage screenshot is far bigger than this


def find_chrome():
    """Chrome to use: $CHROME_PATH if set (e.g. a Playwright-installed Chromium), else the usual names."""
    if os.environ.get("CHROME_PATH") and os.path.exists(os.environ["CHROME_PATH"]):
        return os.environ["CHROME_PATH"]
    for c in CHROME_CANDIDATES:
        path = c if os.path.isabs(c) else shutil.which(c)
        if path and os.path.exists(path):
            return path
    sys.exit("No Chrome/Chromium found. On Linux: apt-get install -y chromium (or chromium-browser).")


def screenshot(chrome, url, png, width=1440, height=900, wait_ms=15000):
    """One headless screenshot, killed after wait + 35s so a hung page can't block the run."""
    profile = tempfile.mkdtemp(prefix="shot-")
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           f"--user-data-dir={profile}", f"--window-size={width},{height}", f"--timeout={wait_ms}",
           f"--user-agent={UA}", "--allow-file-access-from-files", f"--screenshot={png}", url]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=wait_ms / 1000 + 35)
    except subprocess.TimeoutExpired:
        pass
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    return os.path.exists(png) and os.path.getsize(png) > 0


def to_jpeg(png, jpg, width=1200, quality=78):
    """PNG → JPEG ~1200px wide using whatever is available (sips on Mac, Pillow, ImageMagick)."""
    if shutil.which("sips"):
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality), "-Z", str(width), png, "--out", jpg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return True
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB")
        im.thumbnail((width, 10_000))
        im.save(jpg, "JPEG", quality=quality)
        return True
    except Exception:
        pass
    if shutil.which("convert"):
        return subprocess.run(["convert", png, "-resize", f"{width}x", "-quality", str(quality), jpg]).returncode == 0
    return False


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    chrome = find_chrome()

    for pair in sys.argv[2:]:
        name, url = pair.split("=", 1)
        png = os.path.join(out, f"{name}.png")
        if not screenshot(chrome, url, png):
            print(f"FAIL  {name}: no screenshot ({url})")
            continue
        jpg = os.path.join(out, f"{name}.jpg")
        final = jpg if to_jpeg(png, jpg) else png
        if final == jpg:
            os.remove(png)
        size = os.path.getsize(final)
        note = "  <- looks BLANK or blocked, retry another URL or swap the tool" if os.path.getsize(final) < BLANK_BYTES else ""
        print(f"OK    {name}: {os.path.basename(final)} {size // 1024} KB{note}")


if __name__ == "__main__":
    main()
