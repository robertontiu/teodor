import json, sys, random
import numpy as np
from PIL import Image
random.seed(int(sys.argv[4]) if len(sys.argv)>4 else 1)
D='/home/claude/v12/'
ref=np.array(Image.open(D+'main_scene_v18.png').convert('RGB')).astype(float)
sh=np.array(Image.open('/home/claude/v12/gen/mask_shadow18.png').convert('RGBA'))[...,3]>60
fig=np.array(Image.open('/home/claude/v12/gen/mask_figonly.png').convert('RGBA'))[...,3]>30
# dilate figure a little
from scipy.ndimage import binary_dilation
figd=binary_dilation(fig,iterations=6)
opening=np.zeros_like(sh); opening[210:1128,226:980]=True
mode=sys.argv[1]; step=int(sys.argv[2]); size=float(sys.argv[3])
if mode=='shadow': M=sh&opening&~figd
else: M=opening&~sh&~figd
S=[]
def col(x,y,dv):
    c=ref[min(1599,y),min(1199,x)]*dv
    c=np.clip(c+np.random.uniform(-10,10,3),0,255)
    return '#%02x%02x%02x'%tuple(int(v) for v in c)
H,W=M.shape
xs=list(range(226+step//2,980,step))
for x in xs:
    colm=M[:,x]
    y=0
    while y<H:
        if colm[y]:
            y0=y
            while y<H and colm[y]: y+=1
            y1=y
            # chunks
            a=y0
            while a<y1-2:
                b=min(y1, a+random.randint(60,140))
                yy=(a+b)//2
                dv=(1.0+0.9*max(0,(900-yy)/700)) if mode!='shadow' else 0.45
                S.append({"pts":[[x+random.uniform(-2,2),a+size*0.3],[x+random.uniform(-3,3),yy],[x+random.uniform(-2,2),b-size*0.3]],"size":size,"color":col(x,yy,dv)})
                if b>=y1: break
                a=b-4
        else: y+=1
random.shuffle(S)
for s in S: s["pts"]=[[round(p[0],1),round(p[1],1)] for p in s["pts"]]
print(json.dumps({"type":"strokes","brush":"flat","strokes":S,"edge":"hard" if mode=='shadow' else "soft"}))
