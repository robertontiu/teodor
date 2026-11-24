import sys,random,math; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(80)
edge=[{"pts":[[360,1335],[364,1380],[372,1420],[386,1450]],"size":9,"color":"#121214"},
      {"pts":[[352,1340],[356,1390],[364,1430]],"size":9,"color":"#0e0e10"}]
cuffshade=[{"pts":[[318,1350],[372,1330],[426,1312]],"size":12,"color":"#7a7e84"},
           {"pts":[[318,1330],[330,1328]],"size":14,"color":"#1a1a1e"}]
bl=[{"pts":[[320,1340],[425,1305]],"size":10},{"pts":[[322,1325],[425,1292]],"size":8}]
# give the fingers more body on their shadow side
wid=[{"pts":[[452,1446],[490,1500],[518,1540]],"size":9,"color":"#6a3e30"},
     {"pts":[[476,1424],[515,1468],[547,1505]],"size":9,"color":"#6a3e30"}]
act({"arousal":0.2,"tension":0.1,"valence":0.0,"care":1.0},[
 {"type":"strokes","brush":"round","edge":"soft","strokes":edge+wid,"wetmix":0.35},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":cuffshade,"wetmix":0.4},
 {"type":"blend","strokes":bl},
])
