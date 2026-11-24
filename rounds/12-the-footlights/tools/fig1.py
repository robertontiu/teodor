import json, math, random
random.seed(1)
S=[]
def st(pts,size,color): S.append({"pts":[[round(x),round(y)] for x,y in pts],"size":size,"color":color})
# mantle behind, his left (our right): dark
for i in range(9):
    x=668+i*7+random.uniform(-3,3)
    st([(x-6,852+i*4),(x+4,980),(x+10,1110),(x+14,1236)],16,random.choice(["#4a0814","#3c0610","#560c1a"]))
# robe column
for i in range(10):
    x=562+i*12
    c="#a8263a" if i<2 else ("#7a1226" if i<6 else "#560c1c")
    st([(x+2,1010),(x,1120),(x-2,1236)],18,c)
# chest / shoulders
for i in range(7):
    y=848+i*8
    st([(552,y),(610,y-4),(678,y+2)],16,"#9a1c30" if i<3 else "#7a1226")
# belly: curved strokes
cx,cy,rx,ry=588,962,74,66
for k in range(12):
    r=1-k*0.07
    a0,a1=math.radians(200),math.radians(340)
    pts=[(cx+rx*r*math.cos(a0+(a1-a0)*t/6), cy-ry*r*math.sin(a0+(a1-a0)*t/6)) for t in range(7)]
    st(pts,16,"#5a0c1c")
for k in range(9):
    r=0.95-k*0.1
    a0,a1=math.radians(100),math.radians(230)
    pts=[(cx+rx*r*math.cos(a0+(a1-a0)*t/5), cy-ry*r*math.sin(a0+(a1-a0)*t/5)) for t in range(6)]
    st(pts,16,["#c4384a","#b02c40","#9a2036"][k%3])
for k in range(6):
    r=0.7-k*0.1
    a0,a1=math.radians(-40),math.radians(90)
    pts=[(cx+rx*r*math.cos(a0+(a1-a0)*t/5), cy-ry*r*math.sin(a0+(a1-a0)*t/5)) for t in range(6)]
    st(pts,16,"#7e1428")
print(json.dumps({"type":"strokes","brush":"round","strokes":S,"edge":"hard"}))
