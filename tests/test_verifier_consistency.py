"""Verifier consistency — the present-vs-null invariant, locked for every domain.

The review flagged a "present-vs-null inconsistency": a verifier that saw no applicable
artifact might return [] from one module and [NOT_APPLICABLE] from another, so callers
couldn't rely on a uniform "nothing to check here" signal. This test locks the invariant
for EVERY registered verifier: run() on an irrelevant packet returns a NON-EMPTY list whose
every result is NOT_APPLICABLE — never [], never a stray CONFIRMED/MISMATCH on absent input
(a false-positive on emptiness). It also exercises the shared declarative driver.

Runnable with pytest OR `python tests/test_verifier_consistency.py`.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import (  # noqa: E402
    VERIFIERS, WITNESS_VERIFIERS, base,
)
from concordance.verifiers.base import (  # noqa: E402
    VerifierResult, confirm, dispatch, mismatch, na,
)


def _modules():
    return sorted(set(VERIFIERS.values()) | set(WITNESS_VERIFIERS.values()))


def test_absent_artifact_is_uniformly_not_applicable():
    """Every verifier: an empty packet -> a non-empty all-NOT_APPLICABLE result."""
    offenders = []
    for mp in _modules():
        mod = importlib.import_module(mp)
        res = mod.run({})
        ok = bool(res) and all(getattr(r, "status", None) == "NOT_APPLICABLE" for r in res)
        if not ok:
            offenders.append((mp, [getattr(r, "status", "?") for r in res]))
    assert not offenders, f"present-vs-null violators (want non-empty all-NA): {offenders}"


def test_irrelevant_artifact_never_confirms():
    """A packet carrying an UNRELATED artifact key must not coax a CONFIRMED/MISMATCH out of
    any verifier — the cardinal emptiness guard (no sealing on absent input)."""
    bad = []
    for mp in _modules():
        mod = importlib.import_module(mp)
        res = mod.run({"TOTALLY_UNRELATED_ARTIFACT_XYZ": {"foo": 1}})
        if any(getattr(r, "status", None) in ("CONFIRMED", "MISMATCH") for r in res):
            bad.append(mp)
    assert not bad, f"verifiers that judged an unrelated artifact: {bad}"


def test_dispatch_driver_semantics():
    """The declarative driver: key-tuple + callable requirements, uniform na fallback."""
    def _c(art):
        return confirm("c", "ok")

    def _m(art):
        return mismatch("m", "no")

    rules = [
        (("a", "b"), _c),                         # key-tuple: both present
        (lambda art: art.get("flag") is True, _m),  # callable predicate
    ]
    # both fire
    r = dispatch({"K": {"a": 1, "b": 2, "flag": True}}, "K", rules, domain="d")
    assert [x.status for x in r] == ["CONFIRMED", "MISMATCH"]
    # only key-tuple fires
    r = dispatch({"K": {"a": 1, "b": 2}}, "K", rules, domain="d")
    assert [x.status for x in r] == ["CONFIRMED"]
    # artifact present but nothing fires -> single NA
    r = dispatch({"K": {"a": 1}}, "K", rules, domain="d", none_reason="nope")
    assert len(r) == 1 and r[0].status == "NOT_APPLICABLE" and r[0].detail == "nope"
    # absent artifact -> single NA
    r = dispatch({}, "K", rules, domain="d")
    assert len(r) == 1 and r[0].status == "NOT_APPLICABLE"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} consistency tests passed — present-vs-null is uniform across every verifier.")
