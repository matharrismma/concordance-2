"""Core movement test — the going-train base: packet, gates, record, CAS.

Proves: a verdict assembles into a sealed WitnessRecord; the record round-trips
through JSON; the content-hash is reproducible; the CAS stores/fetches/verifies
by hash; and an Anchor takes a generic provenance layer (no hardcoded enum), so
seals are structurally identical on both surfaces. Runnable with `pytest` OR
directly with `python tests/test_core.py`.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import cas  # noqa: E402
from concordance.gates import ok, reject  # noqa: E402
from concordance.packet import EngineResult  # noqa: E402
from concordance.record import Anchor, WitnessRecord, build_record  # noqa: E402
from concordance.verifiers.base import confirm  # noqa: E402


def _sample_record(layer: str = "primary") -> WitnessRecord:
    er = EngineResult(overall="PASS", gate_results=[ok("RED"), ok("FLOOR"), ok("PATH")])
    return build_record(
        engine_result=er,
        verifier_results=(confirm("verify_arithmetic", "2+2=4", {"lhs": 4, "rhs": 4}),),
        anchors=(Anchor(ref="primary source 1", layer=layer),),
        packet_id="pkt_test_1",
    )


def test_record_builds_and_seals():
    rec = _sample_record()
    d = rec.to_dict()
    assert d["overall"] == "PASS"
    assert "content_hash" in d and len(d["content_hash"]) == 64
    assert "final_answer" not in d and "answer" not in d  # the engine never answers


def test_record_roundtrips():
    rec = _sample_record()
    again = WitnessRecord.from_dict(rec.to_dict())
    # content_hash is stable across a to_dict/from_dict/to_dict round trip
    assert again.to_dict()["content_hash"] == rec.to_dict()["content_hash"]


def test_content_hash_is_deterministic():
    assert _sample_record().to_dict()["content_hash"] == _sample_record().to_dict()["content_hash"]


def test_anchor_layer_is_generic():
    # secular layer and witness layer both valid at the schema level (str, not enum)
    secular = _sample_record(layer="reference").to_dict()
    witness = _sample_record(layer="jesus_words").to_dict()
    assert secular["anchors"][0]["layer"] == "reference"
    assert witness["anchors"][0]["layer"] == "jesus_words"
    # structurally identical seals; only the layer value differs
    assert set(secular["anchors"][0].keys()) == set(witness["anchors"][0].keys())


def test_cas_store_fetch_verify_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        d = _sample_record().to_dict()
        h = cas.store(d, base_dir=base)
        assert h == d["content_hash"]
        assert cas.exists(h, base_dir=base)
        fetched = cas.fetch(h, base_dir=base)
        assert fetched is not None and fetched["overall"] == "PASS"
        good, detail = cas.verify(h, base_dir=base)
        assert good, detail


def test_reject_gate_is_hard_failure():
    er = EngineResult(overall="REJECT", gate_results=[reject("RED", "contradicted")])
    rec = build_record(engine_result=er)
    assert not rec.passed
    assert rec.hard_gate_failures and rec.hard_gate_failures[0].gate == "RED"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} core tests passed — the going-train base seals true.")
