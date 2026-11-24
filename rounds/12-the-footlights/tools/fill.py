# usage: fill.py MASK.png COLORS(comma) SIZE STEP LEN ANGLE SPREAD SEED [contour] [nofig] [brush] [edge]
# fills the mask with short angled strokes that stay inside it; 'contour' also traces the outline
import json, sys, random, math
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, binary_erosion
from skimage.measure import find_contours
a=sys.argv
M=np.array(Image.open(a[1]).convert('RGBA'))[...,3]>60
cols=a[2].split(','); size=float(a[3]); step=int(a[4]); L=float(a[5]); ang=float(a[6]); spr=float(a[7])
random.seed(int(a[8])); np.random.seed(int(a[8]))
flags=a[9:]
fig=np.array(Image.open('/home/claude/v12/gen/mask_fig56.png').convert('RGBA'))[...,3]>30
if 'nofig' not in flags: M=M&~binary_dilation(fig,iterations=5)
inner=binary_erosion(M,iterations=max(1,int(size*0.45)))
H,W=M.shape
def ok(x,y): 
    x=int(round(x)); y=int(round(y))
    return 0<=x<W and 0<=y<H and inner[y,x]
S=[]
for y in range(0,H,step):
    for x in range(0,W,step):
        cx=x+random.uniform(0,step); cy=y+random.uniform(0,step)
        if not ok(cx,cy): continue
        t=math.radians(ang+random.uniform(-spr,spr)); l=L*random.uniform(0.6,1.3)
        dx,dy=math.cos(t)*l/2,math.sin(t)*l/2
        p0=[cx-dx,cy-dy]; p2=[cx+dx,cy+dy]
        k=1.0
        while (not ok(*p0) or not ok(*p2)) and k>0.2:
            k*=0.7; p0=[cx-dx*k,cy-dy*k]; p2=[cx+dx*k,cy+dy*k]
        if not (ok(*p0) and ok(*p2)): continue
        S.append({"pts":[[round(p0[0]),round(p0[1])],[round(cx+random.uniform(-2,2)),round(cy)],[round(p2[0]),round(p2[1])]],"size":round(size*random.uniform(0.8,1.15),1),"color":random.choice(cols)})
random.shuffle(S)
out=[{"type":"strokes","brush":(flags[flags.index('brush')+1] if 'brush' in flags else 'flat'),"strokes":S,"edge":(flags[flags.index('edge')+1] if 'edge' in flags else 'soft')}]
if 'contour' in flags:
    C=[]
    Mc=np.array(Image.open(a[1]).convert('RGBA'))[...,3]>60
    figd4=binary_dilation(fig,iterations=4)
    for c in find_contours(Mc.astype(float),0.5):
        if len(c)<20: continue
        seg=12
        for i in range(0,len(c)-seg,seg):
            pts=c[i:i+seg+1:6]
            # skip contour bits that are on the figure or on the clip box
            ym,xm=pts[len(pts)//2]
            if figd4[int(ym),int(xm)]: continue
            C.append({"pts":[[round(p[1]),round(p[0])] for p in pts],"size":size*0.55,"color":cols[0]})
    out.append({"type":"strokes","brush":"round","strokes":C,"edge":"hard"})
print(json.dumps(out))
