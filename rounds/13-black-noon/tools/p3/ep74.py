import sys; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from fingers import finger
S=[];C=[];R=[]
for b,t,w,rim in [((702,1300),(636,1344),25,True),((716,1322),(655,1402),26,True),((742,1340),(690,1450),26,False),((776,1346),(756,1450),22,False),((858,1265),(955,1340),28,True)]:
    s,c,r=finger(b,t,w,'#b47a62','#d9a48a','#6c3a34','#a8705c','#6e3a2c','#fff0e0' if rim else None)
    S+=s;C+=c;R+=r
palm=[{"pts":[[800,1250],[830,1270],[845,1300]],"size":34,"color":"#d29c84"},
      {"pts":[[760,1280],[785,1300]],"size":26,"color":"#a06654"},
      {"pts":[[740,1235],[770,1225],[805,1230]],"size":22,"color":"#c48a72"},
      {"pts":[[735,1320],[770,1335],[800,1335]],"size":18,"color":"#b07a64"}]
act({"arousal":0.15,"tension":0.05,"valence":0.3,"care":1.0},[
 {"type":"strokes","brush":"round","edge":"soft","strokes":palm,"wetmix":0.5},
 {"type":"strokes","brush":"round","edge":"soft","strokes":S,"wetmix":0.4},
 {"type":"strokes","brush":"liner","strokes":C,"wetmix":0.5},
 {"type":"strokes","brush":"liner","strokes":R},
])
