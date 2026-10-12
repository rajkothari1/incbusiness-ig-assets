set -e
S=/tmp/claude-0/-home-user-incbusiness-ig-assets/f0a3506f-6e30-5157-9541-4abd58ab7d09/scratchpad; cd $S
N="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
# hook segment 3.2s: clock 0-0.9 (sped up), checkpoint 0.9-3.2
ffmpeg -hide_banner -loglevel error -y -i gen/ch1.mp4 -i gen/ch2.mp4 -i ui/hook_ov.mov -loop 1 -t 3.2 -i ui/ov_lg.png -loop 1 -t 3.2 -i ui/ov_sh.png -i gen/vh_cut.wav -i aud/hook_sfx.wav -filter_complex "\
[0:v]trim=0.2:2.0,setpts=(PTS-STARTPTS)/2,$N,trim=0:0.9,setpts=PTS-STARTPTS[a];\
[1:v]trim=0.3:2.6,setpts=PTS-STARTPTS,$N,trim=0:2.3,setpts=PTS-STARTPTS[b];\
[a][b]concat=n=2:v=1:a=0[base];\
[base][2:v]overlay=0:0:format=auto[v1];[v1][3:v]overlay=0:0[v2];\
[4:v]format=rgba,fade=t=out:st=3.05:d=0.15:alpha=1[sub];[v2][sub]overlay=0:0,format=yuv420p[v];\
[5]volume=2dB,aformat=channel_layouts=stereo:sample_rates=44100[vo];[6]volume=0.55,aformat=channel_layouts=stereo:sample_rates=44100[sf];\
[vo][sf]amix=inputs=2:normalize=0,alimiter=limit=0.95,apad,atrim=0:3.2[a]" -map "[v]" -map "[a]" -t 3.2 -r 30 -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 44100 out/hook.mp4
ffmpeg -hide_banner -loglevel error -y -i out/hook.mp4 -i out/livekeeping_ewaybill_11pm_v3.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart out/livekeeping_ewaybill_11pm_v4.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 out/livekeeping_ewaybill_11pm_v4.mp4
