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
        # Matt, 2026-10-02 (spoken for the Playbook; "mint"): the game, in his words.
        _card("card_playbook_the_game", "The Game — opening, midgame, closing; two gates, green and red",
              ("The Prisoner's Dilemma: there are many and no true opponents. It isn't two-sided. Multifaceted, "
               "but also it can expand and contract. Opening, midgame and closing. Opening is the optimal path. "
               "Midgame is tit for tat until the finish position is achieved, and then run the final play until "
               "closing. Two gates: green and red. — Matt Harris, 2026-10-02.\n\n"
               "Where it lives in the engine: GREEN is the FLOOR gate (attest_floor — does it break stability or "
               "moral floors?), RED is the RED gate (attest_red — is it aligned with Christ?); kernel.gate rejects a "
               "move on a RED hit or a FLOOR error. The opening is the PATH (wayfind.path — one next step). The "
               "midgame is the reciprocity pattern of the Strategy Concordance (cooperate first, answer in kind, "
               "forgive, be clear) until the finish position. The closing is the final play run to the seal. "
               "'Many and no true opponent' is measured: the opponent is the population's current mix, and the mix "
               "moves — cooperation expands above a critical mass of reciprocators and contracts below it "
               "(game_theory.population; at w = 0.9 six in a hundred are enough), sealed at "
               "https://narrowhighway.org/s/584a4cf4dc91444db1681cc175d53231ca3c332638acb799f01b52389e6d169b. "
               "The Gospel asks more than reciprocity (Matthew 5:44), never less (Matthew 7:12)."),
              ["the-game", "prisoners-dilemma", "opening", "midgame", "closing", "green", "red", "reciprocity"],
              "the game",
              {"phases": ["opening = optimal path", "midgame = tit for tat until the finish position",
                          "closing = the final play"],
               "gates": {"green": "FLOOR", "red": "RED"}, "spoken": "2026-10-02",
               "seal": "https://narrowhighway.org/s/584a4cf4dc91444db1681cc175d53231ca3c332638acb799f01b52389e6d169b"}),
    ]
    # the game's card names the two hard gates and the midgame pattern it runs on
    cards[-1]["connections"] += [
        {"to_card_id": "card_playbook_gate_floor", "relationship": "uses", "evidence": "GREEN = the FLOOR gate"},
        {"to_card_id": "card_playbook_gate_red", "relationship": "uses", "evidence": "RED = the RED gate"},
        {"to_card_id": "card_pattern_reciprocity", "relationship": "uses",
         "evidence": "the midgame is tit for tat — the reciprocity pattern of the Strategy Concordance"},
    ]
    # the keeping's call number + facets on every card, as classify_keeping persists them (the box's copies
    # carry them; a regenerated file must not strip them — the parity check would show the drift)
    try:
        from concordance.corpus import shelve
        for c in cards:
            shelve(c)
    except Exception as e:  # noqa: BLE001 — a bare checkout without the corpus module still mints
        print(f"  (call numbers not applied: {e})", file=sys.stderr)
    out = Path("data") / "playbook_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} playbook cards (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
