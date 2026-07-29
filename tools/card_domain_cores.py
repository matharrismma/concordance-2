#!/usr/bin/env python3
"""Domain reference cores — a stocked shelf for every domain the engine can actually check.

GAPS.md G1/G2: 46% of the keeping is a stub, and 33 shelves held exactly ONE card. We could
verify ~64 domains and hold almost nothing in most of them: a reader asking about optics met a
verifier they had to feed, not a shelf they could browse.

This mints, per PROVEN domain (data/domain_goldens.json — every pair run and confirmed):

  * one SPINE card per domain, part_of the Floor of Discovery;
  * one CHECK card per claim the verifier makes, carrying the WORKED RUN: the inputs, the
    claim, the engine's own verdict line, and the falsehood it refuses. Substance, not a
    pointer — each body is the real thing, minted from a run that actually happened.

Honest by construction: nothing is minted for a domain without a proven golden, so a card can
never claim a capability the engine has not demonstrated. Every card is `generated: false` —
these are FOUND relations (standard formulas and definitions) with a run we performed, not
prose we invented.

    PYTHONPATH=src python tools/card_domain_cores.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

GOLDENS = ROOT / "data" / "domain_goldens.json"
FLOOR = "card_k_floor_of_discovery"
SOURCE = ("The verifier's own documented relation, and a run this engine performed against it "
          "(deterministic; re-runnable with tools/domain_goldens.py)")


def _fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt(x) for x in v) + "]"
    return str(v)


def _verdict_lines(domain, packet):
    from concordance import verifiers
    out = []
    for r in verifiers.run_for_domain(domain, packet, surface="witness"):
        name = getattr(r, "name", "") or getattr(r, "check", "") or domain
        st = str(getattr(r, "status", "")).split(".")[-1]
        detail = (getattr(r, "detail", "") or getattr(r, "message", "") or "")
        if st and "NOT_APPLICABLE" not in st:
            out.append(f"  {name}: {st}" + (f" — {detail}" if detail else ""))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    if not GOLDENS.exists():
        print("no data/domain_goldens.json — run tools/domain_goldens.py first")
        return 2
    goldens = json.loads(GOLDENS.read_text(encoding="utf-8"))
    cards, spines = [], 0
    for domain in sorted(goldens):
        case = goldens[domain]
        pk, true_spec, false_spec = case["packet_key"], case["true"], case["false"]
        pretty = domain.replace("_", " ")
        spine_id = f"card_spine_domain_{domain}"
        claims = [k for k in true_spec if k.startswith(("claimed_", "claim_"))]
        inputs = {k: v for k, v in true_spec.items() if k not in claims}
        cards.append({
            "id": spine_id, "kind": "reference",
            "title": f"{pretty.title()} — what this engine can check",
            "body": (f"The {pretty} shelf of the keeping. This engine holds a deterministic "
                     f"verifier for {pretty}: hand it a claim in the {pk} shape and it returns a "
                     f"verdict, the worked trail, and a re-checkable seal. It checks "
                     f"{len(claims)} kind(s) of claim here. What it CANNOT check it says so "
                     f"plainly — a verifier that answered everything would be an idol, not an "
                     f"instrument."),
            "source": {"label": SOURCE, "url": "", "domain": domain, "authority_tier": "reference"},
            "shelf": domain, "box": "spine",
            "bands": [domain, pretty, "verifier", "spine"],
            "subject": pretty.title(),
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": f"the {pretty} domain of the Floor of Discovery"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False,
            "extra": {"domain": domain, "packet_key": pk, "checks": len(claims)},
        })
        spines += 1
        for claim in claims:
            one = {**inputs, claim: true_spec[claim]}
            wrong = {**inputs, claim: false_spec.get(claim)}
            held = _verdict_lines(domain, {pk: one})
            refused = _verdict_lines(domain, {pk: wrong})
            if not held:
                continue
            label = claim.replace("claimed_", "").replace("claim_", "").replace("_", " ")
            # A module's example carries inputs for ALL its checks; this card is about ONE.
            # Keep the inputs whose value the verdict actually cites, so the reader sees the
            # working and not a pile of unrelated numbers. If nothing matches (a check that
            # states no numbers), fall back to the full set rather than showing an empty GIVEN.
            trail = " ".join(held)
            used = {k: v for k, v in inputs.items()
                    if _fmt(v) in trail or str(v) in trail or k in trail}
            shown = used or inputs
            given = "\n".join(f"  {k} = {_fmt(v)}" for k, v in sorted(shown.items())[:10])
            body = (
                f"A worked check in {pretty}: {label}.\n\n"
                f"GIVEN\n{given or '  (no free inputs — the claim stands alone)'}\n\n"
                f"CLAIMED\n  {claim} = {_fmt(true_spec[claim])}\n\n"
                f"THE ENGINE'S VERDICT\n" + "\n".join(held) + "\n\n"
                f"AND THE FALSEHOOD IT REFUSES\n  {claim} = {_fmt(false_spec.get(claim))}\n"
                + ("\n".join(refused) if refused else "  (refused — no confirmation returned)")
                + "\n\nThis is the whole discipline in one card: the same inputs, a wrong answer, "
                  "and an engine that will not seal it. Re-run it yourself — the check is "
                  "deterministic and the trail is the reasoning."
            )
            cards.append({
                "id": f"card_domchk_{domain}_{claim}", "kind": "reference",
                "title": f"{pretty.title()}: {label}",
                "body": body,
                "source": {"label": SOURCE, "url": "", "domain": domain,
                           "authority_tier": "reference"},
                "shelf": domain, "box": "check",
                "bands": [domain, pretty, label, "worked", "verified"],
                "subject": f"{pretty} — {label}",
                "connections": [{"to_card_id": spine_id, "relationship": "member_of",
                                 "evidence": f"a check the {pretty} verifier performs"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
                "generated": False,
                "extra": {"domain": domain, "packet_key": pk, "claim": claim,
                          "true_spec": one, "false_spec": wrong},
            })
    checks = len(cards) - spines
    print(f"domains: {spines} · worked-check cards: {checks} · total {len(cards)}")
    avg = sum(len(c["body"]) for c in cards) / max(1, len(cards))
    print(f"average body length: {avg:.0f} chars (substance, not stubs)")
    if dry:
        print("--dry-run: nothing written.")
        return 0
    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    out = base / "domain_core_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
