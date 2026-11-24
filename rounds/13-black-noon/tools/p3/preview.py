import sys
from PIL import Image, ImageDraw
def preview(strokesets, out='/tmp/prev.png', box=None):
    im=Image.open('/home/claude/v13/main_full.png').convert('RGB'); d=ImageDraw.Draw(im)
    for ss in strokesets:
        for s in ss:
            d.line([tuple(p) for p in s['pts']],fill=s['color'],width=max(1,int(s['size'])),joint='curve')
    if box: im=im.crop(box)
    im.save(out)
