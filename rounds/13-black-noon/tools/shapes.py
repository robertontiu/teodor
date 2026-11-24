import re, subprocess, io, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/v13/tools')
from hatch import hatch_mask

def elem_masks(group):
    """group: list of svg strings, first '<g transform..>', last '</g>'. Returns [(mask, color, opacity, is_stroke)]"""
    head, tail = group[0], group[-1]
    out = []
    for e in group[1:-1]:
        fill = re.search(r'fill="(#[0-9a-fA-F]{6})"', e)
        strk = re.search(r'stroke="(#[0-9a-fA-F]{6})"', e)
        op = re.search(r'opacity="([0-9.]+)"', e)
        op = float(op.group(1)) if op else 1.0
        if fill:
            col = fill.group(1); w = re.sub(r'fill="#[0-9a-fA-F]{6}"', 'fill="#ffffff"', e); is_s = False
        elif strk:
            col = strk.group(1); w = re.sub(r'stroke="#[0-9a-fA-F]{6}"', 'stroke="#ffffff"', e); is_s = True
        else:
            continue
        w = re.sub(r'opacity="[0-9.]+"', '', w)
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600"><rect width="1200" height="1600" fill="#000"/>%s%s%s</svg>' % (head, w, tail)
        png = subprocess.run(['rsvg-convert', '-w', '1200', '-h', '1600'], input=svg.encode(), capture_output=True).stdout
        m = np.asarray(Image.open(io.BytesIO(png)).convert('L')) > 127
        out.append((m, col, op, is_s))
    return out

def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(a[i] * t + b[i] * (1 - t)) for i in range(3))

def jit(c, rnd, a=8):
    v = [min(255, max(0, int(c[i:i + 2], 16) + int(rnd.gauss(0, a)))) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(v)

def paint_group(group, angle, size, base=None, seed=0, spacing=None, seglen=(30, 90), skip_small=0):
    import random
    rnd = random.Random(seed); strokes = []
    for k, (m, col, op, is_s) in enumerate(elem_masks(group)):
        if m.sum() < skip_small: continue
        c = col if (op >= 0.95 or base is None) else mix(col, base, op)
        sz = size if m.sum() > 3000 else (max(3, size[0] * 0.5), max(4, size[1] * 0.5))
        sp = spacing or sz[0] * 0.7
        st = hatch_mask(m, angle + rnd.uniform(-15, 15), sp, sz, [c], seglen=seglen, seed=seed + k, wobble=1.5, step=3,
                        colorfn=lambda x, y, r, c=c: jit(c, r, 6))
        strokes += st
    return strokes
