"""Identity, injected per surface — never hardcoded at import.

The foundation (the Bible, Christ at the center) is the same under both surfaces.
The IDENTITY string is only what is *surfaced* to the user of that face: the `.com`
reaches the world in its own language; the `.org` names the Rock. Neither denies
the foundation — the secular reach simply does not surface it, and openly links to
the witness.
"""
from __future__ import annotations

# The reach (.com): the world's own language — truth, verification, a receipt.
SECULAR_IDENTITY = (
    "A deterministic verification engine. It checks what is true and hands you a receipt "
    "you can re-verify — a verdict, the worked reasoning, and a permanent content-addressed "
    "seal. It eliminates what is not the answer so that what survives stands on its own."
)

# The witness (.org): the same engine, foundation made plain.
WITNESS_IDENTITY = (
    "Concordance / Narrow Highway serves Jesus Christ. The same engine, with its foundation "
    "made plain: it verifies, keeps, and points — a conduit, not the source. It eliminates "
    "what is not the answer so the narrow path is illuminated by what survives. Good fruit is "
    "the measure. Christ is at the center; the foundation is the Word."
)


def identity_for(surface: str) -> str:
    """Return the identity surfaced for this surface."""
    return WITNESS_IDENTITY if surface == "witness" else SECULAR_IDENTITY
