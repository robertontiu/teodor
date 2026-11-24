import json, math, random, sys
from matplotlib.path import Path
def hatch(poly, angle, spacing, size, colors, seglen=(80,180), jitter=0.3, seed=0, wobble=6):
    rnd=random.Random(seed); P=Path(poly)
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
    R=max(max(xs)-min(xs),max(ys)-min(ys))
    a=math.radians(angle); dx,dy=math.cos(a),math.sin(a); nx,ny=-dy,dx
    out=[]
    t=-R
    while t<R:
        # walk along line, collect inside runs
        s=-R; run=[]
        while s<R:
            x=cx+nx*t+dx*s; y=cy+ny*t+dy*s
            if P.contains_point((x,y)): run.append((x,y))
            elif run: 
                out+=chop(run,seglen,rnd,size,colors,wobble); run=[]
            s+=8
        if run: out+=chop(run,seglen,rnd,size,colors,wobble)
        t+=spacing*(1+rnd.uniform(-jitter,jitter))
    rnd.shuffle(out); return out
def chop(run,seglen,rnd,size,colors,wob):
    res=[];i=0
    while i<len(run)-1:
        n=max(2,int(rnd.uniform(*seglen)/8)); seg=run[i:i+n]
        if len(seg)>=2:
            pts=[[round(x+rnd.uniform(-wob,wob)),round(y+rnd.uniform(-wob,wob))] for x,y in seg[::max(1,len(seg)//4)]]
            if len(pts)<2: pts=[list(map(round,seg[0])),list(map(round,seg[-1]))]
            c=rnd.choices([c if isinstance(c,str) else c[0] for c in colors],[1 if isinstance(c,str) else c[1] for c in colors])[0]
            res.append({"pts":pts,"size":round(rnd.uniform(*size),1),"color":c})
        i+=n-1
    return res
if __name__=="__main__":
    spec=json.load(sys.stdin)
    print(json.dumps(hatch(**spec)))

def hatch_mask(mask, angle, spacing, size, colors, seglen=(80,180), seed=0, wobble=4, step=6, colorfn=None):
    """mask: bool array HxW. strokes along angle, broken where mask is false."""
    import numpy as np
    rnd=random.Random(seed); H,W=mask.shape
    a=math.radians(angle); dx,dy=math.cos(a),math.sin(a); nx,ny=-dy,dx
    cx,cy=W/2,H/2; R=math.hypot(W,H)/2
    out=[]; t=-R
    while t<R:
        s=-R; run=[]
        while s<R:
            x=cx+nx*t+dx*s; y=cy+ny*t+dy*s
            xi,yi=int(x),int(y)
            if 0<=xi<W and 0<=yi<H and mask[yi,xi]: run.append((x,y))
            elif run: out+=chop(run,seglen,rnd,size,colors,wobble); run=[]
            s+=step
        if run: out+=chop(run,seglen,rnd,size,colors,wobble)
        t+=spacing*(1+rnd.uniform(-0.3,0.3))
    if colorfn:
        for o in out:
            x,y=o["pts"][len(o["pts"])//2]; o["color"]=colorfn(x,y,rnd)
    rnd.shuffle(out); return out
