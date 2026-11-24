import sys,random,math; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
from paint2 import radial, poly_mask, field, hexc
from hatch import hatch_mask
from scipy.ndimage import binary_erosion
SUN=(552,458); rnd=random.Random(61)
def er(m,k): return binary_erosion(m,iterations=k)
white=lambda x,y,r: r.choice(["#fbfbf3","#f5f6ec","#ffffff","#eef0e6","#f8f6ea"])
sky=[]
for poly in [[(690,0),(800,0),(790,30),(760,50),(700,40)],
             [(700,370),(770,345),(800,470),(830,520),(770,545),(700,500)],
             [(160,330),(240,345),(300,385),(270,420),(190,400)]]:
    sky+=radial(er(poly_mask(poly),5),SUN,60,(25,70),(10,18),white,seed=len(sky))
def body(poly,cols,seed,size=(12,20)):
    m=er(poly_mask(poly),6)
    def ang(x,y): return math.atan2(y-SUN[1],x-SUN[0])
    return field(m,ang,260,(40,120),size,lambda x,y,r:r.choice(cols),seed=seed,step=6)
topb=body([(915,70),(960,40),(985,0),(1200,0),(1200,215),(1150,190),(1080,140),(1010,100),(960,85)],['#1e1c1c','#2a2726','#34302e','#24201f'],1)
blb=body([(1088,330),(1110,300),(1200,240),(1200,560),(1120,500),(1098,450)],['#1a2e78','#22409a','#14245c','#1c3488'],2)
necks=[]
for poly,cols in [([(905,62),(950,30),(978,45),(942,88)],['#2a1a12','#22150f']),
                  ([(1092,345),(1128,335),(1135,410),(1098,420)],['#4a3030','#3e2828']),
                  ([(232,228),(272,188),(222,128),(178,168)],['#2a201e','#241a18'])]:
    m=er(poly_mask(poly),3)
    necks+=hatch_mask(m,0,5,(6,9),cols,seglen=(20,50),seed=3,wobble=1,step=3)
act({"arousal":0.45,"tension":0.2,"valence":-0.4,"care":0.85},[
 {"type":"strokes","brush":"flat","edge":"soft","strokes":sky},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":topb+blb,"wetmix":0.3},
 {"type":"strokes","brush":"flat","edge":"soft","strokes":necks,"wetmix":0.3},
])
