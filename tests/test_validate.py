"""validate.py — the one canonicalizer + the schema resolver + the sovereign fallback.

These are integrity-core: the canonical form, the content hash, and the structural
validation that backs the RED gate when jsonschema is absent. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import validate  # noqa: E402


def test_canonical_is_sorted_tight_and_raw_utf8():
    assert validate.canonical_json_bytes({"b": 1, "a": "x"}) == b'{"a":"x","b":1}'
    assert "ἀγάπη".encode("utf-8") in validate.canonical_json_bytes({"k": "ἀγάπη"})  # raw, not \u-escaped


def test_content_hash_excludes_named_fields():
    h1 = validate.content_hash({"x": 1, "content_hash": "zzz", "permanent_ref": "p"},
                               exclude=("content_hash", "permanent_ref"))
    h2 = validate.content_hash({"x": 1})
    assert h1 == h2
    assert validate.compute_packet_hash({"a": 1}) == validate.sha256_bytes(validate.canonical_json_bytes({"a": 1}))


def test_resolve_schema_missing_is_none_and_cached():
    bad = str(Path(tempfile.gettempdir()) / "nh-no-such-schema-xyz.json")
    assert validate.resolve_schema(bad) is None
    assert validate.resolve_schema(bad) is None      # second call hits the cache (warns once)
    assert validate.schema_active(bad) is False
    assert validate.schema_active() is True           # the shipped default schema is present
    assert validate.schema_active(skip=True) is False


def test_fallback_validate_required_type_and_additional():
    schema = {"type": "object", "required": ["domain"], "properties": {"domain": {"type": "string"}}}
    _raises(lambda: validate._fallback_validate({}, schema))                 # missing required
    validate._fallback_validate({"domain": "math"}, schema)                  # valid -> no raise
    _raises(lambda: validate._fallback_validate(["not", "object"], schema))  # wrong top-level type
    strict = {**schema, "additionalProperties": False}
    _raises(lambda: validate._fallback_validate({"domain": "math", "extra": 1}, strict))  # unknown key


def test_validate_against_schema_backend_agnostic():
    schema = {"type": "object", "required": ["domain"]}
    _raises(lambda: validate.validate_against_schema({}, schema))   # jsonschema OR fallback rejects
    validate.validate_against_schema({"domain": "x"}, schema)       # valid passes either way


def _raises(fn):
    try:
        fn()
    except Exception:
        return
    raise AssertionError("expected an exception")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} validate tests passed — canonical form, schema resolver, fallback.")
