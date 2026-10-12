import numpy as np, json, wave
SR=44100
T=json.load(open('timeline.json'))
dur=T['total']; N=int(dur*SR)
out=np.zeros((N,2))
bpm=96; beat=60/bpm; bar=4*beat
def note(m): return 440*2**((m-69)/12)
def env(n,a,r):
    e=np.ones(n); a=min(int(a*SR),n); e[:a]=np.linspace(0,1,a)
    e*=np.exp(-np.arange(n)/(r*SR)); return e
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); 
    if i>=N: return
    s=sig[:N-i]*g
    out[i:i+len(s),0]+=s*(1-pan)/1; out[i:i+len(s),1]+=s*(1+pan)/1
# chords: Am F C G  (lofi-ish with 7ths)
prog=[[57,60,64,67],[53,57,60,64],[48,55,60,64],[55,59,62,65]]
bass=[45,41,48,43]
t=0; k=0
rng=np.random.default_rng(1)
while t<dur:
    c=prog[k%4]
    # pad
    n=int(bar*SR*1.05); tt=np.arange(n)/SR
    pad=sum(np.sin(2*np.pi*note(m)*tt)*0.5+np.sin(2*np.pi*note(m)*1.003*tt)*0.5 for m in c)
    pe=np.minimum(1,tt/0.6)*np.minimum(1,(bar*1.05-tt)/0.5)
    add(pad*pe*0.035,t)
    # bass
    for b in [0,2.5]:
        n=int(beat*1.4*SR); tt=np.arange(n)/SR
        bs=np.sin(2*np.pi*note(bass[k%4])*tt)+0.3*np.sin(2*np.pi*note(bass[k%4]+12)*tt)
        add(bs*env(n,0.01,0.5)*0.16,t+b*beat)
    # pluck arpeggio 8ths
    arp=[c[0]+12,c[2]+12,c[1]+12,c[3]+12,c[2]+12,c[0]+24,c[3]+12,c[1]+12]
    for j,m in enumerate(arp):
        n=int(0.5*SR); tt=np.arange(n)/SR
        f=note(m); s=(np.sin(2*np.pi*f*tt)+0.25*np.sin(4*np.pi*f*tt))*env(n,0.003,0.12)
        add(s*0.05,t+j*beat/2,pan=0.3*np.sin(j))
    # drums
    for b in range(4):
        bt=t+b*beat
        if b in (0,2):
            n=int(0.3*SR); tt=np.arange(n)/SR
            kick=np.sin(2*np.pi*(50+90*np.exp(-tt*30))*tt)*np.exp(-tt*9)
            add(kick*0.33,bt)
        if b in (1,3):
            n=int(0.25*SR); tt=np.arange(n)/SR
            sn=rng.standard_normal(n)*np.exp(-tt*22)*0.6+np.sin(2*np.pi*190*tt)*np.exp(-tt*30)*0.4
            add(sn*0.10,bt)
        for h in (0,0.5):
            n=int(0.06*SR); hh=np.diff(rng.standard_normal(n+1))*np.exp(-np.arange(n)/SR*70)
            add(hh*0.03,bt+h*beat+ (0.02 if h else 0),pan=-0.3)
    t+=bar; k+=1
# simple delay reverb
d=int(0.23*SR); rev=out.copy()
for r in range(1,5): rev[d*r:]+=out[:-d*r]*(0.35**r)
out=rev
# fade in/out
fi=int(1.0*SR); out[:fi]*=np.linspace(0,1,fi)[:,None]
fo=int(2.0*SR); out[-fo:]*=np.linspace(1,0,fo)[:,None]
# SFX: whoosh on scene changes, pop on each line
sfx=np.zeros((N,2))
def addsfx(sig,t,g):
    i=int(t*SR); s=sig[:max(0,N-i)]*g; sfx[i:i+len(s)]+=s[:,None]
prev=None
for x in T['lines']:
    if x['s']!=prev and prev is not None:
        n=int(0.6*SR); tt=np.arange(n)/SR
        w=rng.standard_normal(n); 
        # bandpass sweep approx: cumulative smoothing
        a=np.exp(-((tt-0.3)/0.15)**2)
        w=np.convolve(w,np.ones(12)/12,'same')*a
        addsfx(w,x['t0']-0.45,0.5)
    prev=x['s']
    n=int(0.12*SR); tt=np.arange(n)/SR
    pop=np.sin(2*np.pi*(900-500*tt/0.12)*tt)*np.exp(-tt*40)
    addsfx(pop,x['t0']-0.05,0.10)
# ding at key reveals
for tk in [19.42, 22.2, 27.9, 37.8, 44.9, 48.9, 53.15, 64.2, 71.2, 73.74]:
    n=int(1.0*SR); tt=np.arange(n)/SR
    dg=(np.sin(2*np.pi*1568*tt)+0.5*np.sin(2*np.pi*2349*tt))*np.exp(-tt*5)
    addsfx(dg,tk,0.10)
np.save('music.npy',out); np.save('sfx.npy',sfx)
def wr(fn,a):
    a=np.clip(a,-1,1); w=wave.open(fn,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a*32767).astype('<i2').tobytes()); w.close()
wr('music.wav',out/np.abs(out).max()*0.9); wr('sfx.wav',sfx)
print('ok',dur)
