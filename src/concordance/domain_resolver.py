"""Domain resolver — the verify member's next hop, deterministic and model-free.

The Router (router.py) names the MEMBER ("this is a checkable claim -> verify"). This names the
DOMAIN within verify: a plain-language claim -> which of the deterministic verifiers should see it.
No model, like everything else in the body — the signal comes entirely from the verifiers' OWN
vocabulary, harvested statically from source so it can never drift from what actually exists:

  1. the registry aliases (VERIFIERS keys: "mortgage"->real_estate, "heat"->thermodynamics) — a
     hand-curated keyword map already, weight 3;
  2. each module's `verify_*` function names ("verify_molar_mass" -> "molar mass"), weight 2;
  3. distinctive words in each module's docstring, inverse-domain-frequency weighted (a word in one
     domain scores; a word in twenty is generic and nearly free), weight 1.

Sources are read by parsing the .py files (ast), never by importing them, so the package keeps its
lazy-import property (sympy/scipy stay unloaded). Two rules carried from the Router: crisis is never
routed here (callers check is_crisis first; we re-check to be safe), and genuine ambiguity ASKS — a
near-tie returns no single decision and the candidates, never a guess. Every candidate carries the
literal terms that matched, because a rule-based resolver can always show its work.
"""
from __future__ import annotations

import ast
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .verifiers import VERIFIERS

# Words too generic to distinguish a domain — verifier docstrings all share them.
_STOP = frozenset("""
the a an and or of to in on for with without by from as is are be was were been it its this that
these those at into over under not no yes if then else when while each per via not value values
check checks verify verifies verified verifier claim claimed result results compute computed
packet spec domain test tests data number numbers given return returns true false must may can
one two three any all some none only same other another here there which what whom they their
within across between against never always exact exactly deterministic input output run runs field
fields key keys list set string float int bool dict object kind type name names
""".split())

_WORD = re.compile(r"[a-z][a-z0-9_]{2,}")
_INCLUDE_DOCSTRINGS = True           # source (3); toggled off in tuning to isolate its signal/noise

# source (4): the everyday vocabulary a person actually uses for each domain — the bridge the
# aliases/function-names can't build ("convert"->units, "joist"->construction, "half life"->nuclear).
# Hand-curated from how the domains are spoken, NOT reverse-engineered from any test set; auditable,
# version-controlled, and still only a CONFIRM-menu (the person picks). A term may list under several
# domains when it is genuinely shared (the menu then offers both). Phrases are <=3 words, tokens >=3
# chars (one- and two-letter cues like "f-stop" don't tokenize, so they're spelled out: "aperture").
_SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "electrical": ("amp", "amps", "amperage", "volt", "volts", "voltage", "watt", "watts", "wattage",
                   "circuit", "breaker", "wiring", "outlet", "ohm", "ohms", "resistor", "capacitor",
                   "horsepower", "kilowatt"),
    "units": ("convert", "conversion", "fahrenheit", "celsius", "kelvin", "metric", "gallons",
              "liters", "ounces", "kilograms", "miles", "kilometers", "cups", "tablespoons"),
    "probability": ("odds", "chance", "chances", "likelihood", "dice", "roll", "rolling", "coin",
                    "flip", "probability", "lottery"),
    "statistics": ("average", "mean", "median", "deviation", "variance", "correlation", "sample",
                   "samples", "confidence", "regression", "percentile", "measurements", "measurement"),
    "mathematics": ("prove", "proof", "equation", "simplify", "identity", "expression",
                    "derivative", "integral", "algebra"),
    "geometry": ("triangle", "rectangle", "circle", "area", "perimeter", "angle", "angles",
                 "radius", "diameter", "hypotenuse", "pythagorean"),
    "number_theory": ("prime", "primes", "factor", "factors", "divisible", "remainder", "modulo"),
    "chemistry": ("molar", "molarity", "mole", "moles", "compound", "concentration", "stoichiometry",
                  "reaction", "molar mass", "acidic", "sodium", "chloride", "solute"),
    "physics": ("velocity", "acceleration", "momentum", "gravity", "friction", "kinetic",
                "terminal velocity", "projectile", "newtons"),
    "thermodynamics": ("heat", "cool", "cooling", "boil", "boiling", "freeze", "entropy",
                       "specific heat", "insulation", "thermal", "btus"),
    "nuclear_physics": ("radioactive", "radioactivity", "half life", "isotope", "decay",
                        "radiation", "becquerel"),
    "construction": ("joist", "joists", "stud", "studs", "rafter", "rafters", "framing", "lumber",
                     "load bearing", "footing", "drywall", "square foot", "per square"),
    "real_estate": ("mortgage", "down payment", "closing cost", "property tax", "home loan",
                    "amortization", "escrow", "refinance"),
    "finance": ("interest", "compound interest", "savings", "invest", "investment", "loan",
                "principal", "retirement", "dividend", "grow at", "dollars", "grow"),
    "genetics": ("punnett", "punnett square", "allele", "alleles", "dominant", "recessive",
                 "genotype", "phenotype", "heredity", "inherited", "recombination", "chromosome"),
    "hydrology": ("rainfall", "rain", "rain barrel", "rainwater", "runoff", "watershed", "drainage",
                  "aquifer", "flow rate", "cubic feet", "gallons off"),
    "oceanography": ("seawater", "salinity", "tide", "tides", "saltwater", "brackish"),
    "agriculture": ("seed", "seeds", "planting", "acre", "acres", "crop", "crops", "fertilizer",
                    "livestock", "harvest", "bushel", "pasture", "manure"),
    "soil_science": ("soil", "compost", "loam", "topsoil", "amendment", "tilth"),
    "music_theory": ("chord", "chords", "note", "notes", "scale", "interval", "octave", "triad",
                     "key signature"),
    "calendar_time": ("days between", "weekday", "leap year", "passover", "pentecost", "easter",
                      "how many days", "date falls"),
    "exercise_science": ("protein per", "bodyweight", "reps", "heart rate", "workout", "one rep",
                         "calories burned"),
    "formal_logic": ("syllogism", "premise", "premises", "conclusion", "valid argument",
                     "implication", "logically valid", "inference"),
    "computer_science": ("logic gate", "and gate", "boolean", "binary", "algorithm", "truth table",
                         "bitwise"),
    "cryptography": ("password", "passphrase", "encryption", "encrypt", "brute force", "cipher",
                     "key length", "entropy bits"),
    "networking": ("subnet", "subnet mask", "cidr", "hosts", "bandwidth", "packet loss"),
    "optics": ("wavelength", "refraction", "focal length", "nanometer", "diffraction", "prism"),
    "acoustics": ("resonance", "resonant", "pitch", "decibel", "decibels", "sound wave", "hertz"),
    "photography": ("aperture", "shutter", "shutter speed", "exposure", "depth of field"),
    "nutrition": ("calories", "protein", "carbs", "carbohydrate", "vitamin", "serving", "servings"),
    "astronomy": ("light year", "planet", "orbit", "galaxy", "parsec", "magnitude", "nebula"),
    "ephemeris": ("full moon", "new moon", "sunrise", "sunset", "moon phase", "solstice", "equinox"),
    "geology": ("mineral", "sediment", "strata", "erosion", "fault", "earthquake", "radiometric"),
    "meteorology": ("frost", "dew point", "humidity", "forecast", "wind chill", "barometric"),
    "geography": ("latitude", "longitude", "elevation", "population", "distance between"),
    "law": ("contract", "clause", "liability", "statute", "lawsuit", "jurisdiction", "signature clause"),
    "governance": ("decision packet", "witnesses", "quorum", "bylaws", "consensus"),
    "economics": ("inflation", "supply", "demand", "unemployment", "recession"),
    "ecology": ("ecosystem", "biodiversity", "food web", "carbon", "sequestration", "habitat"),
    "biology": ("enzyme", "organism", "mitosis", "photosynthesis", "respiration"),
    "medicine": ("dose", "dosage", "milligrams", "symptom", "blood pressure", "medication"),
}
_CANON: Dict[str, str] = {}          # alias -> canonical domain (module basename)
_INDEX: Dict[str, Dict[str, float]] = {}   # phrase -> {domain: weight}
_DOMAINS: set = set()
_BUILT = False


def _canon_of(modpath: str) -> str:
    return modpath.rsplit(".", 1)[-1]


def _phrases(text: str, n: int = 3):
    """Unigrams..n-grams of the word tokens in text."""
    toks = _WORD.findall(text.lower())
    for i in range(len(toks)):
        for size in range(1, n + 1):
            if i + size <= len(toks):
                yield " ".join(toks[i:i + size])


def _add(index: Dict[str, Dict[str, float]], phrase: str, domain: str, weight: float) -> None:
    if not phrase:
        return
    index.setdefault(phrase, {})
    index[phrase][domain] = max(index[phrase].get(domain, 0.0), weight)


def _build() -> None:
    """Build the phrase->domain weight index once, from static source (no imports)."""
    global _BUILT
    if _BUILT:
        return
    vdir = Path(__file__).resolve().parent / "verifiers"

    # module basename -> {alias terms}, and canonical map
    modpaths = {}
    for alias, modpath in VERIFIERS.items():
        dom = _canon_of(modpath)
        _CANON[alias] = dom
        _DOMAINS.add(dom)
        modpaths[dom] = modpath
        # (1) alias as a keyword (underscores -> spaces), the strongest signal
        _add(_INDEX, alias.replace("_", " "), dom, 3.0)

    # (4) curated everyday vocabulary -> domain, weighted like the aliases (the person's words)
    for dom, terms in _SYNONYMS.items():
        if dom not in _DOMAINS:
            continue   # guard: a synonym for a domain the registry doesn't have is ignored, not phantomed
        for term in terms:
            _add(_INDEX, term, dom, 3.0)

    # (2) + (3) harvest each module's function names and docstring words, statically
    doc_terms: Dict[str, Dict[str, int]] = {}   # domain -> {word: count}
    for dom in sorted(_DOMAINS):
        f = vdir / f"{dom}.py"
        if not f.exists():
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        # (2) verify_* / check_* function names -> phrase
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nm = node.name
                for pre in ("verify_", "check_", "_verify_"):
                    if nm.startswith(pre):
                        phrase = nm[len(pre):].replace("_", " ").strip()
                        if phrase and phrase not in _STOP:
                            _add(_INDEX, phrase, dom, 2.0)
                            # also index each substantive word of the function name
                            for w in phrase.split():
                                if w not in _STOP and len(w) >= 3:
                                    _add(_INDEX, w, dom, 1.5)
        # (3) module docstring words (counted now, idf-weighted after the full pass)
        mod_doc = (ast.get_docstring(tree) or "").lower()
        counts: Dict[str, int] = {}
        for w in _WORD.findall(mod_doc):
            if w in _STOP or len(w) < 4:
                continue
            counts[w] = counts.get(w, 0) + 1
        doc_terms[dom] = counts

    # inverse domain frequency for docstring words: a word in few domains is distinctive.
    ndom = max(len(_DOMAINS), 1)
    df: Dict[str, int] = {}
    for counts in doc_terms.values():
        for w in counts:
            df[w] = df.get(w, 0) + 1
    if _INCLUDE_DOCSTRINGS:
        for dom, counts in doc_terms.items():
            for w, c in counts.items():
                if df[w] >= max(6, ndom // 4):
                    continue   # appears all over -> generic, skip
                idf = math.log(ndom / (df[w] + 0.5))
                _add(_INDEX, w, dom, min(1.0, 0.25 * idf) + 0.05 * min(c, 3))
    _BUILT = True


def resolve_domain(text: str, k: int = 3, margin: float = 0.34, floor: float = 2.5) -> Dict:
    """Name the verify DOMAIN(s) a plain claim should go to. Model-free; explains itself.

    -> {query, crisis, candidates:[{domain, score, why}], decision, ask, reason}
       decision is the single domain when one clearly leads; otherwise None and ask=True (a near-tie
       or weak signal asks rather than guesses). `why` is the literal terms that matched.
    """
    _build()
    t = (str(text) if text else "").strip()
    if not t:
        return {"query": "", "crisis": False, "candidates": [], "decision": None,
                "ask": True, "reason": "nothing was brought"}

    # Crisis is never routed to a verifier. Callers check first; we re-check so the resolver is
    # safe to call on its own. Imported from ask (never copied — a duplicated safety list drifts).
    try:
        from .ask import is_crisis
        if is_crisis(t):
            return {"query": t, "crisis": True, "candidates": [], "decision": None,
                    "ask": False, "reason": "crisis — real people first, never a verifier"}
    except Exception:
        pass

    scores: Dict[str, float] = {}
    why: Dict[str, List[str]] = {}
    seen_phrase: set = set()
    for phrase in _phrases(t):
        hit = _INDEX.get(phrase)
        if not hit:
            continue
        # a longer phrase that already contributed its words shouldn't be double-paid; we credit the
        # phrase and record it, and let unigram overlaps stand (they reinforce, bounded by weights).
        for dom, w in hit.items():
            scores[dom] = scores.get(dom, 0.0) + w
            if phrase not in seen_phrase:
                why.setdefault(dom, []).append(phrase)
        seen_phrase.add(phrase)

    if not scores:
        return {"query": t, "crisis": False, "candidates": [], "decision": None,
                "ask": True, "reason": "no verifier vocabulary matched — try search, or rephrase"}

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    cands = [{"domain": d, "score": round(s, 2),
              "why": sorted(set(why.get(d, [])), key=lambda p: (-len(p), p))[:6]}
             for d, s in ranked[:k]]

    top_dom, top_score = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    # Name a single domain only when the leader is strong AND clearly ahead; else ask.
    lead = (top_score - second) / top_score if top_score else 0.0
    if top_score >= floor and (len(ranked) == 1 or lead >= margin):
        return {"query": t, "crisis": False, "candidates": cands, "decision": top_dom,
                "ask": False, "reason": f"{top_dom}: matched {cands[0]['why']}"}
    return {"query": t, "crisis": False, "candidates": cands, "decision": None, "ask": True,
            "reason": "more than one domain fits — ask which: " + ", ".join(c["domain"] for c in cands)}


def domains() -> List[str]:
    """Every canonical verify domain the resolver can name."""
    _build()
    return sorted(_DOMAINS)
