import json, sys, numpy as np
sys.path.insert(0,'/home/claude/tools')
def lerp(a,b,t):
    a=np.array([int(a[i:i+2],16) for i in (1,3,5)]);b=np.array([int(b[i:i+2],16) for i in (1,3,5)])
    c=a+(b-a)*t; return '#%02x%02x%02x'%tuple(int(round(v)) for v in c)
def grad(stops,y):
    for (y0,c0),(y1,c1) in zip(stops,stops[1:]):
        if y<=y1: return lerp(c0,c1,max(0,min(1,(y-y0)/(y1-y0))))
    return stops[-1][1]
sky=[(470,'#e2dccb'),(700,'#eee8d8'),(850,'#f8f2e2'),(890,'#f6eedd')]
gnd=[(880,'#efe5d0'),(905,'#d6c9ae'),(950,'#b8a888'),(1000,'#9c8b6c')]
rng=np.random.default_rng(5)
ks=[]
for rep in range(2):
  for y in range(472,885,7):
    x0=520;x1=880
    ks.append({"pts":[[x0,y],[x1,y+rng.uniform(-1,1)]],"size":30,"color":grad(sky,y)})
gs=[]
for y in range(876,1004,7):
    for d in (1,-1):
        p=[[516,y],[884,y]]; gs.append({"pts":p[::d],"size":22,"color":grad(gnd,y)})
act={"felt":{"arousal":0.15,"tension":0.1,"valence":0.3,"care":0.85},"do":[
 {"type":"strokes","brush":"knife","impasto":0,"region":{"type":"rect","x":527,"y":474,"w":345,"h":410},"clip":True,"strokes":ks},
 {"type":"strokes","brush":"flat","impasto":0,"load":1.6,"cover":1.0,"wetmix":0.05,"pickup":0.0,"region":{"type":"rect","x":527,"y":872,"w":345,"h":130},"clip":True,"strokes":gs}]}
print(json.dumps(act))
