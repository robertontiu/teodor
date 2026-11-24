import sys,random; sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from run import act; from paint2 import poly_mask; from hatch import hatch_mask
from scipy.ndimage import binary_erosion
from fingers import finger
rnd=random.Random(76)
hand=[(332,1338),(420,1322),(445,1335),(470,1365),(492,1412),(562,1498),(556,1518),(538,1522),(534,1550),(516,1556),(456,1474),(420,1495),(390,1490),(346,1420)]
m=binary_erosion(poly_mask(hand),iterations=5)
base=hatch_mask(m,57,6,(9,12),['#6a4032','#643a2e','#704436'],seglen=(40,90),seed=1,wobble=1,step=3)
S=[];C=[];R=[]
for b,t,w in [((462,1442),(530,1550),24),((484,1420),(558,1510),23)]:
    s,c,r=finger(b,t,w,'#7a4a3a','#a87460','#3a2220','#8a5a48','#4a2a22','#f4ece0'); S+=s;C+=c;R+=r
planes=[{"pts":[[350,1360],[400,1345],[440,1350]],"size":22,"color":"#946450"},     # lit back of hand toward the sky
        {"pts":[[445,1340],[480,1345],[505,1360]],"size":15,"color":"#9a6a54"},     # thumb top
        {"pts":[[360,1440],[395,1475],[430,1480]],"size":20,"color":"#3e2420"},     # shadow side / curled fingers underside
        {"pts":[[400,1468],[420,1474],[440,1470]],"size":9,"color":"#8a5a46"},      # knuckle catch of the curled fingers
        {"pts":[[488,1455],[525,1505]],"size":4,"color":"#1e1210"}]                 # gap between the two fingers
R.append({"pts":[[420,1322],[450,1334],[478,1350],[505,1362]],"size":1.6,"color":"#f4ece0"})
act({"arousal":0.2,"tension":0.15,"valence":0.0,"care":1.0},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":base,"wetmix":0.3},
 {"type":"strokes","brush":"round","edge":"soft","strokes":planes+S,"wetmix":0.45},
 {"type":"strokes","brush":"liner","strokes":C+R},
])
