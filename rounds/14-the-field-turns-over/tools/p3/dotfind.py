import numpy as np, json
from PIL import Image
from scipy.ndimage import label, find_objects, binary_opening
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(int)
r,g,b=im[...,0],im[...,1],im[...,2]
pink=(r>200)&(g<140)&(b>100)
white=(r>215)&(g>215)&(b>185)&(np.abs(r-g)<25)
body=np.load('/home/claude/v14/tools/body_mask.npy')
res={}
for k,m in (('pink',pink),('white',white)):
    m=binary_opening(m,iterations=1)
    lab,n=label(m); out=[]
    for i,sl in enumerate(find_objects(lab)):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if h<5 or w<5 or h>30 or w>30: continue
        cy,cx=(sl[0].start+sl[0].stop)/2,(sl[1].start+sl[1].stop)/2
        out.append([cx,cy,max(h,w)/2])
    res[k]=out; print(k,len(out))
json.dump(res,open('/home/claude/v14/tools/p3/dots_now.json','w'))
