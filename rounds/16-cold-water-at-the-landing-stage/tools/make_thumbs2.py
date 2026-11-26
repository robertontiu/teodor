import subprocess
from PIL import Image, ImageDraw
L,M,D='#ece8dc','#8c8c8c','#2e2e2e'
def svg(body): return f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160"><rect width="120" height="160" fill="{M}"/>{body}</svg>'
T={}
T['I']=svg(f'''<polygon points="0,0 58,0 0,30" fill="{D}"/>
<path d="M0,160 L0,100 Q20,92 40,104 L55,160Z" fill="{L}"/><circle cx="30" cy="92" r="15" fill="{L}"/>
<path d="M14,84 L8,62 L22,74Z" fill="{L}"/><ellipse cx="32" cy="98" rx="5" ry="3" fill="{D}"/>
<circle cx="88" cy="52" r="8" fill="{L}"/><path d="M76,60 L100,60 L98,70 L78,70Z" fill="{L}"/>
<path d="M78,62 Q60,50 44,76 Q58,62 74,70Z" fill="{L}"/><path d="M48,70 l-6,-8 M52,64 l-4,-10 M44,78 l-10,-4" stroke="{L}" stroke-width="3"/>
<path d="M60,120 q15,-4 30,0 M80,100 q12,-3 25,0 M70,140 q20,-5 40,0" stroke="{D}" stroke-width="3" fill="none"/>''')
T['J']=svg(f'''<polygon points="120,0 120,70 90,0" fill="{D}"/>
<circle cx="78" cy="62" r="11" fill="{L}"/><path d="M62,72 L94,72 L92,92 L64,92Z" fill="{L}"/><path d="M66,62 L60,44 L72,54Z" fill="{L}"/>
<path d="M0,160 L0,120 Q30,110 50,130 L60,160Z" fill="{L}"/><circle cx="34" cy="118" r="13" fill="{D}"/>
<path d="M40,112 Q58,80 70,74" stroke="{L}" stroke-width="6" fill="none"/>''')
names={'I':'I man big lower-left, child splashes arc','J':'J child foreground back, man beyond'}
ims=[]
for k,s in T.items():
    open(f'thumbs/thumb_{k}.svg','w').write(s)
    subprocess.run(['rsvg-convert','-w','240','-h','320','-o',f'thumbs/thumb_{k}.png',f'thumbs/thumb_{k}.svg'],check=True)
old=Image.open('thumbs.png'); W,H=old.size
sheet=Image.new('RGB',(W,H+360),'white'); sheet.paste(old,(0,0)); d=ImageDraw.Draw(sheet)
for i,k in enumerate(T):
    x=20+i*260; y=H; sheet.paste(Image.open(f'thumbs/thumb_{k}.png').convert('RGB'),(x,y)); d.text((x,y+325),names[k],fill='black')
sheet.save('thumbs.png')
