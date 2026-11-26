"""Schema v14+: start from schema_5 (v13), clear the old head study (face_4) to sky, lay the new studies over it.
usage: python3 build3.py out.png layer1.png [layer2.png ...]"""
import sys, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_dilation
D='/home/claude/teodor-work/17/schema/'
img=np.asarray(Image.open(D+'schema_5.png').convert('RGB')).astype(float)/255
M=dict(np.load(D+'masks.npz'))
yy,xx=np.mgrid[0:1600,0:1200]
old=np.asarray(Image.open(D+'face_4.png').convert('RGBA'))[...,3]>10
old=binary_dilation(old,iterations=5)&(yy<556)&~(M['skin']&(xx>650))
L=img.mean(-1); old=old|(((xx>520)&(xx<700)&(yy>355)&(yy<548)&(L<0.22))|((xx>480)&(xx<550)&(yy>490)&(yy<525)&(L<0.2)))&M["sky"]&~M["shawl"]&~M["dress"]&~M["skin"]
old=binary_dilation(old,iterations=2)
w=(M['sky']&~old).astype(float)
for c in range(3):
    n=gaussian_filter(img[...,c]*w,14); d=gaussian_filter(w,14)+1e-6
    img[...,c]=np.where(old,n/d,img[...,c])
for p in sys.argv[2:]:
    t=np.asarray(Image.open(p).convert('RGBA')).astype(float)/255
    a=t[...,3:4]; img=img*(1-a)+t[...,:3]*a
Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)).save(sys.argv[1])
