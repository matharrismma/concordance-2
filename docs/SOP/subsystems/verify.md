# SOP · Verify / the Moat

**Purpose.** The deterministic gate: a checkable claim goes in, a sealed three-state verdict —
HOLDS / BROKEN / INCOMPLETE — comes out, and anyone can re-fetch and re-check the seal. The engine
verifies a *provided* derivation; it never generates the answer, and it must never seal a falsehood
as true (the false-positive rate is the metric that governs everything here).

**Wiring.** Modules: `derivation` · `receipts` · `gates` · `kernel` · `audit` · `candidates` ·
`validate` · `warrant`. `audit` extracts checkable claims from prose; `candidates` narrows a proposal
set (born quarantined, a lone winner only when exactly one passes); `derivation` routes each to the
sympy moat or a domain fleet verifier and reduces to a verdict; `receipts` mints the re-checkable
seal; `kernel` is the doctrine every state-change routes through (never silently upgrade authority).
Surfaces: `POST /ask` (a checkable claim → sealed verdict under `verify`), the receipt page at
`GET /s/<hash>`, and the raw JSON at `GET /seal?hash=`.

## Canary — is it up?
Ask it to check a true arithmetic claim and confirm it HOLDS *and* hands back a re-fetchable seal:
```
curl -s -X POST https://narrowhighway.com/ask -H 'content-type: application/json' \
  -d '{"text":"2+2 = 4"}' | python -c "import sys,json;v=json.load(sys.stdin)['verify'];print(v['verdict'], (v.get('seal') or {}).get('cite_url'))"
# expect: HOLDS  https://narrowhighway.org/s/<hash>   —   the same POST with "2+2 = 5" -> BROKEN, never HOLDS.
```
A HOLDS with a `cite_url` you can re-fetch means the moat and the seal chain are both up.

## Operate
Automatic on the found/verify path. Prose runs `candidates.from_prose` → `create_set → commit → route →
narrow`: the commitment hashes the complete raw set *before* any evaluation, routing is a fixed
pre-registered policy blind to proposal weight, and every candidate is preserved. A structured claim
routes straight to `derivation.verify` / `verify_domain`. Verdict precedence is
`BROKEN > SYSTEM_ERROR > INCOMPLETE > HOLDS` — a real falsehood always governs, and *our* failure
(SYSTEM_ERROR) is never rendered as the caller's falsehood. `receipts.mint` seals BROKEN too (proof a
claim is false is as valuable as proof it holds); only PASS enters the tamper-evident ledger chain.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A true claim returns SYSTEM_ERROR / "verification timed out (>8s)" | Cold C-extension import (sympy/scipy) paid *inside* the per-verify wall-clock bound | Call `derivation.warm()` at boot (the server already does) so the heavy import is pre-paid outside the timed path — see the `warm()` note in `derivation.py` |
| Intermittent "verifier busy … retry shortly" ERROR under load | Verify pool saturated (`_MAX_WORKERS`, default 4) — sheds to ERROR, which errs safe (never a false HOLDS) | Expected backpressure; raise `CONCORDANCE_VERIFY_WORKERS` if the box has cores to spare |
| A real claim comes back INCOMPLETE, not HOLDS | No applicable secular verifier for that domain (`NOT_APPLICABLE`) — the ~52% coverage gap | Honest gap, never a false negative dressed as a "no"; the open issue below |
| `seal: null` with a `seal_error` | CAS/ledger write failed; the verdict still stands but is un-receipted | Never presented as receipted — check the CAS dir is writable (`CONCORDANCE_DATA_DIR`) |

## Tests
`tests/test_fp_gate.py` (the crown guard — 0 false-positives across 60+ domains, each with a
known-TRUE and known-FALSE packet), `tests/test_verifiers.py`, `tests/test_kernel.py`,
`tests/test_candidates.py`, `tests/test_receipt.py`, `tests/test_system_error_distinct.py` —
`PYTHONPATH=src python -m pytest tests/test_fp_gate.py tests/test_verifiers.py tests/test_kernel.py tests/test_candidates.py tests/test_receipt.py -q`.
They hold the false-positive floor at zero, the monotonic authority law, candidate-set integrity
(commit-before-evaluate, weight-blind routing), and that a seal is honest by construction.

## Known issues & support
- **Domain verifier coverage ~52%** — unsupported. About half the registered domains have a
  deterministic verifier; the rest return `NOT_APPLICABLE`, so a claim there is INCOMPLETE (an honest
  gap), never a false HOLDS or a false BROKEN. Interim support: the three states stay distinct, so a
  reader is never told their true claim is false merely because we could not check it. The real fix is
  extending the verifier fleet to the uncovered domains.

## Refine
Grow the fleet on the highest-stakes uncovered domains first (the `test_fp_gate.py` pattern: a
known-TRUE and a known-FALSE packet per domain, both routed through `run_for_domain`), so INCOMPLETE
shrinks toward HOLDS/BROKEN without ever admitting a false positive.
