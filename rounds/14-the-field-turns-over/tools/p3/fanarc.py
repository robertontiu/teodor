# relay a pale fan with long arcs swept around a shoulder; argv: cx cy seed size xmin xmax ymin ymax colors(comma) dir
import numpy as np, json, sys
from PIL import Image
from scipy.ndimage import median_filter, gaussian_filter, binary_erosion
cx,cy=float(sys.argv[1]),float(sys.argv[2]); seed=int(sys.argv[3]); size=float(sys.argv[4])
x0,x1,y0,y1=map(int,sys.argv[5:9]); cols=sys.argv[9].split(',')
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(float)
sch=np.stack([median_filter(im[...,i],size=21) for i in range(3)],-1)
lum=sch.mean(-1); pale=gaussian_filter(((lum>185)&(sch.max(-1)-sch.min(-1)<95)).astype(float),5)>0.5
box=np.zeros_like(pale); box[y0:y1,x0:x1]=True; m=pale&box
np.save('/tmp/fanmask.npy',m)
rng=np.random.default_rng(seed); st=[]
ys,xs=np.nonzero(m)
n=int(m.sum()/(size*size*0.9))
for i in rng.choice(len(xs),n,replace=False):
    x,y=xs[i],ys[i]; R=np.hypot(x-cx,y-cy); th=np.arctan2(y-cy,x-cx)
    span=rng.uniform(40,90)/R
    pts=[]
    for t in np.linspace(-span/2,span/2,5):
        px,py=cx+R*np.cos(th+t),cy+R*np.sin(th+t)
        if 0<=int(py)<m.shape[0] and 0<=int(px)<m.shape[1] and m[int(py),int(px)]: pts.append([round(px,1),round(py,1)])
    if len(pts)<2: continue
    st.append({"pts":pts,"size":round(size*rng.uniform(.75,1.2),1),"color":rng.choice(cols)})
print(json.dumps(st))
