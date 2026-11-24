import math
def finger(b,t,w,mid,lit,shd,tipc,crease,rim=None):
    dx,dy=t[0]-b[0],t[1]-b[1]; L=math.hypot(dx,dy); d=(dx/L,dy/L); n=(-d[1],d[0])
    if n[1]>0: n=(-n[0],-n[1])           # n points up (toward the sky)
    P=lambda s,o:[round(b[0]+d[0]*s*L+n[0]*o),round(b[1]+d[1]*s*L+n[1]*o)]
    S=[]
    S.append({"pts":[P(0,0),P(0.5,0),P(0.93,0)],"size":round(w*0.95,1),"color":mid})
    S.append({"pts":[P(0.02,w*0.22),P(0.5,w*0.2),P(0.9,w*0.16)],"size":round(w*0.42,1),"color":lit})
    S.append({"pts":[P(0.02,-w*0.3),P(0.5,-w*0.28),P(0.9,-w*0.22)],"size":round(w*0.3,1),"color":shd})
    S.append({"pts":[P(0.88,0),P(0.97,0)],"size":round(w*0.8,1),"color":tipc})
    C=[]
    for s in (0.42,0.7):
        C.append({"pts":[P(s,w*0.32),P(s+0.01,0),P(s,-w*0.3)],"size":1.8,"color":crease})
    R=[]
    if rim: R.append({"pts":[P(0.1,w*0.5),P(0.45,w*0.5),P(0.75,w*0.45)],"size":1.4,"color":rim})
    return S,C,R
