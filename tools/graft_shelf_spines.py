"""Root the spine-less shelves — every structurally-bare card gets its shelf's home.

The keeping's rule: every card carries at least one STRUCTURAL relation (member_of/part_of), so any
card can be walked back to the Floor. On 2026-07-28 the reachability walk found 552 cards in closed
islands — codex notes and Boethius sections bound to each other by `same_section` with no edge out
to anything rooted. The cause is one shape: the 1.0-era authored shelves (codex, classics,
patristics, hymns, …) were minted BEFORE the spine convention existed, so those shelves have no
`card_spine_*` at all and their cards carry only semantic relations.

Matt's decision (2026-07-28): root them with shelf spines — the FOUND relation, same rule as the
tortoise fix in `find._SPINES`. "This card is on this shelf" is a fact the card already carries;
the spine text is authored, the graft is not. Two cases, both explicit:

  * SPINES  — shelves with no structural home: mint `card_spine_<shelf>` rooted `part_of` the
              Floor, and graft every structurally-bare card `member_of` it.
  * REDIRECTS — shelves that ALREADY have an established structural parent (dictionary's 146,871
              cards are member_of card_spine_words; chemistry's 120 hang on the created order):
              bare cards join their SIBLINGS' parent. No second home is invented for a shelf that
              has one — two parents for one shelf would be its own kind of lie.

Anything bare on a shelf in NEITHER spec is REPORTED and left alone (the graft_orphans discipline:
graft what is certain, name what is not, never guess). Idempotent: cards already structured are
never touched; spines already present are not re-minted.

Note: `card_k_spine_the_word` (the Word-half of the Floor) is itself shelved `codex` and already
structured — it is skipped by the bare-only rule automatically, and codex NOTES get their own
`card_spine_codex` rather than hanging 794 cards directly off the Floor.

    python tools/graft_shelf_spines.py --dry-run     # show the plan
    python tools/graft_shelf_spines.py               # write it
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"
NESTING = {"member_of", "part_of", "nested_in", "figure_of",
           "has_member", "has_part", "contains", "has_figure"}

# Shelves that get a NEW spine, rooted in the Floor. Titles/bodies are authored; the graft is found.
SPINES = {
    "codex":      ("The Codex — the core theological work",
                   "The manuscript: worked notes on the Word — scripture expositions, themes, and "
                   "the connections between them. The codex is the study half of the keeping."),
    "classics":   ("The classics — the great books, kept whole",
                   "Sections of the enduring works (Boethius and company), kept as they were "
                   "written and read section by section."),
    "patristics": ("The patristics — the church fathers",
                   "Sections from the early fathers of the church, kept in their own words."),
    "the-works":  ("The Works — sealed, worked demonstrations",
                   "Every worked, engine-sealed demonstration carded as a seed in the keeping."),
    "animation":  ("The animations — motion that shows a truth",
                   "Animated demonstrations kept in the keeping."),
    "hymns":      ("The hymns — the songs of the faith",
                   "Hymn texts kept in the keeping, sung before they were stored."),
    "maker":      ("The maker's bench — plans and builds",
                   "Maker plans and builds kept in the keeping."),
    "recipes":    ("The recipes — food that has fed people",
                   "Recipes kept in the keeping."),
    "atlas":      ("The atlas — maps of the mappable",
                   "Atlas cards kept in the keeping."),
    # Box-only vintage: 17 "Pressure Architecture" notes live in the DROPLET's cards.jsonl and
    # nowhere locally. Same island shape, same decision, same found rule.
    "domains":    ("The domains — the systems of the world",
                   "Authored notes on the recurring architecture that runs through the systems of "
                   "the world — one design, seen across domains."),
}

# Shelves whose bare cards join their SIBLINGS' established parent — no new spine.
REDIRECTS = {
    "dictionary": "card_spine_words",           # 146,871 siblings already live there
    "chemistry":  "card_k_spine_created_order",  # 120 siblings already live there
    # Old-vintage runtime mints on the box: the CURRENT science_cards.py mint carries
    # part_of card_k_spine_created_order (so the path is already fixed — these are residue),
    # and labor's local siblings hang on the created order too.
    "science":    "card_k_spine_created_order",
    "labor":      "card_k_spine_created_order",
}

# Every plain-jsonl store a graftable card might live in. (.gz corpora are reference decks whose
# cards are minted WITH member_of already — verified by the shortfall report below coming up zero.)
DATA_FILES = ("cards.jsonl", "works_cards.jsonl", "reference_cards.jsonl", "web_cache.jsonl",
              # the two stragglers the first run reported: a verified card and a keystone seed,
              # each also mirrored in a bridges file — graft every copy so the stores stay agreed
              "verified_cards.jsonl", "works_bridges.jsonl",
              "keystone_seeds.jsonl", "keystone_bridges.jsonl")


def _spine_card(shelf: str) -> dict:
    title, body = SPINES[shelf]
    return {"id": f"card_spine_{shelf}", "kind": "reference", "title": title, "body": body,
            "source": {"label": "The keeping — a spine of the authored shelves", "url": "",
                       "domain": "", "authority_tier": "reference"},
            "shelf": "spine", "box": "spine", "bands": [shelf, "spine", "keeping"],
            "subject": title,
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": "a spine of the keeping, rooted in the Floor of Discovery"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False}


def _target_for(shelf: str) -> str | None:
    if shelf in SPINES:
        return f"card_spine_{shelf}"
    return REDIRECTS.get(shelf)


def main() -> int:
    dry = "--dry-run" in sys.argv
    from concordance import corpus
    cards = corpus.default_corpus().cards

    # The plan: every structurally-bare, non-connection card on a shelf we have a considered home for.
    plan: dict = {}          # card_id -> target parent id
    unplanned = Counter()    # bare cards on shelves with no considered home — reported, not guessed
    for cid, c in cards.items():
        if c.get("kind") == "connection" or cid.startswith("card_spine_"):
            continue
        links = c.get("connections") or []
        if any(isinstance(l, dict) and l.get("relationship") in NESTING for l in links):
            continue  # already structured — never touched
        t = _target_for(c.get("shelf") or "")
        if t:
            plan[cid] = t
        else:
            unplanned[c.get("shelf") or "?"] += 1

    by_shelf = Counter(cards[cid].get("shelf") for cid in plan)
    print(f"structurally-bare cards with a considered home: {len(plan)}")
    for sh, n in by_shelf.most_common():
        print(f"  {sh:<12} {n:>6}  -> {_target_for(sh)}")
    spines_needed = [s for s in SPINES if f"card_spine_{s}" not in cards
                     and any(cards[cid].get("shelf") == s for cid in plan)]
    print(f"spines to mint: {spines_needed or 'none (already present)'}")
    if unplanned:
        print(f"\nNOT GRAFTING (no considered home — decide, do not default): {dict(unplanned)}")

    if dry:
        print("\n--dry-run: nothing written.")
        return 0
    if not plan and not spines_needed:
        print("nothing to do.")
        return 0

    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    grafted = 0
    for name in DATA_FILES:
        p = base / name
        if not p.exists():
            continue
        out, changed = [], 0
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                c = json.loads(ln)
            except ValueError:
                out.append(ln)
                continue
            t = plan.get(c.get("id"))
            # re-check bareness against the FILE, not just the in-memory corpus
            links = c.get("connections") or []
            if t and not any(isinstance(l, dict) and l.get("relationship") in NESTING for l in links):
                c.setdefault("connections", []).append(
                    {"to_card_id": t, "relationship": "member_of",
                     "evidence": f"a member of the {c.get('shelf')} shelf in the keeping"})
                changed += 1
            out.append(json.dumps(c, ensure_ascii=False))
        if name == "cards.jsonl":  # spines live beside the cards they root (main store)
            for s in spines_needed:
                out.append(json.dumps(_spine_card(s), ensure_ascii=False))
        if changed or (name == "cards.jsonl" and spines_needed):
            p.write_text("\n".join(out) + "\n", encoding="utf-8")
            print(f"wrote {name}: {changed} card(s) grafted"
                  + (f", {len(spines_needed)} spine(s) added" if name == "cards.jsonl" else ""))
        grafted += changed

    print(f"\ngrafted {grafted} of {len(plan)} planned.")
    if grafted != len(plan):
        # Honest shortfall: these live in a store this tool does not rewrite (likely a .gz deck).
        missing = len(plan) - grafted
        print(f"NOTE: {missing} planned card(s) were not found in {DATA_FILES} — they live in "
              "another store and still need a home. Do not call this done.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
