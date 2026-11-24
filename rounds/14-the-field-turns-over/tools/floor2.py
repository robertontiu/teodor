import json, numpy as np
from PIL import Image
im=np.array(Image.open('/home/claude/v8/main_full.png').convert('RGB')).astype(float)
rng=np.random.default_rng(21)
s=[]
src=(700,990)
for i in range(90):
    x=rng.uniform(380,700); y=rng.uniform(1010,1205)
    # ray direction away from door foot
    d=np.array([x-src[0], y-src[1]]); d=d/ (np.linalg.norm(d)+1e-6)
    L=rng.uniform(40,80)
    p0=[x-d[0]*L/2,y-d[1]*L/2]; p1=[x+d[0]*L/2,y+d[1]*L/2]
    # colour: sample canvas below the patch at similar ray angle
    sx=int(np.clip(x+(1235-y)*d[0]/max(d[1],0.3),5,1190)); sy=1235
    c=im[sy-4:sy+4,sx-4:sx+4].reshape(-1,3).mean(0)
    t=(1205-y)/200  # upper rows nearer door: a touch lighter/warmer
    c=c*(1+0.12*t)+np.array([6,3,0])*t
    c=np.clip(c*rng.uniform(0.96,1.03),0,255)
    s.append({"pts":[p0,p1],"size":float(rng.uniform(14,20)),"color":'#%02x%02x%02x'%tuple(int(v) for v in c)})
act={"felt":{"arousal":0.2,"tension":0.1,"valence":0.1,"care":0.85},"do":[
 {"type":"strokes","brush":"flat","impasto":0.12,"load":1.3,"cover":0.95,"wetmix":0.25,"pickup":0.1,"region":{"type":"poly","pts":[[380,1005],[705,1005],[705,1210],[395,1210]]},"clip":True,"strokes":s}]}
print(json.dumps(act))
