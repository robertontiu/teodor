# head turned toward the light, seen from above: profile against the lemon, lit cheek, dark hair, neck with a lit tendon
import numpy as np
from PIL import Image
from matplotlib.path import Path
from scipy.ndimage import gaussian_filter
H0=np.array([742.,1085.]); u=np.array([0.39,0.92]); v=np.array([0.92,-0.39])
Hh,Ww=1600,1200
yy,xx=np.mgrid[0:Hh,0:Ww].astype(float)
dx,dy=xx-H0[0],yy-H0[1]
A=dx*u[0]+dy*u[1]; B=dx*v[0]+dy*v[1]
pts=np.stack([A.ravel(),B.ravel()],1)
inside=lambda poly: Path(poly).contains_points(pts).reshape(Hh,Ww)
hx=lambda h: np.array([int(h[i:i+2],16) for i in (1,3,5)],float)
img=np.asarray(Image.open('/home/claude/v14/crit_2.png').convert('RGB')).astype(float).copy()
# whole head (hair) - slightly larger than the old ball, an egg tilted
head=((A-2)/70)**2+(B/62)**2<1
# face/cheek region: profile on the +b side
prof=[(34,40),(22,52),(12,55),(4,53),(-4,63),(-12,56),(-17,57),(-21,59),(-26,55),(-32,58),(-40,54),(-50,44),(-55,32),
      (-50,22),(-36,16),(-18,14),(-2,18),(14,24),(28,30)]
face=inside(prof)
# neck: from the jaw down to the shoulders, fading
neck=inside([(-40,50),(-55,40),(-90,48),(-140,62),(-160,0),(-140,-60),(-90,-48),(-50,-40),(-30,-20)])&~face
ear=inside([(-6,4),(-2,14),(-12,20),(-24,14),(-22,2),(-12,0)])
out=img.copy()
# neck first, soft
tn=np.clip(1-np.abs(B-25-(A+50)*-0.1)/22,0,1)*np.clip((A+150)/90,0,1)
nc=hx('#3555bd')*(1-tn[...,None])+hx('#d7e5fb')*tn[...,None]
fade=np.clip((A+165)/50,0,1)
na=gaussian_filter(neck.astype(float),7)*fade
js=np.clip(1-np.abs(A+56)/10,0,1)*na
nc=nc*(1-0.5*js[...,None])+hx('#1d2b8c')*0.5*js[...,None]
out=out*(1-na[...,None])+nc*na[...,None]
hair=head&~face
out[hair]=hx('#16207a')
sheen=hair&(B>20)&(A>10)
out[sheen]=hx('#2f4bb0')
t=np.clip((B-12)/45,0,1)*0.7+np.clip((A+50)/80,0,1)*0.35
t=np.clip(t,0,1)
c0,c1,c2=hx('#5b82d8'),hx('#bcd3f6'),hx('#fffbea')
fc=np.where(t[...,None]<0.6,c0+(c1-c0)*(t[...,None]/0.6),c1+(c2-c1)*((t[...,None]-0.6)/0.4))
out[face]=fc[face]
out[ear&face]=hx('#7d9fe4')
alpha=(head|face|neck).astype(float)
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('/home/claude/v14/tools/p3/head2_sch.png')
np.save('/home/claude/v14/tools/p3/head2_mask.npy',head|face|neck)
np.save('/home/claude/v14/tools/p3/face2_mask.npy',face)
