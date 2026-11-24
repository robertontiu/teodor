import sys, math, random
sys.path.insert(0,'/home/claude/v13/tools'); sys.path.insert(0,'/home/claude/v13/tools/p3')
from fig import F, ang_from, ellpts, fill_lines
SUN=(552,458)
def figure(c, sc, skin, hair, coat, seed, sky_pad=1.2, old=None, angle=None, hairstyle='short', rimc='#f4f2ea'):
    rnd=random.Random(seed)
    ang=angle if angle is not None else ang_from(SUN,c)
    G=F(c[0],c[1],ang,sc)
    eps={}
    # 0 sky over the old head (radial white strokes from the sun)
    sky=[]
    if old:
        ox,oy,rx,ry=old
        for k in range(110):
            t=rnd.uniform(0,2*math.pi); r=math.sqrt(rnd.random())
            x=ox+rx*sky_pad*r*math.cos(t); y=oy+ry*sky_pad*r*math.sin(t)
            a=math.atan2(y-SUN[1],x-SUN[0]); L=rnd.uniform(30,80)
            sky.append({"pts":[[round(x-math.cos(a)*L/2),round(y-math.sin(a)*L/2)],[round(x+math.cos(a)*L/2),round(y+math.sin(a)*L/2)]],
                        "size":round(rnd.uniform(14,26),1),"color":rnd.choice(["#fbfbf3","#f5f6ec","#ffffff","#eef0e6"])})
    eps['sky']=sky
    # 1 body: shoulders and coat going out to the frame
    body=[(-46,95),(46,95),(140,135),(250,215),(330,520),(-330,520),(-250,215),(-140,135)]
    cc=lambda x,y,r: r.choice(coat)
    eps['body']=fill_lines(G,body,9,(14,24),cc,rnd,angle_local=90,wob=4)
    # 2 neck in shadow
    neck=[(-30,40),(30,40),(36,120),(-36,120)]
    eps['neck']=fill_lines(G,neck,6,(9,13),[skin[2],skin[3]],rnd,angle_local=90)
    # 3 face mass: skull ellipse, colour from bounce logic: brightest toward chin/lower planes? use by y
    skull=[(58*math.cos(t*2*math.pi/36),72*math.sin(t*2*math.pi/36)) for t in range(36)]
    def skinc(x,y,r):
        # cheek/brow planes facing down get bounce; sides fall to shadow
        side=abs(x)/58
        if side>0.72: return r.choice([skin[2],skin[3]])
        if -30<y<-8 and abs(x)>8: return skin[3]          # eye sockets zone darker
        return r.choice([skin[0],skin[1],skin[1]])
    eps['face']=fill_lines(G,skull,5,(7,11),skinc,rnd,angle_local=0)
    # 4 hair at the crown, larger than skull, toward the sun
    hairpoly=[(66*math.cos(t),82*math.sin(t)) for t in [math.pi+i*math.pi/18 for i in range(19)]]
    hairpoly=[(x, min(y,-18+abs(x)*0.25)) for x,y in hairpoly]+[(50,-30),(20,-44),(-20,-44),(-50,-30)]
    if hairstyle=='long':
        hairpoly=[(-70,40),(-72,-10)]+[(70*math.cos(t),86*math.sin(t)) for t in [math.pi+i*math.pi/18 for i in range(19)]]+[(72,-10),(70,40),(52,20),(48,-30),(20,-44),(-20,-44),(-48,-30),(-52,20)]
    eps['hair']=fill_lines(G,hairpoly,5,(7,12),lambda x,y,r:r.choice(hair),rnd,angle_local=90,wob=3)
    # 5 features: soft masses, no dots
    f=[]
    for sx in (-1,1):
        f.append({"pts":[G(sx*32,-16),G(sx*20,-19),G(sx*9,-16)],"size":round(15*sc,1),"color":skin[2]})      # socket mass
        f.append({"pts":[G(sx*30,8),G(sx*36,22)],"size":round(8*sc,1),"color":skin[0]})                       # cheekbone plane
    f.append({"pts":[G(0,-14),G(0,8)],"size":round(7*sc,1),"color":skin[0]})            # nose bridge
    f.append({"pts":[G(-8,15),G(8,15)],"size":round(6*sc,1),"color":skin[3]})           # under-nose shadow
    f.append({"pts":[G(-14,37),G(0,38),G(14,37)],"size":round(6*sc,1),"color":skin[2]})  # mouth, soft
    f.append({"pts":[G(-18,62),G(0,66),G(18,62)],"size":round(7*sc,1),"color":skin[0]})  # chin plane
    eps['feat']=f
    # 6 halation: crown dissolves into the glare, rim along the hair sides
    hal=[]
    for k in range(26):
        t=math.pi*1.5+rnd.uniform(-0.9,0.9)    # around crown (local -y)
        x0,y0=66*math.cos(t),82*math.sin(t)
        hal.append({"pts":[G(x0*1.5,y0*1.5),G(x0*0.95,y0*0.95),G(x0*0.78,y0*0.78)],"size":round(rnd.uniform(8,16),1),
                    "color":rnd.choice(["#ffffff","#fbfbf2","#f4f3ea"])})
    rim=[]
    for sx in (-1,1):
        pts=[G(sx*66*math.cos(t),82*math.sin(t)) for t in [math.pi*1.5+sx*0.0+u for u in [i*0.12*sx for i in range(2,12)]]]
        rim.append({"pts":pts,"size":round(3*sc,1),"color":rimc})
        # shoulder rim
        rim.append({"pts":[G(sx*50,98),G(sx*140,137),G(sx*248,215)],"size":round(3*sc,1),"color":rimc})
    eps['hal']=hal; eps['rim']=rim
    return eps, G
