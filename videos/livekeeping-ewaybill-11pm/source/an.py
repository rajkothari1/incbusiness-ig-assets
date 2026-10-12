import numpy as np,subprocess,sys
def load(f):
    b=subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    return np.frombuffer(b,'<i2').astype(float)/32768
for f in sys.argv[1:]:
    x=load(f);sr=16000;fl=640;hop=320
    fr=[x[i:i+fl] for i in range(0,len(x)-fl,hop)]
    rms=np.array([np.sqrt((g**2).mean()) for g in fr]);voiced=rms>rms.max()*0.15
    p=[]
    for g,v in zip(fr,voiced):
        if not v: continue
        g=g-g.mean();ac=np.correlate(g,g,'full')[fl-1:];lo,hi=sr//400,sr//70
        k=lo+np.argmax(ac[lo:hi]);
        if ac[k]>0.3*ac[0]: p.append(sr/k)
    p=np.array(p);st=12*np.log2(p/np.median(p))
    print(f"{f:10s} dur={len(x)/sr:5.2f}s voiced={voiced.mean()*len(x)/sr:4.2f}s medF0={np.median(p):5.0f}Hz pitchSD={st.std():4.2f}st loud={20*np.log10(rms[voiced].mean()):5.1f}dB dyn={rms[voiced].std()/rms[voiced].mean():.2f}")
