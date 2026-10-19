#!/usr/bin/env bash
# Builds out/<id>.mp4 (5s, 1080x1920) + out/<id>-cover.png from data/reels.json.
# Usage: ./render-reels.sh [id...]   (needs node+playwright, ffmpeg, jq)
set -euo pipefail
cd "$(dirname "$0")"
DUR=${DUR:-5}
NODE_PATH=${NODE_PATH:-$(npm root -g)} node render-overlays.js "$@"
mkdir -p out
ids=("$@"); [ ${#ids[@]} -eq 0 ] && mapfile -t ids < <(jq -r '.[].id' data/reels.json)
for id in "${ids[@]}"; do
  bg=$(jq -r --arg id "$id" '.[]|select(.id==$id).bg.file' data/reels.json)
  ss=$(jq -r --arg id "$id" '.[]|select(.id==$id).bg.start' data/reels.json)
  # Background: cover-crop to 9:16 with a slow push-in; overlay fades in over 0.4s.
  ffmpeg -y -v error -ss "$ss" -t "$DUR" -i "bg-videos/$bg" -loop 1 -t "$DUR" -i "build/$id.png" -filter_complex \
    "[0:v]scale=-2:1920,crop=1080:1920,scale=w='trunc(1080*(1+0.08*t/$DUR)/2)*2':h=-2:eval=frame,crop=1080:1920,fps=30,setsar=1[bg];[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1[ov];[bg][ov]overlay=0:0:format=auto,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -preset medium -crf 20 -movflags +faststart -an "out/$id.mp4"
  ffmpeg -y -v error -ss 2.5 -i "out/$id.mp4" -frames:v 1 "out/$id-cover.png"
  jq -r --arg id "$id" '.[]|select(.id==$id).caption' data/reels.json > "out/$id-caption.txt"
  echo "reel $id -> out/$id.mp4 ($(du -h "out/$id.mp4" | cut -f1))"
done
