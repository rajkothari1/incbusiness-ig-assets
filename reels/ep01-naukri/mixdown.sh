#!/bin/bash
# Mixes voice-over + whooshes + riser/boom + music bed (ducked under the voice) into mix.wav.
# Usage: bash mixdown.sh <voice.wav>
set -e
cd "$(dirname "$0")"
VOICE=${1:-vo3_fast.wav}
CUTS="1.49 4.7 6.4 10.22 11.98 18.08 23.62 27.26 31.03"
inputs="-i $VOICE -i music.wav"; filt=""; n=2
for c in $CUTS; do inputs="$inputs -i whoosh.wav"; d=$(python3 -c "print(int(max(0,($c-0.32))*1000))"); filt="$filt[$n]adelay=${d}|${d}[w$n];"; n=$((n+1)); done
inputs="$inputs -i riser.wav -i boom.wav"
filt="$filt[$n]volume=0.5,adelay=32970|32970[w$n];"; n=$((n+1)); filt="$filt[$n]volume=0.5,adelay=34470|34470[w$n];"; n=$((n+1))
fx=""; for i in $(seq 2 $((n-1))); do fx="$fx[w$i]"; done
ffmpeg -y -loglevel error $inputs -filter_complex "\
[0]aformat=channel_layouts=stereo,apad=whole_dur=39.6,asplit=2[v][key];\
[1]volume='0.32+0.3*min(1,max(0,(t-31.03)/3))':eval=frame[m];[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=600[md];\
${filt}[v][md]${fx}amix=inputs=$((n)):normalize=0:duration=longest,alimiter=limit=0.95" -ar 44100 -t 39.6 mix.wav
