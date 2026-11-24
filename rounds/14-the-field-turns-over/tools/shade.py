import numpy as np, sys
from PIL import Image
from scipy.ndimage import gaussian_filter
base=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)/255
sch=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(float)/255
r,g,b=base[...,0],base[...,1],base[...,2]
grass=(g>b+0.1)&(g>=r-0.08)
lum=0.3*r+0.6*g+0.1*b
p=np.percentile(lum[grass],90); s=gaussian_filter(np.clip((p-0.06-lum)/0.3,0,1)*grass,2.5)
same=(np.abs(sch-base).sum(-1)<0.08)
m=np.clip(s*same*1.3,0,1)[...,None]
shade=np.array([0.05,0.30,0.30])*(1-s[...,None]*0.3)+np.array([0.08,0.14,0.36])*0.3*s[...,None]
out=sch*(1-m)+shade*m
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save(sys.argv[3])
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).resize((600,800)).save('/tmp/prev.png')
