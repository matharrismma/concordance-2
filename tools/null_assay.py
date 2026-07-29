#!/usr/bin/env python3
"""THE NULL ASSAY — ring A: run the 100 theories and find what does NOT align.

Matt, 2026-07-28: "You will review all theories and find the ones that do not align."
Widened: "Look across the entire project and all theories that could be associated with the
topics we cover. Same null assay."

`docs/THEORY_CATALOG.md` assigned every theory an EXPECTED class, and said plainly that the
class is "a hint to be TESTED, never a verdict. The assay disposes." This runs that test.

For each theory card the assay asks two questions the engine cannot dodge — and it asks them
of the EVIDENCE, not of the source tree:

  1. Does a verifier for this domain exist, load, and honor its run() contract?
  2. Is there at least one REAL SEALED RUN in the keeping (The Works / verified cards) that
     exercises that domain? A module that merely imports proves nothing.

    claim `seals`    -> needs both. No verifier: OVER_CLAIM. Verifier but no sealed run:
                        UNPROVEN_CLAIM — not a falsehood, an unbacked claim, said plainly.
    claim `partial`  -> needs a verifier; its reach is narrower than the theory by admission.
    claim `map-only` -> claims no seal, so it ALIGNS unless the engine misbehaves. We do not
                        manufacture findings by treating "a verifier exists in this domain" as
                        "this theory is sealable" (biology verifies Punnett squares; that says
                        nothing about sealing Darwinian evolution — the first draft of this
                        assay made exactly that error and reported 9 false findings).

An over-claim is the dangerous direction: it tells a reader we can check something we cannot.

Honest by construction: a domain the engine cannot load is reported COULD_NOT_CHECK, never
counted as a pass and never counted as a failure — our failure is not their falsehood.

    PYTHONPATH=src python tools/null_assay.py            # ring A, human-readable
    PYTHONPATH=src python tools/null_assay.py --json     # machine-readable
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CARDS = ROOT / "data" / "theory_cards.jsonl"


def _load_theories():
    out = []
    if not CARDS.exists():
        return out
    for ln in CARDS.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        c = json.loads(ln)
        if c.get("shelf") != "theories":
            continue
        e = c.get("extra") or {}
        out.append({"id": c.get("id"), "title": c.get("title"),
                    "domain": (e.get("engine_domain") or "").strip(),
                    "claim": (e.get("calibration") or "").strip(),
                    "section": e.get("section") or ""})
    return out


def _sealed_domains():
    """Domains with at least one REAL sealed run in the keeping — The Works (engine-sealed
    demonstrations) and the verified cards minted from live verifications. This is the only
    honest evidence that a domain actually SEALS; a module that merely imports proves nothing.

    (The first version of this assay asked only "does a verifier exist for this domain?" and
    reported 9 findings. That check was wrong: biology has a verifier for Punnett squares,
    which says nothing about sealing Darwinian evolution. Check the check first.)"""
    seen = Counter()
    for name in ("works_cards.jsonl", "verified_cards.jsonl"):
        p = ROOT / "data" / name
        if not p.exists():
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                c = json.loads(ln)
            except ValueError:
                continue
            e = c.get("extra") or {}
            d = (e.get("domain") or e.get("engine_domain")
                 or (c.get("source") or {}).get("domain") or "")
            if d:
                seen[str(d).lower().strip()] += 1
    return seen


def _engine_reach(domain: str):
    """(state, detail) — what the ENGINE actually offers for this domain, found not assumed."""
    from concordance import verifiers
    d = (domain or "").lower().strip()
    if not d:
        return "COULD_NOT_CHECK", "the card names no engine domain"
    if d not in verifiers.VERIFIERS and d not in getattr(verifiers, "WITNESS_VERIFIERS", {}):
        return "NO_VERIFIER", f"no verifier registered for domain {d!r}"
    try:
        # An EMPTY packet: every honest verifier answers n/a rather than raising. This proves
        # the module loads and honors its run() contract — necessary for any claim, but NOT
        # sufficient for a claim of sealing (see _sealed_domains).
        results = verifiers.run_for_domain(d, {}, surface="witness")
    except Exception as exc:  # noqa: BLE001 — a verifier that RAISES is itself the finding
        return "RAISES", f"{type(exc).__name__}: {exc}"
    if not results:
        return "SILENT", "the verifier returned nothing at all on an empty packet"
    kinds = Counter(getattr(r, "status", None) or (r.get("status") if isinstance(r, dict) else "?")
                    for r in results)
    return "VERIFIER_OK", f"{len(results)} result(s) {dict(kinds)}"


def ring_a():
    """Three states per theory, and the verdicts that matter:

    OVER_CLAIM      the card says we can seal it and NO verifier exists — the dangerous
                    direction: a reader is told we check what we cannot.
    UNPROVEN_CLAIM  the card says `seals`, a verifier exists, but NOT ONE sealed run in the
                    whole keeping exercises that domain. Not a falsehood — an unbacked claim,
                    and the honest word for it is "unproven".
    MISALIGNED      the verifier itself misbehaves (raises, or answers nothing).
    ALIGNED         claim and evidence agree. A `map-only` card claims no seal, so it aligns
                    unless the engine misbehaves — we do not manufacture findings by treating
                    "a verifier exists in this domain" as "this theory is sealable".
    """
    theories = _load_theories()
    sealed = _sealed_domains()
    rows, findings = [], []
    for t in theories:
        state, detail = _engine_reach(t["domain"])
        claim, d = t["claim"], (t["domain"] or "").lower().strip()
        proof = sealed.get(d, 0)
        verdict = "ALIGNED"
        if state in ("RAISES", "SILENT"):
            verdict = "MISALIGNED"
        elif state == "COULD_NOT_CHECK":
            verdict = "COULD_NOT_CHECK"
        elif claim in ("seals", "partial") and state == "NO_VERIFIER":
            verdict = "OVER_CLAIM"
        elif claim == "seals" and proof == 0:
            verdict = "UNPROVEN_CLAIM"
        rows.append({**t, "engine": state, "detail": detail, "sealed_runs": proof,
                     "verdict": verdict})
        if verdict != "ALIGNED":
            findings.append(rows[-1])
    return rows, findings


def main() -> int:
    as_json = "--json" in sys.argv
    rows, findings = ring_a()
    if as_json:
        print(json.dumps({"ring": "A", "total": len(rows), "rows": rows,
                          "findings": findings}, ensure_ascii=False, indent=2))
        return 0
    counts = Counter(r["verdict"] for r in rows)
    print(f"NULL ASSAY — ring A: the {len(rows)} theories the sciences and math run on\n")
    print(f"  ALIGNED         {counts['ALIGNED']}")
    print(f"  OVER_CLAIM      {counts['OVER_CLAIM']}   (says we can seal it; no verifier exists)")
    print(f"  UNPROVEN_CLAIM  {counts['UNPROVEN_CLAIM']}   (says `seals`; no sealed run exercises it)")
    print(f"  MISALIGNED      {counts['MISALIGNED']}   (the verifier itself raises or is silent)")
    print(f"  COULD_NOT_CHECK {counts['COULD_NOT_CHECK']}   (a fact about US, never about them)")
    if findings:
        print("\nWHAT DOES NOT ALIGN:")
        for f in findings:
            print(f"  [{f['verdict']:15}] {f['title']}")
            print(f"      claim={f['claim']!r} domain={f['domain']!r} engine={f['engine']} "
                  f"sealed_runs={f['sealed_runs']} — {f['detail']}")
    else:
        print("\nNothing misaligned in ring A — every claim matches what the engine actually does.")
    by_sec = Counter(f["section"] for f in findings)
    if by_sec:
        print("\nfindings by section:", dict(by_sec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
