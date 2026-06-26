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
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


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
