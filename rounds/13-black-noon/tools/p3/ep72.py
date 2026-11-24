import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from geo import G, H
rnd=random.Random(72)
C=(758,300); a=math.radians(105-90)  # rotate local frame: v along length
def P(u,v):
    return [round(C[0]+u*math.cos(a)-v*math.sin(a)), round(C[1]+u*math.sin(a)+v*math.cos(a))]
W,L=50,95
# sleeve first (behind the phone top), charcoal with a rim
sleeve=[]
for i in range(9):
    o=(i-4)*5
    sleeve.append({"pts":[P(o-8,-80),P(o+20,-130),P(o+60,-175)],"size":13,"color":rnd.choice(['#1e1c1c','#2a2726','#24201f'])})
wrist=[{"pts":[P(-10,-88),P(6,-104)],"size":20,"color":"#4a2c1e"}]
body=[]
for u in range(-W+6,W-5,6):
    body.append({"pts":[P(u,-L+8),P(u+rnd.uniform(-1,1),0),P(u,L-8)],"size":9,"color":rnd.choice(['#0c0d12','#101219','#090a0e','#0e1016'])})
# rounded outline hard edge
outline=[]
for side in (-1,1):
    outline.append({"pts":[P(side*W,-L+12),P(side*W,0),P(side*W,L-12)],"size":3.2,"color":"#3c424e" if side<0 else "#1a1c22"})
outline.append({"pts":[P(-W+12,-L),P(0,-L),P(W-12,-L)],"size":3.2,"color":"#4a505c"})
outline.append({"pts":[P(-W+12,L),P(0,L),P(W-12,L)],"size":3.0,"color":"#1a1c22"})
sheen=[{"pts":[P(-W+4,-20),P(0,-55),P(W-4,-88)],"size":16,"color":"#262c38"},{"pts":[P(-W+4,10),P(W-6,-60)],"size":6,"color":"#2e3442"}]
cam=[{"pts":[P(-30,-72),P(-10,-72)],"size":26,"color":"#050608"}]
lens=[]
for (u,v) in [(-30,-78),(-30,-60)]:
    lens.append({"pts":[P(u-3,v),P(u+3,v)],"size":9,"color":"#1c2230"})
flash=[{"pts":[P(-12,-80),P(-11,-80)],"size":6,"color":"#ffffff"}]
for k in range(8):
    t=k*math.pi/4+0.2; r=12 if k%2 else 22
    p0=P(-12,-80); flash.append({"pts":[p0,[p0[0]+round(r*math.cos(t)),p0[1]+round(r*math.sin(t))]],"size":1.8,"color":"#ffffff"})
# fingers: three fingertips wrapping the left edge, thumb on the right
fing=[]
for v in (-30,-2,26):
    fing.append({"pts":[P(-W-14,v),P(-W-4,v+2),P(-W+10,v+4)],"size":17,"color":"#5a3626"})
    fing.append({"pts":[P(-W+2,v-4),P(-W+10,v+3)],"size":5,"color":"#8a5a40"})   # fingertip catch of bounce
    fing.append({"pts":[P(-W-16,v-7),P(-W-4,v-6)],"size":2.2,"color":"#f2ece0"})     # rim from the sky
fing.append({"pts":[P(W+16,-42),P(W+6,-30),P(W-6,-20)],"size":18,"color":"#5a3626"})
fing.append({"pts":[P(W+18,-48),P(W+8,-38)],"size":2.2,"color":"#f2ece0"})
act({"arousal":0.35,"tension":0.4,"valence":-0.7,"care":0.95},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":sleeve+wrist,"wetmix":0.3},
 {"type":"strokes","brush":"flat","edge":"hard","strokes":body+sheen,"wetmix":0.15},
 {"type":"strokes","brush":"round","edge":"hard","strokes":fing+cam+lens,"wetmix":0.2},
 {"type":"strokes","brush":"liner","strokes":outline+flash},
])
