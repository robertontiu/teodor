import sys; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from geo import H
ks=sys.argv[1].split(',')
def reg(k): c,sc,_=H[k]; r=105*sc; return {"type":"ellipse","cx":c[0],"cy":c[1],"rx":r,"ry":r}
act({"arousal":0.3,"tension":0.1,"valence":-0.5,"care":1.0},[
 {"type":"match","brush":"round","size":[4,9],"threshold":0.07,"faithful":1.0,"region":reg(k),"clip":True,"max_strokes":1800,"edge":"soft","wetmix":0.25} for k in ks])
