import sys; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from head import figure; import json
eps,G=figure((340,272),1.25,['#8a6656','#76574a','#4e3a36','#3c2c2a'],['#5e5850','#4a453f','#6e675e','#3a3632'],['#2a2f38','#333a45','#21262e','#3b4350'],56,old=(350,285,95,100))
json.dump({k:eps[k] for k in ['hal','rim']},open('/tmp/ep56_rest.json','w'))
act({"arousal":0.4,"tension":0.2,"valence":-0.4,"care":0.9},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":eps['sky']},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":eps['body']+eps['neck']},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":eps['face']+eps['hair'],"wetmix":0.3},
 {"type":"strokes","brush":"round","edge":"soft","strokes":eps['feat'],"wetmix":0.6},
])
