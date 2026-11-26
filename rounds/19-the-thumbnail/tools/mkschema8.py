import numpy as np
from PIL import Image
from scipy import ndimage as ndi
S=np.asarray(Image.open('plan/m/schema7.png').convert('RGB')).astype(float)
C=np.asarray(Image.open('main_full.png').convert('RGB')).astype(float)
m=np.load('p3/chest2_mask.npy').astype(float)
sig=45
w=ndi.gaussian_filter(m,sig)
out=S.copy()
for c in range(3):
    b=ndi.gaussian_filter(C[...,c]*m,sig)/np.maximum(w,1e-4)
    out[...,c]=np.where(m>0,b,S[...,c])
# feather 12px at the mask edge into the old schema
f=ndi.gaussian_filter(m,6)
f=np.where(m>0,np.clip(f*2-0.0,0,1),0)
f=np.clip((ndi.distance_transform_edt(m)/12),0,1)
out=out*f[...,None]+S*(1-f[...,None])
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('plan/m/schema8.png')
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).resize((600,800)).save('p3/schema8_small.png')
