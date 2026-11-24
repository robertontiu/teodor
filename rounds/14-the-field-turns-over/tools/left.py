import json, numpy as np
exec(open('/home/claude/tools/knife.py').read().split('rng=')[0])
s=[]
for y in range(472,880,6):
    s.append({"pts":[[700,y],[600,y],[524,y]],"size":18,"color":grad(sky,y)})
act={"felt":{"arousal":0.15,"tension":0.1,"valence":0.3,"care":0.85},"do":[
 {"type":"strokes","brush":"flat","impasto":0,"load":1.6,"cover":1.0,"wetmix":0.05,"pickup":0.0,"region":{"type":"rect","x":527,"y":474,"w":200,"h":406},"clip":True,"strokes":s}]}
print(json.dumps(act))
