import math
SUN=(552,458)
H={'tl':((330,262),1.3,None),'top':((872,118),1.2,None),'r':((1000,385),1.3,None),
   'bm':((448,800),1.45,math.radians(100)),'rw':((735,875),1.5,math.radians(82)),'rl':((912,676),1.25,None)}
def G(k):
    c,sc,ang=H[k]
    if ang is None: ang=math.atan2(c[1]-SUN[1],c[0]-SUN[0])
    uy=(math.cos(ang),math.sin(ang)); ux=(-uy[1],uy[0])
    return lambda X,Y:[round(c[0]+sc*(X*60*ux[0]+Y*76*uy[0])),round(c[1]+sc*(X*60*ux[1]+Y*76*uy[1]))]
