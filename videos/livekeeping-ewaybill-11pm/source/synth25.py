import numpy as np, wave
SR=44100; D=25.0; N=int(SR*D)
mus=np.zeros(N); sfx=np.zeros(N); np.random.seed(3)
def add(buf,t,sig,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); buf[i:j]+=g*sig[:j-i]
def env(n,a=0.005,r=0.2):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/r)
def tone(f,d,a=0.005,r=0.2,h=(1,.5,.25)):
    n=int(d*SR);t=np.arange(n)/SR
    return sum(w*np.sin(2*np.pi*f*(k+1)*t) for k,w in enumerate(h))*env(n,a,r)
def noise(d,r=0.03):
    n=int(d*SR); return np.random.randn(n)*env(n,0.001,r)
def kick():
    n=int(.35*SR);t=np.arange(n)/SR;f=50+120*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
H=3.0; UI=10.9
# tension 3.0-10.9: ticks, drone, heartbeat
for k in range(int((UI-H)/0.5)): add(sfx,H+k*0.5,noise(.03,.008)*(1 if k%2==0 else .6),0.35)
n=int((UI-H+0.1)*SR);tt=np.arange(n)/SR;L=UI-H+0.1
drone=(np.sin(2*np.pi*55*tt)+.5*np.sin(2*np.pi*82.4*tt)+.3*np.sin(2*np.pi*110.5*tt))*np.minimum(1,tt/.3)*np.minimum(1,(L-tt)/0.3)
add(mus,H,drone*(0.6+0.4*np.sin(2*np.pi*0.5*tt)),0.18)
for k in range(int(UI-H)): add(mus,H+k*1.0+0.05,kick(),0.35); add(mus,H+k*1.0+0.27,kick(),0.22)
# upbeat from UI, 124bpm
b=60/124; prog=[(261.63,329.63,392.0),(220.0,261.63,329.63),(174.61,220.0,261.63),(196.0,246.94,293.66)]
for i in range(int((D-UI)/b)):
    t=UI+i*b; ch=prog[(i//4)%4]
    add(mus,t,kick(),0.5 if i%2==0 else 0.3)
    if i%2==1: add(mus,t,noise(.15,.05),0.12)
    for j in range(2):
        add(mus,t+j*b/2,noise(.04,.01),0.05); add(mus,t+j*b/2,tone(ch[(i*2+j)%3]*2,.3,.003,.12,(1,.3,.1)),0.10)
    if i%4==0:
        for f in ch: add(mus,t,tone(f,2.0,.05,.8,(1,.2)),0.05)
        add(mus,t,tone(ch[0]/2,1.8,.01,.6,(1,.4)),0.12)
n=int(.6*SR);tt=np.arange(n)/SR; add(sfx,UI-0.6,np.random.randn(n)*(tt/.6)**2,0.25)
for t in [H,5.95,9.0,UI,18.1,20.1,21.9]:
    n=int(.35*SR);tt=np.arange(n)/SR; add(sfx,t-0.15,np.random.randn(n)*np.sin(np.pi*tt/.35)**2,0.18)
for f,dt in [(784,0),(1046.5,0.1),(1568,0.2)]: add(sfx,UI+0.05+dt,tone(f,1.0,.002,.4,(1,.3)),0.2)
for k in range(11): add(sfx,14.33+k*0.05,noise(.02,.005),0.18)
for t in [15.5,17.37]: add(sfx,t,tone(1800,.05,.001,.015,(1,)),0.45); add(sfx,t,noise(.02,.004),0.2)
for f,dt in [(1318.5,0),(1975.5,0.09),(2637,0.18)]: add(sfx,15.9+dt,tone(f,1.2,.002,.35,(1,.3)),0.22)
n=int(2.1*SR);tt=np.arange(n)/SR
eng=(np.sin(2*np.pi*38*tt)+.18*np.sign(np.sin(2*np.pi*19*tt))+.2*np.random.randn(n))*np.minimum(1,tt/.2)*np.minimum(1,(2.1-tt)/.5)
add(sfx,20.0,eng,0.25)
add(sfx,20.4,tone(330,.45,.02,.5,(1,.6,.4,.3)),0.12); add(sfx,20.4,tone(415,.45,.02,.5,(1,.6,.4,.3)),0.1)
fo=int(0.3*SR); mus[-fo:]*=np.linspace(1,0,fo)
add(mus,24.45,kick(),0.9)
for f in (261.63,329.63,392.0,523.25): add(mus,24.45,tone(f,.5,.005,.25,(1,.3)),0.12)
for name,buf in [('music25.wav',mus),('sfx25.wav',sfx)]:
    buf=buf/max(1e-9,np.abs(buf).max())*0.9
    with wave.open(name,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf*32767).astype('<i2').tobytes())
