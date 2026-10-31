#!/usr/bin/env python3
"""FIND each character's common responses in the keeping (Matt, 2026-10-31: "find 100-200 common responses for each
character" — found, never authored). For every face, its SAYING SOURCES are named exactly — shelves whose sentences
are said, not drilled (field manuals, principles, the fathers, Scripture, the almanac; PD / primary / confessional
tiers). Their bodies are split into sentences; hard filters drop questions, exercises, commentary glosses, non-Latin
script, catalog entries and the engine's own boilerplate; each line is scored as an APHORISM in the face's manner
(imperative or second-person lead, short, pointed, manner and scope vocabulary); the top N per face are written as a
CITED corpus — data/faces/responses/<face>.jsonl — the same file that feeds the voice (ElevenLabs, /speak) and the
adapter (tools/face_lora.py). Streams the corpus universe once; never builds the corpus.

    PYTHONPATH=src python tools/face_responses.py                 # on the box: writes data/faces/responses/*.jsonl
    N_PER_FACE=150 PYTHONPATH=src python tools/face_responses.py   # a different cap
    NH_ROOT=/home/nh/concordance-2 PYTHONPATH=/tmp/nhsrc python3 /tmp/face_responses.py   # a shipped copy

Measured 2026-10-31 (933,479 cards, 194,583 on a saying shelf): 16 of 18 faces fill 200 lines; the Nutritionist,
Steward and Counsel have NO saying source in the keeping (a food database, Napoleon's orders, two law cards) — a WANT
for PD sources (USDA Dietary Guidelines; Franklin's Way to Wealth; Blackstone), not a reason to lower the bar.
"""
from __future__ import annotations

import collections
import glob
import heapq
import json
import os
import re
import sys
from pathlib import Path

_ROOT_ENV = os.environ.get("NH_ROOT", "").strip()
ROOT = Path(_ROOT_ENV) if _ROOT_ENV else Path(__file__).resolve().parent.parent
if _ROOT_ENV:
    sys.path.append(str(ROOT / "src"))
else:
    sys.path.insert(0, str(ROOT / "src"))

N = int(os.environ.get("N_PER_FACE", "200"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
OUT = DATA / "faces" / "responses"
TIERS = {"reference", "primary_pd", "primary", "scripture", "father", "catechism", "creed", "verified", "operator",
         "external_aligned"}

# the saying sources per face — shelves whose sentences are SAID, not drilled (2 = the face's own voice shelf)
SOURCES = {
    "face_shepherd":      {"scripture": 2, "sermons": 2, "patristics": 2, "topical": 1, "hymns": 1, "fieldkit": 2, "churches": 1, "codex": 1},
    "face_scholar":       {"lexicon": 2, "greek_nt": 1, "hebrew_ot": 1, "encyclopedia": 2, "commentary": 1, "scripture": 1},
    "face_bard":          {"curriculum": 2, "scripture": 2, "classics": 1, "almanac": 2, "topical": 1, "foreshadows": 1},
    "face_coach":         {"strategy": 2, "playbook": 2, "classics": 1, "curriculum": 1, "the-works": 1},
    "face_steward":       {"strategy": 2, "topical": 1, "scripture": 1, "economics": 1, "finance": 1, "almanac": 1},
    "face_counselor":     {"classics": 2, "scripture": 2, "sermons": 1, "patristics": 1, "topical": 1, "psychology": 1},
    "face_physician":     {"first_aid": 2, "apothecary": 2, "sanitation": 2, "medicine": 1, "regulation": 1},
    "face_nutrition":     {"nutrition": 2, "food": 2, "foods": 2, "recipes": 2, "apothecary": 1, "agriculture": 1},
    "face_social_worker": {"survival": 2, "first_aid": 2, "water": 2, "sanitation": 2, "communications": 2, "power": 2, "energy": 1,
                           "food": 2, "access": 2, "navigation": 2, "practical": 1},
    "face_engineer":      {"systems": 2, "forms": 2, "theories": 1, "trades": 1, "electrical": 1, "tools": 1, "bridges": 1},
    "face_builder":       {"trades": 2, "maker": 2, "survival": 1, "construction": 2, "architecture": 1, "practical": 1},
    "face_gardener":      {"food": 2, "agriculture": 2, "soil_science": 2, "almanac": 2, "survival": 1, "theories": 1},
    "face_planner":       {"strategy": 2, "playbook": 2, "operations_research": 1, "calendar_time": 1, "timekeeping": 1, "logistics": 2, "navigation": 1},
    "face_artisan":       {"hymns": 2, "music_theory": 2, "photography": 2, "trades": 1, "animation": 1, "acoustics": 1},
    "face_counsel":       {"law": 2, "regulation": 2, "document_validation": 1, "governance": 1, "scripture": 1},
    "face_professor":     {"theories": 2, "history": 1, "history_chronology": 1, "classics": 1, "philosophy": 1, "reference": 1},
    "face_tutor":         {"theories": 1, "forms": 2, "calculations": 2, "mathematics": 1, "physics": 1, "curriculum": 1},
    "face_theorist":      {"theories": 2, "forms": 2, "bridges": 2, "millennium": 2, "the-works": 2, "calculations": 1, "mathematics": 1, "physics": 1},
}
STOP = set("""the a an and or of to in on for with by from as at is are was were be been it its this that these those
you your we our they their he she his her i my me not no but if then than so such into out up down over under about
which who whom what when where why how all any each every some more most other own same too very can will just also
there here one two it's don't doesn't never only ever both either neither while until because before after again
further once does did do done have has had having being am""".split())
_WORD = re.compile(r"[a-z][a-z'-]+")
_SENT = re.compile(r"(?<=[.!?;])\s+(?=[A-Z“\"'])")
_BAD = re.compile(r"[\[\]{}<>|=_/\\@#$%^*]|https?:|www\.|\d{3,}|[Ͱ-Ͽ֐-׿]|\bLO\s?\d|\bStep \d|\(\d\.\)|\betc\b|\bi\.e\b|\be\.g\b")
_DRILL = re.compile(r"^(Identify|Explain|Describe|Calculate|Compute|Determine|Which of|Chapter|Figure|Table|Summary|Review|Exercise|Problem|Section|Define|List|Compare|Discuss|Create|Draw|Solve|Find the|Show that|Prove|Write a|Use the|Consider the)\b")
_GLOSS = re.compile(r"^[A-Z][\w' ]{0,40} - ")                          # commentary glosses: "Word - explanation"
_BOILER = re.compile(r"engine domain that can touch it|Calibration:|A worked check in|shelf of the keeping|FoodData Central|"
                     r"— a food in|Chapter [ivx]+|SEALS:|map-only|verifier|the keeping\b")
_TAIL = re.compile(r"(\s[—-]\s[A-Z][A-Za-z.&' ]{0,30}|\s\d{1,2}\.)$")      # "… — U.S." attribution stubs, list numbers
LEAD = {"you", "your", "we", "let", "do", "keep", "take", "give", "ask", "seek", "remember", "consider", "first", "when",
        "if", "never", "always", "learn", "know", "hold", "build", "plant", "store", "boil", "stop", "check", "make", "be",
        "trust", "pray", "go", "come", "look", "listen", "wait", "start", "begin", "measure", "count", "read", "there"}


def words(s: str):
    return [w for w in _WORD.findall(s.lower()) if w not in STOP and len(w) > 2]


def clean(s: str) -> str:
    prev = None
    while prev != s:
        prev, s = s, _TAIL.sub("", s).strip()
    return s


def keep(s: str) -> bool:
    """The hard filters: a saying, not a drill, a gloss, a catalog row or the engine talking about itself."""
    if not (30 <= len(s) <= 140) or s[-1] not in ".!" or not s[0].isupper():
        return False
    if "?" in s or _BAD.search(s) or _DRILL.match(s) or _GLOSS.match(s) or _BOILER.search(s):
        return False
    return sum(ch.isdigit() for ch in s) <= len(s) * 0.05 and sum(ch.isupper() for ch in s) <= len(s) * 0.3


def fit(sentence: str, manner, scope, weight: float) -> float:
    """An aphorism in this face's manner: lead (imperative / second person), brevity, manner + scope vocabulary."""
    ws = words(sentence)
    if len(ws) < 3:
        return 0.0
    m = min(3.0, sum(1.0 for w in ws if w in manner))
    sc = min(2.0, sum(1.0 for w in ws if w in scope))
    lead = sentence.split(" ", 1)[0].lower().strip("“\"'")
    aph = (2.0 if lead in LEAD else 0.0) + (1.0 if re.search(r"\byou\b|\byour\b", sentence.lower()) else 0.0)
    short = 1.0 if len(sentence) <= 110 else 0.0
    return weight * (1.0 + aph + short + m + sc) / (1.0 + max(0, sentence.count(",") - 2) * 0.5)


def universe():
    src = (ROOT / "src" / "concordance" / "corpus.py").read_text(encoding="utf-8")
    extra = re.search(r"EXTRA_CARD_SOURCES = \((.*?)\n\)", src, re.S).group(1)
    return {str(DATA / "cards.jsonl"), str(DATA / "prophecy" / "signposts.jsonl")} | {str(DATA / m) for m in re.findall(r'"([^"]+\.jsonl)"', extra)}


def main() -> int:
    from concordance import faces
    profiles = {}
    for fid, f in faces._FACES.items():
        manner = collections.Counter(words(f.get("manner", "")))
        scope = set()
        for s in f["scope"]:
            scope.update(words(s))
        profiles[fid] = {"manner": manner, "scope": scope, "sources": SOURCES.get(fid, {}), "heap": [], "seen": set()}
    by_shelf = {}
    for fid, p in profiles.items():
        for s in p["sources"]:
            by_shelf.setdefault(s, []).append(fid)
    uni = universe()
    seen = used = 0
    for path in sorted(glob.glob(str(DATA / "**" / "*.jsonl"), recursive=True)):
        if path not in uni:
            continue
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    c = json.loads(ln)
                except Exception:
                    continue
                if not isinstance(c, dict) or "id" not in c:
                    continue
                seen += 1
                shelf = str(c.get("shelf") or "").lower()
                targets = by_shelf.get(shelf)
                if not targets:
                    continue
                src = c.get("source") if isinstance(c.get("source"), dict) else {}
                if str(src.get("authority_tier") or "").lower() not in TIERS:
                    continue
                body = c.get("body")
                if not isinstance(body, str) or len(body) < 40 or len(body) > 40000:
                    continue
                used += 1
                sents = [clean(s.strip()) for s in _SENT.split(" ".join(body.split()))]
                sents = [s for s in sents if keep(s)]
                for fid in targets:
                    p = profiles[fid]
                    w = p["sources"][shelf]
                    for s in sents:
                        key = s.lower()
                        if key in p["seen"]:
                            continue
                        item = (fit(s, p["manner"], p["scope"], w), s, c["id"], shelf, str(src.get("authority_tier")))
                        if len(p["heap"]) < N:
                            heapq.heappush(p["heap"], item)
                            p["seen"].add(key)
                        elif item[0] > p["heap"][0][0]:
                            heapq.heapreplace(p["heap"], item)
                            p["seen"].add(key)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"cards streamed {seen}  cards on a saying shelf (PD/primary) {used}")
    for fid in sorted(profiles):
        rows = sorted(profiles[fid]["heap"], reverse=True)
        with open(OUT / f"{fid}.jsonl", "w", encoding="utf-8") as out:
            for score, s, cid, shelf, tier in rows:
                out.write(json.dumps({"face": fid, "text": s, "card": cid, "shelf": shelf, "tier": tier,
                                      "fit": round(score, 3), "kind": "found"}, ensure_ascii=False) + "\n")
        print(f"{fid:<20} found {len(rows):>3}  shelves {dict(collections.Counter(r[3] for r in rows).most_common(4))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
