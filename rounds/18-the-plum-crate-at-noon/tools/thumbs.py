# Teodor's value thumbnails: 3 values, 120x160 each. Light = paper, M = middle, D = dark.
import subprocess, os
L, M, D = "#ebe5d6", "#9b9384", "#2e2b28"
OUT = os.path.dirname(os.path.abspath(__file__))
def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160"><rect width="120" height="160" fill="{L}"/>{body}</svg>'
T = {}
# T1 high view down onto a market sleeper: diagonal street, crate stack upper-left, sleeper's upturned face, legs of passers-by cropped at right
T[1] = ("High view, market sleeper, diagonal street", f'''
<polygon points="0,0 70,0 40,160 0,160" fill="{M}"/>
<polygon points="0,0 120,0 120,10 0,26" fill="{D}"/>
<rect x="6" y="34" width="40" height="40" fill="{M}" stroke="{D}"/>
<ellipse cx="52" cy="70" rx="9" ry="8" fill="{L}"/>
<path d="M44,78 Q58,86 66,104 L56,110 Q46,98 40,90Z" fill="{D}"/>
<path d="M60,104 L98,132 L94,138 L56,110Z" fill="{M}"/>
<rect x="96" y="14" width="8" height="40" fill="{D}"/><rect x="108" y="30" width="7" height="44" fill="{D}"/>
<rect x="104" y="112" width="8" height="30" fill="{D}"/>''')
# T2 worm's-eye: sleeper on a bench under a huge canopy
T[2] = ("Worm's-eye, bench under canopy", f'''
<path d="M0,0 H120 V70 Q80,90 60,60 Q30,90 0,70Z" fill="{D}"/>
<rect x="56" y="60" width="8" height="100" fill="{D}"/>
<rect x="10" y="118" width="100" height="8" fill="{M}"/>
<ellipse cx="34" cy="106" rx="7" ry="7" fill="{M}"/><path d="M38,110 L90,116 L90,122 L36,122Z" fill="{M}"/>''')
# T3 overhead: lying on a patterned blanket in grass
T[3] = ("Overhead, lying on a patterned blanket", f'''
<rect width="120" height="160" fill="{M}"/>
<polygon points="20,20 110,40 96,150 6,128" fill="{L}"/>
<g fill="{M}">{''.join(f'<circle cx="{20+ (i%6)*15}" cy="{36+(i//6)*18}" r="3"/>' for i in range(36))}</g>
<ellipse cx="62" cy="40" rx="10" ry="12" fill="{L}" stroke="{D}"/>
<path d="M50,52 Q64,48 76,54 L72,118 L54,118Z" fill="{D}"/>''')
# T4 hashira-e narrow crop: balcony, woman leaning on the rail, face to sun, laundry
T[4] = ("Narrow vertical crop, balcony rail, face to the sun", f'''
<rect x="0" y="0" width="120" height="50" fill="{L}"/>
<rect x="0" y="96" width="120" height="64" fill="{M}"/>
<path d="M0,96 H120" stroke="{D}" stroke-width="4"/>
<path d="M10,0 V40 M40,0 V30 M90,0 V46" stroke="{M}" stroke-width="10"/>
<ellipse cx="64" cy="62" rx="10" ry="11" fill="{M}"/>
<path d="M50,74 Q66,70 80,80 L84,96 L46,96Z" fill="{D}"/>''')
# T5 interior intimist: man asleep in an armchair, wallpaper merging
T[5] = ("Interior, armchair, figure merging with wallpaper", f'''
<g fill="{M}">{''.join(f'<rect x="{(i%8)*15}" y="{(i//8)*15}" width="7" height="7"/>' for i in range(80))}</g>
<path d="M20,70 Q60,50 100,70 V150 H20Z" fill="{D}"/>
<ellipse cx="62" cy="68" rx="10" ry="11" fill="{L}"/>
<rect x="34" y="90" width="50" height="36" fill="{L}"/>''')
# T6 ferry deck: crowd at a rail, one head on another's shoulder, horizon diagonal
T[6] = ("Ferry deck crowd, low horizon tilted", f'''
<polygon points="0,90 120,70 120,160 0,160" fill="{M}"/>
<g fill="{D}"><rect x="8" y="60" width="16" height="100"/><rect x="30" y="56" width="18" height="104"/><rect x="74" y="58" width="16" height="102"/><rect x="96" y="54" width="18" height="106"/></g>
<ellipse cx="60" cy="64" rx="9" ry="9" fill="{L}"/><rect x="52" y="72" width="16" height="88" fill="{D}"/>''')
# T7 big face crop: head on folded arm on a market table, fruit foreground
T[7] = ("Close crop, head on folded arm at the table", f'''
<rect x="0" y="100" width="120" height="60" fill="{M}"/>
<g fill="{L}" stroke="{D}">{''.join(f'<circle cx="{8+i*18}" cy="{128+(i%2)*12}" r="9"/>' for i in range(7))}</g>
<path d="M0,96 Q60,80 120,100 V112 H0Z" fill="{D}"/>
<ellipse cx="66" cy="70" rx="30" ry="26" fill="{L}" stroke="{D}"/>
<path d="M30,40 Q66,20 100,50 L96,60 Q66,40 36,56Z" fill="{D}"/>''')
# T8 bicycle courier asleep on a stoop, high crop, steps as stripes
T[8] = ("Steps as stripes, sleeper on a stoop, cut diagonal", f'''
<g fill="{M}">{''.join(f'<polygon points="0,{i*24} 120,{i*24-30} 120,{i*24-18} 0,{i*24+12}"/>' for i in range(9))}</g>
<ellipse cx="38" cy="58" rx="9" ry="9" fill="{L}" stroke="{D}"/>
<path d="M30,66 Q50,64 60,80 L84,120 L74,124 L46,92Z" fill="{D}"/>
<circle cx="96" cy="40" r="16" fill="none" stroke="{D}" stroke-width="4"/>''')
os.makedirs(f"{OUT}/thumbs", exist_ok=True)
for k,(name,body) in T.items():
    p=f"{OUT}/thumbs/t{k}.svg"; open(p,"w").write(svg(body))
    subprocess.run(["rsvg-convert","-w","240","-h","320",p,"-o",p.replace(".svg",".png")],check=True)
