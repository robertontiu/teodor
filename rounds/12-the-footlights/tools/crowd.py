import random
random.seed(11)
out=[]
def cut(cx,top,s,col,rim,arm=0,edge=False,strut=True,tilt=0):
    g=[]
    if edge:
        w=7*s
        g.append(f'<path d="M{cx-w},{top+20*s} Q{cx},{top-4*s} {cx+w},{top+20*s} L{cx+w+2},{top+400*s} L{cx-w-2},{top+400*s} Z" fill="{col}" stroke="{rim}" stroke-width="{1.6*s+0.6}"/>')
        return g
    # shoulders: straight cut cardboard edges
    P=[(-72,400),(-72,118),(-60,96),(-34,84),(-14,80),(-12,66),(12,66),(14,80),(34,84),(60,96),(72,118),(72,400)]
    d="M"+" L".join(f"{cx+x*s:.1f},{top+y*s:.1f}" for x,y in P)+" Z"
    g.append(f'<g transform="rotate({tilt} {cx} {top+200*s})">')
    g.append(f'<path d="{d}" fill="{col}" stroke="{rim}" stroke-width="{1.4*s+0.5}" stroke-linejoin="miter"/>')
    g.append(f'<ellipse cx="{cx}" cy="{top+36*s}" rx="{29*s}" ry="{36*s}" fill="{col}" stroke="{rim}" stroke-width="{1.4*s+0.5}"/>')
    g.append(f'<rect x="{cx-11*s}" y="{top+60*s}" width="{22*s}" height="{24*s}" fill="{col}"/>')
    if arm:
        sd=arm
        A=[(sd*50,100),(sd*72,98),(sd*84,20),(sd*74,16),(sd*52,82)]
        d="M"+" L".join(f"{cx+x*s:.1f},{top+y*s:.1f}" for x,y in A)+" Z"
        g.insert(1,f'<path d="{d}" fill="{col}" stroke="{rim}" stroke-width="{1.2*s+0.5}"/>')
        g.insert(2,f'<ellipse cx="{cx+sd*80*s}" cy="{top+2*s}" rx="{15*s}" ry="{20*s}" fill="{col}" stroke="{rim}" stroke-width="{1.2*s+0.5}"/>')
        g.insert(3,f'<ellipse cx="{cx+sd*92*s}" cy="{top+14*s}" rx="{5*s}" ry="{10*s}" transform="rotate({sd*30} {cx+sd*92*s} {top+14*s})" fill="{col}" stroke="{rim}" stroke-width="{1*s+0.4}"/>')
    if strut:
        g.append(f'<path d="M{cx+random.uniform(-8,8)*s},{top+150*s} L{cx+random.uniform(-30,30)*s},{top+420*s}" stroke="#5e4228" stroke-width="{7*s}" />')
        g.append(f'<rect x="{cx-16*s}" y="{top+140*s}" width="{32*s}" height="{14*s}" fill="#7a6648" opacity="0.6"/>')  # tape
    g.append('</g>')
    return g
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600">',
 '<defs><linearGradient id="fl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b07838"/><stop offset="0.6" stop-color="#7a4a22"/><stop offset="1" stop-color="#2a1a10"/></linearGradient>',
 '<linearGradient id="dk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e140e"/><stop offset="1" stop-color="#0e0a08"/></linearGradient></defs>',
 '<rect x="0" y="1300" width="1200" height="300" fill="url(#dk)"/>']
# far row (on the floor before the dais), aisle in the middle
for x in [40,135,230,325,420, 800,895,990,1085,1180]:
    svg+=cut(x+random.uniform(-10,10),1218+random.uniform(-6,6),0.5,"#3a2616","#d8a458",arm=(1 if x in (135,895) else 0),tilt=random.uniform(-3,3))
svg+=cut(475,1226,0.5,"#3a2616","#d8a458",edge=True)
svg+=cut(752,1222,0.5,"#3a2616","#d8a458",edge=True)
# mid row
for x,arm in [(70,0),(225,1),(380,0),(840,0),(1000,-1),(1150,0)]:
    svg+=cut(x+random.uniform(-10,10),1300+random.uniform(-8,8),0.8,"#24180f","#c89048",arm=arm,tilt=random.uniform(-4,4))
svg+=cut(520,1320,0.8,"#24180f","#c89048",edge=True)
# near row
for x,arm in [(-20,0),(300,0),(920,1),(1210,0)]:
    svg+=cut(x,1420,1.35,"#150e09","#a87038",arm=arm,tilt=random.uniform(-3,3))
svg+=cut(640,1470,1.35,"#150e09","#a87038",edge=True)
svg.append('</svg>')
open('/home/claude/v12/overlay_crowd17.svg','w').write("\n".join(svg))
