"""Scripture verifier (WITNESS surface) — resolve and verify Bible citations.

Resolves a reference to its World English Bible (WEB, public domain) text and verifies
cited anchors: the ref must resolve, and any quoted text must match the WEB. Reads
data/bible_en.jsonl (gitignored; built by tools/migrate_bible.py). Degrades gracefully
(NOT_APPLICABLE) when the data isn't provisioned — the engine still runs.

LEAN port: ref-resolution on the WEB verse text. The Strong's / word-study /
original-language triangulation layer is DEFERRED — it needs the lw/00_source backend.
Witness-surface only (registered in WITNESS_VERIFIERS): surfaced when surface="witness".
The verse text is real, public-domain Scripture — found, never generated.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .base import VerifierResult, confirm, error, mismatch, na

# Common user abbreviations -> canonical WEB book name. Only applied when the target
# book is actually present in the loaded data (no broken aliases).
_COMMON_ABBREV = {
    "gen": "Genesis", "ex": "Exodus", "exod": "Exodus", "lev": "Leviticus",
    "num": "Numbers", "dt": "Deuteronomy", "deut": "Deuteronomy", "josh": "Joshua",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "pr": "Proverbs", "prov": "Proverbs",
    "eccl": "Ecclesiastes", "isa": "Isaiah", "jer": "Jeremiah", "ezek": "Ezekiel",
    "dan": "Daniel", "hos": "Hosea", "mt": "Matthew", "matt": "Matthew", "mk": "Mark",
    "mar": "Mark", "lk": "Luke", "luk": "Luke", "jn": "John", "jhn": "John",
    "rom": "Romans", "1co": "1 Corinthians", "2co": "2 Corinthians", "gal": "Galatians",
    "eph": "Ephesians", "phil": "Philippians", "php": "Philippians", "col": "Colossians",
    "heb": "Hebrews", "jas": "James", "1pe": "1 Peter", "2pe": "2 Peter",
    "1jn": "1 John", "rev": "Revelation",
}


def _norm_book(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()


# The book group must admit SPACES: "Song of Solomon" is the one space-bearing book with no leading
# digit, and the old class [A-Za-z.]+ made the entire book unreachable through every passage surface
# (found 2026-07-28 when the back-matter tables validated their refs). commentary.py, xrefs.py and
# teachings.py already used the space-tolerant form — the core reader was the one left behind.
_REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s*(\d+):(\d+)\s*$")
# `Jude 9` / `Philemon 6` / `Obadiah 1` — a book and ONE number. Only meaningful for a
# one-chapter book, which Bible._parse_single_chapter asks the corpus about.
_BARE_VERSE_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s*(\d+)\s*$")


def _parse_ref(ref: str) -> Optional[Tuple[str, int, int]]:
    m = _REF_RE.match(ref or "")
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3))


# A passage: a single verse, a verse range, or a whole chapter.
#   "John 3:16" · "John 3:16-18" · "John 3" · "1 John 1:9"
_PASSAGE_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s*(\d+)(?::(\d+)(?:\s*-\s*(\d+))?)?\s*$")


class Bible:
    """An indexed WEB Bible: (book, chapter, verse) -> text, plus a book-alias map."""

    def __init__(self, verses: Iterable[dict]):
        self.idx: Dict[Tuple[str, int, int], str] = {}
        self.alias: Dict[str, str] = {}
        self._one_chapter: Dict[str, bool] = {}   # canon -> is it a one-chapter book
        known: set = set()
        for d in verses:
            book = d.get("book")
            ch = d.get("chapter")
            v = d.get("verse")
            if not book or ch is None or v is None:
                continue
            try:
                key = (book, int(ch), int(v))
            except (TypeError, ValueError):
                continue
            self.idx[key] = d.get("text", "")
            known.add(book)
            self.alias.setdefault(_norm_book(book), book)
            ab = d.get("book_abbr")
            if ab:
                self.alias.setdefault(_norm_book(ab), book)
        for ab, target in _COMMON_ABBREV.items():
            if target in known:
                self.alias.setdefault(ab, target)
        # Full names are the never-questioned tier; the known set gates the curated abbreviations.
        self._fullnames = {_norm_book(b): b for b in known}
        self._known_books = known

    def book_candidates(self, raw: str) -> list:
        """Every book the given name could mean — exact aliases plus name prefixes, deduped.

        Prefix inference needs THREE letters. Two-letter fragments are ordinary English words —
        the gate's own test caught 'what is 15 percent of 240' resolving as ISAIAH 15 the day this
        tier was added, which would have made mundane arithmetic open the witness gate. Every
        legitimate two-letter form (Ps, Mt, Mk, Lk, Jn, Ex, Pr, Dt) is already deliberate
        convention in the curated table, so nothing real is lost."""
        n = _norm_book(raw)
        if not n:
            return []
        hits = {canon for key, canon in self.alias.items() if len(n) >= 3 and key.startswith(n)}
        exact = self.alias.get(n)
        if exact:
            hits.add(exact)
        return sorted(hits)

    def _pick_book(self, raw: str, have_page=None):
        """The book is always on the right page — or we ask which of two possibilities.

        (canonical_book | None, candidates). The tiers, in order of trust:
          1. a FULL book name typed out ('Judges', 'Jude') is exact — never questioned;
          2. this project's curated abbreviation table ('Phil' → Philippians, 'Mt' → Matthew) is
             deliberate convention — the right page by long custom;
          3. otherwise gather every book the name could mean (corpus-declared abbreviations AND
             name prefixes: 'Jud' → Jude or Judges), then use everything the request tells us —
             if exactly ONE candidate actually HAS the requested chapter and verse, that is the
             right page ('Jud 5' can only be Judges; Jude has one chapter);
          4. and when two or more could hold the page, ASK — return the candidates and let the
             human go the last mile. A silent guess opens the wrong book for someone, confidently.
        """
        n = _norm_book(raw)
        full = self._fullnames.get(n)
        if full:
            return full, []
        curated = _COMMON_ABBREV.get(n)
        if curated and curated in self._known_books:
            return curated, []
        hits = self.book_candidates(raw)
        if len(hits) == 1:
            return hits[0], []
        if not hits:
            return None, []
        if have_page is not None:
            viable = [b for b in hits if have_page(b)]
            if len(viable) == 1:
                return viable[0], []
            if viable:
                hits = viable
        return None, hits

    def _parse_single_chapter(self, ref: str):
        """`Jude 9` -> (Jude, 1, 9). In a ONE-CHAPTER book a bare number is the verse.

        Found by tools/calibrate.py on its first run, 2026-08-01: `Philemon 6`, `Jude 9` and
        `Obadiah 1` all answered "could not parse reference". Those are not exotic forms — they
        are how these books are ALWAYS cited. Nobody writes "Jude 1:9". Three of the five
        one-chapter books in the canon were unreachable by their ordinary name, and the whole
        suite was green: it is a calibration failure, not a code failure, which is exactly why
        only a standard could find it.

        WHICH BOOKS ARE ONE CHAPTER IS ASKED OF THE CORPUS, never hardcoded. A literal list here
        would be a second source of truth about the canon, free to drift from the text we actually
        hold — and this project's whole claim is that the text is the standard.
        """
        m = _BARE_VERSE_RE.match(ref or "")
        if not m:
            return None
        book_raw, n = m.group(1), int(m.group(2))
        canon, _hits = self._pick_book(book_raw, have_page=lambda b: (b, 1, n) in self.idx)
        if not canon:
            return None
        if not self._is_single_chapter(canon):
            return None                      # `John 3` means CHAPTER 3 — that is /passage's job
        return canon, 1, n

    def _is_single_chapter(self, canon: str) -> bool:
        cached = self._one_chapter.get(canon)
        if cached is None:
            cached = (canon, 2, 1) not in self.idx and (canon, 1, 1) in self.idx
            self._one_chapter[canon] = cached
        return cached

    def resolve(self, ref: str) -> Dict[str, Any]:
        if not self.idx:
            return {"ref": ref, "text": "", "status": "source_missing",
                    "detail": "bible_en.jsonl not provisioned (run tools/migrate_bible.py)"}
        p = _parse_ref(ref)
        if not p:
            p = self._parse_single_chapter(ref)
        if not p:
            return {"ref": ref, "text": "", "status": "not_found",
                    "detail": "could not parse reference"}
        book_raw, ch, v = p
        canon, hits = self._pick_book(book_raw, have_page=lambda b: (b, ch, v) in self.idx)
        if not canon:
            if hits:
                return {"ref": ref, "text": "", "status": "ambiguous",
                        "candidates": [f"{b} {ch}:{v}" for b in hits],
                        "detail": f"{book_raw!r} could be " + " or ".join(hits) +
                                  " — which did you mean? The last mile is yours."}
            return {"ref": ref, "text": "", "status": "not_found",
                    "detail": f"unknown book {book_raw!r}"}
        text = self.idx.get((canon, ch, v))
        if text is None:
            return {"ref": ref, "text": "", "status": "not_found",
                    "detail": f"{canon} {ch}:{v} not in the WEB"}
        return {"ref": f"{canon} {ch}:{v}", "text": text, "status": "ok", "detail": ""}

    def passage(self, ref: str) -> Dict[str, Any]:
        """Read a whole passage — a single verse, a verse range, or a whole chapter — as an
        ordered list of WEB verses. Found, never generated; degrades gracefully when unprovisioned.
        The Bible is the focus: 'we hold every thread so you can take your time and comprehend.'"""
        if not self.idx:
            return {"ref": ref, "verses": [], "count": 0, "status": "source_missing",
                    "detail": "bible_en.jsonl not provisioned (run tools/migrate_bible.py)"}
        m = _PASSAGE_RE.match(ref or "")
        if not m:
            return {"ref": ref, "verses": [], "count": 0, "status": "not_found",
                    "detail": "could not parse passage"}
        book_raw, ch = m.group(1), int(m.group(2))
        if m.group(3) is not None:
            _v = int(m.group(3))
            _has = lambda b: (b, ch, _v) in self.idx  # noqa: E731
        else:
            _has = lambda b: any(k[0] == b and k[1] == ch for k in self.idx)  # noqa: E731
        canon, hits = self._pick_book(book_raw, have_page=_has)
        if not canon:
            if hits:
                tail = f" {ch}" + (f":{m.group(3)}" if m.group(3) else "") + \
                       (f"-{m.group(4)}" if m.group(4) else "")
                return {"ref": ref, "verses": [], "count": 0, "status": "ambiguous",
                        "candidates": [b + tail for b in hits],
                        "detail": f"{book_raw!r} could be " + " or ".join(hits) +
                                  " — which did you mean? The last mile is yours."}
            return {"ref": ref, "verses": [], "count": 0, "status": "not_found",
                    "detail": f"unknown book {book_raw!r}"}
        if m.group(3) is None:  # whole chapter — scan every verse present (robust to gaps / non-1 start)
            found = sorted(((vv, t) for (bk, cc, vv), t in self.idx.items()
                            if bk == canon and cc == ch), key=lambda x: x[0])
            if not found:
                return {"ref": ref, "verses": [], "count": 0, "status": "not_found",
                        "detail": f"{canon} {ch} not in the WEB"}
            verses = [{"ref": f"{canon} {ch}:{vv}", "verse": vv, "text": t} for vv, t in found]
            return {"ref": f"{canon} {ch}", "book": canon, "chapter": ch,
                    "verses": verses, "count": len(verses), "status": "ok"}
        v_start = int(m.group(3))
        v_end = int(m.group(4)) if m.group(4) else v_start
        if v_end < v_start:
            v_start, v_end = v_end, v_start
        v_end = min(v_end, v_start + 200)  # cap the span
        verses = []
        for v in range(v_start, v_end + 1):
            t = self.idx.get((canon, ch, v))
            if t is not None:
                verses.append({"ref": f"{canon} {ch}:{v}", "verse": v, "text": t})
        if not verses:
            return {"ref": ref, "verses": [], "count": 0, "status": "not_found",
                    "detail": f"{canon} {ch}:{v_start}-{v_end} not in the WEB"}
        out_ref = f"{canon} {ch}:{v_start}" if v_end == v_start else f"{canon} {ch}:{v_start}-{v_end}"
        return {"ref": out_ref, "book": canon, "chapter": ch,
                "verses": verses, "count": len(verses), "status": "ok"}


# ── module-level default Bible (lazy, from bible_en.jsonl) ───────────────

_DEFAULT: Optional[Bible] = None


def _bible_path() -> Path:
    env = os.environ.get("CONCORDANCE_BIBLE_EN", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "bible_en.jsonl"


def _load_verses(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def default_bible(path: Optional[Path] = None) -> Bible:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = Bible(_load_verses(path or _bible_path()))
    return _DEFAULT


def _reset() -> None:
    """Test hook: drop the cached default so a new data path is picked up."""
    global _DEFAULT
    _DEFAULT = None


def resolve_ref(ref: str) -> Dict[str, Any]:
    """Resolve a reference to its WEB text: {ref, text, status: ok|not_found|source_missing}."""
    return default_bible().resolve(ref)


def read_passage(ref: str) -> Dict[str, Any]:
    """Read a passage (single verse / range / whole chapter) of the WEB — {ref, verses, count,
    status}. The core reading primitive the study experience is built on."""
    return default_bible().passage(ref)


def passage_text(ref: str) -> str:
    """The joined WEB text of a single-chapter reference, or "" when the ref doesn't parse
    (cross-chapter ranges, comma-lists) or isn't found — the display-only decline the study
    tables (harmony, timeline, teachings) rely on. One cached read of the corpus serves all
    callers; this is THE shared passage-text helper — do not hand-roll another."""
    if not ref:
        return ""
    try:
        p = read_passage(ref)
    except Exception:  # noqa: BLE001 — a missing/corrupt corpus declines, never crashes a table
        return ""
    if p.get("status") != "ok":
        return ""
    return " ".join(v.get("text") or "" for v in p.get("verses") or [])


def word_study(strongs_num: str) -> Dict[str, Any]:
    """Strong's word study — the original-language definition + every occurrence — via the
    triangulation backend (concordance.strongs). The agent in the original source: it FINDS
    the lexicon definition and the verses, never generates them. Returns
    {"status": "unavailable", ...} when the backend or its data isn't provisioned — the
    lean WEB-only path still works without it."""
    try:
        from ..strongs import Concordance
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"strongs backend not importable: {e}"}
    try:
        result = Concordance().word_study(strongs_num)
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": str(e)[:200]}
    # B2: enrich with a synthesized pronunciation guide from the transliteration (honest floor).
    try:
        from .. import pronounce
        src = result.get("pronunciation") or result.get("transliteration") or ""
        if src:
            result["pronunciation_guide"] = pronounce.guide(src)
    except Exception:  # noqa: BLE001 — never break the word study over a pronunciation nicety
        pass
    return result


def cross_references(ref: str) -> Dict[str, Any]:
    """Verses connected to a reference by shared original words (Strong's) — via the backend."""
    try:
        from ..strongs import Concordance
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"strongs backend not importable: {e}"}
    try:
        return Concordance().cross_references(ref)
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": str(e)[:200]}


def word_occurrences(strongs_num: str) -> Dict[str, Any]:
    """Every verse where a Strong's word occurs (the concordance) — via the backend."""
    try:
        from ..strongs import Concordance
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"strongs backend not importable: {e}"}
    try:
        return Concordance().word_occurrences(strongs_num)
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": str(e)[:200]}


def original_words(ref: str) -> Dict[str, Any]:
    """The tagged original words of a single verse — {ref, words:[{word_pos,word,strongs}], status}.
    Lets the reader tap the ORIGINAL word (not the English gloss) to open its study."""
    try:
        from ..strongs import Concordance
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"strongs backend not importable: {e}"}
    try:
        c = Concordance()
        bcv = c._ref_to_bcv(ref)
        if not bcv:
            return {"ref": ref, "status": "not_found", "words": [], "detail": "could not parse reference"}
        b, ch, v = bcv
        words = c.verse_words(b, ch, v)
        return {"ref": ref, "status": "ok" if words else "no_words", "count": len(words), "words": words}
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "detail": str(e)[:200]}


def _verify_anchor(anchor: Any) -> VerifierResult:
    name = "scripture.anchor"
    if isinstance(anchor, str):
        ref, claimed = anchor, None
    elif isinstance(anchor, dict):
        ref, claimed = anchor.get("ref"), anchor.get("text")
    else:
        return error(name, f"anchor must be a ref string or {{ref,text}}, got {type(anchor).__name__}")
    if not ref:
        return na(name, "anchor missing 'ref'")
    r = resolve_ref(ref)
    if r["status"] == "source_missing":
        return na(name, r["detail"])
    if r["status"] != "ok":
        return mismatch(name, f"{ref}: {r['detail']}", {"ref": ref, "status": r["status"]})
    if claimed:
        a, b = _norm_text(claimed), _norm_text(r["text"])
        if a and (a in b or b in a):
            return confirm(name, f"{r['ref']} resolves and the quoted text matches the WEB",
                           {"ref": r["ref"], "web_text": r["text"]})
        return mismatch(name, f"{r['ref']} quoted text does not match the WEB",
                        {"ref": r["ref"], "web_text": r["text"], "claimed": claimed})
    return confirm(name, f"{r['ref']} resolves: {r['text'][:80]}",
                   {"ref": r["ref"], "web_text": r["text"]})


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    anchors = packet.get("scripture_anchors")
    if anchors is None:
        anchors = (packet.get("SCRIPTURE_VERIFY") or {}).get("anchors")
    if not anchors:
        return [na("scripture", "no scripture_anchors present")]
    if isinstance(anchors, (str, dict)):
        anchors = [anchors]
    return [_verify_anchor(a) for a in anchors]
