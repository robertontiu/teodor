"""Make a contact sheet of Teodor's past paintings, so a new painting can be measured against them.

Usage: python3 studio/contact_sheet.py <repo>/rounds <out.jpg>
"""
import sys, glob, os
from PIL import Image, ImageDraw

rounds, out = sys.argv[1], sys.argv[2]
paths = sorted(glob.glob(os.path.join(rounds, "*", "painting.jpg")))
W, H, cols, pad = 225, 300, 6, 8
rows = (len(paths) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (W + pad) + pad, rows * (H + 22 + pad) + pad), (20, 18, 16))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(paths):
    x, y = pad + (i % cols) * (W + pad), pad + (i // cols) * (H + 22 + pad)
    sheet.paste(Image.open(p).convert("RGB").resize((W, H)), (x, y))
    d.text((x, y + H + 4), os.path.basename(os.path.dirname(p))[:34], fill=(220, 210, 195))
sheet.save(out, quality=88)
print(f"{len(paths)} paintings -> {out}")
