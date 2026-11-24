import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, median_filter, binary_erosion
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(float)
body=np.load('/home/claude/v14/tools/body_mask.npy')
face=np.load('/home/claude/v14/tools/p3/face2_mask.npy')
base=np.stack([median_filter(im[...,i],size=25) for i in range(3)],-1)
H,W=body.shape; yy,xx=np.mgrid[0:H,0:W].astype(float)
def blob(cx,cy,sx,sy,ang):
    a=np.deg2rad(ang); dx,dy=xx-cx,yy-cy
    p=dx*np.cos(a)+dy*np.sin(a); q=-dx*np.sin(a)+dy*np.cos(a)
    return np.exp(-(p/sx)**2-(q/sy)**2)
# light: chest plane on the sun side, the shoulder, the top of the outflung arm
L=np.maximum.reduce([blob(700,880,70,40,-23)*0.85, blob(770,895,45,30,0)*0.9, blob(950,880,170,16,3)*0.6, blob(560,640,50,110,-65)*0.4])
inner=binary_erosion(body,iterations=6)
L=L*gaussian_filter(inner.astype(float),4)
lc=np.array([214,228,248.])  # pale cerulean
hc=np.array([250,246,222.])  # warm cream at the peak
col=lc*(1-np.clip((L-0.6)/0.3,0,1)[...,None])+hc*np.clip((L-0.6)/0.3,0,1)[...,None]
out=base*(1-L[...,None]*0.85)+col*L[...,None]*0.85
out[~body]=im[~body]; out[face]=im[face]
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('/home/claude/v14/tools/p3/bodylight_sch.png')
m=(L>0.08)&body&~face
np.save('/home/claude/v14/tools/p3/bodylight_mask.npy',m); print(m.sum())
