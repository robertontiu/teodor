import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
reg={"type":"poly","pts":[[315,1325],[455,1305],[545,1395],[590,1500],[565,1585],[495,1585],[445,1515],[395,1525],[335,1485]]}
act({"arousal":0.2,"tension":0.1,"valence":0.0,"care":1.0},[
 {"type":"match","brush":"flat","size":[7,14],"threshold":0.05,"faithful":1.0,"region":reg,"clip":True,"max_strokes":800,"edge":"soft","wetmix":0.25},
 {"type":"match","brush":"round","size":[3,7],"threshold":0.035,"faithful":1.0,"region":reg,"clip":True,"max_strokes":2500,"edge":"soft","wetmix":0.25},
])
