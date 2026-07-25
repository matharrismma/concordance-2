#!/usr/bin/env python3
"""Card Matt's authored framework — the Fractal Playbook — into the corpus as a small deck.

The Fractal Playbook (`Lighthouse/lw/08_docs/foundations/01_fractal_playbook.md`) is the Body's
shared memory of faithful obedience to the Head (Jesus Christ, the Word). Its atomic unit — Confession,
Anchors, Action, Outcome, Witness, Wait, Status — and its Four Gates of Confirmation (RED / FLOOR /
BROTHERS / GOD) are the same pattern the whole engine runs on: a claim is quarantined until it aligns
with Christ, holds the floor, is witnessed, and survives a wait. "One pattern. Repeated faithfully."

Conduit, not source: each card is gathered from Matt's authored doc, attributed, generated=False.
Nested under a playbook spine → the Word (obedience to the Head). Git-tracked (authored content).

    PYTHONPATH=src python tools/card_playbook.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

WORD = "card_k_spine_the_word"
SPINE = "card_spine_playbook"
SRC = "The Fractal Playbook (Final) — Lighthouse/lw/08_docs/foundations/01_fractal_playbook.md"


def _card(cid, title, body, bands, subject, extra=None):
    return {
        "id": cid, "kind": "reference", "title": title[:180], "body": body,
        "source": {"label": SRC, "url": "", "domain": "playbook", "authority_tier": "reference"},
        "shelf": "playbook", "box": "framework",
        "bands": ["playbook", "framework", "obedience"] + list(bands),
        "subject": subject,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a piece of the Fractal Playbook framework"}],
        "author": "Matt Harris (Fractal Playbook)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": extra or {},
    }


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The Fractal Playbook — the Body's memory of obedience",
        "body": ("The Body's shared memory of faithful obedience to the Head (Jesus Christ, the Word). "
                 "Head = authority; Body = people acting in obedience; Playbook = the testimony of what "
                 "was done, what happened, what was corrected. It is NOT Scripture — it cannot create "
                 "doctrine or bind conscience. One pattern, repeated faithfully at every scale."),
        "source": {"label": SRC, "url": "", "domain": "", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["playbook", "framework", "obedience", "spine"],
        "subject": "the fractal playbook",
        "connections": [{"to_card_id": WORD, "relationship": "part_of",
                         "evidence": "the Body's obedience to the Head — rooted in the Word"}],
        "author": "Matt Harris (Fractal Playbook)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }
    cards = [
        spine,
        _card("card_playbook_atomic_unit", "The Atomic Unit — a Playbook Entry",
              ("Each entry is a single fractal unit: (1) Confession — 'I may be wrong…'; (2) Anchors — the "
               "Scripture refs used; (3) Action — OPEN / BUILD / RESERVE / PRUNE / HOLD; (4) Outcome — "
               "fruit / mixed / failed; (5) Witness — at least two affirmations to confirm; (6) Wait — a "
               "mandatory time gate; (7) Status — QUARANTINE → CONFIRMED (or REJECTED)."),
              ["atomic", "unit", "entry", "confession", "witness", "wait", "status"], "the playbook entry",
              {"fields": ["Confession", "Anchors", "Action", "Outcome", "Witness", "Wait", "Status"],
               "actions": ["OPEN", "BUILD", "RESERVE", "PRUNE", "HOLD"]}),
        _card("card_playbook_gate_red", "Four Gates — RED (aligned with Christ)",
              "The first gate of confirmation: is it aligned with Christ? Reject if not. The Words in Red govern.",
              ["four-gates", "red", "christ", "align"], "the RED gate", {"gate": "RED"}),
        _card("card_playbook_gate_floor", "Four Gates — FLOOR (holds the moral/stability floor)",
              "The second gate: does it break stability or moral floors? Reject if broken.",
              ["four-gates", "floor", "stability", "moral"], "the FLOOR gate", {"gate": "FLOOR"}),
        _card("card_playbook_gate_brothers", "Four Gates — BROTHERS (witnesses affirm)",
              "The third gate: do the witnesses affirm? Quarantine until at least two are met (Matthew 18:16).",
              ["four-gates", "brothers", "witness", "quarantine"], "the BROTHERS gate", {"gate": "BROTHERS"}),
        _card("card_playbook_gate_god", "Four Gates — GOD (the wait completes)",
              "The fourth gate: has the wait period completed? Quarantine until the time gate is met. God confirms in time.",
              ["four-gates", "god", "wait", "time", "quarantine"], "the GOD gate", {"gate": "GOD"}),
        _card("card_playbook_pruning", "Pruning — entries are not permanent truth",
              ("Entries may be corrected, superseded, pruned, or marked 'failed'. Failure is not hidden; "
               "it is used to refine faithfulness (John 15:2 — every branch that bears fruit He prunes)."),
              ["pruning", "correction", "failure", "refine"], "pruning"),
        _card("card_playbook_universality", "Universality — one pattern at every scale",
              ("Because the structure is identical at every scale, the Playbook is portable: personal "
               "discipleship, family governance, church operations, economic development, engineering "
               "decisions. One pattern. Repeated faithfully."),
              ["universality", "fractal", "scale", "portable"], "universality"),
    ]
    out = Path("data") / "playbook_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} playbook cards (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
