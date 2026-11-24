import json, numpy as np
from PIL import Image
im=np.array(Image.open('/home/claude/v8/main_full.png').convert('RGB')).astype(float)
rng=np.random.default_rng(31)
L=np.array([0x2a,0x20,0x15],float)
s=[]
for i in range(700):
    x=rng.uniform(392,712); y=rng.uniform(1004,1214)
    R=im[int(y)-3:int(y)+3,716:724].reshape(-1,3).mean(0)
    t=np.clip((x-400)/310,0,1)**1.3
    c=L+(R-L)*t
    c=np.clip(c*rng.uniform(0.97,1.03),0,255)
    d=np.array([x-700,y-990.]);d/=np.linalg.norm(d)+1e-6
    l=rng.uniform(14,26)
    s.append({"pts":[[x-d[0]*l/2,y-d[1]*l/2],[x+d[0]*l/2,y+d[1]*l/2]],"size":float(rng.uniform(9,13)),"color":'#%02x%02x%02x'%tuple(int(v) for v in c)})
act={"felt":{"arousal":0.15,"tension":0.1,"valence":0.1,"care":0.9},"do":[
 {"type":"strokes","brush":"flat","impasto":0.1,"load":1.3,"cover":0.95,"wetmix":0.3,"pickup":0.05,"region":{"type":"poly","pts":[[392,1004],[716,1004],[716,1214],[402,1214]]},"clip":True,"strokes":s}]}
print(json.dumps(act))
