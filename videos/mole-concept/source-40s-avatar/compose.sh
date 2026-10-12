set -e
cd av
# trim each clip to its chunk length, 30fps, 250x250
L=(9.76 13.42 13.75 4.89)
for k in 0 1 2 3; do ffmpeg -v error -y -i t$k.mp4 -t ${L[$k]} -an -vf "fps=30,crop=600:600:190:170,scale=250:250:flags=lanczos,setsar=1" -c:v libx264 -crf 14 -pix_fmt yuv420p c$k.mp4; done
printf "file c0.mp4\nfile c1.mp4\nfile c2.mp4\nfile c3.mp4\n" > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy avatar.mp4
# circle mask
ffmpeg -v error -y -f lavfi -i "color=black:s=250x250,format=gray,geq=lum='if(lt(hypot(X-124.5,Y-124.5),124),255,0)'" -frames:v 1 mask.png
cd ..
ffmpeg -v error -y -i vo.wav -af "loudnorm=I=-15:TP=-1.5:LRA=11" -ar 44100 -ac 2 von.wav
python3 - <<'PY'
import numpy as np, wave
def rd(f):
    w=wave.open(f);n=w.getnframes();ch=w.getnchannels();a=np.frombuffer(w.readframes(n),'<i2').astype(float)/32768;return a.reshape(-1,ch)
v=rd('von.wav');m=rd('music.wav');s=rd('sfx.wav')
N=max(len(v),len(m));pad=lambda a:np.vstack([a,np.zeros((N-len(a),2))]);v,m,s=pad(v),pad(m),pad(s)
SR=44100;env=np.abs(v).max(1);k=int(.25*SR);env=np.convolve(env,np.ones(k)/k,'same')
duck=np.where(env>0.01,0.11,0.30);k2=int(.3*SR);duck=np.convolve(duck,np.ones(k2)/k2,'same')
out=v+m*duck[:,None]+s*0.9;out=np.clip(out/max(1,np.abs(out).max()/0.95),-1,1)
w=wave.open('mix.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((out*32767).astype('<i2').tobytes());w.close()
PY
ffmpeg -v error -y -i silent.mp4 -i av/avatar.mp4 -loop 1 -i av/mask.png -i mix.wav \
 -filter_complex "[1:v][2:v]alphamerge[av];[0:v][av]overlay=755:1345:shortest=0:eof_action=pass[v]" \
 -map "[v]" -map 3:a -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -t 41.82 -movflags +faststart final40.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 final40.mp4
