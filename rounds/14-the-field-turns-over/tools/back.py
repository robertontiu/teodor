import json
cx,fy,h=760,912,215
k=h/210.0
P=lambda x,y:[round(cx+x*k,1),round(fy-(210-y)*k,1)]
S=lambda pts,w,c:{"pts":[P(*p) for p in pts],"size":w,"color":c}
sky="#f3ebd9"
fix=[S([(8,150),(8,175)],7,sky),S([(16,190),(17,205)],6,"#c7b89b"),   # clear old rear shin
     S([(9,118),(12,140),(13,158)],8.5,"#5c6064"),S([(13,158),(17,175),(22,190)],7.5,"#585c60")]
spine=[S([(0,y),(0,y+4)],3.4,"#868a8e") for y in range(44,108,7)]
spine+= [S([(0,y+4.5),(0,y+6)],2.0,"#3e4246") for y in range(44,104,7)]
blades=[S([(-17,50),(-6,52),(-8,68)],2.0,"#7a7e83"),S([(17,50),(6,52),(8,68)],2.0,"#7a7e83"),
        S([(-26,43),(26,43)],2.2,"#8f9398"),S([(-4,4),(3,3),(6,9)],2.0,"#8c9095")]
sole=[S([(19,191),(25,196)],5,"#9a9b98"),S([(19,193),(24,197)],2,"#c9c7bf"),S([(-16,207),(-5,208)],4,"#45484b")]
act={"felt":{"arousal":0.15,"tension":0.15,"valence":0.1,"care":0.98},"do":[
 {"type":"strokes","brush":"round","impasto":0.1,"load":1.5,"cover":1.0,"wetmix":0.05,"pickup":0.0,"edge":"hard","strokes":fix},
 {"type":"strokes","brush":"liner","impasto":0.25,"strokes":spine+blades+sole}]}
print(json.dumps(act))
