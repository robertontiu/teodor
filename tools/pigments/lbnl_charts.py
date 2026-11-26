"""Read the Kubelka-Munk K and S spectra out of the LBNL Pigment Database's published spectral charts.

Source: R. Levinson, P. Berdahl, H. Akbari, Lawrence Berkeley National Laboratory Pigment Database
(https://coolcolors.lbl.gov/LBNL-Pigment-Database/database.html), with the method in "Solar spectral optical
properties of pigments, Part I: model for deriving scattering and absorption coefficients from transmittance and
reflectance measurements" and "Part II: survey of common colorants", Solar Energy Materials & Solar Cells 89
(2005) 319-349 and 351-389. Thin films (about 15-30 um) of artists' acrylic paints (mostly Liquitex) were
measured over a void (reflectance and transmittance), over an opaque white and over an opaque black, from
300 to 2500 nm, and K and S (mm^-1) were computed per film; tints are paint mixed with titanium white W03 by
volume (1:4 and 1:9).

The numeric datafiles are AES-encrypted for the project's partners, so they are not used. The public charts
(spectral-charts/pdf/<code>-tint-ladder-spectral-chart.pdf, <code>-masstone-spectral-chart.pdf) are vector
graphics written by R: every curve is a polyline of 441 points (300-2500 nm in 5 nm steps) in panel II
("K-M coefficient (mm^-1)", log axis; purple = absorption K, gold = backscattering S, per the chart's legend).
This script maps those points back to data through the axis ticks drawn in the same file (x: 500-2500 nm ticks;
y: 10^-1 ... 10^3), so the values are the plotted ones (2 decimal places in PDF points: about 0.3% in K or S,
0.8 nm in wavelength), not a raster digitisation.

  python3 tools/pigments/lbnl_charts.py [chart.pdf ...]   # default: every PDF in $TEODOR_PIGMENT_DATA/lbnl/charts
writes $TEODOR_PIGMENT_DATA/lbnl/lbnl_ks.json: per chart, per column, K and S (mm^-1) at 400-700 nm / 10 nm and the
column's caption (paint code, name, pigment, PVC, film thicknesses).
"""
import json, os, re, sys, glob
import numpy as np
from pypdf import PdfReader

DATA = os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data"))
WL = np.arange(400, 701, 10)
K_COL, S_COL = (0.627, 0.125, 0.941), (1.0, 0.843, 0.0)


def content(path):
    page = PdfReader(path).pages[0]
    c = page.get_contents()
    return c.get_data().decode("latin-1")


def parse(text):
    """Stroked polylines with their clip rectangle and colour, tick segments, and text items."""
    clip, col, cur = None, None, []
    paths, ticks, texts = [], [], []
    for line in text.split("\n"):
        p = line.split()
        if not p:
            continue
        if line.endswith("re W n"):
            clip = tuple(map(float, p[-7:-3]))
        elif p[-1] == "RG":
            col = tuple(round(float(v), 3) for v in p[:3])
        elif len(p) == 7 and p[2] == "m" and p[5] == "l" and p[6] == "S":       # "x y m x y l S": an axis or tick segment
            ticks.append(tuple(map(float, (p[0], p[1], p[3], p[4]))))
        elif p[-1] == "m":
            cur = [(float(p[0]), float(p[1]))]
        elif p[-1] == "l":
            cur.append((float(p[0]), float(p[1])))
        elif p[-1] in ("S", "s"):
            if cur:
                paths.append(dict(clip=clip, col=col, pts=np.array(cur)))
            cur = []
        elif "Tm" in line and "Tj" in line:
            m = re.search(r"([-\d.]+) ([-\d.]+) Tm\s*\((.*)\) Tj", line)
            if m:
                texts.append((float(m.group(1)), float(m.group(2)), m.group(3).replace("\\(", "(").replace("\\)", ")")))
    return paths, ticks, texts


def axes(ticks, x0, y0, w, h):
    """Linear x (nm) and log y maps of the panel whose plot box starts at (x0, y0), from its tick segments."""
    xt = sorted({round(a, 2) for a, b, c, d in ticks if abs(a - c) < 1e-6 and abs(b - y0) < 0.01 and d < b and x0 - 0.1 <= a <= x0 + w + 0.1
                 and b - d > 4})                         # major x ticks hang 4.75 pt below the box
    yt = sorted({round(b, 2) for a, b, c, d in ticks if abs(b - d) < 1e-6 and abs(a - x0) < 0.01 and c < a and a - c > 4
                 and y0 <= b <= y0 + h})                 # major y ticks
    if len(xt) != 5 or len(yt) != 5:
        raise ValueError(f"unexpected ticks for panel at {x0},{y0}: {xt} {yt}")
    fx = np.polyfit(xt, [500, 1000, 1500, 2000, 2500], 1)
    fy = np.polyfit(yt, [-1, 0, 1, 2, 3], 1)
    return (lambda x: np.polyval(fx, x)), (lambda y: 10 ** np.polyval(fy, y))


def captions(texts, x0, w):
    lines = sorted([(y, x, s) for x, y, s in texts if y < 45 and x0 - 2 <= x < x0 + w], key=lambda t: (-t[0], t[1]))
    out, last = [], None
    for y, x, s in lines:
        if last is not None and abs(y - last) < 1:
            out[-1] += s
        else:
            out.append(s)
        last = y
    return [s.strip() for s in out]


def thickness(texts, x0, w, y_lo, y_hi):
    """Film thicknesses printed in a panel ('16 um/void', '18 um/white', '17 um/black'), joined per line."""
    rows = {}
    for x, y, s in texts:
        if x0 <= x < x0 + w and y_lo <= y <= y_hi:
            rows.setdefault(round(y), []).append((x, s))
    found = {}
    for y, items in rows.items():
        t = "".join(s for _, s in sorted(items))
        for m in re.finditer(r"(\d+)\s*m+/?\s*(void|white|black)", t.replace(" ", "")):
            found[m.group(2)] = int(m.group(1))
    return found


def read_chart(path):
    paths, ticks, texts = parse(content(path))
    panels = sorted({p["clip"] for p in paths if p["clip"] and p["col"] in (K_COL, S_COL)})
    cols = []
    for clip in panels:
        x0, y0, w, h = clip
        fx, fy = axes(ticks, x0, y0, w, h)
        res = {}
        for name, colr in (("K", K_COL), ("S", S_COL)):
            segs = [p["pts"] for p in paths if p["clip"] == clip and p["col"] == colr]
            pts = np.concatenate(segs)
            lam, val = fx(pts[:, 0]), fy(pts[:, 1])
            o = np.argsort(lam)
            lam, val = lam[o], val[o]
            # a value is only read where the curve has points within 6 nm (gaps stay NaN)
            v = np.interp(WL, lam, np.log10(val))
            near = np.array([np.min(np.abs(lam - w_)) for w_ in WL]) < 6
            res[name] = [round(float(10 ** a), 5) if ok else None for a, ok in zip(v, near)]
        cap = captions(texts, x0, w)
        th = thickness(texts, x0, w, y0 + h + 40, y0 + h + 160)       # panel I sits above panel II
        th.update(thickness(texts, x0, w, y0 - 40, y0))               # panel III's labels sit below panel II
        cols.append(dict(caption=cap, thickness_um=th, K_per_mm=res["K"], S_per_mm=res["S"]))
    return cols


def main(files):
    out = {"source": "LBNL Pigment Database spectral charts (Levinson, Berdahl, Akbari 2005), read by tools/pigments/lbnl_charts.py",
           "wavelengths_nm": [400, 700, 10], "unit": "K and S per mm of dry film", "charts": {}}
    for f in files:
        try:
            out["charts"][os.path.basename(f)] = read_chart(f)
            print(os.path.basename(f), [c["caption"][:2] for c in out["charts"][os.path.basename(f)]])
        except Exception as e:
            print(f"{f}: {e}", file=sys.stderr)
    dst = os.path.join(DATA, "lbnl", "lbnl_ks.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(out, open(dst, "w"), indent=1)
    print(dst)


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob(os.path.join(DATA, "lbnl", "charts", "*.pdf"))))
