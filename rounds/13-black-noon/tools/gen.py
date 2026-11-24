import json, math, sys
def face_to(x,z,tx=0,tz=0):
    return math.degrees(math.atan2(tx-x, tz-z))
def ringA(variant=1):
    figs=[]
    spec=[ # angle deg around camera, radius, height, color, spine, arm reach, coat/dress
        (180,1.05,1.80,"#1d2a3a",48,True,"coat"),   # top of frame (behind look dir)
        (140,1.10,1.70,"#b8241c",40,True,"dress"),
        (220,1.15,1.78,"#2e3d2a",42,False,"coat"),
        (100,1.25,1.65,"#d8d2b0",30,False,None),
        (260,1.20,1.85,"#20202a",35,True,None),
        (60,1.35,1.75,"#3a4a6a",25,False,"coat"),
        (300,1.30,1.60,"#c8b030",28,False,"dress"),
        (20,1.5,1.8,"#2a2a2a",20,False,None),
        (340,1.45,1.72,"#6a2a4a",22,False,"coat"),
    ]
    for ang,r,h,col,sp,reach,cl in spec:
        x=r*math.sin(math.radians(ang)); z=r*math.cos(math.radians(ang))
        f={"type":"figure","pos":[round(x,3),0,round(z,3)],"facing":round(face_to(x,z),1),"height":h,
           "color":col,"skin":"#d9a080","hair":"#1a1410",
           "joints":{"spine":sp,"head":35,"shoulders":0.02,
                     "arm_l":[70 if reach else 15,10,20 if reach else 15],
                     "arm_r":[85 if reach else 25,-5,10 if reach else 60],
                     "leg_l":[10,10],"leg_r":[-5,0]}}
        if cl: f[cl]=True
        figs.append(f)
    return {
     "camera":{"pos":[0,0.25,0.05],"look_at":[0,6,-1.6],"fov":70},
     "sun":{"azimuth":170,"elevation":72,"color":"#fffbe0","intensity":2.4,"softness":14},
     "sky":{"zenith":"#e8f0f0","horizon":"#fbfbea","sun_glow":1.5,"disc":3},
     "ambient":{"sky":"#bcd0e0","ground":"#a0a080","intensity":0.55},
     "fog":{"color":"#f4f4e4","density":0.01},
     "ground":{"color":"#9a9a8c","color2":"#8a8a7e"},
     "exposure":1.3,"objects":figs}
def topB():
    import random; random.seed(3)
    figs=[]
    cols=["#1a1a22","#c02018","#e8e0c0","#2a4a8a","#d0b020","#303a30","#f0f0f0","#6a2050","#202020"]
    for i in range(26):
        a=random.uniform(0,360); r=random.uniform(1.6,4.2)
        x=r*math.sin(math.radians(a)); z=r*math.cos(math.radians(a))
        recoil = r<2.6
        f={"type":"figure","pos":[round(x,2),0,round(z,2)],"facing":round(face_to(x,z)+random.uniform(-25,25),1),
           "height":random.uniform(1.55,1.9),"color":random.choice(cols),"skin":"#d0a080","hair":"#201810",
           "pose":"walk" if not recoil else "stand",
           "joints":{"spine":-8 if recoil else 0,"arm_l":[random.choice([10,60,120]),20,30],"arm_r":[random.choice([10,70,150]),15,40]} }
        figs.append(f)
    figs+= [{"type":"box","pos":[0.2,0.04,0.1],"size":[0.32,0.08,0.12],"rot":30,"color":"#e8e8e8","round":0.03},
            {"type":"ellipsoid","pos":[-0.5,0.08,-0.3],"radii":[0.2,0.08,0.12],"rot":10,"color":"#c8b020"},
            {"type":"sphere","pos":[0.7,0.06,0.5],"r":0.06,"color":"#d02818"}]
    return {"camera":{"pos":[0.5,13,4.5],"look_at":[0,0,0],"fov":42},
     "sun":{"azimuth":120,"elevation":55,"color":"#fffff0","intensity":2.6,"softness":16},
     "sky":{"zenith":"#c0d8e8","horizon":"#f0f0e8","sun_glow":0.8,"disc":0},
     "ambient":{"sky":"#90b0d0","ground":"#c0c0b0","intensity":0.5},
     "fog":{"color":"#e8ece8","density":0.004},
     "ground":{"color":"#d8d4c4","color2":"#c4c0b0"},"exposure":1.25,"objects":figs}
def closeC():
    f={"type":"figure","pos":[0,0,0],"facing":10,"height":1.7,"dress":True,"color":"#141418","skin":"#e0b090","hair":"#0a0a0a",
       "joints":{"leg_l":[0,100],"leg_r":[0,100],"spine":-22,"head":-40,"arm_l":[150,40,15],"arm_r":[140,35,25]}}
    return {"camera":{"pos":[0.6,0.5,2.3],"look_at":[0,1.0,0],"fov":50},
     "sun":{"azimuth":200,"elevation":30,"color":"#f0f8ff","intensity":2.6,"softness":16},
     "sky":{"zenith":"#4a6aa8","horizon":"#e8f0f8","sun_glow":1.2,"disc":2},
     "ambient":{"sky":"#a0b8e0","ground":"#e8eef8","intensity":0.6},
     "fog":{"color":"#e8f0f8","density":0.01},
     "ground":{"color":"#f4f6fa","color2":"#e0e8f0"},"exposure":1.3,"objects":[f,
       {"type":"tree","pos":[-6,0,-14],"h":5,"bare":True,"color":"#203040","trunk":"#101820"},
       {"type":"fence","a":[-12,0,-10],"b":[10,0,-12],"h":1.0,"color":"#203040"}]}
w=sys.argv[1]; out=sys.argv[2]
d={"A":ringA,"B":topB,"C":closeC}[w]()
json.dump(d,open(out,"w"),indent=1)
