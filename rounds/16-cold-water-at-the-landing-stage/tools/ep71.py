# Break the ruler-straight lower edge of the jetty shadow: ripples of lit teal cutting up into it,
# shadow tongues reaching down into the lit water; broken reflections under the posts.
import json
y = lambda x: 345 - 0.557*x
teal = ["#2a8a86","#2f9488","#289080","#33968c"]
dark = ["#1f3270","#1c2c68","#22346e"]
s1, s2 = [], []
for i,x in enumerate([20,100,180,260,340,420,500,570]):
    s1.append({"pts":[[x-28,round(y(x)-7)],[x+6,round(y(x)-10)],[x+38,round(y(x)-6)]],"size":14+(i%3)*3,"color":teal[i%4],"pressure":0.75})
    s2.append({"pts":[[x+44,round(y(x+44)+4)],[x+80,round(y(x+44)+9)]],"size":11+(i%2)*4,"color":dark[i%3],"pressure":0.7})
posts = [
 {"pts":[[78,346],[73,358]],"size":8,"color":"#241f4a","pressure":0.8},
 {"pts":[[81,370],[74,382]],"size":7,"color":"#2a2a58","pressure":0.7},
 {"pts":[[338,170],[333,182]],"size":7,"color":"#241f4a","pressure":0.8},
 {"pts":[[341,192],[335,203]],"size":6,"color":"#2a2a58","pressure":0.7}]
ep={"felt":{"arousal":0.3,"tension":0.15,"valence":0.6,"care":0.7},
 "do":[{"type":"strokes","brush":"filbert","strokes":s1,"fat":0.95,"impasto":0.55,"wetmix":0.35,"cover":0.95},
       {"type":"strokes","brush":"filbert","strokes":s2,"fat":0.95,"impasto":0.5,"wetmix":0.35,"cover":0.95},
       {"type":"strokes","brush":"round","strokes":posts,"fat":0.95,"impasto":0.5,"wetmix":0.3,"cover":0.9}]}
json.dump(ep,open('/home/claude/teodor-work/16/ep_71.json','w'))
