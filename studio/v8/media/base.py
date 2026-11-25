"""The medium interface. A medium is the studio's "instrument": the paint's physics, its tools,
its support and how it looks. The core (studio.py) only knows this interface.

Every medium keeps `cv.col`, the canvas's current apparent colour (H, W, 3, reflectance 0..1),
because looking, matching and the critic's views work on it. Anything else a medium needs
(wetness, water, pigment in suspension, paper height, impasto height...) it declares in
`arrays` and reads and writes as `cv.<name>`; the core saves and loads them.

To add a medium: write media/<name>.py with a Medium subclass, register it in media/__init__.py,
add its entry to studio/media.json and document it in docs/MANUAL.md.
"""
import numpy as np
from scipy.ndimage import gaussian_filter


def hx(h):
    h = h.lstrip("#")
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

    def glaze(self, cv, mask, col, op):
        """A thin transparent layer over the masked area."""
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

    # --- the last stage
    def finish(self, cv, op, params):
        """Finishing operations particular to the medium (varnish, fixative...)."""
        raise SystemExit(f"{self.name} has no finishing step '{op}'. Available: {', '.join(self.finishes) or 'none'}")
