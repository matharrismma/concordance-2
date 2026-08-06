"""The Candidate Engine's covenants: commitment before verification, verification over weight.

Task #135, specified by docs/RED_TEAM_CANDIDATE_ENGINE_2026-08-05.md. Each test here refuses
one failure mode from the assessment's threat register (§6) or its mandatory adversarial
suite (§9.1) — probability laundering, selective disclosure, verification shopping,
winner-only retention. The module invariant under test, verbatim (§5.2): "No candidate may
move from proposal to verified fact merely because it has a high proposal_weight, appears in
several correlated samples, or wins a model-based ranking."
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import candidates as cand  # noqa: E402
from concordance import derivation  # noqa: E402

# Pre-pay the sympy import at collection, outside the per-verification wall clock — a cold
# C-extension import inside the timeout can turn a TRUE claim into a transient SYSTEM_ERROR
# (derivation.warm's own docstring), which here would read as a quarantine and fail a test
# about a claim the moat can perfectly well check.
derivation.warm()


def _make():
    """One committed-shape fixture set: a truth and a falsehood about the same question."""
    return cand.create_set("what is 2+2?", ["2+2 = 4", "2+2 = 5"],
                           generator="model-x/1.0", generation_method="vs")


# ── birth: content-addressed, quarantined, weight verbatim ───────────────────────────────────

def test_creation_is_content_addressed_and_the_weight_rides_verbatim():
    """The set id must come from the CONTENT of the raw set — no clock, no counter — and the
    generator's verbalized number must be stored exactly as given: untrusted metadata, never
    evidence. An absent weight must stay absent, because defaulting one would be the module
    authoring the very metadata it refuses to trust (§4.2)."""
    cs = cand.create_set("what is 2+2?",
                         [{"raw_text": "2+2 = 4", "proposal_weight": 0.125}, "2+2 = 5"],
                         generator="model-x/1.0", generation_method="vs")
    assert cs["candidate_set_id"].startswith("cset_")
    assert [c["candidate_id"] for c in cs["candidates"]] == ["c000", "c001"]
    assert cs["candidates"][0]["proposal_weight"] == 0.125
    assert "proposal_weight" not in cs["candidates"][1], "an absent weight was invented"
    assert cs["query_hash"] and cs["prompt_hash"] is None
    for c in cs["candidates"]:
        assert c["verification_status"] == "quarantine", "nothing is verified at birth"
        assert c["selection_status"] == "retained-alternative"
        assert c["safety_status"] == "allow"
        assert c["cluster_id"] is None and c["parent_ids"] == []


def test_the_same_input_mints_the_same_addresses():
    """Determinism is what makes the receipt independently recomputable (tools/verify_seal.py's
    whole premise): two births from the same raw material must agree on the set id AND, after
    commit, on the full commitment hash."""
    a, b = _make(), _make()
    assert a["candidate_set_id"] == b["candidate_set_id"]
    cand.commit(a)
    cand.commit(b)
    assert a["commitment"] == b["commitment"]
    assert len(a["commitment"]) == 64, "the commitment is the full canonical SHA-256"


# ── the commitment gate (§6, selective disclosure) ───────────────────────────────────────────

def test_route_and_narrow_refuse_an_uncommitted_set():
    """Selective disclosure is only preventable if NOTHING evaluates before the complete raw
    set is hashed. An uncommitted set must be refused outright — not quietly committed on the
    way through, which would make the gate decorative."""
    with pytest.raises(ValueError, match="not committed"):
        cand.route(_make())
    with pytest.raises(ValueError, match="not committed"):
        cand.narrow(_make())


def test_membership_is_frozen_at_commit():
    """After commit the set can gain nothing and lose nothing: append raises structurally
    (the list became a tuple), and a swapped-in membership list is caught by the commitment
    recheck. The late 'add this better candidate' — or 'drop that embarrassing one' — is
    exactly what the hash exists to stop."""
    cs = cand.commit(_make())
    with pytest.raises(AttributeError):
        cs["candidates"].append({"candidate_id": "c999", "raw_text": "1 = 1"})
    cs["candidates"] = list(cs["candidates"]) + [dict(cs["candidates"][0],
                                                      candidate_id="c999")]
    with pytest.raises(ValueError, match="commitment"):
        cand.route(cs)


def test_the_stages_hold_their_registered_order():
    """§8.2 prohibits surfaces that blur where nondeterminism ended and checking began; the
    same discipline inside the module: narrow before route is refused, receipt before narrow
    is refused, and an unregistered routing policy version is refused — a policy chosen after
    outcomes is verification shopping wearing a version string (§6)."""
    cs = cand.commit(_make())
    with pytest.raises(ValueError, match="route"):
        cand.narrow(cs)
    with pytest.raises(ValueError, match="narrow"):
        cand.receipt(cs)
    with pytest.raises(ValueError, match="pre-registered"):
        cand.route(cs, policy_version="v9.9")


# ── the invariant: verification beats weight, both ways (§9.1) ───────────────────────────────

def test_a_high_weight_falsehood_is_rejected_by_the_moat():
    """The assessment's own adversarial case (§9.1): 'High proposal-weight candidate conflicts
    with deterministic verification.' The weight loses. A 0.97 on 2+2=5 buys nothing."""
    cs = cand.create_set("what is 2+2?",
                         [{"raw_text": "2+2 = 5", "proposal_weight": 0.97},
                          {"raw_text": "2+2 = 4", "proposal_weight": 0.03}],
                         generator="model-x/1.0", generation_method="vs")
    cand.commit(cs)
    cand.route(cs)
    cand.narrow(cs)
    by_id = {c["candidate_id"]: c for c in cs["candidates"]}
    assert by_id["c000"]["verification_status"] == "reject"
    assert by_id["c000"]["selection_status"] == "rejected"
    assert by_id["c000"]["proposal_weight"] == 0.97, "the weight survives, verbatim — as metadata"


def test_the_only_correct_candidate_is_selected_whatever_its_weight():
    """§9.1 again, the mirror case: 'Low proposal-weight candidate is the only correct
    answer.' Selection follows the declared rule over verification results alone, so the 0.01
    candidate wins on the mathematics and the 0.97 favorite is rejected beside it."""
    cs = cand.create_set("what is 2+2?",
                         [{"raw_text": "2+2 = 5", "proposal_weight": 0.97},
                          {"raw_text": "2+2 = 22", "proposal_weight": 0.02},
                          {"raw_text": "2+2 = 4", "proposal_weight": 0.01}],
                         generator="model-x/1.0", generation_method="vs")
    cand.commit(cs)
    cand.route(cs)
    cand.narrow(cs)
    selected = [c["candidate_id"] for c in cs["candidates"]
                if c["selection_status"] == "selected"]
    assert selected == ["c002"], "the single passing candidate, and only it, is selected"
    by_id = {c["candidate_id"]: c for c in cs["candidates"]}
    assert by_id["c002"]["verification_status"] == "pass"
    assert by_id["c000"]["selection_status"] == "rejected"
    assert by_id["c001"]["selection_status"] == "rejected"


def test_the_weight_never_reaches_routing_or_narrowing_code():
    """Structural proof of the invariant, not a promise: the field name may appear in storage
    and docstring contexts (create_set, _raw_material, the module header) but must NOT appear
    in the SOURCE of any deciding function. If this fails, ranking code has started reading
    the generator's number — the exact laundering the red team prohibits (§6)."""
    for fn in (cand.route, cand.narrow, cand._route_one, cand._arithmetic_side,
               cand._assert_committed_and_intact):
        assert "proposal_weight" not in inspect.getsource(fn), (
            f"{fn.__name__} reads the untrusted generator weight")


# ── complete retention: the receipt carries the losers too ───────────────────────────────────

def test_the_receipt_retains_every_candidate_never_winner_only(tmp_path, monkeypatch,
                                                               corpus_left_as_found):
    """Top decision from the assessment: 'do not seal only the winning answer.' The sealed
    record must carry the rejected, the quarantined prose (held, never judged by a math
    verifier — the mis-typing §7.1 prohibits), the whole trace, and the commitment. And its
    hash must recompute under the ONE canonical form, or it is not that record.

    CAS and data dirs point at tmp so the seal write is hermetic; corpus_left_as_found puts
    the corpus singleton back afterward (the receipt-card mint touches it best-effort)."""
    monkeypatch.setenv("CONCORDANCE_CAS_DIR", str(tmp_path / "cas"))
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    cs = cand.create_set("what is 2+2?",
                         ["2+2 = 4", "2+2 = 5", "the answer is a mystery"],
                         generator="model-x/1.0", generation_method="direct")
    cand.commit(cs)
    cand.route(cs)
    trace = cand.narrow(cs)
    out = cand.receipt(cs)
    rec = out["record"]
    assert len(rec["candidates"]) == 3, "a candidate went missing between narrow and seal"
    statuses = {c["candidate_id"]: c["verification_status"] for c in rec["candidates"]}
    assert statuses == {"c000": "pass", "c001": "reject", "c002": "quarantine"}
    assert rec["commitment"] == cs["commitment"], "the receipt must cite the commitment it honored"
    assert rec["trace"] == trace and rec["trace"][0]["event"] == "narrow_begin"
    assert rec["policy_version"] == "v0.1" and rec["selection_rule"] == cand.SELECTION_RULE
    # Re-checkable by anyone: the same canonical form the independent verifier uses.
    from concordance import cas as _cas
    assert _cas.content_hash_of(rec) == out["content_hash"]
    if out["sealed"]:
        assert _cas.fetch(out["content_hash"]) is not None, (
            "sealed:true but the object is not re-fetchable — the one lie a receipt may never tell")
    else:
        assert out["seal_error"], "an unsealed receipt must name why"


def test_prose_is_held_not_judged():
    """A sentence is not an equation. Routing 'the kingdom = heaven' to sympy would read two
    free symbols and mint a REJECT on a claim that was never arithmetic — our routing gap
    rendered as their falsehood. The unroutable stays quarantined, with the reason on the
    trace."""
    cs = cand.create_set("a mixed bag",
                         ["the kingdom = heaven", "entirely plain prose"],
                         generator="model-x/1.0", generation_method="direct")
    cand.commit(cs)
    cand.route(cs)
    cand.narrow(cs)
    for c in cs["candidates"]:
        assert c["verification_status"] == "quarantine", (
            f"{c['candidate_id']} ({c['raw_text']!r}) was judged by a verifier it never fit")
        assert c["selection_status"] == "retained-alternative"
    quarantined = [e for e in cs["trace"] if e["event"] == "quarantined"]
    assert len(quarantined) == 2 and all(e["why"] for e in quarantined)
