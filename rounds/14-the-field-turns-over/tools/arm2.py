import json, numpy as np
axis=[[368,926],[420,960],[466,998],[512,1042],[552,1084]]
def off(pts,o):
    out=[]
    P=np.array(pts,float)
    for i,p in enumerate(P):
        d=P[min(i+1,len(P)-1)]-P[max(i-1,0)]; d/=np.linalg.norm(d)
        n=np.array([-d[1],d[0]])
        w=o*(1-0.25*i/(len(P)-1))
        out.append(list(p+n*w))
    return out
sleeve=[]
for o,c,sz in [(-12,"#2a2118",14),(-4,"#201912",14),(4,"#1a140f",14),(12,"#140f0b",13),(0,"#1d1611",20)]:
    sleeve.append({"pts":off(axis,o),"size":sz,"color":c})
# elbow fold and cuff
sleeve+= [{"pts":[[458,986],[470,1002],[476,1014]],"size":5,"color":"#0f0b08"},
          {"pts":[[536,1060],[556,1080],[568,1098]],"size":24,"color":"#1b1510"}]
hand=[{"pts":[[566,1098],[590,1110],[612,1116]],"size":26,"color":"#7c5a40"},   # palm mass
      {"pts":[[570,1108],[594,1120],[612,1124]],"size":14,"color":"#5a3f2c"},   # heel shadow
      {"pts":[[610,1108],[632,1104],[652,1100]],"size":8,"color":"#93704f"},    # index
      {"pts":[[612,1115],[636,1114],[656,1110]],"size":8,"color":"#8a674a"},    # middle
      {"pts":[[610,1122],[632,1124],[650,1121]],"size":7.5,"color":"#7c5c42"},  # ring
      {"pts":[[604,1128],[620,1132],[635,1131]],"size":6.5,"color":"#6e5039"},  # little
      {"pts":[[586,1102],[597,1090],[610,1084]],"size":8,"color":"#8c6a4b"}]    # thumb
rims=[{"pts":[[600,1098],[618,1101],[636,1098],[652,1096]],"size":2.4,"color":"#e9cda4"},
      {"pts":[[594,1089],[604,1082],[612,1081]],"size":2.2,"color":"#f0d5ac"},
      {"pts":[[640,1107],[656,1106]],"size":1.8,"color":"#d9b88f"},
      {"pts":[[392,930],[410,940]],"size":2.2,"color":"#8a7055"},
      {"pts":[[440,966],[462,982]],"size":2.2,"color":"#7d664c"},
      {"pts":[[500,1018],[520,1036]],"size":2.0,"color":"#86704f"},
      {"pts":[[540,1058],[556,1074]],"size":2.0,"color":"#9a8060"}]
act={"felt":{"arousal":0.2,"tension":0.15,"valence":0.3,"care":0.98},"do":[
 {"type":"strokes","brush":"round","impasto":0.35,"load":1.5,"cover":1.0,"wetmix":0.05,"pickup":0.0,"edge":"hard","strokes":sleeve},
 {"type":"strokes","brush":"round","impasto":0.5,"load":1.5,"cover":1.0,"wetmix":0.1,"pickup":0.0,"edge":"hard","strokes":hand},
 {"type":"strokes","brush":"liner","impasto":0.4,"strokes":rims}]}
print(json.dumps(act))
