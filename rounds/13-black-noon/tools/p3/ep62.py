import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
BM={"type":"ellipse","cx":448,"cy":815,"rx":125,"ry":150}
RW={"type":"ellipse","cx":735,"cy":890,"rx":135,"ry":165}
RL={"type":"ellipse","cx":930,"cy":680,"rx":135,"ry":105}
act({"arousal":0.35,"tension":0.15,"valence":-0.4,"care":0.95},[
 {"type":"match","brush":"flat","size":[7,16],"threshold":0.05,"faithful":0.95,"region":BM,"clip":True,"max_strokes":700,"edge":"soft"},
 {"type":"match","brush":"flat","size":[7,16],"threshold":0.05,"faithful":0.95,"region":RW,"clip":True,"max_strokes":700,"edge":"soft"},
 {"type":"match","brush":"flat","size":[7,16],"threshold":0.05,"faithful":0.95,"region":RL,"clip":True,"max_strokes":700,"edge":"soft"},
])
