"""The medium interface. A medium is the studio's "instrument": the paint's physics, its tools,
its support and how it looks. The core (studio.py) only knows this interface.

Every medium keeps `cv.col`, the canvas's current apparent colour (H, W, 3, reflectance 0..1),
because looking, matching and the critic's views work on it. Anything else a medium needs
(wetness, water, pigment in suspension, paper height, impasto height...) it declares in
`arrays` and reads and writes as `cv.<name>`; the core saves and loads them.

To add a medium: write media/<name>.py with a Medium subclass, register it in media/__init__.py,
add its entry to studio/media.json and document it in docs/MANUAL.md.
"""
import os
import numpy as np
from scipy.ndimage import gaussian_filter


def hx(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def _ks(R):
    R = np.clip(R, 0.003, 0.997)
    return (1 - R) ** 2 / (2 * R)


def _unks(k):
    return 1 + k - np.sqrt(k * k + 2 * k)


def kmix(a, b, t):
    """Pigment mixing: Kubelka-Munk (per channel) blended with a little linear mixing
    so that tints with white stay luminous."""
    km = _unks(_ks(a) * (1 - t) + _ks(b) * t)
    lin = a * (1 - t) + b * t
    return (0.58 * km + 0.42 * lin).astype(np.float32)


def noise_field(h, w, sigma, seed):
    rng = np.random.default_rng(seed)
    n = gaussian_filter(rng.random((h, w)).astype(np.float32), sigma)
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


class Medium:
    name = "base"
    arrays = ("col",)            # per-pixel state saved with the canvas (float16 on disk)
    tools = {}                   # tool id -> one-line description (shown in the manual)
    supports = {}                # support id -> description; the first is the default
    finishes = {}                # finish op id -> one-line description

    # --- canvas life
    def texture(self, h, w, support):
        """The support's surface (0..1), used for tooth, grain and absorbency."""
        return noise_field(h, w, 0.8, 7)

    def init_state(self, cv, ground):
        """Fill the medium's arrays for a fresh canvas. cv.col is already the ground colour."""
        for a in self.arrays:
            if a != "col":
                setattr(cv, a, np.zeros((cv.H, cv.W), np.float32))

    # --- the hand's contact with the surface
    def make_tool(self, it, size, color, rng):
        """Return an object with .dab(cv, x, y, ang, press, rscale) and the attributes the core
        sets while playing a stroke (.size, .step, .speedfx, optional .liner)."""
        raise NotImplementedError

    def glaze(self, cv, mask, col, op, it=None):
        """A thin transparent layer over the masked area (it: the whole intention, for extra parameters)."""
        cv.col = kmix(cv.col, col[None, None, :], (mask * op)[..., None])

    # --- time
    def episode_end(self, cv):
        """What happens between episodes (drying, flowing, settling)."""

    def dry(self, cv, amount):
        """Let time pass: amount 0..1 of the way to fully dry."""

    # --- seeing
    def render(self, cv):
        """Return a PIL image of the canvas as it looks (lighting, sheen, support)."""
        raise NotImplementedError

    # --- revision: taking paint away (core intentions scrape, wipe, paintout; studio.py do_revise)
    glaze_role = "glaze"         # the layer role a `glaze` intention lays in this medium (wash, glaze, body...)
    revision_tools = {}          # op -> a tool id of this medium the core sweeps over the region for that op

    def revise(self, cv, op, mask, it, felt, rng, core):
        """Take paint away in the masked region (op: scrape | wipe | paintout). Return True when done, or
        NotImplemented to let the core fall back (revision_tools, an eraser/knife/rag tool, a finishing step of
        the same name, then its default). Raise SystemExit with a clear reason when the medium can't do it."""
        return NotImplemented

    # hand_defaults(it, kind) -> dict may be defined: defaults the core merges under an intention before it runs
    # (the intention's own keys win), e.g. {"articulation": "plain", "role_scale": False} for tools calibrated on the
    # plain stroke (ink's line tools). A tool may also set `.wave = 0` to opt out of the core's slow pressure wave.

    # --- the detail pass (detail.py; docs/MANUAL.md "Detail pass")
    # In a detail opened at N x, cv.px_scale is N and the core passes `_px_scale` in the intention to make_tool. A
    # medium whose tools and render keep their physical features at that scale (bristle clumps, hairs, grain, edge
    # widths and blur radii in canvas px times px_scale) sets detail_scale_aware = True; the others still work in a
    # detail (all arrays are resampled, the support's texture keeps its size) but their inner textures are finer.
    detail_scale_aware = False

    # finish_check(cv) -> (lines, flags) may be defined by a medium for `report finish` (docs/FINISHING.md);
    # without it the core runs its own default checks.

    # --- the last stage
    def finish(self, cv, op, params):
        """Finishing operations particular to the medium (varnish, fixative...)."""
        raise SystemExit(f"{self.name} has no finishing step '{op}'. Available: {', '.join(self.finishes) or 'none'}")


# ---------------------------------------------------------------- transparent films (Kubelka-Munk layers)
def pigment(over_white, over_black):
    """Absorption K and scattering S per channel (for unit thickness) from a pigment's appearance as a
    film over white and over black (Curtis et al. 1997, section 5.2). Both are RGB arrays 0..1;
    over_black must be darker than over_white. A transparent pigment is nearly black over black; an
    opaque one looks almost the same over both."""
    Rw = np.clip(np.asarray(over_white, np.float64), 0.02, 0.98)
    Rb = np.clip(np.asarray(over_black, np.float64), 0.005, None)
    Rb = np.minimum(Rb, Rw - 0.01)
    a = 0.5 * (Rw + (Rb - Rw + 1) / Rb)
    b = np.sqrt(np.maximum(a * a - 1, 1e-9))
    x = (b * b - (a - Rw) * (a - 1)) / (b * (1 - Rw))
    x = np.maximum(x, 1 + 1e-6)
    S = (1 / b) * 0.5 * np.log((x + 1) / (x - 1))
    K = S * (a - 1)
    return K.astype(np.float32), S.astype(np.float32)


def pigment_from_hex(color, opacity=0.3):
    """A convenient pigment from one colour: opacity 0 = a pure transparent dye, 1 = fully opaque.
    Over black it shows as color * opacity * 0.9 (a judgement call, not a measurement)."""
    w = hx(color) if isinstance(color, str) else np.asarray(color, np.float32)
    return pigment(w, np.clip(w * (0.04 + 0.86 * opacity), 0.005, None))


def km_layer(R0, K, S, x):
    """Composite a pigment film of thickness x (H, W) with constants K, S (3,) over a substrate of
    reflectance R0 (H, W, 3), using the Kubelka-Munk layer equations: the film's own reflectance
    R = sinh(bSx)/c and transmittance T = b/c, then R_total = R + T^2 R0 / (1 - R R0)."""
    K = np.asarray(K, np.float32); S = np.maximum(np.asarray(S, np.float32), 1e-4)
    x = np.maximum(np.asarray(x, np.float32), 0)[..., None]
    a = (S + K) / S
    b = np.sqrt(np.maximum(a * a - 1, 1e-6))
    bSx = np.minimum(b * S * x, 30)
    sh, ch = np.sinh(bSx), np.cosh(bSx)
    c = a * sh + b * ch
    R = sh / c
    T = b / c
    R0 = np.clip(R0, 0, 1)
    return np.clip(R + T * T * R0 / (1 - R * R0 + 1e-6), 0, 1).astype(np.float32)


# ---------------------------------------------------------------- the measured pigment library
_PIGMENTS = None


def load_pigments():
    """studio/pigments.json (measured pigments with provenance; docs/media-data.md), searched next to the
    studio (a work dir made by tools/make_brief.py) and in the repo's studio/ folder. Returns the list."""
    global _PIGMENTS
    if _PIGMENTS is None:
        here = os.path.dirname(os.path.abspath(__file__))
        for c in (os.path.join(here, "..", "pigments.json"), os.path.join(here, "..", "..", "pigments.json")):
            if os.path.exists(c):
                import json
                _PIGMENTS = json.load(open(c))["pigments"]
                break
        else:
            _PIGMENTS = []
    return _PIGMENTS


def find_pigment(key):
    """A pigment by Colour Index name (e.g. 'PB27') or by name (e.g. 'Prussian blue'), case-insensitive."""
    k = key.lower()
    for p in load_pigments():
        if (p.get("ci") or "").lower() == k or (p.get("name") or "").lower() == k:
            return p
    return None
