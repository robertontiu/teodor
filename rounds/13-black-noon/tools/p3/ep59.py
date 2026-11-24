import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
TL={"type":"ellipse","cx":300,"cy":240,"rx":150,"ry":150}
TOP={"type":"ellipse","cx":860,"cy":80,"rx":190,"ry":150}
R={"type":"ellipse","cx":1000,"cy":385,"rx":150,"ry":140}
act({"arousal":0.35,"tension":0.15,"valence":-0.4,"care":0.95},[
 {"type":"match","brush":"flat","size":[10,22],"threshold":0.05,"faithful":0.95,"region":TL,"clip":True,"max_strokes":500,"edge":"soft"},
 {"type":"match","brush":"flat","size":[10,22],"threshold":0.05,"faithful":0.95,"region":TOP,"clip":True,"max_strokes":500,"edge":"soft"},
 {"type":"match","brush":"flat","size":[10,22],"threshold":0.05,"faithful":0.95,"region":R,"clip":True,"max_strokes":500,"edge":"soft"},
])
