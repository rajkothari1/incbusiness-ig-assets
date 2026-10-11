"""Builds 1080x1920 Instagram reels from rendered cards.

Usage:
  REEL=1 node generator/render.js <stories.json> <day>/reels/cards
  python3 generator/make-reels.py <stories.json> <day>/reels

Each reel: animated brand gradient + slow-panning blurred story photo as a moving
background, white incbusiness logo, the card sliding in and floating, and a CTA line.

The profile grid crops reels to the centre 3:4 (y 240 to 1680 of 1920), so the logo, card and CTA
all sit inside that band. Each reel gets its own background palette.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stories_file, out_dir = sys.argv[1], sys.argv[2]
stories = json.load(open(stories_file))

DUR, FPS = 8, 30
W, H = 1080, 1920
CARD_W, CARD_Y = 920, 372
LOGO_Y, CTA_Y = 262, 1590
# one gradient palette per reel (c0..c3), cycled by story order
PALETTES = [
    ('0x0B1257', '0x23308F', '0x3C1060', '0x9C1C2B'),  # navy to crimson
    ('0x06363F', '0x0E7C7B', '0x124E78', '0x0B1F3A'),  # teal
    ('0x2B0B4F', '0x6A1B9A', '0xC2185B', '0x311B92'),  # purple to pink
    ('0x3E1F00', '0xB45309', '0x7C2D12', '0x1F2937'),  # amber
    ('0x052E16', '0x15803D', '0x0F766E', '0x14532D'),  # green
    ('0x1E1B4B', '0x4338CA', '0x0369A1', '0x0F172A'),  # indigo to sky
    ('0x450A0A', '0xB91C1C', '0x9A3412', '0x1C1917'),  # red
    ('0x0C4A6E', '0x0284C7', '0x7E22CE', '0x082F49'),  # ocean to violet
    ('0x3B0764', '0xA21CAF', '0xDB2777', '0x1E1B4B'),  # magenta
    ('0x1F2937', '0x475569', '0x0F766E', '0x111827'),  # slate
]
LOGO = os.path.join(ROOT, 'generator/assets/incbusiness-logo-white.png')
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'

for idx, s in enumerate(stories):
    c0, c1, c2, c3 = PALETTES[idx % len(PALETTES)]
    card = os.path.join(out_dir, 'cards', f"{s['slug']}.png")
    photo = os.path.join(ROOT, s.get('heroPhoto') or s['background'])
    out = os.path.join(out_dir, f"{s['slug']}.mp4")
    card_y = (f"if(lt(t,0.7),{CARD_Y}+260*pow(1-t/0.7,3),"
              f"{CARD_Y}+10*sin(2*PI*(t-0.7)/3))")
    graph = ';'.join([
        # moving brand gradient
        f"gradients=s={W}x{H}:r={FPS}:d={DUR}:n=4:c0={c0}:c1={c1}:c2={c2}:c3={c3}:speed=0.02:type=linear[grad]",
        # blurred story photo, slowly panning and zooming
        f"[1:v]scale=-2:{int(H*1.15)},crop={W}:{H}:x='(iw-ow)*t/{DUR}':y='(ih-oh)/2',"
        f"gblur=sigma=22,eq=brightness=-0.12:saturation=1.2,format=rgba,colorchannelmixer=aa=0.42[photo]",
        "[grad][photo]overlay=0:0:shortest=1[bg]",
        # card slides up and fades in, then floats
        f"[2:v]scale={CARD_W}:-1,format=rgba,fade=t=in:st=0:d=0.6:alpha=1[card]",
        f"[bg][card]overlay=x=(W-w)/2:y='{card_y}'[v1]",
        # logo
        "[3:v]scale=460:-1,format=rgba,fade=t=in:st=0.3:d=0.6:alpha=1[logo]",
        f"[v1][logo]overlay=x=(W-w)/2:y={LOGO_Y}[v2]",
        # CTA
        f"[v2]drawtext=fontfile={FONT}:text='Follow @incbusiness.official':fontcolor=white:fontsize=46:"
        f"x=(w-text_w)/2:y={CTA_Y}:alpha='if(lt(t,1.2),0,min(1,(t-1.2)/0.5))',format=yuv420p[vout]",
    ])
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo:d={DUR}',
           '-loop', '1', '-t', str(DUR), '-r', str(FPS), '-i', photo,
           '-loop', '1', '-t', str(DUR), '-r', str(FPS), '-i', card,
           '-loop', '1', '-t', str(DUR), '-r', str(FPS), '-i', LOGO,
           '-filter_complex', graph, '-map', '[vout]', '-map', '0:a',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', str(FPS),
           '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('reel', out)
