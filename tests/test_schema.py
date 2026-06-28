"""The RED schema gate is real — malformed input is rejected, and its status is visible.

Before this, no schema file existed, so the RED malformed-input guarantee was a silent
no-op on every install. Now the schema ships inside the package, a packet missing its
domain is rejected at RED (works with OR without jsonschema, via the sovereign structural
fallback), and /health reports schema_active so a silently-off gate is impossible to miss.
Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, validate_packet  # noqa: E402
from concordance import validate  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402


def test_schema_ships_inside_the_package_and_is_active():
    assert validate.DEFAULT_SCHEMA_PATH.is_file(), "schema must ship inside the package"
    assert validate.resolve_schema() is not None
    assert validate.schema_active() is True
    assert validate.schema_active(skip=True) is False


def test_malformed_packet_rejected_at_red():
    # missing the required 'domain' -> RED reject (jsonschema if present, else structural fallback)
    er = validate_packet({"created_epoch": 1, "COMB_VERIFY": {}}, now_epoch=1, config=EngineConfig())
    assert er.overall == "REJECT"
    reds = [g for g in er.gate_results if g.gate == "RED" and g.status == "REJECT"]
    assert reds and any("schema" in " ".join(g.reasons).lower() for g in reds)


def test_non_object_packet_rejected():
    er = validate_packet([], now_epoch=1, config=EngineConfig())  # a list is not a packet
    assert er.overall == "REJECT"


def test_valid_packet_not_rejected_for_schema_reasons():
    er = validate_packet({"domain": "combinatorics", "created_epoch": 1}, now_epoch=1, config=EngineConfig())
    schema_fail = [g for g in er.gate_results
                   if g.gate == "RED" and any("schema validation failed" in r for r in g.reasons)]
    assert not schema_fail  # a well-formed packet never fails the schema gate


def test_health_reports_schema_active():
    st, payload = dispatch("GET", "/health", {}, None, EngineConfig("secular"))
    assert st == 200 and payload["schema_active"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} schema tests passed — the RED malformed-input gate is real + visible.")
