"""EngineConfig — one engine, one foundation, two surfaces + run settings.

The biblical foundation is load-bearing on BOTH surfaces (the truth-model, the
disciplines, Scripture in the substrate; Christ at the center). `surface` selects
ONLY what is surfaced to the user: the identity, the provenance layers, and whether
the witness verifiers/routers are exposed. It does not add or remove the foundation.

The run settings (run_verifiers, skip_schema_validation, default_scope, schema_path)
configure how the engine executes a packet — folded into the one config object so a
caller wires a single thing (the watch discipline: fewer parts).
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
    run_verifiers: bool = True
    skip_schema_validation: bool = False
    default_scope: str = "local"
    schema_path: str = ""

    def __post_init__(self) -> None:
        if self.surface not in SURFACES:
            raise ValueError(f"surface must be one of {SURFACES}, got {self.surface!r}")

    # ── surface seam ─────────────────────────────────────────────────────

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
