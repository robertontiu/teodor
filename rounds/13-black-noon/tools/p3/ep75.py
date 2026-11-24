import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
reg={"type":"poly","pts":[[600,1330],[690,1270],[740,1190],[830,1180],[900,1240],[975,1320],[960,1370],[880,1330],[800,1380],[770,1470],[680,1475],[620,1400]]}
act({"arousal":0.15,"tension":0.05,"valence":0.2,"care":1.0},[
 {"type":"match","brush":"round","size":[3,7],"threshold":0.04,"faithful":1.0,"region":reg,"clip":True,"max_strokes":2500,"edge":"soft","wetmix":0.2},
])
