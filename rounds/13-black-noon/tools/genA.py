import json, math, sys
def face_to(x,z): return math.degrees(math.atan2(-x,-z))
# (angle, radius, height, color, spine, head, arm_l, arm_r, clothing, skin, hair, pose override)
P=[
 (200,0.80,1.82,"#121418",60,25,[10,8,20],[25,-6,15],"coat","#c89070","#14100c"),
 (150,0.75,1.70,"#c81e14",55,30,[20,10,40],[5,0,10],"dress","#e0b090","#3a2210"),
 (110,0.85,1.78,"#e8e4d0",50,25,[0,6,10],[35,-10,25],None,"#a06848","#0a0808"),
 (65,0.70,1.75,"#1e3c9a",62,30,[15,5,15],[0,8,10],None,"#d8a080","#c0a060"),
 (20,0.85,1.66,"#d8c818",48,35,[10,10,30],[8,5,20],"coat","#e8c0a0","#201410"),
 (300,0.90,1.88,"#2a2a26",45,30,[5,6,15],[20,0,30],"coat","#b07858","#101010"),
]
figs=[]
for a,r,h,c,sp,hd,al,ar,cl,sk,hr in P:
    x=r*math.sin(math.radians(a)); z=r*math.cos(math.radians(a))
    f={"type":"figure","pos":[round(x,3),0,round(z,3)],"facing":round(face_to(x,z),1),"height":h,"color":c,"skin":sk,"hair":hr,
       "joints":{"spine":sp,"head":hd,"arm_l":al,"arm_r":ar,"leg_l":[25,15],"leg_r":[5,5]}}
    if cl: f[cl]=True
    figs.append(f)
# close kneeling figure reaching right into our face
x,z=0.35,-0.15
figs.append({"type":"figure","pos":[x,0,z],"facing":round(face_to(x,z),1),"height":1.72,"color":"#f0eee6","skin":"#d09070","hair":"#1a120c",
  "joints":{"leg_l":[80,85],"leg_r":[0,95],"spine":40,"head":30,"arm_l":[55,-5,20],"arm_r":[10,10,30]}})
d={"camera":{"pos":[0,0.12,0],"look_at":[0.3,5,-0.9],"fov":68},
 "sun":{"azimuth":200,"elevation":70,"color":"#fffbe8","intensity":2.6,"softness":14},
 "sky":{"zenith":"#eef4e4","horizon":"#fcfcf0","sun_glow":1.5,"disc":4},
 "ambient":{"sky":"#c8d8e8","ground":"#b8b8a0","intensity":0.6},
 "fog":{"color":"#f4f6ea","density":0.01},
 "ground":{"color":"#9a9a90","color2":"#8a8a80"},"exposure":1.3,"objects":figs}
json.dump(d,open(sys.argv[1],"w"),indent=1)
