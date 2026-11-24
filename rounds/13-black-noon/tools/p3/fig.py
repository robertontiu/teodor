import math, random
def F(cx,cy,ang,sc):
    """local frame: x across the face, y from crown(-) to chin(+), y axis points along ang (radians, outward)."""
    uy=(math.cos(ang),math.sin(ang)); ux=(-uy[1],uy[0])
    return lambda x,y:[round(cx+sc*(x*ux[0]+y*uy[0])),round(cy+sc*(x*ux[1]+y*uy[1]))]
def ang_from(sun,c): return math.atan2(c[1]-sun[1],c[0]-sun[0])
def ellpts(G,cx,cy,rx,ry,n=40): return [G(cx+rx*math.cos(t*2*math.pi/n),cy+ry*math.sin(t*2*math.pi/n)) for t in range(n)]
def fill_lines(G,poly_local,step,size,cols,rnd,angle_local=90,wob=2):
    """fill a local polygon with strokes along angle_local (deg, in local frame) using scanlines"""
    from matplotlib.path import Path
    P=Path(poly_local); xs=[p[0] for p in poly_local]; ys=[p[1] for p in poly_local]
    a=math.radians(angle_local); d=(math.cos(a),math.sin(a)); n=(-d[1],d[0])
    cx,cy=sum(xs)/len(xs),sum(ys)/len(ys); R=max(max(xs)-min(xs),max(ys)-min(ys))
    out=[]; t=-R
    while t<R:
        run=[]; s=-R
        while s<=R:
            x=cx+n[0]*t+d[0]*s; y=cy+n[1]*t+d[1]*s
            if P.contains_point((x,y)): run.append((x,y))
            elif run: break
            s+=3
        if len(run)>=2:
            # split into 1-3 pieces
            k=rnd.choice([1,1,2]); L=len(run)
            for j in range(k):
                seg=run[j*L//k:(j+1)*L//k+1]
                if len(seg)<2: continue
                pts=[G(seg[0][0]+rnd.uniform(-wob,wob),seg[0][1]),G(seg[len(seg)//2][0]+rnd.uniform(-wob,wob),seg[len(seg)//2][1]),G(seg[-1][0],seg[-1][1])]
                c=cols(seg[len(seg)//2][0],seg[len(seg)//2][1],rnd) if callable(cols) else rnd.choice(cols)
                out.append({"pts":pts,"size":round(rnd.uniform(*size),1),"color":c})
        t+=step*rnd.uniform(0.8,1.2)
    rnd.shuffle(out); return out
