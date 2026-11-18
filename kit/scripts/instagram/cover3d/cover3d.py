"""3D reel cover: a cover config (JSON) -> a 2160x3840 JPEG, rendered with three.js in headless Chrome.

    python3 cover3d.py COVER.json OUT.jpg

COVER.json fields:
 {"layout": "L1" | "L2",            # L1: title on top, number below, prop on the floor beside it; L2: number on top, title below, prop top right
  "bg": "<css background>",         # its own colour world (gradients), see list-reel-playbook.md for ready palettes
  "grid": "rgba(255,255,255,.06)",  # faint grid lines: white-ish on dark backgrounds, rgba(0,0,0,.045) on light ones
  "logo": "light" | "dark",         # light logo on dark backgrounds, dark logo on light ones
  "rim": "#hex",                    # back light colour, a light tint of the accent
  "lines": [{"t": "Your", "s": 150, "c": "#fff", "i": 0, "w": 900}, ...],   # title lines: text, px size (auto-shrinks to fit), colour, italic, weight
  "extra": {"t": "tools", "c": "#fff"},  # optional small word under the number (L1 only), may be left out
  "num": "20", "mat": {"c": "#ff5a36", "k": "plastic" | "metal" | "pearl"},
  "prop": {"kind": "<one of PROPS in engine.html>", "a": "#accent", "b": "#second", "k": "#dark parts (optional)"}}
"""
import functools, http.server, json, pathlib, sys, threading

HERE = pathlib.Path(__file__).parent


def render(cfg, out):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    try:
        with sync_playwright() as pw:
            args = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
            try:
                br = pw.chromium.launch(channel='chrome', args=args)
            except Exception:
                br = pw.chromium.launch(args=args)
            pg = br.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=2)
            errors = []
            pg.on('pageerror', lambda e: errors.append(str(e)))
            pg.add_init_script(f'window.COVER = {json.dumps(cfg)};')
            pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/engine.html')
            try:
                pg.wait_for_function('window.READY === true', timeout=90000)
            except Exception:
                sys.exit('Cover did not render: ' + '; '.join(errors or ['timeout']))
            pg.wait_for_timeout(600)
            png = pathlib.Path(out).with_suffix('.png')
            pg.screenshot(path=str(png))
            br.close()
        Image.open(png).convert('RGB').save(out, quality=94)
        png.unlink()
    finally:
        srv.shutdown()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    render(json.loads(pathlib.Path(sys.argv[1]).read_text()), sys.argv[2])
    print('cover ->', sys.argv[2])
