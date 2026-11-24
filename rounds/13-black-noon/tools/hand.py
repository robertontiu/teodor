import math
def hand(cx,cy,scale,rot,skin,shade,fingers_spread=1.0,sleeve=None,sleeve_from=None):
    out=[]
    if sleeve and sleeve_from:
        sx,sy=sleeve_from
        ang=math.atan2(cy-sy,cx-sx); nx,ny=-math.sin(ang),math.cos(ang)
        w0,w1=70*scale,48*scale
        px=cx-math.cos(ang)*70*scale; py=cy-math.sin(ang)*70*scale
        pts=[(sx+nx*w0,sy+ny*w0),(px+nx*w1,py+ny*w1),(px-nx*w1,py-ny*w1),(sx-nx*w0,sy-ny*w0)]
        out.append('<polygon points="%s" fill="%s"/>'%(" ".join("%.0f,%.0f"%p for p in pts),sleeve))
        # wrist
        out.append('<ellipse cx="%.0f" cy="%.0f" rx="%.0f" ry="%.0f" fill="%s" transform="rotate(%.0f %.0f %.0f)"/>'%(px+(cx-px)*0.5,py+(cy-py)*0.5,55*scale,34*scale,skin,math.degrees(ang),px+(cx-px)*0.5,py+(cy-py)*0.5))
    g=['<g transform="translate(%.0f %.0f) rotate(%.0f) scale(%.2f)">'%(cx,cy,rot,scale)]
    # palm
    g.append('<path d="M-60,-20 C-70,40 -40,85 0,90 C45,88 72,45 62,-25 C40,-50 -40,-50 -60,-20 Z" fill="%s"/>'%skin)
    g.append('<path d="M-30,10 C-10,30 15,32 35,15" stroke="%s" stroke-width="6" fill="none" opacity="0.6"/>'%shade)
    # fingers (radiating downward = toward viewer)
    for i,(a,L,w) in enumerate([(-38,95,22),(-14,118,23),(8,122,22),(30,104,20)]):
        a=a*fingers_spread
        x0=-45+i*30; y0=70
        x1=x0+math.sin(math.radians(a))*L; y1=y0+math.cos(math.radians(a))*L
        g.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="%d" stroke-linecap="round"/>'%(x0,y0,x1,y1,skin,w*2))
        g.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="5" stroke-linecap="round" opacity="0.5"/>'%(x0+(x1-x0)*0.45,y0+(y1-y0)*0.45,x0+(x1-x0)*0.5,y0+(y1-y0)*0.5,shade))
    # thumb
    g.append('<path d="M-55,0 C-110,20 -130,60 -125,85" stroke="%s" stroke-width="40" stroke-linecap="round" fill="none"/>'%skin)
    g.append('</g>')
    return out+g
