import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
TL={"type":"ellipse","cx":322,"cy":252,"rx":95,"ry":95}
TOP={"type":"ellipse","cx":868,"cy":112,"rx":90,"ry":95}
R={"type":"ellipse","cx":1005,"cy":385,"rx":105,"ry":100}
act({"arousal":0.2,"tension":0.08,"valence":-0.3,"care":1.0},[
 {"type":"match","brush":"round","size":[3,8],"threshold":0.03,"faithful":1.0,"region":TL,"clip":True,"max_strokes":1500,"edge":"soft","wetmix":0.35},
 {"type":"match","brush":"round","size":[3,8],"threshold":0.03,"faithful":1.0,"region":TOP,"clip":True,"max_strokes":1500,"edge":"soft","wetmix":0.35},
 {"type":"match","brush":"round","size":[3,8],"threshold":0.03,"faithful":1.0,"region":R,"clip":True,"max_strokes":1500,"edge":"soft","wetmix":0.35},
])
