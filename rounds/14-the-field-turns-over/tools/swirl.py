# grass strokes outside a mask, curving around a centre (vortex), colors from schema with broken jitter
import numpy as np, json, sys
from PIL import Image
from scipy.ndimage import binary_dilation
mask=np.load(sys.argv[1]); sch=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(float)
sp=int(sys.argv[3]); L=float(sys.argv[4]); size=float(sys.argv[5]); seed=int(sys.argv[6])
cx,cy,twist=map(float,sys.argv[7].split(',')); jit=float(sys.argv[8]); dil=int(sys.argv[9])
keep=json.loads(sys.argv[10]) if len(sys.argv)>10 else None
rng=np.random.default_rng(seed); H,W=mask.shape
m=binary_dilation(mask,iterations=dil) if dil>0 else mask
st=[]
for y in range(0,H,sp):
  for x in range(0,W,sp):
    x0=x+rng.uniform(0,sp); y0=y+rng.uniform(0,sp)
    if not(0<=x0<W and 0<=y0<H) or m[int(y0),int(x0)]: continue
    if keep and not (keep[0]<=x0<keep[0]+keep[2] and keep[1]<=y0<keep[1]+keep[3]): continue
    pts=[[x0,y0]]; px,py=x0,y0
    for k in range(3):
      dx,dy=px-cx,py-cy; r=np.hypot(dx,dy)+1e-6
      # tangent plus outward component
      tx,ty=-dy/r,dx/r; ox,oy=dx/r,dy/r
      vx,vy=tx*twist+ox*(1-twist),ty*twist+oy*(1-twist); n=np.hypot(vx,vy); vx/=n; vy/=n
      px+=vx*L/3; py+=vy*L/3
      if not(0<=px<W and 0<=py<H) or m[int(py),int(px)]: break
      pts.append([round(px,1),round(py,1)])
    if len(pts)<2: continue
    c=sch[int(y0),int(x0)]*(1+rng.normal(0,jit)); c=np.clip(c+rng.normal(0,jit*60,3),0,255).astype(int)
    st.append({"pts":[[round(a,1),round(b,1)] for a,b in pts],"size":round(size*rng.uniform(.75,1.2),1),"color":'#%02x%02x%02x'%tuple(c)})
rng.shuffle(st); print(json.dumps(st))
