"""The studio's media ("instruments"). Register new media here."""
from .oil import Oil

MEDIA = {m.name: m for m in (Oil(),)}


def get_medium(name):
    if name not in MEDIA:
        raise SystemExit(f"Unknown medium '{name}'. Available: {', '.join(MEDIA)}")
    return MEDIA[name]
