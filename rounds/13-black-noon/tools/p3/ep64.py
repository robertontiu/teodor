import sys,random; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(64)
strands=[]
for k in range(14):
    x0=rnd.uniform(668,812); 
    strands.append({"pts":[[round(x0),812],[round(x0+rnd.uniform(-14,14)),845],[round(x0+rnd.uniform(-24,24)),round(rnd.uniform(860,900))]],
                    "size":round(rnd.uniform(1.8,3.2),1),"color":rnd.choice(['#2a120c','#3a1a10','#1e0c08','#5a2a18'])})
mouth=[{"pts":[[732,915],[738,925],[742,945]],"size":15,"color":"#140606"},
       {"pts":[[726,922],[740,920],[752,926]],"size":6,"color":"#1a0808"}]
act({"arousal":0.45,"tension":0.4,"valence":-0.6,"care":0.9},[
 {"type":"glaze","color":"#24121a","opacity":0.45,"region":{"type":"ellipse","cx":740,"cy":848,"rx":82,"ry":40},"feather":22},
 {"type":"glaze","color":"#1c1218","opacity":0.45,"region":{"type":"ellipse","cx":452,"cy":772,"rx":82,"ry":40},"feather":22},
 {"type":"glaze","color":"#1c1210","opacity":0.4,"region":{"type":"ellipse","cx":905,"cy":662,"rx":70,"ry":40},"feather":22},
 {"type":"strokes","brush":"liner","strokes":strands+mouth},
])
