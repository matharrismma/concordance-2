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
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .verifiers import VERIFIERS, WITNESS_VERIFIERS

# ORTHOGONALIZE THE DOMAIN BASIS (DESIGN_FROM_THE_DOTS lever 2). The domain vectors share phrases — the
# Gram off-diagonals, which show up as cross-talk (the runner-up crowding the leader). Down-weight each
# phrase by HOW MANY domains carry it, so a domain scores on what is DISTINCT to it (common-mode removal).
# A phrase in one domain is untouched (82% of them); a shared phrase contributes less to each, so the
# correct domain's own vocabulary wins the margin. Default ON; CONCORDANCE_DECORR=off restores the flat
# basis. Measured on the recall families: cross-talk 0.270->0.225, invariance 96.9%->99.0%.
_DECORR = (os.environ.get("CONCORDANCE_DECORR", "idf").strip().lower() not in ("off", "0", "false", "none"))

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
    # ── reach (issue #11, 2026-10-16): everyday vocabulary for the 29 registered domains that had none.
    # Written as _phrases tokenizes a query; words another domain owns are deliberately left out.
    "approximation": ('ballpark', 'rough estimate', 'approximately', 'roughly', 'order magnitude', 'close enough', 'within percent', 'give take', 'estimate within'),
    "archaeology": ('carbon dating', 'radiocarbon dating', 'radiometric dating', 'half lives', 'artifact age', 'dating the sample', 'potassium argon', 'uranium lead', 'decay dating', 'sample age'),
    "architecture": ('floor area ratio', 'occupant load', 'stair riser', 'stair tread', 'window wall ratio', 'building code', 'load bearing wall', 'egress', 'building height', 'setback', 'occupancy limit'),
    "atomic": ('electron configuration', 'quantum numbers', 'electron shell', 'valence electrons', 'orbital', 'orbitals', 'principal quantum', 'energy level', 'fine structure', 'shell capacity', 'subshell', 'aufbau', 'pauli exclusion', 'hund rule'),
    "chess": ('chess', 'checkmate', 'stalemate', 'castling', 'passant', 'chessboard', 'chess position', 'chess move', 'fen position', 'knight', 'bishop', 'rook'),
    "condensed_matter": ('phonon', 'fermi energy', 'fermi level', 'bragg', 'crystal lattice', 'unit cell', 'debye temperature', 'band gap', 'quantum hall', 'superconductor', 'semiconductor', 'lattice constant', 'brillouin zone', 'solid state'),
    "cybersecurity": ('password entropy', 'password strength', 'tls version', 'cvss', 'cvss score', 'subnet', 'subnet mask', 'cidr', 'port number', 'well known port', 'open port', 'firewall rule', 'brute force attack'),
    "document_validation": ('isbn', 'luhn', 'check digit', 'credit card number', 'ean', 'upc', 'barcode', 'valid isbn', 'checksum digit', 'card number valid'),
    "electrochemistry": ('nernst equation', 'cell potential', 'electrode potential', 'faraday', 'electrolysis', 'galvanic cell', 'voltaic cell', 'half cell', 'reduction potential', 'half reaction', 'electroplating', 'cell emf'),
    "elliptic_curves": ('elliptic curve', 'bsd', 'birch swinnerton', 'swinnerton dyer', 'rank the curve', 'mordell', 'weierstrass', 'rational points', 'cremona'),
    "energy": ('off grid', 'solar panel', 'solar panels', 'battery bank', 'kwh per day', 'watt hours', 'kilowatt hours', 'amp hours', 'inverter', 'generator sizing', 'daily consumption', 'solar yield', 'peak sun hours'),
    "game_theory": ('nash equilibrium', 'prisoner dilemma', 'prisoners dilemma', 'dominant strategy', 'payoff matrix', 'expected payoff', 'zero sum', 'zero sum game', 'mixed strategy', 'tit for tat', 'iterated game', 'best response'),
    "information_theory": ('shannon entropy', 'bits entropy', 'channel capacity', 'hamming distance', 'binary symmetric channel', 'bits per symbol', 'mutual information', 'huffman', 'compression ratio', 'information content', 'surprisal'),
    "linear_algebra": ('dot product', 'cross product', 'matrix', 'matrices', 'determinant', 'eigenvalue', 'eigenvalues', 'eigenvector', 'vector magnitude', 'unit vector', 'matrix multiplication', 'transpose', 'inverse matrix', 'identity matrix', 'linear transformation', 'rank the matrix', 'angle between vectors'),
    "manufacturing": ('six sigma', 'sigma level', 'control limits', 'control chart', 'process capability', 'cpk', 'tolerance stack', 'tolerance stackup', 'defects per million', 'dpmo', 'upper control limit', 'lower control limit'),
    "materials_science": ('stress strain', 'young modulus', 'youngs modulus', 'tensile strength', 'yield strength', 'thermal expansion', 'coefficient expansion', 'hardness', 'mohs hardness', 'brinell', 'rockwell', 'elastic modulus', 'alloy', 'ductile', 'brittle'),
    "molecular_geometry": ('vsepr', 'molecular geometry', 'molecular shape', 'bond angle', 'bond angles', 'tetrahedral', 'trigonal planar', 'trigonal bipyramidal', 'octahedral', 'bent molecule', 'linear molecule', 'lone pairs', 'electron domains', 'electron geometry', 'steric number'),
    "neuroscience": ('action potential', 'resting potential', 'membrane potential', 'nernst potential', 'goldman', 'goldman equation', 'weber fechner', 'just noticeable difference', 'neuron', 'neurons', 'synapse', 'ion channel', 'sodium potassium', 'myelin', 'refractory period'),
    "operations_research": ('linear programming', 'linear program', 'feasible region', 'critical path', 'critical path method', 'pert', 'knapsack', 'assignment problem', 'simplex', 'objective function', 'optimal solution', 'minimize cost', 'maximize profit', 'transportation problem'),
    "periodic_table": ('periodic table', 'atomic number', 'atomic mass', 'element symbol', 'noble gas', 'noble gases', 'halogen', 'halogens', 'alkali metal', 'transition metal', 'isotope', 'isotopes', 'moseley', 'group and period', 'which element', 'atomic weight'),
    "philosophy": ('modal logic', 'necessarily', 'possible worlds', 'ethical framework', 'utilitarian', 'utilitarianism', 'deontology', 'deontological', 'virtue ethics', 'categorical imperative', 'epistemology', 'priori', 'posteriori', 'law identity', 'ship theseus', 'trolley problem', 'justified true belief', 'ontology', 'metaphysics', 'consequentialism', 'empiricism', 'rationalism'),
    "photonics": ('waveguide', 'ring resonator', 'free spectral range', 'fiber loss', 'attenuation', 'electro optic', 'half wave voltage', 'second harmonic', 'slope efficiency', 'silicon photonics', 'photonic', 'single mode fiber', 'fiber optic', 'cutoff wavelength'),
    "polynomial": ('rational root', 'rational roots', 'root theorem', 'polynomial', 'polynomials', 'integer coefficients', 'synthetic division', 'factor the polynomial', 'polynomial zeros'),
    "pressure_fighting": ('pressure fighting', 'combat grammar', 'pressure fighter', 'cutting the ring', 'ring control', 'octagon control', 'forward pressure', 'clinch', 'takedown', 'guard pass', 'ground and pound', 'striking range'),
    "retrieval": ('search precision', 'search recall', 'retrieval precision', 'retrieval recall', 'reciprocal rank', 'target rank', 'top result rank', 'false silence', 'retrieval quality'),
    "rhetoric": ('straw man', 'strawman', 'slippery slope', 'red herring', 'appeal authority', 'appeal emotion', 'begging the question', 'false dilemma', 'circular reasoning', 'non sequitur', 'quoque', 'hasty generalization', 'rhetorical', 'persuasion', 'ethos', 'pathos', 'logos'),
    "sound_law": ('grimm law', 'grimms law', 'sound shift', 'sound change', 'consonant shift', 'verner law', 'verners law', 'great vowel shift', 'cognate', 'cognates', 'proto indo european', 'proto germanic', 'umlaut', 'ablaut', 'lenition', 'palatalization', 'dissimilation', 'historical linguistics'),
    "spectral": ('change domain', 'diagonalize', 'diagonalization', 'eigenbasis', 'fourier transform', 'fourier', 'convolution theorem', 'frequency domain', 'time domain', 'laplace transform', 'transform and solve', 'basis change', 'spectral decomposition', 'map back'),
    "sports_analytics": ('batting average', 'pythagorean expectation', 'elo rating', 'elo', 'expected score', 'games behind', 'win percentage', 'runs scored', 'runs allowed', 'points per game', 'base percentage', 'slugging percentage', 'rating update'),
    "electrical": ("amp", "amps", "amperage", "volt", "volts", "voltage", "watt", "watts", "wattage",
                   "circuit", "breaker", "wiring", "outlet", "ohm", "ohms", "resistor", "capacitor",
                   "horsepower", "kilowatt"),
    "units": ("convert", "conversion", "fahrenheit", "celsius", "kelvin", "metric", "gallons",
              "liters", "ounces", "kilograms", "miles", "kilometers", "cups", "tablespoons",
              "mile", "meters", "meter", "kilometer", "inch", "inches",
              "yard", "yards", "centimeter", "centimeters", "millimeter"),
    "physical_constants": ("speed of light", "planck", "planck constant", "avogadro",
                           "avogadro's number", "boltzmann", "gravitational constant",
                           "elementary charge", "gas constant", "fine structure", "electron mass",
                           "proton mass", "vacuum permittivity"),
    "probability": ("odds", "chance", "chances", "likelihood", "dice", "roll", "rolling", "coin",
                    "flip", "probability", "lottery"),
    "statistics": ("average", "mean", "median", "deviation", "variance", "correlation", "sample",
                   "samples", "confidence", "regression", "percentile", "measurements", "measurement"),
    "mathematics": ("prove", "proof", "equation", "simplify", "identity", "expression",
                    "derivative", "integral", "algebra", "fibonacci", "golden ratio",
                    "square root", "to the power", "power of", "squared", "cubed",
                    "percent", "percentage"),
    "geometry": ("triangle", "rectangle", "circle", "area", "perimeter", "angle", "angles",
                 "radius", "diameter", "hypotenuse", "pythagorean", "cube", "volume", "cubic",
                 "sphere", "cylinder", "prism", "surface area"),
    "number_theory": ("prime", "primes", "factor", "factors", "divisible", "remainder", "modulo",
                      "divisor", "divisors", "number of divisors", "factorial"),
    "combinatorics": ("choose", "combination", "combinations", "permutation", "permutations",
                      "arrange", "arrangement", "arrangements", "ways to arrange", "ways to choose",
                      "derangement", "derangements", "binomial coefficient"),
    "labor": ("hourly", "per hour", "an hour", "hourly rate", "wage", "wages", "salary",
              "annual salary", "overtime", "gross pay", "net pay", "paycheck", "minimum wage",
              "hours worked", "hours", "hour", "paid", "earnings", "take home", "pay period"),
    # wordcraft IS our phonics program (CMU/ARPABET: rhyme, homophone, silent letter, vowel/edge
    # sound, syllables) AND the etymology shelf (Webster 1913: "X comes from Latin"). Both verify
    # here, so both route here.
    "wordcraft": ("homophone", "homophones", "anagram", "anagrams", "palindrome", "syllable",
                  "syllables", "vowel", "vowels", "consonant", "consonants", "silent letter",
                  "silent", "pronounced", "phoneme", "begins with", "starts with",
                  "most common letter", "spelled", "letters in",
                  # phonics (the pronunciation shelf)
                  "rhyme", "rhymes", "rhyming", "vowel sound", "long vowel", "short vowel",
                  "the sound", "sound of",
                  # etymology (the Webster 1913 shelf)
                  "etymology", "from latin", "from greek", "from arabic", "from french",
                  "comes from latin", "comes from greek", "derives from", "derived from",
                  "latin word", "greek word", "loanword", "root word", "originally meant",
                  "borrowed from"),
    "chemistry": ("molar", "molarity", "mole", "moles", "compound", "concentration", "stoichiometry",
                  "reaction", "molar mass", "molecular weight", "molecular mass", "grams per mole",
                  "acidic", "sodium", "chloride", "solute",
                  # chirality & asymmetric autocatalysis (Kagan-Soai; the ee/amplification verifiers)
                  "chirality", "chiral", "enantiomer", "enantiomers", "enantiomeric excess", "racemic",
                  "autocatalysis", "autocatalytic", "homochirality", "optical purity", "asymmetric synthesis"),
    "physics": ("velocity", "acceleration", "momentum", "gravity", "friction", "kinetic",
                "terminal velocity", "projectile", "newtons", "accelerating", "accelerates",
                "from rest", "deceleration", "free fall"),
    "thermodynamics": ("heat", "cool", "cooling", "boil", "boiling", "freeze", "entropy",
                       "specific heat", "insulation", "thermal", "btus"),
    "nuclear_physics": ("radioactive", "radioactivity", "half life", "isotope", "decay",
                        "radiation", "becquerel"),
    "construction": ("joist", "joists", "stud", "studs", "rafter", "rafters", "framing", "lumber",
                     "load bearing", "footing", "drywall", "square foot", "per square"),
    "real_estate": ("mortgage", "down payment", "closing cost", "property tax", "home loan",
                    "amortization", "escrow", "refinance"),
    "finance": ("interest", "compound interest", "savings", "invest", "invested", "investment",
                "loan", "principal", "retirement", "dividend", "grow at", "dollars", "grow",
                "compound", "compounded", "compounding", "doubles", "annually"),
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
                      "how many days", "date falls", "day of the week", "fell on", "what day",
                      "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"),
    "exercise_science": ("protein per", "bodyweight", "reps", "heart rate", "workout", "one rep",
                         "calories burned"),
    "formal_logic": ("syllogism", "premise", "premises", "conclusion", "valid argument",
                     "implication", "logically valid", "inference", "implies", "equivalent",
                     "equivalent to", "logically equivalent", "tautology", "contrapositive",
                     "biconditional", "if and only if", "de morgan", "modus ponens",
                     "modus tollens", "consequent", "antecedent"),
    # linguistics is GENERAL; Strong's/Biblical word relations are one specialized lane, NOT the
    # primary meaning of linguistics (Matt, 2026-10-10). General etymology lives in wordcraft
    # (Webster shelf); historical sound change in sound_law. Keep the general cognate cue here.
    "linguistics": ("cognate", "cognates"),
    "history_chronology": ("bce", "century", "centuries", "elapsed years", "years between",
                           "lasted", "dynasty", "ancient", "millennium", "reign"),
    "computer_science": ("logic gate", "and gate", "boolean", "binary", "algorithm", "truth table",
                         "bitwise"),
    "cryptography": ("password", "passphrase", "encryption", "encrypt", "brute force", "cipher",
                     "key length", "entropy bits"),
    "networking": ("subnet", "subnet mask", "cidr", "hosts", "bandwidth", "packet loss"),
    "optics": ("wavelength", "refraction", "focal length", "nanometer", "diffraction", "prism",
               # the double slit (fringe = optics.double_slit; matter wave = optics.de_broglie)
               "double slit", "double-slit", "interference pattern", "fringe", "fringes", "fringe spacing",
               "young's experiment", "de broglie", "matter wave"),
    "quantum_computing": ("born rule", "amplitude squared", "squared amplitude", "probability amplitude",
                          "qubit", "qubits", "superposition", "wavefunction", "wave function",
                          "wavefunction collapse", "measure the state", "measurement outcome"),
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

# THE WITNESS INDEX — see _build(). Consulted only when resolve_domain(..., surface="witness").
_WINDEX: Dict[str, Dict[str, float]] = {}   # phrase -> {witness domain: weight}
_WDOMAINS: set = set()
# curated everyday vocabulary for the three witness domains (the person's words on narrowhighway.org)
_WSYNONYMS: Dict[str, Tuple[str, ...]] = {
    # Terms are written the way _phrases tokenizes a query (words of 3+ letters, at most 3 of them), and the
    # build normalizes them again as a guard — a curated phrase that can never match is a silent dead entry.
    "scripture": ("verse", "verses", "passage", "chapter", "bible", "scripture", "scriptures", "book of",
                  "bible say", "bible says", "gospel", "psalm", "psalms", "epistle",
                  "old testament", "new testament", "genesis", "exodus", "matthew", "mark", "luke", "john",
                  "romans", "revelation"),
    "theology_doctrine": ("doctrine", "doctrines", "creed", "nicene", "trinity", "justification", "atonement",
                          "sanctification", "catechism", "orthodox", "orthodoxy", "heresy", "council",
                          "confession faith", "systematic theology"),
    "witness": ("testimony", "testify", "profession faith", "bear witness", "three witnesses", "witnesses",
                "attest", "attestation", "witnessed"),
}


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
            # Normalize exactly as _phrases tokenizes a query (3+ letter words, at most 3 of them). A curated
            # phrase stored RAW with a short word in it ("speed of light", "day of the week") could never
            # match a query and was a silent dead entry — 20 of 550 were (issue #22). Longer than the
            # n-gram window is dead too, so it is skipped rather than stored.
            term_n = " ".join(_WORD.findall(term.lower()))
            if term_n and len(term_n.split()) <= 3:
                _add(_INDEX, term_n, dom, 3.0)

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
                if df[w] >= max(6, ndom // 10):
                    continue   # appears in many domains -> generic prose/code leak, skip at the source
                               # (the tuning queue showed canonical/match/engine/physical/arithmetic...
                               #  were routing noise; no real term spans 7+ of 77 unrelated domains)
                idf = math.log(ndom / (df[w] + 0.5))
                _add(_INDEX, w, dom, min(1.0, 0.25 * idf) + 0.05 * min(c, 3))

    # ORTHOGONALIZE THE DOMAIN BASIS — the final pass over the whole index (aliases + synonyms +
    # function names + docstrings), so EVERY shared phrase is decorrelated, not only the docstring words.
    # Down-weight by domain-frequency: a phrase in one domain is untouched; a phrase in d domains keeps
    # log(1 + N/d)/log(1 + N). This shrinks the Gram off-diagonals (cross-talk) without discarding any
    # domain — the distinctive vocabulary that clears the floor is df=1 and stays at full strength.
    if _DECORR:
        nd = max(len(_DOMAINS), 1)
        denom = math.log(1 + nd)
        for _p, _doms in _INDEX.items():
            _dfreq = len(_doms)
            if _dfreq <= 1:
                continue
            _f = math.log(1 + nd / _dfreq) / denom
            for _d in _doms:
                _doms[_d] *= _f
    # ── THE WITNESS INDEX (reach sprint, 2026-10-16). The witness-surface verifiers (scripture,
    # theology_doctrine, witness) are registered only in WITNESS_VERIFIERS, which this resolver never read —
    # so on narrowhighway.org a verse question could not reach the scripture verifier at all. They live in a
    # SEPARATE index consulted only when surface == "witness": the secular index above (and its decorrelation
    # over the N secular domains) is byte-identical, and the Gate holds — a witness verifier never routes on
    # the secular face. Aliases + curated everyday words + the modules' verify_/check_ names; no idf pass
    # (three domains — distinctive words reinforce; there is no secular basis to decorrelate against).
    for alias, modpath in WITNESS_VERIFIERS.items():
        dom = _canon_of(modpath)
        _CANON.setdefault(alias, dom)
        _WDOMAINS.add(dom)
        _add(_WINDEX, alias.replace("_", " "), dom, 3.0)
    for dom, terms in _WSYNONYMS.items():
        for term in terms:
            # normalize exactly as _phrases tokenizes a query; a phrase longer than the n-gram window is dead
            term_n = " ".join(_WORD.findall(term.lower()))
            if term_n and len(term_n.split()) <= 3:
                _add(_WINDEX, term_n, dom, 3.0)
    for dom in sorted(_WDOMAINS):
        f = vdir / f"{dom}.py"
        if not f.exists():
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nm = node.name
                for pre in ("verify_", "check_", "_verify_"):
                    if nm.startswith(pre):
                        phrase = nm[len(pre):].replace("_", " ").strip()
                        if phrase and phrase not in _STOP:
                            _add(_WINDEX, phrase, dom, 2.0)
                            for w in phrase.split():
                                if w not in _STOP and len(w) >= 3:
                                    _add(_WINDEX, w, dom, 1.5)
    _BUILT = True


# A claim can be bare arithmetic with no domain word at all ("40 + 60 + 25 = 125", "5! = 120",
# "sqrt(144) = 12", "pi is 3.14159"): no vocabulary to match, but the STRUCTURE names the
# destination — route by the shape of the key (radix), not by scanning the corpus. This is a
# FALLBACK, consulted only when the vocabulary did not reach the floor, so a real domain word
# always wins. The hyphen is deliberately NOT an operator here: "2026-05-02" is a date, not a
# subtraction, and none of the bare-arithmetic forms need subtraction.
_ARITH_OP = re.compile(r"\d\s*[+*/×÷^%]\s*\d")
_ARITH_WORD = re.compile(r"\d\s*(?:x|times|divided by|plus|minus)\b|\bto the power\b"
                         r"|\bsquare root\b|\bsqrt\b|\d\s*%|\bpercent\b")
_ARITH_BANG = re.compile(r"\d\s*!")
_ARITH_CONST = re.compile(r"\b(?:pi|tau|phi|euler)\b")


def _structural(text: str) -> Optional[str]:
    """The domain a bare numeric claim computes to, or None — shape only, never vocabulary.
    A factorial bang -> number_theory; arithmetic, roots, powers, percent, a named constant ->
    mathematics (verify_numeric / verify_equality / verify_number_theory see the actual claim)."""
    s = text.lower()
    if not any(ch.isdigit() for ch in s):
        return None
    if _ARITH_BANG.search(s):
        return "number_theory"
    if _ARITH_OP.search(s) or _ARITH_WORD.search(s) or _ARITH_CONST.search(s):
        return "mathematics"
    return None


def resolve_domain(text: str, k: int = 3, margin: float = 0.34, floor: float = 2.5,
                   surface: str = "secular") -> Dict:
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
    if surface == "witness":
        # the witness face also reaches the witness verifiers — the Gate opens inward, never outward
        for phrase in _phrases(t):
            hit = _WINDEX.get(phrase)
            if not hit:
                continue
            for dom, w in hit.items():
                scores[dom] = scores.get(dom, 0.0) + w
                if phrase not in seen_phrase:
                    why.setdefault(dom, []).append(phrase)
            seen_phrase.add(phrase)

    if not scores:
        dom = _structural(t)
        if dom:
            return {"query": t, "crisis": False,
                    "candidates": [{"domain": dom, "score": 2.6, "why": ["numeric form"]}],
                    "decision": dom, "ask": False, "reason": f"{dom}: a bare numeric/arithmetic form"}
        return {"query": t, "crisis": False, "candidates": [], "decision": None,
                "ask": True, "reason": "no verifier vocabulary matched — try search, or rephrase"}

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    cands = [{"domain": d, "score": round(s, 2),
              "why": sorted(set(why.get(d, [])), key=lambda p: (-len(p), p))[:6]}
             for d, s in ranked[:k]]

    top_dom, top_score = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    # BORN RULE + LOGARITHMS (Matt, 2026-10-12), SURFACED as a first-class confidence signal: route by
    # amplitude SQUARED, normalized to a probability distribution over the candidates; entropy (logs) is
    # the ambiguity, crosstalk the runner-up's share. The DECISION keeps the proven pairwise margin
    # (lead = 1 - second/top >= margin) — which IS this confidence for two candidates. Measured: swapping
    # the decision to the full-distribution confidence only DEFERS more many-way ties (route 81.4% ->
    # 77.8%) with invariance flat, no clear gain for a resolver the answer path already masks — so the
    # math says keep the decision and EXPOSE the signal (for the FIND door, display, and a future,
    # recall-measured rework). See the validated design in memory.
    amps = [max(0.0, s) ** 2 for _, s in ranked[:max(k, 3)]]
    _Z = sum(amps) or 1.0
    probs = [a / _Z for a in amps]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0.0)
    meta = {"confidence": round(probs[0] if probs else 0.0, 3), "entropy": round(entropy, 3),
            "crosstalk": round(second / top_score, 3) if top_score else 0.0}
    # Name a single domain only when the leader is strong AND clearly ahead; else ask.
    lead = (top_score - second) / top_score if top_score else 0.0
    if top_score >= floor and (len(ranked) == 1 or lead >= margin):
        return {"query": t, "crisis": False, "candidates": cands, "decision": top_dom,
                "ask": False, "reason": f"{top_dom}: matched {cands[0]['why']}", **meta}
    # Basis overlap, not genuine ambiguity: if the SAME term drove both leaders ("molar mass" for
    # chemistry AND periodic_table), that is one signal split across overlapping domains, not two
    # interpretations — route to the stronger. The sine/cosine lesson: this tie is non-orthogonality,
    # not a real choice, and either verifier would see the same claim. A near-tie driven by
    # DIFFERENT terms is a real ambiguity and still asks, below.
    if top_score >= floor and len(cands) > 1 and (set(cands[0]["why"]) & set(cands[1]["why"])):
        return {"query": t, "crisis": False, "candidates": cands, "decision": top_dom, "ask": False,
                "reason": f"{top_dom}: {cands[0]['why']} (shared term across overlapping domains, strongest wins)", **meta}
    # Vocabulary was too weak to name a domain (below the floor): try the structural form before
    # giving up. A genuine near-tie between real domains (top >= floor) still asks — never guessed.
    if top_score < floor:
        dom = _structural(t)
        if dom:
            return {"query": t, "crisis": False,
                    "candidates": [{"domain": dom, "score": 2.6, "why": ["numeric form"]}] + cands,
                    "decision": dom, "ask": False, "reason": f"{dom}: a bare numeric/arithmetic form", **meta}
    return {"query": t, "crisis": False, "candidates": cands, "decision": None, "ask": True,
            "reason": "more than one domain fits — ask which: " + ", ".join(c["domain"] for c in cands), **meta}


def domains() -> List[str]:
    """Every canonical verify domain the resolver can name."""
    _build()
    return sorted(_DOMAINS)
