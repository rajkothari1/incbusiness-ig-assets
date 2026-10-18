#!/bin/bash
# Mixes voice-over + whooshes + riser/boom + music bed (ducked under the voice) into mix.wav.
set -e
cd "$(dirname "$0")"
VOICE=${1:-vo_fast.wav}
DUR=56.9
CUTS="1.68 4.06 6.3 10.99 13.7 17.42 22.93 27.49 34.72 40.24 44.04 48.31"
END=51.75
inputs="-i $VOICE -i music.wav"; filt=""; n=2
for c in $CUTS; do inputs="$inputs -i whoosh.wav"; d=$(python3 -c "print(int(max(0,($c-0.32))*1000))"); filt="$filt[$n]adelay=${d}|${d}[w$n];"; n=$((n+1)); done
inputs="$inputs -i riser.wav -i boom.wav"
r=$(python3 -c "print(int(($END-1.5)*1000))"); e=$(python3 -c "print(int($END*1000))")
filt="$filt[$n]volume=0.5,adelay=$r|$r[w$n];"; n=$((n+1)); filt="$filt[$n]volume=0.5,adelay=$e|$e[w$n];"; n=$((n+1))
fx=""; for i in $(seq 2 $((n-1))); do fx="$fx[w$i]"; done
ffmpeg -y -loglevel error $inputs -filter_complex "\
[0]aformat=channel_layouts=stereo,apad=whole_dur=$DUR,asplit=2[v][key];\
[1]volume='0.32+0.3*min(1,max(0,(t-48.31)/3))':eval=frame[m];[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=600[md];\
${filt}[v][md]${fx}amix=inputs=$((n)):normalize=0:duration=longest,alimiter=limit=0.95" -ar 44100 -t $DUR mix.wav
