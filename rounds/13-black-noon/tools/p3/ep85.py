import sys,math,json,numpy as np; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
c=np.load('main_col.npy').astype(np.float32)
last=json.load(open('/home/claude/v13/tools/last_act.json'))
liner=last['do'][2]['strokes']
bad=[s for s in liner if not (abs(s['pts'][0][0]-552)<110 and abs(s['pts'][0][1]-458)<110)]   # keep the sun rims
out=[]
for s in bad:
    for i in range(len(s['pts'])-1):
        (x0,y0),(x1,y1)=s['pts'][i],s['pts'][i+1]
        xs=slice(max(0,min(x0,x1)-10),max(x0,x1)+10); ys=slice(max(0,min(y0,y1)-10),max(y0,y1)+10)
        p=c[ys,xs].reshape(-1,3); p=p[p.mean(1)<0.6]
        col=np.median(p,0) if len(p) else np.array([0.3,0.1,0.08])
        out.append({"pts":[[x0,y0],[x1,y1]],"size":7,"color":'#%02x%02x%02x'%tuple(int(v*255) for v in col)})
act({"arousal":0.15,"tension":0.05,"valence":-0.2,"care":1.0},[{"type":"strokes","brush":"round","edge":"soft","strokes":out,"wetmix":0.5}])
