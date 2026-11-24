# schema L: field value gradient, snow-angel wings (pressed bright grass), short contact shadow, dot-rings
import numpy as np, sys, math
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt, binary_opening, binary_closing, gaussian_filter, binary_fill_holes
from scipy.spatial import ConvexHull
A=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)/255; out=sys.argv[2]
H,W=A.shape[:2]; r,g,b=A[...,0],A[...,1],A[...,2]
body=binary_opening((b>r+0.15)&(b>g+0.04),iterations=2); body=binary_fill_holes(binary_closing(body,iterations=3))
ghost=binary_opening((r>g+0.25)&((r>b+0.15)|(b>g+0.25)) & ~body,iterations=2)
yy,xx=np.mgrid[0:H,0:W]
# head centre (given) and torso
hx,hy=float(sys.argv[3]),float(sys.argv[4])
# wings: convex hull of ghost + nearby arms, per side (split by line through head along torso axis)
def hull_mask(m):
    pts=np.argwhere(m)[:, ::-1]
    if len(pts)<10: return np.zeros_like(m)
    hl=ConvexHull(pts); poly=[tuple(pts[i]) for i in hl.vertices]
    im=Image.new('L',(W,H),0); ImageDraw.Draw(im).polygon(poly,fill=255); return np.asarray(im)>0
side=(xx-hx)*0.55-(yy-hy)*0.83>0   # crude split
armzone=((xx-hx)**2+(yy-hy)**2)<520**2
wing=np.zeros((H,W),bool)
for s in (side,~side):
    m=(ghost|(body&armzone&(np.hypot(xx-hx,yy-hy)>120)))&s&armzone
    wing|=hull_mask(ghost&s|(m&binary_opening(m,iterations=6)))
wing&=~body
dout=distance_transform_edt(~body); din=distance_transform_edt(body)
dw=distance_transform_edt(~(body|(gaussian_filter(wing.astype(float),38)>0.45)|ghost))
# field: far = deep viridian, near = acid yellow-green, wing = pale lemon-white
far=(np.clip((dw-40)/380,0,1)**0.8)[...,None]
near=np.array([0.80,0.88,0.20]); deep=np.array([0.10,0.42,0.30])
F=near*(1-far)+deep*far
# grass flicker
rng=np.random.default_rng(7); n=gaussian_filter(rng.normal(0,1,(H,W)),6); F=F*(1+0.10*n[...,None])
wingglow=np.clip(gaussian_filter(wing.astype(float),38)*0.75+gaussian_filter(ghost.astype(float),7)*0.9,0,1)
wingcol=np.array([1.0,0.98,0.80])
F=F*(1-wingglow[...,None]*0.92)+wingcol*wingglow[...,None]*0.92
# halo of light close to the body edge (bleached grass), short
halo=np.exp(-dout/45)*(~body); F=F*(1-0.55*halo[...,None])+np.array([1,0.97,0.75])*0.55*halo[...,None]
# contact shadow: original shadow, only within 70 px of body, teal
lum=0.3*r+0.6*g+0.1*b; shadow=(lum<0.45)&~body&~ghost&(dout<70)&(dout>3)
sh=gaussian_filter(shadow.astype(float),3)*np.clip(1-dout/80,0,1)
F=F*(1-0.75*sh[...,None])+np.array([0.05,0.30,0.36])*0.75*sh[...,None]
# body: keep render, push cobalt; lit planes toward cerulean
B=A.copy(); bl=0.3*B[...,0]+0.6*B[...,1]+0.1*B[...,2]
cob=np.array([0.11,0.20,0.72]); cer=np.array([0.40,0.66,0.98]); dark=np.array([0.05,0.07,0.38])
t=np.clip((bl-0.18)/0.25,0,1)[...,None]
Bc=np.where(t<0.5, dark*(1-2*t)+cob*2*t, cob*(2-2*t)+cer*(2*t-1))
img=np.where(body[...,None],Bc,F)
im=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)); d=ImageDraw.Draw(im)
# dot rings: rows along distance contours from body|wing
def ring_pts(dist,band,spacing,mask):
    cand=np.argwhere((np.abs(dist-band)<1.0)&mask); rng.shuffle(cand); pts=[]
    grid={}
    for y,x in cand:
        k=(x//spacing,y//spacing); ok=True
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for (px,py) in grid.get((k[0]+dx,k[1]+dy),[]):
                    if (px-x)**2+(py-y)**2<spacing**2: ok=False;break
                if not ok:break
            if not ok:break
        if ok: pts.append((x,y)); grid.setdefault(k,[]).append((x,y))
    return pts
calm=np.hypot(xx-1150,yy-80)>430   # upper-right corner rests
cols=[(255,92,150),(255,252,235),(255,92,150),(40,190,200),(255,252,235)]
for k,band in enumerate(range(30,470,46)):
    rad=max(3.5,13-k*1.0); sp=int(rad*5.2)
    for (x,y) in ring_pts(dw,band,sp,~body&calm):
        fade=1-band/560
        if rng.random()>fade+0.15: continue
        c=cols[k%len(cols)]; d.ellipse([x-rad,y-rad,x+rad,y+rad],fill=c)
# on the body: inward rows, lemon and rose, densest at edge
for k,band in enumerate(range(14,60,22)):
    rad=max(3.0,7-k*2); sp=int(rad*6)
    for (x,y) in ring_pts(din,band,sp,body):
        if rng.random()>1-k*0.22: continue
        c=(250,240,90) if k%2==0 else (255,120,170); d.ellipse([x-rad,y-rad,x+rad,y+rad],fill=c)
im.save(out); im.resize((450,600)).save('/tmp/schL_s.png')
np.save('/tmp/body_mask.npy',body); np.save('/tmp/wing_mask.npy',wing)
