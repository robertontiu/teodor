import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from geo import G
rnd=random.Random(68); hal=[]; blends=[]
for k,n,spread in [('tl',30,1.2),('top',26,1.1),('r',28,1.2),('bm',34,1.25),('rw',34,1.25),('rl',30,1.25)]:
    g=G(k)
    for i in range(n):
        t=-math.pi/2+rnd.uniform(-spread,spread)
        o=rnd.uniform(1.25,1.6); inn=rnd.uniform(0.88,1.0) if abs(t+math.pi/2)<0.7 else rnd.uniform(0.98,1.06)
        hal.append({"pts":[g(o*math.cos(t),o*math.sin(t)),g(1.06*math.cos(t),1.06*math.sin(t)),g(inn*math.cos(t),inn*math.sin(t))],
                    "size":round(rnd.uniform(6,12),1),"color":rnd.choice(["#ffffff","#fbfbf2","#f6f5ea","#fffdf0"])})
    for i in range(10):
        t=-math.pi/2+rnd.uniform(-0.9,0.9)
        blends.append({"pts":[g(1.15*math.cos(t),1.15*math.sin(t)),g(0.95*math.cos(t),0.95*math.sin(t))],"size":round(rnd.uniform(10,16),1)})
act({"arousal":0.6,"tension":0.3,"valence":-0.5,"care":0.8},[
 {"type":"strokes","brush":"flat","edge":"lost","strokes":hal,"wetmix":0.35,"impasto":0.7},
 {"type":"blend","strokes":blends},
])
