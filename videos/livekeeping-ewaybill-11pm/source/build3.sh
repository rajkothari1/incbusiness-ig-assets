set -e
S=/tmp/claude-0/-home-user-incbusiness-ig-assets/f0a3506f-6e30-5157-9541-4abd58ab7d09/scratchpad; cd $S
N="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
ffmpeg -hide_banner -loglevel error -y -i gen/c1.mp4 -i gen/c2b.mp4 -i gen/c3b.mp4 -i ui/ui2.mp4 -i gen/c4b.mp4 -i gen/c5.mp4 -i ui/end.mp4 -filter_complex "\
[0:v]trim=0:4.7,setpts=PTS-STARTPTS,$N[a];\
[1:v]trim=0:4.1,setpts=PTS-STARTPTS,$N[b];\
[2:v]trim=0.2:2.9,setpts=PTS-STARTPTS,$N[c];\
[3:v]trim=0:9.6,setpts=PTS-STARTPTS,$N[d];\
[4:v]trim=0.2:3.0,setpts=PTS-STARTPTS,scale=1260:2240,crop=1080:1920:90:240,fps=30,setsar=1,format=yuv420p[e];\
[5:v]trim=0.6:5.0,setpts=(PTS-STARTPTS)/1.63,$N,trim=0:2.7[f];\
[6:v]trim=0:3.5,setpts=PTS-STARTPTS,$N[g];\
[a][b][c][d][e][f][g]concat=n=7:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 16 -preset medium out/base3.mp4
OV="lg 0 11.5
t1 0 4.7
s1 0.1 4.7
t2 4.7 8.8
s2 4.75 8.8
t3 8.8 11.5
s3 8.8 11.5
t4 21.1 23.9
s5 21.15 23.9
t5 23.9 26.6
s6 24.7 26.6"
inputs="-i out/base3.mp4"; fc=""; prev="0:v"; i=1
while read n a b; do d=$(python3 -c "print(round($b-$a,3))"); fo=$(python3 -c "print(round($d-0.15,3))")
 if [ "$a" = "0" ]; then fin=""; else fin="fade=t=in:st=0:d=0.2:alpha=1,"; fi
 inputs="$inputs -loop 1 -t $d -i ui/ov_$n.png"
 fc="$fc[$i:v]format=rgba,${fin}fade=t=out:st=$fo:d=0.15:alpha=1,setpts=PTS-STARTPTS+$a/TB[o$i];[$prev][o$i]overlay=0:0:eof_action=pass[v$i];"
 prev="v$i"; i=$((i+1)); done <<< "$OV"
A=$i
inputs="$inputs -i gen/v1.mp3 -i gen/v2.mp3 -i gen/v3.mp3 -i gen/v4b.mp3 -i gen/v5.mp3 -i gen/cta2.mp3 -i aud/music.wav -i aud/sfx.wav"
fc="$fc[$((A))]volume=0.5dB,adelay=100:all=1[a1];[$((A+1))]volume=4dB,adelay=4750:all=1[a2];[$((A+2))]volume=2dB,adelay=8800:all=1[a3];[$((A+3))]atempo=1.08,volume=2dB,adelay=11600:all=1[a4];[$((A+4))]volume=2dB,adelay=21150:all=1[a5];[$((A+5))]atempo=1.06,volume=1dB,adelay=24650:all=1[a6];"
fc="$fc[a1][a2][a3][a4][a5][a6]amix=inputs=6:normalize=0,aformat=channel_layouts=stereo[vo];[vo]asplit[vo1][vo2];"
fc="$fc[$((A+6))]volume=0.32,aformat=channel_layouts=stereo[mu];[mu][vo2]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=300[mud];[$((A+7))]volume=0.5,aformat=channel_layouts=stereo[sf];"
fc="$fc[vo1][mud][sf]amix=inputs=3:normalize=0,alimiter=limit=0.95,atrim=0:30.1[aout]"
ffmpeg -hide_banner -loglevel error -y $inputs -filter_complex "$fc" -map "[$prev]" -map "[aout]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -t 30.1 out/livekeeping_ewaybill_11pm_v3.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 out/livekeeping_ewaybill_11pm_v3.mp4
