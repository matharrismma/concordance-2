"""EngineConfig — one engine, one foundation, two surfaces.

The biblical foundation is load-bearing on BOTH surfaces (the truth-model, the
disciplines, Scripture in the substrate; Christ at the center). `surface` selects
ONLY what is surfaced to the user: the identity, the provenance layers, and whether
the witness verifiers/routers are exposed. It is not a switch that adds or removes
the foundation — the foundation is always there.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import branding, layers

SURFACES: tuple[str, ...] = ("secular", "witness")


@dataclass(frozen=True)
class EngineConfig:
    """The configuration of one engine face.

    secular -> the .com reach (no religious wording surfaced)
    witness -> the .org witness (the foundation surfaced explicitly)
    """

    surface: str = "secular"

    def __post_init__(self) -> None:
        if self.surface not in SURFACES:
            raise ValueError(f"surface must be one of {SURFACES}, got {self.surface!r}")

    @property
    def identity(self) -> str:
        """The identity string surfaced to a user of this face."""
        return branding.identity_for(self.surface)

    @property
    def source_layers(self) -> tuple[str, ...]:
        """The provenance layers surfaced on this face."""
        return layers.layers_for(self.surface)

    @property
    def witness_surfaced(self) -> bool:
        """Whether the scripture/theology/witness verifiers and routers are surfaced.

        False on the secular reach. The FOUNDATION is present and load-bearing
        regardless; this only governs what the surface exposes.
        """
        return self.surface == "witness"
