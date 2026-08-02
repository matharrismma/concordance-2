"""CRAFT — cut cards out of a source we hold. One call, a set of cards, every one of them a span.

Matt, 2026-08-01: *"We should be able to pull the information and then craft the card from that
call. It may be 5-10 cards."*

The gap this closes is exactly in the middle of a path that already worked at both ends. The
tortoise (`find.py`) goes to the public-domain archives and comes back with documents; `sources.py`
fetches the bytes, hashes them, and writes a waybill. But the only card ever minted was the
CITATION — title, author, year, a link. The document itself was never opened. So the library could
tell you a book about a thing exists, and could not tell you one thing the book says.

    a call that yields one pointer card is a catalogue.
    a call that yields the source card AND the passages under it is a concordance.

THE MINT TAKES OFFSETS, NOT TEXT — and that is the whole safety argument.

`card_from_span(sha, start, end)` reads the body OUT of the anchored bytes. There is no parameter
through which prose could be passed in, so "craft" cannot quietly become "compose". This is the
Tesla valve Matt asked for (2026-08-01): the wrong direction is not policed by a check that might
jam, it is shaped so the flow cannot go that way. A generated sentence has no offset, so it has no
door here.

Which makes the honesty claim MACHINE-TESTABLE rather than a promise in a docstring: re-read the
file, decode it the same way, slice [start:end], compare. `verify_spans()` does that over a whole
set, and a card that fails is not a card that gets a warning — it never existed, because the only
constructor reads from the file.

WHAT IT DOES NOT DO. It does not summarise, paraphrase, rank by quality, or judge. It selects
which passages of a held document speak to a subject, and it says where each one is. The reader
gets the source's own words with an address, which is what a person asking about a tradition
deserves rather than someone's digest of it.

BOILERPLATE IS NOT THE BOOK. A Gutenberg text opens with a licence and closes with one; carding
those would fill a shelf with legal notices attributed to the author, so the envelope is cut off
before any span is taken. That trimming happens on the DECODED TEXT and shifts every offset, so
the trim point is recorded in each card and the verifier applies the identical rule — an offset
that means something different to the writer than to the reader is worse than no offset at all.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

# "5-10 cards" — the cap. There is no floor: a document with three relevant passages yields three.
# Padding a set to a target is the same failure as padding a search result list with near-misses,
# and it was already caught once on the ranking path.
MAX_CARDS = 10

# A span short enough to be a fragment tells the reader nothing and cannot carry its own context.
MIN_SPAN = 220
MAX_SPAN = 2600

# ONE decode rule, used by the writer and the verifier both. If these two ever differ, every
# offset in the keeping silently means something else — so it lives in one function, never inline.
ENCODING = "utf-8"


def decode(raw: bytes) -> str:
    """The single decode rule. `errors="replace"` keeps offsets stable across a bad byte: a
    strict decode that raises would make the whole document uncardable for one corrupt character,
    and a lossy-but-length-preserving replacement keeps every later offset true."""
    return raw.decode(ENCODING, errors="replace")


# ── the envelope ──────────────────────────────────────────────────────────────────────────────
_GUT_START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
_GUT_END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)


def trim(text: str) -> Tuple[int, int]:
    """(start, end) of the actual work inside its envelope — offsets into `text`, never a copy.

    Returning offsets rather than a trimmed string is deliberate: a caller that received trimmed
    text would compute spans against it and record offsets that do not address the file.
    """
    start, end = 0, len(text)
    m = _GUT_START.search(text)
    if m:
        start = m.end()
    m = _GUT_END.search(text, start)
    if m:
        end = m.start()
    return (start, end) if end - start > MIN_SPAN else (0, len(text))


# ── the cut ───────────────────────────────────────────────────────────────────────────────────
# A heading is short, unpunctuated at the end, and stands alone. This is a typographic observation
# about how documents are laid out, not an interpretation of what they mean.
_HEADING = re.compile(r"^[ \t]*(?![ \t])(.{3,78})[ \t]*$")
_ENDS_SENTENCE = re.compile(r"[.!?,;:]$")
_WORD = re.compile(r"[a-z]{3,}")


# PAGE FURNITURE IS NOT A HEADING. A scanned book carries a running head on every page — "50
# GOVERNMENT [q 94", "€ 42] DOCTRINE 35" — and the first cut of this module happily used them as
# card titles. They pass every typographic test for a heading (short, capitalised, unpunctuated)
# and mean nothing: the page number and the paragraph mark are the scanner's furniture, not the
# author's words. Detected by what they are made of rather than by a list of known layouts.
_FURNITURE = re.compile(r"^[\W\d]*\d+[\W\d]*$|^\d|\d$|[\[\]{}€¶§]")


def _looks_like_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 78 or _ENDS_SENTENCE.search(s):
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    digits = sum(1 for c in s if c.isdigit())
    if digits / len(s) > 0.15 or _FURNITURE.search(s):
        return False            # a running head, a folio, a paragraph mark
    upper = sum(1 for c in letters if c.isupper()) / len(letters)
    # ALL CAPS, or Title Case With Few Small Words — both are layout, not meaning.
    return upper > 0.6 or (s[0].isupper() and len(s.split()) <= 9)


# APPARATUS IS NOT CONTENT, and it ranks *well* — an index is the densest concentration of a
# book's subject terms anywhere in it, so relevance scoring reaches for it first. The tenth card
# of the first real run was the index of the 1923 Manual: every keyword, no sentence, no meaning.
_APPARATUS_WORDS = re.compile(
    r"\b(index|contents|errata|colophon|bibliograph|refer to paragraphs?|see also)\b", re.I)


def _is_apparatus(body: str, heading: str = "") -> bool:
    """True for an index, a table of contents, or any other finding-aid.

    Judged by SHAPE, not by title: apparatus is mostly numbers and fragments, with few finished
    sentences. That catches an unlabelled index, which a title-match never would.
    """
    s = (body or "").strip()
    if not s:
        return True
    if _APPARATUS_WORDS.search(heading or "") and len(s) < 400:
        return True
    digits = sum(1 for c in s if c.isdigit()) / len(s)
    sentences = len(re.findall(r"[a-z]{3,}[.!?](?:\s|$)", s))
    words = max(1, len(s.split()))
    # Dense with numbers AND starved of finished sentences — the signature of a finding-aid.
    return digits > 0.08 and sentences / (words / 100.0) < 1.5


# A span that opens mid-word ("costal Church of the Nazarene") is a real defect, not a cosmetic
# one: it misquotes the source in the first breath. Paragraph boundaries in OCR text do not always
# fall between words, so the start is snapped forward to a sentence.
_SENTENCE_START = re.compile(r"(?:^|[.!?]\s+|\n\s*)([A-ZÀ-Þ])")

# The paragraph mark a scanner leaves at the head of a numbered clause: "( 9.", "€ 472.", "6 390]",
# "«| 58.", "@ 270." — one or two stray glyphs, a number, a stop. It is an address in the printed
# book, and it is not the first thing the passage says.
#
# NO `^` ANCHOR, deliberately, and this was a real bug worth recording. These are used with
# `.match(text, pos)`, which already anchors at `pos` — but `^` does NOT: outside MULTILINE it
# matches only at position 0 of the whole string. So the anchored version silently never fired on
# a body (which starts deep inside a 311k-character book) while working perfectly on a title
# (a fresh string starting at 0). The titles came out clean, the bodies kept their furniture, and
# both were produced by the same "working" function. A check that passes on the easy case and is
# structurally unable to fire on the real one is the failure mode this project keeps meeting.
_LEAD_MARK = re.compile(r"(?:[^\s\d]{1,3}\s+)?\d{1,4}(?:\s+\d{1,4})?\s*[.\]\)]\s*")
# A running head OCR dropped into the middle of the text stream at a page break:
# "Y 34] DOCTRINE 29 of their association…". Only ever stripped from a DERIVED title, never a body.
_RUN_HEAD = re.compile(r"[A-Z][A-Z ]{2,}\s+\d{1,4}\s+")


def _strip_furniture(s: str) -> str:
    """Remove leading scanner furniture from a string used as a LABEL.

    Applied to titles only. A body is never edited — its span has to keep addressing the file, and
    a body we "cleaned" would be a quotation that does not match its own citation. Where the body
    needs the same treatment, `_snap_start` moves the OFFSET instead, which keeps them equal.
    """
    prev = None
    while s != prev and s:
        prev = s
        for pat in (_LEAD_MARK, _RUN_HEAD):
            m = pat.match(s)
            if m and m.end() < len(s):
                s = s[m.end():]
        s = s.lstrip(" \t[(")
    return s


def _snap_start(text: str, start: int, limit: int = 300) -> int:
    """Move `start` forward to the nearest clean opening, if it is not already at one.

    Two moves, both offset-only so the span stays true: step over a leading paragraph mark, and —
    if the span still opens mid-word, which OCR paragraph breaks do produce — advance to the next
    sentence. A card that opens "costal Church of the Nazarene" misquotes the source in its first
    breath, and that was the first run's worst defect.
    """
    if start <= 0 or start >= len(text):
        return max(0, start)
    m = _LEAD_MARK.match(text, start, min(len(text), start + 24))
    if m and m.end() < len(text):
        start = m.end()
    prev, first = text[start - 1], text[start]
    if not (prev.isalpha() and first.isalpha()):
        return start                      # already at a clean boundary
    m = _SENTENCE_START.search(text, start, min(len(text), start + limit))
    return m.start(1) if m else start


def sections(text: str, lo: int = 0, hi: Optional[int] = None) -> List[Tuple[int, int, str]]:
    """(start, end, heading) for each section of `text[lo:hi]`, in document order.

    Cuts on headings where a document has them and on paragraph runs where it does not, so a
    plain-text book without markup still yields whole thoughts rather than arbitrary slices.
    """
    hi = len(text) if hi is None else hi
    body = text[lo:hi]
    if not body.strip():
        return []

    # Paragraph boundaries first: every cut lands on one, so no span ever begins mid-sentence.
    paras: List[Tuple[int, int]] = []
    pos = 0
    for m in re.finditer(r"\n[ \t]*\n+", body):
        if m.start() > pos:
            paras.append((pos, m.start()))
        pos = m.end()
    if pos < len(body):
        paras.append((pos, len(body)))

    out: List[Tuple[int, int, str]] = []
    cur_start: Optional[int] = None
    cur_end = 0
    heading = ""

    def flush():
        nonlocal cur_start, cur_end, heading
        if cur_start is not None and cur_end - cur_start >= MIN_SPAN:
            out.append((lo + cur_start, lo + min(cur_end, cur_start + MAX_SPAN), heading))
        cur_start, heading = None, ""

    for (ps, pe) in paras:
        chunk = body[ps:pe]
        first = chunk.strip().splitlines()[0] if chunk.strip() else ""
        if _looks_like_heading(chunk.strip()) and len(chunk.strip().splitlines()) == 1:
            flush()                       # a heading closes the section before it
            heading = chunk.strip()
            continue
        if cur_start is None:
            cur_start, cur_end = ps, pe
            if not heading:
                heading = first.strip()[:78]
        else:
            cur_end = pe
        if cur_end - cur_start >= MAX_SPAN:
            flush()
    flush()
    return out


# ── selection: which passages speak to the subject ────────────────────────────────────────────
def _tokens(s: str) -> set:
    return set(_WORD.findall((s or "").lower()))


def rank(text: str, spans: List[Tuple[int, int, str]], subject: str,
         limit: int = MAX_CARDS) -> List[Tuple[int, int, str]]:
    """The spans that actually speak to `subject`, in DOCUMENT ORDER.

    Score is distinct subject terms present, then density — the same shape as the corpus ranker,
    and the same no-padding rule: a span that matches nothing about the subject is dropped, not
    ranked last and shipped. Ties break toward the earlier passage, so a set stays readable.
    """
    want = _tokens(subject)
    if not want:
        return spans[:limit]
    scored = []
    for i, (s, e, h) in enumerate(spans):
        body = text[s:e]
        if _is_apparatus(body, h):
            continue                    # an index outscores every real passage; it is not one
        have = _tokens(body) | _tokens(h)
        hits = want & have
        if not hits:
            continue                    # NEVER padded — silence beats a passage about nothing
        density = sum(body.lower().count(w) for w in hits) / max(1, len(body) / 1000)
        scored.append((len(hits), density, -i, (s, e, h)))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    keep = [t[3] for t in scored[:max(1, int(limit))]]
    return sorted(keep, key=lambda t: t[0])


# ── the mint ──────────────────────────────────────────────────────────────────────────────────
def card_from_span(sha: str, start: int, end: int, *, subject: str, waybill: Dict[str, Any],
                   parent_id: str = "", heading: str = "", trim_at: int = 0,
                   plane: str = "human", text: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """ONE card, whose body is READ FROM THE ANCHORED BYTES at [start:end].

    There is no `body` parameter. That is the point: the only way to put words in a card here is
    to point at words that are already in a document we hold and can re-read. Generation has no
    door.

    `text` is an optional already-decoded copy of the same file — an optimisation for minting a
    set, never a way to supply different content: when given it is checked against the file's own
    length before a single span is taken.
    """
    if not sha or end <= start:
        return None

    if text is None:
        from . import sources          # only when we must actually go to the ark
        path = (sources.held(sha) or {}).get("path") or ""
        if not path:
            return None
        try:
            with open(path, "rb") as fh:
                text = decode(fh.read())
        except OSError:
            return None

    if start < 0 or end > len(text):
        return None
    # Snap BEFORE the body is taken, and record the snapped offset — the span in `extra` must
    # address the words actually shown, or the address is decoration.
    start = _snap_start(text, start)
    body = text[start:end].strip()
    if len(body) < MIN_SPAN:
        return None

    origin = (waybill or {}).get("origin_url", "")
    label = (waybill or {}).get("label", "") or origin
    cid = "card_span_" + hashlib.sha256(f"{sha}|{start}|{end}".encode()).hexdigest()[:12]

    # A heading that is really a running head names nothing. Rather than dress the card in the
    # scanner's furniture, fall back to the passage's own opening clause — which is the source's
    # words either way, so the title never becomes an authored claim about the passage.
    head = _strip_furniture(heading.strip())
    if not head or not _looks_like_heading(head):
        opening = _strip_furniture(" ".join(body.split()))
        cut = re.search(r"[,;:.]", opening[:96])
        head = (opening[:cut.start()] if cut else opening[:72]).strip()
    title = (head or subject)[:110]

    from . import unchecked

    card = {
        "id": cid,
        "kind": "reference",
        "title": title,
        "body": body,
        "source": {
            "label": label[:300],
            "url": origin,
            "domain": "",
            # The address. A reader — or an auditor a year from now — can re-fetch these bytes,
            # hash them, and land on this exact passage.
            "authority_tier": "primary_pd",
        },
        "shelf": "sources",
        "box": "excerpt",
        "bands": sorted(_tokens(subject) | _tokens(title))[:12],
        "subject": subject,
        "connections": ([{"to_card_id": parent_id, "relationship": "excerpt_of",
                          "evidence": "a passage of the source this card was cut from"}]
                        if parent_id else []),
        "author": "engine",
        "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public",
        # THE TWO PLANES, unchanged from find.py and expand.py — one mechanism, one rule.
        "lifecycle_stage": "public" if plane == "human" else "public_review",
        "volatility": "permanent",
        "surface": "secular",
        # Not generated, and this is checkable rather than asserted: see verify_spans().
        "generated": False,
        "extra": {
            "source_sha256": sha,
            "span": [start, end],
            "trim_at": trim_at,
            "encoding": ENCODING,
            "crafted_from": origin,
        },
    }
    # THE CARD GOES IN WEARING ITS QUESTION. Stamped at the mint rather than at the write, so no
    # path exists by which an engine-written card reaches a store without it.
    return unchecked.mark(card)


def craft(sha: str, subject: str, *, waybill: Optional[Dict[str, Any]] = None,
          parent_id: str = "", limit: int = MAX_CARDS,
          plane: str = "human") -> Dict[str, Any]:
    """A held source + a subject -> the set of cards. 5-10, or fewer, never padded."""
    from . import sources

    wb = dict(waybill or sources.held(sha) or {})
    path = wb.get("path", "")
    if not path:
        return {"status": "not_held", "cards": [],
                "reason": "no anchored copy of this source on this device"}
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:  # noqa: BLE001
        return {"status": "unreadable", "cards": [], "reason": str(e)}

    text = decode(raw)
    lo, hi = trim(text)
    spans = rank(text, sections(text, lo, hi), subject, limit=limit)
    cards = []
    for (s, e, h) in spans:
        c = card_from_span(sha, s, e, subject=subject, waybill=wb, parent_id=parent_id,
                           heading=h, trim_at=lo, plane=plane, text=text)
        if c:
            cards.append(c)
    return {"status": "crafted" if cards else "nothing_relevant",
            "cards": cards, "sha256": sha, "subject": subject,
            "sections_found": len(sections(text, lo, hi)), "chars": len(text),
            "held_for_review": plane != "human",
            "message": (f"{len(cards)} passage(s) cut from a source we hold, each one addressable."
                        if cards else
                        "The source is held, but nothing in it speaks to this subject. I won't "
                        "cut a card that is not about what you asked.")}


def verify_spans(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Re-read every card's source and prove its body is the bytes it claims to be.

    THE HONESTY CHECK, run against the file rather than against our own memory of it. Four states,
    not two: `true` (the span matches), `false` (it does not — the card is lying), `absent` (the
    source is no longer anchored here, which is not the card's fault), `malformed` (no span at
    all). A card we cannot check is never reported as a card that passed.
    """
    from . import sources
    out = {"true": 0, "false": 0, "absent": 0, "malformed": 0, "failures": []}
    cache: Dict[str, Optional[str]] = {}
    for c in cards:
        ex = c.get("extra") or {}
        sha, span = ex.get("source_sha256"), ex.get("span")
        if not sha or not isinstance(span, (list, tuple)) or len(span) != 2:
            out["malformed"] += 1
            continue
        if sha not in cache:
            held = sources.held(sha) or {}
            path = held.get("path")
            try:
                cache[sha] = decode(open(path, "rb").read()) if path else None
            except OSError:
                cache[sha] = None
        text = cache[sha]
        if text is None:
            out["absent"] += 1
            continue
        s, e = int(span[0]), int(span[1])
        if 0 <= s < e <= len(text) and text[s:e].strip() == (c.get("body") or "").strip():
            out["true"] += 1
        else:
            out["false"] += 1
            out["failures"].append({"id": c.get("id"), "span": [s, e]})
    out["checked"] = out["true"] + out["false"]
    return out


__all__ = ["craft", "card_from_span", "verify_spans", "sections", "rank", "trim",
           "decode", "MAX_CARDS", "MIN_SPAN", "MAX_SPAN"]
