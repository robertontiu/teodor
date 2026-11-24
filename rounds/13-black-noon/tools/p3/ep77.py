import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(77); bl=[]
for b,t in [((462,1442),(530,1550)),((484,1420),(558,1510))]:
    dx,dy=t[0]-b[0],t[1]-b[1]; L=math.hypot(dx,dy); d=(dx/L,dy/L); n=(-d[1],d[0])
    for i in range(16):
        s=0.05+0.9*i/15; cx,cy=b[0]+dx*s,b[1]+dy*s
        bl.append({"pts":[[round(cx-n[0]*14),round(cy-n[1]*14)],[round(cx+n[0]*14),round(cy+n[1]*14)]],"size":9})
for i in range(30):
    x=rnd.uniform(345,480); y=rnd.uniform(1345,1480)
    a=math.radians(57+90+rnd.uniform(-20,20)); L=rnd.uniform(20,40)
    bl.append({"pts":[[round(x-math.cos(a)*L/2),round(y-math.sin(a)*L/2)],[round(x+math.cos(a)*L/2),round(y+math.sin(a)*L/2)]],"size":round(rnd.uniform(12,18),1)})
act({"arousal":0.15,"tension":0.05,"valence":0.0,"care":1.0},[{"type":"blend","strokes":bl}])
