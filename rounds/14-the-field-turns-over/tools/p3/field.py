# varied field strokes: broad and long far from the head, crossing dot rows; colors from a dot-free blur of the canvas
import numpy as np, json, sys
from PIL import Image
from scipy.ndimage import median_filter, binary_dilation, gaussian_filter
rmin,rmax,sp,L,size,seed,twist,brush=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),int(sys.argv[6]),float(sys.argv[7]),sys.argv[8]
darken=float(sys.argv[9]) if len(sys.argv)>9 else 0
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(float)
sch=np.stack([median_filter(im[...,i],size=17) for i in range(3)],-1)
body=binary_dilation(np.load('/home/claude/v14/tools/body_mask.npy'),iterations=10)
lum=sch.mean(-1); pale=gaussian_filter(((lum>200)&(sch.max(-1)-sch.min(-1)<70)).astype(float),6)>0.5
blk=body|pale
rng=np.random.default_rng(seed); H,W=blk.shape; cx,cy=742,1085
st=[]
for y in range(0,H,sp):
  for x in range(0,W,sp):
    x0=x+rng.uniform(0,sp); y0=y+rng.uniform(0,sp)
    if not(0<=x0<W and 0<=y0<H) or blk[int(y0),int(x0)]: continue
    R=np.hypot(x0-cx,y0-cy)
    if not (rmin<=R<rmax): continue
    pts=[[x0,y0]]; px,py=x0,y0; l=L*rng.uniform(.6,1.3)
    for k in range(4):
      dx,dy=px-cx,py-cy; r=np.hypot(dx,dy)+1e-6
      tx,ty=-dy/r,dx/r; ox,oy=dx/r,dy/r
      vx,vy=tx*twist+ox*(1-twist),ty*twist+oy*(1-twist); n=np.hypot(vx,vy)
      px+=vx/n*l/4; py+=vy/n*l/4
      if not(0<=px<W and 0<=py<H) or blk[int(py),int(px)]: break
      pts.append([round(px,1),round(py,1)])
    if len(pts)<2: continue
    c=sch[int(y0),int(x0)]
    f=1-darken*np.clip((R-rmin)/(rmax-rmin+1),0,1)
    c=np.clip(c*f*(1+rng.normal(0,0.05))+rng.normal(0,7,3),0,255).astype(int)
    st.append({"pts":[[round(a,1),round(b,1)] for a,b in pts],"size":round(size*rng.uniform(.7,1.3),1),"color":'#%02x%02x%02x'%tuple(c)})
rng.shuffle(st); print(json.dumps(st))
