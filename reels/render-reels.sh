#!/usr/bin/env bash
# Builds out/<id>.mp4 (5s reel with background music, follow CTA from 3s), out/<id>-cover.png (upload as reel cover) and out/<id>-caption.txt
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
  # bg-videos/ is gitignored: fetch the Mixkit clip (<clipid>.mp4) if this container doesn't have it yet.
  if [ ! -s "bg-videos/$bg" ]; then
    mkdir -p bg-videos; c=${bg%.mp4}
    curl -sfL -m 300 -o "bg-videos/$bg" "https://assets.mixkit.co/videos/$c/$c-1080.mp4" || curl -sfL -m 300 -o "bg-videos/$bg" "https://assets.mixkit.co/videos/$c/$c-720.mp4"
  fi
  mf=$(jq -r --arg id "$id" '.[]|select(.id==$id).music.file' data/reels.json)
  ms=$(jq -r --arg id "$id" '.[]|select(.id==$id).music.start' data/reels.json)
  # music/ is gitignored too: Mixkit Music Free License tracks, fetched by id.
  if [ ! -s "music/$mf" ]; then mkdir -p music; c=${mf%.mp3}; curl -sfL -m 120 -o "music/$mf" "https://assets.mixkit.co/music/$c/$c.mp3"; fi
  ffmpeg -y -v error -ss "$ss" -t "$DUR" -i "bg-videos/$bg" -loop 1 -t "$DUR" -i "build/$id-reel.png" -loop 1 -t "$DUR" -i "build/$id-cta.png" -ss "$ms" -t "$DUR" -i "music/$mf" -filter_complex \
    "[0:v]$GRADE,scale=w='trunc(1080*(1+0.08*t/$DUR)/2)*2':h=-2:eval=frame,crop=1080:1920,fps=30,setsar=1[bg];[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1[ov];[2:v]format=rgba,fade=in:st=3:d=0.35:alpha=1[cta];[bg][ov]overlay=0:0:format=auto[b1];[b1][cta]overlay=x=0:y='max(0,40*(1-(t-3)/0.35))':enable='gte(t,3)':format=auto,format=yuv420p[v];[3:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:d=0.3,afade=t=out:st=$(echo "$DUR-0.8"|bc):d=0.8,aresample=44100[a]" \
    -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -t "$DUR" -movflags +faststart "out/$id.mp4"
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
