import json
exec(open('/home/claude/tools/walker.py').read().split('lead=')[0])
st=W(760,912,215,"#565a5e","#474b4f")
# replace straight rear leg (index of that stroke) with bent leg
cx,fy,h=760,912,215;k=h/210.0
P=lambda x,y:[round(cx+x*k,1),round(fy-(210-y)*k,1)]
S=lambda pts,w,c:{"pts":[P(*p) for p in pts],"size":w,"color":c}
st=[s for s in st if not (abs(s["pts"][0][0]-P(9,118)[0])<0.5 and abs(s["pts"][0][1]-P(9,118)[1])<0.5)]
st+= [S([(9,118),(12,140),(13,158)],8.5,"#565a5e"),S([(13,158),(17,175),(22,190)],7.5,"#52565a")]
spine=[S([(0,y),(0,y+4)],3.4,"#878b8f") for y in range(44,108,7)]
spine+=[S([(0,y+4.5),(0,y+6)],2.0,"#3a3e42") for y in range(44,104,7)]
det=[S([(-17,50),(-6,52),(-8,68)],2.0,"#777b80"),S([(17,50),(6,52),(8,68)],2.0,"#777b80"),
     S([(-26,43),(26,43)],2.2,"#8f9398"),S([(-4,4),(3,3),(6,9)],2.0,"#8c9095"),
     S([(19,191),(25,196)],5,"#97989a"),S([(19,193),(24,197)],2,"#cfcac0")]
# cast shadow toward us, running from feet over the outer ground to the sill
shadow=[{"pts":[[752,915],[742,950],[730,990],[722,1002]],"size":9,"color":"#8a7a62"},
        {"pts":[[778,908],[772,940],[760,975]],"size":6,"color":"#948670"}]
act={"felt":{"arousal":0.15,"tension":0.15,"valence":0.1,"care":0.98},"do":[
 {"type":"strokes","brush":"round","impasto":0.3,"load":1.5,"cover":1.0,"wetmix":0.05,"pickup":0.0,"edge":"hard","strokes":st},
 {"type":"strokes","brush":"liner","impasto":0.25,"strokes":spine+det},
 {"type":"strokes","brush":"round","impasto":0.05,"load":1.0,"cover":0.6,"edge":"soft","strokes":shadow}]}
print(json.dumps(act))
