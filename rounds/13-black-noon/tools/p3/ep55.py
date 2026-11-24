import sys, math, random
sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(55)
cx,cy,R=552,458,92
# white burn ring first, covering the acid fringe, radiating short knife marks
ring=[]
for k in range(140):
    a=rnd.uniform(0,2*math.pi); r0=R-4; r1=R+rnd.uniform(25,70)
    ring.append({"pts":[[round(cx+math.cos(a)*r0),round(cy+math.sin(a)*r0)],[round(cx+math.cos(a)*r1),round(cy+math.sin(a)*r1)]],
                 "size":round(rnd.uniform(6,14),1),"color":rnd.choice(["#fffef6","#fbfbf2","#f6f8f0","#ffffff"])})
# disc: chords
disc=[]
y=cy-R+6
while y<cy+R-4:
    h=math.sqrt(max(0,R*R-(y-cy)**2))-5
    disc.append({"pts":[[round(cx-h),round(y)],[round(cx),round(y+rnd.uniform(-2,2))],[round(cx+h),round(y)]],"size":13,
                 "color":rnd.choice(["#0b0814","#100b1c","#0d0a12","#140e22"])})
    y+=9
rim=[{"pts":[[round(cx+math.cos(t/40*2*math.pi)*R),round(cy+math.sin(t/40*2*math.pi)*R)] for t in range(i,i+9)],"size":3,"color":"#ffffff"} for i in range(0,40,8)]
act({"arousal":0.6,"tension":0.35,"valence":-0.6,"care":0.85},[
 {"type":"strokes","brush":"knife","edge":"hard","strokes":ring,"impasto":0.8},
 {"type":"strokes","brush":"flat","edge":"hard","strokes":disc,"region":{"type":"ellipse","cx":cx,"cy":cy,"rx":R,"ry":R},"clip":True},
 {"type":"strokes","brush":"liner","strokes":rim},
])
