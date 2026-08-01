#!/usr/bin/env python3
"""THE ANCIENT ASSAY — 1,000 probes into the keeping, weighted to religion and knowledge before 1 AD.

    python tools/assay_ancient.py https://narrowhighway.com
    python tools/assay_ancient.py http://127.0.0.1:8002 --workers 6

Matt, 2026-08-01: *"Run 1000 test runs. Across various topics. Focused mainly on religions and
knowledge prior to 1AD. Find errors or regression and identify the source."*

This is not the unit suite. The unit suite proves the code does what it was told; this asks whether
the LIBRARY answers when a real person asks a real question — which is a different question and the
only one that matters to a reader.

FOUR VERDICTS, NEVER TWO. A query that returns nothing is not the same failure as one that raises,
and neither is the same as one that answers with a broken card:

  ERROR      the engine failed — 5xx, dropped connection, malformed JSON. OUR fault, always a defect.
  EMPTY      no card in the keeping matches. A GAP, not a defect — this is the want list's raw
             material, and pretending it is a bug would hide the real ones.
  DEGRADED   cards came back, but carrying damage we have repaired before: an unrendered `§slug`
             title, a citation pointing at a retired page, an empty body. THESE ARE REGRESSIONS and
             each one names the repair pass it escaped.
  OK         answered, with at least one card that actually mentions what was asked.

WHY EACH DEGRADATION CHECK EXISTS — every one is a defect this project has already fixed once, so
its reappearance is a regression with a known author:

  slug_title       `§aur_07_xxiii` never rendered to `7.23`     (tools/repair_cards.py, render_title)
  retired_citation `/encyclopedia.html?ref=` or `/canon.html?ref=`  (tools/repoint_citations.py — and
                   4,039 of 4,743 of these were once reported fixed while still live in the shards,
                   so this check reads the SERVED card, not the file)
  empty_body       a card with a title and nothing to read       (assay EMPTY verdict, R5)
  no_shelf         a card that belongs to no shelf — an orphan   (the no-orphans rule)

COVERAGE IS REPORTED BEFORE ANY VERDICT: how many probes, against which host, over how many domains,
and how many actually reached the engine. A pass rate over an unknown denominator is not a
measurement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# ── THE PROBES ────────────────────────────────────────────────────────────────────────────────
# Grouped by tradition/domain so a failure can be attributed rather than merely counted. Everything
# here is attested before 1 AD (a few traditions are attested later but rooted earlier — marked).
TOPICS: dict = {
    "mesopotamia_religion": [
        "Enuma Elish", "Epic of Gilgamesh", "Marduk", "Tiamat", "Enlil", "Enki", "Anu", "Ishtar",
        "Inanna", "Tammuz", "Dumuzi", "Ereshkigal", "Nergal", "Ninurta", "Shamash", "Sin moon god",
        "Adad", "Nabu", "Ashur", "Utnapishtim", "Atrahasis", "ziggurat", "Etemenanki", "Eridu",
        "Nippur", "Uruk", "Lagash", "Umma", "Kish", "Sumerian King List", "Descent of Inanna",
        "Ludlul bel nemeqi", "Babylonian theodicy", "Code of Hammurabi", "Enmerkar", "Lugalbanda",
        "Ninhursag", "Nanna", "Anunnaki", "Igigi", "apkallu", "Adapa", "Enuma Anu Enlil",
        "Babylonian astronomical diaries", "MUL.APIN", "Venus tablet of Ammisaduqa", "Esagila",
        "Sumerian temple hymns", "Gudea cylinders", "Shurpu", "Maqlu",
    ],
    "egypt_religion": [
        "Book of the Dead", "Pyramid Texts", "Coffin Texts", "Osiris", "Isis", "Horus", "Set",
        "Ra", "Amun", "Amun-Ra", "Ptah", "Thoth", "Anubis", "Hathor", "Sekhmet", "Maat",
        "Akhenaten", "Aten", "Great Hymn to the Aten", "Nefertiti", "Book of Gates",
        "Amduat", "weighing of the heart", "ka and ba", "Duat", "Ennead", "Ogdoad", "Heliopolis",
        "Memphis theology", "Shabaka Stone", "Instruction of Ptahhotep", "Instruction of Amenemope",
        "Dispute between a man and his Ba", "Tale of Sinuhe", "Westcar Papyrus", "Edwin Smith papyrus",
        "Ebers papyrus", "Rhind Mathematical Papyrus", "Moscow Mathematical Papyrus", "Narmer Palette",
        "Rosetta Stone", "hieroglyphs", "Serapis", "Apis bull", "Opet festival", "Sed festival",
        "canopic jars", "mummification",
    ],
    "hebrew_second_temple": [
        "Torah", "Tanakh", "Pentateuch", "Septuagint", "Masoretic Text", "Dead Sea Scrolls",
        "Qumran", "Community Rule", "War Scroll", "Temple Scroll", "Habakkuk Pesher",
        "Copper Scroll", "Essenes", "Pharisees", "Sadducees", "Zealots", "Sanhedrin",
        "Second Temple", "Zerubbabel", "Ezra", "Nehemiah", "Maccabees", "Hasmonean",
        "Antiochus IV Epiphanes", "Hanukkah", "Book of Enoch", "Jubilees", "Book of Sirach",
        "Wisdom of Solomon", "Tobit", "Judith", "Baruch", "Psalms of Solomon",
        "Testaments of the Twelve Patriarchs", "Elephantine papyri", "Samaritan Pentateuch",
        "Nash Papyrus", "Shema Yisrael", "Decalogue", "Day of Atonement", "Passover", "Shavuot",
        "Sukkot", "Jubilee year", "Levitical priesthood", "Aaronic blessing", "Ketef Hinnom",
        "Siloam inscription", "Mesha Stele", "Tel Dan Stele",
    ],
    "canaan_phoenicia": [
        "Baal", "Asherah", "El Canaanite", "Anat", "Mot", "Yam", "Dagon", "Molech",
        "Ugarit", "Baal Cycle", "Ras Shamra", "Keret Epic", "Aqhat Epic", "Ugaritic alphabet",
        "Phoenician alphabet", "Melqart", "Astarte", "Tanit", "Eshmun", "Byblos", "Tyre", "Sidon",
        "Carthage", "Sanchuniathon", "high place bamah", "Asherah pole", "Baal Hammon",
    ],
    "persia_zoroastrian": [
        "Zoroaster", "Zarathustra", "Ahura Mazda", "Angra Mainyu", "Avesta", "Gathas", "Yasna",
        "Vendidad", "Yasht", "Amesha Spentas", "Asha", "Druj", "Fravashi", "Chinvat Bridge",
        "Frashokereti", "Tower of Silence", "Magi", "Achaemenid religion", "Behistun Inscription",
        "Cyrus Cylinder", "Darius I", "Xerxes daiva inscription", "Mithra", "Anahita", "Verethragna",
        "Zurvanism", "fire temple", "haoma",
    ],
    "greek_religion_philosophy": [
        "Homer Iliad", "Homer Odyssey", "Hesiod Theogony", "Works and Days", "Orphism",
        "Orphic hymns", "Eleusinian Mysteries", "Demeter and Persephone", "Dionysian Mysteries",
        "Delphi oracle", "Pythia", "Zeus", "Athena", "Apollo", "Artemis", "Hermes", "Hephaestus",
        "Poseidon", "Hera", "Hades", "Prometheus", "Titanomachy", "Homeric Hymns", "Pindar",
        "Aeschylus", "Sophocles", "Euripides", "Aristophanes", "Thales", "Anaximander",
        "Anaximenes", "Heraclitus", "Parmenides", "Zeno of Elea", "Empedocles", "Anaxagoras",
        "Democritus", "Leucippus", "Pythagoras", "Pythagorean theorem", "Socrates", "Plato Republic",
        "Plato Timaeus", "Plato Phaedo", "theory of forms", "Aristotle Metaphysics",
        "Aristotle Nicomachean Ethics", "Aristotle Organon", "Aristotle Physics", "Epicurus",
        "Epicureanism", "Zeno of Citium", "Stoicism", "Chrysippus", "Cynicism", "Diogenes",
        "Pyrrho", "skepticism", "Neoplatonism roots", "logos Heraclitus", "nous", "Academy",
        "Lyceum", "Stoa Poikile", "Isocrates", "Thucydides", "Herodotus", "Xenophon",
    ],
    "rome_pre_christian": [
        "Cicero De Natura Deorum", "Cicero De Officiis", "Lucretius De Rerum Natura", "Virgil Aeneid",
        "Virgil Eclogues", "Horace Odes", "Ovid Metamorphoses", "Livy Ab Urbe Condita",
        "Roman religion", "Jupiter Optimus Maximus", "Vesta", "Vestal Virgins", "pontifex maximus",
        "augury", "haruspex", "Sibylline Books", "Lares and Penates", "Saturnalia", "Bacchanalia",
        "Cybele Magna Mater", "Mithraism origins", "Twelve Tables", "Roman calendar",
        "Julian calendar", "Varro", "Cato the Elder", "Seneca the Elder", "Polybius",
        "Sallust", "Catullus", "Plautus", "Terence", "Vitruvius", "Pliny the Elder",
    ],
    "india_pre1ad": [
        "Rigveda", "Samaveda", "Yajurveda", "Atharvaveda", "Brahmanas", "Aranyakas",
        "Upanishads", "Brihadaranyaka Upanishad", "Chandogya Upanishad", "Katha Upanishad",
        "Isha Upanishad", "Mundaka Upanishad", "Brahman", "Atman", "karma", "samsara", "moksha",
        "dharma", "rita", "Agni", "Indra", "Varuna", "Soma", "Purusha Sukta", "Nasadiya Sukta",
        "Vedanta roots", "Samkhya", "Yoga Sutras roots", "Nyaya", "Vaisheshika", "Mimamsa",
        "Siddhartha Gautama", "Four Noble Truths", "Eightfold Path", "Tripitaka", "Pali Canon",
        "Dhammapada", "Ashoka edicts", "Sanchi", "Mahavira", "Jainism", "ahimsa", "anekantavada",
        "Charvaka", "Panini Ashtadhyayi", "Arthashastra", "Sushruta Samhita", "Charaka Samhita",
        "Ayurveda", "Bakhshali manuscript", "Sulba Sutras", "Mahabharata", "Ramayana",
        "Bhagavad Gita",
    ],
    "china_pre1ad": [
        "I Ching", "Book of Changes", "Confucius Analects", "Confucianism", "Mencius", "Xunzi",
        "Laozi Tao Te Ching", "Daoism", "Zhuangzi", "Liezi", "Mozi", "Mohism", "Han Feizi",
        "Legalism", "Shang Yang", "Sun Tzu Art of War", "Book of Documents", "Shijing Book of Songs",
        "Book of Rites", "Spring and Autumn Annals", "Zuo Zhuan", "Guanzi", "Huainanzi",
        "Sima Qian Shiji", "Mandate of Heaven", "yin and yang", "wu xing five phases", "qi",
        "ancestor veneration", "oracle bones", "Zhou dynasty ritual", "Nine Chapters roots",
        "Zhoubi Suanjing", "Chu Ci", "Warring States",
    ],
    "other_traditions": [
        "Druids", "Celtic religion", "Ogham roots", "Norse pre-Christian roots", "Germanic paganism",
        "Scythian religion", "Thracian Orpheus", "Etruscan religion", "Etruscan haruspicy",
        "Olmec religion", "Maya Long Count", "Zapotec writing", "Nubian Kushite religion",
        "Meroitic", "Berber ancient religion", "Arabian pre-Islamic deities", "Nabataean Dushara",
        "Petra", "Palmyra Bel", "Hittite religion", "Hittite laws", "Hurrian Kumarbi",
        "Elamite religion", "Urartian Haldi", "Minoan religion", "Mycenaean Linear B religion",
        "Sabaean South Arabian", "Aksumite roots", "Japanese Yayoi ritual", "Korean Gojoseon",
    ],
    "ancient_mathematics": [
        "Euclid Elements", "Archimedes", "Archimedes method of exhaustion", "Eratosthenes",
        "Eratosthenes sieve", "Eratosthenes earth circumference", "Apollonius of Perga conics",
        "Hipparchus", "Aristarchus of Samos", "Eudoxus", "Theaetetus", "Hippocrates of Chios",
        "Plimpton 322", "Babylonian sexagesimal", "Egyptian fractions", "Pythagorean triples",
        "golden ratio ancient", "irrational numbers discovery", "Zeno paradoxes",
        "method of false position", "Chinese remainder theorem roots", "Nine Chapters",
        "gnomon", "Antikythera mechanism", "Callippic cycle", "Metonic cycle", "Saros cycle",
        "Babylonian System A", "Babylonian System B", "Seleucid astronomy", "Kidinnu",
        "Naburimannu", "Berossus", "Autolycus of Pitane", "Menaechmus", "Archytas",
    ],
    "ancient_science_medicine": [
        "Hippocrates", "Hippocratic Corpus", "Hippocratic Oath", "four humors", "Galen precursors",
        "Herophilus", "Erasistratus", "Alexandria Library", "Museum of Alexandria",
        "Theophrastus plants", "Theophrastus stones", "Aristotle History of Animals",
        "Dioscorides roots", "Ebers papyrus remedies", "Kahun Gynaecological Papyrus",
        "trepanation ancient", "Babylonian medicine", "Sakikku diagnostic handbook",
        "Chinese acupuncture roots", "Huangdi Neijing", "Sushruta surgery", "ancient metallurgy",
        "bronze age tin", "iron age smelting", "Damascus steel roots", "Roman concrete",
        "aqueduct engineering", "Archimedes screw", "Ctesibius", "Philo of Byzantium",
        "Hero of Alexandria roots", "ancient glassmaking", "Egyptian faience", "papyrus making",
        "parchment Pergamon", "cuneiform tablets", "Linear A", "Linear B", "Phaistos Disc",
        "ancient dyeing Tyrian purple", "ancient agriculture irrigation", "shaduf", "qanat",
        "terracing agriculture", "crop rotation ancient", "olive press", "wine amphora",
    ],
    "ancient_texts_law_wisdom": [
        "Code of Ur-Nammu", "Laws of Eshnunna", "Lipit-Ishtar", "Middle Assyrian laws",
        "Hittite law code", "Draco laws", "Solon reforms", "Twelve Tables Rome",
        "Instruction of Shuruppak", "Counsels of Wisdom", "Ahiqar", "Papyrus Insinger",
        "Maxims of Ani", "Admonitions of Ipuwer", "Prophecy of Neferti", "Eloquent Peasant",
        "Sumerian proverbs", "Egyptian love poetry", "Hymn to the Nile", "Great Hymn to Osiris",
        "Cyrus proclamation", "Amarna letters", "Mari letters", "Nuzi tablets", "Ebla tablets",
        "Hittite treaties", "vassal treaty Esarhaddon", "Sefire inscriptions", "Zakkur stele",
        "Karatepe bilingual", "Kilamuwa", "Deir Alla inscription", "Lachish letters",
        "Arad ostraca", "Samaria ostraca", "Gezer calendar",
    ],
}

# Query shapes: the same term asked the way different callers ask. A library that only answers
# exact titles is not a library.
SHAPES = [
    "{t}",
    "what is {t}",
    "{t} meaning",
    "{t} origin",
]

_TOKEN = re.compile(r"[A-Za-z]{4,}")
_RETIRED = ("/encyclopedia.html", "/canon.html")

_LOCK = threading.Lock()


def _get(base: str, path: str, timeout: float = 45.0):
    url = base.rstrip("/") + path
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            body = None
        return e.code, body
    except Exception as e:  # noqa: BLE001
        return 0, {"__client__": f"{type(e).__name__}: {e}"}


def _source_url(card: dict) -> str:
    """A search brief carries `source` as a LABEL STRING; only the full card carries a URL.

    The first version assumed `source` was always the card's dict and called `.get("url")` on it,
    which raised AttributeError on every single hit. Worth stating plainly: the check for retired
    citations CANNOT be answered from a search result at all — the field is not there. Pretending
    otherwise would have reported "0 retired citations" over data that never contained one, which
    is a false all-clear. `--cards N` fetches full cards to answer it honestly.
    """
    src = card.get("source")
    if isinstance(src, dict):
        return str(src.get("url") or "")
    return ""


def _degradations(card: dict) -> list:
    """Damage we have repaired before. Each name points at the pass it escaped."""
    out = []
    title = str(card.get("title") or "")
    if "§" in title:
        out.append("slug_title")                       # tools/repair_cards.py render_title
    if not title.strip():
        out.append("no_title")
    url = _source_url(card)
    if url and any(r in url for r in _RETIRED):
        out.append("retired_citation")                 # tools/repoint_citations.py
    if not str(card.get("snippet") or card.get("body") or "").strip():
        out.append("empty_body")                       # assay EMPTY (R5)
    if not str(card.get("shelf") or "").strip():
        out.append("no_shelf")                         # the no-orphans rule
    return out


def probe(base: str, domain: str, term: str, shape: str) -> dict:
    q = shape.format(t=term)
    t0 = time.time()
    code, body = _get(base, "/search?q=" + urllib.parse.quote(q) + "&limit=5")
    dt = time.time() - t0
    rec = {"domain": domain, "term": term, "query": q, "code": code, "secs": dt,
           "verdict": "OK", "why": "", "degraded": [], "count": 0, "ids": []}

    if code == 0 or code >= 500 or not isinstance(body, dict):
        rec["verdict"] = "ERROR"
        rec["why"] = (body or {}).get("__client__") or f"HTTP {code}"
        return rec
    if code >= 400:
        rec["verdict"] = "ERROR"
        rec["why"] = f"HTTP {code} — the engine refused a plain read"
        return rec

    results = body.get("results") or []
    rec["count"] = len(results)
    rec["ids"] = [str(c.get("id")) for c in results if isinstance(c, dict) and c.get("id")]
    if not results:
        rec["verdict"] = "EMPTY"
        rec["why"] = "nothing in the keeping answers this"
        return rec

    dmg = []
    for c in results:
        dmg.extend(_degradations(c))
    if dmg:
        rec["verdict"] = "DEGRADED"
        rec["degraded"] = sorted(set(dmg))
        rec["why"] = ",".join(sorted(set(dmg)))
        return rec

    # Relevance: does any card actually mention what was asked? Catches "answers with junk".
    want = {w.lower() for w in _TOKEN.findall(term)}
    if want:
        hay = " ".join(f"{c.get('title','')} {c.get('snippet','') or c.get('body','')}"
                       for c in results).lower()
        if not any(w in hay for w in want):
            rec["verdict"] = "DEGRADED"
            rec["degraded"] = ["off_topic"]
            rec["why"] = "results mention none of the query's words"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default="https://narrowhighway.com")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=1000, help="how many probes to run")
    ap.add_argument("--out", default="", help="write the full record as JSON")
    ap.add_argument("--cards", type=int, default=250,
                    help="how many FULL cards to read for the citation check (0 = skip)")
    args = ap.parse_args()

    plan = []
    for domain, terms in TOPICS.items():
        for t in terms:
            plan.append((domain, t, SHAPES[0]))
    # Fill toward the requested count with the other query shapes, round-robin so every domain is
    # deepened evenly rather than exhausting one.
    si = 1
    while len(plan) < args.limit and si < len(SHAPES):
        for domain, terms in TOPICS.items():
            for t in terms:
                if len(plan) >= args.limit:
                    break
                plan.append((domain, t, SHAPES[si]))
            if len(plan) >= args.limit:
                break
        si += 1
    plan = plan[:args.limit]

    terms_total = sum(len(v) for v in TOPICS.values())
    print("THE ANCIENT ASSAY — religions and knowledge before 1 AD")
    print(f"  host      : {args.base}")
    print(f"  coverage  : {len(plan):,} probes over {len(TOPICS)} domains "
          f"({terms_total} distinct terms x up to {len(SHAPES)} query shapes)")
    print(f"  workers   : {args.workers}")
    print()

    records, idx = [], [0]

    crashes = []

    def worker():
        # A WORKER THAT DIES MUST NOT LEAVE A CLEAN-LOOKING REPORT BEHIND. The first run of this
        # tool raised AttributeError in 5 of 6 threads, completed 1 probe of 1,000, printed a full
        # verdict table, and exited 0. Every number in it was true and the whole thing was a lie —
        # exactly the silent-subset failure this assay exists to find, committed by the assay.
        # Now a crash is captured, counted, and made fatal to the verdict.
        while True:
            with _LOCK:
                if idx[0] >= len(plan):
                    return
                i = idx[0]
                idx[0] += 1
            d, t, s = plan[i]
            try:
                r = probe(args.base, d, t, s)
            except Exception as e:  # noqa: BLE001
                with _LOCK:
                    crashes.append(f"{type(e).__name__}: {e} (probe {d}/{t})")
                continue
            with _LOCK:
                records.append(r)
                n = len(records)
                if n % 100 == 0:
                    print(f"    ...{n:,} / {len(plan):,}", flush=True)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(max(1, args.workers))]
    t0 = time.time()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    elapsed = time.time() - t0

    # COVERAGE GATE — refuse to render a verdict over a subset. This is the whole discipline of
    # this file turned on itself: a report that describes 1 probe as though it described 1,000 is
    # worse than no report, because it will be believed.
    if crashes or len(records) < len(plan):
        print(f"\n{'!' * 78}")
        print(f"REFUSING TO REPORT — {len(records):,} of {len(plan):,} probes completed, "
              f"{len(crashes)} crashed.")
        print("A verdict over an unknown subset is not a measurement. Fix the harness, re-run.")
        seen = defaultdict(int)
        for c in crashes:
            seen[c.split(" (probe ")[0]] += 1
        for why, n in sorted(seen.items(), key=lambda x: -x[1])[:6]:
            print(f"  {n:>5}x  {why}")
        print("!" * 78)
        return 2

    by_verdict = defaultdict(int)
    by_domain = defaultdict(lambda: defaultdict(int))
    dmg_kinds = defaultdict(int)
    for r in records:
        by_verdict[r["verdict"]] += 1
        by_domain[r["domain"]][r["verdict"]] += 1
        for d in r["degraded"]:
            dmg_kinds[d] += 1

    reached = sum(1 for r in records if r["code"] == 200)
    print(f"\n  ran {len(records):,} probes in {elapsed:,.0f}s "
          f"({reached:,} reached the engine and returned 200)\n")
    print("=" * 78)
    print("VERDICTS")
    for v in ("OK", "EMPTY", "DEGRADED", "ERROR"):
        n = by_verdict.get(v, 0)
        pct = (100.0 * n / len(records)) if records else 0
        print(f"  {v:<9} {n:>6,}  {pct:5.1f}%")

    if dmg_kinds:
        print("\nDEGRADATION BY KIND — each names the repair pass it escaped")
        src = {"slug_title": "tools/repair_cards.py --kind render_title",
               "retired_citation": "tools/repoint_citations.py (--shards too)",
               "empty_body": "tools/repair_cards.py --retract (assay EMPTY)",
               "no_shelf": "the no-orphans rule — card minted without a shelf",
               "no_title": "card minted without a title",
               "off_topic": "ranking, not data — search returned unrelated cards"}
        for k, n in sorted(dmg_kinds.items(), key=lambda x: -x[1]):
            print(f"  {n:>6,}  {k:<18} -> {src.get(k, '?')}")

    print("\nBY DOMAIN (sorted by what is MISSING — this is the want list's raw material)")
    print(f"  {'domain':<28} {'ok':>6} {'empty':>6} {'degr':>6} {'err':>5}   worst gap")
    rows = sorted(by_domain.items(), key=lambda kv: -(kv[1].get("EMPTY", 0)))
    for domain, c in rows:
        tot = sum(c.values())
        empties = [r["term"] for r in records if r["domain"] == domain and r["verdict"] == "EMPTY"]
        ex = empties[0] if empties else ""
        print(f"  {domain:<28} {c.get('OK',0):>6} {c.get('EMPTY',0):>6} "
              f"{c.get('DEGRADED',0):>6} {c.get('ERROR',0):>5}   {ex[:28]}")

    errs = [r for r in records if r["verdict"] == "ERROR"]
    if errs:
        print(f"\nERRORS — {len(errs)} (always a defect; the engine failed a plain read)")
        seen = defaultdict(list)
        for r in errs:
            seen[r["why"]].append(r["query"])
        for why, qs in sorted(seen.items(), key=lambda x: -len(x[1])):
            print(f"  {len(qs):>5}x  {why}")
            for q in qs[:3]:
                print(f"           e.g. {q}")

    degs = [r for r in records if r["verdict"] == "DEGRADED"]
    if degs:
        print(f"\nDEGRADED — {len(degs)} examples (first 12)")
        for r in degs[:12]:
            print(f"  [{r['why']}] {r['query']}")

    # ── THE CITATION PASS — answerable only from FULL cards, so it says how many it read ────────
    # A search brief carries `source` as a label with no URL. Reporting "0 retired citations" from
    # briefs would be a false all-clear over a field that was never present.
    if args.cards:
        ids = []
        for r in records:
            for cid in r.get("ids", []):
                if cid not in ids:
                    ids.append(cid)
        ids = ids[:args.cards]
        print(f"\nCITATION PASS — reading {len(ids):,} FULL cards (of "
              f"{len(set(i for r in records for i in r.get('ids', []))):,} distinct cards seen)")
        bad, checked = defaultdict(list), 0
        for cid in ids:
            code, body = _get(args.base, "/card?id=" + urllib.parse.quote(cid))
            if code != 200 or not isinstance(body, dict):
                continue
            card = body.get("card") if isinstance(body.get("card"), dict) else body
            checked += 1
            u = _source_url(card)
            if u and any(x in u for x in _RETIRED):
                bad["retired_citation"].append(f"{cid} -> {u}")
            if "§" in str(card.get("title") or ""):
                bad["slug_title"].append(cid)
        print(f"  read {checked:,} cards")
        if not bad:
            print("  no retired citations, no unrendered slugs in the sample")
        for k, v in sorted(bad.items(), key=lambda x: -len(x[1])):
            print(f"  {len(v):>5}  {k}")
            for ex in v[:4]:
                print(f"           {ex}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=1)
        print(f"\nfull record -> {args.out}")

    # EMPTY is a gap, not a failure. Only ERROR and DEGRADED are defects.
    return 1 if (by_verdict.get("ERROR") or by_verdict.get("DEGRADED")) else 0


if __name__ == "__main__":
    sys.exit(main())
