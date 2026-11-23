import cairo, json, sys, math, random, os

W, H = 600, 800
CANVAS = "/home/claude/exp/canvas.png"
LOG = "/home/claude/exp/strokes.jsonl"


def hx(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def mix(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def catmull(pts, steps=14):
    if len(pts) < 2:
        return pts
    p = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        seglen = math.dist(p1, p2)
        n = max(2, int(seglen / 2.5))
        for s in range(n):
            t = s / n
            t2, t3 = t * t, t * t * t
            out.append([
                0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(2)])
    out.append(pts[-1])
    return out


def new(ground="#0b0c16"):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    c.set_source_rgb(*hx(ground))
    c.paint()
    s.write_to_png(CANVAS)
    open(LOG, "w").close()


def stroke(spec):
    s = cairo.ImageSurface.create_from_png(CANVAS)
    c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    rnd = random.Random(spec.get("seed", 1))
    pts = catmull([list(p) for p in spec["pts"]])
    w = spec.get("w", 8)
    col = hx(spec["color"])
    a = spec.get("a", 0.85)
    dry = spec.get("dry", 0.7)
    n = len(pts)
    if spec.get("glaze"):
        for k in range(10):
            c.set_line_width(w * (1 - k * 0.07))
            c.set_source_rgba(*col, a / 6)
            c.move_to(*pts[0])
            for p in pts[1:]:
                c.line_to(p[0] + rnd.uniform(-1, 1), p[1] + rnd.uniform(-1, 1))
            c.stroke()
        s.write_to_png(CANVAS)
        return
    nr = []
    for i in range(n):
        q, o = pts[min(n - 1, i + 1)], pts[max(0, i - 1)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        l = math.hypot(dx, dy) or 1
        nr.append((-dy / l, dx / l))
    pr = lambda t: min(1, t * 6 + 0.2) * (1 - t * spec.get("taper", 0.5))
    c.set_source_rgba(*mix(col, [0, 0, 0], 0.55), a * 0.28)
    c.set_line_width(w * 0.85)
    c.move_to(pts[0][0] + 1, pts[0][1] + 1.2)
    for p in pts[1:]:
        c.line_to(p[0] + 1, p[1] + 1.2)
    c.stroke()
    k = spec.get("k") or max(3, min(16, round(w / 1.3)))
    for b in range(k):
        off = (b / (k - 1) if k > 1 else 0.5) - 0.5 + rnd.uniform(-0.06, 0.06)
        bc = col
        if abs(off) > 0.3:
            bc = mix(col, [1, 1, 1] if off < 0 else [0, 0, 0], (abs(off) - 0.3) * (1.1 if off < 0 else 0.9))
        bc = [min(1, max(0, v + rnd.uniform(-0.08, 0.08))) for v in bc]
        load = 0.5 + rnd.random() * 1.3
        dr = dry + rnd.uniform(-0.15, 0.25)
        c.set_line_width(max(0.6, w / k * 1.7 * rnd.uniform(0.7, 1.3)))
        for i in range(1, n):
            t, t0 = i / (n - 1), (i - 1) / (n - 1)
            if t > dr and rnd.random() < (t - dr) * 2.6:
                continue
            p0, p1, n0, n1 = pts[i - 1], pts[i], nr[i - 1], nr[i]
            c.set_source_rgba(*bc, a * (1 - t ** (1 / load) * 0.6))
            c.move_to(p0[0] + n0[0] * off * w * pr(t0), p0[1] + n0[1] * off * w * pr(t0))
            c.line_to(p1[0] + n1[0] * off * w * pr(t), p1[1] + n1[1] * off * w * pr(t))
            c.stroke()
    s.write_to_png(CANVAS)


if __name__ == "__main__":
    if sys.argv[1] == "new":
        new(sys.argv[2] if len(sys.argv) > 2 else "#0b0c16")
    elif sys.argv[1] == "replay":
        lines = [json.loads(l) for l in open(LOG) if l.strip()]
        new()
        for sp in lines:
            stroke(sp)
        with open(LOG, "w") as f:
            f.write("".join(json.dumps(sp) + "\n" for sp in lines))
    else:
        specs = json.loads(sys.argv[2])
        if isinstance(specs, dict):
            specs = [specs]
        for sp in specs:
            stroke(sp)
            with open(LOG, "a") as f:
                f.write(json.dumps(sp) + "\n")
    os.system(f"cp {CANVAS} /home/claude/exp/view.png")
