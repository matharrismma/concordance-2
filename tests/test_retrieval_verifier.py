"""The fleet turned inward — the verifier that measures our own finding.

The load-bearing test here is test_a_false_silence_is_our_failure. Every other retrieval failure
is visible: a wrong result can be argued with. "Nothing found" cannot — it looks like honesty,
reads like humility, and is indistinguishable from a broken index. If that check ever stops
firing, the library can quietly lose documents it holds and the want list will fill with wants
we could already have met.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-ret-"))

from concordance.verifiers import retrieval as R  # noqa: E402


def _one(packet, name):
    return next(v for v in R.run({"RET_VERIFY": packet}) if v.name == name)


def test_precision_is_the_published_formula():
    v = _one({"query": "q", "returned_ids": ["a", "b", "c", "d"],
              "relevant_ids": ["a", "c", "z"], "claimed_precision": 0.5},
             "retrieval.precision")
    assert v.status == "CONFIRMED", v.detail
    assert abs(v.data["actual_precision"] - 0.5) < 1e-12
    assert set(v.data["noise_ids"]) == {"b", "d"}


def test_recall_names_what_was_dropped():
    """A recall number without the missing ids says you failed but not what you failed to find."""
    v = _one({"query": "q", "returned_ids": ["a"], "relevant_ids": ["a", "b", "c"],
              "claimed_recall": 1 / 3}, "retrieval.recall_of_known")
    assert v.status == "CONFIRMED", v.detail
    assert set(v.data["missed_ids"]) == {"b", "c"}


def test_a_repeated_result_cannot_inflate_precision():
    """Retrieval sets are sets. Without dedupe, returning the same good hit four times scores
    1.000 — a system grading its own homework."""
    v = _one({"query": "q", "returned_ids": ["a", "a", "a", "b"],
              "relevant_ids": ["a"], "claimed_precision": 0.5}, "retrieval.precision")
    assert v.status == "CONFIRMED", v.detail
    assert v.data["returned"] == 2                       # a, b — not 4


def test_rank_zero_means_absent_not_first():
    v = _one({"query": "q", "returned_ids": ["x", "y"], "target_id": "z", "claimed_rank": 0},
             "retrieval.rank_of_target")
    assert v.status == "CONFIRMED"
    assert v.data["actual_rank"] == 0 and v.data["reciprocal_rank"] == 0.0
    assert "NOT RETURNED" in v.detail


def test_a_false_silence_is_our_failure():
    """THE ONE THAT MATTERS. Zero results while the corpus holds a match is a MISMATCH against
    us — and the detail must say so, so it is never filed as a gap in the world."""
    v = _one({"query": "how to purify water", "claimed_result_count": 0,
              "corpus_contains_match": True, "relevant_ids": ["card_water_1"]},
             "retrieval.no_false_silence")
    assert v.status == "MISMATCH"
    assert "FALSE SILENCE" in v.detail
    assert "our failure" in v.detail and "must not be recorded as a want" in v.detail
    assert v.data["witness_ids"] == ["card_water_1"]     # the proof it was there


def test_an_honest_miss_stays_an_honest_miss():
    """The mirror image: nothing found AND nothing held is correct, and must not be scored as a
    defect — otherwise the check pressures us to fabricate results."""
    v = _one({"query": "flux capacitor repair", "claimed_result_count": 0,
              "corpus_contains_match": False}, "retrieval.no_false_silence")
    assert v.status == "CONFIRMED"
    assert "honest miss" in v.detail


def test_a_nonempty_result_is_not_a_silence():
    v = _one({"query": "q", "claimed_result_count": 7, "corpus_contains_match": True},
             "retrieval.no_false_silence")
    assert v.status == "CONFIRMED" and "not a silence" in v.detail


def test_the_caller_cannot_loosen_the_tolerance_to_force_a_pass():
    """clamp_tol must hold here too — an adversarial caller widening the window would turn this
    verifier into a rubber stamp on our own quality."""
    v = _one({"query": "q", "returned_ids": ["a", "b"], "relevant_ids": ["a"],
              "claimed_precision": 0.9, "tolerance": 10.0}, "retrieval.precision")
    assert v.status == "MISMATCH", v.detail


def test_an_empty_packet_is_not_applicable():
    res = R.run({})
    assert len(res) == 1 and res[0].status == "NOT_APPLICABLE"


def test_the_verifier_is_registered_as_an_ordinary_domain():
    """Our retrieval gets no gentler a verifier than a stranger's chemistry."""
    from concordance import verifiers
    reg = getattr(verifiers, "VERIFIERS", None) or getattr(verifiers, "DOMAIN_VERIFIERS", {})
    assert any("retrieval" in k for k in reg), sorted(reg)[:5]
