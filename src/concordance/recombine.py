"""RECOMBINE — the expressive half of the Cubo model: say it by RECOMBINING found instances over the
frame, never by generating. The bumblebee principle (recombine, don't generate) and "found, not authored,"
applied to speech.

Comprehension by the cube already works (decode a real sentence by the anchor it carries — `readwith`).
This is the other direction: given an intent and a pool of REAL, verbatim instances (sentences the keeping
holds, each tagged with the embodied anchor it carries), assemble a coherent answer by SELECTING and
ORDERING those fragments along the frame — existence → identity → motion — most relevant first. Every word
traces to a found instance; nothing is sampled from weights, nothing is composed to fit. If the pool holds
too little to answer, it says so (an honest gap) rather than inventing.

TWO GRAINS:
  • `compose` (v0) — EXTRACTIVE: select + frame-order whole verbatim SENTENCES.
  • `weave`  (v0.1) — CLAUSE-level: shrink the unit to the verbatim CLAUSE (a sharper answer, still a
    contiguous substring of ONE source), and join clauses with FRAME joints that assert nothing. The
    truth guard a verification engine must keep: no clause is altered, the frame joints carry no claim,
    and two clauses from DIFFERENT sources are held apart by a boundary (never fused by a conjunction), so
    the weave can never assert what no single source said. Per-clause provenance rides in `pieces`.

Still not yet the full frontier: resolving reference and inflecting a found word (which would modify the
verbatim) are the deeper craft, deliberately NOT done here — every content token stays real and cited.

`compose` is a pure function (instances are injected), so it is offline-testable and reaches for nothing on
its own; a caller gathers the instances (e.g. via `readwith.decodable` over the cards a search returned).
GATED for wiring by CONCORDANCE_RECOMBINE; the pure core always runs.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

_WORD = re.compile(r"[a-z0-9]+")

# The frame's narrative order: set the scene (what exists) → say what it is → what one does. An anchor the
# instance carries places it; an unknown/other-tongue anchor takes the middle (identity) role.
_ROLE = {
    "there is": 0, "there are": 0, "here is": 0, "il y a": 0, "es gibt": 0, "sunt": 0, "hay": 0,
    "i am": 1, "it is": 1, "this is": 1, "je suis": 1, "c'est": 1, "il est": 1, "ich bin": 1,
    "das ist": 1, "sum": 1, "est": 1, "soy": 1, "estoy": 1,
    "i go": 2, "je vais": 2, "ich gehe": 2, "eo": 2, "voy": 2,
}
_DEFAULT_ROLE = 1


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_RECOMBINE", "").strip().lower() in ("1", "true", "yes", "on")


def _toks(s: str) -> set:
    return {w for w in _WORD.findall(str(s or "").lower()) if len(w) > 2}


def compose(query: str, instances: List[Dict[str, Any]], *, limit: int = 5) -> Dict[str, Any]:
    """Assemble an answer from found, verbatim `instances` (each `{text, source, anchor}`), ordered along
    the frame and by relevance to `query`. Returns the composed passage + every fragment with its source.
    Honest empty when nothing fits — never invents to fill the gap."""
    qt = _toks(query)
    ranked = []
    for ins in instances:
        text = str((ins.get("text") if isinstance(ins, dict) else ins) or "").strip()
        if not text:
            continue
        anchor = str((ins.get("anchor") if isinstance(ins, dict) else "") or "").strip().lower()
        role = _ROLE.get(anchor, _DEFAULT_ROLE)
        rel = len(_toks(text) & qt)                       # overlap with the intent
        if qt and rel == 0:                               # APTNESS: skip a fragment that misses the intent
            continue
        ranked.append((role, -rel, len(text), text, ins))
    ranked.sort(key=lambda x: (x[0], x[1], x[2], x[3]))    # frame order → relevance → shortest → stable
    chosen: List[Dict[str, Any]] = []
    seen = set()
    for _role, _nrel, _ln, text, ins in ranked:
        if text in seen:
            continue
        seen.add(text)
        chosen.append({"text": text,
                       "source": (ins.get("source") if isinstance(ins, dict) else None),
                       "anchor": (ins.get("anchor") if isinstance(ins, dict) else None)})
        if len(chosen) >= max(1, int(limit)):
            break
    if not chosen:
        return {"passage": "", "fragments": [], "found": False,
                "means": "the keeping holds nothing that answers this by the frame — an honest gap, not a guess"}
    return {"passage": " ".join(c["text"] for c in chosen), "fragments": chosen, "found": True,
            "means": (f"composed from {len(chosen)} found, verbatim fragment(s), ordered by the frame "
                      "(existence → identity → motion); every word is real and cited — nothing generated")}


# ── v0.1 — clause-level weaving ────────────────────────────────────────────────────────────────────

# Clause boundaries: strong punctuation and a comma before a joining word. Splitting HERE keeps each piece
# a contiguous, verbatim span of the source — we never reach inside a clause.
_CLAUSE_SPLIT = re.compile(r"\s*[;:]\s*|\s+[—–]\s+|\s+-\s+|,\s+(?=and |but |so |then |or |for |yet |because |which |that |when |while |where )", re.I)
_TRIM = " \t\r\n,.;:—–-\"'()[]"


def _spans(text: str, anchor: str = "") -> List[Dict[str, Any]]:
    """Split a found sentence into verbatim clause spans (each a contiguous substring), tagging each with
    the embodied anchor it carries. Spans with too little content are dropped; if it will not split, the
    whole sentence rides as one span."""
    text = str(text or "").strip()
    if not text:
        return []
    out: List[Dict[str, Any]] = []
    for raw in _CLAUSE_SPLIT.split(text):
        span = str(raw or "").strip(_TRIM).strip()
        if len(_WORD.findall(span)) < 3:                  # a real clause, not a stray fragment
            continue
        low = span.lower()
        a = next((p for p in _ROLE if p in low), (anchor or "").strip().lower())
        out.append({"span": span, "anchor": a, "role": _ROLE.get(a, _DEFAULT_ROLE), "toks": _toks(span)})
    if not out:
        low = text.lower()
        a = next((p for p in _ROLE if p in low), (anchor or "").strip().lower())
        out.append({"span": text, "anchor": a, "role": _ROLE.get(a, _DEFAULT_ROLE), "toks": _toks(text)})
    return out


def weave(query: str, instances: List[Dict[str, Any]], *, limit: int = 4) -> Dict[str, Any]:
    """Weave an answer from found CLAUSES over the frame. Sharper than `compose` (clause, not sentence),
    with frame joints that assert nothing and a cross-source boundary so no two clauses fuse into a claim
    a source did not make. `pieces` carries per-clause provenance; `passage` is the rendered convenience."""
    qt = _toks(query)
    spans: List[Dict[str, Any]] = []
    for ins in instances:
        text = str((ins.get("text") if isinstance(ins, dict) else ins) or "")
        src = ins.get("source") if isinstance(ins, dict) else None
        anch = str((ins.get("anchor") if isinstance(ins, dict) else "") or "")
        for sp in _spans(text, anch):
            sp["source"] = src
            sp["rel"] = len(sp["toks"] & qt)
            spans.append(sp)
    # APTNESS (rung 1): never speak a grounded-but-irrelevant clause. Keep only clauses that actually
    # touch the intent, SELECT the most relevant, then ORDER the survivors by the frame for a coherent
    # reading. Selection is by aptness; the frame is only for how the chosen clauses are read.
    pool = [s for s in spans if (not qt) or s["rel"] > 0]
    pool.sort(key=lambda s: (-s["rel"], len(s["span"]), s["span"]))    # most apt first
    chosen: List[Dict[str, Any]] = []
    seen = set()
    for s in pool:
        if s["span"] in seen:
            continue
        seen.add(s["span"])
        chosen.append(s)
        if len(chosen) >= max(1, int(limit)):
            break
    if not chosen:
        return {"passage": "", "pieces": [], "found": False,
                "means": "the keeping holds no clause that ANSWERS this by the frame — an honest gap, not a guess"}
    chosen.sort(key=lambda s: (s["role"], -s["rel"], len(s["span"]), s["span"]))   # frame order for reading
    pieces: List[Dict[str, Any]] = []
    for i, s in enumerate(chosen):
        if i > 0:
            prev = chosen[i - 1]
            same = prev.get("source") is not None and prev.get("source") == s.get("source")
            # smooth WITHIN a source (it already related its own clauses); a BOUNDARY across sources so two
            # verbatim clauses are never fused into a single assertion no source made
            pieces.append({"text": ", " if same else "; ", "kind": "frame"})
        pieces.append({"text": s["span"], "kind": "found", "source": s.get("source"), "anchor": s.get("anchor")})
    passage = "".join(p["text"] for p in pieces).strip()
    n_src = len({s.get("source") for s in chosen})
    covered = round(len(_toks(passage) & qt) / len(qt), 2) if qt else None
    return {"passage": passage, "pieces": pieces, "found": True, "covered": covered,
            "means": (f"woven from {len(chosen)} found clause(s) across {n_src} source(s), ordered by the "
                      "frame; the joints assert nothing and clauses from different sources are held apart — "
                      "no claim is made that a source did not make; nothing is generated or altered")}


# ── reference resolution — found-for-found only ─────────────────────────────────────────────────────

_PRONOUN = {"it", "they", "this", "these", "that", "those"}
# words that END a noun phrase introduced by an anchor (prepositions, conjunctions, copulas)
_STOP_NP = {"in", "on", "at", "of", "to", "for", "with", "by", "from", "and", "but", "or", "nor",
            "that", "which", "who", "is", "are", "was", "were", "be", "been", "will", "would"}
# anchors that INTRODUCE a subject noun phrase, so its referent is unambiguous (frame-driven antecedent).
# "it is" is deliberately excluded — it is anaphoric itself, not a clean noun-introducer.
_INTRODUCERS = ("there is ", "there are ", "here is ", "this is ")


def _lead_pronoun(clause: str) -> Optional[str]:
    m = re.match(r"\s*([A-Za-z]+)", str(clause or ""))
    return m.group(1) if (m and m.group(1).lower() in _PRONOUN) else None


def _antecedent(clause: str) -> Optional[str]:
    """The noun phrase a clause INTRODUCES via a frame anchor (e.g. 'there is [clean water] in …'). Only a
    frame-introduced subject counts, so the referent is unambiguous; everything else yields None (we would
    rather leave a pronoun than guess its antecedent)."""
    low = str(clause or "").lower()
    for a in _INTRODUCERS:
        i = low.find(a)
        if i == -1:
            continue
        rest = str(clause)[i + len(a):]
        np: List[str] = []
        for w in rest.split():
            wl = w.strip(_TRIM).lower()
            if not wl or wl in _STOP_NP:
                break
            np.append(w.strip(_TRIM))
            if len(np) >= 3:
                break
        if np and np[0].lower() in ("a", "an", "the"):
            np = np[1:]                                   # 'The ' + 'a rock' → 'The rock'
        phrase = " ".join(np).strip()
        if phrase and _WORD.findall(phrase):
            return phrase
    return None


# ── inflection (rung 3) — number/tense AGREEMENT on the derived resolved variant only ───────────────
_VERB_PL = {"is": "are", "was": "were", "has": "have"}       # singular → plural
_VERB_SG = {v: k for k, v in _VERB_PL.items()}              # plural → singular (are→is, were→was, have→has)


def _is_plural(phrase: str) -> bool:
    """Heuristic number of an antecedent: plural if any content word is an -s plural (waters, rivers) —
    conservative (skips -ss like 'grass'); irregulars (men) read singular, acceptable for a marked variant."""
    for w in str(phrase or "").split():
        wl = w.strip(_TRIM).lower()
        if len(wl) > 3 and wl.endswith("s") and not wl.endswith("ss"):
            return True
    return False


def _inflect(clause: str, antecedent: str) -> tuple:
    """Correct the FIRST copula/aux in a RESOLVED clause to agree with the substituted antecedent's number.
    Returns (clause, mark|None). Only is/are, was/were, has/have — forms we can determine; nothing else is
    touched, and this only ever runs on the already-derived resolved variant, never on the verbatim."""
    plural = _is_plural(antecedent)
    toks = str(clause or "").split()
    for i, t in enumerate(toks):
        low = t.strip(_TRIM).lower()
        repl = _VERB_PL.get(low) if plural else _VERB_SG.get(low)
        if repl and repl != low:
            toks[i] = t.lower().replace(low, repl, 1) if low in t.lower() else repl
            return " ".join(toks), {"from": low, "to": repl}
    return clause, None


def resolve_refs(pieces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve a leading pronoun to a FOUND antecedent — the reference-resolution rung, held to one rule:
    substitute a found token for a found token. Only when the antecedent was INTRODUCED by a frame anchor
    in an immediately preceding clause of the SAME source (so it is unambiguous and already asserted). The
    verbatim `text` is never overwritten; a `resolved` variant + a `resolution` mark are offered beside it,
    and `resolved_passage` renders the reading. No found antecedent → the pronoun stands."""
    out: List[Dict[str, Any]] = []
    last_ante: Optional[str] = None
    last_src: Any = None
    for p in pieces:
        p = dict(p)
        if p.get("kind") == "found":
            clause = str(p.get("text") or "")
            pron = _lead_pronoun(clause)
            if pron and last_ante and last_src == p.get("source"):
                p["resolved"] = re.sub(r"^\s*" + re.escape(pron), "The " + last_ante, clause, count=1)
                p["resolution"] = {"pronoun": pron, "antecedent": last_ante,
                                   "kind": "found-for-found (frame-introduced antecedent, same source)"}
                # INFLECTION (rung 3): make the verb agree with the substituted antecedent's number — on
                # the resolved variant ONLY, marked; the verbatim `text` is never touched.
                inflected, mark = _inflect(p["resolved"], last_ante)
                if mark:
                    p["resolved"] = inflected
                    p["inflection"] = mark
            ante = _antecedent(clause)
            if ante:
                last_ante, last_src = ante, p.get("source")
        out.append(p)
    parts = [(p.get("resolved") or p.get("text") or "") if p.get("kind") == "found" else p.get("text", "")
             for p in out]
    return {"pieces": out, "resolved_passage": "".join(parts).strip()}


# ── live wiring — speak from the keeping ────────────────────────────────────────────────────────────

def answer(query: str, *, subject: str = "en", limit: int = 4, top_cards: int = 6,
           search_fn: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
           decodable_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Speak from the LIVE keeping: search for relevant cards, read the verbatim anchor-carrying sentences
    out of each (`readwith.decodable`), weave them by the frame, and resolve references found-for-found.
    Dependencies are injected for tests; production defaults are the live corpus + reader."""
    if search_fn is None:
        from . import corpus
        search_fn = lambda q: corpus.search(q, limit=top_cards)          # noqa: E731
    if decodable_fn is None:
        from . import readwith
        # REACH (rung 2): read anchor-carrying sentences from the card's RESIDENT BODY — no ark needed, so
        # a serving node speaks by the cube over the ~substance cards. An ark-equipped node can inject
        # `lambda c: readwith.decodable(c, subject)` to also read whole works.
        def decodable_fn(card: Dict[str, Any]) -> Dict[str, Any]:       # noqa: E306
            body = str(card.get("body") or "")
            # SPEAKING draws from ALL clean sentences (anchor tags the frame role but is not required),
            # so the engine reaches far more of the keeping than the teaching (anchor-only) side does.
            return {"found": readwith.sentences_in(body, subject, require_anchor=False) if body else []}
    cards = search_fn(query) or []
    instances: List[Dict[str, Any]] = []
    for c in cards[:max(1, int(top_cards))]:
        try:
            d = decodable_fn(c) or {}
        except Exception:  # noqa: BLE001 — a card the reader can't open is skipped, not fatal
            continue
        src = str(c.get("title") or c.get("id") or "a source")
        for f in (d.get("found") or []):
            if f.get("text"):
                instances.append({"text": f.get("text"), "anchor": f.get("anchor"), "source": src})
    w = weave(query, instances, limit=limit)
    if not w.get("found"):
        return {**w, "instances": len(instances)}
    rr = resolve_refs(w["pieces"])
    return {"passage": w["passage"], "resolved_passage": rr.get("resolved_passage"),
            "pieces": rr.get("pieces", w["pieces"]), "found": True, "instances": len(instances),
            "covered": w.get("covered"),
            "sources": sorted({p.get("source") for p in w["pieces"]
                               if p.get("kind") == "found" and p.get("source")}),
            "means": w["means"] + " — spoken from the live keeping; references resolved found-for-found."}
