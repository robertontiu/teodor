# Calm the tangle on the right of the near water: broad dark pieces along the same ring family (centre (300,1215)),
# laid over the crossing ribbons; then three short pale crest pieces only, broken.
import json, math
cx, cy = 300, 1215
def arc(rx, ry, a0, a1, n=5):
    return [[round(cx + rx*math.cos(math.radians(a)),1), round(cy + ry*math.sin(math.radians(a)),1)] for a in [a0+(a1-a0)*i/(n-1) for i in range(n)]]
body = []
plan = [(420,90,5,40,"#1a2a72",46),(520,135,4,36,"#16226a",50),(620,180,4,32,"#1c2c74",54),(720,235,6,34,"#18246c",56),
        (820,290,8,36,"#1a2870",58),(920,345,10,34,"#16205e",60),(1020,400,12,32,"#18246a",60),
        (470,112,20,52,"#1c2a70",44),(670,205,22,50,"#1a2668",50),(870,320,24,48,"#16225f",56)]
for rx,ry,a0,a1,c,s in plan:
    body.append({"pts":arc(rx,ry,a0,a1),"size":s,"color":c,"pressure":0.7})
crest = [
 {"pts":arc(560,150,14,26,4),"size":9,"color":"#4a6cb8","pressure":0.6},
 {"pts":arc(760,250,10,19,4),"size":8,"color":"#3e60ac","pressure":0.6},
 {"pts":arc(960,370,16,23,3),"size":7,"color":"#3a5aa4","pressure":0.6}]
ep={"felt":{"arousal":0.3,"tension":0.3,"valence":0.0,"care":0.7},
 "do":[{"type":"strokes","brush":"flat","strokes":body,"fat":0.9,"impasto":0.5,"wetmix":0.5,"cover":0.93,"load":1.6},
       {"type":"strokes","brush":"round","strokes":crest,"fat":0.9,"impasto":0.65,"wetmix":0.25,"cover":0.9}]}
json.dump(ep,open('/home/claude/teodor-work/16/ep_64.json','w'))
