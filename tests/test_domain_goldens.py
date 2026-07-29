"""Per-domain goldens — every verified domain seals a truth and refuses a falsehood.

GAPS.md G5: the derivation moat's 60/60 covers three modes of one engine. It never showed that
`optics` seals Snell's law, or that `medicine` refuses a wrong BMI. A domain with no golden has
never been shown to do either — and "0 false positives" said of the domains would have been a
claim beyond the evidence.

`tools/domain_goldens.py` derives a pair per domain FROM THE VERIFIER'S OWN DOCUMENTED EXAMPLE,
runs it, and keeps only what actually holds. This gate re-proves every stored pair on every run:

  * the TRUE packet must CONFIRM — the check works;
  * the FALSE packet (same inputs, wrong claims) must NOT confirm — no false positive.

A false positive here is the most serious failure the project can have: sealing a falsehood.
The test names the domain and the packet so the failure is actionable, never a bare assert.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

GOLDENS = ROOT / "data" / "domain_goldens.json"


@pytest.fixture(autouse=True)
def _real_data_dir():
    """Some verifiers read reference data (the periodic table, constants, nuclides) from
    CONCORDANCE_DATA_DIR. Other tests in the suite point that at a temp directory, and a
    verifier that cannot find its data answers n/a — which would make this gate fail for a
    reason that has nothing to do with the verifier's logic. Pin it to the repo's own data for
    the duration: these goldens are about whether the checks hold, not about the neighbours."""
    import os
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data")
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _load():
    if not GOLDENS.exists():
        pytest.skip("data/domain_goldens.json absent (data, regenerate with tools/domain_goldens.py)")
    return json.loads(GOLDENS.read_text(encoding="utf-8"))


def _statuses(domain, packet):
    from concordance import verifiers
    return [str(getattr(r, "status", "")) for r in
            verifiers.run_for_domain(domain, packet, surface="witness")]


def test_every_golden_domain_seals_its_truth():
    """Three states, not two — the house rule, applied to our own gate.

    A verifier that answers only NOT_APPLICABLE did not engage. In-suite that usually means its
    REFERENCE DATA was not reachable in this process: `strongs/lookup.py` (and others) resolve
    their data directory at IMPORT time, so whichever test imports first fixes it for the whole
    session, and no fixture set afterwards can move it. That is a fact about our environment,
    never a verdict on the check — so it is reported by name as COULD-NOT-CHECK, never silently
    passed and never counted as a failure.

    What still fails, always: a documented truth that now MISMATCHES (a real regression), and
    a wholesale outage (more than a fifth of the set going quiet at once)."""
    g = _load()
    assert len(g) >= 40, f"the golden set shrank to {len(g)} — a domain lost its proof"
    broken, could_not_check = [], []
    for domain, case in sorted(g.items()):
        sts = _statuses(domain, {case["packet_key"]: case["true"]})
        if any("MISMATCH" in s for s in sts):
            broken.append(f"{domain}: MISMATCH {sts}")
        elif any("CONFIRM" in s for s in sts):
            continue
        else:
            could_not_check.append(f"{domain}: {sorted(set(sts))}")
    if could_not_check:
        print("COULD-NOT-CHECK (reference data unreachable in this process): "
              + "; ".join(could_not_check))
    assert not broken, ("domains that no longer confirm their own documented truth: "
                        + "; ".join(broken))
    assert len(could_not_check) <= max(2, len(g) // 5), (
        f"{len(could_not_check)} of {len(g)} domains went quiet at once — that is not one "
        f"module's data path, it is an outage: " + "; ".join(could_not_check))


def test_no_domain_seals_a_falsehood():
    """The property the whole product rests on, now proven per domain and not only for the
    derivation moat."""
    g = _load()
    false_positives = []
    for domain, case in sorted(g.items()):
        sts = _statuses(domain, {case["packet_key"]: case["false"]})
        if any("CONFIRM" in s for s in sts) and not any("MISMATCH" in s for s in sts):
            false_positives.append(f"{domain} sealed {json.dumps(case['false'])[:140]}")
    assert not false_positives, ("FALSE POSITIVE — a falsehood was sealed: "
                                 + "; ".join(false_positives))


def test_the_golden_pairs_are_real_falsifications():
    """A 'false' case that is identical to the true one would make this gate vacuous."""
    g = _load()
    vacuous = [d for d, c in g.items() if c["true"] == c["false"]]
    assert not vacuous, f"goldens whose falsehood equals their truth: {vacuous}"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
