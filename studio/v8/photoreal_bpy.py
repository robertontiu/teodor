"""Runs inside the Python that has Blender's `bpy` wheel (tools/setup_photoreal.py), never in the studio's own
Python. Reads <base>.json and <base>.npz written by photoreal.export, builds the scene for Cycles, renders the
beauty image and a coverage pass, and writes <base>_beauty.npy and <base>_ids.npy (linear float, top row first).

Material values: measured ones cite their source in photoreal.py; the procedural micro-relief and colour amounts are
judgements tuned by eye and against the close-up ruler (docs/research/hyperrealism-gaps.md, G1 second part)."""
import json
import math
import sys
import time

import bpy
import numpy as np

base = sys.argv[-1]
meta = json.load(open(base + ".json"))
ARR = np.load(base + ".npz")
W, H = meta["W"], meta["H"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
cy = sc.cycles
cy.device = "CPU"
cy.samples = meta["samples"]
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.02
cy.use_denoising = meta["denoise"]
cy.max_bounces = 12
cy.diffuse_bounces = 3
cy.glossy_bounces = 4
cy.transmission_bounces = 12
cy.transparent_max_bounces = 16
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.sample_clamp_indirect = 8.0
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "32"
if meta.get("region"):
    # render only this part of the frame (x0, y0, x1, y1 as fractions, y from the top), the rest left empty
    x0, y0, x1, y1 = meta["region"]
    sc.render.use_border = True
    sc.render.use_crop_to_border = False
    sc.render.border_min_x, sc.render.border_max_x = x0, x1
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1, 1 - y0
if meta.get("threads"):
    sc.render.threads_mode = "FIXED"
    sc.render.threads = meta["threads"]
try:
    sc.cycles_curves.shape = "THICK"
    sc.cycles_curves.subdivisions = 2
except Exception:
    pass

# ------------------------------------------------------------------ node helpers
class G:
    def __init__(self, mat):
        self.nt = mat.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def inp(self, n, key, v):
        s = n.inputs[key]
        if hasattr(v, "is_output") or hasattr(v, "links"):
            self.link(v, s)
        else:
            s.default_value = v

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.inp(n, i, v)
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.node("ShaderNodeVectorMath", operation=op)
        self.inp(n, 0, a)
        if b is not None:
            self.inp(n, 1, b)
        if scale is not None:
            self.inp(n, "Scale", scale)
        return n.outputs[1] if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs[0]

    def attr(self, name, kind="Fac"):
        n = self.node("ShaderNodeAttribute", attribute_name=name)
        return n.outputs[{"Fac": "Fac", "Vector": "Vector", "Color": "Color"}[kind]]

    def smooth(self, e0, e1, x):
        n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        self.inp(n, "Value", x)
        self.inp(n, "From Min", e0)
        self.inp(n, "From Max", e1)
        return n.outputs["Result"]

    def mix(self, a, b, t, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.inp(n, "Factor", t)
        self.inp(n, 6, a)
        self.inp(n, 7, b)
        return n.outputs[2]

    def combine(self, x, y, z):
        n = self.node("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.inp(n, i, v)
        return n.outputs[0]

    def sep(self, v):
        n = self.node("ShaderNodeSeparateXYZ")
        self.inp(n, 0, v)
        return n.outputs


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m


def principled(g):
    b = g.node("ShaderNodeBsdfPrincipled")
    out = g.node("ShaderNodeOutputMaterial")
    g.link(b.outputs[0], out.inputs["Surface"])
    return b, out


# ------------------------------------------------------------------ materials
def skin_material(pm):
    mat = new_mat("skin")
    g = G(mat)
    b, out = principled(g)
    try:
        b.subsurface_method = "RANDOM_WALK_SKIN"
    except Exception:
        b.subsurface_method = "RANDOM_WALK"
    rest = g.attr("rest", "Vector")
    face = g.attr("face")
    det = pm["detail"]
    seed = float(pm["seed"])
    rs = g.vmath("ADD", rest, (seed * 0.37, seed * 0.11, seed * 0.23))
    # --- pores: pits around the feature points of a 3D Voronoi field cut by the surface. A surface meets a pit of
    # radius r round points of density 1/c^3 per volume at 2r/c^3 per area, so cells of c = 1.25 mm with pit radii of
    # 0.25-0.43 mm give about 30-45 pits per cm2 (Flament et al. 2015: 10-90 per cm2 on the cheek, areas 0.06-0.37
    # mm2), their cut radii mostly 0.1-0.35 mm; present in 85% of cells on the face, 40% on the body [S + H]
    vor = g.node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
    g.inp(vor, "Vector", rs)
    g.inp(vor, "Scale", 800.0)
    g.inp(vor, "Randomness", 1.0)
    rnd = g.sep(vor.outputs["Color"])
    rr = g.math("MULTIPLY_ADD", rnd[0], 0.14, 0.2)                # sphere radius in cell units: 0.25-0.43 mm
    pit = g.math("SUBTRACT", 1.0, g.smooth(0.0, 1.0, g.math("DIVIDE", vor.outputs["Distance"], rr)))
    present = g.math("LESS_THAN", rnd[1], g.math("MULTIPLY_ADD", face, 0.45, 0.4))
    pit = g.math("MULTIPLY", g.math("POWER", pit, 1.5), present)
    # --- the micro-relief's furrows: ridged noise (lines where a smooth noise crosses its mean), two octaves, cells of
    # about 0.6 and 0.3 mm (the skin's tertiary and secondary lines; scale by eye [H])
    def ridge(scale, w, k):
        nz = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
        g.inp(nz, "Vector", g.vmath("ADD", rs, (k, 2 * k, 3 * k)))
        g.inp(nz, "Scale", scale)
        g.inp(nz, "Detail", 1.0)
        g.inp(nz, "Roughness", 0.5)
        d = g.math("ABSOLUTE", g.math("SUBTRACT", nz.outputs["Fac"], 0.5))
        return g.math("SUBTRACT", 1.0, g.smooth(0.0, w, d))
    # line widths about 0.1-0.15 mm: thinner lines than a pixel only add noise that the samples average away [H]
    fur = g.math("ADD", ridge(1300.0, 0.12, 1.7), g.math("MULTIPLY", ridge(2600.0, 0.12, 5.3), 0.5))
    # --- wrinkles of age: horizontal forehead lines about 9 mm apart, crow's feet radiating from the outer corners,
    # fine lines under the eyes; deeper with age (masks from photoreal.py; spacing and depth by eye [H])
    age = pm["age"]
    agef = max(0.0, min(1.0, (age - 25) / 40))
    zz = g.sep(rest)[2]
    warp = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(warp, "Vector", rs)
    g.inp(warp, "Scale", 60.0)
    g.inp(warp, "Detail", 2.0)
    ph = g.math("MULTIPLY_ADD", warp.outputs["Fac"], 0.9, g.math("DIVIDE", zz, 0.009))
    fl = g.math("POWER", g.math("MULTIPLY_ADD", g.math("COSINE", g.math("MULTIPLY", ph, 2 * math.pi)), 0.5, 0.5), 10.0)
    fl = g.math("MULTIPLY", fl, g.attr("fh"))
    ang = g.attr("crow_a")
    cf = g.math("POWER", g.math("MULTIPLY_ADD", g.math("COSINE", g.math("MULTIPLY_ADD", warp.outputs["Fac"], 1.2, g.math("MULTIPLY", ang, 9.0))), 0.5, 0.5), 8.0)
    cf = g.math("MULTIPLY", cf, g.attr("crow"))
    wr = g.math("ADD", fl, cf)
    xx = g.sep(rest)[0]
    lipl = g.math("POWER", g.math("MULTIPLY_ADD", g.math("COSINE", g.math("MULTIPLY", g.math("MULTIPLY_ADD", warp.outputs["Fac"], 0.0006, xx), 2 * math.pi / 0.0012)), 0.5, 0.5), 6.0)
    lipl = g.math("MULTIPLY", lipl, g.attr("lips"))
    wr = g.math("ADD", wr, g.math("MULTIPLY", lipl, 0.5 / max(agef, 0.2)))
    # --- the height (m) and the bump
    dp = 0.0001 * det           # pore depth 100 um, by eye against the ruler [H]
    df = 0.00004 * det * (0.7 + 0.6 * agef)
    dw = 0.00012 * det * agef
    h = g.math("MULTIPLY", pit, -dp)
    h = g.math("MULTIPLY_ADD", fur, -df, h)
    h = g.math("MULTIPLY_ADD", wr, -dw, h)
    # the soft swell between pores, small (a large swell read as orange peel in part one) [H]
    sw = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(sw, "Vector", rs)
    g.inp(sw, "Scale", 400.0)
    g.inp(sw, "Detail", 2.0)
    h = g.math("MULTIPLY_ADD", sw.outputs["Fac"], 0.000012 * det, h)
    h = g.math("MULTIPLY", h, g.attr("skin"))
    bump = g.node("ShaderNodeBump")
    g.inp(bump, "Height", h)
    g.inp(bump, "Distance", 1.0)
    g.inp(bump, "Strength", 1.0)
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    # --- colour: the vertex colour, mottled (blood and melanin at 3-20 mm), redder where the blood runs, the shaved
    # beard's cool shadow, a few small moles and age spots, the pits a little darker [H]
    col = g.attr("col", "Vector")
    mot = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(mot, "Vector", rs)
    g.inp(mot, "Scale", 120.0)
    g.inp(mot, "Detail", 4.0)
    g.inp(mot, "Roughness", 0.6)
    mf = g.math("MULTIPLY_ADD", mot.outputs["Fac"], 0.24, 0.88)
    mot2 = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(mot2, "Vector", g.vmath("ADD", rs, (3.1, 1.7, 0.4)))
    g.inp(mot2, "Scale", 35.0)
    g.inp(mot2, "Detail", 2.0)
    blood = g.math("MULTIPLY", g.math("ADD", g.attr("red"), g.math("MULTIPLY", g.math("SUBTRACT", mot2.outputs["Fac"], 0.45), 0.6)), 1.0, clamp=True)
    c = g.mix(col, g.vmath("MULTIPLY", col, (1.0, 0.78, 0.80)), g.math("MULTIPLY", blood, 0.35))
    c = g.vmath("SCALE", c, scale=mf)
    c = g.mix(c, g.vmath("MULTIPLY", col, (0.62, 0.66, 0.74)), g.math("MULTIPLY", g.attr("beard"), 0.55 * min(1.0, pm["beard"] / 0.6)))
    c = g.mix(c, g.vmath("MULTIPLY", col, (0.80, 0.74, 0.78)), g.math("MULTIPLY", g.attr("orbit"), 0.5))
    oli = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(oli, "Vector", g.vmath("ADD", rs, (5.5, 0.3, 2.2)))
    g.inp(oli, "Scale", 18.0)
    c = g.mix(c, g.vmath("MULTIPLY", col, (0.97, 0.95, 0.82)), g.math("MULTIPLY", g.smooth(0.4, 0.7, oli.outputs["Fac"]), 0.5))
    # the shaved beard's follicles: a dark dot per hair, under the skin (the cut stubble shows as dots) [H]
    fol = g.node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
    g.inp(fol, "Vector", g.vmath("ADD", rs, (1.1, 4.4, 2.7)))
    g.inp(fol, "Scale", 900.0)
    fd = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(0.12, 0.3, fol.outputs["Distance"])), g.attr("beard"))
    c = g.mix(c, g.vmath("MULTIPLY", col, (0.35, 0.33, 0.36)), g.math("MULTIPLY", fd, 0.6 * min(1.0, pm["beard"] / 0.6)))
    mole = g.node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
    g.inp(mole, "Vector", g.vmath("ADD", rs, (7.3, 2.2, 9.1)))
    g.inp(mole, "Scale", 70.0)
    mr = g.sep(mole.outputs["Color"])
    ms = g.math("MULTIPLY", g.math("LESS_THAN", mr[0], 0.035 + 0.02 * agef),
                g.math("SUBTRACT", 1.0, g.smooth(0.03, 0.06 + 0.05 * 1.0, mole.outputs["Distance"])))
    c = g.mix(c, g.vmath("MULTIPLY", col, (0.55, 0.45, 0.40)), g.math("MULTIPLY", ms, g.math("MULTIPLY", g.attr("face"), 0.7)))
    c = g.vmath("SCALE", c, scale=g.math("MULTIPLY_ADD", pit, -0.12 * det, 1.0))
    g.link(c, b.inputs["Base Color"])
    # --- subsurface: Jensen's skin, in metres
    skin = g.attr("skin")
    g.inp(b, "Subsurface Weight", skin)
    g.inp(b, "Subsurface Radius", (3.67, 1.37, 0.68))
    g.inp(b, "Subsurface Scale", 0.001)
    g.inp(b, "IOR", 1.38)
    # --- the sheen: a broad lobe of roughness about 0.45 everywhere (Weyrich's fits put skin's Torrance-Sparrow m at
    # 0.3-0.45), the oily T-zone and lips smoother and with an oily coat, wet lid margins wetter [S + H]
    tz, lips, wet = g.attr("tz"), g.attr("lips"), g.attr("wet")
    rn = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(rn, "Vector", rs)
    g.inp(rn, "Scale", 250.0)
    rough = g.math("SUBTRACT", 0.44, g.math("MULTIPLY", tz, 0.08))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", lips, 0.18))
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", wet, 0.35))
    rough = g.math("MULTIPLY_ADD", rn.outputs["Fac"], 0.12, g.math("SUBTRACT", rough, 0.06))
    rough = g.math("MAXIMUM", rough, 0.08)
    g.link(rough, b.inputs["Roughness"])
    oil = pm["oil"]
    coat = g.math("MULTIPLY", g.math("MULTIPLY_ADD", tz, 0.3 * oil, 0.04 * oil), skin)
    coat = g.math("ADD", coat, g.math("MULTIPLY", lips, 0.2))
    coat = g.math("MAXIMUM", coat, g.math("MULTIPLY", wet, 0.9))
    # the oil sits as droplets in the micro-relief, so its film breaks over the pores [H]
    coat = g.math("MULTIPLY", coat, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", pit, 0.8)))
    g.link(coat, b.inputs["Coat Weight"])
    g.inp(b, "Coat Roughness", 0.2)
    g.inp(b, "Coat IOR", 1.46)
    try:
        b.inputs["Coat Normal"]
        g.link(bump.outputs["Normal"], b.inputs["Coat Normal"])
    except Exception:
        pass
    return mat


def cloth_material():
    mat = new_mat("cloth")
    g = G(mat)
    b, out = principled(g)
    g.link(g.attr("col", "Color"), b.inputs["Base Color"])
    g.inp(b, "Roughness", 0.85)
    g.inp(b, "Sheen Weight", 0.4)
    # a weave at 0.4 mm and a slow crumple: by eye [H]
    nz = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(nz, "Scale", 60.0)
    g.inp(nz, "Detail", 6.0)
    bump = g.node("ShaderNodeBump")
    g.inp(bump, "Height", nz.outputs["Fac"])
    g.inp(bump, "Strength", 0.15)
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def simple_material(name, col, rough, sss=0.0, coat=0.0):
    mat = new_mat(name)
    g = G(mat)
    b, out = principled(g)
    g.inp(b, "Base Color", tuple(col) + (1.0,))
    g.inp(b, "Roughness", rough)
    if sss:
        g.inp(b, "Subsurface Weight", sss)
        g.inp(b, "Subsurface Scale", 0.001)
    if coat:
        g.inp(b, "Coat Weight", coat)
        g.inp(b, "Coat Roughness", 0.05)
    return mat


def eye_material(pm, R_mm):
    """The eyeball: sclera and the recessed iris in the eye's own unit frame (z the axis); a tear film coat."""
    mat = new_mat("eye")
    g = G(mat)
    b, out = principled(g)
    tc = g.node("ShaderNodeTexCoord")
    p = tc.outputs["Object"]
    x, y, z = g.sep(p)
    rxy = g.vmath("LENGTH", g.combine(x, y, 0.0))
    E = meta_eye
    ri = E["iris_r_mm"] / R_mm
    rp = E["pupil_r_mm"] / R_mm
    front = g.math("GREATER_THAN", z, 0.5)
    iris = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(ri - 0.012, ri + 0.004, rxy)), front)
    pupil = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(rp - 0.008, rp + 0.006, rxy)), front)
    # iris: radial fibres (noise stretched along the radius), a lighter collarette, a dark limbal ring [H]
    ang = g.math("ARCTAN2", y, x)
    nz = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(nz, "Vector", g.combine(g.math("MULTIPLY", g.math("SINE", ang), 2.0), g.math("MULTIPLY", g.math("COSINE", ang), 2.0), g.math("MULTIPLY", rxy, 2.5)))
    g.inp(nz, "Scale", 9.0)
    g.inp(nz, "Detail", 6.0)
    g.inp(nz, "Roughness", 0.65)
    fib = g.math("MULTIPLY_ADD", nz.outputs["Fac"], 1.6, 0.55)
    coll = g.math("SUBTRACT", 1.0, g.smooth(0.0, 0.05, g.math("ABSOLUTE", g.math("SUBTRACT", rxy, rp + 0.09))))
    limb = g.smooth(ri * 0.82, ri, rxy)
    # a brown iris reflects about 10-20% (its colour from the scene is a display value, darker than its albedo) [H]
    ic = g.vmath("SCALE", tuple(pm["iris"]), scale=g.math("MULTIPLY", fib, 2.2))
    ic = g.mix(ic, g.vmath("SCALE", tuple(pm["iris"]), scale=1.8), g.math("MULTIPLY", coll, 0.5))
    ic = g.mix(ic, (0.012, 0.01, 0.01, 1), g.math("MULTIPLY", limb, 0.75))
    # sclera: off-white, pinker and veined toward the corners (away from the axis) [H]
    vn = g.node("ShaderNodeTexNoise", noise_dimensions="3D")
    g.inp(vn, "Vector", p)
    g.inp(vn, "Scale", 14.0)
    g.inp(vn, "Detail", 8.0)
    veins = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(0.0, 0.04, g.math("ABSOLUTE", g.math("SUBTRACT", vn.outputs["Fac"], 0.5)))),
                   g.smooth(0.75, 0.25, z))
    scl = g.mix(tuple(pm["sclera"]) + (1,), (0.55, 0.22, 0.2, 1), g.math("MULTIPLY", veins, 0.35))
    scl = g.mix(scl, (0.62, 0.42, 0.38, 1), g.math("MULTIPLY", g.smooth(0.6, 0.1, z), 0.35))
    c = g.mix(scl, ic, iris)
    c = g.mix(c, (0.006, 0.005, 0.005, 1), pupil)
    g.link(c, b.inputs["Base Color"])
    g.inp(b, "Roughness", 0.3)
    g.link(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, iris), 0.25), b.inputs["Subsurface Weight"])
    g.inp(b, "Subsurface Scale", 0.0005)
    # the tear film over the sclera (the cornea is its own glass) [H]
    g.link(g.math("SUBTRACT", 1.0, iris), b.inputs["Coat Weight"])
    g.inp(b, "Coat Roughness", 0.04)
    return mat


def glass_material(name, ior, shadow_pass=1.0):
    """Clear glass (the cornea, water) that lets shadow rays through (Cycles traces no caustics: without this the
    iris under a cornea and the skin under a drop would lie in their own shadow)."""
    mat = new_mat(name)
    g = G(mat)
    b = g.node("ShaderNodeBsdfPrincipled")
    g.inp(b, "Transmission Weight", 1.0)
    g.inp(b, "Roughness", 0.0)
    g.inp(b, "IOR", ior)
    g.inp(b, "Base Color", (1, 1, 1, 1))
    tr = g.node("ShaderNodeBsdfTransparent")
    lp = g.node("ShaderNodeLightPath")
    mx = g.node("ShaderNodeMixShader")
    g.link(g.math("MULTIPLY", lp.outputs["Is Shadow Ray"], shadow_pass), mx.inputs[0])
    g.link(b.outputs[0], mx.inputs[1])
    g.link(tr.outputs[0], mx.inputs[2])
    out = g.node("ShaderNodeOutputMaterial")
    g.link(mx.outputs[0], out.inputs["Surface"])
    return mat


def hair_material(name, mel, grey, redness=0.45, rough=0.32):
    """Chiang et al. 2016's hair BSDF (Cycles' Principled Hair), by melanin; a share `grey` of the strands white
    (Panhard et al. 2012's greying by age, through figure.GREY)."""
    mat = new_mat(name)
    g = G(mat)
    h = g.node("ShaderNodeBsdfHairPrincipled")
    try:
        h.parametrization = "MELANIN"
    except Exception:
        pass
    hi = g.node("ShaderNodeHairInfo")
    isg = g.math("LESS_THAN", hi.outputs["Random"], grey)
    m = g.math("MULTIPLY_ADD", isg, 0.03 - mel, mel)
    g.link(m, h.inputs["Melanin"])
    g.inp(h, "Melanin Redness", redness)
    g.inp(h, "Roughness", rough)
    g.inp(h, "Radial Roughness", 0.3)
    g.inp(h, "Random Color", 0.12)
    g.inp(h, "Random Roughness", 0.15)
    try:
        g.inp(h, "Coat", 0.0)
    except Exception:
        pass
    out = g.node("ShaderNodeOutputMaterial")
    g.link(h.outputs[0], out.inputs["Surface"])
    return mat


def id_material(name, rgb):
    mat = new_mat(name)
    g = G(mat)
    e = g.node("ShaderNodeEmission")
    g.inp(e, "Color", tuple(rgb) + (1,))
    g.inp(e, "Strength", 1.0)
    out = g.node("ShaderNodeOutputMaterial")
    g.link(e.outputs[0], out.inputs["Surface"])
    return mat


# ------------------------------------------------------------------ geometry
def link(obj):
    sc.collection.objects.link(obj)
    return obj


def mesh_obj(name, V, F, attrs=None, smooth=True, subdiv=0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in f) for f in F])
    me.update()
    if smooth:
        me.shade_smooth() if hasattr(me, "shade_smooth") else [setattr(p, "use_smooth", True) for p in me.polygons]
    for k, v in (attrs or {}).items():
        v = np.asarray(v, np.float32)
        if v.ndim == 1:
            a = me.attributes.new(k, "FLOAT", "POINT")
            a.data.foreach_set("value", v)
        else:
            a = me.attributes.new(k, "FLOAT_VECTOR", "POINT")
            a.data.foreach_set("vector", v.reshape(-1))
    ob = link(bpy.data.objects.new(name, me))
    if subdiv:
        md = ob.modifiers.new("sub", "SUBSURF")
        md.levels = subdiv
        md.render_levels = subdiv
    return ob


def curves_obj(name, pts, cnt, radius, taper):
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([int(c) for c in cnt])
    cv.position_data.foreach_set("vector", np.asarray(pts, np.float32).reshape(-1))
    # radius tapering from the root to the tip
    rad = np.concatenate([radius * (1 - (1 - taper) * np.linspace(0, 1, int(c)) ** 1.5) for c in cnt]).astype(np.float32)
    ra = cv.attributes.get("radius") or cv.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", rad)
    return link(bpy.data.objects.new(name, cv))


def uv_sphere(nu=96, nv=64):
    th = np.linspace(0, np.pi, nv + 1)
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    V = [(0, 0, 1)]
    for t in th[1:-1]:
        for p in ph:
            V.append((math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t)))
    V.append((0, 0, -1))
    V = np.array(V)
    F = []
    for j in range(nu):
        F.append((0, 1 + j, 1 + (j + 1) % nu))
    for i in range(nv - 2):
        a, b_ = 1 + i * nu, 1 + (i + 1) * nu
        for j in range(nu):
            F.append((a + j, b_ + j, b_ + (j + 1) % nu, a + (j + 1) % nu))
    last = len(V) - 1
    a = 1 + (nv - 2) * nu
    for j in range(nu):
        F.append((a + (j + 1) % nu, a + j, last))
    return V, F


def place(ob, c, R, s):
    import mathutils
    M = mathutils.Matrix(np.asarray(R).tolist()).to_4x4()
    M.translation = mathutils.Vector(c)
    ob.matrix_world = M @ mathutils.Matrix.Diagonal((s[0], s[1], s[2], 1.0))


meta_eye = dict(sclera_mm=11.5, cornea_r_mm=7.8, apex_mm=12.5, iris_r_mm=5.85, pupil_r_mm=1.75, chamber_mm=3.1)

# ------------------------------------------------------------------ build
t0 = time.time()
id_mats = dict(skin=id_material("id_skin", (1, 0, 0)), hair=id_material("id_hair", (0, 1, 0)), cloth=id_material("id_cloth", (0, 0, 1)),
               face_hair=id_material("id_fh", (1, 0, 0)))
swap = []        # (object, material slot index, id material)
for i, pm in enumerate(meta["people"]):
    pre = f"p{i}_"
    V = ARR[pre + "V"]
    Q = ARR[pre + "Q"]
    names = [k[len(pre) + 2:] for k in ARR.files if k.startswith(pre + "a_")]
    at = {k: ARR[pre + "a_" + k] for k in names}
    # wrinkle masks (rest coordinates of the person, Blender axes: x, y = -z, z = y): forehead and crow's feet [H]
    rest = at["rest"] / pm["scale"]
    rx, ry, rz = rest[:, 0], -rest[:, 1], rest[:, 2]        # back to the base mesh's (x, y up, z forward)
    face = at["face"]
    sm = lambda e0, e1, x: np.clip((x - e0) / (e1 - e0), 0, 1) ** 2 * (3 - 2 * np.clip((x - e0) / (e1 - e0), 0, 1))
    at["fh"] = (sm(0.752, 0.762, rz) * sm(0.80, 0.785, rz) * sm(0.045, 0.03, np.abs(rx)) * face).astype(np.float32)
    cx, cz = 0.047, 0.727
    dx, dz = np.abs(rx) - cx, rz - cz
    rr = np.hypot(dx, dz)
    at["crow"] = (np.exp(-(rr / 0.011) ** 2) * sm(0.002, 0.005, dx) * face).astype(np.float32)
    at["crow_a"] = np.arctan2(dz, np.maximum(dx, 1e-4)).astype(np.float32)
    cloth_f = at["cloth"][Q].mean(1) > 0.5
    ob = mesh_obj(f"person{i}", V, Q, at, subdiv=2)
    ms, mc = skin_material(pm), cloth_material()
    ob.data.materials.append(ms)
    ob.data.materials.append(mc)
    mi = np.where(cloth_f, 1, 0).astype(np.int32)
    ob.data.polygons.foreach_set("material_index", mi)
    swap.append((ob, [id_mats["skin"], id_mats["cloth"]]))
    for part, col, rough, sss in (("teeth", (0.78, 0.72, 0.6), 0.25, 0.3), ("tongue", (0.5, 0.16, 0.15), 0.35, 0.6)):
        F = ARR[pre + part]
        used = np.unique(F)
        remap = -np.ones(len(V), np.int64)
        remap[used] = np.arange(len(used))
        o2 = mesh_obj(f"{part}{i}", V[used], remap[F], subdiv=1)
        o2.data.materials.append(simple_material(part, col, rough, sss))
        swap.append((o2, [id_mats["skin"]]))
    # eyes: the sclera sphere at the size that fills the lids; the cornea (7.8 mm radius of curvature) meets it at the
    # limbus, 5.85 mm from the axis; the iris a flat disc 3.1 mm behind the corneal apex (Gullstrand / Atchison &
    # Smith) [S]; sizes in mm, then in units of this eyeball's radius
    Vs, Fs = uv_sphere()
    E = meta_eye
    R_mm = pm["eyes"][0]["r"] * 1000.0 if pm["eyes"] else E["sclera_mm"]
    z_l = math.sqrt(max(R_mm ** 2 - E["iris_r_mm"] ** 2, 1.0))
    d_c = z_l - math.sqrt(E["cornea_r_mm"] ** 2 - E["iris_r_mm"] ** 2)
    apex = d_c + E["cornea_r_mm"]
    zi = (apex - E["chamber_mm"]) / R_mm
    Ve = Vs.copy()
    ri = E["iris_r_mm"] / R_mm
    rxy = np.hypot(Ve[:, 0], Ve[:, 1])
    flat = (Ve[:, 2] > zi) & (rxy < ri * 1.12)
    Ve[flat, 2] = zi + 0.012 * (1 - (rxy[flat] / ri) ** 2)        # the iris bulges a little toward the pupil [H]
    emat, cmat = eye_material(pm, R_mm), glass_material("cornea", 1.376)
    for j, e in enumerate(pm["eyes"]):
        oe = mesh_obj(f"eye{i}{j}", Ve, Fs)
        place(oe, e["c"], e["R"], (e["r"],) * 3)
        oe.data.materials.append(emat)
        swap.append((oe, [id_mats["skin"]]))
        rc = E["cornea_r_mm"] / R_mm
        off = d_c / R_mm
        Vc = Vs * rc + np.array([0, 0, off])
        oc = mesh_obj(f"cornea{i}{j}", Vc, Fs)
        place(oc, e["c"], e["R"], (e["r"],) * 3)
        oc.data.materials.append(cmat)
        swap.append((oc, [id_mats["skin"]]))
    # strands
    kinds = {}
    for s in pm["strands"]:
        pts, cnt = ARR[s["key"] + "_pts"], ARR[s["key"] + "_cnt"]
        oh = curves_obj(s["key"], pts, cnt, s["radius"], s["taper"])
        k = s["kind"]
        if k not in kinds:
            if k == "hair":
                kinds[k] = hair_material("hair", pm["mel_hair"], pm["grey"])
            elif k == "lash":
                kinds[k] = hair_material("lash", min(0.97, pm["mel_brow"] + 0.1), 0.0, rough=0.35)
            elif k == "brow":
                kinds[k] = hair_material("brow", pm["mel_brow"], pm["grey"] * 0.5)
            else:
                kinds[k] = hair_material("stubble", pm["mel_hair"], pm["grey"])
        oh.data.materials.append(kinds[k])
        swap.append((oh, [id_mats["hair"] if k == "hair" else id_mats["face_hair"]]))
    if pm.get("droplets"):
        wm = glass_material("water", 1.333, 0.7)
        C, N_, Rr = ARR[pre + "drop_c"], ARR[pre + "drop_n"], ARR[pre + "drop_r"]
        Vd, Fd = uv_sphere(32, 20)
        for j in range(len(C)):
            n = N_[j] / np.linalg.norm(N_[j])
            a = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
            a /= np.linalg.norm(a)
            bb = np.cross(n, a)
            od = mesh_obj(f"drop{i}_{j}", Vd, Fd)
            place(od, C[j], np.stack([a, bb, n], 1), (Rr[j], Rr[j], Rr[j] * 0.6))
            od.data.materials.append(wm)
            swap.append((od, [id_mats["skin"]]))

# camera
import mathutils
cm = meta["cam"]
cam = bpy.data.cameras.new("cam")
cam.sensor_fit = "VERTICAL"
aspect = W / H
cam.sensor_height = 43.27 / math.sqrt(1 + aspect * aspect)      # the 35 mm-equivalent frame (scene.SENSOR_DIAG_MM)
cam.sensor_width = cam.sensor_height * aspect
cam.lens = cam.sensor_height / 2 / math.tan(meta["fov"] / 2)
cam.clip_start = 0.05
if meta.get("focus") and meta.get("fstop"):
    cam.dof.use_dof = True
    cam.dof.focus_distance = meta["focus"]
    cam.dof.aperture_fstop = meta["fstop"]
co = link(bpy.data.objects.new("cam", cam))
Rm = np.stack([np.array(cm["rt"]), np.array(cm["up"]), -np.array(cm["fw"])], 1)
M = mathutils.Matrix(Rm.tolist()).to_4x4()
M.translation = mathutils.Vector(cm["pos"])
co.matrix_world = M
sc.camera = co

# sun: Blender's sun shines along its local -z
s = meta["sun"]
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = s["strength"]
sun.color = s["color"]
sun.angle = math.radians(s["angle"])
so = link(bpy.data.objects.new("sun", sun))
z = np.array(s["dir"]); z /= np.linalg.norm(z)
x = np.cross([0, 0, 1.0], z) if abs(z[2]) < 0.99 else np.array([1.0, 0, 0])
x /= np.linalg.norm(x)
y = np.cross(z, x)
so.matrix_world = mathutils.Matrix(np.stack([x, y, z], 1).tolist()).to_4x4()
for j, L in enumerate(meta["lights"]):
    pl = bpy.data.lights.new(f"pt{j}", "POINT")
    pl.energy = L["power"]
    pl.color = L["color"]
    po = link(bpy.data.objects.new(f"pt{j}", pl))
    po.location = L["pos"]

# world: the ambient sky above, the ground's bounce below
w = bpy.data.worlds.new("world")
sc.world = w
try:
    w.use_nodes = True
except Exception:
    pass
nt = w.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
wo = meta["world"]
tc = nt.nodes.new("ShaderNodeTexCoord")
sx = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sx.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.3
mr.inputs["From Max"].default_value = 0.4
nt.links.new(sx.outputs[2], mr.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMix")
mx.data_type = "RGBA"
nt.links.new(mr.outputs["Result"], mx.inputs["Factor"])
mx.inputs[6].default_value = tuple(wo["ground"]) + (1,)
mx.inputs[7].default_value = tuple(wo["sky"]) + (1,)
bg = nt.nodes.new("ShaderNodeBackground")
nt.links.new(mx.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = wo["strength"]
ow = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(bg.outputs[0], ow.inputs["Surface"])
print(f"photoreal: scene built in {time.time() - t0:.1f} s", flush=True)


def render_to(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    px = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(H, W, 4)[::-1]


t1 = time.time()
beauty = render_to(base + "_beauty.exr")
np.save(base + "_beauty.npy", beauty)
print(f"photoreal: beauty {W}x{H} at {meta['samples']} samples in {time.time() - t1:.0f} s", flush=True)
# the coverage pass: every surface an emission of its class
for ob, mats in swap:
    for k, m in enumerate(mats):
        if k < len(ob.data.materials):
            ob.data.materials[k] = m
cy.samples = 16
cy.use_denoising = False
cy.use_adaptive_sampling = False
sun.energy = 0.0
bg.inputs["Strength"].default_value = 0.0
t2 = time.time()
ids = render_to(base + "_ids.exr")
np.save(base + "_ids.npy", ids)
print(f"photoreal: coverage pass in {time.time() - t2:.0f} s", flush=True)
