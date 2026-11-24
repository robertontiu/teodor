# grander shadow: the figure's silhouette thrown by the footlights, scale 1.7 from (400,1400),
# chest puffed, crown enlarged and upright. Writes gen/shadow56.svg and gen/mask_shadow56.png
import subprocess
D='/home/claude/v12/gen/'
body='''
 <path d="M650,846 C700,850 720,900 726,980 C734,1080 748,1180 766,1246 L640,1250 C660,1150 668,1050 664,960 Z"/>
 <path d="M556,990 C552,1080 546,1170 538,1244 L700,1246 C694,1170 688,1080 682,990 Z"/>
 <path d="M530,860 C550,830 670,832 690,858 C704,900 690,945 655,965 L530,965 C520,920 522,880 530,860 Z"/>
 <ellipse cx="600" cy="960" rx="80" ry="80"/>
 <path d="M664,858 L748,930 L686,1006 L668,994 L716,932 L654,882 Z"/>
 <path d="M664,858 L752,926 L744,942 L660,872 Z"/>
 <circle cx="672" cy="1004" r="15"/>
 <path d="M548,866 L512,790 L486,728 L506,720 L532,782 L576,852 Z"/>
 <path d="M548,866 L512,790 L486,728 L494,724 L522,790 L560,860 Z"/>
 <path d="M484,732 L510,722 L506,712 L482,720 Z"/>
 <ellipse cx="492" cy="702" rx="17" ry="18"/>
 <ellipse cx="606" cy="796" rx="27" ry="31" transform="rotate(-14 606 796)"/>
 <path d="M584,808 C590,826 612,834 628,820 L622,836 C606,842 588,832 584,808 Z"/>
 <ellipse cx="612" cy="848" rx="80" ry="16"/>
 <g transform="rotate(-6 606 770)">
  <path d="M584,776 L582,740 L592,756 L598,730 L606,752 L614,726 L620,752 L628,732 L632,758 L640,742 L636,776 Z"/>
  <rect x="582" y="770" width="56" height="8"/>
 </g>
'''
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600" width="1200" height="1600">
<defs><clipPath id="in"><rect x="222" y="170" width="800" height="958"/></clipPath>
<filter id="b"><feGaussianBlur stdDeviation="2.5"/></filter></defs>
<g clip-path="url(#in)"><g filter="url(#b)" fill="#000"><g transform="translate(380,1400) scale(1.7) translate(-380,-1400)">{body}</g></g></g>
</svg>'''
open(D+'shadow56.svg','w').write(svg)
subprocess.run(['rsvg-convert','-w','1200','-h','1600','-o',D+'mask_shadow56.png',D+'shadow56.svg'],check=True)
