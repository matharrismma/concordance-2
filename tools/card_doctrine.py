#!/usr/bin/env python3
"""Card the RECURRING ARCHITECTURE out of Matt's planning documents, so the concepts are usable.

Matt, 2026-07-30, on six documents at once: *"They don't have to co-exist right now, but I do want
all of the concepts used that are beneficial."*

So this does not adopt any document wholesale — no commercial frame, no capital plan, no hardware
programme enters the system as policy. It harvests the CONCEPTS, attributed, and puts them where
they can be found: in the keeping, searchable, in the graph, reachable by an agent.

WHAT THE SIX DOCUMENTS SHARE, which is the actual finding. Read together — a theology companion, a
company vision, a community capital plan, a watch design bible, an energy architecture, and a
humanoid robot planning bible — they describe ONE pattern in six materials:

    a request is not an authority · authority is bounded and separated from execution ·
    an independent witness observes the result · the record is sealed OUTSIDE the requester ·
    and the whole thing degrades in a stated order rather than collapsing

The robot says it most plainly ("The Main may request… the record is sealed outside the requesting
process"); The Way says it as governance (the household owns, the community governs, the Levites
administer, and the founder's authority SUNSETS); the Floor says it as world physics (RED · FLOOR ·
BROTHERS · GOD). This is [[feedback_systems_of_the_world_recurring_design_2026-07-25]] — one design
over many planes — and it is worth carding precisely because the same shape keeps proving itself.

CONDUIT, NOT AUTHOR. Every card below quotes or closely paraphrases Matt's own text and names the
document it came from. `generated: false` — these are his words, gathered
([[feedback_gather_dont_author_wisdom_aligns_2026-07-11]]), not mine invented.

    PYTHONPATH=src python tools/card_doctrine.py            # write data/doctrine_cards.jsonl
    PYTHONPATH=src python tools/card_doctrine.py --dry-run  # show what would be written
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "data" / "doctrine_cards.jsonl"
SHELF = "doctrine"

# Each source document, named once so every card can carry its provenance.
SRC = {
    "floor": ("The Floor of Discovery — Biblical Foundations of Concordance",
              "Matt Harris, companion to Root Access: Master Planning Bible"),
    "vision": ("Concordance — Company Vision & Offering at Scale", "Matt Harris"),
    "way": ("The Way — Distributed and Planned Community Technical and Capital Plan v0.2",
            "Matt Harris, working draft July 2026"),
    "prism": ("Project Prism — The Architecture of Time, Design Bible v2.3", "Matt Harris"),
    "ugm": ("Universal Gradient Manifold — A Heat-Source-Agnostic Energy Operating System",
            "Matt Harris"),
    "robot": ("Humanoid Robot — Integrated Architecture and Development Planning Bible v0.2",
              "Matt Harris"),
}

# (key, title, body, source key, what it already governs in the live system)
CONCEPTS = [
    ("authority_chain",
     "A request is not an authority — the four-layer chain",
     "\"The Main may request. The Steward may admit a bounded capability. The Motion Executive may "
     "generate only approved trajectories. The Reflex layer continuously limits pressure, flow, "
     "current, force, speed, balance, and joint state. Independent sensors witness the result, and "
     "the record is sealed outside the requesting process.\"\n\n"
     "Stated for a robot, this is the general law the other documents restate in their own "
     "materials: intelligence may PROPOSE; a separate, independently governed layer determines what "
     "may actually happen; and the record of what happened is kept somewhere the requester cannot "
     "reach. The value is in the separation, not in any one layer's cleverness.",
     "robot",
     "Already load-bearing here: `shelves.curate` refuses a typed name as authority and keeps the "
     "check in the module so neither the HTTP nor the MCP door can bypass it; `consent.guard()` "
     "admits a bounded capability for an agent; every curation act is sealed with a steward and a "
     "reason in an append-only record the actor cannot edit."),

    ("four_gates",
     "The four gates — RED · FLOOR · BROTHERS · GOD",
     "RED — submission to the words spoken by Jesus as the ultimate attestation and computational "
     "standard; the first and hardest gate, and everything downstream activates only after it is "
     "satisfied.\nFLOOR — the unified Bible and physical reality as ONE integrated floor: "
     "\"Special Revelation and General Revelation are not two domains. They are one floor.\"\n"
     "BROTHERS — the witness principle (Deuteronomy 19:15, Matthew 18:16): nodes cannot "
     "self-validate; two or three witnesses establish a matter.\nGOD — final submission to the "
     "Architect; the moment every claim is weighed against the true floor.\n\n"
     "In the narrative these are never named in-world. Characters experience them as how reality "
     "itself works — physics, not policy.",
     "floor",
     "Three of the four are built: RED and FLOOR exist as attestations (`attest_red`, "
     "`attest_floor`), and BROTHERS is the moderation floor's rule that three DISTINCT SIGNING "
     "witnesses — keys, never typed names — are needed to hold an item for a human. GOD, the "
     "time-window gate, is NOT built; it is the honest gap in the set."),

    ("reservoir_manifold",
     "The reservoir and the manifold — value is in the routing layer, not the engine",
     "\"The most valuable asset in an energy system is not the fuel or the engine. It is the "
     "reservoir that stores a gradient and the manifold that routes that gradient to useful work.\"\n\n"
     "Source → Gradient → Reservoir → Manifold → Converter → Work. Biology standardizes energy "
     "through ATP, and the key insight is not the molecule but the COMMON INTERFACE. The manifold "
     "decouples sources from loads and allows many inputs and many outputs; it is the enduring "
     "platform while fuels, engines, and storage technologies evolve.",
     "ugm",
     "The same shape as the keeping: sources → cards (the reservoir) → search and the graph (the "
     "manifold) → verifiers (the converter) → an answer a person can use. It is also why a card "
     "stays bare while presentation is derived on the way out — the record is the reservoir, and "
     "the experience layer is a converter that must never be welded to it."),

    ("gate_closure",
     "A gate closes against a number, an owner, and a fallback",
     "\"Symmetry of rigor… every gate closes against a number, an owner and a fallback.\" Gate Zero "
     "is feasibility BEFORE form: the architecture is not permitted to proceed on enthusiasm, only "
     "on a first-order budget that closes. Numbers that are provisional are marked provisional — "
     "\"design targets, not measured performance\".",
     "prism",
     "Stronger than what this project's own gate does. `tools/check.py` closes against a number "
     "(coverage floors, 0 false positives, a real exit code) but names no OWNER and no FALLBACK for "
     "a failing gate. The punch list has completion tests; it does not say who answers for each or "
     "what happens if one cannot close. Worth adopting."),

    ("authority_sunset",
     "Founder authority sunsets — the centre becomes a service, not a ruler",
     "\"The founder has no permanent operational authority over local villages; startup authority "
     "sunsets into the ordinary governance system.\" Launch steward authority ends automatically at "
     "36 months or when three communities are operating, whichever comes first. Capital earns "
     "economic rights, NEVER additional political votes. One household cannot purchase more "
     "political power by contributing more capital.\n\n"
     "\"The permanent centre is therefore a service architecture\": liquidity, administration, and "
     "the common rule are supplied centrally; government and leaders are local.",
     "way",
     "Bears directly on the Commons. The steward token is today a single permanent secret with no "
     "expiry, no rotation, and no record of who holds it — the opposite of a sunsetting authority. "
     "The principle also already governs the shelf: a member's own signature withdraws their own "
     "card, because ownership is local and the centre only carries."),

    ("exit_is_funded",
     "A funded right of exit, or it is not voluntary",
     "\"Membership is voluntary, and every household has a practical, FUNDED right of exit.\" No "
     "single entity controls a member's housing, employment, money, church standing, healthcare, "
     "and exit rights. Enrollment does not transfer title or create a lien unless separately and "
     "expressly granted. The Seed Trust is \"a standing buyer, not a governing owner\".\n\n"
     "Membership levels are modular and separately signed, so participation is never confused with "
     "encumbrance.",
     "way",
     "The software equivalent already holds and should be named as the same principle: a shelf is a "
     "key the member holds, the server keeps only public keys, private drops are withheld by the "
     "one public boundary, and a member can withdraw their own words with their own signature. "
     "Exit is not a feature request here; it is the default state."),

    ("degradation_order",
     "A stated degradation order — what is shed first, decided before the pressure",
     "The energy architecture names an explicit degradation order rather than letting a system "
     "discover its priorities under load, and the operating states are steward-enforced with a "
     "declared capability window. A system that has not decided what it sheds first will shed "
     "whatever fails first, which is rarely what it would have chosen.",
     "robot",
     "This project has the mechanism and not the statement: shards freeze and unfreeze, and the "
     "`core` shard can never be frozen — that IS a degradation order, but it is nowhere written as "
     "one. What gets served when memory, disk, or network is short should be a declared order a "
     "reader can check, not an emergent property of which code path happens to fail."),

    ("agents_are_the_users",
     "The dominant users of intelligence will not be humans",
     "\"By 2028–2030, the dominant users of intelligence will not be humans — they will be "
     "autonomous agents and multi-agent systems generating and acting on billions of claims per "
     "day.\" The failure modes named: hallucination and drift at machine speed; O(n²) coordination "
     "collapsing under swarm volume; no external grounding; and an audit and liability crisis with "
     "no scalable way to verify AI-mediated decisions.",
     "vision",
     "MEASURED, not predicted: on 2026-07-30 the access logs showed ClaudeBot at 44,439 requests — "
     "35% of ALL traffic — with GPTBot behind it, the card permalink the single most-used thing "
     "here (46,190), and `/mcp` being indexed by agent registries and scoring engines. The thesis "
     "is arriving early and can be checked against the log rather than argued."),
]


def build() -> list:
    cards = []
    spine = {
        "id": "card_spine_doctrine", "kind": "note",
        "title": "The recurring architecture — one pattern, six materials",
        "body": ("Concepts gathered from Matt Harris's planning documents — a theology companion, a "
                 "company vision, a community capital plan, a watch design bible, an energy "
                 "architecture, and a humanoid robot planning bible. Read together they describe "
                 "ONE pattern in six materials: a request is not an authority; authority is bounded "
                 "and separated from execution; an independent witness observes the result; the "
                 "record is sealed outside the requester; and the whole degrades in a stated order.\n\n"
                 "These are carried as CONCEPTS, not adopted as policy. Where one already governs "
                 "something live, the card says so and names it."),
        "source": {"label": "Matt Harris — planning documents, 2026",
                   "authority_tier": "author"},
        "shelf": SHELF, "box": "spine", "bands": ["doctrine", "architecture", "recurring form"],
        "subject": "the recurring architecture",
        # ROOTED, because nothing in the keeping is an island. The first run of this carder shipped
        # the spine with `connections: []` and the gate refused it — 9 cards stranded in a new
        # island that never reaches the Floor. That guard is the whole reason a doctrine card is
        # worth having: an idea nobody can walk to from the Floor is not part of the map.
        "connections": [{"to_card_id": "card_k_spine_the_word", "relationship": "part_of",
                         "evidence": "the pattern was unpacked from Scripture, not invented — "
                                     "the Floor of Discovery names the Word as its source"}],
        "author": "matt", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "durable",
        "surface": "secular", "generated": False,
        "extra": {"documents": len(SRC)},
    }
    cards.append(spine)

    for key, title, body, srckey, applies in CONCEPTS:
        label, who = SRC[srckey]
        cards.append({
            "id": f"card_doctrine_{key}", "kind": "note", "title": title,
            "body": body + "\n\nWHERE IT ALREADY BEARS WEIGHT — " + applies,
            "source": {"label": f"{label} — {who}", "ref": label,
                       "authority_tier": "author"},
            "shelf": SHELF, "box": "concept",
            "bands": ["doctrine", "architecture", key.replace("_", " ")],
            "subject": title,
            "connections": [{"to_card_id": "card_spine_doctrine", "relationship": "part_of",
                             "evidence": "one of the recurring-architecture concepts"}],
            "author": "matt", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "durable",
            "surface": "secular", "generated": False,
            "extra": {"document": label, "concept": key},
        })
    return cards


def main() -> int:
    cards = build()
    if "--dry-run" in sys.argv:
        for c in cards:
            print(f"  {c['id']:<34} {c['title'][:64]}")
        print(f"\n{len(cards)} cards (dry run — nothing written)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    avg = sum(len(c["body"]) for c in cards) // len(cards)
    print(f"wrote {len(cards)} cards to {OUT}  (avg body {avg} chars)")
    print("register it in corpus.py's loader list, then rebuild shards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
