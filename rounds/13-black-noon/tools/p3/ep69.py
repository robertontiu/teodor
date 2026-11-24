import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from geo import G
rnd=random.Random(69); arcs=[]; bl=[]
for k,spread in [('tl',1.3),('top',1.0),('r',1.3),('bm',1.35),('rw',1.35),('rl',1.35)]:
    g=G(k)
    for rr,cols,sz in [(1.18,["#ffffff","#fbfbf2"],(16,22)),(1.09,["#f4f2ea","#ecebe2","#fbfaf0"],(12,16)),(1.0,["#d8d6cc","#cfccc0","#e4e2d8"],(8,12))]:
        for j in range(7):
            t0=-math.pi/2+rnd.uniform(-spread,spread); L=rnd.uniform(0.25,0.5)
            ts=[t0+L*u/4 for u in range(5)]
            r=rr+rnd.uniform(-0.03,0.03)
            arcs.append({"pts":[g(r*math.cos(t),r*math.sin(t)) for t in ts],"size":round(rnd.uniform(*sz),1),"color":rnd.choice(cols)})
    for j in range(8):
        t0=-math.pi/2+rnd.uniform(-spread,spread); ts=[t0+0.3*u/3 for u in range(4)]
        bl.append({"pts":[g(1.04*math.cos(t),1.04*math.sin(t)) for t in ts],"size":round(rnd.uniform(14,20),1)})
act({"arousal":0.35,"tension":0.15,"valence":-0.4,"care":0.9},[
 {"type":"strokes","brush":"flat","edge":"lost","strokes":arcs,"wetmix":0.55},
 {"type":"blend","strokes":bl},
])
