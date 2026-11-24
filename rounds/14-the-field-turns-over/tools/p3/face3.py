import numpy as np, json, subprocess
rng=np.random.default_rng(64)
H0=np.array([742.,1085.]); u=np.array([0.39,0.92]); v=np.array([0.92,-0.39])
P=lambda a,b: (H0+u*a+v*b).round(1).tolist()
# 1 face fill from schema, fine strokes
fill=json.loads(subprocess.check_output(['python3','/home/claude/v14/tools/fillmask.py','/home/claude/v14/tools/p3/face2_mask.npy','/home/claude/v14/tools/p3/head2_sch.png','3','6','3.5','64']))
# 2 broad soft light: dabs, no lines
dabs=[]
for (a,b,s,c) in [(-8,40,10,'#fff3cf'),(10,44,10,'#fff6d8'),(-26,46,9,'#fbf0cc'),(2,48,7,'#fffdf0'),(-14,50,6,'#fffdf2'),(20,40,8,'#f3efd6'),(-40,44,7,'#e8ecf6')]:
    for k in range(3):
        aa,bb=a+rng.uniform(-3,3),b+rng.uniform(-3,3)
        dabs.append({"pts":[P(aa,bb),P(aa+2,bb+1)],"size":s*rng.uniform(.8,1.1),"color":c})
# shadow plane toward the hairline
for a in np.arange(-48,30,6):
    dabs.append({"pts":[P(a,17+rng.uniform(0,3)),P(a+5,19)],"size":6,"color":rng.choice(['#6f92dc','#5f84d6','#7a9be0'])})
# 3 profile: grass hugging the silhouette
prof=[(34,40),(22,52),(12,55),(4,53),(-4,63),(-12,56),(-17,57),(-21,59),(-26,55),(-32,58),(-40,54),(-50,44),(-55,32)]
pa=np.array(prof,float); seg=[]
for i in range(len(pa)-1):
    for t in np.linspace(0,1,5,endpoint=False): seg.append(pa[i]*(1-t)+pa[i+1]*t)
seg=np.array(seg+[pa[-1]])
gr=[]
for off in (3,7):
    for i in range(len(seg)-2):
        (a0,b0),(a1,b1)=seg[i],seg[i+2]
        gr.append({"pts":[P(a0,b0+off),P(a1,b1+off)],"size":4.5,"color":rng.choice(['#e8ec4e','#eef05a','#e2e648','#f0f070'])})
# 4 the stray lump below the head
lump=[{"pts":[[712,1150],[728,1170],[744,1182]],"size":14,"color":"#e4e84a"},{"pts":[[706,1162],[722,1180]],"size":12,"color":"#dfe446"}]
json.dump(fill,open('/tmp/f1.json','w')); json.dump(dabs,open('/tmp/f2.json','w')); json.dump(gr,open('/tmp/f3.json','w')); json.dump(lump,open('/tmp/f4.json','w'))
