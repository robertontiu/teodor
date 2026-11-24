import numpy as np, math
from scipy.ndimage import gaussian_filter, distance_transform_edt
from PIL import Image, ImageDraw
def hx(h): return np.array([int(h[i:i+2],16)/255 for i in (1,3,5)],np.float32)
H,W=1600,1200
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
def capsule(a,b,ra,rb,box):
    x0,y0,x1,y1=box
    X=xx[y0:y1,x0:x1]; Y=yy[y0:y1,x0:x1]
    ax,ay=a; bx,by=b; vx,vy=bx-ax,by-ay; L2=vx*vx+vy*vy+1e-6
    t=np.clip(((X-ax)*vx+(Y-ay)*vy)/L2,0,1)
    d=np.hypot(X-(ax+t*vx),Y-(ay+t*vy)); r=ra+(rb-ra)*t
    return np.sqrt(np.clip(r*r-d*d,0,None)), t
def render_hand(img,alpha,chains,palm_poly,dark,light,rim,box,thick=22,light_dir=(0.0,-0.25,1.0),rim_dir=(0,-1),creases=True):
    x0,y0,x1,y1=box
    h=np.zeros((y1-y0,x1-x0),np.float32)
    # palm: inside distance -> height
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon([tuple(p) for p in palm_poly],fill=255)
    pm=gaussian_filter(np.array(m)[y0:y1,x0:x1].astype(np.float32),6)>127
    dist=distance_transform_edt(pm)
    hp=np.where(pm,thick*np.sqrt(np.clip(dist/thick,0,1)*(2-np.clip(dist/thick,0,1))),0)*0.55
    h=np.maximum(h,hp)
    crease=np.zeros_like(h)
    for ch in chains:
        pts,rads=ch
        for i in range(len(pts)-1):
            hc,t=capsule(pts[i],pts[i+1],rads[i],rads[i+1],box)
            h=np.maximum(h,hc)
            if creases and 0<i:
                X=xx[y0:y1,x0:x1]-pts[i][0]; Y=yy[y0:y1,x0:x1]-pts[i][1]
                crease+=np.exp(-(X**2+Y**2)/(rads[i]**2*0.9))*np.exp(-((X*(pts[i+1][0]-pts[i][0])+Y*(pts[i+1][1]-pts[i][1]))/ (math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])+1e-6))**2/6)
        # knuckle pad bumps
    hs=gaussian_filter(h,1.2)
    gy,gx=np.gradient(hs)
    n=np.stack([-gx,-gy,np.ones_like(hs)],-1); n/=np.linalg.norm(n,axis=-1,keepdims=True)
    L=np.array(light_dir,np.float32); L/=np.linalg.norm(L)
    sh=np.clip((n*L).sum(-1),0,1)**1.6
    cav=np.clip((hs-gaussian_filter(hs,8))/6,-1,1)
    sh=np.clip(sh*0.9+0.25*cav-0.5*np.clip(crease,0,1),0,1)
    col=hx(dark)*(1-sh[...,None])+hx(light)*sh[...,None]
    rr=np.clip(n[...,0]*rim_dir[0]+n[...,1]*rim_dir[1],0,1)**2*np.clip(1-n[...,2],0,1)*3
    rr=np.clip(rr,0,1)
    col=col*(1-rr[...,None])+hx(rim)*rr[...,None]
    msk=h>0.5
    sub=img[y0:y1,x0:x1]; sa=alpha[y0:y1,x0:x1]
    sub[msk]=col[msk]; sa[msk]=1
def chain(base,angs,lens,r0,r1):
    pts=[base]; x,y=base
    for a,l in zip(angs,lens):
        x+=l*math.cos(math.radians(a)); y+=l*math.sin(math.radians(a)); pts.append((x,y))
    rads=[r0+(r1-r0)*i/(len(pts)-1) for i in range(len(pts))]
    return pts,rads
