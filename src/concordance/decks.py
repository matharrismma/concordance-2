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

    # ── NEED DECKS ─────────────────────────────────────────────────────────────────────────────
    # Frontloaded for the situation, not the domain. Matt: "We can anticipate need based on previous
    # topics, so we can frontload different decks of the same cards." A card like 'boil water to make
    # it safe' belongs to many of these at once — the deck is a hand dealt for a moment of need, cut
    # ACROSS shelves. Each carries a `seed` (the phrase that defines its content, so it can be OPENED
    # with no query) and distress-phrased keywords (what routes a frightened search TO it).
    {"id": "power-out", "name": "When the power goes out", "need": True,
     "desc": "Light, heat, keeping food, staying in touch, and caring for the sick when the grid is "
             "down — what a household reaches for first in a blackout.",
     "shelves": {"energy", "practical", "communications", "medicine"},
     "seed": "power outage blackout no electricity generator battery backup solar candle lantern "
             "light heat without power keep food cold refrigerator freezer charge phone emergency",
     "keywords": {"power", "outage", "blackout", "electricity", "generator", "battery", "grid",
                  "candle", "lantern", "dark", "refrigerator", "freezer", "charge", "solar", "backup"}},
    {"id": "water-safe", "name": "When the water isn't safe to drink", "need": True,
     "desc": "Make water safe to drink, store it, and find it — boiling, filtering, disinfecting, and "
             "the sicknesses bad water brings, for when the tap can't be trusted.",
     "shelves": {"water", "sanitation", "medicine", "first_aid", "survival"},
     "seed": "purify water boil water disinfect filter contaminated well dehydration safe drinking "
             "water storage bleach cloudy waterborne cholera diarrhea rain collection spring",
     "keywords": {"water", "purify", "boil", "filter", "contaminated", "well", "dehydration",
                  "thirsty", "drinking", "waterborne", "cholera", "diarrhea", "rainwater", "spring"}},
    {"id": "first-aid-far", "name": "Someone's hurt and help is far away", "need": True,
     "desc": "Stop the bleeding, treat the wound, splint the break, cool the burn, and know the signs "
             "of shock and infection — first aid for when the hospital is hours off.",
     "shelves": {"first_aid", "medicine", "apothecary", "survival"},
     "seed": "stop bleeding wound dressing fracture splint burn CPR choking shock hypothermia fever "
             "infection first aid emergency far from hospital sprain bite poisoning herbal remedy",
     "keywords": {"bleeding", "wound", "cut", "fracture", "broken", "burn", "cpr", "choking", "shock",
                  "injury", "hurt", "emergency", "bandage", "sprain", "bite", "poison", "unconscious"}},
    {"id": "grow-food", "name": "Growing and keeping your own food", "need": True,
     "desc": "Plant a garden, tend the soil, save seed, and put food up for the year — canning, "
             "drying, and the root cellar, so the harvest lasts.",
     "shelves": {"agriculture", "almanac", "ecology"},
     "seed": "vegetable garden plant crops soil seed saving planting harvest canning preserve food "
             "root cellar compost fertilizer companion planting orchard livestock chickens almanac",
     "keywords": {"garden", "grow", "plant", "crop", "vegetable", "seed", "harvest", "soil", "canning",
                  "preserve", "compost", "orchard", "farm", "livestock", "chickens", "drying"}},
    {"id": "offgrid-comms", "name": "Reaching the world off the grid", "need": True,
     "desc": "Two-way radio, antennas, and signaling — how to call for help and stay in touch when "
             "the phone network is gone.",
     "shelves": {"communications", "navigation"},
     "seed": "two way radio ham radio CB antenna signal frequency emergency broadcast morse code "
             "walkie talkie mesh reach help without phone repeater band",
     "keywords": {"radio", "ham", "antenna", "signal", "frequency", "morse", "walkie", "broadcast",
                  "communicate", "mesh", "transmit", "repeater", "band", "cb"}},
    {"id": "sanitation", "name": "Staying clean and healthy without plumbing", "need": True,
     "desc": "Handle human waste, wash safely, and keep sickness from spreading when there's no "
             "running water or sewer — latrines, hygiene, and disease prevention.",
     "shelves": {"sanitation", "water", "medicine"},
     "seed": "human waste latrine outhouse compost toilet handwashing hygiene disease prevention "
             "greywater sewage without plumbing keep clean garbage flies sanitation",
     "keywords": {"sanitation", "latrine", "toilet", "waste", "hygiene", "sewage", "wash",
                  "handwashing", "disease", "plumbing", "outhouse", "greywater", "flies"}},
    {"id": "stay-warm", "name": "Keeping warm and fed through winter", "need": True,
     "desc": "Heat without the grid, hold in the warmth, and stock the pantry — wood heat, "
             "insulation, and food storage for the cold months.",
     "shelves": {"energy", "agriculture", "almanac", "survival", "practical"},
     "seed": "stay warm wood stove heat insulation winter cold shelter blanket food storage stockpile "
             "root cellar preserve firewood chimney frozen pipes season almanac",
     "keywords": {"warm", "heat", "winter", "cold", "wood", "stove", "insulation", "firewood",
                  "blanket", "freeze", "frozen", "chimney", "pantry", "stockpile"}},
    {"id": "handyman", "name": "Fixing and building it yourself", "need": True,
     "desc": "Repair what breaks and build what you need — carpentry, plumbing, wiring, and the old "
             "trade handbooks, so you don't have to call anyone.",
     "shelves": {"practical"},
     "seed": "repair fix build carpentry woodworking joinery plumbing wiring tools maintenance "
             "construction masonry blacksmith mechanics how to make handyman",
     "keywords": {"repair", "fix", "build", "carpentry", "woodworking", "plumbing", "wiring", "tool",
                  "maintenance", "construction", "handyman", "diy", "masonry", "blacksmith", "mechanic"}},
    {"id": "navigate", "name": "Finding your way", "need": True,
     "desc": "Read a map, hold a bearing, and find north by compass or stars — wayfinding when the "
             "phone can't help and you can't get lost.",
     "shelves": {"navigation", "survival"},
     "seed": "navigate compass map bearing north dead reckoning lost direction landmark stars "
             "find your way wayfinding latitude terrain orienteering",
     "keywords": {"navigate", "compass", "map", "bearing", "north", "direction", "lost", "wayfinding",
                  "landmark", "orienteering", "terrain"}},
    {"id": "homestead", "name": "Starting a homestead from scratch", "need": True,
     "desc": "The whole off-grid life in one hand — water, power, food, animals, and waste — for a "
             "family setting out to provide for itself on the land.",
     "shelves": {"agriculture", "almanac", "apothecary", "energy", "water", "sanitation", "practical", "survival"},
     "seed": "homestead self sufficient off grid livestock chickens goats well solar water system "
             "garden food preservation land smallholding self reliance almanac herbal",
     "keywords": {"homestead", "sufficient", "offgrid", "livestock", "goats", "well", "solar",
                  "self-reliance", "smallholding", "land", "acreage"}},
    {"id": "be-not-afraid", "name": "When you're afraid", "need": True,
     "desc": "The Word for fear — 'fear not' from Genesis to Revelation, with commentary and a "
             "practice to walk it out. The most-spoken command in Scripture.",
     "shelves": {"codex", "commentary", "fieldkit"},
     "seed": "fear afraid anxious worry peace courage do not be afraid fear not trust the Lord anxiety "
             "comfort strength be strong and courageous perfect love casts out fear",
     "keywords": {"afraid", "fear", "anxious", "anxiety", "worry", "scared", "panic", "peace",
                  "courage", "terrified", "dread", "overwhelmed"}},
    {"id": "grieving", "name": "When you're grieving a loss", "need": True,
     "desc": "Comfort for mourning — the Word's promises to those who weep, with commentary, and the "
             "hope of the resurrection.",
     "shelves": {"codex", "commentary", "fieldkit"},
     "seed": "grief death mourning loss comfort hope resurrection sorrow weep those who mourn blessed "
             "eternal life valley of the shadow he will wipe away every tear",
     "keywords": {"grief", "grieving", "death", "died", "mourning", "loss", "funeral", "comfort",
                  "sorrow", "mourn", "bereaved", "widow", "buried"}},
    {"id": "money-tight", "name": "When money is tight", "need": True,
     "desc": "Provision when there's not enough — daily bread and contentment from the Word, sound "
             "stewardship, and where to find help and resources for free.",
     "shelves": {"economics", "codex", "access", "practical"},
     "seed": "money poor provision budget debt work daily bread stewardship contentment worry about "
             "money free resources food assistance make do frugal thrift save",
     "keywords": {"money", "poor", "broke", "debt", "budget", "bills", "provision", "afford",
                  "stewardship", "unemployed", "frugal", "assistance", "rent"}},
    {"id": "teach-kids", "name": "Teaching your children at home", "need": True,
     "desc": "For the homeschooling family — reading and arithmetic, the dictionary, the living "
             "world, history, and worked math, gathered for teaching your own.",
     "shelves": {"dictionary", "taxonomy", "history", "codex", "curriculum", "the-works"},
     "seed": "teach homeschool lesson reading writing arithmetic phonics children learn curriculum "
             "grammar math science history for kids spelling vocabulary catechism",
     "keywords": {"teach", "homeschool", "lesson", "reading", "arithmetic", "phonics", "curriculum",
                  "children", "kids", "learn", "school", "educate", "spelling", "catechism"}},
    # Domain homes for the practical shelves the atlas had left uncovered.
    {"id": "field", "name": "The Field Library — survival & self-reliance",
     "desc": "The practical library for living without the grid: survival skills, the trade and "
             "handyman handbooks, and the Field Kit protocols — self-reliance, gathered.",
     "shelves": {"survival", "practical", "fieldkit"},
     "seed": "survival self reliance preparedness field guide practical skills emergency bushcraft "
             "off grid handbook trade",
     "keywords": {"survival", "prepper", "preparedness", "self-reliance", "bushcraft", "field",
                  "practical", "wilderness", "prepping"}},
    {"id": "earth-sciences", "name": "The Earth — geology, forests & the sciences",
     "desc": "The public-domain science of the earth: geology and minerals, forests and watersheds, "
             "and the federal technical surveys — the ground beneath the homestead.",
     "shelves": {"geology", "ecology", "science"},
     "seed": "geology rock mineral soil survey forest ecology watershed scientific report earth "
             "science terrain erosion water table strata",
     "keywords": {"geology", "rock", "mineral", "soil", "forest", "ecology", "watershed", "science",
                  "survey", "terrain", "erosion", "strata"}},
]

_BY_ID = {d["id"]: d for d in _DECKS}
# precompute the routing vocabulary for each deck (keywords + name + shelf words + seed words) — the
# seed of a need-deck is exactly the language a frightened search uses, so it belongs in the router.
for _d in _DECKS:
    _d["_route"] = (set(_d["keywords"]) | _toks(_d["name"])
                    | {w for s in _d["shelves"] for w in _toks(s)}
                    | _toks(_d.get("seed", "")))


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
             "need": bool(d.get("need")),      # a situation deck (frontloaded) vs a domain deck
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


def open_deck(deck_id: str, limit: int = 15) -> Optional[Dict[str, Any]]:
    """Deal the frontloaded hand — the cards this situation calls for, in order, with NO query
    needed. A need-deck carries a `seed` (the phrase that defines its content); a domain deck opens
    on its own name. The Hare deals from the deck's own shelves; if the seed comes up thin, it
    broadens within those same shelves by the deck's keywords, so a deck is never emptier than its
    shelves. Returns None for an unknown deck. Conduit, not source — every card is one we hold."""
    d = _BY_ID.get(deck_id)
    if not d:
        return None
    from . import corpus
    shelves = set(d["shelves"])
    limit = max(1, min(int(limit), 60))
    hits = corpus.search(d.get("seed") or d["name"], limit=limit, shelves=shelves)
    if len(hits) < limit:                       # thin seed → broaden within the deck's own shelves
        seen = {h.get("id") for h in hits}
        for kw in sorted(d.get("keywords", ())):
            for h in corpus.search(kw, limit=limit, shelves=shelves):
                if h.get("id") not in seen:
                    hits.append(h); seen.add(h.get("id"))
                    if len(hits) >= limit:
                        break
            if len(hits) >= limit:
                break

    def _brief(c):
        return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
                "snippet": (c.get("body") or "")[:160]}
    return {"id": d["id"], "name": d["name"], "desc": d["desc"], "need": bool(d.get("need")),
            "shelves": sorted(shelves), "count": len(hits[:limit]),
            "cards": [_brief(c) for c in hits[:limit]]}


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
