# shaded schema for neck + upturned face; writes mask and schema image
import numpy as np, json
from PIL import Image
H0=np.array([742.,1085.]); u=np.array([0.39,0.92]); v=np.array([0.92,-0.39])
Hh,Ww=1600,1200
yy,xx=np.mgrid[0:Hh,0:Ww].astype(float)
dx,dy=xx-H0[0],yy-H0[1]
a=dx*u[0]+dy*u[1]; b=dx*v[0]+dy*v[1]
L=np.array([0.55,-0.45,0.70]); L/=np.linalg.norm(L)
shade=np.full((Hh,Ww),-1.0); mask=np.zeros((Hh,Ww),bool)
# neck capsule from a=-150 to a=-50, radius widening toward the shoulders
r=np.clip(40+np.clip(-a-90,0,60)*0.4,40,62)
s=b/r; inn=(a>-160)&(a<-45)&(np.abs(s)<1)
nz=np.sqrt(np.clip(1-s**2,0,1))
sv=np.stack([s*v[0],s*v[1],nz],-1)
sh=(sv@L)
alpha=np.zeros((Hh,Ww)); fade=np.clip((a+140)/45,0,1)*np.clip((1-np.abs(s))*3,0,1)
mask|=inn; shade[inn]=sh[inn]*0.55; alpha[inn]=fade[inn]
# face: ellipsoid, foreshortened
ea,eb=29.,45.; fa=(a+30)/ea; fb=b/eb; inf=(fa**2+fb**2)<1
nz2=np.sqrt(np.clip(1-fa**2-fb**2,0,1))
nx=fa*u[0]+fb*v[0]; ny=fa*u[1]+fb*v[1]
n=np.stack([nx*0.8,ny*0.8,nz2+0.3],-1); n/=np.linalg.norm(n,axis=-1,keepdims=True)
sh2=n@L+0.12
mask|=inf; shade[inf]=np.maximum(shade[inf],sh2[inf]); alpha[inf]=np.maximum(alpha[inf],np.clip((1-(fa**2+fb**2))*6,0,1)[inf])
ramp=[(0,'#1d2b8c'),(0.35,'#3f66c9'),(0.6,'#7fa6ea'),(0.82,'#cfe0fa'),(1.0,'#fffbe9')]
def col(t):
    t=np.clip(t,0,1); out=np.zeros(t.shape+(3,))
    for (t0,c0),(t1,c1) in zip(ramp[:-1],ramp[1:]):
        k=(t>=t0)&(t<=t1); w=((t-t0)/(t1-t0))[k][:,None]
        a0=np.array([int(c0[i:i+2],16) for i in (1,3,5)]);a1=np.array([int(c1[i:i+2],16) for i in (1,3,5)])
        out[k]=a0*(1-w)+a1*w
    return out
img=np.asarray(Image.open('/home/claude/v14/crit_2.png').convert('RGB')).astype(float)
if img.shape[:2]!=(Hh,Ww): img=np.asarray(Image.open('/home/claude/v14/crit_2.png').convert('RGB').resize((Ww,Hh))).astype(float)
hr=(((a+22)/42)**2+(b/60)**2<1)&~inf&(a>-52)
mask|=hr; shade[hr]=-0.2; alpha[hr]=1.0
img=img.copy(); al=alpha[mask][:,None]; img[mask]=img[mask]*(1-al)+col(shade[mask])*al
mask=alpha>0.15; np.save('/home/claude/v14/tools/p3/alpha.npy',alpha)
Image.fromarray(img.astype(np.uint8)).save('/home/claude/v14/tools/p3/head_sch.png')
np.save('/home/claude/v14/tools/p3/head_mask.npy',mask)
np.save('/home/claude/v14/tools/p3/face_mask.npy',inf)
print(mask.sum(),inf.sum())
