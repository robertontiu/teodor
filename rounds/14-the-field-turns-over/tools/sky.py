import json, numpy as np
def lerp(a,b,t):
    a=np.array([int(a[i:i+2],16) for i in (1,3,5)]);b=np.array([int(b[i:i+2],16) for i in (1,3,5)])
    c=a+(b-a)*t; return '#%02x%02x%02x'%tuple(int(round(v)) for v in c)
def col(y):
    stops=[(470,'#e2dccb'),(700,'#eee8d8'),(850,'#f8f2e2'),(875,'#f4ecda'),(920,'#d8ccb3'),(1000,'#a69676')]
    for (y0,c0),(y1,c1) in zip(stops,stops[1:]):
        if y<=y1: return lerp(c0,c1,max(0,(y-y0)/(y1-y0)))
    return stops[-1][1]
strokes=[]
rng=np.random.default_rng(3)
for y in range(470,1004,9):
    x0=515+rng.uniform(-5,5); x1=885+rng.uniform(-5,5)
    pts=[[x0,y],[ (x0+x1)/2, y+rng.uniform(-1.5,1.5)],[x1,y]]
    strokes.append({"pts":pts,"size":24,"color":col(y)})
    strokes.append({"pts":pts[::-1],"size":24,"color":col(y)})
act={"felt":{"arousal":0.2,"tension":0.1,"valence":0.3,"care":0.8},"do":[
 {"type":"strokes","brush":"flat","impasto":0,"load":1.4,"cover":1.0,"wetmix":0.15,"region":{"type":"rect","x":527,"y":474,"w":345,"h":528},"clip":True,"strokes":strokes}]}
print(json.dumps(act))
