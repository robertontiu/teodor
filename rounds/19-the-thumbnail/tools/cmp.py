import numpy as np, sys, json
from PIL import Image
from scipy import ndimage as ndi
im=np.asarray(Image.open('/home/claude/teodor-work/19/main_full.png').convert('RGB'),float)/255
def L(c):
    y=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4).mean(-1)
    return np.where(y>0.008856,116*np.cbrt(y)-16,903.3*y)
Lc=ndi.gaussian_filter(L(im),4); Ls=ndi.gaussian_filter(np.load('/home/claude/teodor-work/19/plan/m/schema3_L.npy'),4)
M=np.load('/home/claude/teodor-work/19/plan/m/schema2_masks.npz')
for name,m in [('sky',M['sky']),('ground',M['ground']),('cloth',M['cloth']&(M['grass']<0.2)),('hair',M['hair']),('grass',M['grass']>0.5)]:
    print(f"{name:7s} canvas {Lc[m].mean():5.1f} schema {Ls[m].mean():5.1f}  canvas p10/p90 {np.percentile(Lc[m],10):5.1f}/{np.percentile(Lc[m],90):5.1f} schema {np.percentile(Ls[m],10):5.1f}/{np.percentile(Ls[m],90):5.1f}")
