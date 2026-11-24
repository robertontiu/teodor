import math
def T(cx,cy,rot,sc):
    a=math.radians(rot)
    return lambda x,y: [round(cx+sc*(x*math.cos(a)-y*math.sin(a))), round(cy+sc*(x*math.sin(a)+y*math.cos(a)))]
def features(cx,cy,rot,sc,mouth=False,k=1.0,bounce='#d08a58'):
    G=T(cx,cy,rot,sc); s=[]
    for sx in (-1,1):
        s.append({'pts':[G(sx*30,-22),G(sx*21,-24),G(sx*11,-21)],'size':round(13*sc*k,1),'color':'#2a1812'})   # socket shadow
        s.append({'pts':[G(sx*34,-12),G(sx*20,-15),G(sx*8,-12)],'size':round(3.5*sc,1),'color':bounce})         # lit brow underside
        s.append({'pts':[G(sx*10,15),G(sx*6,16)],'size':round(5*sc,1),'color':'#120806'})                      # nostril
    s.append({'pts':[G(-13,8),G(0,6),G(13,8)],'size':round(4*sc,1),'color':bounce})                            # nose underside
    if mouth:
        s.append({'pts':[G(-10,40),G(0,42),G(10,40)],'size':round(12*sc,1),'color':'#1a0806'})
        s.append({'pts':[G(-12,47),G(0,50),G(12,47)],'size':round(3*sc,1),'color':bounce})
    else:
        s.append({'pts':[G(-13,40),G(0,42),G(13,40)],'size':round(3.5*sc,1),'color':'#2a140e'})
    return s
