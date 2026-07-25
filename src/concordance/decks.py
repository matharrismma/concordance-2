"""Decks — the Hare. Many curated card SETS; predict the one this interaction needs; search it
first for speed; fall back to the whole keeping so nothing is ever missed (the Tortoise).

Matt: "We can have many sets of cards, so we predict which card deck you need or will need in this
interaction — it optimizes the search and gets more speed. Think of it like having many Pokémon
decks depending on the situation and the opponent. Name the position; more positions allow faster
decisions." (The Pressure Fighting System, applied to retrieval.)

This first cut builds DOMAIN decks from the corpus's own shelves — safe and non-interpretive. The
ARCHETYPE decks (the characters of the Bible) and their micropositions layer on top next, grounded
in Scripture. The predictor only reorders what we already hold, and the fallback guarantees the
Tortoise still reaches everything — it just gets there second. Conduit, not source.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

_TOK = re.compile(r"[a-z0-9]{2,}")


def _toks(s: str) -> Set[str]:
    return set(_TOK.findall(str(s or "").lower()))


# id, name, description, shelves (the cards it holds), keywords (what routes a query TO it)
_DECKS: List[Dict[str, Any]] = [
    {"id": "scripture-original", "name": "Scripture in the Original Tongues — verse by verse",
     "desc": "The whole Bible in the languages it was given in: the Greek New Testament (SBLGNT) and "
             "the Hebrew Bible (Leningrad), one verse at a time, each with its Strong's numbers.",
     "shelves": {"greek_nt", "hebrew_ot"},
     "keywords": {"hebrew", "greek", "verse", "original", "septuagint", "masoretic", "leningrad",
                  "sblgnt", "tanakh", "torah", "gospel", "epistle", "genesis", "psalm", "john",
                  "strongs", "morphology", "lemma", "manuscript", "text"}},
    {"id": "tongues", "name": "The Original Tongues — Hebrew & Greek",
     "desc": "The lexicon: every Strong's word, its transliteration and lexical range — the plumb-line.",
     "shelves": {"lexicon"},
     "keywords": {"hebrew", "greek", "strongs", "strong", "lexicon", "transliteration", "aramaic",
                  "septuagint", "word", "study", "meaning", "root", "original", "tongue", "language"}},
    {"id": "word", "name": "The Dictionary & Thesaurus",
     "desc": "Every word: what it means, and the words that stand with it.",
     "shelves": {"dictionary"},
     "keywords": {"define", "definition", "meaning", "synonym", "antonym", "thesaurus", "word",
                  "spell", "vocabulary", "term", "means"}},
    {"id": "scripture", "name": "Scripture & the Word",
     "desc": "The Bible, the fathers, the confessions, the hymns — the Word and its witnesses.",
     "shelves": {"codex", "patristics", "connections", "hymns", "commentary", "sermons"},
     "keywords": {"scripture", "bible", "verse", "gospel", "jesus", "christ", "god", "lord", "faith",
                  "commentary", "sermon", "spurgeon", "henry", "exposition", "preaching",
                  "church", "father", "doctrine", "psalm", "hymn", "prayer", "sin", "grace", "holy",
                  "testament", "apostle", "prophet", "salvation", "cross", "spirit", "heaven"}},
    {"id": "body", "name": "The Medicines & the Body",
     "desc": "Medicines and their class, and foods and their nourishment — for the keeping of the body.",
     "shelves": {"medicine", "nutrition", "activities"},
     "keywords": {"drug", "dose", "dosage", "medicine", "medication", "pill", "symptom", "disease",
                  "exercise", "activity", "met", "calories", "workout", "fitness",
                  "treatment", "health", "vitamin", "calorie", "food", "nutrition", "diet", "protein",
                  "pain", "fever", "blood", "heart", "sick", "remedy"}},
    {"id": "heavens", "name": "The Heavens",
     "desc": "Named and naked-eye stars: position, distance, brightness, spectral type.",
     "shelves": {"astronomy"},
     "keywords": {"star", "planet", "constellation", "galaxy", "magnitude", "spectral", "sky",
                  "night", "nebula", "orbit", "celestial", "astronomy", "cosmos"}},
    {"id": "matter", "name": "Matter & the Atom",
     "desc": "The nuclides, the elements and the physical laws.",
     "shelves": {"nuclear physics", "chemistry", "physics"},
     "keywords": {"nuclide", "isotope", "half", "life", "element", "atom", "atomic", "decay",
                  "radioactive", "proton", "neutron", "physics", "chemistry", "reaction", "energy"}},
    {"id": "earth", "name": "The Earth & its Places",
     "desc": "Named places of the earth — country, coordinates, population.",
     "shelves": {"geography"},
     "keywords": {"place", "city", "country", "location", "latitude", "longitude", "town", "map",
                  "where", "capital", "region", "nation", "geography", "population"}},
    {"id": "networks", "name": "Networks & Machines",
     "desc": "The IANA registry of service names and port numbers.",
     "shelves": {"networking", "rfcs"},
     "keywords": {"port", "protocol", "tcp", "udp", "ip", "network", "service", "computer", "socket",
                  "rfc", "standard", "internet", "ietf", "specification",
                  "packet", "server", "dns", "http", "ssh"}},
    {"id": "nations", "name": "Money & the Nations",
     "desc": "World Bank open indicators — economies across countries and years.",
     "shelves": {"economics"},
     "keywords": {"gdp", "economy", "economic", "inflation", "indicator", "world", "bank",
                  "development", "economics", "trade", "income", "growth", "poverty"}},
    {"id": "works", "name": "The Works — worked & sealed",
     "desc": "Real worked demonstrations of mathematics, science and engineering, each sealed.",
     "shelves": {"the-works"},
     "keywords": {"proof", "worked", "sealed", "demonstration", "theorem", "math", "mathematics",
                  "engineering", "derivation", "verify", "seal", "calculate"}},
    {"id": "land", "name": "The Land — grow, make, keep",
     "desc": "Crops, soil, recipes and maker knowledge — the practical arts.",
     "shelves": {"agriculture", "recipes", "maker"},
     "keywords": {"crop", "plant", "garden", "soil", "grow", "farm", "harvest", "recipe", "cook",
                  "make", "build", "tool", "repair", "seed", "rotation"}},
    {"id": "history", "name": "History — the dated events of the world",
     "desc": "Battles, wars, treaties, disasters and turning points, each with its date and a link to "
             "the full record — for the LORD is Lord of history (Daniel 2:21).",
     "shelves": {"history"},
     "keywords": {"history", "historical", "event", "battle", "war", "treaty", "siege", "revolution",
                  "when did", "what happened", "year", "century", "ancient", "medieval", "modern",
                  "empire", "dynasty", "date of", "timeline"}},
    {"id": "books", "name": "The Great Books",
     "desc": "The great literature of the world, in the public domain — some 77,000 works from Project "
             "Gutenberg, each a click from its full text.",
     "shelves": {"classics", "gutenberg"},
     "keywords": {"literature", "book", "classic", "novel", "story", "poem", "author", "chapter",
                  "read", "text", "gutenberg", "fiction", "essay", "play", "poetry", "volume"}},
    {"id": "languages", "name": "The Languages of the Earth",
     "desc": "The world's languages by family and region, each with its phonological inventory — the "
             "consonants, vowels and tones it is spoken with.",
     "shelves": {"languages"},
     "keywords": {"language", "tongue", "phoneme", "consonant", "vowel", "dialect", "linguistics",
                  "family", "glottolog", "phoible", "spoken", "accent", "phonology", "ipa", "speak"}},
    {"id": "life", "name": "The Tree of Life — the living kinds",
     "desc": "Every creature with a common name — mammals, birds, fish, plants, the microbes we know "
             "by name — with its scientific name, rank and place in the tree of life.",
     "shelves": {"taxonomy"},
     "keywords": {"animal", "plant", "species", "organism", "creature", "genus", "mammal", "bird",
                  "fish", "insect", "tree", "flower", "taxonomy", "scientific", "kingdom", "life",
                  "reptile", "amphibian", "fungus", "bacteria"}},
    {"id": "sequences", "name": "Integer Sequences — the OEIS core",
     "desc": "The foundational integer sequences: the primes, Fibonacci, Catalan, the partitions, and "
             "thousands more the whole of number theory keeps returning to.",
     "shelves": {"oeis"},
     "keywords": {"sequence", "integer", "oeis", "fibonacci", "catalan", "prime", "primes", "partition",
                  "series", "recurrence", "combinatorics", "number", "triangular", "factorial", "terms"}},
    {"id": "churches", "name": "The Churches — one Lord, many traditions (calibrated)",
     "desc": "Every major tradition of the Church, gathered from its own confession and measured against "
             "the one plumb-line — calibrated, not judged; each tradition's gift, and the creeds held in common.",
     "shelves": {"churches"},
     "keywords": {"church", "denomination", "tradition", "confession", "catholic", "orthodox", "protestant",
                  "lutheran", "reformed", "presbyterian", "anglican", "baptist", "methodist", "pentecostal",
                  "anabaptist", "creed", "denominations", "which church", "difference between"}},
    {"id": "builders", "name": "The Builders of the Floor — credited with love",
     "desc": "The historians, scientists and mathematicians who mapped the Floor of Discovery — each credited "
             "magnanimously for the truth they kept, their shortfalls named honestly, all held with love. "
             "Many were worshippers thinking God's thoughts after Him.",
     "shelves": {"builders"},
     "keywords": {"scientist", "mathematician", "historian", "newton", "kepler", "euclid", "gödel", "godel",
                  "darwin", "einstein", "aristotle", "pascal", "leibniz", "euler", "faraday", "maxwell",
                  "cantor", "turing", "contribution", "who discovered", "credit", "genius", "builders"}},
    {"id": "foreshadows", "name": "The Nations' Foreshadows — seeds of the Word, fulfilled in Christ",
     "desc": "The faiths that came before Christ, credited magnanimously where they contributed — the seeds "
             "and shadows scattered among the nations (Acts 17), the fulfillment named plainly. What arose "
             "after is measured by the test of the spirits (1 John 4:2-3), always in love.",
     "shelves": {"foreshadows"},
     "keywords": {"religion", "religions", "foreshadow", "praeparatio", "paganism", "greek philosophy", "plato",
                  "stoic", "zoroastrian", "magi", "hinduism", "buddhism", "confucius", "daoism", "the way",
                  "islam", "mystery religions", "true myth", "unknown god", "world religions", "other religions"}},
    {"id": "playbook", "name": "The Fractal Playbook — obedience, confirmed",
     "desc": "The Body's memory of faithful obedience: the atomic Playbook Entry (Confession, Anchors, "
             "Action, Outcome, Witness, Wait, Status) and the Four Gates — RED, FLOOR, BROTHERS, GOD.",
     "shelves": {"playbook"},
     "keywords": {"playbook", "obedience", "confession", "witness", "wait", "quarantine", "confirmed",
                  "four", "gates", "prune", "pruning", "governance", "decision", "confirm", "faithful"}},
    {"id": "free-access", "name": "Free Tools — the connection to lawful free access",
     "desc": "Where to get books, textbooks, research and media FREE and legally — public libraries, "
             "open textbooks, open access, the public domain, and the tools that won in court. Everything "
             "up to the line, nothing on it.",
     "shelves": {"access"},
     "keywords": {"free", "library", "libby", "textbook", "openstax", "borrow", "download", "open access",
                  "paper", "pdf", "read", "tool", "legal", "gutenberg", "hoopla", "kanopy", "hathitrust",
                  "unpaywall", "where can i get", "how to get", "for free", "without paying"}},
    # The systems of the world — one design cascading over planes (the recurring form).
    {"id": "systems", "name": "The Systems of the World — one design, many planes",
     "desc": "Electrical, fluid, thermal, mechanical, control, wave — the same effort-and-flow form, "
             "the same equations, recurring across every domain. To learn one is to learn them all.",
     "shelves": {"systems"},
     "keywords": {"system", "analogy", "isomorphism", "recurring", "effort", "flow", "impedance",
                  "cascade", "fractal", "shadow", "inverse", "design", "one design", "diffusion"}},
    {"id": "electronics", "name": "Electronics & Electrical Systems",
     "desc": "Voltage and current, resistance, capacitance, inductance — the clearest window onto the effort-flow form.",
     "shelves": {"systems", "physics"},
     "keywords": {"electronics", "electrical", "circuit", "voltage", "current", "resistor", "capacitor",
                  "inductor", "ohm", "kirchhoff", "transistor", "diode", "amplifier", "signal"}},
    {"id": "fluids", "name": "Hydrodynamics & Fluid Systems",
     "desc": "Pressure and flow, viscosity, pumps and pipes — the fluid face of the one design.",
     "shelves": {"systems", "physics"},
     "keywords": {"hydrodynamics", "fluid", "flow", "pressure", "pipe", "hydraulic", "bernoulli", "pump",
                  "viscosity", "reynolds", "turbulence", "laminar", "vortex", "aerodynamics"}},
    {"id": "thermal", "name": "Thermal Systems",
     "desc": "Temperature and heat-flow, conduction, thermal resistance and capacitance — the heat face of the form.",
     "shelves": {"systems", "physics"},
     "keywords": {"thermal", "heat", "temperature", "thermodynamics", "conduction", "convection", "fourier",
                  "entropy", "insulation", "radiator", "cooling"}},
    {"id": "mechanical", "name": "Mechanical Systems",
     "desc": "Force and velocity, springs, dampers, masses, gears — an RLC circuit in different clothes.",
     "shelves": {"systems", "physics"},
     "keywords": {"mechanical", "force", "torque", "spring", "damper", "mass", "newton", "gear", "motion",
                  "lever", "pulley", "friction", "momentum", "statics"}},
    {"id": "control", "name": "Control Systems",
     "desc": "Feedback — the universal regulator, from thermostat to governor to homeostasis, one loop, one math.",
     "shelves": {"systems"},
     "keywords": {"control", "feedback", "pid", "governor", "regulator", "stability", "transfer function",
                  "homeostasis", "setpoint", "loop", "damping", "oscillation"}},
    {"id": "waves", "name": "Waves & Oscillation",
     "desc": "The one wave equation and the one harmonic oscillator — sound, light, water, string, all rhyming.",
     "shelves": {"systems", "physics"},
     "keywords": {"wave", "oscillation", "frequency", "resonance", "harmonic", "vibration", "acoustics",
                  "pendulum", "amplitude", "wavelength", "interference", "standing wave"}},
    {"id": "fieldkit", "name": "The Field Kit — Scripture protocols to practice",
     "desc": "An authored deck: 30 protocol cards from the Sermon on the Mount and the Epistles — "
             "each an anchor Scripture, a floor, and a seven-day practice. Hearing plus doing.",
     "shelves": {"fieldkit"},
     "keywords": {"practice", "protocol", "obedience", "obey", "discipline", "habit", "walk", "doing",
                  "sermon", "mount", "beatitude", "fruit", "drift", "accountability", "fieldkit",
                  "sanctification", "discipleship", "grow", "struggle", "temptation"}},
]

_BY_ID = {d["id"]: d for d in _DECKS}
# precompute the routing vocabulary for each deck (keywords + name + shelf words)
for _d in _DECKS:
    _d["_route"] = set(_d["keywords"]) | _toks(_d["name"]) | {w for s in _d["shelves"] for w in _toks(s)}


def all_decks() -> List[Dict[str, Any]]:
    """Every deck, with a live card count (the atlas can render these)."""
    from . import corpus
    cor = corpus.default_corpus()
    counts: Dict[str, int] = {}
    for c in cor.cards.values():
        if corpus.is_public(c):
            counts[c.get("shelf", "")] = counts.get(c.get("shelf", ""), 0) + 1
    return [{"id": d["id"], "name": d["name"], "desc": d["desc"],
             "shelves": sorted(d["shelves"]),
             "cards": sum(counts.get(s, 0) for s in d["shelves"])}
            for d in _DECKS]


def predict(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Name the position: which deck(s) does this interaction call for? Scores each deck by how
    much the query overlaps its routing vocabulary. Returns the top-k that match (possibly none —
    then the caller searches the whole keeping, the Tortoise)."""
    qt = _toks(query)
    if not qt:
        return []
    scored = []
    for d in _DECKS:
        overlap = qt & d["_route"]
        if overlap:
            scored.append((len(overlap), d, sorted(overlap)))
    scored.sort(key=lambda x: -x[0])
    return [{"id": d["id"], "name": d["name"], "score": s, "matched": m}
            for s, d, m in scored[:max(1, int(k))]]


def deck_shelves(deck_id: str) -> Optional[Set[str]]:
    d = _BY_ID.get(deck_id)
    return set(d["shelves"]) if d else None


def search(query: str, deck_id: Optional[str] = None, limit: int = 12) -> Dict[str, Any]:
    """Search a deck first (the Hare), falling back to the whole keeping if the deck comes up
    short (the Tortoise). If no deck is given, predict it. Always honest about which ran."""
    from . import corpus
    predicted = predict(query, k=1)
    if not deck_id and predicted:
        deck_id = predicted[0]["id"]
    shelves = deck_shelves(deck_id) if deck_id else None

    hits: List[dict] = []
    if shelves:
        hits = corpus.search(query, limit=limit, shelves=shelves)
    fell_back = False
    if len(hits) < max(3, limit // 3):          # deck too thin → the Tortoise reaches everything
        fell_back = True
        seen = {h.get("id") for h in hits}
        for h in corpus.search(query, limit=limit):
            if h.get("id") not in seen:
                hits.append(h)
                if len(hits) >= limit:
                    break

    def _brief(c):
        return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
                "snippet": (c.get("body") or "")[:140]}
    return {"query": query, "deck": deck_id, "predicted": predicted,
            "fell_back_to_full": fell_back, "count": len(hits[:limit]),
            "results": [_brief(c) for c in hits[:limit]]}
