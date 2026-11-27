"""A CPU triangle rasteriser in numpy, for meshes in scene blockouts (scene.py, human.py).

There is no GPU here and no headless OpenGL (no PyOpenGL, moderngl or OSMesa in the studio's
dependencies), so meshes are drawn by a z-buffer in numpy:

- `raster(sx, sy, depth, tris, W, H, persp)`: every triangle's covered pixel centres, nearest first.
  Triangles are bucketed by the size of their screen bounding box; each bucket tests a k x k block of
  candidate pixels per triangle at once, keeps those inside all three edge functions, and resolves
  depth per pixel by sorting. Returns the depth buffer, the triangle per pixel and the barycentric
  weights (perspective-correct when `persp`).
- `ShadowMap`: the same rasteriser seen from the sun (orthographic), sampled with percentage-closer
  filtering whose radius grows with the distance to the blocker (soft shadows, PCSS-like), so a
  mesh casts shadows on itself and on the SDF world, with the same `softness` as the SDF shadows.

Speed (2 vCPU): about 0.1-0.3 s for the 37 000 triangles of a person, at 200 x 260 to 450 x 600.
"""
import math
import numpy as np


def raster(sx, sy, depth, tris, W, H, persp=True, cull=None, near=1e-3):
    """sx, sy: pixel coordinates of the vertices (pixel centres at integers); depth: camera z (persp)
    or any linear depth; tris (T,3) vertex indices. cull: None, or +1/-1 to drop triangles whose screen
    winding has that sign. Returns zbuf (H,W) (inf where empty), tri (H,W) int32 (-1 empty), bary (H,W,3)."""
    tris = np.asarray(tris, np.int64)
    x0, x1, x2 = sx[tris[:, 0]], sx[tris[:, 1]], sx[tris[:, 2]]
    y0, y1, y2 = sy[tris[:, 0]], sy[tris[:, 1]], sy[tris[:, 2]]
    z0, z1, z2 = depth[tris[:, 0]], depth[tris[:, 1]], depth[tris[:, 2]]
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    ok = np.abs(area) > 1e-12
    if persp:
        ok &= (z0 > near) & (z1 > near) & (z2 > near)
    if cull is not None:
        ok &= np.sign(area) != cull
    xmin = np.ceil(np.minimum(np.minimum(x0, x1), x2)).astype(np.int64)
    xmax = np.floor(np.maximum(np.maximum(x0, x1), x2)).astype(np.int64)
    ymin = np.ceil(np.minimum(np.minimum(y0, y1), y2)).astype(np.int64)
    ymax = np.floor(np.maximum(np.maximum(y0, y1), y2)).astype(np.int64)
    xmin, ymin = np.maximum(xmin, 0), np.maximum(ymin, 0)
    xmax, ymax = np.minimum(xmax, W - 1), np.minimum(ymax, H - 1)
    ok &= (xmax >= xmin) & (ymax >= ymin)
    ext = np.maximum(xmax - xmin, ymax - ymin) + 1
    zbuf = np.full(W * H, np.inf, np.float64)
    tbuf = np.full(W * H, -1, np.int64)
    bbuf = np.zeros((W * H, 3), np.float32)
    lo = 0
    k = 1
    while True:
        sel = np.nonzero(ok & (ext > lo) & (ext <= k))[0]
        if len(sel):
            oy, ox = np.mgrid[0:k, 0:k]
            ox, oy = ox.ravel(), oy.ravel()
            step = max(1, int(3_000_000 // (k * k)))
            for c in range(0, len(sel), step):
                t = sel[c:c + step]
                px = xmin[t][:, None] + ox[None]
                py = ymin[t][:, None] + oy[None]
                inb = (px <= xmax[t][:, None]) & (py <= ymax[t][:, None])
                a = area[t][:, None]
                # edge functions (barycentric numerators) at the pixel centres
                w0 = ((x1[t][:, None] - px) * (y2[t][:, None] - py) - (x2[t][:, None] - px) * (y1[t][:, None] - py)) / a
                w1 = ((x2[t][:, None] - px) * (y0[t][:, None] - py) - (x0[t][:, None] - px) * (y2[t][:, None] - py)) / a
                w2 = 1 - w0 - w1
                eps = -1e-7
                m = inb & (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
                if not m.any():
                    continue
                ti, ci = np.nonzero(m)
                w0, w1, w2 = w0[ti, ci], w1[ti, ci], w2[ti, ci]
                tt = t[ti]
                if persp:
                    iz = w0 / z0[tt] + w1 / z1[tt] + w2 / z2[tt]
                    z = 1 / iz
                    b0, b1 = w0 / z0[tt] * z, w1 / z1[tt] * z
                else:
                    z = w0 * z0[tt] + w1 * z1[tt] + w2 * z2[tt]
                    b0, b1 = w0, w1
                pix = py[ti, ci] * W + px[ti, ci]
                o = np.lexsort((z, pix))
                pix, z = pix[o], z[o]
                first = np.ones(len(pix), bool)
                first[1:] = pix[1:] != pix[:-1]
                o = o[first]; pix = pix[first]; z = z[first]
                win = z < zbuf[pix]
                o, pix, z = o[win], pix[win], z[win]
                zbuf[pix] = z
                tbuf[pix] = tt[o]
                bbuf[pix, 0] = b0[o]; bbuf[pix, 1] = b1[o]; bbuf[pix, 2] = 1 - b0[o] - b1[o]
        lo = k
        if k >= ext[ok].max(initial=0):
            break
        k *= 2
    return zbuf.reshape(H, W), tbuf.reshape(H, W), bbuf.reshape(H, W, 3)


class ShadowMap:
    """Depth of the meshes seen from the sun (orthographic along -ld). `visibility(p, n)` returns 0..1."""

    def __init__(self, verts, tris, ld, texel=0.0025, softness=10.0, max_res=3072):
        ld = np.asarray(ld, np.float64)
        ld = ld / np.linalg.norm(ld)
        up = np.array([0, 1, 0.0]) if abs(ld[1]) < 0.95 else np.array([0, 0, 1.0])
        self.lx = np.cross(up, ld); self.lx /= np.linalg.norm(self.lx)
        self.ly = np.cross(ld, self.lx)
        self.ld = ld
        P = np.asarray(verts, np.float64)
        u, v = P @ self.lx, P @ self.ly
        pad = 0.05
        self.u0, self.v0 = u.min() - pad, v.min() - pad
        ext = max(u.max() - self.u0, v.max() - self.v0) + pad
        self.texel = max(texel, ext / max_res)
        self.W = int(math.ceil((u.max() + pad - self.u0) / self.texel)) + 1
        self.H = int(math.ceil((v.max() + pad - self.v0) / self.texel)) + 1
        sx, sy = (u - self.u0) / self.texel, (self.v0 + (self.H - 1) * self.texel - v) / self.texel
        dep = -(P @ ld)                 # smaller = nearer the sun
        self.z, _, _ = raster(sx, sy, dep, tris, self.W, self.H, persp=False)
        self.soft = softness
        rng = np.random.default_rng(7)
        # a Poisson-like disk: 24 points by a golden-angle spiral
        k = np.arange(24) + 0.5
        r = np.sqrt(k / 24)
        a = k * 2.39996
        self.disk = np.stack([r * np.cos(a), r * np.sin(a)], 1) + rng.normal(0, 0.01, (24, 2))

    def _look(self, u, v):
        x = np.clip(np.round((u - self.u0) / self.texel).astype(np.int64), 0, self.W - 1)
        y = np.clip(np.round((self.v0 + (self.H - 1) * self.texel - v) / self.texel).astype(np.int64), 0, self.H - 1)
        inside = ((u - self.u0) >= 0) & ((u - self.u0) / self.texel <= self.W - 1) & \
                 ((self.v0 + (self.H - 1) * self.texel - v) >= 0) & ((self.v0 + (self.H - 1) * self.texel - v) / self.texel <= self.H - 1)
        z = self.z[y, x]
        return np.where(inside, z, np.inf)

    def visibility(self, p, n=None, bias=0.004, search=0.12):
        p = np.asarray(p, np.float64)
        if n is not None:
            p = p + np.asarray(n, np.float64) * max(0.006, 1.5 * self.texel)
        u, v, d = p @ self.lx, p @ self.ly, -(p @ self.ld)
        # blocker search: the mean depth of what lies nearer the sun within `search` m
        su = self.disk[None, :, 0] * search
        sv = self.disk[None, :, 1] * search
        zb = self._look(u[:, None] + su, v[:, None] + sv)
        blk = zb < (d[:, None] - bias)
        nb = blk.sum(1)
        vis = np.ones(len(p))
        has = nb > 0
        if not has.any():
            return vis.astype(np.float32)
        zm = np.where(blk, zb, 0).sum(1)[has] / nb[has]
        # penumbra grows with the gap between receiver and blocker (the SDF shadows' k: width ~ gap / k)
        rad = np.clip((d[has] - zm) / self.soft, 1.2 * self.texel, search)
        zz = self._look(u[has, None] + self.disk[None, :, 0] * rad[:, None], v[has, None] + self.disk[None, :, 1] * rad[:, None])
        vis[has] = (zz >= d[has, None] - bias).mean(1)
        return vis.astype(np.float32)


# ---------------------------------------------------------------- hair strands (screen space)
def _splat(acc, xs, ys, w):
    """Bilinear splat of weights w at sub-pixel positions into acc (H, W), in place."""
    H, W = acc.shape
    x0, y0 = np.floor(xs).astype(np.int64), np.floor(ys).astype(np.int64)
    fx, fy = xs - x0, ys - y0
    flat = acc.reshape(-1)
    for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        flat += np.bincount((yi[ok] * W + xi[ok]), weights=(w * ww)[ok], minlength=H * W)


def strands(mask, dirf, px_per_mm, seed=11, length_mm=(2.5, 8.0), spacing_mm=0.09, clump_mm=0.6, max_strands=120000):
    """Hair as strands in screen space: streamlines of the hair's growth direction (dirf, (H, W, 2) unit vectors in
    the picture) seeded over the hair (mask), each traced both ways for its length and splatted as a thin line, in
    two families: fine strands (one hair about every spacing_mm across the flow) and clumps (locks about clump_mm
    wide that share a brightness). Returns per pixel: cov (0-1, how much of the pixel is covered by strands: the
    gaps between them read as the deeper, darker hair), bright (each strand's and clump's own brightness, mean 1) and
    shift (each strand's tilt of its highlight, -1..1: the sheen breaks along strands instead of one band).
    Lengths, spacing and spreads are judgements (hair is 0.02-0.18 mm across; drawn hair is a 0.3-0.5 mm line)."""
    H, W = mask.shape
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    out = dict(cov=np.zeros((H, W), np.float32), bright=np.ones((H, W), np.float32), shift=np.zeros((H, W), np.float32))
    if len(ys) < 20:
        return out
    ppm = max(float(px_per_mm), 0.3)
    step = 0.6
    res = {}
    for fam, (sp_mm, bsd, w_mul) in (("fine", (spacing_mm, 0.22, 1.0)), ("clump", (clump_mm, 0.16, 1.0))):
        Lpx = np.array(length_mm) * ppm
        n = int(min(max_strands, len(ys) / max(sp_mm * ppm * Lpx.mean(), 1e-3)))
        n = max(n, 50)
        k = rng.integers(0, len(ys), n)
        sx0 = xs[k] + rng.random(n); sy0 = ys[k] + rng.random(n)
        L = rng.uniform(Lpx[0], Lpx[1], n)
        b = np.exp(rng.normal(0, bsd, n))
        s_ = rng.uniform(-1, 1, n)
        acc = np.zeros((H, W), np.float64); accb = np.zeros((H, W), np.float64); accs = np.zeros((H, W), np.float64)
        for sgn in (1.0, -1.0):
            x, y = sx0.copy(), sy0.copy()
            px_, py_ = None, None
            alive = np.ones(n, bool)
            nsteps = int(np.ceil(Lpx[1] / 2 / step))
            for t in range(nsteps):
                xi = np.clip(x.astype(np.int64), 0, W - 1); yi = np.clip(y.astype(np.int64), 0, H - 1)
                alive &= mask[yi, xi] & (t * step < L / 2)
                if not alive.any():
                    break
                d = dirf[yi, xi] * sgn
                if px_ is not None:                        # keep the direction continuous along the strand
                    flip = (d[:, 0] * px_ + d[:, 1] * py_) < 0
                    d[flip] *= -1
                # a strand tapers toward its ends: weight falls over its last third
                tw = np.clip((L / 2 - t * step) / (L / 6), 0, 1)
                w = np.where(alive, step * tw, 0.0)
                _splat(acc, x, y, w); _splat(accb, x, y, w * b); _splat(accs, x, y, w * s_)
                px_, py_ = d[:, 0], d[:, 1]
                x = x + d[:, 0] * step; y = y + d[:, 1] * step
        res[fam] = (acc, accb / np.maximum(acc, 1e-9), accs / np.maximum(acc, 1e-9))
    fine, clump = res["fine"], res["clump"]
    # coverage: a strand about a hair's width (0.07 mm) wide; the expected density per pixel normalises it so an even
    # head of hair is mostly covered, with gaps where the strands part
    dens = fine[0] / max(float(np.median(fine[0][mask])) if mask.any() else 1.0, 1e-6)
    out["cov"] = (1 - np.exp(-1.3 * dens)).astype(np.float32)
    out["bright"] = (np.where(fine[0] > 0, fine[1], 1.0) * np.where(clump[0] > 0, clump[1], 1.0)).astype(np.float32)
    out["shift"] = np.where(fine[0] > 0, fine[2], 0.0).astype(np.float32)
    return out
