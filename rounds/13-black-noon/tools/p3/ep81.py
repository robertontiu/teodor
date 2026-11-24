import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
fix=[{"pts":[[382,1338],[384,1380],[390,1420],[398,1452]],"size":16,"color":"#7e503f"},
     {"pts":[[392,1345],[396,1390]],"size":10,"color":"#845543"}]
cont=[{"pts":[[364,1340],[366,1380],[370,1420],[380,1452]],"size":7,"color":"#121214"}]
sleeve=[{"pts":[[312,1318],[350,1306],[390,1296],[428,1286]],"size":14,"color":"#0e0e10"},
        {"pts":[[318,1310],[372,1292],[424,1278]],"size":12,"color":"#141418"}]
act({"arousal":0.15,"tension":0.05,"valence":0.0,"care":1.0},[
 {"type":"strokes","brush":"round","edge":"soft","strokes":fix,"wetmix":0.4},
 {"type":"strokes","brush":"flat","edge":"hard","strokes":cont+sleeve,"wetmix":0.2},
 {"type":"glaze","color":"#5a6068","opacity":0.35,"region":{"type":"poly","pts":[[316,1330],[426,1296],[430,1318],[320,1356]]},"feather":6},
])
