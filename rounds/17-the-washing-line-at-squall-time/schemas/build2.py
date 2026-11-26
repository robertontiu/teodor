"""Schema v13+: start from schema_3 (v12), darken the storm behind the head, lay the new studies over it.
usage: python3 build2.py out.png layer1.png [layer2.png ...]"""
import sys, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
D='/home/claude/teodor-work/17/schema/'
img=np.asarray(Image.open(D+'schema_3c.png').convert('RGB')).astype(float)/255
M=dict(np.load(D+'masks.npz'))
yy,xx=np.mgrid[0:1600,0:1200]
# a darker strip of storm behind the head and down the raised arm (the critic: light her face against a darkened strip)
g=np.exp(-(((xx-480)/150.0)**2+((yy-440)/170.0)**2))
g=np.maximum(g, 0.7*np.exp(-(((xx-620)/120.0)**2+((yy-300)/220.0)**2)))
g=np.maximum(g, 0.9*np.exp(-(((xx-140)/170.0)**2+((yy-840)/90.0)**2)))
# clean the old hand's fingers that the new study doesn't cover
from scipy.ndimage import binary_dilation as bd
ha=np.asarray(Image.open(D+'hand_1.png').convert('RGBA'))[...,3]>10
old=bd(M['skin']&(xx<200)&(yy>740)&(yy<940)&~ha,iterations=3)&~ha
w=(~old&M['sky']).astype(float)
for c in range(3):
    n=gaussian_filter(img[...,c]*w,12); d=gaussian_filter(w,12)+1e-6
    img[...,c]=np.where(old,n/d,img[...,c])
sky=gaussian_filter((M['sky']|old).astype(float),3)
k=(0.30*g*sky)[...,None]
dark=np.array([0x2c,0x31,0x3a])/255
img=img*(1-k)+dark*k
for p in sys.argv[2:]:
    t=np.asarray(Image.open(p).convert('RGBA')).astype(float)/255
    a=t[...,3:4]; img=img*(1-a)+t[...,:3]*a
Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)).save(sys.argv[1])
