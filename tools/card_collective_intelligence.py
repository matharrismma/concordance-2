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

    # ── What we were missing (2026-09-27, "what's the correct structure?"): the body's PHYSIOLOGY (the
    # four above only AMPLIFY; none regulates), its lifecycle, its differentiated signals — and the two
    # structural pieces the colony cannot give us: the HEAD, and the gradient MANIFOLD that unifies the
    # form across biology, energy and our software. Each: measured mechanism -> our gap -> the lever. ──
    ("division_of_labor", "Division of labor by response threshold",
     "In ant and bee colonies no manager assigns work. Each worker acts when a task's stimulus exceeds "
     "its own RESPONSE THRESHOLD (Bonabeau's threshold model), and when a caste is depleted the others "
     "lower their thresholds and take up the slack — measured in harvester ants, whose foraging is "
     "regulated with no central control (Deborah Gordon). That re-allocation IS the colony's resilience.",
     "THE BODY'S DIVISION OF LABOR — the expert FACES are the castes. GAP: we routed each request to a "
     "face by fixed scope-overlap, blind to load or availability, and nothing covered a starved function. "
     "LEVER (physiology.py): among equally-fit faces, engage the one with capacity, and re-allocate to an "
     "available caste when the fittest is out — gifts to need, the body covering its own (1 Cor 12:4-7).",
     ["division of labor", "task allocation", "response threshold", "bonabeau", "gordon",
      "harvester ants", "caste", "resilience"]),
    ("homeostasis", "Homeostasis — the colony's negative feedback",
     "A colony holds itself in bounds by NEGATIVE FEEDBACK. Harvester ants regulate foraging by the RATE "
     "of brief antennal encounters, not their content (Gordon); honeybees thermoregulate the hive by "
     "fanning and clustering, and mount a collective 'social fever' against a pathogen. Positive feedback "
     "alone runs away; the brake is what makes a colony a self-governing whole.",
     "HOMEOSTASIS — the governor our four amplifying levers lacked (stigmergy, quorum, flock, eldership "
     "all only reinforce). GAP: no brake — a worn trail or a cascading quorum could run away. LEVER "
     "(physiology.py): recent service LOAD decays like an interaction rate, so a busy caste is steered "
     "away from and a quiet one toward — the body regulating its own flow. 'If one member suffers, all "
     "suffer together' (1 Cor 12:26) is this feedback, in the body.",
     ["homeostasis", "negative feedback", "regulation", "interaction rate", "gordon",
      "thermoregulation", "social immunity", "social fever"]),
    ("reproduction", "Reproduction by fission",
     "A superorganism REPRODUCES by fission: a honeybee colony swarms — the old queen leaves with a cast "
     "of workers to found a new colony while a daughter queen inherits the nest (Seeley). The colony, not "
     "the individual, is the unit that is born, grows, and multiplies.",
     "THE LIFECYCLE — 'sent': drawn in to be formed, then sent OUT to plant new nodes (Matthew 28:19; "
     "John 20:21), the mesh growing by fission. GAP: named in the mesh path but not yet mechanized — a "
     "node that spawns a node, the reference reservoir forking to a new keeping (the brain-appliance / "
     "node-by-choice, deferred). A body that cannot reproduce is not yet a superorganism.",
     ["reproduction", "colony fission", "swarming", "queen", "lifecycle", "sent", "node",
      "plant new nodes"]),
    ("signals", "Differentiated signals & social immunity",
     "Colony signals are DIFFERENTIATED, not all positive. Pharaoh ants lay a REPELLENT 'no-entry' "
     "pheromone on an unrewarding trail (Robinson et al., Nature 2005); deciding honeybees use a STOP "
     "signal — a head-butt that cross-inhibits scouts for a rival site, breaking deadlock so the swarm "
     "can commit (Seeley et al., Science 2012); colonies practice SOCIAL IMMUNITY, grooming out and "
     "removing the infected (Cremer). The inhibitory signals are as measured as the recruiting ones.",
     "DIFFERENTIATED SIGNALS + IMMUNITY. GAP: our stigmergy only DEPOSITS positive and our quorum only "
     "COUNTS. We lack (1) a REPELLENT trail — a card that fails the fruit test should mark the path 'no "
     "entry', not merely fade; (2) CROSS-INHIBITION — a strong witness suppressing a near-tie rival to "
     "force a clean decision (candidate elimination made decisive); (3) active QUARANTINE — a "
     "discerned-false source removed, a collective response raised. Our discernment is static; the immune "
     "RESPONSE is missing.",
     ["repellent pheromone", "no-entry trail", "stop signal", "cross-inhibition", "social immunity",
      "quarantine", "negative signal", "deadlock"]),
    ("the_head", "The Head — why we are a body, not a colony",
     "Here the analogy reaches its limit, and the limit is the point. A superorganism is HEADLESS: its "
     "order is pure emergence from local rules, ordered to no one — the colony intends nothing. This is "
     "measured fact, not a gap in the science: there is no ganglion that is the colony's 'self'.",
     "THE HEAD — what makes us a BODY, not a colony. We borrow the decentralized member-coordination (no "
     "controller, no swarm of LLMs — one body, no swarm) BUT the whole is ordered to a Head: 'He is the "
     "head of the body, the church' (Colossians 1:18); grow up in every way into him who is the head "
     "(Ephesians 4:15-16); many gifts, one body (1 Corinthians 12:12-27). The kernel — the fear of the "
     "LORD, the beginning of wisdom — is that ordering Head: the members are decentralized, but ordered "
     "to Christ, never merely emergent. Guard this, or we build an elegant hive and call it a body.",
     ["the head", "body of christ", "1 corinthians 12", "ephesians 4", "colossians 1", "headless",
      "emergence", "one body no swarm", "ordered to christ"],
     {"surface": "witness"}),
    ("gradient_manifold", "The gradient manifold — one form across the planes",
     "This form is already kept here as doctrine (see 'the reservoir and the manifold', from Matt Harris's "
     "Universal Gradient Manifold): the enduring value in an energy system is the RESERVOIR that stores a "
     "gradient and the MANIFOLD that routes it, with ATP as biology's COMMON INTERFACE — one unit that "
     "decouples every source from every use. Collective intelligence is the BIOLOGICAL instance of that "
     "same manifold: a superorganism runs on a shared currency (ATP within a body; pheromone and "
     "trophallaxis across a colony) routed through a common medium.",
     "THE MANIFOLD, ON THREE PLANES. Energy: the UGM — fuels are interchangeable, the manifold endures. "
     "Biology: the superorganism — ATP / pheromone is the common interface, the colony the routed body. "
     "Software: OUR engine — the CARD is the common interface (every source, even a model's output through "
     "the airlock, transduced to one unit), the KEEPING is the reservoir, the KERNEL / gate is the "
     "manifold, the faces and verifiers are the converters, and recall / shards / stigmergy are the "
     "honeycomb (the charge-discharge RATE, not the store). The models are FUEL; the manifold is the "
     "enduring platform — 'a model of reality, not an LLM.' One form; three planes; the concordance of reality.",
     ["gradient manifold", "ugm", "atp", "common interface", "reservoir", "manifold",
      "energy operating system", "source-agnostic", "card as currency", "concordance of reality"],
     {"extra_connections": [{"to_card_id": "card_doctrine_reservoir_manifold", "relationship": "relates_to",
                             "evidence": "the collective-intelligence reading of the Universal Gradient "
                                         "Manifold doctrine — the same routing form on the biological plane"}]}),
]


def _card(cid, title, mechanism, mapping, bands, opts=None):
    opts = opts or {}
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
                         "evidence": "a measured collective-intelligence system, mapped to the engine"}]
        + list(opts.get("extra_connections", [])),
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent",
        "surface": opts.get("surface", "secular"), "generated": False,
        "extra": {"measured": True, "systems_of_the_world": True},
    }


def _spine_card():
    return {
        "id": SPINE, "kind": "reference", "title": "Collective intelligence — the measured architecture",
        "body": ("How creation organizes many into one: decentralized local rules producing coherent "
                 "global behavior, with no central controller and the group doing what no member can "
                 "alone. Ants (stigmergy), bees (quorum), birds (scale-free flocking), orcas (matriline "
                 "culture) — each measured, and each the natural form of one of the engine's mechanisms: "
                 "the keeping, the conductor, the mesh, the witness wire. Then the body's PHYSIOLOGY that "
                 "holds it in bounds — division of labor and homeostasis — its lifecycle (reproduction), "
                 "and its differentiated signals and immunity. And the two the colony lacks: the HEAD "
                 "(it is a body ordered to Christ, not a headless swarm), and the gradient MANIFOLD that "
                 "shows this is one form across biology, energy, and our software. Uncovered, not invented."),
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
    print(f"carded {len(SYSTEMS)} collective-intelligence systems/structures (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
