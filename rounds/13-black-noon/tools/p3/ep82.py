import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
coat=[{"pts":[[338+d,1334],[341+d,1380],[346+d,1420],[356+d,1456]],"size":9,"color":c} for d,c in [(0,'#0e0e10'),(7,'#111114'),(14,'#0f0f12'),(20,'#131316')]]
act({"arousal":0.15,"tension":0.05,"valence":0.0,"care":1.0},[
 {"type":"strokes","brush":"flat","edge":"hard","strokes":coat,"wetmix":0.15},
])
