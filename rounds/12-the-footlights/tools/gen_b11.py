import json, random, sys, math
import numpy as np
random.seed(5)
obj=[]
B=1.05   # dais top
# dais: stepped, gilt edges
obj.append({"type":"box","pos":[0,B/2,-0.6],"size":[3.2,B,2.4],"color":"#7a4a1c","round":0.04})
obj.append({"type":"box","pos":[0,B-0.06,0.62],"size":[3.3,0.14,0.12],"color":"#d0a040","round":0.04})
obj.append({"type":"box","pos":[0,0.25,0.95],"size":[3.8,0.5,0.6],"color":"#5a3416","round":0.03})
# back wall
obj.append({"type":"box","pos":[0,6,-2.4],"size":[16,12,0.3],"color":"#2a120c"})
# huge EMPTY gilt frame, he stands inside it at its bottom rail
FZ=-1.55; fw=2.5; ftop=B+3.3; fb=B+0.02; rail=0.34
for p,s in [([0,ftop,FZ],[fw+2*rail,rail,0.26]),([0,fb,FZ],[fw+2*rail,rail,0.26]),
            ([-(fw/2+rail/2),(ftop+fb)/2,FZ],[rail,ftop-fb+rail,0.26]),([(fw/2+rail/2),(ftop+fb)/2,FZ],[rail,ftop-fb+rail,0.26])]:
    obj.append({"type":"box","pos":p,"size":s,"color":"#c8902e","round":0.07})
# inner moulding
for p,s in [([0,ftop-rail/2-0.04,FZ+0.1],[fw,0.07,0.06]),([0,fb+rail/2+0.04,FZ+0.1],[fw,0.07,0.06]),
            ([-fw/2+0.04,(ftop+fb)/2,FZ+0.1],[0.07,ftop-fb-rail,0.06]),([fw/2-0.04,(ftop+fb)/2,FZ+0.1],[0.07,ftop-fb-rail,0.06])]:
    obj.append({"type":"box","pos":p,"size":s,"color":"#e8b850","round":0.02})
# corner rosettes
for cx in (-(fw/2+rail/2),(fw/2+rail/2)):
    for cy in (ftop,fb):
        obj.append({"type":"sphere","pos":[cx,cy,FZ+0.14],"r":0.26,"color":"#d8a038"})
# crest on top of the frame (ornate cartouche, no emblem)
obj.append({"type":"ellipsoid","pos":[0,ftop+0.38,FZ+0.05],"radii":[0.55,0.32,0.12],"color":"#d09a34"})
# curtains swag
for sx in (-1,1):
    for k in range(5):
        obj.append({"type":"cylinder","pos":[sx*(2.6+k*0.3),0,-2.0+k*0.05],"r":0.2,"h":9,"color":"#5e1416"})
# ---- the ruler
H=1.45; s=H/1.70; spine=-6; facing=-28
fp=np.array([0.05,B,-0.9])
R={"type":"figure","pos":list(map(float,fp)),"facing":facing,"height":H,"pose":"stand",
   "joints":{"spine":spine,"head":-16,"head_yaw":-35,"arm_r":[168,-38,8],"arm_l":[0,4,0],"leg_l":[4,0],"leg_r":[-8,4]},
   "coat":True,"color":"#7a1024","skin":"#e2bca6","hair":None}
del R["hair"]
obj.append(R)
def rot_x(a):
    c,s_=math.cos(a),math.sin(a); return np.array([[1,0,0],[0,c,-s_],[0,s_,c]])
def rot_y(a):
    c,s_=math.cos(a),math.sin(a); return np.array([[c,0,s_],[0,1,0],[-s_,0,c]])
Rs=rot_x(math.radians(spine)); Mr=rot_y(math.radians(facing))
lift=0.925
def W(v): return list(map(float, fp+Mr@((np.array(v)+np.array([0,lift,0]))*s)))
def Wl(v): return W(Rs@np.array(v))
sh=Wl([0.18,0.45,0]); el=Wl([0.40,0.20,0.02]); hand=Wl([0.17,0.06,0.10])
obj.append({"type":"capsule","a":sh,"b":el,"r":0.05*s,"color":"#7a1024"})
obj.append({"type":"capsule","a":el,"b":hand,"r":0.043*s,"color":"#7a1024"})
obj.append({"type":"sphere","pos":hand,"r":0.05*s,"color":"#e2bca6"})
# belly out, gold sash across it
bel=Wl([0,0.06,0.09]); obj.append({"type":"ellipsoid","pos":bel,"radii":[0.22*s,0.23*s,0.23*s],"color":"#7a1024"})
obj.append({"type":"capsule","a":Wl([0.15,0.36,0.13]),"b":Wl([-0.17,0.0,0.25]),"r":0.045,"color":"#e09030"})
# ermine collar/cape short
obj.append({"type":"ellipsoid","pos":Wl([0,0.47,-0.02]),"radii":[0.25*s,0.07*s,0.17*s],"color":"#ece2d0"})
# mantle behind, pooling
obj.append({"type":"capsule","a":Wl([0,0.45,-0.14]),"b":Wl([0.02,-0.85,-0.3]),"r":0.2*s,"color":"#5a0c1c"})
obj.append({"type":"ellipsoid","pos":[0.15,B+0.02,-1.25],"radii":[0.5,0.05,0.3],"color":"#5a0c1c"})
# tiny crown, slightly askew
hd=W(Rs@np.array([0,0.62,0.03]))
obj.append({"type":"cylinder","pos":[hd[0]-0.01,hd[1]+0.06,hd[2]],"r":0.055,"h":0.08,"color":"#f2c848"})
# ---- cardboard crowd, from behind; flat boards with easel struts
for row in range(6):
    z=2.2+row*1.0
    n=7+row*2
    for i in range(n):
        x=(i-(n-1)/2)*0.68+random.uniform(-0.1,0.1)
        h=random.uniform(1.55,1.7); rot=random.choice([random.uniform(-15,15),random.uniform(-15,15),random.choice([-1,1])*random.uniform(45,70)])
        c=random.choice(["#7a5a3a","#6e5034","#80603e"])
        obj.append({"type":"box","pos":[x,h*0.62,z],"size":[0.46,h*0.5,0.015],"rot":rot,"color":c})  # torso board
        obj.append({"type":"ellipsoid","pos":[x,h*0.94,z],"radii":[0.115,0.14,0.01],"rot":rot,"color":c})
        obj.append({"type":"box","pos":[x,h*0.19,z],"size":[0.05,h*0.38,0.015],"rot":rot,"color":"#5a4028"})  # single post
        # easel strut toward the viewer
        obj.append({"type":"capsule","a":[x,h*0.6,z+0.02],"b":[x+random.uniform(-0.05,0.05),0,z+0.55],"r":0.016,"color":"#4a3220"})
        if random.random()<0.4:
            sd=random.choice([-1,1])
            obj.append({"type":"capsule","a":[x+sd*0.2,h*0.82,z],"b":[x+sd*0.26,h*1.12,z],"r":0.035,"color":c})
sc={"camera":{"pos":[0.8,2.7,8.4],"look_at":[0,2.35,-1],"fov":27},
 "sun":{"azimuth":168,"elevation":40,"color":"#ffb060","intensity":0.45,"softness":12},
 "sky":{"zenith":"#0c0606","horizon":"#160c0a","sun_glow":0,"disc":0},
 "ambient":{"sky":"#2a2430","ground":"#2a1a12","intensity":0.2},
 "fog":{"color":"#1a0e0a","density":0.035},
 "ground":{"color":"#2a1810","color2":"#22140e"},
 "lights":[{"pos":[-1.0,3.4,0.9],"color":"#fff0d8","intensity":9,"radius":1.5},
           {"pos":[0,3.0,-1.3],"color":"#ffb050","intensity":1.3,"radius":1.2}],
 "exposure":1.25,"objects":obj}
json.dump(sc,open(sys.argv[1],"w"),indent=1)
