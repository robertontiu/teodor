import json, random, math, sys
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 4)
S=[]
def band_v(x0,x1,y0,y1,cols,size):
    n=len(cols)
    for i,c in enumerate(cols):
        x=x0+(x1-x0)*(i+0.5)/n
        y=y0
        while y<y1:
            L=random.uniform(90,200); yy=min(y1,y+L)
            S.append({"pts":[[round(x+random.uniform(-2,2)),round(y)],[round(x+random.uniform(-2,2)),round((y+yy)/2)],[round(x+random.uniform(-2,2)),round(yy)]],"size":size,"color":c})
            y=yy-10
            if yy>=y1: break
def band_h(y0,y1,x0,x1,cols,size):
    n=len(cols)
    for i,c in enumerate(cols):
        y=y0+(y1-y0)*(i+0.5)/n
        x=x0
        while x<x1:
            L=random.uniform(90,200); xx=min(x1,x+L)
            S.append({"pts":[[round(x),round(y+random.uniform(-2,2))],[round((x+xx)/2),round(y+random.uniform(-2,2))],[round(xx),round(y+random.uniform(-2,2))]],"size":size,"color":c})
            x=xx-10
            if xx>=x1: break
# left post: lit from the halo side (inner = right) and beam; outer darker
band_v(82,196,200,1110,["#3e2810","#6a4a1c","#9a7230","#c09440","#d8b058","#a07830","#5a3c16"],18)
band_v(196,222,205,1120,["#e8c870","#b08838","#4a3014"],10)
# right post: inner edge (left side) catches the halo
band_v(1008,1124,200,1110,["#4a3014","#9a7230","#c8a050","#a07830","#6a4a1c","#3e2810","#2a1a0a"],18)
band_v(982,1008,205,1120,["#4a3014","#c09440","#e0bc62"],10)
# top rail: underside lit faintly, top dark
band_h(60,176,180,1010,["#2e1e0c","#5a3c16","#8a6428","#a88034","#7a5420","#4a3014"],20)
band_h(176,206,200,1000,["#d0a850","#a88034","#3a2410"],10)
# bottom rail: top lit strongly (pool of light), front darker
band_h(1128,1146,190,1010,["#f0d080","#d8b058"],10)
band_h(1146,1206,150,1050,["#c09440","#9a7230","#6a4a1c","#3e2810"],16)
print(json.dumps({"type":"strokes","brush":"flat","strokes":S,"edge":"hard"}))
