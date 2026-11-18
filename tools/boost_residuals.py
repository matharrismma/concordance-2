#!/usr/bin/env python3
"""WHAT EACH RANKING CONSTANT IS WORTH, AND WHAT IT OVERRULES — read this before changing one.

The ranker combines signals with constants chosen by judgment: 9.0 for an exact title, 4.0 for the
theories shelf, 3.0 for the survival field library, 4.0 for full-phrase title coverage, 2.0 for
substance, and 1000.0 for the subject partition. On 2026-11-17 one of them had silently become the
entire ranking: `_finalize` multiplied a score that already contained SUBJECT_TIER, so a theories
card scored (base + 1000) x 4 while a card plainly about the subject scored ~1000, and 26 of 68 real
questions were led by a theories card whose term frequency of the subject was one or two. Nobody had
measured what the constant was worth against the thing it multiplied. This tool is so that nobody
has to find that out by reading sixty-eight answers again.

THE MEASURE NEEDS NO LABELS, which is what makes it affordable to run. Stand one boost down, see
whether the top hit changes, and when it does compare the BASE scores — the engine's own TF-IDF
relevance, before any boost and before the tier — of the card the boost PROMOTED against the card it
DEMOTED:

    override ratio = base(promoted) / base(demoted)

    >= 1.0   the boost CONFIRMS the evidence: it promoted a card that was already more relevant
     < 1.0   the boost OVERRIDES the evidence
    << 1.0   the boost asserts against measurement — the shape of the 2026-11-17 defect
             (theories: 26 of 68 top hits, median ratio 0.137, worst 0.048, overrode 26 of 26)

That ratio is the innovation of a Kalman filter written for a ranker: the disagreement between the
model (relevance) and the correction (the constant). A healthy boost breaks near-ties. A pathological
one overturns a landslide.

A LOW RATIO FLAGS RISK, NOT ERROR, and the report must not be read as a verdict. Measured the same
day, of the four theories cases that survived the fix, "why does the inverse square law hold"
promotes *Newton's law of universal gravitation* over "1.4 Inverse Functions" at ratio 0.380 — the
boost doing exactly what it was asked for — while "show me the original Greek word, with cross
references" promotes *Projective geometry (perspective & the cross-ratio)* at 0.300, matching on the
token "cross". The ratio cannot tell those apart. What it does is turn "is this constant healthy?"
from an unanswerable question into a number and a list a reader checks in a minute.

AND A ZERO IS UNINTERPRETABLE WITHOUT ITS DENOMINATOR, so the report always prints the fire counts
beside the changes. The exact-title boost — the LARGEST multiplier in the ranker — changed the top
hit on 0 of 68 questions, which says nothing whatever about it: it fired on ONE scoring candidate out
of 76,010, because its case (a verse or named-work lookup, "Philippians 4:13") is almost absent from
these batteries. That constant is UNMEASURED, not inert, and it needs a verse-lookup battery before
anyone touches it. Reading that zero as "it does nothing" would be the same error as reading a
movement count as an accuracy.

THIS TOOL REPORTS AND NEVER FITS. It does not tune, does not suggest a value, and writes nothing to
the keeping. Fitting 9.0 to sixty-eight questions would make the ranker a small statistical model,
which is the opposite of mapping a found structure — the constants stay chosen, and this only makes
the choosing accountable.

HOW IT STAYS HONEST. search()'s `_finalize` is a closure and cannot be called from outside, so the
boost arithmetic is written out again here — which is a drift hazard, not a convenience. So the tool
PROVES ITSELF BEFORE IT REPORTS: the mirror must reproduce `Corpus.search`'s served order on every
question, or the run REFUSES and reports nothing. If you change `_finalize` and not this file, this
file stops working rather than quietly measuring the wrong engine. `--old` deliberately restores the
pre-2026-11-17 arithmetic to show what the report catches, and cannot be validated that way; it says
so in its own output.

Usage:
    python tools/boost_residuals.py [--data DIR] [--out FILE] [--limit N] [--old]

  --data   the keeping's data directory (default: the CONCORDANCE_DATA_DIR already set, or ./data)
  --out    write the full report here as well as to stdout
  --limit  use only the first N questions (a smoke run; the full set is ~68 and takes minutes)
  --old    restore the pre-fix arithmetic (boosts multiply the tier sum). Self-validation is skipped.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# The boosts this tool can stand down. `substance` is read by `_score` as a module global and so can
# be stood down without touching the engine; the 1.5 all-tokens bonus is a LITERAL inside `_score`
# and cannot be reached from here. It is named in the report so its absence is not mistaken for a
# clean bill of health.
BOOSTS: Tuple[str, ...] = ("exact_title", "survival", "theories", "phrase", "substance", "tier")
NOT_MEASURED: Tuple[str, ...] = (
    "the 1.5x all-tokens bonus — a literal inside _score, not reachable from a probe",
    "stigmergy / repellent / alignment — gated off by default, so they are 1.0 here",
)


# ── the questions: the repository's own tracked batteries, never a scratch file ──────────────
def _clean(text) -> str:
    if not isinstance(text, str):
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    if not (8 <= len(t) <= 300):
        return ""
    if t[0] in "{[" or '":' in t or "':" in t:      # a stringified mapping, not a question
        return ""
    return t


def questions(eval_dir: Path) -> List[str]:
    """Real questions from the three tracked batteries that actually hold them, each by its own
    shape. `frontdoor_claims.json` and `recall_phrasings.json` hold CLAIMS, not questions, and the
    remaining probes carry no question text — they are keyed by id for /chains, /stick and /verify."""
    out: List[str] = []
    seen = set()

    def add(text) -> None:
        t = _clean(text)
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)

    p = eval_dir / "face_routes.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")).get("routes", []):
            add(r.get("text"))
    p = eval_dir / "live_probes.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("path") == "/ask" and isinstance(r.get("body"), dict):
                add(r["body"].get("text"))
    p = eval_dir / "coherent_model" / "answer.py"
    if p.exists():
        block = p.read_text(encoding="utf-8").split("STRESS = [", 1)[-1].split("\n]", 1)[0]
        for m in re.finditer(r'\(\s*"([^"]+)"\s*,', block):
            add(m.group(1))
    return out


# ── the mirror of search()'s ranking, which proves itself against the engine ─────────────────
def rank(corpus, query: str, limit: int = 5, *, off: str = "", old: bool = False) -> List[tuple]:
    """(final, base, card) ranked as `Corpus.search` ranks, with one boost optionally stood down.

    Everything but the boost arithmetic is the engine's own: `_score`, `_candidates`, `_idf`,
    `_with_variants`, `subject_family`, `is_public` and the frozen-shard merge."""
    from concordance import corpus as C
    from concordance import corpus_db as CDB
    from concordance import growth as _growth

    tier = C.SUBJECT_TIER
    query = str(query) if query else ""
    asked = {t for t in C._tokens(query) if t not in CDB._STOP}
    query_tokens = corpus._with_variants(asked)
    if not query_tokens:
        return []
    seat = corpus._subject_of(asked, corpus._idf(asked)) if asked else None
    idf = corpus._idf(query_tokens)
    fam = corpus.subject_family(seat) if seat else set()
    qn = " ".join(query.lower().split())
    q_exact = {qn} | {r.lower() for r in _growth.refs_in_text(query or "")}

    def boosts(card: dict, s: float) -> float:
        title_n = " ".join(str(card.get("title", "")).lower().split())
        ref_n = " ".join(str((card.get("source") or {}).get("ref", "")).lower().split())
        pron = card.get("shelf") == "pronunciation"
        if not pron and off != "exact_title":
            if title_n in q_exact or (ref_n and ref_n in q_exact and title_n in q_exact):
                s *= 9.0
            elif q_exact and (title_n in q_exact or ref_n in q_exact):
                s *= 4.0
        if card.get("shelf") == "survival" and (C._PRACTICAL & query_tokens):
            if off != "survival":
                s *= 3.0
        elif card.get("shelf") == "theories" and off != "theories":
            s *= C.THEORY_WEIGHT
        if len(asked) >= 2 and not pron and off != "phrase":
            hay = set(C._tokens(str(card.get("title", "")) + " "
                                + " ".join(card.get("bands") or [])))
            if hay and asked <= hay:
                s *= 4.0
        return s

    def scored_of(card: dict) -> Optional[tuple]:
        s_full = corpus._score(card, query_tokens, idf, subject=seat)
        if s_full <= 0:
            return None
        base = s_full - (tier if s_full >= tier else 0.0)
        in_tier = s_full >= tier and off != "tier"
        if old:                                   # the pre-2026-11-17 arithmetic: boosts over the sum
            return (boosts(card, base + (tier if in_tier else 0.0)), base, card)
        return (boosts(card, base) + (tier if in_tier else 0.0), base, card)

    scored = []
    for cid in corpus._candidates(query_tokens, seat_family=(fam or None)):
        card = corpus.cards.get(cid)
        if card and C.is_public(card):
            r = scored_of(card)
            if r:
                scored.append(r)
    frozen = C.frozen_shelves() if corpus._froze else frozenset()
    if frozen:
        CDB.thaw_for(*frozen)
        have = {card.get("id") for _f, _b, card in scored}
        for hit in CDB.search(query, limit=max(int(limit) * 3, 60), include_witness=True):
            if hit.get("shelf") not in frozen or hit.get("id") in have or not C.is_public(hit):
                continue
            r = scored_of(hit)
            if r:
                scored.append(r)
                have.add(hit.get("id"))
    scored.sort(key=lambda x: (-x[0], str(x[2].get("id") or "")))
    if scored and scored[0][0] >= tier:
        scored = [x for x in scored if x[0] >= tier]
    return scored[:max(1, int(limit))]


def validate(corpus, qs: List[str], limit: int = 5) -> List[str]:
    """The questions on which the mirror does NOT reproduce the engine's served order. Must be empty
    — otherwise `_finalize` has changed and this file is measuring an engine that no longer exists."""
    bad = []
    for q in qs:
        corpus._search_cache.clear()
        served = [h.get("id") for h in corpus.search(q, limit=limit)]
        mine = [card.get("id") for _f, _b, card in rank(corpus, q, limit)]
        if served != mine:
            bad.append(q)
    return bad


# ── the two measurements ─────────────────────────────────────────────────────────────────────
def fire_counts(corpus, qs: List[str]) -> Tuple[Counter, Counter, int]:
    """(questions where each boost fired, candidates it fired on, total scoring candidates)."""
    from concordance import corpus as C
    from concordance import corpus_db as CDB
    from concordance import growth as _growth

    per_q, per_card, total = Counter(), Counter(), 0
    for q in qs:
        asked = {t for t in C._tokens(q) if t not in CDB._STOP}
        query_tokens = corpus._with_variants(asked)
        if not query_tokens:
            continue
        seat = corpus._subject_of(asked, corpus._idf(asked)) if asked else None
        idf = corpus._idf(query_tokens)
        fam = corpus.subject_family(seat) if seat else set()
        qn = " ".join(q.lower().split())
        q_exact = {qn} | {r.lower() for r in _growth.refs_in_text(q or "")}
        seen = Counter()
        for cid in corpus._candidates(query_tokens, seat_family=(fam or None)):
            card = corpus.cards.get(cid)
            if not card or not C.is_public(card):
                continue
            s = corpus._score(card, query_tokens, idf, subject=seat)
            if s <= 0:
                continue
            total += 1
            title_n = " ".join(str(card.get("title", "")).lower().split())
            ref_n = " ".join(str((card.get("source") or {}).get("ref", "")).lower().split())
            pron = card.get("shelf") == "pronunciation"
            if not pron and q_exact and (title_n in q_exact or ref_n in q_exact):
                seen["exact_title"] += 1
            if card.get("shelf") == "survival" and (C._PRACTICAL & query_tokens):
                seen["survival"] += 1
            elif card.get("shelf") == "theories":
                seen["theories"] += 1
            if len(asked) >= 2 and not pron:
                hay = set(C._tokens(str(card.get("title", "")) + " "
                                    + " ".join(card.get("bands") or [])))
                if hay and asked <= hay:
                    seen["phrase"] += 1
            if len(str(card.get("body") or "")) >= C.STUB_BODY_CHARS:
                seen["substance"] += 1
            if s >= C.SUBJECT_TIER:
                seen["tier"] += 1
        for k, v in seen.items():
            per_q[k] += 1
            per_card[k] += v
    return per_q, per_card, total


def residuals(corpus, qs: List[str], *, old: bool = False, progress=None) -> Dict[str, List[dict]]:
    """Per boost, every question where standing it down changes the top hit, with the override ratio."""
    from concordance import corpus as C

    out: Dict[str, List[dict]] = {b: [] for b in BOOSTS}
    for q in qs:
        full = rank(corpus, q, 5, old=old)
        if not full:
            continue
        top = full[0]
        for b in BOOSTS:
            prev = C.SUBSTANCE_WEIGHT
            if b == "substance":
                C.SUBSTANCE_WEIGHT = 1.0
            try:
                without = rank(corpus, q, 5, off=b, old=old)
            finally:
                C.SUBSTANCE_WEIGHT = prev
            if not without or without[0][2].get("id") == top[2].get("id"):
                continue
            base_p, base_d = top[1], without[0][1]
            out[b].append({
                "q": q,
                "ratio": (base_p / base_d) if base_d > 0 else float("inf"),
                "base_p": round(base_p, 3), "base_d": round(base_d, 3),
                "promoted": f"[{top[2].get('shelf')}] {str(top[2].get('title', ''))[:58]}",
                "demoted": f"[{without[0][2].get('shelf')}] "
                           f"{str(without[0][2].get('title', ''))[:58]}",
                "same_tier": (top[0] >= C.SUBJECT_TIER) == (without[0][0] >= C.SUBJECT_TIER)})
        if progress:
            progress(q)
    return out


def report(qs: List[str], res: Dict[str, List[dict]], per_q: Counter, per_card: Counter,
           total: int, *, old: bool, validated: bool, worst: int = 6) -> str:
    L = [f"PER-BOOST RESIDUAL REPORT · {len(qs)} questions · {total:,} scoring candidates · "
         f"arithmetic = {'OLD (pre-2026-11-17)' if old else 'CURRENT'}",
         ("mirror validated against Corpus.search on every question"
          if validated else
          "MIRROR NOT VALIDATED — --old restores an arithmetic the engine no longer uses, so the "
          "order cannot be checked against it. Read this arm only as a demonstration of the report."),
         "",
         "override ratio = base(card the boost promoted) / base(card it demoted); base is the engine's",
         "own TF-IDF score before any boost and before the subject tier.",
         "  >= 1.0 CONFIRMS the evidence    < 1.0 OVERRIDES it    << 1.0 asserts against measurement",
         "A low ratio flags RISK, not error. A zero change-count with a low fire count means the",
         "constant is UNMEASURED by these questions, not that it does nothing.",
         ""]
    L.append(f"{'boost':<13}{'top changed':>13}{'median':>9}{'worst':>8}{'overrode':>10}"
             f"{'fired (questions)':>20}{'fired (candidates)':>21}")
    for b in BOOSTS:
        ch = res.get(b) or []
        if ch:
            rs = sorted(x["ratio"] for x in ch)
            L.append(f"{b:<13}{f'{len(ch)}/{len(qs)}':>13}{statistics.median(rs):>9.3f}"
                     f"{rs[0]:>8.3f}{sum(1 for x in ch if x['ratio'] < 1.0):>10}"
                     f"{f'{per_q[b]}/{len(qs)}':>20}{per_card[b]:>21,}")
        else:
            L.append(f"{b:<13}{f'0/{len(qs)}':>13}{'-':>9}{'-':>8}{'-':>10}"
                     f"{f'{per_q[b]}/{len(qs)}':>20}{per_card[b]:>21,}")
    for b in BOOSTS:
        ch = res.get(b) or []
        if not ch:
            continue
        L += ["", "=" * 108,
              f"{b}: the {min(worst, len(ch))} largest overrides"]
        for x in sorted(ch, key=lambda y: y["ratio"])[:worst]:
            L.append(f"   ratio {x['ratio']:.3f}  (base {x['base_p']} vs {x['base_d']})"
                     f"{'' if x['same_tier'] else '   [tier differs]'}")
            L.append(f"      Q: {x['q'][:92]}")
            L.append(f"      promoted: {x['promoted']}")
            L.append(f"      demoted : {x['demoted']}")
    L += ["", "=" * 108, "NOT MEASURED by this report:"]
    L += [f"  - {s}" for s in NOT_MEASURED]
    return "\n".join(L)


def main(argv: List[str]) -> int:
    args = list(argv)
    old = "--old" in args
    data = None
    out_path = None
    limit = 0
    for flag, cast in (("--data", str), ("--out", str), ("--limit", int)):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                print(f"{flag} needs a value")
                return 2
            val = cast(args[i + 1])
            if flag == "--data":
                data = val
            elif flag == "--out":
                out_path = val
            else:
                limit = val
    root = Path(__file__).resolve().parent.parent
    if data:
        os.environ["CONCORDANCE_DATA_DIR"] = str(Path(data).resolve())
    os.environ.setdefault("CONCORDANCE_MEMO", "0")      # a report never writes a memo
    sys.path.insert(0, str(root / "src"))
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                    # noqa: BLE001 — a plain pipe is fine
        pass

    from concordance import corpus as C
    data_dir = Path(os.environ.get("CONCORDANCE_DATA_DIR") or (root / "data"))
    qs = questions(data_dir.parent / "eval")
    if not qs:
        qs = questions(root / "eval")
    if not qs:
        print(f"no questions found — looked in {data_dir.parent / 'eval'} and {root / 'eval'}")
        return 2
    if limit:
        qs = qs[:limit]

    n_before = C.card_count()
    corpus = C.default_corpus()
    print(f"{n_before:,} cards · {len(qs)} questions · "
          f"arithmetic={'OLD' if old else 'CURRENT'}", flush=True)

    validated = False
    if not old:
        bad = validate(corpus, qs)
        print(f"MIRROR CHECK: {len(qs) - len(bad)}/{len(qs)} reproduce the engine's served order",
              flush=True)
        if bad:
            for q in bad[:4]:
                print("  MISMATCH:", q)
            print("REFUSING TO REPORT: search()'s _finalize and this file have drifted apart. "
                  "Bring the `boosts` mirror back into step before trusting any number here.")
            return 1
        validated = True

    res = residuals(corpus, qs, old=old, progress=lambda q: print(f"· {q[:72]}", flush=True))
    per_q, per_card, total = fire_counts(corpus, qs)
    text = report(qs, res, per_q, per_card, total, old=old, validated=validated)
    print("\n" + text)
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"\nwrote {p}")
    # a report may not change the keeping, and says so by checking
    if C.card_count() != n_before:
        print(f"REPORT CHANGED THE KEEPING ({n_before:,} -> {C.card_count():,}) — this is a defect")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
