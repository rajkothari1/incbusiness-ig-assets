set -e
S=/tmp/claude-0/-home-user-incbusiness-ig-assets/f0a3506f-6e30-5157-9541-4abd58ab7d09/scratchpad; cd $S
N="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
# split voice w4 into phrases placed on UI beats (UI starts 10.9)
ffmpeg -hide_banner -loglevel error -y -i gen/w4.mp3 -filter_complex "\
[0]atrim=0:1.44,asetpts=PTS-STARTPTS,adelay=50:all=1[p1];[0]atrim=1.88:3.10,asetpts=PTS-STARTPTS,adelay=1000:all=1[p2];\
[0]atrim=3.63:4.69,asetpts=PTS-STARTPTS,adelay=2750:all=1[p3];[0]atrim=5.19:5.64,asetpts=PTS-STARTPTS,adelay=4450:all=1[p4];\
[0]atrim=5.95:6.72,asetpts=PTS-STARTPTS,adelay=5050:all=1[p5];[p1][p2][p3][p4][p5]amix=inputs=5:normalize=0" gen/w4_cut.wav
ffmpeg -hide_banner -loglevel error -y -loop 1 -t 0.9 -i gen/h1.png -i gen/ch2.mp4 -i gen/c1.mp4 -i gen/c2b.mp4 -i gen/c3b.mp4 -i ui/ui3.mp4 -i gen/c4b.mp4 -i gen/c5.mp4 -i ui/end.mp4 -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='1.45-0.4*min(on/12\,1)':x='iw/2-(iw/zoom/2)+sin(on*1.9)*18*max(0\,1-on/22)':y='ih/2-(ih/zoom/2)+cos(on*2.3)*18*max(0\,1-on/22)':d=1:s=1080x1920:fps=30,trim=0:0.9,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[h1];\
[1:v]trim=0.3:2.4,setpts=PTS-STARTPTS,$N[h2];\
[2:v]trim=0:2.95,setpts=PTS-STARTPTS,$N[a];\
[3:v]trim=0:3.05,setpts=PTS-STARTPTS,$N[b];\
[4:v]trim=0.2:2.1,setpts=PTS-STARTPTS,$N[c];\
[5:v]trim=0:7.2,setpts=PTS-STARTPTS,$N[d];\
[6:v]trim=0.2:2.2,setpts=PTS-STARTPTS,scale=1260:2240,crop=1080:1920:90:240,fps=30,setsar=1,format=yuv420p[e];\
[7:v]trim=0.6:5.0,setpts=(PTS-STARTPTS)/2.44,$N,trim=0:1.8[f];\
[8:v]trim=0:3.1,setpts=PTS-STARTPTS,$N[g];\
[h1][h2][a][b][c][d][e][f][g]concat=n=9:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 16 -preset medium out/base25.mp4
OV="lg 0 10.9
hk 0 3.0
sh 0.05 3.0
t1 3.0 5.95
s1 3.0 5.95
t2 5.95 9.0
s2 5.95 9.0
t3 9.0 10.9
s3 9.0 10.9
t4 18.1 20.1
s5 18.15 20.1
t5 20.1 21.9
s6 20.2 21.9"
inputs="-i out/base25.mp4"; fc=""; prev="0:v"; i=1
while read n a b; do d=$(python3 -c "print(round($b-$a,3))"); fo=$(python3 -c "print(round($d-0.15,3))")
 if [ "$n" = "hk" ]; then inputs="$inputs -i ui/hook_ov.mov"; fc="$fc[$i:v]trim=0:3.0,setpts=PTS-STARTPTS[o$i];[$prev][o$i]overlay=0:0:eof_action=pass[v$i];"
 else
 if [ "$a" = "0" ] || [ "$n" = "t1" ] || [ "$n" = "s1" ]; then fin=""; else fin="fade=t=in:st=0:d=0.15:alpha=1,"; fi
 inputs="$inputs -loop 1 -t $d -i ui/ov_$n.png"
 fc="$fc[$i:v]format=rgba,${fin}fade=t=out:st=$fo:d=0.15:alpha=1,setpts=PTS-STARTPTS+$a/TB[o$i];[$prev][o$i]overlay=0:0:eof_action=pass[v$i];"; fi
 prev="v$i"; i=$((i+1)); done <<< "$OV"
A=$i
inputs="$inputs -i gen/vh_cut.wav -i gen/w1.mp3 -i gen/w2.mp3 -i gen/w3.mp3 -i gen/w4_cut.wav -i gen/w5.mp3 -i gen/w6.mp3 -i aud/music25.wav -i aud/sfx25.wav -i aud/hook_sfx.wav"
fc="$fc[$((A))]atempo=1.04,volume=2dB,adelay=20:all=1[a0];[$((A+1))]volume=1.5dB,adelay=3020:all=1[a1];[$((A+2))]atempo=1.05,volume=2.5dB,adelay=5970:all=1[a2];[$((A+3))]volume=1.5dB,adelay=9020:all=1[a3];[$((A+4))]volume=1dB,adelay=10900:all=1[a4];[$((A+5))]atempo=1.1,volume=1dB,adelay=18150:all=1[a5];[$((A+6))]volume=1dB,adelay=20200:all=1[a6];"
fc="$fc[a0][a1][a2][a3][a4][a5][a6]amix=inputs=7:normalize=0,aformat=channel_layouts=stereo:sample_rates=44100[vo];[vo]asplit[vo1][vo2];"
fc="$fc[$((A+7))]volume=0.32,aformat=channel_layouts=stereo:sample_rates=44100[mu];[mu][vo2]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=300[mud];[$((A+8))]volume=0.5,aformat=channel_layouts=stereo:sample_rates=44100[sf];[$((A+9))]atrim=0:3.0,volume=0.55,aformat=channel_layouts=stereo:sample_rates=44100[hs];"
fc="$fc[vo1][mud][sf][hs]amix=inputs=4:normalize=0,alimiter=limit=0.95,atrim=0:25[aout]"
ffmpeg -hide_banner -loglevel error -y $inputs -filter_complex "$fc" -map "[$prev]" -map "[aout]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -t 25 out/livekeeping_ewaybill_11pm_v5_25s.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 out/livekeeping_ewaybill_11pm_v5_25s.mp4
