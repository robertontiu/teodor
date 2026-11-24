import sys,math,random; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
rnd=random.Random(84)
arm=[{"pts":[[858,960],[838,995],[818,1035]],"size":2.4,"color":"#ffd8c0"},{"pts":[[806,1060],[790,1100],[778,1140]],"size":2.0,"color":"#ffc8a8"}]
lip=[{"pts":[[736,953],[746,955],[756,952]],"size":3,"color":"#c09080"}]
hair=[]
for a0,a1 in [(-160,-128),(-118,-92),(-84,-60),(-50,-22)]:
    pts=[[round(737+102*math.cos(math.radians(a))),round(882+98*math.sin(math.radians(a)))] for a in range(a0,a1+1,6)]
    hair.append({"pts":pts,"size":1.8,"color":"#fff6e6"})
sun=[]
for a0 in range(0,360,50):
    pts=[[round(552+93*math.cos(math.radians(a))),round(458+93*math.sin(math.radians(a)))] for a in range(a0,a0+38,6)]
    sun.append({"pts":pts,"size":2.6,"color":"#ffffff"})
collar=[{"pts":[[655,965],[685,970],[715,975]],"size":14,"color":"#8a1410"},{"pts":[[660,955],[700,960]],"size":10,"color":"#7a1210"}]
act({"arousal":0.3,"tension":0.15,"valence":-0.3,"care":1.0},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":collar,"wetmix":0.3},
 {"type":"strokes","brush":"round","edge":"soft","strokes":lip,"wetmix":0.4},
 {"type":"strokes","brush":"liner","strokes":arm+hair+sun},
])
