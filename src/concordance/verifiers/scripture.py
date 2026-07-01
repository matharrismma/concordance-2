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


_REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z.]+)\s*(\d+):(\d+)\s*$")


def _parse_ref(ref: str) -> Optional[Tuple[str, int, int]]:
    m = _REF_RE.match(ref or "")
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3))


# A passage: a single verse, a verse range, or a whole chapter.
#   "John 3:16" · "John 3:16-18" · "John 3" · "1 John 1:9"
_PASSAGE_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z.]+)\s*(\d+)(?::(\d+)(?:\s*-\s*(\d+))?)?\s*$")


class Bible:
    """An indexed WEB Bible: (book, chapter, verse) -> text, plus a book-alias map."""

    def __init__(self, verses: Iterable[dict]):
        self.idx: Dict[Tuple[str, int, int], str] = {}
        self.alias: Dict[str, str] = {}
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

    def resolve(self, ref: str) -> Dict[str, Any]:
        if not self.idx:
            return {"ref": ref, "text": "", "status": "source_missing",
                    "detail": "bible_en.jsonl not provisioned (run tools/migrate_bible.py)"}
        p = _parse_ref(ref)
        if not p:
            return {"ref": ref, "text": "", "status": "not_found",
                    "detail": "could not parse reference"}
        book_raw, ch, v = p
        canon = self.alias.get(_norm_book(book_raw))
        if not canon:
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
        canon = self.alias.get(_norm_book(book_raw))
        if not canon:
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
