import json
from PIL import Image, ImageDraw
r=json.load(open('plan/m/regions.json'))
im=Image.open('main_full.png').convert('RGB')
d=ImageDraw.Draw(im)
cols={'sky':'red','lower':'blue','sleeve':'green','torso':'magenta','ground':'yellow','hairr':'cyan','grass':'orange','face_core':'white','face_work':'white','chest':'magenta','sky_round_hand':'red'}
def polys(v):
    if isinstance(v,dict): return [v]
    if v and isinstance(v[0],dict): return v
    return [{'type':'poly','pts':v}]
for k,v in r.items():
    if k in ('grass','sky','lower','sky_round_hand'): continue
    for x in polys(v):
        if x['type']=='poly':
            d.line([tuple(p) for p in x['pts']]+[tuple(x['pts'][0])], fill=cols.get(k,'black'), width=8)
        else:
            d.ellipse([x['cx']-x['rx'],x['cy']-x['ry'],x['cx']+x['rx'],x['cy']+x['ry']],outline='white',width=6)
im.resize((600,800)).save('p3/regs.png')
