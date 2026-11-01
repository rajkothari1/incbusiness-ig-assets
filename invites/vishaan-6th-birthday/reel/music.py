"""Synthesizes a 10s (full song) 'Happy Birthday to You' (public-domain melody) as music-box + soft chords."""
import numpy as np, wave, sys
SR=44100; DUR=10.0; BPM=172; B=60/BPM
def f(n):  # MIDI -> Hz
    return 440*2**((n-69)/12)
G4,A4,B4,C5,D5=67,69,71,72,74
# (note, start_beat, length_beats)
E5,F5,G5=76,77,79
mel=[(G4,0,.75),(G4,.75,.25),(A4,1,1),(G4,2,1),(C5,3,1),(B4,4,3),
     (G4,7,.75),(G4,7.75,.25),(A4,8,1),(G4,9,1),(D5,10,1),(C5,11,3),
     (G4,14,.75),(G4,14.75,.25),(G5,15,1),(E5,16,1),(C5,17,1),(B4,18,1),(A4,19,2),
     (F5,21,.75),(F5,21.75,.25),(E5,22,1),(C5,23,1),(D5,24,1),(C5,25,4)]
chords=[([48,52,55],1,3),([43,47,50,53],4,3),([43,47,50,53],8,3),([48,52,55],11,3),
        ([48,52,55,58],15,3),([41,45,48],18,3),([48,52,55],22,2),([43,47,50,53],24,1),([48,52,55,60],25,4)]
out=np.zeros(int(SR*DUR)+SR)
def bell(freq,t0,length,amp):
    n=int(SR*(length+0.6)); t=np.arange(n)/SR
    env=np.exp(-t*3.2)*np.minimum(1,t/0.005)
    tone=(np.sin(2*np.pi*freq*t)+.45*np.sin(2*np.pi*2*freq*t)*np.exp(-t*5)
          +.25*np.sin(2*np.pi*3.01*freq*t)*np.exp(-t*8)+.12*np.sin(2*np.pi*4.2*freq*t)*np.exp(-t*12))
    i=int(SR*t0); seg=out[i:i+n]; seg+=amp*env[:len(seg)]*tone[:len(seg)]
def pad(freq,t0,length,amp):
    n=int(SR*length); t=np.arange(n)/SR
    env=np.minimum(1,t/0.08)*np.minimum(1,(length-t)/0.25).clip(0)
    tone=np.sin(2*np.pi*freq*t)+.3*np.sin(2*np.pi*2*freq*t)
    i=int(SR*t0); seg=out[i:i+n]; seg+=amp*env[:len(seg)]*tone[:len(seg)]
OFF=0.15
for n,s,l in mel:
    bell(f(n),OFF+s*B,l*B,.55); bell(f(n+12),OFF+s*B,l*B,.12)
for notes,s,l in chords:
    for n in notes: pad(f(n),OFF+s*B,l*B,.07)
    # little "oom-pah" bass on each beat
    for k in range(int(l)):
        bell(f(notes[0]-12),OFF+(s+k)*B,B,.25 if k==0 else .12)
# sparkle at the start
for k,n in enumerate([84,88,91,96]): bell(f(n),0.02+k*0.06,.3,.08)
out=out[:int(SR*DUR)]
fade=int(SR*.6); out[-fade:]*=np.linspace(1,0,fade)
out=out/np.abs(out).max()*0.85
pcm=(out*32767).astype(np.int16)
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
