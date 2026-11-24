import sys; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from head import figure; import json
eps,G=figure((340,272),1.25,['#6e5044','#5a4238','#3a2a28','#2c2020'],['#3e3832','#2e2a26','#4a443c','#24201c'],['#2a2f38','#333a45','#21262e','#3b4350'],57)
neckdark=[dict(s,color='#241a18') for s in eps['neck']]
act({"arousal":0.3,"tension":0.15,"valence":-0.4,"care":0.95},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":neckdark,"wetmix":0.3},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":eps['face']+eps['hair'],"wetmix":0.25},
 {"type":"strokes","brush":"round","edge":"soft","strokes":eps['feat'],"wetmix":0.7},
 {"type":"strokes","brush":"flat","edge":"lost","strokes":eps['hal'],"wetmix":0.5},
])
