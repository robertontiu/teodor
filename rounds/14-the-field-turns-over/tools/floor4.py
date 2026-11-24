import json, numpy as np
rng=np.random.default_rng(41)
def h(c): return np.array([int(c[i:i+2],16) for i in (1,3,5)],float)
def hexc(c): return '#%02x%02x%02x'%tuple(int(v) for v in np.clip(c,0,255))
src=np.array([700.,880.])
def infan(x,y):
    # signed distance-ish inside fan between rays
    t=(y-1004)/596
    xl=527+(300-527)*t; xr=871+(1060-871)*t
    w=(xr-xl)
    a=np.clip((x-xl)/45+0.5,0,1)*np.clip((xr-x)/45+0.5,0,1)
    return a
def col(x,y):
    t=np.clip((y-1004)/596,0,1)
    lit=h('#6c5640')*(1-t)+h('#3e2c1b')*t
    dark=h('#2a1c11')*(1-t)+h('#1e140c')*t
    a=infan(x,y)
    c=dark+(lit-dark)*a
    # walker shadow
    sx=726+(640-726)*np.clip((y-1004)/300,0,1)
    if y<1320:
        k=np.exp(-((x-sx)/(9+10*(y-1004)/300))**2)*(1-(y-1004)/330)
        c=c*(1-0.35*k)
    return c
s=[]
for i in range(900):
    x=rng.uniform(380,1200); y=rng.uniform(1006,1600)
    d=np.array([x,y])-src; d/=np.linalg.norm(d)
    L=rng.uniform(50,110); sz=rng.uniform(16,26)
    c=col(x,y)*rng.uniform(0.95,1.05)
    s.append({"pts":[[x-d[0]*L/2,y-d[1]*L/2],[x+d[0]*L/2,y+d[1]*L/2]],"size":float(sz),"color":hexc(c)})
region={"type":"poly","pts":[[395,1004],[1200,1004],[1200,1600],[448,1600],[432,1300],[418,1160],[402,1060]]}
act={"felt":{"arousal":0.3,"tension":0.1,"valence":0.2,"care":0.7},"do":[
 {"type":"strokes","brush":"flat","impasto":0.3,"load":1.3,"cover":0.95,"wetmix":0.3,"pickup":0.1,"region":region,"clip":True,"strokes":s}]}
print(json.dumps(act))
