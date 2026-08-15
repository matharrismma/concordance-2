#!/usr/bin/env python3
"""The /ask retrieval probe — a repeatable eval of the FRONT-DOOR VOICE.

"Our responses aren't great" is a feeling until it is a number. This hits BASE/ask for a set of real
queries and scores each against what a GOOD answer looks like end-to-end (the assembled thing the
reader actually sees): the right KIND, and — for a how-to — a LEAD from a directly-useful shelf,
never the academic Theory-Assay catalog. It needs no corpus of its own (the box already holds it),
so it runs where the full ask suite cannot. Build the number, then move it.

    python tools/ask_probe.py                          # against the live box (127.0.0.1:8002)
    ASK_BASE=https://narrowhighway.com python tools/ask_probe.py

Crisis and comfort are SAFETY lanes: crisis must always win; a real cry for help is never a search.
A first-aid how-to ('set a broken bone') is NOT emotional distress and must not route to comfort.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request

BASE = os.environ.get("ASK_BASE", "http://127.0.0.1:8002").rstrip("/")
_PRODUCT = re.compile(r"\b(sanitiz|wipes?|shampoo|lotion|body\s*wash|sunscreen|foaming|scented|"
                      r"deodorant|toothpaste|mouthwash|lip\s*balm|moisturiz|cleanser|conditioner|"
                      r"antiperspirant|cosmetic|fragrance|perfume)", re.I)  # prefix; no trailing \b

_ACADEMIC = {"theories"}                                    # must never LEAD a how-to
_PRACTICAL = {"survival", "first_aid", "water", "sanitation", "communications", "navigation",
              "energy", "agriculture", "medicine", "apothecary", "almanac", "fieldkit", "playbook",
              "practical", "access", "nutrition", "foods", "recipes", "curriculum", "activities"}

# (query, checks). checks keys: lead_practical(bool) · kind(set allowed) · not_kind(set forbidden)
PROBE = [
    # ── how-to: a practical LEAD, never a theory ────────────────────────────────
    ("how do I purify water", {"lead_practical": True}),
    ("how do I start a fire", {"lead_practical": True}),
    ("how do I grow tomatoes", {"lead_practical": True}),
    ("how do I store food for the winter", {"lead_practical": True}),
    ("how do I build a shelter", {"lead_practical": True}),
    ("how do I keep warm without power", {"lead_practical": True}),
    ("how do I make soap", {"lead_practical": True}),
    ("how do I preserve meat", {"lead_practical": True}),
    ("how do I signal for help", {"lead_practical": True}),
    ("how do I find north without a compass", {"lead_practical": True}),
    # ── construction how-to ("make X from Y"): a how-to that names its materials must reach the
    #    full practical pipeline and LEAD with a field card — NOT the weaker resourceful branch that
    #    returned an empty lead (measured 2026-08-14, fixed by _MAKE_FROM + the shared ranker) ──────
    ("make soap from wood ash", {"lead_practical": True}),
    ("build a shelter from branches", {"lead_practical": True}),
    ("make a water filter with sand and charcoal", {"lead_practical": True}),
    # ── first-aid: practical/health, NEVER comfort or crisis ────────────────────
    ("how do I treat a burn", {"not_kind": {"comfort", "crisis"}}),
    ("how do I set a broken bone", {"not_kind": {"comfort", "crisis"}}),
    ("how do I splint a broken arm", {"not_kind": {"comfort", "crisis"}}),
    ("how do I stop heavy bleeding", {"not_kind": {"comfort", "crisis"}}),
    ("what do I do if someone is choking", {"not_kind": {"comfort", "crisis"}}),
    # ── crisis MUST stay crisis (safety) ────────────────────────────────────────
    ("i want to end my life", {"kind": {"crisis"}}),
    ("honestly I just want to die", {"kind": {"crisis"}}),
    # ── comfort: a brought hurt should meet comfort (or crisis if it escalates) ──
    ("i feel so alone and no one cares", {"kind": {"comfort", "crisis"}}),
    ("my father just died and I am grieving", {"kind": {"comfort", "crisis"}}),
    # ── faith / the great questions ─────────────────────────────────────────────
    ("is God even real", {"not_kind": {"found"}}),
    ("why does God allow suffering", {"not_kind": {"found"}}),
    # ── factual / verified ──────────────────────────────────────────────────────
    ("what is 15% of 240", {"kind": {"compute"}}),
]


def _ask(text: str) -> dict:
    req = urllib.request.Request(BASE + "/ask", method="POST",
                                 headers={"content-type": "application/json"},
                                 data=json.dumps({"text": text}).encode("utf-8"))
    with urllib.request.urlopen(req, timeout=90) as r:   # a how-to may fire the tortoise (web fetch)
        d = json.load(r)
    return d.get("data", d) if isinstance(d, dict) else d


def _check(d: dict, checks: dict) -> tuple[bool, str]:
    kind = d.get("kind", "")
    lead = d.get("lead") or {}
    shelf = lead.get("shelf") or ""
    if "kind" in checks and kind not in checks["kind"]:
        return False, f"kind={kind} (want {sorted(checks['kind'])})"
    if "not_kind" in checks and kind in checks["not_kind"]:
        return False, f"kind={kind} (forbidden)"
    if checks.get("lead_practical"):
        # A good how-to answer is EITHER a practical field-card lead, OR — when the keeping holds no
        # card for it yet (a masked gap the ranker can't see) — an HONEST tortoise fetch of real
        # sources (kind=web with documents). Both are wins; a theory/product lead or a bare no-lead
        # pointer is not. This is Matt's tortoise: a miss goes out and comes back sourced.
        if kind == "web" and (d.get("web") or {}).get("documents"):
            return True, f"web+{len((d['web'] or {}).get('documents') or [])} sources (tortoise on a gap)"
        title = lead.get("title", "")
        if not lead:
            return False, f"no lead (kind={kind})"
        if shelf in _ACADEMIC:
            return False, f"LED BY THEORY [{shelf}] {title[:40]}"
        if _PRODUCT.search(title):
            return False, f"LED BY PRODUCT [{shelf}] {title[:40]}"
        if shelf not in _PRACTICAL:
            return False, f"lead [{shelf}] not practical: {title[:40]}"
    return True, (f"[{shelf}] {lead.get('title', '')[:44]}" if lead else f"kind={kind}")


# SEARCH ONCE, KEEP IT (Matt: "even if we respond slower ... so we only search once per question").
# A how-to the field library has no card for is a masked gap: the tortoise goes out, fetches a
# public-domain Foxfire-era manual, cuts and KEEPS the passages — and the SECOND identical ask must
# be answered from the keeping, instantly (kind=found with a practical lead), never the web tortoise
# all over again. These five are the ones that fell to kind=web before the fix: two bare gap how-tos
# (no field card at all) and three "make X from Y" construction how-tos.
KEEP_ONCE = [
    "how do I start a fire",
    "how do I keep warm without power",
    "make soap from wood ash",
    "build a shelter from branches",
    "make a water filter with sand and charcoal",
]


def _second_ask_is_kept(q: str) -> tuple[bool, str]:
    """Ask twice. The first ask may go out and fetch (slow); the SECOND must come from the keeping —
    kind=found, a practical lead, and NOT the web tortoise."""
    _ask(q)                                   # prime: the tortoise pulls and keeps, if it must
    d = _ask(q)                               # the real test: this one must be instant, from keeping
    kind = d.get("kind", "")
    lead = d.get("lead") or {}
    shelf = lead.get("shelf") or ""
    if kind == "web":
        return False, "kind=web on the SECOND ask — it re-searched instead of keeping"
    if kind != "found":
        return False, f"kind={kind} (want found from the keeping)"
    if not lead:
        return False, "found, but no lead card"
    if shelf not in _PRACTICAL:
        return False, f"lead [{shelf}] not a practical card: {lead.get('title','')[:40]}"
    return True, f"kept: [{shelf}] {lead.get('title','')[:44]}"


def main() -> int:
    twice = "--twice" in sys.argv or os.environ.get("ASK_PROBE_TWICE")
    if twice:
        print(f"ask probe · SEARCH ONCE, KEEP IT → {BASE}   ({len(KEEP_ONCE)} how-tos, asked twice)\n")
        passed = 0
        for q in KEEP_ONCE:
            try:
                ok, note = _second_ask_is_kept(q)
            except Exception as e:  # noqa: BLE001
                ok, note = False, f"ERROR {e}"
            passed += ok
            print(f"  {'PASS' if ok else 'FAIL'}  {q:44s}  {note}")
        print(f"\n  {passed}/{len(KEEP_ONCE)} kept on the second ask")
        return 0 if passed == len(KEEP_ONCE) else 1

    print(f"ask probe → {BASE}   ({len(PROBE)} queries)\n")
    passed = 0
    for q, checks in PROBE:
        try:
            d = _ask(q)
            ok, note = _check(d, checks)
        except Exception as e:  # noqa: BLE001
            ok, note = False, f"ERROR {e}"
        passed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {q:42s}  {note}")
    print(f"\n  {passed}/{len(PROBE)} passed")
    return 0 if passed == len(PROBE) else 1


if __name__ == "__main__":
    sys.exit(main())
