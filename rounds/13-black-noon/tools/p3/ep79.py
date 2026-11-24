import sys,random,math; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(79)
coat=[]
for i in range(14):
    y=1330+i*11
    coat.append({"pts":[[318,y-8],[352+rnd.uniform(-3,3),y+4],[362,y+12]],"size":round(rnd.uniform(12,16),1),"color":rnd.choice(['#0e0e10','#121216','#0b0b0d'])})
cuff=[{"pts":[[316,1338],[370,1318],[426,1302]],"size":30,"color":"#d6d8d6"},
      {"pts":[[318,1326],[372,1306],[424,1290]],"size":10,"color":"#f2f2ee"},
      {"pts":[[322,1352],[374,1332],[428,1316]],"size":6,"color":"#8a8e92"},
      {"pts":[[300,1300],[360,1280],[420,1268]],"size":26,"color":"#0e0e10"}]
tips=[{"pts":[[520,1532],[528,1544]],"size":18,"color":"#b88068"},{"pts":[[550,1494],[557,1505]],"size":17,"color":"#b88068"}]
rim=[{"pts":[[478,1402],[510,1440],[545,1480],[556,1494]],"size":1.5,"color":"#f4ece0"},
     {"pts":[[456,1426],[490,1478],[515,1514]],"size":1.3,"color":"#e8d8c8"},
     {"pts":[[372,1312],[420,1300],[452,1318]],"size":1.5,"color":"#f4ece0"}]
act({"arousal":0.2,"tension":0.1,"valence":0.0,"care":1.0},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":coat,"wetmix":0.2},
 {"type":"strokes","brush":"flat","edge":"hard","strokes":cuff,"wetmix":0.15,"impasto":0.8},
 {"type":"strokes","brush":"round","edge":"soft","strokes":tips,"wetmix":0.5},
 {"type":"strokes","brush":"liner","strokes":rim},
])
