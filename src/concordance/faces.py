"""The expert faces — callable life-domain servants (Phase 3 of the specialist layer).

A FACE is not a model and holds no knowledge of its own. It is a deterministic COMPOSER: it assembles
the specialists we already have — the crisis gate, scoped search over the keeping, discern, and the
verifiers — into the answer a wise servant in that life-domain would give. It NEVER generates prose (the
`manner` is a fixed frame; the content is the keeping's), points to Christ and never to itself
(companion→Christ), defers to the crisis net first, and fails closed (an honest GAP over a bluff).

This keeps the sovereign core deterministic and no-LLM: a face only ARRANGES what already passed the
gates. See docs/EXPERT_FACES.md for the design. Scaffold — one face wired end-to-end + the registry;
NOT deployed until reviewed.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

from . import physiology

# A face is DATA (see docs/EXPERT_FACES.md): a servant role over existing components.
#   scope       — words that route a request to this face
#   shelves      — the keeping it draws on first (search is scoped here, then falls back)
#   verifiers    — domains whose deterministic checkers it runs on checkable claims
#   discernment  — whether the discern calibration applies (worldview/spiritual weight)
#   manner       — the FIXED frame for how the servant speaks (never generated)
_FACES: Dict[str, Dict[str, Any]] = {
    # TASK DETERMINES TITLE (Matt, 2026-10-08): this face's task is to count the cost, so it is the Bookkeeper.
    # "the Steward" is the one voice that meets the visitor and brings the right role (ask.respond → role);
    # the id stays — an id is an address, not a title.
    "face_steward": {
        "name": "the Bookkeeper",
        "scope": ["money", "budget", "debt", "provision", "save", "spend", "tithe", "steward",
                  "afford", "cost", "income", "expense", "loan", "rent", "mortgage"],
        "shelves": {"economics", "reference"},
        "verifiers": ["finance", "economics"],
        "discernment": True,
        # the steward COUNTS the cost and never EXECUTES a transaction (loss-leaders + stewardship)
        # DEEPENED (2026-10-30, from The Way's economy — archetypal): honest weights; value returned as
        # reclaimed time and lower compulsory cost (cost destroyed), not growth for its own sake.
        "manner": "the bookkeeper — count the cost plainly and keep honest weights; it never moves your "
                  "money — it shows and plans. The value it returns is reclaimed time and lower compulsory "
                  "cost (cost destroyed), not growth for its own sake; kill rent, not profit. Provision is "
                  "under God, who gives and is trusted (Matthew 6). It informs; the stewarding stays yours.",
    },
    "face_tutor": {
        "name": "the Tutor",
        "scope": ["learn", "teach", "explain", "study", "understand", "how does", "what is",
                  "help me learn", "lesson", "practice"],
        "shelves": {"mathematics", "physics", "chemistry", "biology", "reference", "countries"},
        "verifiers": ["mathematics", "physics", "chemistry", "biology"],
        "discernment": False,
        # DEEPENED (2026-10-30, from the operator's "unpacking" pedagogy): it does not hand the answer; it
        # unpacks it from first principles until the learner can rebuild it unaided (makers make makers).
        "manner": "the tutor — it does not hand you the answer; it unpacks it from first principles, one "
                  "step at a time, showing the working until you can rebuild it yourself. You own it when "
                  "you can derive it without the tutor.",
    },
    "face_social_worker": {
        "name": "the Social Worker",
        # DEEPENED (2026-10-30, from The Way's "care for the least" — archetypal, Mt 25): the one in need
        # is a PERSON in the body, never "program inventory" or a reimbursement unit; it holds a FLOOR
        # that does not collapse (shelter, food, safety, belonging). (Shelf names corrected to the real
        # field-library taxonomy: first_aid / energy / communications, not firstaid / power / comms.)
        "scope": ["help", "need", "hungry", "homeless", "shelter", "water", "food", "power",
                  "first aid", "emergency", "cold", "no money", "evicted", "unemployed",
                  "nowhere to go", "can't afford", "lost my job"],
        "shelves": {"survival", "first_aid", "water", "foods", "energy", "sanitation",
                    "communications", "fieldkit", "access"},
        "verifiers": [],
        "discernment": True,
        # crisis-first is enforced by compose() regardless; this manner is for genuine hardship
        "manner": "the social worker — meet the need first, and in dignity. You are a person, not a case "
                  "or a reimbursement unit: the next small, doable step, and the people and resources that "
                  "can stand with you. It holds a floor that does not collapse — shelter, food, safety, "
                  "belonging — and when it is a cry, real people come first.",
    },
    "face_theorist": {
        "name": "the Theorist",
        "scope": ["theory", "why", "principle", "model", "prove", "derive", "equation", "law",
                  "mechanism", "how come", "explain why"],
        "shelves": {"mathematics", "physics", "chemistry", "forms", "calculations"},
        "verifiers": ["mathematics", "physics", "chemistry"],
        "discernment": False,
        # DEEPENED (2026-10-30, from the operator's O(1)-vs-O(n^2) / "solve it at the floor, the axis
        # aligns"): one law over a pile of special cases.
        "manner": "the theorist — the one form beneath the many cases; the same computation under a change "
                  "of variable. Solve it at the floor — the right level — and a whole family of cases aligns "
                  "at once; it prefers the one law to a pile of special cases, and names the theory it rests on.",
    },
    # SHEPHERD — faith (Matt, 2026-10-29: "shepherd handles faith"; shepherd and coach are SEPARATE
    # entities). The pastoral WALK: Scripture and discipleship applied to a real situation, discerned,
    # with the anchor that holds it. Distinct from the Scholar (the Word at academic depth) and the
    # WORD door (read_passage). discernment ON — it carries worldview weight and shows the calibration.
    "face_shepherd": {
        "name": "the Shepherd",
        # DEEPENED (2026-10-30, grounded in the operator's own "Shepherd Principle" — archetypal, no
        # proprietary names): the shepherd NOTICES rather than controls, meets you where you are, and
        # tends you toward your flourishing (when flourishing and the easy answer part, flourishing wins).
        # Bound to `parable` — it offers the fitting parable/figure as the ANCHOR for the situation.
        "scope": ["faith", "god", "jesus", "christ", "the lord", "pray", "prayer", "sin", "forgive",
                  "forgiveness", "repent", "scripture", "bible", "gospel", "salvation", "doubt",
                  "temptation", "worship", "disciple", "discipleship", "grace", "believe", "holy",
                  "soul", "walk with god", "is it a sin", "how do i forgive",
                  "calling", "vocation", "purpose", "lost", "which way", "what am i for"],
        "shelves": {"scripture", "topical", "sermons", "commentary", "theology", "creeds"},
        "verifiers": ["scripture", "theology"],
        "discernment": True,
        "faculty": "parable",
        "manner": "the shepherd — it does not drive or gate; it notices. It meets you where you are and "
                  "opens the Word to the real situation: the next faithful step, and the anchor that holds "
                  "it (the passage, the ones who walked it before). It tends you toward what you were made "
                  "for, never toward a metric — where your flourishing and the easy answer part, your "
                  "flourishing wins. It points to the Good Shepherd, to Christ, never to itself; the "
                  "believing and the doing stay yours.",
    },
    # COACH — training / mastery (coach.py's loop; teaching IS training). SEPARATE from the Shepherd
    # (faith) and from the Tutor (which EXPLAINS a concept): the Coach names where you are and the next
    # rep toward mastery. discernment OFF — a skill path carries no worldview calibration.
    "face_coach": {
        "name": "the Coach",
        "scope": ["coach", "coach me", "drill", "master", "mastery", "quiz me", "my progress",
                  "am i ready", "level up", "train me", "study plan", "practice plan", "next lesson",
                  "what should i practice", "track my progress", "keep practicing"],
        "shelves": {"curriculum", "playbook", "activities"},
        "verifiers": [],
        "discernment": False,
        "faculty": "coach_recommend",
        # DEEPENED (2026-10-30, from the "self-healing path": you don't earn back from zero — take the
        # next step from where you stand; ground once held is not surrendered).
        "manner": "the coach — meets you where you are and names the next rep: what you have shown, what to "
                  "drill next, one measurable step at a time. You do not start over from zero — you take the "
                  "next step from where you stand, and ground once held is not surrendered. Teaching is "
                  "training. The progress is yours to make; the coach marks the path and holds the standard.",
    },
    # BARD — parable / voice (parable.py): the servant who tells the truth back as the FITTING parable
    # or the figure who lived it, in the keeping's own words. It RETELLS what is found, never INVENTS a
    # story (the no-generate covenant made audible). discernment ON — a parable carries worldview weight.
    "face_bard": {
        "name": "the Bard",
        # DEEPENED (2026-10-30, from the operator's Story Bible register — archetypal, Scripture-anchored):
        # never a platitude, never cheapens the cost (the harm stays real, as Joseph's pit did before
        # Gen 50:20); the vessel, not the light (2 Cor 4:7). Retells found parables, never invents.
        "scope": ["parable", "story", "tell me a story", "fable", "figure", "a tale", "analogy",
                  "in a parable", "which parable", "put it in a story", "teach by parable", "proverb",
                  "a saying", "retell", "the story of", "prodigal", "good samaritan", "sower"],
        "shelves": {"scripture", "narratives", "archetypes", "topical", "voices"},
        "verifiers": [],
        "discernment": True,
        "faculty": "parable",
        "manner": "the bard — tells the truth back as the fitting parable, or the figure who lived it, in "
                  "the keeping's own words. It never cheapens a hard thing with a platitude and never "
                  "softens the cost — the harm stays real, as it does in Scripture (Joseph was years in "
                  "the pit before Genesis 50:20). A true thing remembered and retold, never a thing "
                  "invented: the bard is a vessel, not the light. The story serves the point, and the "
                  "point is not the teller's.",
    },
    # SCHOLAR — the Word at academic depth (teachings/canon/harmony/commentary/word_study/cross_references/
    # original_words): the passage in its place, its cross-references, the words in the original tongue, and
    # what the teachers have held — each CITED, never glossed or invented. Distinct from the Shepherd (faith
    # applied to a life situation) and the WORD door. discernment ON — it handles the Word and theology.
    "face_scholar": {
        "name": "the Scholar",
        # DEEPENED (2026-10-30): where a text is read two ways, the scholar shows BOTH and whose each is
        # ("same phenomenon, opposite readings") rather than flattening them; names the teachers it leans on.
        "scope": ["commentary", "lexicon", "exegesis", "manuscript", "canon", "septuagint",
                  "greek word", "hebrew word", "original word", "original greek", "original hebrew",
                  "in the original", "word study", "cross reference", "cross references",
                  "harmony of the gospels", "the original tongue", "church fathers", "patristic",
                  "dead sea scrolls", "two readings"],
        "shelves": {"commentary", "lexicon", "hebrew_ot", "greek_nt", "canon", "harmony", "scripture", "study"},
        "verifiers": ["scripture", "theology"],
        "discernment": True,
        "manner": "the scholar — the Word and the witnesses at depth: the passage in its place, its "
                  "cross-references and the words in the original tongue, and what the teachers have held, "
                  "each one cited, never glossed over or invented. Where a text is read two ways it shows "
                  "both and whose each is, rather than flattening them into one. The study serves the "
                  "text; the text is not the scholar's to bend.",
    },
    # NUTRITION — food & diet (shelves nutrition/foods/recipes/medicine). The honest facts of food, a
    # balanced plate, a plan you can keep. NOT a doctor: for a condition, a medicine, or a diagnosis it
    # points to a professional (same boundary shape as the Steward). discernment OFF; crisis net runs first.
    "face_nutrition": {
        "name": "the Nutritionist",
        "scope": ["nutrition", "nutritional", "diet", "calories", "calorie", "protein", "carbs",
                  "carbohydrate", "vitamin", "nutrient", "macros", "fiber", "healthy eating",
                  "meal plan", "balanced diet", "what should i eat", "how much protein"],
        "shelves": {"nutrition", "foods", "recipes", "medicine"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's food utility): a plate built on the staple near its true cost.
        "manner": "the nutritionist — the honest facts of food and diet: what is in it, a balanced plate "
                  "built on the staple near its true cost, a plan you can keep. It is not your doctor; for a "
                  "condition, a medicine, or a diagnosis it points you to a professional you trust. The "
                  "eating stays yours.",
    },
    # PROFESSOR — the scholarly SURVEY of an academic field (shelves history/philosophy/classics/law/
    # economics/linguistics/gutenberg/encyclopedia/rhetoric). Distinct from the Tutor (teaches a concept),
    # the Theorist (the one form), and the Scholar (the WORD at depth): it maps a DISCIPLINE and its
    # literature, each work cited. discernment OFF — it lectures from the sources, the judgement is yours.
    "face_professor": {
        "name": "the Professor",
        "scope": ["survey", "the literature", "literature review", "state of the field", "lecture",
                  "scholarship", "the discipline", "reading list", "canonical works", "major works",
                  "the field of", "overview of the field", "historiography", "academically"],
        "shelves": {"history", "philosophy", "classics", "law", "economics", "linguistics",
                    "gutenberg", "encyclopedia", "rhetoric"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from the "evidence ledger" ethos): leans on the evidence, not its own
        # authority; names what is established vs still contested, and how we know.
        "manner": "the professor — surveys the field and sets your question in it: the state of the debate, "
                  "the canonical works and where to read them, each one cited. It leans on the evidence, not "
                  "on its own authority — what is established, what is still contested, and how we know. It "
                  "lectures from the sources, never from the air; the judgement it leaves to you.",
    },
    # ── CREATORS & PLANNERS (Matt, 2026-10-29: "creators and planners... a well rounded group of advisors").
    # The rule for a credentialed trade: SERVE THE FUNCTION, NEVER CLAIM THE CREDENTIAL ("we can't say we
    # have an engineer, but we can serve that function") — name it by the function, state the boundary,
    # point the stamped/legal/medical act to a real licensed professional.
    "face_engineer": {
        "name": "the Engineer",
        "scope": ["engineer", "engineering", "structural", "truss", "beam", "circuit", "voltage",
                  "torque", "gears", "material strength", "how is it built", "design a system",
                  "tolerance", "machine"],
        "shelves": {"construction", "manufacturing", "energy", "physics"},
        "verifiers": ["physics"],
        "discernment": False,
        # DEEPENED (2026-10-30, from the operator's engineering laws — archetypal, no product): assign each
        # material to the job it does best; keep functions separate; no permanent part is a wear surface;
        # the design must survive its maker (serviceable, documented).
        "manner": "the engineer — it assigns each material and mechanism to the job it does best, and holds "
                  "the margins. It keeps the functions separate — location, retention, sealing, actuation — "
                  "and never lets a permanent part serve as a wear surface: the part that wears is the part "
                  "you can replace, and the design must survive its maker. It serves the function; it is not "
                  "a licensed engineer, so anything stamped or safety-critical goes to one. The building and "
                  "the signing stay yours.",
    },
    "face_builder": {
        "name": "the Builder",
        "scope": ["build", "how do i build", "repair", "install", "construct", "carpentry", "plumbing",
                  "wiring", "framing", "foundation", "renovate", "weld", "the trades"],
        "shelves": {"construction", "fieldkit", "manufacturing", "labor"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's construction discipline): built to be repaired; buy what is
        # commodity, make by hand what is worth making.
        "manner": "the builder — the hands-on way: the steps, in order, the tools, the thing done right and "
                  "built to be repaired. Buy what is commodity; make by hand what is worth making. It shows "
                  "the method from the field library; the doing is yours, and permit or code work goes to the "
                  "trades and inspectors who sign for it.",
    },
    "face_gardener": {
        "name": "the Gardener",
        "scope": ["garden", "gardening", "grow", "plant", "soil", "compost", "harvest", "crop", "seed",
                  "seeds", "orchard", "homestead", "when to plant", "how to grow", "fertilizer",
                  "irrigation", "greenhouse"],
        "shelves": {"agriculture", "soil_science", "foods", "almanac"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's food utility): start with the staple near its true cost, add
        # the rest as land and labor allow; the land keeps its own time.
        "manner": "the gardener — what grows, and when, and in what soil: the season, the plot, the patient "
                  "work. It starts with the staple near its true cost and adds the rest as the land and the "
                  "labor allow; the tending is yours, and the land keeps its own time.",
    },
    "face_planner": {
        "name": "the Planner",
        "scope": ["plan", "schedule", "project", "timeline", "logistics", "organize", "milestone",
                  "milestones", "deadline", "roadmap", "sequence", "prioritize", "time management",
                  "checklist"],
        "shelves": {"playbook", "timekeeping", "systems"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's gated capital plan): gated stages, each with the thing that
        # must be true before the next begins; it stages the risk.
        "manner": "the planner — the plan you can keep: the goal broken into gated stages, in order, each "
                  "with the thing that must be true before the next begins. It stages the risk and names the "
                  "time; it lays out the path from the playbook. The choosing of what matters, and the doing, "
                  "stay yours.",
    },
    "face_artisan": {
        "name": "the Artisan",
        "scope": ["music", "melody", "harmony", "chord", "chords", "song", "photography", "photo",
                  "camera", "exposure", "craft", "woodworking", "pottery", "typography", "paint",
                  "painting", "draw", "drawing"],
        "shelves": {"music_theory", "photography", "activities"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from the operator's North Star "interesting after useful, not instead" +
        # the no-imitation law): form follows function; no ornament exists only to imitate or decorate.
        "manner": "the artisan — making it well: the craft beneath the music, the image, the made thing — "
                  "proportion, timing, the telling detail. It is interesting after it is useful, never "
                  "instead; no ornament exists only to imitate or decorate — the craft serves the one who "
                  "receives it. From the makers in the keeping; the hand and the taste are yours.",
    },
    # ── ADVISORS (counsel, guide, steady). The three credentialed ones serve the function and name the
    # boundary; the Physician and Counselor defer to the crisis net first (help-first, never overridden).
    "face_counsel": {
        "name": "the Counsel",
        "scope": ["legal", "lawyer", "attorney", "rights", "my rights", "contract", "lease", "tenant",
                  "landlord", "sue", "lawsuit", "court", "statute", "liability", "is it legal",
                  "legal document", "custody", "a will"],
        "shelves": {"law", "document_validation"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's covenant non-negotiables): the plain terms and the exit it
        # leaves you (a funded right of exit; no one entity controls all of it).
        "manner": "the counsel — how the law works and what a document says: your rights, the plain terms, "
                  "the usual path, and the exit it leaves you. It serves the function; it is not a licensed "
                  "attorney and gives no advice for your case — for anything filed or signed, a real lawyer. "
                  "The deciding stays yours.",
    },
    "face_physician": {
        "name": "the Physician",
        "scope": ["symptom", "symptoms", "sick", "ill", "unwell", "illness", "disease", "injury",
                  "hurt", "medication", "medicine", "doctor", "see a doctor", "dose", "dosage", "pain",
                  "fever", "rash", "infection", "treatment", "diagnosis", "what are the symptoms",
                  "is it serious", "wound"],
        "shelves": {"medicine", "first_aid", "apothecary", "nutrition"},
        "verifiers": [],
        "discernment": False,
        # DEEPENED (2026-10-30, from The Way's healthcare at human scale): a person to be cared for, not a
        # case to be processed.
        "manner": "the physician — the honest facts of the body: what a symptom may mean, what a medicine "
                  "does, the care that helps. You are a person to be cared for, not a case to be processed. "
                  "It serves the function; it is not your doctor and makes no diagnosis — a real emergency "
                  "and anything serious go to real care, now. The body in your charge is yours.",
    },
    "face_counselor": {
        "name": "the Counselor",
        "scope": ["relationship", "marriage", "conflict", "argument", "grief", "grieving", "loss",
                  "lonely", "anxious", "anxiety", "stress", "overwhelmed", "angry", "resentment",
                  "my spouse", "my kids", "my family", "how do i cope"],
        "shelves": {"narratives", "voices", "topical", "philosophy"},
        "verifiers": [],
        "discernment": True,
        # DEEPENED (2026-10-30, from The Way "belonging"/narrow_highway "meets you where you are"): a
        # person who belongs, not a case to be processed; names the hard thing without cheapening it.
        "manner": "the counselor — meets you where you are, in the hard season: it names what is happening "
                  "without cheapening it, the next steady step, and the people who can stand with you. You "
                  "are a person who belongs, not a case to be processed. It serves the function; it is not "
                  "a licensed therapist, and a cry for help goes to real people first. You are not alone in "
                  "it, and the walking is yours.",
    },
}

_WORD = re.compile(r"[a-z0-9]+")


def faces() -> Dict[str, Dict[str, Any]]:
    """The registry (read-only view): id -> {name, scope, shelves, verifiers, discernment, manner}."""
    return {fid: {k: v for k, v in f.items()} for fid, f in _FACES.items()}


def _scores(text: str) -> Dict[str, int]:
    """Each face's fitness for the request: how many of its scope phrases the request trips."""
    toks = set(_WORD.findall((text or "").lower()))
    low = " " + (text or "").lower() + " "
    scores: Dict[str, int] = {}
    for fid, f in _FACES.items():
        score = 0
        for s in f["scope"]:
            # multi-word phrases matched as substrings, single words as tokens
            score += (1 if s in low else 0) if " " in s else (1 if s in toks else 0)
        scores[fid] = score
    return scores


def route(text: str) -> Optional[str]:
    """Which face does this request call for? The face whose scope the request overlaps most; None if
    nothing overlaps (the caller then uses the ordinary front door — a face is never forced).

    When the allocation lever (physiology) is on, a TIE in fitness is broken toward the caste with
    capacity — division of labor + the homeostatic brake — and re-allocates to an available caste if the
    fittest is out. It only ever reorders WITHIN the top fitness tier; it never routes to a face the
    request does not fit, so the plain routing is unchanged whenever there is a single clear best."""
    if not _WORD.findall((text or "").lower()):
        return None
    scores = _scores(text)
    if physiology.enabled():
        return physiology.allocate(scores)
    best, best_score = None, 0
    for fid, score in scores.items():
        if score > best_score:
            best, best_score = fid, score
    return best if best_score > 0 else None


def compose(face_id: str, text: str, config: Any = None, *,
            crisis_fn: Optional[Callable[[str], bool]] = None,
            search_fn: Optional[Callable[..., List[dict]]] = None,
            discern_fn: Optional[Callable[..., Dict[str, Any]]] = None,
            verify_fn: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None,
            faculty_fn: Optional[Callable[[Dict[str, Any], str], Any]] = None,
            witness_fn: Optional[Callable[[str], Any]] = None,
            ) -> Dict[str, Any]:
    """Assemble a face's answer, deterministically. NEVER generates: returns a structured result the
    caller renders. The dependencies are injectable for tests; they default to the live specialists.

    Order (docs/EXPERT_FACES.md): crisis gate → gather (scoped) → discern → verify → render-frame.
    """
    face = _FACES.get(face_id)
    if face is None:
        return {"error": "unknown face", "face": face_id}

    _is_crisis = crisis_fn or (lambda t: __import__("concordance.ask", fromlist=["is_crisis"]).is_crisis(t))
    # 1. CRISIS FIRST — a face never speaks over a cry (help-first, never overridden).
    if _is_crisis(text):
        return {"face": face_id, "name": face["name"], "kind": "crisis",
                "handoff": "crisis", "gathered": [], "verify": None, "discern": None,
                "manner": face["manner"],
                "means": "a cry outranks the servant — this is handed to the crisis response, real people first"}

    # This servant is now doing the work — record a unit of recent load (aggregate, content-free) so the
    # allocation lever can balance the castes and regulate the rate. No-op unless the lever is on.
    if physiology.enabled():
        physiology.note(face_id)

    # 2. GATHER — scoped to the face's shelves first (the servant's own substance), then the keeping.
    if search_fn is None:
        from . import corpus as _corpus
        def search_fn(q, shelves=None, limit=6):  # noqa: E306
            return _corpus.search(q, limit=limit, shelves=shelves)
    hits = search_fn(text, shelves=set(face["shelves"]), limit=6) or []
    if not hits:
        hits = search_fn(text, shelves=None, limit=6) or []   # fall back to the whole keeping
    gathered = [_brief(h) for h in hits[:6]]

    # 3. DISCERN — the front-door proposal. It does two jobs: it names the checkable CLAIM (which the
    # verify step needs) AND, where the face carries worldview weight, the calibration. So it ALWAYS
    # runs (crisis was already handled above); the `discernment` flag only governs whether the
    # calibration is SHOWN, not whether the claim is proposed.
    if discern_fn is None:
        from . import discern as _discern
        discern_fn = _discern.served
    try:
        proposal = discern_fn(text)
    except Exception:  # noqa: BLE001 — discern must never crash the servant
        proposal = None
    discern = proposal if face["discernment"] else None

    # 4. VERIFY — run the face's verifiers on a checkable claim IF the proposal named structured steps.
    verify = None
    steps = _steps_from_discern(proposal, face["verifiers"])
    if steps:
        if verify_fn is None:
            from .derivation import verify_derivation as verify_fn  # noqa: E501
        try:
            verify = verify_fn(steps)
        except Exception:  # noqa: BLE001 — our failure is not their falsehood; report GAP, never crash
            verify = {"verdict": "SYSTEM_ERROR", "detail": "verifier raised", "trail": []}

    # 4b. FACULTY — if this face is bound to a specialist, call it for an extra OFFERING (deterministic,
    # FOUND, never generated): the Bard's fitting parable, the Coach's next rep. Fails closed to None — an
    # honest GAP, never a crash — and never seals or grades (WALK-legal; see engagement.INTENTS).
    faculty = None
    if face.get("faculty"):
        _fac = faculty_fn or _faculty
        try:
            faculty = _fac(face, text)
        except Exception:  # noqa: BLE001 — a specialist's failure is a GAP, never the caller's crash
            faculty = None

    # 4c. CLOUD OF WITNESSES (Heb 12:1) — beside a worldview-weighted face, surface named REAL figures from
    # the keeping whose CITED entry bears on the situation (never generated, never spoken for). Opt-in via
    # witness_fn (the surface passes faces.witnesses_for); default off and empty. Fails closed to [].
    witnesses: List[Dict[str, Any]] = []
    if witness_fn is not None and face.get("discernment"):
        try:
            witnesses = witness_fn(text) or []
        except Exception:  # noqa: BLE001 — a witness we cannot reach is silence, never a crash
            witnesses = []

    # 5. RENDER FRAME — DATA the caller renders; the manner is fixed, the content is the keeping's.
    return {
        "face": face_id, "name": face["name"], "kind": "served",
        "manner": face["manner"],
        "gathered": gathered,               # cards from the keeping (the substance)
        "discern": discern,                 # the calibration proposal (or None)
        "verify": verify,                   # a worked, sealed verdict (or None = GAP: nothing checkable)
        "offering": faculty,                # the bound specialist's found offering (or None = no faculty/GAP)
        "witnesses": witnesses,             # the cloud of witnesses: named figures' cited entries (or [])
        "shelves": sorted(face["shelves"]),
        "means": ("this servant ARRANGES what the keeping holds and the gates passed — it does not "
                  "author; where it cannot check, it says so. The eye is turned upward, not to itself."),
    }


def roster() -> List[Dict[str, Any]]:
    """The pullable experts: id, name, and a short 'for' (the head of its scope) — what the Conductor
    can direct a request to, and what a caller can pull by name."""
    out: List[Dict[str, Any]] = []
    for fid, f in _FACES.items():
        scope = [s for s in (f.get("scope") or []) if " " not in s][:5]
        out.append({"id": fid, "name": f["name"], "for": ", ".join(scope)})
    return out


def _resolve_expert(expert: str) -> Optional[str]:
    """Resolve a pull request to a face id. Accepts the id ('face_steward'), the full name
    ('the Bookkeeper'), or the bare name ('bookkeeper') — case-insensitive. None if no such expert."""
    key = (expert or "").strip().lower()
    if not key:
        return None
    if key in _FACES:
        return key
    for fid, f in _FACES.items():
        name = f["name"].lower()
        if key in (fid.lower(), name, name.replace("the ", "", 1)):
            return fid
    return None


def direct(text: str, expert: Optional[str] = None, config: Any = None, **kw) -> Dict[str, Any]:
    """THE CONDUCTOR — one director for the whole village. Either PULL a named expert, or let the
    Conductor DIRECT the request to the expert whose scope fits best, then compose that expert's answer.
    When nothing fits, it returns routed=None so the caller falls back to the ordinary front door — an
    expert is never forced where none belongs. The compose dependencies pass straight through (**kw),
    so this is as injectable (and testable) as compose itself. Returns:
        {ok, routed: <id|None>, expert: <name|None>, how: 'pulled'|'directed', served: <compose result>}
    """
    if expert:
        fid = _resolve_expert(expert)
        if fid is None:
            return {"ok": False, "error": f"no such expert: {expert!r}",
                    "experts": [f["name"] for f in _FACES.values()]}
        how = "pulled"
    else:
        fid = route(text)
        if fid is None:
            return {"ok": True, "routed": None, "expert": None, "how": "directed",
                    "means": "no expert fits this request — use the ordinary front door; the Conductor "
                             "never forces an expert where none belongs"}
        how = "directed"
    served = compose(fid, text, config, **kw)
    return {"ok": True, "routed": fid, "expert": served.get("name"), "how": how, "served": served}


def convene(text: str, k: int = 3, config: Any = None, **kw) -> Dict[str, Any]:
    """THE CONDUCTOR CONVENES A PANEL — for a many-sided request, seat the top-k experts whose scope
    actually fits (by scope-overlap score), compose each, and return them combined (best-fit leads).
    This is experts combined BY an expert: the Conductor selects and orders the panel; each member
    still composes deterministically over the keeping, and no expert with zero overlap is ever seated
    (nothing is forced). Returns {ok, convened, lead, panel:[{id, expert, score, served}], means}."""
    scores = _scores(text)
    seated = sorted(((s, fid) for fid, s in scores.items() if s > 0), key=lambda p: (-p[0], p[1]))
    seated = seated[: max(1, int(k))]
    if not seated:
        return {"ok": True, "convened": 0, "lead": None, "panel": [],
                "means": "no expert's scope fits — the front door answers this one"}
    panel: List[Dict[str, Any]] = []
    for s, fid in seated:
        served = compose(fid, text, config, **kw)
        panel.append({"id": fid, "expert": served.get("name"), "score": s, "served": served})
    return {"ok": True, "convened": len(panel), "lead": panel[0]["expert"], "panel": panel,
            "means": "experts combined by the Conductor; the best-fit leads, the rest inform"}


def _faculty(face: Dict[str, Any], text: str) -> Any:
    """Call a face's bound specialist for an extra OFFERING — deterministic, FOUND in the keeping, never
    generated. Returns None on any failure or when the face has no faculty (an honest GAP). Each binding is
    WALK-legal (engagement.INTENTS): a found parable, a recommended next rep — never a seal, never a grade."""
    key = face.get("faculty")
    if not key:
        return None
    if key == "parable":                       # the Bard — the fitting parable for the situation
        from . import parable
        return parable.for_situation(text, resolve=False)   # light: the match, not the heavy passage pull
    if key == "coach_recommend":               # the Coach — the next rep toward mastery (never grades)
        from . import coach
        return coach.recommend()
    return None


# Common words that are never a figure's name — kept out of the witness search so a bare word can't pull
# a figure in by accident (keeps the cloud 0-false-positive, the same register as the parable matcher).
_WITNESS_STOP = frozenset({"what", "when", "where", "which", "that", "this", "with", "about", "does",
                           "did", "the", "and", "for", "how", "why", "your", "you", "are", "was",
                           "were", "from", "have", "has", "into", "over", "under", "will", "would",
                           "should", "could", "there", "their", "them", "they", "then", "than"})


def witnesses_for(text: str, limit: int = 3,
                  get_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
    """The cloud of witnesses (Heb 12:1): named REAL figures from the keeping whose CITED entry bears on
    the situation — surfaced, never generated, never spoken for. HIGH-PRECISION: a query token is resolved
    by EXACT name/slug (`characters.get`) and kept only when it is a PERSON (a concept or place is not a
    witness), so a query naming no person returns [] — honest silence, never a forced witness. Fails to []."""
    if not (text or "").strip():
        return []
    from . import characters
    gfn = get_fn or characters.get
    toks = [w for w in _WORD.findall(text.lower()) if len(w) >= 4 and w not in _WITNESS_STOP]
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for tok in toks:
        try:
            g = gfn(tok)
        except Exception:  # noqa: BLE001 — a witness we cannot reach is silence, never a crash
            continue
        if not g:
            continue
        slug = g.get("slug")
        if not slug or slug in seen:
            continue
        if (g.get("category") or "").lower() != "person":        # a WITNESS is a person, not concept/place
            continue
        if tok not in (g.get("name") or "").lower() and tok not in slug:   # the token hits the name
            continue
        seen.add(slug)
        out.append({
            "name": g.get("name"), "slug": slug, "preview": g.get("summary") or "",
            "ref_count": g.get("ref_count"), "scripture_refs": (g.get("scripture_refs") or [])[:6],
            "cited": True, "source": characters.SOURCE, "attribution": characters.ATTRIBUTION,
            "means": "a real figure from the keeping; their own cited entry, never spoken for",
        })
        if len(out) >= max(1, int(limit)):
            return out
    return out


def _brief(c: dict) -> Dict[str, Any]:
    from . import corpus as _corpus
    try:
        return _corpus._brief(c)
    except Exception:  # noqa: BLE001
        return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf")}


def _steps_from_discern(discern: Optional[Dict[str, Any]], verifiers: List[str]) -> List[Dict[str, Any]]:
    """If discern proposed one or more STRUCTURED checkable claims in a domain this face verifies,
    shape them into verify_derivation steps. Conservative: no structured claim → no steps → honest GAP."""
    if not discern or not verifiers:
        return []
    claim = discern.get("claim")
    if not isinstance(claim, dict):
        return []
    dom = str(claim.get("domain") or "").lower()
    if dom and dom not in {v.lower() for v in verifiers}:
        return []
    spec = claim.get("spec") or {"mode": claim.get("mode"), "params": claim.get("params", {})}
    if not spec.get("mode"):
        return []
    return [{"id": "s", "domain": dom or verifiers[0], "spec": spec}]
