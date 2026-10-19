#!/usr/bin/env bash
# Builds out/<id>.mp4 (5s reel, follow CTA from 3s), out/<id>-cover.png (upload as reel cover) and out/<id>-caption.txt
# from data/reels.json, plus out/grid-preview.png. Usage: ./render-reels.sh [id...]  (needs node+playwright, ffmpeg, jq)
set -euo pipefail
cd "$(dirname "$0")"
DUR=${DUR:-5}
NODE_PATH=${NODE_PATH:-$(npm root -g)} node render-overlays.js "$@"
mkdir -p out
ids=("$@"); [ ${#ids[@]} -eq 0 ] && mapfile -t ids < <(jq -r '.[].id' data/reels.json)
# Theme grade: cover-crop to 9:16, black & white, slight contrast.
GRADE="scale=-2:1920,crop=1080:1920,hue=s=0,eq=contrast=1.12"
for id in "${ids[@]}"; do
  bg=$(jq -r --arg id "$id" '.[]|select(.id==$id).bg.file' data/reels.json)
  ss=$(jq -r --arg id "$id" '.[]|select(.id==$id).bg.start' data/reels.json)
  ffmpeg -y -v error -ss "$ss" -t "$DUR" -i "bg-videos/$bg" -loop 1 -t "$DUR" -i "build/$id-reel.png" -loop 1 -t "$DUR" -i "build/$id-cta.png" -filter_complex \
    "[0:v]$GRADE,scale=w='trunc(1080*(1+0.08*t/$DUR)/2)*2':h=-2:eval=frame,crop=1080:1920,fps=30,setsar=1[bg];[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1[ov];[2:v]format=rgba,fade=in:st=3:d=0.35:alpha=1[cta];[bg][ov]overlay=0:0:format=auto[b1];[b1][cta]overlay=x=0:y='max(0,40*(1-(t-3)/0.35))':enable='gte(t,3)':format=auto,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -preset medium -crf 20 -movflags +faststart -an "out/$id.mp4"
  ffmpeg -y -v error -ss "$ss" -i "bg-videos/$bg" -i "build/$id-cover.png" -filter_complex \
    "[0:v]$GRADE,setsar=1[bg];[bg][1:v]overlay=0:0" -frames:v 1 "out/$id-cover.png"
  jq -r --arg id "$id" '.[]|select(.id==$id).caption' data/reels.json > "out/$id-caption.txt"
  echo "reel $id -> out/$id.mp4 ($(du -h "out/$id.mp4" | cut -f1))"
done
# Profile grid preview: 3 columns, 3:4 crop, newest (last id) top-left like Instagram.
python3 - <<'PY'
import json
from PIL import Image
ids=[r['id'] for r in json.load(open('data/reels.json'))][::-1]
W,H,G=360,480,6
rows=(len(ids)+2)//3
sheet=Image.new('RGB',(3*W+2*G,rows*H+(rows-1)*G),'white')
for i,id in enumerate(ids):
    im=Image.open(f'out/{id}-cover.png').crop((0,240,1080,1680)).resize((W,H))
    sheet.paste(im,((i%3)*(W+G),(i//3)*(H+G)))
sheet.save('out/grid-preview.png')
PY
echo "grid -> out/grid-preview.png"
