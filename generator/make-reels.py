"""Builds 1080x1920 Instagram reels from rendered cards.

Usage:
  REEL=1 node generator/render.js <stories.json> <day>/reels/cards
  python3 generator/make-reels.py <stories.json> <day>/reels

Each reel: animated brand gradient + slow-panning blurred story photo as a moving
background, white incbusiness logo, the card sliding in and floating, and a CTA line.
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
CARD_W, CARD_Y = 980, 330
LOGO = os.path.join(ROOT, 'generator/assets/incbusiness-logo-white.png')
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'

for s in stories:
    card = os.path.join(out_dir, 'cards', f"{s['slug']}.png")
    photo = os.path.join(ROOT, s.get('heroPhoto') or s['background'])
    out = os.path.join(out_dir, f"{s['slug']}.mp4")
    card_y = (f"if(lt(t,0.7),{CARD_Y}+260*pow(1-t/0.7,3),"
              f"{CARD_Y}+10*sin(2*PI*(t-0.7)/3))")
    graph = ';'.join([
        # moving brand gradient
        f"gradients=s={W}x{H}:r={FPS}:d={DUR}:n=4:c0=0x0B1257:c1=0x23308F:c2=0x3C1060:c3=0x9C1C2B:speed=0.02:type=linear[grad]",
        # blurred story photo, slowly panning and zooming
        f"[1:v]scale=-2:{int(H*1.15)},crop={W}:{H}:x='(iw-ow)*t/{DUR}':y='(ih-oh)/2',"
        f"gblur=sigma=22,eq=brightness=-0.12:saturation=1.2,format=rgba,colorchannelmixer=aa=0.42[photo]",
        "[grad][photo]overlay=0:0:shortest=1[bg]",
        # card slides up and fades in, then floats
        f"[2:v]scale={CARD_W}:-1,format=rgba,fade=t=in:st=0:d=0.6:alpha=1[card]",
        f"[bg][card]overlay=x=(W-w)/2:y='{card_y}'[v1]",
        # logo
        "[3:v]scale=520:-1,format=rgba,fade=t=in:st=0.3:d=0.6:alpha=1[logo]",
        "[v1][logo]overlay=x=(W-w)/2:y=200[v2]",
        # CTA
        f"[v2]drawtext=fontfile={FONT}:text='Follow @incbusiness.official':fontcolor=white:fontsize=46:"
        f"x=(w-text_w)/2:y=1690:alpha='if(lt(t,1.2),0,min(1,(t-1.2)/0.5))',format=yuv420p[vout]",
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
