import sys, math, numpy as np; sys.path.insert(0,'/home/claude/v13/tools/p3')
from facegen import render_head
from PIL import Image
from scipy.ndimage import gaussian_filter
base=np.asarray(Image.open(sys.argv[2] if len(sys.argv)>2 else '/home/claude/v13/main_full.png').convert('RGB'),np.float32)/255
from PIL import ImageDraw
PATCH={'bm':[([(390,905),(470,890),(530,905),(540,960),(420,990)],'#121214')],
       'rw':[([(660,990),(810,985),(830,1040),(690,1050)],'#7a1410')],
       'rl':[([(1000,650),(1040,630),(1075,700),(1050,750),(1005,720)],'#3c3c40')]}
pim=Image.fromarray((base*255).astype(np.uint8)); d=ImageDraw.Draw(pim)
for k in sys.argv[1].split(','):
    for poly,c in PATCH.get(k,[]): d.polygon(poly,fill=c)
base=np.asarray(pim,np.float32)/255
img=np.zeros_like(base); a=np.zeros(base.shape[:2],np.float32)
HEADS={
 'tl': dict(c=(330,262),sc=1.3,dark='#1e1616',light='#7a5a50',hair=['#2a2522','#4a423a'],rimc='#f3f1e8',coat=['#22272f','#3a4250'],seed=1,eyes_open=True),
 'top':dict(c=(872,118),sc=1.2,dark='#1a0f0a',light='#6a4430',hair=['#120d0a','#2a1d16'],rimc='#f6f0e2',coat=['#1c1a1a','#3a3634'],seed=2,eyes_open=True),
 'r':  dict(c=(1000,385),sc=1.3,dark='#2a1c1c',light='#8c6c60',hair=['#8a6a38','#c0a062'],rimc='#fffbea',coat=['#142a6a','#2a4aa0'],seed=3,long_hair=True,eyes_open=True),
'bm': dict(c=(448,800),sc=1.45,dark='#181212',light='#7a5e50',hair=['#141010','#2a2420'],rimc='#f3efe4',coat=['#0e0e10','#1a1a1e'],seed=4,ang=math.radians(100),body=False,eyes_open=True),
 'rw': dict(c=(735,875),sc=1.5,dark='#201212',light='#8e6050',hair=['#2a120c','#4a2216'],rimc='#fff2e0',coat=['#6a0c0c','#a01a14'],seed=5,ang=math.radians(82),body=False,mouth_open=0.9,long_hair=True,eyes_open=True),
 'rl': dict(c=(912,676),sc=1.25,dark='#180e0a',light='#664430',hair=['#100c0a','#221a14'],rimc='#f3efe4',coat=['#3a3a3e','#55555a'],seed=6,body=False,eyes_open=True),
}
sel=sys.argv[1].split(',')
for k in sel: render_head(img,a,**HEADS[k])
a=gaussian_filter(a,0.8)[...,None]
out=base*(1-a)+img*a
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save('/home/claude/v13/ref_p3.png')
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).crop((0,0,1200,700)).resize((600,350)).save('/tmp/refprev.png')
