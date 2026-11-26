# Near water: broken flattened rings spreading from the man's body (centre ~ (300,1215)),
# broad loaded strokes, darkest close to him, a lighter crest only where a ring tips toward the sky.
import json, math, random
random.seed(62)
cx, cy = 300, 1215
def arc(rx, ry, a0, a1, n=5):
    return [[round(cx + rx*math.cos(math.radians(a)),1), round(cy + ry*math.sin(math.radians(a)),1)]
            for a in [a0 + (a1-a0)*i/(n-1) for i in range(n)]]
body, crests = [], []
darks = ["#16226a", "#1a2c78", "#1c2462", "#183a72", "#22306e"]
mids = ["#24448a", "#2a3c86", "#1f4c84", "#2e3a8a"]
rings = [(340,70),(450,110),(570,160),(700,220),(840,290),(980,370)]
for k,(rx,ry) in enumerate(rings):
    a = 8
    while a < 170:
        span = random.uniform(22, 48) * (1 + 0.3*k/5)
        a1 = min(a+span, 172)
        size = random.uniform(30, 54) * (0.8 + 0.25*k/5)
        col = random.choice(darks if k < 3 else darks+mids)
        body.append({"pts": arc(rx, ry, a, a1), "size": round(size), "color": col, "pressure": round(random.uniform(0.55,0.85),2)})
        if random.random() < 0.45:
            # crest: a thinner lighter stroke on the far (upper) side of the ring piece, shorter
            m0 = a + span*0.2; m1 = a + span*random.uniform(0.45,0.8)
            crests.append({"pts": arc(rx - size*0.35, ry - size*0.25, m0, m1, 4), "size": round(random.uniform(7,13)),
                           "color": random.choice(["#3e62b0","#4a72bc","#3a58a4","#5a7cc4"]), "pressure": 0.6})
        a = a1 + random.uniform(4, 14)
ep = {"felt":{"arousal":0.45,"tension":0.4,"valence":0.0,"care":0.6},
 "do":[
  {"type":"strokes","brush":"filbert","strokes":body,"fat":0.9,"impasto":0.55,"wetmix":0.45,"cover":0.95,"load":1.5},
  {"type":"strokes","brush":"round","strokes":crests,"fat":0.9,"impasto":0.6,"wetmix":0.3,"cover":0.9}
 ]}
json.dump(ep, open('/home/claude/teodor-work/16/ep_62.json','w'))
print(len(body), len(crests))
