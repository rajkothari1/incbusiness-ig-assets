import numpy as np, wave
SR=44100; D=3.2; N=int(SR*D); b=np.zeros(N); np.random.seed(7)
def add(t,s,g):
    i=int(t*SR); j=min(N,i+len(s)); b[i:j]+=g*s[:j-i]
tt=lambda d: np.arange(int(d*SR))/SR
# gong / bell hit at 0.05
t=tt(2.0); gong=sum(w*np.sin(2*np.pi*f*t) for f,w in [(98,1),(196,.6),(294,.4),(415,.3),(587,.2)])*np.exp(-t*1.6)*np.minimum(1,t/.003)
add(0.05,gong,0.55)
# sub boom
t=tt(.6); f=40+90*np.exp(-t*20); add(0.05,np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*5),0.9)
# ticks
for k in range(3): add(0.25+k*0.22,np.random.randn(int(.02*SR))*np.exp(-tt(.02)*400),0.25)
# whoosh into cut 0.9
t=tt(.3); add(0.75,np.random.randn(len(t))*np.sin(np.pi*t/.3)**2,0.3)
# siren 0.9-3.2: two-tone wail
t=tt(2.3); fr=np.where((t*2.6)%1<.5,720,960); ph=np.cumsum(fr)/SR
sir=np.sign(np.sin(2*np.pi*ph))*0.35+np.sin(2*np.pi*ph)*0.65; sir*=np.minimum(1,t/.1)*np.minimum(1,(2.3-t)/.2)
add(0.9,sir,0.16)
# boom at 0.9
t=tt(.5); f=45+80*np.exp(-t*25); add(0.9,np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*6),0.7)
# stamp thud 2.2
t=tt(.5); f=55+120*np.exp(-t*30); add(2.2,np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7),1.0); add(2.2,np.random.randn(int(.08*SR))*np.exp(-tt(.08)*60),0.5)
# tense pulse bass under hook
t=tt(3.2); add(0,np.sin(2*np.pi*55*t)*(0.5+0.5*np.sign(np.sin(2*np.pi*4*t)))*np.minimum(1,t/.1),0.12)
b=b/np.abs(b).max()*0.9
with wave.open('hook_sfx.wav','wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((b*32767).astype('<i2').tobytes())
