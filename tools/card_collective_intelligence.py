#!/usr/bin/env python3
"""COLLECTIVE INTELLIGENCE — the measured natural systems that ARE our architecture.

Matt, 2026-09-27: "Look at animal behavior. Ants, bees, birds, orcas... these systems have interactions
that have been measured. We need to see how they fit into the system." They fit exactly: each is a
MEASURED instance of the same form our engine runs — decentralized local rules producing coherent global
behavior, no central controller, the group doing what no member can alone. We did not invent the
architecture; we uncovered it (the concordance of reality; elegance as God's signature). Each maps
one-to-one onto one of our four mechanisms.

Conduit, not author: the mechanism of each is the MEASURED science (cited); the mapping to our system is
the "systems of the world" recurring-form connection (kin to the strategy concordance's "decentralize =
the colony without a center: ants"). generated=False. Rooted under a spine -> the Floor. Git-tracked.

    python tools/card_collective_intelligence.py            # (re)write data/collective_intelligence_cards.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_collective_intelligence"

# (id, animal, title, MEASURED mechanism + source, OUR mechanism it maps to + how, bands)
SYSTEMS = [
    ("ants", "Ant stigmergy",
     "Ants coordinate with no central plan and no direct messaging: each leaves and reads pheromone in "
     "the shared environment (STIGMERGY). Positive feedback converges the colony on the shortest path; "
     "EVAPORATION keeps exploration alive so it never locks in too early; the deposit is proportional to "
     "path quality. Measured, and formalized as a proven algorithm — Ant Colony Optimization (Dorigo).",
     "THE KEEPING. Our cards are the pheromone trails; the keeping is the shared environment through which "
     "the engine coordinates — no runtime swarm messaging. A retrieval deposits a trail (stigmergy.py); "
     "unused trails evaporate; recall self-organizes toward what serves. The connections are the "
     "reinforced paths.",
     ["ants", "stigmergy", "pheromone", "ant colony optimization", "swarm", "self-organization"]),
    ("bees", "Honeybee quorum",
     "A honeybee swarm choosing a new home decides by DISTRIBUTED, quality-weighted voting: a scout "
     "advertises a site with waggle-dance vigor proportional to its QUALITY, and the swarm commits only "
     "when a QUORUM (~15 scouts at one site) is reached — measured bee-by-bee by Thomas Seeley on "
     "Appledore Island. The mechanism reliably picks the best of the options.",
     "THE CONDUCTOR. The engine weighs options by measured quality and commits when enough independent "
     "evidence converges — a quorum, not a guess. Honest advertising (a scout never oversells a poor "
     "site) is our 'our failure is not their falsehood'; the quorum is the 'two or three gathered'.",
     ["bees", "honeybee", "quorum", "waggle dance", "swarm decision", "seeley", "collective decision"]),
    ("birds", "Starling murmuration",
     "Thousands of starlings turn as one with no leader. Filmed in 3D (Cavagna, Giardina; STARFLAG, Rome), "
     "each bird tracks a FIXED number of neighbours — about six or seven, TOPOLOGICAL, not by distance — "
     "and the flock shows SCALE-FREE correlation: a perturbation crosses 50,000 birds as fast as 500 "
     "(Cavagna et al., PNAS 2010). Local rules, global coherence.",
     "THE MESH / THE FASCIA. Each node keeps a fixed set of links (topological, like a mesh friend-link), "
     "and a signal propagates across the whole body regardless of size — the fractal polymathic mesh, "
     "'everything connects on planes'. Coherence with no central node.",
     ["birds", "starlings", "murmuration", "flocking", "boids", "scale-free", "topological", "mesh"]),
    ("orcas", "Orca matrilines & dialects",
     "Killer whales live in MATRILINES (matriarch-led, up to four generations, females to ~90) and carry "
     "learned vocal DIALECTS passed down the family — measured CULTURE, 'vocal clans' that fingerprint a "
     "group. Cooperative hunts run on ROLE specialization coordinated by real-time calls (Ford; Rendell & "
     "Whitehead on cetacean culture).",
     "THE WITNESS WIRE + THE CLOUD OF WITNESSES. Knowledge is kept and transmitted across 'generations' "
     "(reader -> contributor -> writer); the decks / denominational voices are the group dialects (one "
     "body, many repertoires); the matriarch is the elder tier of accumulated, weighted wisdom; the "
     "cooperative roles are the expert FACES collaborating.",
     ["orcas", "killer whales", "matriline", "dialect", "animal culture", "cooperative hunting",
      "cultural transmission"]),
]


def _card(cid, title, mechanism, mapping, bands):
    return {
        "id": f"card_ci_{cid}", "kind": "reference", "title": title,
        "body": (f"{mechanism} — HOW IT FITS OUR SYSTEM: {mapping} We did not invent this form; we "
                 f"uncovered it — the concordance of reality, elegance as the Maker's signature."),
        "source": {"label": "Collective intelligence — measured natural systems, mapped to the engine",
                   "url": "", "domain": "systems", "authority_tier": "reference"},
        "shelf": "science", "box": "collective_intelligence",
        "bands": list(bands) + ["collective intelligence", "systems of the world", "swarm intelligence"],
        "subject": title,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a measured collective-intelligence system, mapped to the engine"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"measured": True, "systems_of_the_world": True},
    }


def _spine_card():
    return {
        "id": SPINE, "kind": "reference", "title": "Collective intelligence — the measured architecture",
        "body": ("How creation organizes many into one: decentralized local rules producing coherent "
                 "global behavior, with no central controller and the group doing what no member can "
                 "alone. Ants (stigmergy), bees (quorum), birds (scale-free flocking), orcas (matriline "
                 "culture) — each measured, and each the natural form of one of the engine's mechanisms: "
                 "the keeping, the conductor, the mesh, the witness wire. Uncovered, not invented."),
        "source": {"label": "Collective intelligence — the measured architecture", "url": "",
                   "domain": "systems", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["collective intelligence", "swarm", "self-organization", "systems of the world", "spine"],
        "subject": "collective intelligence",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "collective intelligence, a shelf of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def main() -> int:
    cards = [_spine_card()] + [_card(*s) for s in SYSTEMS]
    out = Path("data") / "collective_intelligence_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(SYSTEMS)} collective-intelligence systems (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
