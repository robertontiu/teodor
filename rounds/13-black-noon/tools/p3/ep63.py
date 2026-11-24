import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
BM={"type":"ellipse","cx":448,"cy":805,"rx":95,"ry":120}
RW={"type":"ellipse","cx":735,"cy":880,"rx":105,"ry":135}
RL={"type":"ellipse","cx":912,"cy":676,"rx":95,"ry":82}
act({"arousal":0.2,"tension":0.08,"valence":-0.3,"care":1.0},[
 {"type":"match","brush":"round","size":[3,7],"threshold":0.03,"faithful":1.0,"region":BM,"clip":True,"max_strokes":1800,"edge":"soft","wetmix":0.35},
 {"type":"match","brush":"round","size":[3,7],"threshold":0.03,"faithful":1.0,"region":RW,"clip":True,"max_strokes":1800,"edge":"soft","wetmix":0.35},
 {"type":"match","brush":"round","size":[3,7],"threshold":0.03,"faithful":1.0,"region":RL,"clip":True,"max_strokes":1800,"edge":"soft","wetmix":0.35},
])
