"""Witness-surface test — the .org overlay surfaces only on surface="witness".

The seam, the other direction: theology/witness verifiers run on the witness surface
and are absent on the secular reach, while the shared foundation (and the secular
verifiers) are unaffected. Runnable with `pytest` OR `python tests/test_witness.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, validate_and_seal  # noqa: E402
from concordance.verifiers import WITNESS_VERIFIERS, _get_witness_module, run_for_domain  # noqa: E402


def test_witness_verifiers_surface_only_on_witness():
    for d in ("theology_doctrine", "witness"):
        on = run_for_domain(d, {}, surface="witness")
        off = run_for_domain(d, {}, surface="secular")
        assert on, f"{d}: the witness surface must surface the verifier"
        assert off == [], f"{d}: the secular reach must NOT surface the witness verifier (got {off})"


def test_witness_modules_load():
    for d in sorted(WITNESS_VERIFIERS):
        m = _get_witness_module(d)
        assert m is not None and hasattr(m, "run"), f"{d}: witness module failed to load"


def test_canon_imports():
    import concordance.canon as canon  # the layered-canon data module
    assert canon is not None


def test_secular_surface_unaffected():
    # a secular claim still verifies on the secular reach — witness gating doesn't disturb it
    pkt = {"domain": "combinatorics",
           "COMB_VERIFY": {"comb_n": 5, "comb_k": 2, "claimed_combinations": 10},
           "created_epoch": 1_700_000_000, "required_witnesses": 0}
    rec = validate_and_seal(pkt, now_epoch=1_700_000_000 + 3601, config=EngineConfig("secular"))
    assert rec.overall == "PASS"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} witness-surface tests passed — .org surfaces the witness, .com does not.")
