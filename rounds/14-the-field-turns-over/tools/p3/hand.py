import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import median_filter, gaussian_filter
cur=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(float)
old=np.asarray(Image.open('/home/claude/v14/crit_2.png').convert('RGB')).astype(float)
x0,y0,x1,y1=940,840,1200,1070
box=old[y0:y1,x0:x1]
pk_=(box[...,0]>box[...,1]+10)|(box[...,2]>box[...,1]+10)
w=(~pk_).astype(float)
bg=np.stack([gaussian_filter(box[...,i]*w,12)/(gaussian_filter(w,12)+1e-6) for i in range(3)],-1)
# arm/hand drawing at 4x
S=4; W,H=(x1-x0)*S,(y1-y0)*S
def T(pts): return [((x-x0)*S,(y-y0)*S) for x,y in pts]
sil=Image.new('L',(W,H),0); d=ImageDraw.Draw(sil)
arm=[(940,866),(1000,866),(1060,868),(1092,874),(1130,862),(1168,858),(1200,860),(1200,950),(1182,952),(1178,968),(1184,990),(1172,998),(1154,982),(1134,962),(1100,952),(1060,958),(1000,962),(940,964)]
d.polygon(T(arm),fill=255)
sil=np.asarray(sil.filter(ImageFilter.GaussianBlur(3)).resize((x1-x0,y1-y0),Image.LANCZOS)).astype(float)/255
# shading: light from the upper right / above: top of forearm lit, palm (facing up) lit, a crease, thumb lit on top
yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
top=np.interp(xx,[940,1100,1200],[866,872,872]); bot=np.interp(xx,[940,1100,1200],[964,950,948])
t=np.clip((yy-top)/(bot-top),0,1)            # 0 at top edge, 1 at bottom edge
lit=np.exp(-((t-0.32)/0.28)**2)
palm=np.clip((xx-1100)/30,0,1)
lit=lit*(0.75+0.25*palm)+palm*0.25*np.exp(-((t-0.5)/0.35)**2)
dark=np.array([30,44,140.]); mid=np.array([70,108,210.]); hi=np.array([178,202,244.]); peak=np.array([240,242,230.])
L=np.clip(lit,0,1)[...,None]
col=np.where(L<0.5, dark+(mid-dark)*(L/0.5), mid+(hi-mid)*((L-0.5)/0.5))
pk=np.clip((lit-0.9)/0.1,0,1)[...,None]*palm[...,None]*0.6
col=col*(1-pk)+peak*pk
# palm crease (life line) and thumb separation, soft darks
cr=np.exp(-(((yy-(930+(xx-1110)*0.4))/3.0)**2))*np.clip((xx-1108)/8,0,1)*np.clip((1168-xx)/8,0,1)
col=col*(1-0.45*cr[...,None])+dark*0.45*cr[...,None]
# thumb: lit top
th=np.exp(-((np.hypot(xx-1165,yy-975)-0)/12)**2)
col=col*(1-0.5*th[...,None])+hi*0.5*th[...,None]
sch=bg*(1-sil[...,None])+col*sil[...,None]
out=cur.copy(); out[y0:y1,x0:x1]=sch
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('/home/claude/v14/tools/p3/hand_sch.png')
m=np.zeros(cur.shape[:2],bool); m[y0+4:y1-4,1080:1200]=True
np.save('/home/claude/v14/tools/p3/hand_mask.npy',m)
Image.fromarray(np.clip(sch,0,255).astype(np.uint8)).resize(((x1-x0)*2,(y1-y0)*2)).save('/tmp/hand.png')
