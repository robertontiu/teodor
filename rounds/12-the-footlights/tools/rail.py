import json, random
random.seed(9)
S=[]
def band_h(y0,y1,x0,x1,cols,size):
    n=len(cols)
    for i,c in enumerate(cols):
        y=y0+(y1-y0)*(i+0.5)/n; x=x0
        while True:
            xx=min(x1,x+random.uniform(80,180))
            S.append({"pts":[[round(x),round(y+random.uniform(-1.5,1.5))],[round((x+xx)/2),round(y+random.uniform(-1.5,1.5))],[round(xx),round(y+random.uniform(-1.5,1.5))]],"size":size,"color":c})
            if xx>=x1: break
            x=xx-8
for a,b in [(130,548),(698,1070)]:
    band_h(1126,1144,a,b,["#f4d488","#e0b864"],10)
    band_h(1144,1196,a,b,["#c8984a","#a87a34","#7a5424","#4a3014"],14)
    band_h(1196,1226,a-60,b+60,["#e0a858","#c88c44"],14)
print(json.dumps({"type":"strokes","brush":"flat","strokes":S,"edge":"soft"}))
