import sys,math; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from geo import G, H
def face_region(k,pad=1.0):
    c,sc,_=H[k]; return {"type":"ellipse","cx":c[0],"cy":c[1],"rx":62*sc*pad,"ry":62*sc*pad}
mouth=[]
for i in range(9):
    t=i/8; 
    mouth.append({"pts":[[740-17+round(34*t),908],[740-19+round(38*t),928],[740-15+round(30*t),950]],"size":7,"color":"#160707"})
act({"arousal":0.35,"tension":0.3,"valence":-0.6,"care":0.95},[
 {"type":"glaze","color":"#2a1a1c","opacity":0.5,"region":face_region('bm'),"feather":18},
 {"type":"glaze","color":"#2c1818","opacity":0.45,"region":face_region('rw'),"feather":18},
 {"type":"glaze","color":"#24160f","opacity":0.45,"region":face_region('rl'),"feather":18},
 {"type":"strokes","brush":"round","edge":"soft","strokes":mouth,"wetmix":0.3},
])
