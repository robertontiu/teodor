# strokes that fill a mask, following the form (perpendicular to the distance gradient), colors sampled from the schema
import numpy as np, json, sys
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter
mask=np.load(sys.argv[1]); sch=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(float)
sp=int(sys.argv[3]); L=float(sys.argv[4]); size=float(sys.argv[5]); seed=int(sys.argv[6])
region=json.loads(sys.argv[7]) if len(sys.argv)>7 else None
shift=float(sys.argv[8]) if len(sys.argv)>8 else 0.0
rng=np.random.default_rng(seed)
d=gaussian_filter(distance_transform_edt(mask),4); gy,gx=np.gradient(d)
H,W=mask.shape; st=[]
for y in range(sp//2,H,sp):
  for x in range(sp//2,W,sp):
    x0=int(np.clip(x+rng.uniform(-sp/2,sp/2),0,W-1)); y0=int(np.clip(y+rng.uniform(-sp/2,sp/2),0,H-1))
    if not mask[y0,x0]: continue
    if region and not (region[0]<=x0<region[0]+region[2] and region[1]<=y0<region[1]+region[3]): continue
    vx,vy=-gy[y0,x0],gx[y0,x0]; n=np.hypot(vx,vy)
    if n<1e-3: a=rng.uniform(0,np.pi); vx,vy=np.cos(a),np.sin(a)
    else: vx,vy=vx/n,vy/n
    l=L*rng.uniform(.6,1.1); pts=[]
    for t in (-.5,0,.5):
      px,py=x0+vx*l*t,y0+vy*l*t
      if 0<=int(py)<H and 0<=int(px)<W and mask[int(py),int(px)]: pts.append([round(px,1),round(py,1)])
    if len(pts)<2: pts=[[x0-vx*3,y0-vy*3],[x0+vx*3,y0+vy*3]]
    c=sch[y0,x0]*(1+shift); c=np.clip(c,0,255).astype(int)
    st.append({"pts":pts,"size":round(size*rng.uniform(.8,1.15),1),"color":'#%02x%02x%02x'%tuple(c)})
print(json.dumps(st))
