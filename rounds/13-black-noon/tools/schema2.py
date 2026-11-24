# Teodor phase-2 overlay: black sun, uplit faces, hands (pulse fingers, open hand), phone.
import math
def head(cx, cy, s, rot, skin, shade, bounce, hair, mouth="line", hang=0, rim="#ffffff"):
    g = ['<g transform="translate(%d %d) rotate(%d) scale(%.2f)">' % (cx, cy, rot, s)]
    # neck going to the body (local +y)
    g.append('<path d="M-34,40 C-36,70 -40,95 -50,120 L50,120 C40,95 36,70 34,40 Z" fill="%s"/>' % shade)
    g.append('<path d="M-30,60 C-20,95 20,95 30,60 C20,120 -20,120 -30,60 Z" fill="%s" opacity="0.55"/>' % bounce)
    # hair / cranium behind the face (local -y, toward the sky gap)
    g.append('<ellipse cx="0" cy="-38" rx="66" ry="60" fill="%s"/>' % hair)
    # face oval seen from below: wide jaw, short forehead
    g.append('<path d="M-50,-30 C-56,5 -48,40 -28,62 C-14,76 14,76 28,62 C48,40 56,5 50,-30 C30,-44 -30,-44 -50,-30 Z" fill="%s"/>' % shade)
    # warm bounce from the pavement on the undersides: jaw, chin, cheek bottoms
    g.append('<path d="M-42,26 C-36,54 -18,74 0,78 C18,74 36,54 42,26 C40,70 30,96 0,104 C-30,96 -40,70 -42,26 Z" fill="%s"/>' % bounce)
    g.append('<path d="M-46,-4 C-44,14 -38,26 -30,34 L-40,30 C-46,20 -48,8 -46,-4 Z" fill="%s" opacity="0.8"/>' % bounce)
    g.append('<path d="M46,-4 C44,14 38,26 30,34 L40,30 C46,20 48,8 46,-4 Z" fill="%s" opacity="0.8"/>' % bounce)
    # nose underside (lit) and nostrils (dark)
    g.append('<path d="M-15,12 C-10,4 10,4 15,12 C10,26 -10,26 -15,12 Z" fill="%s"/>' % bounce)
    g.append('<ellipse cx="-8" cy="15" rx="5" ry="3.5" fill="#140c0a"/><ellipse cx="8" cy="15" rx="5" ry="3.5" fill="#140c0a"/>')
    # brow ridge undersides lit, sockets dark
    g.append('<path d="M-38,-12 C-28,-20 -10,-18 -6,-12 C-14,-8 -30,-6 -38,-12 Z" fill="%s" opacity="0.7"/>' % bounce)
    g.append('<path d="M38,-12 C28,-20 10,-18 6,-12 C14,-8 30,-6 38,-12 Z" fill="%s" opacity="0.7"/>' % bounce)
    g.append('<ellipse cx="-21" cy="-22" rx="15" ry="8" fill="#1a100c" opacity="0.55"/><ellipse cx="21" cy="-22" rx="15" ry="8" fill="#1a100c" opacity="0.55"/>')
    # mouth
    if mouth == "open":
        g.append('<ellipse cx="0" cy="40" rx="14" ry="9" fill="#1a0806"/>')
        g.append('<path d="M-14,44 C-6,50 6,50 14,44" stroke="%s" stroke-width="3" fill="none"/>' % bounce)
    else:
        g.append('<path d="M-14,40 C-5,43 5,43 14,40" stroke="#2a140e" stroke-width="4" fill="none"/>')
    # hanging hair toward us (local +y beyond the face edges)
    if hang:
        g.append('<path d="M-66,-40 C-80,10 -76,70 -62,%d C-50,90 -44,40 -46,-10 Z" fill="%s"/>' % (110+hang*4, hair))
        g.append('<path d="M66,-40 C80,10 76,70 62,%d C50,95 44,40 46,-10 Z" fill="%s"/>' % (130+hang*4, hair))
        g.append('<path d="M-60,-30 C-60,30 -58,70 -50,100" stroke="#7a4020" stroke-width="3" fill="none" opacity="0.7"/>')
    # rim of glare on the cranium (sky side)
    g.append('<path d="M-62,-62 C-52,-92 -24,-100 -4,-99" stroke="%s" stroke-width="4" fill="none"/>' % rim)
    g.append('<path d="M14,-98 C34,-96 54,-84 63,-60" stroke="%s" stroke-width="3" fill="none"/>' % rim)
    g.append('</g>')
    return g

def taper(pts, w0, w1, col, op=1.0):
    L = []; R = []; n = len(pts)
    for i, (x, y) in enumerate(pts):
        j = min(i + 1, n - 1); k = max(i - 1, 0)
        dx, dy = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]; d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d; w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    P = L + R[::-1]
    return '<polygon points="%s" fill="%s" opacity="%.2f"/>' % (" ".join("%.0f,%.0f" % p for p in P), col, op)

def finger(x, y, ang, lens, ws, skin, shade, light, nail=True):
    """ang in degrees, 0 = pointing down (+y). bends: list of angle changes per joint."""
    out = []; pts = [(x, y)]; a = ang
    for L, da in lens:
        a += da
        x += math.sin(math.radians(a)) * L; y += math.cos(math.radians(a)) * L; pts.append((x, y))
    out.append(taper(pts, ws[0], ws[1], skin))
    # shadow side
    sp = [(px - 0.22 * ws[0] * math.cos(math.radians(ang)), py + 0.0) for px, py in pts]
    out.append(taper(sp, ws[0] * 0.35, ws[1] * 0.3, shade, 0.7))
    # knuckle creases
    for px, py in pts[1:-1]:
        out.append('<ellipse cx="%.0f" cy="%.0f" rx="%.0f" ry="2.5" fill="%s" opacity="0.6" transform="rotate(%.0f %.0f %.0f)"/>' % (px, py, ws[0] * 0.35, shade, -a, px, py))
    # fingertip pad catching bounce
    out.append('<circle cx="%.0f" cy="%.0f" r="%.1f" fill="%s" opacity="0.9"/>' % (pts[-1][0], pts[-1][1], ws[1] * 0.42, light))
    return out, pts

def build(path):
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1600">']
    sx, sy = 540, 450
    s.append('<defs><radialGradient id="g" cx="%d" cy="%d" r="760" gradientUnits="userSpaceOnUse">'
             '<stop offset="0" stop-color="#ffffff" stop-opacity="1"/><stop offset="0.16" stop-color="#ffffff" stop-opacity="0.97"/>'
             '<stop offset="0.38" stop-color="#f6f9dc" stop-opacity="0.8"/><stop offset="0.6" stop-color="#e4ecb0" stop-opacity="0.2"/>'
             '<stop offset="1" stop-color="#d6e09a" stop-opacity="0"/></radialGradient></defs>' % (sx, sy))
    s.append('<rect x="0" y="0" width="1200" height="1600" fill="url(#g)"/>')
    # the black sun: the burnt afterimage in the eye, with a hard acid fringe
    s.append('<circle cx="%d" cy="%d" r="74" fill="#d8f040" opacity="0.9"/>' % (sx, sy))
    s.append('<circle cx="%d" cy="%d" r="64" fill="#1a1428"/>' % (sx, sy))
    s.append('<circle cx="%d" cy="%d" r="40" fill="#0c0a14"/>' % (sx, sy))
    # rays of glare
    for k in range(28):
        a = k * 2 * math.pi / 28 + 0.07 * (k % 3)
        r0, r1 = 82, 170 + 90 * ((k * 7) % 5) / 4
        s.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#ffffff" stroke-width="%d" stroke-linecap="round" opacity="0.9"/>'
                 % (sx + math.cos(a) * r0, sy + math.sin(a) * r0, sx + math.cos(a) * r1, sy + math.sin(a) * r1, 6 + (k % 3) * 4))
    # top-right figure is cobalt (replaces the yellow): keep the 3D, just remove yellow by nothing here
    # HEADS (cx,cy,scale,rot: chin points toward the body)
    s += head(350, 285, 1.25, 160, "#8a5a44", "#4a3028", "#c87a42", "#120e0c")          # top-left, upside down
    s += head(880, 95, 1.1, 190, "#9a6a50", "#5a3a2c", "#d08a50", "#1c140e")            # top, upside down
    s += head(1010, 400, 1.15, 250, "#c09070", "#7a5a40", "#e0a060", "#c0a060")          # right, blond, chin to the right
    s += head(905, 680, 1.15, 290, "#6a4030", "#3a2218", "#a8603a", "#0a0808")           # right lower
    s += head(445, 790, 1.35, -12, "#8a5a44", "#2e1e18", "#c47040", "#0e0c0a")           # black-coat man
    s += head(735, 880, 1.4, 14, "#c08a6a", "#5a3628", "#e88a50", "#3a1a0c", mouth="open", hang=7)  # red woman, hair hanging
    # PHONE held down at us from the top figure
    s.append('<g transform="translate(760 300) rotate(18)">'
             '<rect x="-42" y="-78" width="84" height="156" rx="12" fill="#0a0a0e"/>'
             '<rect x="-36" y="-72" width="72" height="144" rx="9" fill="#1c2030"/>'
             '<circle cx="-20" cy="-56" r="9" fill="#2a3a5a"/><circle cx="-20" cy="-56" r="4" fill="#e8f4ff"/>'
             '</g>')
    s.append(taper([(830, 160), (800, 220), (780, 260)], 54, 46, "#9a6a50"))
    s.append(taper([(722, 250), (712, 270)], 22, 18, "#b07a5a"))
    s.append(taper([(800, 250), (812, 286)], 22, 18, "#b07a5a"))
    # FOCAL OPEN HAND (red woman), palm toward us, coming down at the viewer
    s.append(taper([(930, 1000), (870, 1110), (800, 1180)], 120, 98, "#a8150c"))       # sleeve
    s.append(taper([(812, 1165), (790, 1190)], 100, 92, "#7a0e08"))                      # cuff shadow
    skin, shade, light = "#d89a74", "#8a4e38", "#f4c8a0"
    s.append('<path d="M720,1175 C680,1200 670,1260 684,1310 C696,1350 750,1372 812,1362 C858,1352 884,1300 874,1245 C864,1195 800,1160 720,1175 Z" fill="%s"/>' % skin)
    s.append('<path d="M688,1240 C684,1290 700,1335 740,1358 C712,1320 702,1280 706,1240 Z" fill="%s" opacity="0.6"/>' % shade)
    s.append('<path d="M836,1205 C866,1240 872,1290 852,1330 C878,1300 880,1240 858,1212 Z" fill="%s" opacity="0.8"/>' % light)
    s.append('<path d="M716,1262 C750,1280 800,1282 846,1262" stroke="%s" stroke-width="3" fill="none" opacity="0.6"/>' % shade)
    s.append('<path d="M730,1300 C770,1312 810,1310 840,1296" stroke="%s" stroke-width="2.5" fill="none" opacity="0.5"/>' % shade)
    for x, y, ang, lens, ws in [
        (694, 1322, -40, [(40, 0), (30, 6), (24, 8)], (28, 22)),    # little, splayed
        (728, 1352, -18, [(52, 0), (36, 4), (28, 6)], (33, 26)),    # ring
        (774, 1364, 0, [(58, 0), (40, 2), (30, 3)], (36, 28)),     # middle
        (822, 1356, 20, [(52, 0), (38, -3), (28, -4)], (34, 27)),   # index
    ]:
        f, _ = finger(x, y, ang, lens, ws, skin, shade, light); s += f
    f, _ = finger(866, 1270, 66, [(48, -8), (40, -14), (30, -10)], (42, 30), skin, shade, light); s += f  # thumb out to the right
    # PULSE FINGERS (black-coat man): dark, backlit, two fingers extended toward the bottom edge (our throat)
    s.append(taper([(250, 1000), (300, 1200), (360, 1330)], 130, 104, "#0e1014"))       # sleeve
    s.append(taper([(340, 1320), (365, 1345)], 110, 104, "#d8dcd4"))                      # shirt cuff, glare-lit
    sk2, sh2, li2 = "#7a4a34", "#3a2218", "#c88050"
    s.append('<path d="M330,1350 C320,1400 340,1450 380,1470 C420,1480 450,1450 450,1410 C452,1370 420,1340 380,1335 Z" fill="%s"/>' % sk2)
    s.append('<path d="M335,1360 C330,1400 345,1440 372,1460" stroke="%s" stroke-width="10" fill="none" opacity="0.7"/>' % sh2)
    s.append('<path d="M440,1380 C452,1410 448,1445 430,1465" stroke="%s" stroke-width="6" fill="none" opacity="0.9"/>' % li2)
    for x, y, ang, lens, ws in [(392, 1462, 22, [(60, 0), (46, 2), (34, 4)], (30, 22)),
                                (425, 1448, 34, [(62, 0), (48, 2), (34, 4)], (30, 22))]:
        f, _ = finger(x, y, ang, lens, ws, sk2, sh2, li2); s += f
    for x, y in [(360, 1462), (343, 1440)]:                                                 # curled fingers: knuckles only
        s.append('<ellipse cx="%d" cy="%d" rx="17" ry="13" fill="%s"/>' % (x, y, sk2))
        s.append('<ellipse cx="%d" cy="%d" rx="9" ry="5" fill="%s" opacity="0.9"/>' % (x + 4, y + 6, li2))
    s.append('</svg>')
    open(path, 'w').write("\n".join(s))

if __name__ == "__main__":
    build('/home/claude/v13/overlay_P2.svg')
