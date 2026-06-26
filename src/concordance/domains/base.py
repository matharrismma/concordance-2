"""Domain validators — the FLOOR-layer attestation checks.

A domain validator checks the author's *affirmations* (did they attest the
constraints their domain requires) — distinct from a verifier, which checks the
*artifact* (does the math actually hold). Attestation lives on FLOOR; verification
lives on RED.

Most domains have no validator (verification on RED carries the weight); the loader
returns None for those, and the engine treats that as a pass-through. The registry
grows as domain validators port (see PORT_PLAN.md). Ported from 1.0; the registry
starts empty in 2.0 — secular domain validators mount here as they land.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional, Protocol, Tuple, Type, runtime_checkable

from ..packet import GateResult


@runtime_checkable
class DomainValidator(Protocol):
    domain: str

    def validate_red(self, packet: Dict[str, Any]) -> List[GateResult]: ...

    def validate_floor(self, packet: Dict[str, Any]) -> List[GateResult]: ...


# Domain name (canonical or alias) -> (module path, class name). Lazy import on
# first hit. Empty for now — domain validators port here as they land.
_DOMAIN_VALIDATOR_REGISTRY: Dict[str, Tuple[str, str]] = {}

_LOADED_VALIDATOR_CLASSES: Dict[str, Type] = {}


def load_domain_validator(domain: str) -> Optional[DomainValidator]:
    """Resolve a domain to a fresh validator instance, or None if unregistered.

    O(1) lookup, lazy import on first hit, class cached thereafter."""
    domain = (domain or "").lower()
    cls = _LOADED_VALIDATOR_CLASSES.get(domain)
    if cls is not None:
        return cls()
    entry = _DOMAIN_VALIDATOR_REGISTRY.get(domain)
    if entry is None:
        return None
    module_path, class_name = entry
    cls = getattr(importlib.import_module(module_path), class_name)
    _LOADED_VALIDATOR_CLASSES[domain] = cls
    return cls()
