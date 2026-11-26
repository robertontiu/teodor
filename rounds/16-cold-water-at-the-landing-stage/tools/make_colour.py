import subprocess
from PIL import Image, ImageDraw
def study(p):
    w,deep,ring,flesh,shadow,spray,jetty,jettyl,hair,outline=p
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160">
<defs><linearGradient id="g" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="{w}"/><stop offset="1" stop-color="{deep}"/></linearGradient></defs>
<rect width="120" height="160" fill="url(#g)"/>
<path d="M60,118 q15,-4 30,0 M78,98 q12,-3 25,0 M66,140 q20,-5 40,0 M50,40 q15,-3 30,0 M90,30 q10,-2 25,0" stroke="{ring}" stroke-width="3" fill="none"/>
<polygon points="0,0 60,0 0,32" fill="{jetty}"/><path d="M0,10 L40,0 M0,20 L52,2" stroke="{jettyl}" stroke-width="2"/>
<ellipse cx="34" cy="128" rx="36" ry="12" fill="{deep}" opacity="0.7"/>
<path d="M0,160 L0,104 Q22,94 44,106 L58,160Z" fill="{flesh}"/><path d="M0,160 L0,118 Q12,112 22,122 L28,160Z" fill="{shadow}"/>
<circle cx="32" cy="92" r="15" fill="{flesh}"/><path d="M18,90 a15,15 0 0 1 10,-12 l-2,18z" fill="{shadow}"/>
<path d="M18,82 L10,60 L26,74Z" fill="{flesh}"/><path d="M22,78 q8,-10 18,-6" stroke="{hair}" stroke-width="5" fill="none"/>
<ellipse cx="35" cy="98" rx="5" ry="3" fill="{outline}"/>
<circle cx="88" cy="52" r="8" fill="{flesh}"/><path d="M82,46 q6,-6 12,0" stroke="{hair}" stroke-width="4" fill="none"/><path d="M76,60 L100,60 L98,70 L78,70Z" fill="{flesh}"/>
<path d="M78,62 Q60,48 42,78 Q58,62 74,70Z" fill="{spray}"/><path d="M48,70 l-6,-8 M52,64 l-4,-10 M44,78 l-10,-4 M58,58 l-2,-10" stroke="{spray}" stroke-width="3"/>
</svg>'''
P={'1 emerald water / vermilion skin':('#45b07a','#2a5a6a','#9fd8b0','#ef8a6a','#6e4a9a','#f6f1d8','#d9822e','#a8501e','#1a1a22','#1a1a22'),
   '2 ultramarine deep / orange skin':('#3d5fa8','#1f2a6e','#7fa0e0','#f0a060','#3d5fa8','#fbf2b0','#3f7d5e','#2a5a40','#6e4a9a','#1a1a22'),
   '3 green-gold shallows / rose skin':('#7fbf70','#2f6f7a','#e6d860','#e89aa0','#6e4a9a','#f0ebdf','#df4a2e','#a02a2a','#2a3488','#2a3488')}
ims=[]
for i,(k,p) in enumerate(P.items()):
    open(f'studies/colour_{i+1}.svg','w').write(study(p))
    subprocess.run(['rsvg-convert','-w','300','-h','400','-o',f'studies/colour_{i+1}.png',f'studies/colour_{i+1}.svg'],check=True)
    ims.append((k,Image.open(f'studies/colour_{i+1}.png').convert('RGB')))
sheet=Image.new('RGB',(3*320+20,450),'white'); d=ImageDraw.Draw(sheet)
for i,(k,im) in enumerate(ims):
    sheet.paste(im,(20+i*320,20)); d.text((20+i*320,428),k,fill='black')
sheet.save('colour_studies.png')
