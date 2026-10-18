#!/bin/bash
# Mixes voice-over + whooshes + riser/boom + music bed (ducked under the voice) into mix.wav.
set -e
cd "$(dirname "$0")"
VOICE=${1:-vo_fast.wav}
DUR=58.2
CUTS="1.76 4.24 6.52 11.5 13.28 16.99 22.91 27.54 35.07 40.95 44.9 49.5"
END=52.98
inputs="-i $VOICE -i music.wav"; filt=""; n=2
for c in $CUTS; do inputs="$inputs -i whoosh.wav"; d=$(python3 -c "print(int(max(0,($c-0.32))*1000))"); filt="$filt[$n]adelay=${d}|${d}[w$n];"; n=$((n+1)); done
inputs="$inputs -i riser.wav -i boom.wav"
r=$(python3 -c "print(int(($END-1.5)*1000))"); e=$(python3 -c "print(int($END*1000))")
filt="$filt[$n]volume=0.5,adelay=$r|$r[w$n];"; n=$((n+1)); filt="$filt[$n]volume=0.5,adelay=$e|$e[w$n];"; n=$((n+1))
fx=""; for i in $(seq 2 $((n-1))); do fx="$fx[w$i]"; done
ffmpeg -y -loglevel error $inputs -filter_complex "\
[0]aformat=channel_layouts=stereo,apad=whole_dur=$DUR,asplit=2[v][key];\
[1]volume='0.32+0.3*min(1,max(0,(t-49.5)/3))':eval=frame[m];[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=600[md];\
${filt}[v][md]${fx}amix=inputs=$((n)):normalize=0:duration=longest,alimiter=limit=0.95" -ar 44100 -t $DUR mix.wav
