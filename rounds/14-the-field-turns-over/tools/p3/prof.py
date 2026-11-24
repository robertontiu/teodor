import numpy as np, json
rng=np.random.default_rng(55)
H0=np.array([742.,1085.]); u=np.array([0.39,0.92]); v=np.array([0.92,-0.39])
P=lambda a,b: (H0+u*a+v*b).round(1).tolist()
prof=[(34,40),(22,52),(12,55),(4,53),(-4,63),(-12,56),(-17,57),(-21,59),(-26,55),(-32,58),(-40,54),(-50,44),(-55,32)]
# dense interpolation of the profile
pa=np.array(prof,float); seg=[]
for i in range(len(pa)-1):
    for t in np.linspace(0,1,6,endpoint=False): seg.append(pa[i]*(1-t)+pa[i+1]*t)
seg.append(pa[-1]); seg=np.array(seg)
grass=[]; cols=['#e4eb4a','#ecef5a','#f2f07a','#e1e54a','#f4f39a']
# grass outside the profile: short strokes in bands following the profile
for off in (5,11,17,23):
    for i in range(0,len(seg)-3,2):
        a0,b0=seg[i]; a1,b1=seg[i+3]
        grass.append({"pts":[P(a0,b0+off+rng.uniform(-2,2)),P(a1,b1+off+rng.uniform(-2,2))],"size":round(rng.uniform(6,8),1),"color":rng.choice(cols)})
rng.shuffle(grass)
edge=[{"pts":[P(a,b-1.5) for a,b in seg],"size":2.2,"color":"#fffdf0"}]
# hairline: the hard boundary between lit face and dark hair (b about 14-30)
hl=[(28,30),(14,24),(-2,18),(-18,14),(-36,16),(-50,22)]
dark=[{"pts":[P(a,b-2) for a,b in hl],"size":3,"color":"#121a66"}]
json.dump(grass,open('/tmp/g.json','w')); json.dump(edge,open('/tmp/e.json','w')); json.dump(dark,open('/tmp/d.json','w'))
