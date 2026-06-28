"""Packet validation + canonical hashing helpers.

Uses jsonschema when installed; falls back to a minimal structural check
(required fields, top-level type, unrecognized keys) so the core stays
sovereign — it runs with zero non-stdlib deps. Ported as-is from 1.0.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None
    _HAS_JSONSCHEMA = False


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """THE one canonical JSON form for the whole floor: sorted keys, tight separators,
    ensure_ascii=False. ensure_ascii=False is load-bearing — Greek/Hebrew (the witness
    surface) stays human-readable in stored seals AND hashes identically everywhere. A
    content-addressed integrity system must have exactly one canonical form; this is it."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_hash(obj: Any, *, exclude: tuple = ()) -> str:
    """The canonical SHA-256 used across CAS, records, and the ledger. `exclude` drops
    self-referential dict keys (e.g. content_hash, permanent_ref) so the hash is stable."""
    if exclude and isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if k not in exclude}
    return sha256_bytes(canonical_json_bytes(obj))


def load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


# The schema ships INSIDE the package so it is always present (wheel or source); the RED
# malformed-input gate is only real if the schema actually loads.
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "packet.schema.json"
_SCHEMA_CACHE: Dict[str, Any] = {}
_SCHEMA_WARNED: set = set()


def resolve_schema(schema_path=None):
    """Load the packet schema (cached), or None. A missing schema is LOUD (logged once) —
    a silently-off RED gate is an integrity hole, so its absence must be visible."""
    key = str(schema_path or DEFAULT_SCHEMA_PATH)
    if key in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[key]
    try:
        schema = load_schema(Path(key))
    except (OSError, ValueError) as e:
        import logging
        if key not in _SCHEMA_WARNED:
            logging.getLogger("concordance").warning(
                "RED schema gate INACTIVE: cannot load packet schema at %s (%s) — "
                "malformed-input validation is OFF", key, e)
            _SCHEMA_WARNED.add(key)
        schema = None
    _SCHEMA_CACHE[key] = schema
    return schema


def schema_active(schema_path=None, skip: bool = False) -> bool:
    """True iff malformed-input validation will actually run (schema present + not skipped)."""
    return (not skip) and resolve_schema(schema_path) is not None


def _fallback_validate(packet: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Minimal structural validation when jsonschema is absent."""
    errors: List[str] = []
    for r in schema.get("required", []):
        if r not in packet:
            errors.append(f"missing required field: {r!r}")
    if schema.get("type") == "object" and not isinstance(packet, dict):
        errors.append(f"top-level must be object, got {type(packet).__name__}")
    if schema.get("additionalProperties") is False and isinstance(packet, dict):
        properties = set(schema.get("properties", {}).keys())
        for k in packet.keys():
            if k not in properties:
                errors.append(f"unrecognized key: {k!r}")
    if errors:
        raise ValueError("schema validation failed: " + "; ".join(errors))


def validate_against_schema(packet: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate packet against schema (jsonschema if available, else structural)."""
    if _HAS_JSONSCHEMA:
        jsonschema.validate(instance=packet, schema=schema)
    else:
        _fallback_validate(packet, schema)


def compute_packet_hash(packet: Dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(packet))
