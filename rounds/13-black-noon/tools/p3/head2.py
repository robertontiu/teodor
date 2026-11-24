import sys, math, random
sys.path.insert(0,'/home/claude/v13/tools/p3')
from fig import F, ang_from, fill_lines
SUN=(552,458)
def head2(c, sc, base, lights, hair, seed, rimc='#f6f2e6', angle=None, hair_extent=-40, lightmul=1.0):
    rnd=random.Random(seed); ang=angle if angle is not None else ang_from(SUN,c); G=F(c[0],c[1],ang,sc)
    skull=[(60*math.cos(t*2*math.pi/40),76*math.sin(t*2*math.pi/40)) for t in range(40)]
    E={}
    E['base']=fill_lines(G,skull,5,(8,12),lambda x,y,r:r.choice(base),rnd,angle_local=0,wob=1)
    hp=[(64*math.cos(t),80*math.sin(t)) for t in [math.pi+i*math.pi/20 for i in range(21)]]
    hp=[(x,min(y,hair_extent+abs(x)**2/120)) for x,y in hp]
    E['hair']=fill_lines(G,hp,4,(7,11),lambda x,y,r:r.choice(hair),rnd,angle_local=90,wob=2)
    L=lights; l=[]
    # forehead plane (between hairline and brows)
    l.append({"pts":[G(-26,-34),G(0,-37),G(26,-34)],"size":round(10*sc,1),"color":L[1]})
    # brow ridges over the sockets
    for sx in (-1,1):
        l.append({"pts":[G(sx*36,-27),G(sx*22,-28),G(sx*10,-26)],"size":round(5*sc,1),"color":L[0]})
        # cheekbone
        l.append({"pts":[G(sx*38,0),G(sx*30,12),G(sx*24,18)],"size":round(9*sc,1),"color":L[1]})
        # lower lid/upper cheek small catch
        l.append({"pts":[G(sx*28,-6),G(sx*16,-5)],"size":round(3*sc,1),"color":L[1]})
    # nose bridge and tip
    l.append({"pts":[G(0,-20),G(0,-4),G(0,10)],"size":round(7*sc,1),"color":L[1]})
    l.append({"pts":[G(-3,10),G(3,11)],"size":round(8*sc,1),"color":L[0]})
    # upper lip ridge, lower lip, chin
    l.append({"pts":[G(-12,26),G(12,26)],"size":round(5*sc,1),"color":L[1]})
    l.append({"pts":[G(-11,42),G(0,44),G(11,42)],"size":round(5*sc,1),"color":L[1]})
    l.append({"pts":[G(-20,58),G(0,63),G(20,58)],"size":round(10*sc,1),"color":L[0]})
    E['lights']=l
    # rim along both sides of the crown silhouette
    rim=[]
    for sx in (-1,1):
        ts=[math.pi*1.5+sx*u for u in [0.35+i*0.09 for i in range(10)]]
        rim.append({"pts":[G(64*math.cos(t),80*math.sin(t)) for t in ts],"size":round(2.6*sc,1),"color":rimc})
    E['rim']=rim
    hal=[]
    for k in range(18):
        t=math.pi*1.5+rnd.uniform(-0.7,0.7); x0,y0=64*math.cos(t),80*math.sin(t)
        hal.append({"pts":[G(x0*1.45,y0*1.45),G(x0*1.02,y0*1.02),G(x0*0.86,y0*0.86)],"size":round(rnd.uniform(7,13),1),
                    "color":rnd.choice(["#ffffff","#fbfbf2","#f4f3ea"])})
    E['hal']=hal
    return E,G
