import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
cur=np.asarray(Image.open('/home/claude/v14/main_full.png').convert('RGB')).astype(float)
Hh,Ww=cur.shape[:2]; yy,xx=np.mgrid[0:Hh,0:Ww].astype(float)
X=[780,820,860,900,940,980,1020,1060,1092,1130,1168,1200]
TOP=[840,852,858,862,862,864,867,868,872,864,859,860]
BOT=[990,972,960,956,955,955,955,957,952,952,950,950]
top=np.interp(xx,X,TOP); bot=np.interp(xx,X,BOT)
t=(yy-top)/(bot-top)
sil=((t>0)&(t<1)&(xx>=780)).astype(float)
# thumb
th=Image.new('L',(Ww,Hh),0); ImageDraw.Draw(th).polygon([(1136,950),(1180,950),(1186,988),(1174,998),(1154,982)],fill=255)
thm=np.asarray(th).astype(float)/255
sil=np.clip(sil+thm,0,1); sil=gaussian_filter(sil,1.5)
lit=0.25+0.75*np.exp(-((t-0.3)/0.32)**2)*(1+0.08*np.sin(xx/23))
palm=np.clip((xx-1095)/30,0,1)
lit=np.clip(lit*(0.8+0.2*palm),0,1)
dark=np.array([24,36,128.]); mid=np.array([62,98,206.]); hi=np.array([176,200,244.]); peak=np.array([226,234,240.])
L=lit[...,None]
col=np.where(L<0.5, dark+(mid-dark)*(L/0.5), mid+(hi-mid)*((L-0.5)/0.5))
pk=(np.clip((lit-0.88)/0.12,0,1)*palm)[...,None]*0.7
col=col*(1-pk)+peak*pk
# palm crease, thumb lit
cr=np.exp(-((yy-(932+(xx-1110)*0.35))/2.5)**2)*np.clip((xx-1108)/8,0,1)*np.clip((1170-xx)/8,0,1)
col=col*(1-0.4*cr[...,None])+dark*0.4*cr[...,None]
tl=np.exp(-(np.hypot(xx-1164,yy-972)/11)**2)*thm
col=col*(1-0.6*tl[...,None])+hi*0.6*tl[...,None]
# fade into the existing shoulder
w=np.clip((xx-800)/90,0,1)[...,None]
col=cur*(1-w)+col*w
sch=cur*(1-sil[...,None])+col*sil[...,None]
Image.fromarray(np.clip(sch,0,255).astype(np.uint8)).save('/home/claude/v14/tools/p3/arm_sch.png')
m=(gaussian_filter(sil,3)>0.05)&(xx>=790)
np.save('/home/claude/v14/tools/p3/arm_mask.npy',m)
Image.fromarray(np.clip(sch,0,255).astype(np.uint8)).crop((760,820,1200,1020)).save('/tmp/arm.png')
