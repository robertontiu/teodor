# seeds for a tint block: one stroke deep inside each visible piece of an area of colour HEX in an SVG schema
import sys, json, subprocess, numpy as np
from PIL import Image
from scipy.ndimage import label, distance_transform_edt
svg, hexc = sys.argv[1], sys.argv[2]
subprocess.run(["rsvg-convert", "-w", "1200", "-h", "1600", svg, "-o", "/tmp/t18p3/tint_full.png"], check=True)
a = np.asarray(Image.open("/tmp/t18p3/tint_full.png").convert("RGB"), np.float32) / 255
c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)]) / 255
m = np.abs(a - c).max(-1) < 0.03
lb, n = label(m)
out = []
for k in range(1, n + 1):
    mk = lb == k
    if mk.sum() < 200: continue
    d = distance_transform_edt(mk)
    y, x = np.unravel_index(np.argmax(d), d.shape)
    sz = float(min(8, d.max() * 0.8))
    x, y = int(x), int(y)
    out.append({"pts": [[x - 2, y], [x + 2, y]], "size": sz, "color": hexc})
print(json.dumps(out))
