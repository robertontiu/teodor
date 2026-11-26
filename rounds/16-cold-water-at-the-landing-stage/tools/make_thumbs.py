import subprocess, os
from PIL import Image, ImageDraw
L,M,D='#ece8dc','#8c8c8c','#2e2e2e'
def svg(body): return f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160"><rect width="120" height="160" fill="{M}"/>{body}</svg>'
T={}
# A: high view from jetty, man lower-left face up, child in air upper right, jetty diagonal top-right
T['A']=svg(f'''<polygon points="70,0 120,0 120,60" fill="{D}"/>
<ellipse cx="45" cy="112" rx="34" ry="14" fill="{L}" opacity="0.9"/>
<ellipse cx="45" cy="104" rx="15" ry="20" fill="{L}"/><path d="M22,96 L33,82 L42,92 Z M68,96 L57,82 L48,92 Z" fill="{L}"/>
<ellipse cx="45" cy="98" rx="6" ry="3" fill="{D}"/>
<path d="M78,30 q8,-6 14,2 l6,14 -10,4 -8,-6 z" fill="{L}"/><path d="M84,50 l-4,10 M92,48 l6,10" stroke="{L}" stroke-width="4"/>''')
# B: extreme close head+hands, spray, child's feet at top
T['B']=svg(f'''<path d="M0,150 Q60,120 120,150 L120,160 L0,160Z" fill="{D}"/>
<circle cx="60" cy="95" r="30" fill="{L}"/><path d="M15,80 L35,55 L50,75 Z M105,80 L85,55 L70,75Z" fill="{L}"/>
<ellipse cx="60" cy="105" rx="10" ry="6" fill="{D}"/><path d="M5,125 L20,110 L30,128 L45,112 L60,130 L75,112 L92,128 L105,110 L118,126" stroke="{L}" stroke-width="5" fill="none"/>
<rect x="70" y="0" width="7" height="18" fill="{L}"/><rect x="82" y="0" width="7" height="14" fill="{L}"/>''')
# C: worm view from water, child against light sky (silhouette risk)
T['C']=svg(f'''<rect width="120" height="70" fill="{L}"/><rect y="55" width="120" height="12" fill="{D}"/>
<circle cx="62" cy="30" r="8" fill="{D}"/><path d="M50,40 L74,40 L80,55 L45,55Z" fill="{D}"/>
<circle cx="35" cy="130" r="16" fill="{L}"/><path d="M15,120 L25,100 L32,115Z" fill="{L}"/>''')
# D: side view jetty horizontal, child running off, man lower right
T['D']=svg(f'''<rect width="120" height="60" fill="{L}"/><rect y="70" width="70" height="10" fill="{D}"/><rect x="10" y="80" width="4" height="40" fill="{D}"/><rect x="55" y="80" width="4" height="40" fill="{D}"/>
<circle cx="72" cy="45" r="5" fill="{D}"/><path d="M68,50 l10,0 4,15 -16,2z" fill="{D}"/>
<circle cx="95" cy="125" r="8" fill="{L}"/><ellipse cx="95" cy="132" rx="16" ry="4" fill="{L}"/>''')
# E: directly overhead, two heads in water, rings, jetty edge left
T['E']=svg(f'''<rect width="22" height="160" fill="{D}"/>
<ellipse cx="70" cy="60" rx="30" ry="22" fill="none" stroke="{L}" stroke-width="3"/><circle cx="70" cy="60" r="9" fill="{L}"/>
<ellipse cx="60" cy="120" rx="22" ry="16" fill="none" stroke="{L}" stroke-width="2"/><circle cx="60" cy="120" r="6" fill="{L}"/>''')
# F: two heads facing each other, high view, splash between
T['F']=svg(f'''<polygon points="0,0 120,0 120,22 0,40" fill="{D}"/>
<circle cx="32" cy="100" r="16" fill="{L}"/><path d="M12,112 L30,118 L48,112 L46,128 L14,128Z" fill="{L}"/>
<circle cx="90" cy="82" r="10" fill="{L}"/>
<path d="M55,95 L60,70 L64,92 L70,74 L72,96" stroke="{L}" stroke-width="4" fill="none"/>''')
# G: man on ladder lowering into cold water, child in water splashing upward at him
T['G']=svg(f'''<rect width="120" height="48" fill="{D}"/><rect x="40" y="40" width="4" height="90" fill="{D}"/><rect x="66" y="40" width="4" height="90" fill="{D}"/>
<circle cx="56" cy="60" r="11" fill="{L}"/><path d="M38,70 L74,70 L70,110 L42,110Z" fill="{L}"/>
<circle cx="28" cy="135" r="7" fill="{L}"/><path d="M28,128 L40,105 L46,118" stroke="{L}" stroke-width="4" fill="none"/>''')
# H: child huge in mid-air top, man small below laughing up
T['H']=svg(f'''<path d="M20,10 q30,-15 60,10 l15,40 -35,25 -30,-20z" fill="{L}"/><path d="M95,0 L120,0 L120,40Z" fill="{D}"/>
<circle cx="70" cy="135" r="10" fill="{L}"/><ellipse cx="70" cy="142" rx="24" ry="7" fill="none" stroke="{L}" stroke-width="3"/>''')
names={'A':'A high jetty view, man big lower-left, child aloft','B':'B extreme close, head+hands, feet at top','C':'C worm view, child against sky','D':'D side eye-level jetty','E':'E overhead, two heads + rings','F':'F two heads facing, high view','G':'G man on ladder, child splashes','H':'H child huge aloft, man small'}
os.chdir('/home/claude/teodor-work/16/thumbs')
ims=[]
for k,s in T.items():
    open(f'thumb_{k}.svg','w').write(s)
    subprocess.run(['rsvg-convert','-w','240','-h','320','-o',f'thumb_{k}.png',f'thumb_{k}.svg'],check=True)
    ims.append((k,Image.open(f'thumb_{k}.png').convert('RGB')))
sheet=Image.new('RGB',(4*260+20,2*360+20),'#ffffff'); d=ImageDraw.Draw(sheet)
for i,(k,im) in enumerate(ims):
    x=20+(i%4)*260; y=20+(i//4)*360
    sheet.paste(im,(x,y)); d.text((x,y+325),names[k][:40],fill='black')
sheet.save('/home/claude/teodor-work/16/thumbs.png')
