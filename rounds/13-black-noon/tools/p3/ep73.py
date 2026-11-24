import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
C=(758,300); a=math.radians(15)
def P(u,v): return [round(C[0]+u*math.cos(a)-v*math.sin(a)), round(C[1]+u*math.sin(a)+v*math.cos(a))]
W=50
fing=[]
for v in (-30,-2,26):
    fing.append({"pts":[P(-W-14,v-1),P(-W-2,v+1),P(-W+8,v+3)],"size":14,"color":"#3e2620"})
    fing.append({"pts":[P(-W+4,v+1),P(-W+10,v+3)],"size":7,"color":"#9a8278"})   # nail facing us
    fing.append({"pts":[P(-W-6,v-6),P(-W-5,v+7)],"size":1.6,"color":"#1a0e0a"})   # knuckle crease
    fing.append({"pts":[P(-W-18,v-6),P(-W-6,v-5)],"size":1.8,"color":"#f2ece0"})
fing.append({"pts":[P(W+14,-42),P(W+5,-31),P(W-4,-22)],"size":15,"color":"#3e2620"})
fing.append({"pts":[P(W-1,-26),P(W-6,-21)],"size":7,"color":"#9a8278"})
fing.append({"pts":[P(W+18,-48),P(W+8,-38)],"size":1.8,"color":"#f2ece0"})
cuff=[{"pts":[P(-6,-98),P(8,-118),P(24,-132)],"size":24,"color":"#1e1c1c"},{"pts":[P(14,-100),P(30,-124)],"size":2,"color":"#e8e6dc"}]
bl=[{"pts":[P(-W+8,-20),P(0,-55),P(W-8,-85)],"size":14},{"pts":[P(-W+8,10),P(W-10,-60)],"size":10}]
act({"arousal":0.25,"tension":0.15,"valence":-0.6,"care":1.0},[
 {"type":"match","brush":"round","size":[4,9],"threshold":0.06,"faithful":1.0,"region":{"type":"ellipse","cx":880,"cy":110,"rx":96,"ry":96},"clip":True,"max_strokes":1500,"edge":"soft","wetmix":0.25},
 {"type":"blend","strokes":bl},
 {"type":"strokes","brush":"round","edge":"hard","strokes":cuff+fing,"wetmix":0.15},
])
