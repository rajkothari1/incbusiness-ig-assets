import numpy as np, wave
SR=44100; D=30.1; N=int(SR*D)
mus=np.zeros(N); sfx=np.zeros(N)
def add(buf,t,sig,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); buf[i:j]+=g*sig[:j-i]
def env(n,a=0.005,r=0.2):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/r)
def tone(f,d,a=0.005,r=0.2,h=(1,.5,.25)):
    n=int(d*SR);t=np.arange(n)/SR
    s=sum(w*np.sin(2*np.pi*f*(k+1)*t) for k,w in enumerate(h)); return s*env(n,a,r)
def noise(d,r=0.03):
    n=int(d*SR); return np.random.randn(n)*env(n,0.001,r)
def kick():
    n=int(.35*SR);t=np.arange(n)/SR;f=50+120*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
np.random.seed(3)
# --- Part 1 (0-11.5): tension. clock ticks + low drone + heartbeat
for k in range(23):
    t=k*0.5; add(sfx,t,noise(.03,.008)*(1 if k%2==0 else .6),0.35)
n=int(11.6*SR);tt=np.arange(n)/SR
drone=(np.sin(2*np.pi*55*tt)+.5*np.sin(2*np.pi*82.4*tt)+.3*np.sin(2*np.pi*110.5*tt))*np.minimum(1,tt/1.0)*np.minimum(1,(11.6-tt)/0.4)
add(mus,0,drone*(0.6+0.4*np.sin(2*np.pi*0.5*tt)),0.18)
for k in range(11): add(mus,k*1.0+0.05,kick(),0.35); add(mus,k*1.0+0.27,kick(),0.22)
# --- Part 2 (11.5-30): upbeat, 120bpm
bpm=120;b=60/bpm;t0=11.5
prog=[(261.63,329.63,392.0),(220.0,261.63,329.63),(174.61,220.0,261.63),(196.0,246.94,293.66)] # C Am F G
for i in range(int((D-t0)/b)):
    t=t0+i*b; ch=prog[(i//4)%4]
    add(mus,t,kick(),0.5 if i%2==0 else 0.3)
    if i%2==1: add(mus,t,noise(.15,.05),0.12)
    for j in range(2):
        add(mus,t+j*b/2,noise(.04,.01),0.05)
        f=ch[(i*2+j)%3]*2; add(mus,t+j*b/2,tone(f,.3,.003,.12,(1,.3,.1)),0.10)
    if i%4==0:
        for f in ch: add(mus,t,tone(f,2.0,.05,.8,(1,.2)),0.05)
        add(mus,t,tone(ch[0]/2,1.8,.01,.6,(1,.4)),0.12)
# riser into UI + whoosh
n=int(.6*SR);tt=np.arange(n)/SR;ris=np.random.randn(n)*(tt/.6)**2
add(sfx,10.9,ris,0.25)
for t in [4.7,8.8,11.5,21.1,23.9,26.6]:
    n=int(.35*SR);tt=np.arange(n)/SR;w=np.random.randn(n)*np.sin(np.pi*tt/.35)**2
    add(sfx,t-0.15,w,0.18)
# UI taps / typing / ding
U=11.5
for t in [6.9,8.9]: add(sfx,U+t,tone(1800,.05,.001,.015,(1,)),0.45); add(sfx,U+t,noise(.02,.004),0.2)
for k in range(11): add(sfx,U+5.4+k*0.06,noise(.02,.005),0.18)
for f,dt in [(784,0),(1046.5,0.1),(1568,0.2)]: add(sfx,U+0.05+dt,tone(f,1.0,.002,.4,(1,.3)),0.2)
for f,dt in [(1318.5,0),(1975.5,0.09),(2637,0.18)]: add(sfx,U+7.5+dt,tone(f,1.2,.002,.35,(1,.3)),0.22)
# truck engine for S5
n=int(2.9*SR);tt=np.arange(n)/SR
eng=(np.sin(2*np.pi*38*tt)+.6*np.sign(np.sin(2*np.pi*19*tt))*.3+.2*np.random.randn(n))*np.minimum(1,tt/.3)*np.minimum(1,(2.9-tt)/.6)
add(sfx,23.8,eng,0.25)
# horn
add(sfx,24.4,tone(330,.45,.02,.5,(1,.6,.4,.3)),0.12); add(sfx,24.4,tone(415,.45,.02,.5,(1,.6,.4,.3)),0.1)
# final fade
fo=int(0.35*SR); mus[-fo:]*=np.linspace(1,0,fo)
add(mus,29.55,kick(),0.9)
for f in (261.63,329.63,392.0,523.25): add(mus,29.55,tone(f,.5,.005,.25,(1,.3)),0.12)
for name,buf in [('music.wav',mus),('sfx.wav',sfx)]:
    buf=buf/max(1e-9,np.abs(buf).max())*0.9
    with wave.open(name,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf*32767).astype('<i2').tobytes())
