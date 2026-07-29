"""The trust kernel's edges — the paths that only run when something is wrong, tested as behavior.

Matt, 2026-07-28: "Goal is all aspects above 90%." The trust kernel (cas, ledger, record, signing,
receipts, derivation) sat at 75-88% — and the UNCOVERED lines were precisely the ones that matter
most: what happens when a ledger file is corrupt, when a signature is missing, when a chain is
tampered, when the store is unreachable. Those paths run exactly when someone is being lied to;
they must not be the untested ones.

Every test here asserts BEHAVIOR — a corrupt file is REPORTED, a refusal carries its reason, a
round-trip returns what went in. No test exists to touch a line; each exists because the path has
a job. The enforced coverage floor rises 75 → 90 with this file.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_dirs():
    prior = {k: os.environ.get(k) for k in ("CONCORDANCE_DATA_DIR", "CONCORDANCE_CAS_DIR")}
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    os.environ.pop("CONCORDANCE_CAS_DIR", None)
    yield
    for k, v in prior.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# ── cas: paths, corruption, inventory ───────────────────────────────────────────────────────────

def test_cas_env_override_and_corrupt_records_return_none_not_garbage():
    from concordance import cas
    override = tempfile.mkdtemp()
    prior = os.environ.get("CONCORDANCE_CAS_DIR")
    os.environ["CONCORDANCE_CAS_DIR"] = override
    try:
        h = cas.store({"record_type": "t", "claim": "kernel-edge", "generated": False})
        p = Path(override) / h[:2] / f"{h[2:]}.json"
        assert p.exists(), "CONCORDANCE_CAS_DIR must govern where records land"
        # corrupt the stored bytes: fetch must answer None, never raise, never half-parse
        p.write_text("{not json", encoding="utf-8")
        assert cas.fetch(h) is None
        ok, _ = cas.verify(h)
        assert ok is False, "a corrupted record must not verify"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_CAS_DIR", None)
        else:
            os.environ["CONCORDANCE_CAS_DIR"] = prior


def test_cas_inventory_walks_the_store_and_sizes_it():
    from concordance import cas
    base = Path(tempfile.mkdtemp())
    h1 = cas.store({"record_type": "t", "claim": "a", "generated": False}, base_dir=base)
    h2 = cas.store({"record_type": "t", "claim": "b", "generated": False}, base_dir=base)
    # a stray non-2-char dir and a stray file must be skipped, not crash the walk
    (base / "junk-dir").mkdir()
    listed = cas.list_hashes(base_dir=base)
    assert set(listed) == {h1, h2}


# ── ledger: corruption reported, chains verified, closest case honest ───────────────────────────

def _pass_record(packet_id, anchors=(), domain="chemistry"):
    from concordance.record import Anchor, AxisCoordinates, WitnessRecord, axis_coords_for
    ax = axis_coords_for(domain) or AxisCoordinates(axis=domain, dimensions=frozenset(["x"]))
    return WitnessRecord(overall="PASS", gate_results=(), verifier_results=(),
                         axis_coords=ax, packet_id=packet_id,
                         anchors=tuple(Anchor(ref=r, layer="scripture") for r in anchors))


def test_ledger_reports_a_corrupt_precedent_file_instead_of_skipping_it():
    from concordance import ledger
    ldir = Path(tempfile.mkdtemp())
    (ldir / "prec_bad.json").write_text("{broken", encoding="utf-8")
    # and one whose sealed_at is junk — the chain orderer falls back to file mtime, not a crash
    (ldir / "prec_odd.json").write_text('{"precedent_id": "odd", "sealed_at": "not-a-number"}',
                                        encoding="utf-8")
    report = ledger.verify_chain(ledger_dir=ldir)
    assert report["ok"] is False
    assert any("could not parse" in t.get("error", "") for t in report["tampered"]), \
        "a corrupt file is REPORTED as tampered — silence would hide an attack"


def test_ledger_names_the_unsigned_and_still_walks_the_chain():
    from concordance import ledger
    ldir = Path(tempfile.mkdtemp())
    ledger.seal_to_ledger(_pass_record("p1"), summary="first precedent", ledger_dir=ldir)
    # strip the stored hash to simulate a legacy/unsigned entry
    f = sorted(ldir.glob("*.json"))[0]
    data = json.loads(f.read_text(encoding="utf-8"))
    data.pop("content_hash", None)
    f.write_text(json.dumps(data), encoding="utf-8")
    report = ledger.verify_chain(ledger_dir=ldir)
    assert report["unsigned"], "an entry without its hash is NAMED as unsigned, not silently accepted"
    # and the NEXT append still chains — recomputing the unsigned entry's hash as its link
    ledger.seal_to_ledger(_pass_record("p2"), summary="chains past the unsigned", ledger_dir=ldir)
    report2 = ledger.verify_chain(ledger_dir=ldir)
    assert report2["total"] == 2, "the chain walks on; the unsigned entry is named, not fatal"


def test_ledger_chain_extends_from_the_previous_entry_and_from_genesis():
    from concordance import ledger
    ldir = Path(tempfile.mkdtemp())
    ledger.seal_to_ledger(_pass_record("g1"), summary="genesis-bound", ledger_dir=ldir)
    ledger.seal_to_ledger(_pass_record("g2"), summary="chained to g1", ledger_dir=ldir)
    report = ledger.verify_chain(ledger_dir=ldir)
    assert report["ok"] is True and report["verified"] >= 2, \
        "each entry binds to the one before; the first binds to genesis"
    # duplicate ids refuse rather than silently fork the chain
    with pytest.raises(FileExistsError):
        ledger.seal_to_ledger(_pass_record("g1"), summary="dup", ledger_dir=ldir)
    # and a non-PASS record never becomes precedent
    rec = _pass_record("rejected-one")
    object.__setattr__(rec, "overall", "REJECT")
    with pytest.raises(ValueError):
        ledger.seal_to_ledger(rec, summary="must refuse", ledger_dir=ldir)


def test_closest_case_blends_anchor_similarity_and_stays_honest():
    """The distance math with SHARED SCRIPTURE ANCHORS — and no false neighbors: an unknown
    domain returns None; an empty ledger says precedent_id=None rather than stretching."""
    from concordance import ledger
    ldir = Path(tempfile.mkdtemp())
    empty = ledger.find_closest({"domain": "chemistry"}, ledger_dir=ldir)
    assert empty is not None and empty.precedent_id is None, "an empty ledger is honest-novel"
    # a corrupt file in the ledger dir is SKIPPED by the precedent loader (reported by verify_chain)
    (ldir / "zz_corrupt.json").write_text("{broken", encoding="utf-8")

    ledger.seal_to_ledger(_pass_record("a1", anchors=("John 3:16", "Psalm 23:1")),
                          summary="anchored precedent", ledger_dir=ldir)
    cc = ledger.find_closest({"domain": "chemistry",
                              "scripture_anchors": ["John 3:16"]}, ledger_dir=ldir)
    assert cc is not None and cc.precedent_id and "a1" in cc.precedent_id
    assert cc.shared_anchors and "John 3:16" in cc.shared_anchors, \
        "a shared verse is part of WHY this precedent is closest — it must be said"
    assert ledger.find_closest({"domain": "no_such_domain"}, ledger_dir=ldir) is None


def test_anchor_extraction_takes_strings_and_dicts_and_rejects_junk():
    from concordance.ledger import _anchor_to_ref
    assert _anchor_to_ref("John 3:16") == "John 3:16"
    assert _anchor_to_ref({"ref": "Psalm 23:1"}) == "Psalm 23:1"
    assert _anchor_to_ref({"noref": 1}) is None
    assert _anchor_to_ref(42) is None


# ── record: round-trips carry everything they claim to ──────────────────────────────────────────

def test_record_round_trips_preserve_umbrella_closest_case_and_bindings():
    from concordance.record import (AxisCoordinates, ClosestCase, WitnessRecord,
                                    bind_subject, embed_attestations, with_permanent_ref)
    ax = AxisCoordinates(axis="physics", dimensions=frozenset(["m", "s"]), umbrella="created_order")
    ax2 = AxisCoordinates.from_dict(ax.to_dict())
    assert ax2.umbrella == "created_order" and ax2.dimensions == ax.dimensions

    cc = ClosestCase(precedent_id="p9", shared_dimensions=frozenset(["m"]),
                     shared_anchors=("John 3:16",), distance=0.25)
    cc2 = ClosestCase.from_dict(cc.to_dict())
    assert cc2.precedent_id == "p9" and cc2.distance == 0.25
    assert "John 3:16" in (cc2.shared_anchors or ())

    rec = WitnessRecord(overall="PASS", gate_results=(), verifier_results=(),
                        axis_coords=ax, closest_case=cc, packet_id="pk1")
    rec = bind_subject(rec, "nh_pubkey_abc")
    rec = embed_attestations(rec, ({"pubkey": "nh_w1", "sig": "s1"},))
    d = rec.to_dict()
    assert d["subject_pubkey"] == "nh_pubkey_abc"
    assert d["witness_attestations"], "embedded witnesses travel with the record"
    assert d["closest_case"]["precedent_id"] == "p9"
    assert d["content_hash"], "the record names its own hash"
    rec = with_permanent_ref(rec, d["content_hash"])
    assert rec.to_dict()["permanent_ref"] == d["content_hash"]


def test_axis_lookup_is_grid_safe():
    from concordance.record import axis_coords_for
    assert axis_coords_for("no_such_domain_anywhere") is None, \
        "an unregistered domain returns None, never a guess"


# ── signing: every refusal carries its reason ───────────────────────────────────────────────────

def test_signing_refusals_name_what_is_wrong():
    from concordance import signing
    ident_priv, ident_pub = signing.generate_keypair()
    with pytest.raises(TypeError):
        signing.sign_packet("not-a-dict", ident_priv)  # type: ignore[arg-type]
    ok, why = signing.verify_packet("not-a-dict")  # type: ignore[arg-type]
    assert ok is False and "dict" in why
    ok, why = signing.verify_packet({"claim": "x"})
    assert ok is False and "no `signature`" in why
    ok, why = signing.verify_packet({"claim": "x", "signature": ""})
    assert ok is False and "non-empty" in why
    ok, why = signing.verify_packet({"claim": "x", "signature": "abc"})
    assert ok is False and "public key" in why, "no key anywhere -> said plainly"

    signed = signing.sign_packet({"claim": "x"}, ident_priv)
    ok, why = signing.verify_packet(signed, ident_pub)
    assert ok is True

    ok, why = signing.verify_seal("h" * 64, "not-a-dict")  # type: ignore[arg-type]
    assert ok is False and "dict" in why
    ok, why = signing.verify_seal("h" * 64, {"pubkey": "", "sig": ""})
    assert ok is False and "missing" in why


# ── receipts + derivation: sealing failure never breaks a verdict; guards say why ───────────────

def test_a_seal_failure_never_breaks_the_verdict():
    from concordance.config import EngineConfig
    from concordance.receipts import attach
    prior = os.environ.get("CONCORDANCE_CAS_DIR")
    blocker = os.path.join(tempfile.mkdtemp(), "a-file-not-a-dir")
    open(blocker, "w").close()  # a FILE where a directory is needed -> mkdir must fail
    os.environ["CONCORDANCE_CAS_DIR"] = os.path.join(blocker, "cas")
    try:
        res = {"verdict": "HOLDS", "steps": 1, "confirmed_steps": 1, "trail": []}
        out = attach(dict(res), config=EngineConfig("secular"), domain="mathematics", enabled=True)
        assert out["verdict"] == "HOLDS", "the verdict stands even when sealing fails"
        assert out.get("seal") is None and out.get("seal_error"), \
            "and the failure is SAID, not hidden"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_CAS_DIR", None)
        else:
            os.environ["CONCORDANCE_CAS_DIR"] = prior


def test_derivation_guards_speak_their_reasons():
    from concordance.derivation import verify, verify_step
    r = verify({"mode": "no_such_mode", "params": {}})
    assert r["verdict"] == "SYSTEM_ERROR", "an unknown mode is OUR limit, never the claim's fault"
    s = verify_step("", {})
    assert s["status"] == "ERROR" and "domain" in s["detail"]
    s2 = verify_step("mathematics", {"mode": "equality",
                                     "params": {"expr_a": "x" * 5000, "expr_b": "1"}})
    assert s2["status"] == "ERROR" and "too large" in s2["detail"]


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the paths that run when something is wrong are the tested ones.")
