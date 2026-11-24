import json, numpy as np
rng=np.random.default_rng(11)
def mix(a,b,t):
    a=np.array([int(a[i:i+2],16) for i in (1,3,5)]);b=np.array([int(b[i:i+2],16) for i in (1,3,5)])
    return '#%02x%02x%02x'%tuple(int(v) for v in a+(b-a)*t)
floor=[]
for y in range(1028,1185,7):
    for d in (0,1):
        x0,x1=398,672
        cl=mix('#3a2f23','#5e4a35',(y-1028)/160*0.3+0.35*d)
        pts=[[x0,y],[x1,y+rng.uniform(-3,3)]]
        floor.append({"pts":pts if d else pts[::-1],"size":14,"color":mix(cl,'#6a5640',rng.uniform(0,0.4))})
sleeve=[{"pts":[[372,928],[420,962],[468,1000],[515,1045],[556,1088]],"size":36,"color":"#1d1712"},
        {"pts":[[380,920],[425,952],[470,990],[518,1036],[560,1080]],"size":20,"color":"#241c15"},
        {"pts":[[540,1078],[560,1098]],"size":30,"color":"#1a1410"}]
hand=[{"pts":[[562,1094],[585,1106],[606,1112]],"size":24,"color":"#7a563d"},
      {"pts":[[566,1100],[590,1112],[610,1118]],"size":14,"color":"#5e412f"},
      {"pts":[[606,1110],[626,1108],[645,1103]],"size":7,"color":"#8d664a"},
      {"pts":[[607,1116],[628,1116],[648,1112]],"size":7,"color":"#835d43"},
      {"pts":[[604,1122],[624,1124],[641,1121]],"size":6.5,"color":"#76533b"},
      {"pts":[[598,1126],[615,1131],[629,1130]],"size":6,"color":"#6c4b36"},
      {"pts":[[588,1100],[598,1090],[611,1086]],"size":7,"color":"#8a6347"}]
rims=[{"pts":[[574,1096],[596,1100],[612,1103],[632,1100],[646,1098]],"size":2.6,"color":"#e8c9a0"},
      {"pts":[[592,1092],[603,1085],[612,1084]],"size":2.2,"color":"#efd2a8"},
      {"pts":[[630,1107],[648,1106]],"size":2.0,"color":"#d9b78e"},
      {"pts":[[384,915],[425,944],[470,982],[520,1030],[556,1072]],"size":2.6,"color":"#a88c66"}]
act={"felt":{"arousal":0.2,"tension":0.15,"valence":0.3,"care":0.98},"do":[
 {"type":"strokes","brush":"flat","impasto":0.2,"load":1.2,"cover":0.9,"wetmix":0.35,"region":{"type":"poly","pts":[[398,1028],[672,1028],[672,1185],[410,1185]]},"clip":True,"strokes":floor},
 {"type":"strokes","brush":"round","impasto":0.3,"load":1.5,"cover":1.0,"wetmix":0.05,"pickup":0.0,"edge":"hard","strokes":sleeve},
 {"type":"strokes","brush":"round","impasto":0.45,"load":1.5,"cover":1.0,"wetmix":0.1,"pickup":0.0,"edge":"hard","strokes":hand},
 {"type":"strokes","brush":"liner","impasto":0.4,"strokes":rims}]}
print(json.dumps(act))
