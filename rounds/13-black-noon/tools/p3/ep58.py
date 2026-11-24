import sys,random,math; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from head2 import head2
E,G=head2((340,272),1.25,['#3a2a26','#33241f','#40302a'],['#8c6450','#6e4e40'],['#1e1a18','#26201c','#171412'],58)
rnd=random.Random(1)
# cover the orange remnant and tidy neck: dark collar/neck strokes from G local
neck=[{"pts":[G(x,60),G(x*1.1,100),G(x*1.2,150)],"size":12,"color":rnd.choice(['#241a18','#2a201c','#1e1716'])} for x in range(-36,37,8)]
orange=[{"pts":[[400+rnd.randint(-40,40),150+rnd.randint(-40,40)],[0,0]],"size":18,"color":"#f4f4ea"} for _ in range(0)]
act({"arousal":0.3,"tension":0.15,"valence":-0.4,"care":0.95},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":E['base']+neck,"wetmix":0.2},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":E['hair'],"wetmix":0.2},
 {"type":"strokes","brush":"round","edge":"soft","strokes":E['lights'],"wetmix":0.45},
 {"type":"strokes","brush":"liner","strokes":E['rim']},
])
