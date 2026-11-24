# sink dots back into the paint: far from the head most go; some are dragged along the vortex
import numpy as np, json, sys
from PIL import Image
im=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(int)
d=json.load(open('/home/claude/v14/tools/p3/dots_now.json'))
rng=np.random.default_rng(int(sys.argv[1]))
cx,cy=742,1085; H,W=im.shape[:2]
cover=[]; drag=[]
yy,xx=np.mgrid[-14:15,-14:15]
for k in ('pink','white'):
  for x,y,r in d[k]:
    R=np.hypot(x-cx,y-cy)
    p=np.clip((R-230)/520,0,0.88)
    tx,ty=-(y-cy)/R,(x-cx)/R
    if rng.random()<p:
      # surrounding paint colour
      ring=(np.hypot(xx,yy)>r+3)&(np.hypot(xx,yy)<r+9)
      ys=np.clip(int(y)+yy[ring],0,H-1); xs=np.clip(int(x)+xx[ring],0,W-1)
      px=im[ys,xs]; ok=~(((px[:,0]>200)&(px[:,1]<150))|((px.min(1)>210)))
      if ok.sum()<5: continue
      c=np.median(px[ok],0).astype(int)
      L=r*2.4
      cover.append({"pts":[[x-tx*L,y-ty*L],[x+tx*L,y+ty*L]],"size":round(r*2+5,1),"color":'#%02x%02x%02x'%tuple(c)})
    elif R>330 and rng.random()<0.5:
      drag.append([x,y,r,tx,ty])
json.dump(cover,open('/tmp/cover.json','w')); json.dump(drag,open('/tmp/drag.json','w'))
print(len(cover),len(drag))
