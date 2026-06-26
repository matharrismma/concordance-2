"""Source layers — who or what stands behind a sealed claim.

The foundation is shared on both surfaces. What differs is which provenance layers
are *surfaced* to the user. The secular reach uses generic provenance tiers; the
witness surface surfaces the biblical layers explicitly. This is a SURFACE choice,
never a change to the foundation.
"""
from __future__ import annotations

# The secular reach (.com): generic, domain-neutral provenance tiers.
SECULAR_LAYERS: tuple[str, ...] = ("primary", "secondary", "tertiary", "reference")

# The witness surface (.org): the biblical source layers, surfaced explicitly.
WITNESS_LAYERS: tuple[str, ...] = ("jesus_words", "bible", "apostles", "recognized_elders")


def layers_for(surface: str) -> tuple[str, ...]:
    """Return the source layers surfaced for this surface."""
    return WITNESS_LAYERS if surface == "witness" else SECULAR_LAYERS
