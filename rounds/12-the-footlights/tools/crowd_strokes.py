import random, json, sys
random.seed(11)
rows=[]
def cut(cx,top,s,col,rim,arm=0,edge=False,strut=True,tilt=0):
    body=[];rims=[];struts=[]
    sh=lambda c: c
    if edge:
        w=7*s
        for dx in (-w/2,w/2):
            body.append({"pts":[[cx+dx,top+10*s],[cx+dx,top+200*s],[cx+dx,top+400*s]],"size":max(3,w),"color":col})
        rims.append({"pts":[[cx-w,top+400*s],[cx-w,top+20*s],[cx,top],[cx+w*0.6,top+14*s]],"size":max(1.5,1.6*s+0.6),"color":rim})
        return body,rims,struts
    # torso: vertical strokes
    n=int(6+4*s)
    for i in range(n):
        x=cx-66*s+132*s*(i+0.5)/n
        ytop=top+(118 if abs(x-cx)>60*s else (96 if abs(x-cx)>34*s else 84))*s
        body.append({"pts":[[x,ytop],[x+random.uniform(-1,1),top+260*s],[x,top+410*s]],"size":132*s/n*1.5,"color":col})
    # shoulder line strokes
    body.append({"pts":[[cx-70*s,top+112*s],[cx-34*s,top+88*s],[cx+34*s,top+88*s],[cx+70*s,top+112*s]],"size":16*s,"color":col})
    # neck and head
    body.append({"pts":[[cx,top+88*s],[cx,top+60*s]],"size":20*s,"color":col})
    for k in range(5):
        yy=top+(6+k*15)*s
        hw=29*s*[0.55,0.9,1.0,0.9,0.6][k]
        body.append({"pts":[[cx-hw*0.5,yy],[cx+hw*0.5,yy]],"size":hw*1.3,"color":col})
    if arm:
        sd=arm
        body.append({"pts":[[cx+sd*60*s,top+96*s],[cx+sd*72*s,top+50*s],[cx+sd*80*s,top+12*s]],"size":20*s,"color":col})
        body.append({"pts":[[cx+sd*80*s,top+16*s],[cx+sd*80*s,top-12*s]],"size":26*s,"color":col})
        rims.append({"pts":[[cx+sd*68*s,top+96*s],[cx+sd*86*s,top+20*s],[cx+sd*92*s,top-10*s],[cx+sd*80*s,top-18*s],[cx+sd*68*s,top-6*s]],"size":max(1.5,1.3*s+0.5),"color":rim})
    # rims: straight cut outline (top edges only, lit from above/behind stage)
    rims.append({"pts":[[cx-72*s,top+170*s],[cx-72*s,top+118*s],[cx-60*s,top+96*s],[cx-34*s,top+84*s],[cx-14*s,top+80*s]],"size":max(1.5,1.4*s+0.5),"color":rim})
    rims.append({"pts":[[cx+14*s,top+80*s],[cx+34*s,top+84*s],[cx+60*s,top+96*s],[cx+72*s,top+118*s],[cx+72*s,top+150*s]],"size":max(1.5,1.2*s+0.5),"color":rim})
    import math
    hp=[[cx+29*s*math.cos(a)*0.98,top+36*s-36*s*math.sin(a)] for a in [math.radians(d) for d in range(200,-21,-20)]]
    rims.append({"pts":hp,"size":max(1.5,1.4*s+0.5),"color":rim})
    if strut:
        x0=cx+random.uniform(-8,8)*s; x1=cx+random.uniform(-30,30)*s
        struts.append({"pts":[[x0,top+150*s],[x1,top+420*s]],"size":7*s,"color":"#5e4228"})
    return body,rims,struts
R=[]
row=[]
for x in [40,135,230,325,420, 800,895,990,1085,1180]:
    row.append(cut(x+random.uniform(-10,10),1218+random.uniform(-6,6),0.5,"#3a2616","#d8a458",arm=(1 if x in (135,895) else 0)))
row.append(cut(475,1226,0.5,"#3a2616","#d8a458",edge=True)); row.append(cut(752,1222,0.5,"#3a2616","#d8a458",edge=True))
R.append(row); row=[]
for x,arm in [(70,0),(225,1),(380,0),(840,0),(1000,-1),(1150,0)]:
    row.append(cut(x+random.uniform(-10,10),1300+random.uniform(-8,8),0.8,"#33231a","#d09850",arm=arm))
row.append(cut(520,1320,0.8,"#33231a","#d09850",edge=True)); R.append(row); row=[]
for x,arm in [(-20,0),(300,0),(920,1),(1210,0)]:
    row.append(cut(x,1420,1.35,"#241810","#b88040",arm=arm))
row.append(cut(640,1470,1.35,"#241810","#b88040",edge=True)); R.append(row)
which=int(sys.argv[1]); part=sys.argv[2]
idx={"body":0,"rim":1,"strut":2}[part]
S=[]
for c in R[which]: S+=c[idx]
for st in S: st["pts"]=[[round(a,1),round(b,1)] for a,b in st["pts"]]
brush={"body":"round","rim":"liner","strut":"round"}[part]
print(json.dumps({"type":"strokes","brush":brush,"strokes":S,"edge":"hard"}))
