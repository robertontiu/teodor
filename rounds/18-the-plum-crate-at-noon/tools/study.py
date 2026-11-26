# Colour studies of T9 (refined): same drawing, three palettes. Drawing in a 1200x1600 viewBox.
import subprocess, math, random, sys
def crates(P):
    random.seed(4)
    out=[]
    # crate wall: rows of crates tilted, seen from above-front, upper-left, stepping down to the right
    rows=[(0,-20,5),(1,250,4),(2,520,3)]
    fruit_cycle=P["fruits"]
    k=0
    for r,y0,n in rows:
        for i in range(n):
            x=-40+i*190 + r*-10
            y=y0 + i*28
            if x>820-r*140: continue
            fc=fruit_cycle[k%len(fruit_cycle)]; k+=1
            out.append(f'<g transform="rotate(-8 {x} {y})"><rect x="{x}" y="{y}" width="180" height="230" fill="{P["crate"]}" stroke="{P["key"]}" stroke-width="5"/>'
                       f'<rect x="{x+12}" y="{y+12}" width="156" height="150" fill="{P["crate_in"]}" stroke="{P["key"]}" stroke-width="3"/>')
            for a in range(4):
                for b in range(3):
                    cx=x+32+a*39+random.uniform(-4,4); cy=y+40+b*44+random.uniform(-4,4)
                    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{random.uniform(17,21):.0f}" fill="{fc}" stroke="{P["key"]}" stroke-width="2.5"/>')
            out.append(f'<path d="M{x+10},{y+190} H{x+170} M{x+10},{y+210} H{x+170}" stroke="{P["key"]}" stroke-width="3"/></g>')
    return "".join(out)
def cobbles(P):
    random.seed(9); out=[]
    for r in range(-6,40):
        for c in range(-2,16):
            x=c*92+(r%2)*46 - r*14; y=r*58 + c*10
            out.append(f'<rect x="{x}" y="{y}" width="80" height="48" rx="16" fill="{P["cobble"]}" stroke="{P["cob_line"]}" stroke-width="3"/>')
    return "".join(out)
def figure(P):
    k=P["key"]
    s=[]
    # stool (an upended crate) under him
    s.append(f'<polygon points="520,860 760,830 800,1020 560,1060" fill="{P["stool"]}" stroke="{k}" stroke-width="6"/>')
    # legs: trousers, long diagonal, crossed at the ankles
    s.append(f'<path d="M650,930 Q760,960 860,1120 L980,1360 L930,1390 L800,1180 Q720,1060 610,1020Z" fill="{P["trousers"]}" stroke="{k}" stroke-width="7"/>')
    s.append(f'<path d="M700,1000 Q820,1040 900,1170 L1040,1350 L990,1390 L840,1220 Q760,1120 660,1080Z" fill="{P["trousers"]}" stroke="{k}" stroke-width="7"/>')
    s.append(f'<path d="M925,1380 Q960,1450 1010,1470 L1060,1440 L985,1355Z M985,1385 Q1040,1440 1100,1440 L1110,1400 L1040,1345Z" fill="{P["boots"]}" stroke="{k}" stroke-width="6"/>')
    # torso: shirt with apron, leaning back against the crates
    s.append(f'<path d="M330,700 Q450,640 600,700 Q700,780 720,900 Q700,1000 640,1030 L520,1010 Q420,920 360,840Z" fill="{P["shirt"]}" stroke="{k}" stroke-width="7"/>')
    s.append(f'<path d="M430,760 Q560,740 650,800 Q700,900 680,1000 L560,1010 Q470,900 430,760Z" fill="{P["apron"]}" stroke="{k}" stroke-width="6"/>')
    # shirt pattern (flat, ignores folds)
    for i in range(10):
        for j in range(8):
            x=340+i*40; y=700+j*45
            s.append(f'<path d="M{x},{y} l10,10 M{x+10},{y} l-10,10" stroke="{P["shirt_pat"]}" stroke-width="4" clip-path="url(#shirtclip)"/>')
    # arms folded loosely on the belly, hands around a half-peeled fruit
    s.append(f'<path d="M360,760 Q330,860 420,930 Q520,960 600,920 L610,880 Q520,905 450,880 Q410,830 420,770Z" fill="{P["shirt"]}" stroke="{k}" stroke-width="6"/>')
    s.append(f'<path d="M620,760 Q700,840 660,900 Q620,930 580,930 L570,895 Q620,880 630,850 Q620,800 590,770Z" fill="{P["shirt"]}" stroke="{k}" stroke-width="6"/>')
    s.append(f'<ellipse cx="575" cy="905" rx="46" ry="40" fill="{P["skin"]}" stroke="{k}" stroke-width="4"/>')
    s.append(f'<ellipse cx="640" cy="910" rx="40" ry="34" fill="{P["skin"]}" stroke="{k}" stroke-width="4"/>')
    s.append(f'<circle cx="610" cy="880" r="34" fill="{P["held"]}" stroke="{k}" stroke-width="4"/>')
    s.append(f'<path d="M640,890 q30,30 10,60 q-10,-20 -24,-30Z" fill="{P["peel_in"]}" stroke="{k}" stroke-width="3"/>')
    # neck and head tipped back, face turned up to the viewer
    s.append(f'<path d="M430,700 Q470,740 540,720 L530,670 L450,660Z" fill="{P["skin"]}" stroke="{k}" stroke-width="5"/>')
    s.append(f'<g transform="rotate(-24 470 560)">'
             f'<ellipse cx="470" cy="560" rx="112" ry="138" fill="{P["skin"]}" stroke="{k}" stroke-width="6"/>'
             f'<path d="M362,520 Q380,410 470,402 Q565,405 582,520 Q560,460 470,455 Q385,460 362,520Z" fill="{P["hair"]}" stroke="{k}" stroke-width="4"/>'
             # closed eyes: lids as soft downward arcs, smile lines at the corners
             f'<path d="M405,555 Q430,570 455,556" stroke="{k}" stroke-width="4" fill="none"/>'
             f'<path d="M490,556 Q515,570 540,555" stroke="{k}" stroke-width="4" fill="none"/>'
             f'<path d="M398,560 l-10,8 M547,560 l10,8" stroke="{k}" stroke-width="2" fill="none"/>'
             f'<path d="M470,575 Q462,610 470,620 Q480,624 488,618" stroke="{k}" stroke-width="3" fill="none"/>'
             f'<path d="M438,650 Q472,668 506,650" stroke="{k}" stroke-width="4" fill="none"/>'
             f'<ellipse cx="420" cy="612" rx="22" ry="14" fill="{P["cheek"]}"/><ellipse cx="525" cy="612" rx="22" ry="14" fill="{P["cheek"]}"/>'
             f'<path d="M355,560 q-14,10 -4,40 q8,6 14,-6" fill="{P["skin"]}" stroke="{k}" stroke-width="4"/>'
             f'</g>')
    return "".join(s)
def passers(P):
    k=P["key"]; s=[]
    # passer-by 1: legs cropped at the right edge, mid-stride, path bending round his boots
    s.append(f'<path d="M1110,330 L1080,640 L1120,650 L1160,360Z" fill="{P["p1"]}" stroke="{k}" stroke-width="6"/>')
    s.append(f'<path d="M1200,380 L1150,700 L1200,720Z" fill="{P["p1"]}" stroke="{k}" stroke-width="6"/>')
    s.append(f'<path d="M1080,640 L1040,690 L1110,700 L1125,650Z" fill="{P["shoe1"]}" stroke="{k}" stroke-width="5"/>')
    s.append(f'<path d="M1040,330 q-30,80 0,150 l60,-10 q-20,-70 0,-140Z" fill="{P["bag"]}" stroke="{k}" stroke-width="5"/>')
    # passer-by 2: one foot lifted, stepping over his boots, at the lower right
    s.append(f'<path d="M1150,1180 L1120,1400 L1170,1410 L1200,1200Z" fill="{P["p2"]}" stroke="{k}" stroke-width="6"/>')
    s.append(f'<path d="M1120,1400 L1070,1440 L1150,1455 L1170,1410Z" fill="{P["shoe2"]}" stroke="{k}" stroke-width="5"/>')
    s.append(f'<path d="M1200,1450 L1140,1600 L1200,1600Z" fill="{P["p2"]}" stroke="{k}" stroke-width="6"/>')
    return "".join(s)
def awning(P):
    k=P["key"]; s=[f'<clipPath id="aw"><polygon points="720,0 1200,0 1200,300"/></clipPath><g clip-path="url(#aw)">']
    for i in range(12):
        x=700+i*80
        s.append(f'<polygon points="{x},0 {x+40},0 {x+40+260},300 {x+260},300" fill="{P["awn"] if i%2==0 else P["awn2"]}"/>')
    s.append(f'</g><path d="M720,0 L1200,300" stroke="{k}" stroke-width="8"/>')
    # scallop edge
    for i in range(8):
        x=720+i*62; y=i*62*300/480
        s.append(f'<path d="M{x},{y} q20,40 62,39" fill="{P["awn"]}" stroke="{k}" stroke-width="4"/>')
    return "".join(s)
def svg(P):
    shirtclip='<clipPath id="shirtclip"><path d="M330,700 Q450,640 600,700 Q700,780 720,900 Q700,1000 640,1030 L520,1010 Q420,920 360,840Z"/></clipPath>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600"><defs>{shirtclip}'
            f'<linearGradient id="bk" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{P["bok"]}"/><stop offset="0.35" stop-color="{P["bok"]}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect width="1200" height="1600" fill="{P["paper"]}"/>{cobbles(P)}'
            f'<rect width="1200" height="1600" fill="url(#bk)"/>'
            f'<clipPath id="cw"><polygon points="0,0 820,0 690,560 470,800 0,930"/></clipPath><g clip-path="url(#cw)"><rect width="1200" height="1600" fill="{P["wall"]}"/>{crates(P)}</g>'
            f'{awning(P)}{passers(P)}{figure(P)}</svg>')
PAL={
 "A_warm_market": dict(paper="#efe7d4",cobble="#e4dccb",cob_line="#b9b1a2",bok="#7fa7c4",wall="#3a4f66",crate="#9a958a",crate_in="#3a4f66",
   fruits=["#dcb54a","#d86a3a","#d9849b","#6f7d4a","#dcb54a"],awn="#c8442e",awn2="#f3eee4",key="#22201e",stool="#c9a2a0",
   trousers="#3a4f66",boots="#22201e",shirt="#7fa7c4",shirt_pat="#f3eee4",apron="#1f4e79",skin="#f0d9bd",cheek="#e8a898",hair="#22201e",
   held="#d86a3a",peel_in="#f3eee4",p1="#6f7d4a",shoe1="#22201e",bag="#d9849b",p2="#9a958a",shoe2="#c8442e"),
 "B_aizuri_with_warm_heart": dict(paper="#efe7d4",cobble="#e8e0cf",cob_line="#a9b6c2",bok="#1f4e79",wall="#1f4e79",crate="#7fa7c4",crate_in="#3a4f66",
   fruits=["#7fa7c4","#3a4f66","#7fa7c4","#9a958a"],awn="#1f4e79",awn2="#f3eee4",key="#1b2433",stool="#9a958a",
   trousers="#3a4f66",boots="#1b2433",shirt="#f3eee4",shirt_pat="#7fa7c4",apron="#1f4e79",skin="#f0d6b8",cheek="#e39a8a",hair="#1b2433",
   held="#d86a3a",peel_in="#f3eee4",p1="#3a4f66",shoe1="#1b2433",bag="#7fa7c4",p2="#7fa7c4",shoe2="#1f4e79"),
 "C_green_pink_noon": dict(paper="#efe7d4",cobble="#e9e1cf",cob_line="#c2b6a0",bok="#dcb54a",wall="#6f7d4a",crate="#c9a2a0",crate_in="#6f7d4a",
   fruits=["#d9849b","#dcb54a","#8aa060","#d9849b","#c8442e"],awn="#d9849b",awn2="#f3eee4",key="#22201e",stool="#dcb54a",
   trousers="#6f7d4a",boots="#22201e",shirt="#f3eee4",shirt_pat="#d9849b",apron="#3a4f66",skin="#f0d9bd",cheek="#e39a8a",hair="#22201e",
   held="#dcb54a",peel_in="#f3eee4",p1="#3a4f66",shoe1="#22201e",bag="#dcb54a",p2="#c9a2a0",shoe2="#22201e"),
}
for name,P in PAL.items():
    open(f"study_{name}.svg","w").write(svg(P))
    subprocess.run(["rsvg-convert","-w","450","-h","600",f"study_{name}.svg","-o",f"study_{name}.png"],check=True)
