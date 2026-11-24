import json, sys
def W(cx, fy, h, c, cdark, s=1.0, glance=True):
    # back-view walker in stride; cx center x, fy foot y (planted), h total height
    k=h/210.0
    P=lambda x,y:[round(cx+x*k,1),round(fy-(210-y)*k,1)]  # y measured from top 0..210
    st=[]
    L=lambda pts,w,col=c: st.append({"pts":[P(*p) for p in pts],"size":max(1.5,w*k),"color":col})
    # head (egg) slightly turned to left
    for dx in (-5,-1,3): L([(dx,6),(dx-1,14),(dx-1,26)],9)
    L([(0,27),(0,40)],4)                  # neck
    # back shell: tapered, strokes downward
    for dx in (-24,-16,-8,0,8,16,24):
        L([(dx,42),(dx*0.7,62),(dx*0.35,92)],10,cdark if abs(dx)<10 else c)
    L([(-27,44),(27,44)],9)              # shoulder bar
    L([(0,92),(0,110)],6)                 # narrow spine waist
    L([(-14,112),(14,112)],14)            # pelvis
    # planted left leg (viewer left), straight
    L([(-9,118),(-10,152),(-11,186),(-11,206)],8)
    L([(-15,207),(-6,208)],5)
    # rear right leg, pushing off: knee lower/closer, heel raised
    L([(9,118),(12,154),(15,172),(16,192)],8)
    # far-swing left arm (forward, foreshortened, partly hidden)
    L([(-29,47),(-31,72),(-27,92)],6)
    # near-swing right arm (back toward us, longer, outward)
    L([(29,47),(36,76),(41,104)],6)
    L([(41,104),(42,112)],5)
    return st
def rims(cx,fy,h,col):
    k=h/210.0
    P=lambda x,y:[round(cx+x*k,1),round(fy-(210-y)*k,1)]
    out=[]
    R=lambda pts,w: out.append({"pts":[P(*p) for p in pts],"size":w,"color":col})
    R([(-8,4),(-11,14),(-10,26)],2.2)   # head left (toward the man's lamp side but here sky light)
    R([(-2,1),(5,3),(9,12),(8,25)],2.2)
    R([(-33,44),(-34,70),(-30,92)],2.0)
    R([(33,44),(40,74),(45,104)],2.0)
    R([(-16,112),(-15,150),(-16,186)],1.8)
    R([(18,116),(18,150),(20,190)],1.8)
    return out
lead=W(760,912,215,"#5c6064","#4b4f53")
f1=W(628,893,118,"#9a9890","#8e8c85")
f2=W(838,886,72,"#c2bdb0","#bdb7a9")
act={"felt":{"arousal":0.15,"tension":0.15,"valence":0.1,"care":0.98},"do":[
 {"type":"strokes","brush":"round","impasto":0.2,"load":1.4,"cover":1.0,"wetmix":0.1,"pickup":0.05,"edge":"hard","strokes":f2+f1},
 {"type":"strokes","brush":"round","impasto":0.3,"load":1.5,"cover":1.0,"wetmix":0.1,"pickup":0.05,"edge":"hard","strokes":lead},
 {"type":"strokes","brush":"liner","impasto":0.2,"strokes":rims(760,912,215,"#fbf4e2")}]}
print(json.dumps(act))
