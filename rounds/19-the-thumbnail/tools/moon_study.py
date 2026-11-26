"""Moon study at 8x for the detail (canvas 1990,355 100x100): a waxing gibbous, 73% lit, the lit limb up
and a little left (toward the sun); highlands L* 74, two soft maria ~8 below, the unlit part lost in the sky
(a day moon: the dark side is sky). Sky = the drawn sky around it."""
import numpy as np, math, sys
from PIL import Image
from scipy import ndimage as ndi
X0, Y0, W, H, N = 1990, 355, 100, 100, 8
sky = float(sys.argv[1])
cx, cy, r = (2040 - X0 + 0.5) * N - 0.5, (404 - Y0 + 0.5) * N - 0.5, 13.2 * N
yy, xx = np.mgrid[0:H * N, 0:W * N].astype(float)
dx, dy = (xx - cx) / r, (yy - cy) / r
u = np.array([-0.32, -0.95]); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]])
a = dx * u[0] + dy * u[1]; b = dx * v[0] + dy * v[1]
rr = np.sqrt(dx ** 2 + dy ** 2)
k = 2 * 0.73 - 1
term = -k * np.sqrt(np.clip(1 - b ** 2, 0, 1))
lit = np.clip((a - term) / 0.06 + 0.5, 0, 1) * np.clip((1 - rr) / (1.2 / r) + 0.5, 0, 1)
Lm = 74 + 2 * np.clip(a, 0, 1)
def blob(px, py, s): return np.exp(-(((dx - px) ** 2 + (dy - py) ** 2) / (2 * s * s)))
maria = 8 * blob(-0.25, -0.2, 0.22) + 6 * blob(0.2, -0.35, 0.16) + 5 * blob(0.05, 0.15, 0.18) + 4 * blob(-0.45, 0.25, 0.12)
Lm = Lm - maria
L = sky * (1 - lit) + Lm * lit
L = ndi.gaussian_filter(L, 1.0)
np.save("/home/claude/teodor-work/19/plan/m/moon_study_L.npy", L)
fy = (L + 16) / 116; lin = np.where(L > 8, fy ** 3, L / 903.3)
s = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
Image.fromarray(np.clip(s * 255, 0, 255).astype(np.uint8)).convert("RGB").save("/home/claude/teodor-work/19/plan/m/moon_study_8x.png")
