import numpy as np, json
from PIL import Image
from scipy.ndimage import label, find_objects, binary_opening, binary_erosion
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(int)
r,g,b=im[...,0],im[...,1],im[...,2]
body=binary_erosion(np.load('/home/claude/v14/tools/body_mask.npy'),iterations=3)
dot=(((r>150)&(g>150)&(b<170))|((r>190)&(g<150))|((r>200)&(g>200)&(b>190)))&body
dot=binary_opening(dot,iterations=1)
lab,n=label(dot); rng=np.random.default_rng(61); st=[]
yy,xx=np.mgrid[-16:17,-16:17]; H,W=body.shape
for i,sl in enumerate(find_objects(lab)):
    h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
    if h<4 or w<4 or h>32 or w>32: continue
    cy,cx=(sl[0].start+sl[0].stop)/2,(sl[1].start+sl[1].stop)/2; rr=max(h,w)/2
    # along the body axis: legs (top-left) keep their dots; toward the chest they go
    t=(cx*0.39+cy*0.92)  # projection on the body axis
    p=np.clip((t-560)/220,0,1)
    if rng.random()>p: continue
    ring=(np.hypot(xx,yy)>rr+2)&(np.hypot(xx,yy)<rr+8)
    ys=np.clip(int(cy)+yy[ring],0,H-1); xs=np.clip(int(cx)+xx[ring],0,W-1)
    ok=body[ys,xs]&~dot[ys,xs]
    if ok.sum()<5: continue
    c=np.median(im[ys,xs][ok],0).astype(int)
    st.append({"pts":[[cx-rr*0.6,cy-rr*1.4],[cx+rr*0.6,cy+rr*1.4]],"size":round(rr*2+4,1),"color":'#%02x%02x%02x'%tuple(c)})
print(len(st)); json.dump(st,open('/tmp/bd.json','w'))
