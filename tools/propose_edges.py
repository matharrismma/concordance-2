#!/usr/bin/env python3
"""PROPOSE — find the connections nobody has written yet, and show the evidence for each.

    PYTHONPATH=src python tools/propose_edges.py                 # the ranked proposals
    PYTHONPATH=src python tools/propose_edges.py --min 2.0 --n 40

Matt, 2026-08-02: *"Look for the obvious connections. I was adding these by hand. We never had a
tool to help me find them."*

That is the whole gap. The floor's 104 edges were WRITTEN — by him, then by me — which means the
next hundred need a person again, and a library that grows by one author's recall grows at the
speed of that recall and stops at its edge. A concordance should be able to say *these two things
are talking about the same thing, and here is why I think so.*

IT PROPOSES; IT NEVER WRITES. Every candidate is printed with the evidence that raised it, and a
human (or a verifier) disposes. This is the standing rule of the house — intuition proposes, the
assay disposes — and it is load-bearing here because the failure mode of an automatic edge-miner
is exactly the failure this project fights: a plausible-looking link with nothing behind it. The
53 false `cites` edges that had to be cleaned out were of that kind. An edge that does not carry
a real relation is worse than an absent one, because it makes the map lie.

THE FIRST VERSION MINED THE THEORY CARDS AND FOUND ONLY ITS OWN TEMPLATE. Every proposal it
ranked highest shared the words "theology, interpretive, signpost, foundational" — the assay's
CLASSIFICATION BOILERPLATE, which every card carries — and its "wave equation" marker was firing
on the word "resonance" from our own verdict scale. Reading an actual card body (which should
have come first) settled it: these cards are LABELS, not knowledge. Body text is
"Cell theory — an engine domain that can touch it: biology. Calibration: map-only…". There is no
content in them to connect, so no amount of cleverness over them could ever have worked. An
instrument that mistakes its own template for a finding accuses the thing it measures.

SO THE TOOL ASKS THE LIBRARY INSTEAD. The keeping holds ~551,000 cards of real books,
encyclopedia entries and commentary — people who wrote about these theories, often two at a time
because they saw the connection. That is the honest signal, and it is somebody else's judgement
rather than my own vocabulary trick:

  co-retrieval   for each theory, ask the keeping for it (the project's own ranker, subject
                 partition and all) and keep the cards that come back. Two theories that pull the
                 SAME sources are being discussed together by real authors.
  the witnesses  every proposal prints the shared source cards BY TITLE. That is the evidence, and
                 it is checkable: open the book and see whether it really treats both.
  the shape      a small set of form markers read from the TITLES only (never the boilerplate) —
                 exponential decay, wave, conservation, entropy, eigenvalue, equilibrium — which
                 flag a candidate for `same_form`, the relation this house holds highest.

It PROPOSES; it never writes. The 53 false `cites` edges that had to be cleaned out are why: an
edge that does not carry a real relation is worse than an absent one, because it makes the map lie.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

_WORD = re.compile(r"[a-z][a-z'-]{3,}")

# Words that carry no discriminating power on a shelf of scientific theories. Deliberately short:
# the IDF over the shelf does most of the work, and a long hand list is a place for bias to hide.
_STOP = frozenset("""the and for that with this from are was were will been being have has had
theory theories law laws principle model system systems science field study states state
which what when where while than then them they their there these those over under about into
each other others such only also more most much many some very both between within without
across through during before after above below same different first second third
calibrated judged assay engine domain card cards keeping shelf source""".split())

# THE FORM MARKERS. Each is a mathematical SHAPE, not a topic — two theories carrying the same
# marker are doing the same arithmetic in different clothes, which is precisely what `same_form`
# is for. Kept small and specific; a marker that matches everything finds nothing.
_FORMS = {
    "exponential decay": (r"\bhalf-?life|\bexponential (?:decay|growth)|\be\^?\(-|\bdecay constant"
                          r"|\bdiscount(?:ing|ed)?\b"),
    "inverse square": r"\binverse[- ]square|\b1/r\^?2|\bfalls? off (?:as|with) (?:the )?square",
    "wave equation": r"\bwave (?:equation|length)|\bharmonic|\bfrequenc|\bresonan|\bdiffract|\bstanding wave",
    "conservation": r"\bconserv|\bbalance[sd]?\b|\binvariant|\bcannot be (?:created|destroyed)",
    "equilibrium": r"\bequilibri|\bsteady[- ]state|\ble chatelier|\bshifts? to oppose",
    "entropy / log": r"\bentropy|\blogarithm|\blog\b|\bbits? of\b|\bdisorder",
    "eigenvalue": r"\beigen|\bcharacteristic (?:polynomial|equation)|\bspectrum|\bmode[s]?\b",
    "integer ratio": r"\binteger ratio|\bsmall[- ]integer|\bwhole[- ]number ratio|\b2:1\b|\b3:2\b",
    "rate equation": r"\brate (?:equation|constant|law)|\bfirst[- ]order|\bkinetics|\bper unit time",
    "probability": r"\bprobabilit|\bdistribution|\bvariance|\bexpected value|\brandom",
    "optimization": r"\boptimi|\bmaximi|\bminimi|\bdual(?:ity)?\b|\bconstraint",
    "geometry / packing": r"\btiling|\bpacking|\blattice|\bsymmetr|\bpolygon|\bangle",
}


def _anchor(title: str) -> str:
    """The words to ask the library with — the theory's name, minus the parenthetical gloss.

    "Shannon information theory (entropy, channel capacity)" -> "Shannon information theory".
    The gloss is our own editorial addition; the name is what an author would have written.
    """
    t = re.split(r"[(\[]", str(title or ""))[0]
    t = t.replace("&", " ").replace("/", " ")
    return " ".join(t.split())[:60]


# The words a theory's name shares with a hundred other names. A subject seat landing on one of
# these is a name collision waiting to happen -- "Central limit theorem" and "Fundamental theorem
# of algebra" both took the seat "theorem", because in a keeping of Gutenberg books, geography and
# taxonomy, "theorem" is rarer than "central" or "algebra". Global rarity is domain-blind; on a
# shelf of scientific names these words are the LEAST identifying, whatever the corpus thinks.
_GENERIC_NAME_WORDS = frozenset("""theorem theory law laws principle model equation identity
axioms axiom thesis hypothesis effect rule relation formula method""".split())

_PROPER = re.compile(r"([A-Z][a-z]{2,})")


def _identifying(title: str) -> str:
    """The words that actually name this theory, INCLUDING the parenthetical.

    "Law of conservation of mass (Lavoisier)" -> "conservation mass Lavoisier". The person's name
    is the most identifying token a scientific title carries -- it survives translation and
    paraphrase, and a book naming two of them together is real evidence.

    A CAPITALIZATION HEURISTIC WAS TRIED FIRST AND SILENTLY DROPPED EXACTLY THOSE NAMES: every
    title is Title Case, so the leading word ("Central", "Modern", "Cell") always looked proper,
    and the real names in parentheses never won. Rather than debug a rule whose failure mode is
    invisible, this keeps EVERY word that is not structural -- no cleverness to misfire, and the
    ranker weights the rare name highly on its own, which was the whole point.
    """
    raw = str(title or "").replace("&", " ").replace("/", " ")
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", raw)
             if w.lower() not in _GENERIC_NAME_WORDS and len(w) > 3]
    return " ".join(dict.fromkeys(words))[:70] if words else _anchor(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(ROOT, "data", "theory_cards.jsonl"))
    ap.add_argument("--n", type=int, default=25, help="how many proposals to show")
    ap.add_argument("--min", type=float, default=2.0, help="score floor")
    ap.add_argument("--depth", type=int, default=25, help="sources retrieved per theory")
    args = ap.parse_args()

    from concordance import corpus

    th = {}
    for line in open(args.path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            c = json.loads(line)
        except ValueError:
            continue
        if c.get("shelf") == "theories":
            th[c["id"]] = c

    joined = set()
    for cid, c in th.items():
        for e in (c.get("connections") or []):
            if e.get("relationship") in ("rests_on", "limits", "same_form"):
                joined.add(frozenset((cid, str(e.get("to_card_id")))))

    # ASK THE LIBRARY FOR EACH THEORY. The witnesses are whatever the keeping returns — books,
    # encyclopedia entries, commentary — retrieved by the project's own ranker so a proposal
    # inherits the same subject partition every reader gets.
    theory_ids = set(th)
    sources, titles, subjects = {}, {}, {}
    for cid, c in th.items():
        q = _identifying(c.get("title"))
        try:
            hits = corpus.search(q, limit=args.depth) or []
        except Exception:  # noqa: BLE001
            hits = []
        # A WITNESS MUST CARRY THE SUBJECT, not merely a word from the title. The first run
        # ranked "Central limit theorem" beside "Fundamental theorem of algebra" because their
        # witnesses all contained the word THEOREM — the shared-generic-word artifact one level
        # up from the boilerplate that killed version one. The subject seat (the globally rarest
        # token of the name, the same machinery every reader's search uses) is the filter: a card
        # about Lavoisier must actually say Lavoisier.
        try:
            subj = corpus.subject_of(q)
        except Exception:  # noqa: BLE001
            subj = None
        fam = corpus.Corpus.subject_family(subj) if subj else set()
        subjects[cid] = subj
        keep = {}
        for h in hits:
            hid = str(h.get("id") or "")
            if not hid or hid in theory_ids:       # a theory card is not a witness to itself
                continue
            if fam:
                text = (str(h.get("title") or "") + " " + str(h.get("snippet") or "")
                        + " " + str(h.get("body") or "")).lower()
                if not any(w in text for w in fam):
                    continue
            keep[hid] = str(h.get("title") or "")[:58]
        sources[cid] = keep
        titles[cid] = q

    # a source cited by half the shelf witnesses nothing in particular — weight by rarity
    src_df = defaultdict(int)
    for keep in sources.values():
        for hid in keep:
            src_df[hid] += 1
    n = max(1, len(th))

    forms = {}
    for cid, c in th.items():
        # TITLES ONLY. The bodies are assay boilerplate; reading them is what made the first
        # version match "resonance" from our own verdict scale.
        text = (str(c.get("title") or "") + " " + " ".join(c.get("bands") or [])).lower()
        forms[cid] = {name for name, pat in _FORMS.items() if re.search(pat, text)}

    ids = sorted(th)
    proposals = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if frozenset((a, b)) in joined:
                continue
            # A NAME COLLISION IS NOT A CONNECTION. "Central limit theorem" and "Fundamental
            # theorem of algebra" both take the subject seat "theorem" — because in a keeping of
            # Gutenberg books, geography and taxonomy, "theorem" is rarer than "central" or
            # "algebra". The rarest-token heuristic is domain-blind, and this is where it shows.
            # Two theories sharing a subject share a WORD, and their witnesses are guaranteed to
            # overlap for no reason at all. Recorded rather than patched over: the limitation is
            # real, and the honest response is to refuse the pair, not to trust it.
            if subjects.get(a) and subjects.get(a) == subjects.get(b):
                continue
            shared = set(sources[a]) & set(sources[b])
            if not shared:
                continue
            # rarer shared witnesses count for more; a source everyone pulls counts for little
            weight = sum(math.log(n / (src_df[h] + 1)) + 0.35 for h in shared)
            shared_forms = forms[a] & forms[b]
            score = weight + 1.1 * len(shared_forms)
            if score < args.min:
                continue
            witnesses = sorted(shared, key=lambda h: src_df[h])[:3]
            proposals.append((score, a, b, sorted(shared_forms),
                              [sources[a][h] for h in witnesses]))

    proposals.sort(key=lambda x: -x[0])
    shown = min(args.n, len(proposals))
    print(f"PROPOSED CONNECTIONS — {len(proposals)} above {args.min}, showing {shown}")
    print(f"(co-retrieval over the keeping, depth {args.depth}; nothing is written)")
    print()
    for score, a, b, shared_forms, witnesses in proposals[:args.n]:
        da = (th[a].get("source") or {}).get("domain") or "?"
        db = (th[b].get("source") or {}).get("domain") or "?"
        print(f"  [{score:5.2f}]{'  ACROSS DOMAINS' if da != db else ''}")
        print(f"     {th[a].get('title')}  ({da})   [subject: {subjects.get(a)}]")
        print(f"     {th[b].get('title')}  ({db})   [subject: {subjects.get(b)}]")
        if shared_forms:
            print(f"       same form : {', '.join(shared_forms)}")
        for w in witnesses:
            print(f"       witness   : {w}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
