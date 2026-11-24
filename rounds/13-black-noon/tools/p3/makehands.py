import sys,math,numpy as np; sys.path.insert(0,'/home/claude/v13/tools/p3')
from handgen import render_hand, chain
from PIL import Image
from scipy.ndimage import gaussian_filter
base=np.asarray(Image.open(sys.argv[1]).convert('RGB'),np.float32)/255
img=np.zeros_like(base); a=np.zeros(base.shape[:2],np.float32)
# OPEN HAND (red woman): wrist up-right, fingers fanning down-left, thumb right
wr=(800,1215)
open_chains=[
 chain((722,1312),[162,158,154],[40,27,21],14,10),
 chain((735,1335),[140,136,132],[43,30,23],14.5,10.5),
 chain((760,1352),[124,120,116],[44,32,24],14,10),
 chain((788,1350),[108,104,100],[36,25,19],12,8.5),
 chain((828,1265),[28,36,44],[50,40,32],17,11),
]
open_palm=[(760,1205),(840,1215),(865,1265),(830,1320),(795,1358),(745,1350),(712,1318),(725,1250)]
render_hand(img,a,open_chains,open_palm,'#5a2e24','#dca088','#fff2e6',(560,1120,1020,1560),thick=45,creases=False)
pulse_chains=[
 chain((480,1405),[55,58,62],[52,38,30],13.5,10),
 chain((462,1428),[60,63,66],[54,40,31],14,10.5),
 chain((440,1442),[75,150,220],[30,22,16],13,10),
 chain((415,1447),[80,155,225],[25,18,14],11.5,9),
 chain((440,1350),[10,40],[45,35],15,11),
]
pulse_palm=[(345,1330),(425,1320),(470,1350),(495,1400),(470,1440),(420,1450),(370,1430),(345,1390)]
render_hand(img,a,pulse_chains,pulse_palm,'#3a221e','#b8826c','#f6f0e6',(300,1280,640,1600),thick=45,rim_dir=(0.4,-0.9),creases=False)
a=gaussian_filter(a,0.7)[...,None]
out=base*(1-a)+img*a
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save('/home/claude/v13/ref_p3.png')
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).crop((280,1100,1000,1600)).save('/tmp/r.png')
