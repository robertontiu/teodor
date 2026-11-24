import numpy as np, math
from scipy.ndimage import gaussian_filter
SUN=(552,458)
def hx(h): return np.array([int(h[i:i+2],16)/255 for i in (1,3,5)],np.float32)
def g(X,Y,x0,y0,sx,sy): return np.exp(-((X-x0)/sx)**2-((Y-y0)/sy)**2)
def render_head(img, alpha, c, sc, dark, light, hair, rimc, coat, ang=None, mouth_open=0.0, seed=0,
                light_dir=(0.15,0.35,1.0), hairline=-0.5, body=True, long_hair=False, eyes_open=False):
    H,W=alpha.shape
    if ang is None: ang=math.atan2(c[1]-SUN[1],c[0]-SUN[0])
    uy=np.array([math.cos(ang),math.sin(ang)]); ux=np.array([-uy[1],uy[0]])
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    dx=xx-c[0]; dy=yy-c[1]
    lx=(dx*ux[0]+dy*ux[1])/sc; ly=(dx*uy[0]+dy*uy[1])/sc
    X=lx/60; Y=ly/76
    wY=1-0.22*np.clip(Y,0,None)**2
    Xp=X/wY
    r2=Xp**2+Y**2
    head=r2<1
    h0=np.sqrt(np.clip(1-r2,0,1))
    h=h0.copy()
    for s in (-1,1):
        h+=0.10*g(X,Y,s*0.36,-0.30,0.26,0.07)
        h-=0.17*g(X,Y,s*0.33,-0.15,0.16,0.10)
        h+=0.05*g(X,Y,s*0.33,-0.15,0.08,0.05)   # eyeball catch
        h+=0.08*g(X,Y,s*0.13,0.12,0.07,0.05)
        h+=0.07*g(X,Y,s*0.5,0.03,0.18,0.12)
        h-=0.05*g(X,Y,s*0.3,0.32,0.08,0.12)     # nasolabial
    ramp=np.clip((Y+0.28)/0.40,0,1)*np.where(Y<0.13,1.0,np.exp(-((Y-0.13)/0.05)**2))
    h+=0.26*np.exp(-(X/0.085)**2)*ramp
    h-=0.05*g(X,Y,0,0.2,0.14,0.03)
    h+=0.06*g(X,Y,0,0.36,0.2,0.05)
    if mouth_open>0:
        h-=0.35*mouth_open*g(X,Y,0,0.46,0.16,0.08*(1+mouth_open))
    else:
        h-=0.07*g(X,Y,0,0.42,0.22,0.022)
    h+=0.06*g(X,Y,0,0.52,0.16,0.05)
    h+=0.08*g(X,Y,0,0.80,0.22,0.1)
    hp=h*60*sc
    gy_,gx_=np.gradient(gaussian_filter(hp,1.0))
    n=np.stack([-gx_,-gy_,np.ones_like(hp)],-1); n/=np.linalg.norm(n,axis=-1,keepdims=True)
    # light in local frame -> image frame
    lxv,lyv,lz=light_dir
    Lv=np.array([lxv*ux[0]+lyv*uy[0], lxv*ux[1]+lyv*uy[1], lz]); Lv/=np.linalg.norm(Lv)
    shade=np.clip((n*Lv).sum(-1),0,1)**1.4
    cav=np.clip((hp-gaussian_filter(hp,6*sc))/(8*sc),-1,1)
    shade=np.clip(shade*0.85+0.45*cav,0,1)
    D,Lc,R=hx(dark),hx(light),hx(rimc)
    col=D*(1-shade[...,None])+Lc*shade[...,None]
    if mouth_open>0:
        mm=g(X,Y,0,0.47,0.21,0.075*(1+mouth_open))
        col=col*(1-np.clip((mm-0.35)*3,0,1)[...,None])+hx('#160806')*np.clip((mm-0.35)*3,0,1)[...,None]
        tl=g(X,Y,0,0.47+0.075*(1+mouth_open)*0.75,0.12,0.02)
        col=col*(1-0.5*tl[...,None])+hx(light)*0.5*tl[...,None]
    if eyes_open:
        for s_ in (-1,1):
            e=g(X,Y,s_*0.31,-0.13,0.13,0.045)
            col=col*(1-np.clip((e-0.4)*2.5,0,1)[...,None])+hx('#140c0a')*np.clip((e-0.4)*2.5,0,1)[...,None]
            sp=g(X,Y,s_*0.29+0.02,-0.15,0.025,0.018)
            col=col*(1-sp[...,None]*0.9)+hx('#f0eee6')*sp[...,None]*0.9
    rim=np.clip(1-n[...,2],0,1)**2.2*np.clip(0.4-Y,0,1.2)
    rim=np.clip(rim*2.8,0,1)
    # hair
    hl=hairline+0.35*X**2+0.035*np.sin(X*9+seed)+0.02*np.sin(X*23+2*seed)
    hairm=((r2<1.12**2)&(Y<0.15)&((Y<hl)|(r2>=1)))
    if long_hair: hairm|=((r2>=0.97)&(r2<1.16**2)&(Y<0.7))
    rng=np.random.default_rng(seed)
    strands=gaussian_filter(rng.random((H,W)).astype(np.float32),[2,2])
    hc=[hx(c_) for c_ in hair]
    hcol=hc[0]*(1-strands[...,None])+hc[1]*strands[...,None]
    hrim=np.clip((r2-1.02)/0.2,0,1)*np.clip(-0.2-Y,0,1)*0.8
    col=np.where(hairm[...,None],hcol*(1-hrim[...,None]*0.0)+0,col)
    rimall=np.where(hairm,np.clip(hrim*1.3,0,1),rim)
    col=col*(1-rimall[...,None]*0.85)+R*rimall[...,None]*0.85
    m=(head|hairm)
    # neck and body behind
    if body:
        neck=(np.abs(X)<0.5+0.1*np.clip(Y-1,0,None))&(Y>0.4)&(Y<1.55)&~m
        nc=hx(dark)*0.8
        body_m=(Y>1.3)&(np.abs(X)<0.62+1.9*np.clip((Y-1.3)/0.45,0,1)**0.5)&~m
        bshade=np.clip(1-np.abs(X)/3.2,0,1)
        bcol=hx(coat[0])*(1-bshade[...,None]*0.5)+hx(coat[1])*bshade[...,None]*0.5
        img[neck]=nc; alpha[neck]=1
        img[body_m]=bcol[body_m]; alpha[body_m]=1
    img[m]=col[m]; alpha[m]=1
    return img,alpha
