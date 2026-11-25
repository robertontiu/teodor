"""The studio's media ("instruments"). Every module in this folder that defines a Medium subclass
with a `name` is registered automatically, so media can be added in parallel without editing a
shared list. Oil is first (the default)."""
import importlib, inspect, os
from .base import Medium

MEDIA = {}
_here = os.path.dirname(os.path.abspath(__file__))
_order = ["oil"] + sorted(f[:-3] for f in os.listdir(_here)
                          if f.endswith(".py") and f[:-3] not in ("__init__", "base", "oil"))
for _mod in _order:
    try:
        m = importlib.import_module(f".{_mod}", __name__)
    except ModuleNotFoundError:
        continue
    for _, cls in inspect.getmembers(m, inspect.isclass):
        if issubclass(cls, Medium) and cls is not Medium and cls.__module__ == m.__name__ and getattr(cls, "name", "base") != "base":
            MEDIA[cls.name] = cls()


def get_medium(name):
    if name not in MEDIA:
        raise SystemExit(f"Unknown medium '{name}'. Available: {', '.join(MEDIA)}")
    return MEDIA[name]
