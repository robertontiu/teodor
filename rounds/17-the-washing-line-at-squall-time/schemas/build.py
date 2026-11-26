import sys, numpy as np
from PIL import Image
W,H=1200,1600
def rgba(p): return np.asarray(Image.open(p).convert('RGBA')).astype(float)/255
def hexc(h): return np.array([int(h[i:i+2],16) for i in (1,3,5)])/255
def ramp(L, cols):
    cols=[hexc(c) for c in cols]; n=len(cols)-1
    t=np.clip(L,0,1)*n; i=np.clip(t.astype(int),0,n-1); f=(t-i)[...,None]
    C=np.array(cols); return C[i]*(1-f)+C[i+1]*f
def over(base, top):
    a=top[...,3:4]; base[...,:3]=base[...,:3]*(1-a)+top[...,:3]*a; return base
sky, sheet, crest, face = sys.argv[1:5]; out=sys.argv[5]
img=rgba(sky)
img=over(img, rgba(sheet))
r=np.asarray(Image.open('../blk_scene_v1.png').convert('RGB')).astype(float)/255
m=np.load('../blk_elements.npz')
L=(0.3*r[...,0]+0.59*r[...,1]+0.11*r[...,2])
Ln=np.clip((L-0.02)/0.6,0,1)
skin=m['she.arms']|m['she.hands']|m['she.neck']
cloth=m['she.drapery']|m['she.torso']|m['she.legs']
mx=r.max(-1)+1e-6; warm=(r[...,0]-r[...,2])/mx>0.25
dress=cloth&warm; shawl=cloth&~warm
yy,xx=np.mgrid[0:H,0:W]
far=shawl&(xx>650+ (yy-500)*0.05)
from scipy.ndimage import binary_dilation
far=binary_dilation(far,iterations=4)
all_=skin|cloth
edge=binary_dilation(far,iterations=2)&~(skin)
cloth=cloth&~far; shawl=shawl&~far
lay=np.zeros((H,W,4))
lay[...,:3]=np.where(skin[...,None], ramp(Ln,['#3e2c27','#6e4c3f','#a87862','#d3a68a']), lay[...,:3])
lay[...,:3]=np.where(dress[...,None], ramp(Ln,['#221a14','#3b2d21','#5a4532','#86694d']), lay[...,:3])
lay[...,:3]=np.where(shawl[...,None], ramp(Ln,['#191818','#2a2827','#403c39','#625c56']), lay[...,:3])
lay[...,3]=((skin|cloth)&~(far&~skin)).astype(float)
img=over(img, lay)
img=over(img, rgba(sys.argv[6]))
img=over(img, rgba(crest))
img=over(img, rgba(face))
Image.fromarray((np.clip(img[...,:3],0,1)*255).astype(np.uint8)).save(out)
