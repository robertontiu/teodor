import math
def seg(x0,y0,a,L,w,col,op=1):
    x1=x0+math.sin(math.radians(a))*L; y1=y0+math.cos(math.radians(a))*L
    return x1,y1,'<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-linecap="round" opacity="%.2f"/>'%(x0,y0,x1,y1,col,w,op)
def hand(cx,cy,s,rot,skin,shade,light,curl=0.0,spread=1.0):
    """palm seen from below, fingers pointing down-ish (toward viewer). curl 0..1 bends fingers inward (grasp)."""
    g=['<g transform="translate(%.0f %.0f) rotate(%.0f) scale(%.2f)">'%(cx,cy,rot,s)]
    g.append('<path d="M-58,-40 C-66,10 -55,60 -30,78 L40,80 C60,55 66,10 56,-42 C30,-60 -30,-60 -58,-40 Z" fill="%s"/>'%skin)
    g.append('<path d="M-50,-30 C-56,20 -45,55 -25,72" stroke="%s" stroke-width="14" fill="none" opacity="0.45"/>'%shade)
    g.append('<path d="M50,-30 C56,20 50,50 38,70" stroke="%s" stroke-width="8" fill="none" opacity="0.5"/>'%light)
    fingers=[(-32,(-12,),(46,38,30),(22,19,16)),(-10,(-4,),(54,42,32),(23,20,17)),(12,(4,),(52,40,31),(22,19,16)),(33,(12,),(42,32,26),(19,16,14))]
    for x0,(a0,),Ls,Ws in fingers:
        a=a0*spread; x,y=x0,74
        for k,(L,W) in enumerate(zip(Ls,Ws)):
            col=skin if k<2 else shade
            x,y,ln=seg(x,y,a,L,W,skin); g.append(ln)
            a += -a0*0.2 + (curl*38 if x0<0 else -curl*38)*0  # keep
            a += curl*35*(1 if k==0 else 1.2)*(-1 if a0<0 else 1)*-1
        g.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="0.6"/>'%(x,y,Ws[2]*0.35,light))
    # thumb
    x,y=-56,0; a=-60
    for L,W in ((40,30),(34,24),(28,19)):
        x,y,ln=seg(x,y,a,L,W,skin); g.append(ln); a+=25+curl*20
    g.append('</g>')
    return g
def limb(pts,w0,w1,col):
    # tapered polygon along polyline
    out=[];n=len(pts)
    L=[];R=[]
    for i,(x,y) in enumerate(pts):
        j=min(i+1,n-1);k=max(i-1,0)
        dx,dy=pts[j][0]-pts[k][0],pts[j][1]-pts[k][1];d=math.hypot(dx,dy) or 1
        nx,ny=-dy/d,dx/d; w=w0+(w1-w0)*i/(n-1)
        L.append((x+nx*w,y+ny*w));R.append((x-nx*w,y-ny*w))
    P=L+R[::-1]
    return ['<polygon points="%s" fill="%s"/>'%(" ".join("%.0f,%.0f"%p for p in P),col)]
