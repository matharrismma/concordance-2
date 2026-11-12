"""THE CANON LAYERS: the books beyond the 66, each read on a layer of its own (run 2026-11-11-full-canons).

The Roman Catholic and Eastern Orthodox churches read books beyond the 66 as Scripture; canon.py names them and
who holds them. Their text is built on the box by tools/build_canon_layers.py from two public-domain editions,
eBible.org's World English Bible (eng-web, the default) and its Douay-Rheims 1899 (engDRA, on request), and is
read here only from the build pinned for "canon-layers" (concordance.builds.built_dir, the one way in to built
data): <edition>.jsonl and layers.json. Nothing here reads a bible_<lang>.jsonl or the 66, and nothing here is
merged into them. A build that is not on this node reads as not built, and is looked for again on the next request.

WHEN THE LAYERS ARE ASKED. scripture.read_passage and scripture.resolve_ref call `lookup` only when the 66's own
lookup recognises no book name in the reference at all: never when it finds a 66 book but not the chapter or
verse (Daniel 13:1 and Esther 10:4 read as the 66 read them), never when a name is ambiguous among the 66 (Jud
1:1). The one exception is explicit: Psalm 151 (`psalm_151`), since Psalms has no chapter 151. The names are
canon.py's for the Catholic and Eastern Orthodox books and the Greek forms, matched whole after normalising, never
by prefix, so no name, abbreviation or prefix of a 66 book reaches an added book: Daniel (Greek) and Esther (Greek)
are reached only by those names or by the names of their additions.

THE PROSE GUARD. Where text is read as a possible reference (ask.find_ref, ask's own reading of the reference it
found, the console), the mode is "prose": an added book answers only to a full name in FULL_NAMES, never to an
abbreviation that is a common English word (sir, bar, tob, bel, wisdom), so 'yes sir 2:15 works for me' reads as
it read before. The readers a caller asks by name (read_passage, the MCP tools, /passage) use "names", which adds
canon.py's listed abbreviations.

EACH EDITION IN ITS OWN NUMBERING. Every reading says its edition, its licence, whose numbering it is and its
standing from canon.py. The Douay-Rheims follows the Vulgate's numbering and is never renumbered to the WEB's (its
Tobit 4:16 is the WEB's 4:15). An addition that stands inside a book of the layer (Susanna, Bel and the Dragon,
the Prayer of Azariah, the Letter of Jeremiah) is read in its own verse numbers mapped onto its span, and the
reading gives both: Susanna 1 is Daniel (Greek) 13:1. A verse the edition holds with no text reads as missing,
never as found. An addition the Douay-Rheims prints inside a book of the 66 reads as a miss that says where.

MEMORY. An edition is read on the first request that needs it, never at boot and never for a reading of the 66,
and then kept for the life of the process.
"""
from __future__ import annotations

import json
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

from . import builds as _builds
from . import canon as _canon

BUILD = "canon-layers"
DEFAULT_EDITION = "eng-web"
# Each edition id, and the names a caller may give it.
EDITIONS: Dict[str, Tuple[str, ...]] = {
    "eng-web": ("eng-web", "web", "world english bible"),
    "engDRA": ("engdra", "dra", "douay-rheims", "douay", "drb", "douay-rheims 1899"),
}
LAYER_NOTE = "a book beyond the 66, read on its own layer and never merged into the 66"
AZARIAH_NOTE = ("That count runs along the span, verse 1 being its first. Editions that print it as a book of its "
                "own, such as the KJV and the NRSV, number it 1-68 where this span holds 67 verses, so from some "
                "verse on their number may differ from this one by one.")
_SPAN_CAP = 200                         # the longest range one passage reads, as for the 66


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# Full names: the only names an added book answers to where prose is read as a reference.
FULL_NAMES = frozenset(_key(n) for n in (
    "tobit", "judith", "wisdom of solomon", "sirach", "ecclesiasticus", "baruch",
    "1 maccabees", "2 maccabees", "3 maccabees", "4 maccabees", "1 esdras", "prayer of manasseh", "psalm 151",
    "additions to esther", "additions of esther", "rest of esther", "esther (greek)", "greek esther",
    "daniel (greek)", "greek daniel", "prayer of azariah", "song of the three young men",
    "song of the three holy children", "susanna", "bel and the dragon", "letter of jeremiah", "epistle of jeremiah",
))


def _build_index() -> Dict[str, str]:
    """Every name of a Catholic or Eastern Orthodox book and of the Greek forms, normalised, to canon.py's name."""
    idx: Dict[str, str] = {}
    for trad in ("catholic", "eastern_orthodox"):
        for canonical, aliases in _canon.TRADITION_ADDITIONS[trad]["books"].items():
            for name in (canonical, *aliases):
                idx.setdefault(_key(name), canonical)
    for canonical, form in _canon.GREEK_FORMS.items():
        for name in (canonical, *form["aliases"]):
            idx.setdefault(_key(name), canonical)
    return idx


NAMES: Dict[str, str] = _build_index()

# a reference to an added book: a name (a leading ordinal, parentheses allowed), then optionally chapter, verse, range
_REF = re.compile(r"^\s*(?P<book>[1-4]?\s*[A-Za-z][A-Za-z.() ]*?)\s*(?:(?P<ch>\d{1,3})(?:\s*:\s*(?P<v>\d{1,3}[a-z]?)"
                  r"(?:\s*-\s*(?P<v2>\d{1,3}[a-z]?))?)?)?\s*$")
_THE = ("prayer ", "additions ", "letter ", "song ", "epistle ", "rest ")


def edition_id(edition: Any) -> Optional[str]:
    """'eng-web' or 'engDRA' for any name a caller may give; the default for none; None for an unknown name."""
    if edition is None or not str(edition).strip():
        return DEFAULT_EDITION
    k = _key(str(edition))
    for ed, names in EDITIONS.items():
        if k in {_key(n) for n in names}:
            return ed
    return None


def _title(canonical: str) -> str:
    """canon.py's name as a title: 'bel and the dragon' -> 'Bel and the Dragon'."""
    small = {"and", "the", "of", "to"}
    words = canonical.split()
    titled = " ".join(w if (i and w in small) else (w[:1].upper() + w[1:]) for i, w in enumerate(words))
    return titled.replace("(greek)", "(Greek)")


def _named(canonical: str) -> str:
    """The name as a sentence uses it: 'the Prayer of Azariah', 'Susanna'."""
    return ("the " if canonical.startswith(_THE) else "") + _title(canonical)


def _num(label: str) -> int:
    m = re.match(r"\d+", label or "")
    return int(m.group(0)) if m else -1


# ------------------------------------------------------------------------------------------------ the build

class _Layer:
    """One edition, indexed: (book, chapter, label) -> text, with its manifest."""

    def __init__(self, ed: str, meta: Dict[str, Any], rows: List[dict]):
        self.ed, self.meta = ed, meta
        self.name = meta.get("name") or ed
        self.idx: Dict[Tuple[str, int, str], str] = {}
        self.order: Dict[Tuple[str, int], List[str]] = {}
        self.chapters: Dict[str, List[int]] = {}
        for r in rows:
            book, ch, v = r.get("book"), r.get("chapter"), r.get("verse")
            if not isinstance(book, str) or not isinstance(ch, int) or isinstance(ch, bool) or v is None:
                continue
            label = str(v)
            self.idx[(book, ch, label)] = r.get("text") or ""
            self.order.setdefault((book, ch), []).append(label)
            if ch not in self.chapters.setdefault(book, []):
                self.chapters[book].append(ch)
        self.books: Dict[str, str] = {}
        for b in meta.get("books") or []:
            canonical = NAMES.get(_key(b.get("name") or ""))
            if canonical:
                self.books[canonical] = b["name"]
        self.within: Dict[str, Dict[str, Any]] = meta.get("within") or {}
        self.in_the_66: Dict[str, Dict[str, Any]] = meta.get("in_the_66") or {}


_LOCK = threading.Lock()
_LOADED: Dict[str, _Layer] = {}


def _reset() -> None:
    """Test hook: forget every loaded edition."""
    with _LOCK:
        _LOADED.clear()


def loaded() -> List[str]:
    """The editions this process has read so far: none until a request needs one."""
    return sorted(_LOADED)


def _load(ed: str) -> Optional[_Layer]:
    """The edition, read on first use and kept; None when the pinned build is not on this node (not cached, so a
    build that lands later is found on the next request)."""
    got = _LOADED.get(ed)
    if got is not None:
        return got
    with _LOCK:
        got = _LOADED.get(ed)
        if got is not None:
            return got
        where = _builds.built_dir(BUILD)
        if where is None:
            return None
        try:
            held = json.loads((where / "layers.json").read_text(encoding="utf-8"))
            meta = (held.get("editions") or {}).get(ed) if isinstance(held, dict) else None
            if not isinstance(meta, dict):
                return None
            rows = []
            with open(where / f"{ed}.jsonl", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        rows.append(json.loads(line))
        except (OSError, ValueError, AttributeError):
            return None
        got = _Layer(ed, meta, rows)
        _LOADED[ed] = got
        return got


# ------------------------------------------------------------------------------------------------ the answers

def standing(canonical: str) -> Dict[str, Any]:
    """canon.py's report for a book: who holds it and the history, never a verdict."""
    out = dict(_canon.canon_status(canonical))
    out["book"] = _title(canonical)
    return out


def _labels(layer: _Layer) -> Dict[str, Any]:
    m = layer.meta
    return {"lang": "en", "edition": layer.ed, "translation": m.get("name"), "source": m.get("source"),
            "license": m.get("license"), "numbering": m.get("numbering"), "layer": LAYER_NOTE}


def _miss(asked: str, shape: str, detail: str, **extra: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {"ref": asked, "status": "not_found", "detail": detail}
    out.update({"verses": [], "count": 0} if shape == "passage" else {"text": ""})
    out.update(extra)
    return out


def _span_text(w: Dict[str, Any]) -> str:
    """Where a span stands: 'Daniel (Greek) 13', 'Daniel (Greek) 3:24-90', 'Esther 10:4-16:24', 'Daniel'."""
    if w.get("from"):
        return f"{w['book']} {w['from']}-{w['to']}"
    if w.get("chapter"):
        return f"{w['book']} {w['chapter']}" + ("" if w.get("whole_chapter") else f":{w['first']}-{w['last']}")
    return w["book"]


def _within_note(canonical: str, w: Dict[str, Any], who: str) -> str:
    """Where an addition is read, in a sentence: within a book, or on a span with its own verse numbers."""
    named = _named(canonical)
    named = named[:1].upper() + named[1:]
    if not w.get("chapter"):
        return (f"{named} are read within {w['book']}, a book of this layer: the {who} prints them inside its "
                f"verses, not as a book apart.")
    offset = int(w["first"]) - 1
    n = f"{w['book']} {w['chapter']}:" + ("N" if offset == 0 else f"(N+{offset})")
    note = f"{named} is read where the {who} prints it, as {_span_text(w)}; its verse N is {n}."
    if canonical == "prayer of azariah":
        note += " " + AZARIAH_NOTE
    return note


def _span_at(layer: _Layer, book: str, ch: int, label: str) -> Optional[Tuple[str, Dict[str, Any], int]]:
    """The addition whose span holds this verse: (canonical, span, the verse's number in the addition)."""
    if not label.isdigit():
        return None
    for canonical, w in sorted(layer.within.items()):
        if w.get("book") == book and w.get("chapter") == ch and int(w["first"]) <= int(label) <= int(w["last"]):
            return canonical, w, int(label) - int(w["first"]) + 1
    return None


def _pick(layer: _Layer, book: str, ch: int, lo: Optional[str], hi: Optional[str]) -> List[str]:
    """The labels of a chapter from lo to hi, in the file's order; every label when lo is None."""
    order = layer.order.get((book, ch), [])
    if lo is None:
        return list(order)
    if hi is None or hi == lo:
        return [lo] if lo in order else []
    a, b = sorted((_num(lo), _num(hi)))
    b = min(b, a + _SPAN_CAP)
    return [x for x in order if a <= _num(x) <= b]


def named_in_full(ref: str) -> bool:
    """The prose guard's one rule: `ref` names an added book by a full name in FULL_NAMES, or Psalm 151 as
    'Psalm 151' or 'Psalms 151'. Never an abbreviation such as sir, bar, tob, bel or wisdom."""
    m = _REF.match(ref or "")
    if not m:
        return False
    k = _key(m.group("book"))
    return k in FULL_NAMES or (k in ("psalm", "psalms") and m.group("ch") == "151")


def lookup(ref: str, shape: str, *, edition: Any = None, mode: str = "names") -> Optional[Dict[str, Any]]:
    """The reading of the added book `ref` names, or None when it names none in this mode, so the 66's reading
    stands. `shape` is "passage" (verses) or "ref" (one verse). scripture.py calls it only when the 66 recognise
    no book name in `ref`."""
    m = _REF.match(ref or "")
    if not m or mode not in ("names", "prose"):
        return None
    canonical = NAMES.get(_key(m.group("book")))
    if canonical is None or (mode == "prose" and not named_in_full(ref)):
        return None
    return read(canonical, m.group("ch"), m.group("v"), m.group("v2"), ref, shape, edition)


def psalm_151(ref: str, verse: Optional[str], verse_to: Optional[str], shape: str, *,
              edition: Any = None) -> Dict[str, Any]:
    """Psalm 151, the explicit exception: the 66 read 'Psalm 151:1' as Psalms, which has no chapter 151."""
    return read("psalm 151", None if verse is None else "1", verse, verse_to, ref, shape, edition, cite="Psalm 151")


def read(canonical: str, ch: Optional[str], v: Optional[str], v2: Optional[str], asked: str, shape: str,
         edition: Any = None, cite: Optional[str] = None) -> Dict[str, Any]:
    """Canon.py's book `canonical` at chapter `ch`, verse `v` (to `v2`), in an edition, labelled."""
    ed = edition_id(edition)
    if ed is None:
        return _miss(asked, shape, f"no edition {str(edition)!r} on the canon layers; they hold eng-web (the World "
                     f"English Bible, the default) and engDRA (the Douay-Rheims 1899)", editions=list(EDITIONS),
                     standing=standing(canonical))
    layer = _load(ed)
    if layer is None:
        return _miss(asked, shape, f"{_title(canonical)} is kept on a layer of its own beyond the 66, and that "
                     f"layer's text is not built on this node", built=False, edition=ed, standing=standing(canonical))
    labels = _labels(layer)
    if canonical in layer.books:
        return _read_book(layer, layer.books[canonical], canonical, ch, v, v2, asked, shape, labels, cite)
    w = layer.within.get(canonical)
    if w and w.get("chapter"):
        return _read_span(layer, canonical, w, ch, v, v2, asked, shape, labels)
    held = ", ".join(layer.books.values())
    printed = layer.in_the_66.get(canonical)
    if printed:
        if canonical in _canon.GREEK_FORMS:
            said = (f"The {layer.name} holds {printed['book']} with its additions as one book under a code of the "
                    f"66, which no layer holds")
        else:
            said = (f"The {layer.name} prints {_named(canonical)} within its {printed['book']}, as "
                    f"{_span_text(printed)}, a book of the 66 under its own code, which no layer holds")
        return _miss(asked, shape, f"{said}. This layer holds only the added books with codes of their own in this "
                     f"edition: {held}.", printed_at=_span_text(printed), standing=standing(canonical), **labels)
    return _miss(asked, shape, f"The {layer.name} layer holds no {_title(canonical)}; it holds {held}.",
                 standing=standing(canonical), **labels)


def _read_book(layer: _Layer, book: str, canonical: str, ch: Optional[str], v: Optional[str], v2: Optional[str],
               asked: str, shape: str, labels: Dict[str, Any], cite: Optional[str]) -> Dict[str, Any]:
    chapters = layer.chapters.get(book, [])
    one_chapter = chapters == [1]
    if ch is None:
        if not one_chapter:
            return _miss(asked, shape, f"name a chapter of {book}: the {layer.name} holds chapters "
                         f"{chapters[0]}-{chapters[-1]}" if chapters else f"the {layer.name} holds no {book}",
                         standing=standing(canonical), **labels)
        c, lo, hi = 1, None, None
    elif v is None and one_chapter:
        c, lo, hi = 1, ch, None                                     # 'Prayer of Manasseh 5' is its verse 5
    else:
        c, lo, hi = int(ch), v, v2
    if shape == "ref" and lo is None:
        return _miss(asked, shape, "name a verse: a single reference reads one verse",
                     standing=standing(canonical), **labels)
    return _answer(layer, book, c, _pick(layer, book, c, lo, hi), canonical, asked, shape, labels, cite,
                   whole=lo is None)


def _read_span(layer: _Layer, canonical: str, w: Dict[str, Any], ch: Optional[str], v: Optional[str],
               v2: Optional[str], asked: str, shape: str, labels: Dict[str, Any]) -> Dict[str, Any]:
    """An addition inside a book of the layer, read in its own verse numbers mapped onto its span."""
    name = _title(canonical)
    first, last = int(w["first"]), int(w["last"])
    size = last - first + 1
    if ch is None:                                                   # the name alone: the whole span
        if shape == "ref":
            return _miss(asked, shape, f"name a verse of {name}, 1 to {size}", standing=standing(canonical),
                         **labels)
        lo, hi = 1, size
    elif v is None:
        lo, hi = int(ch), int(ch)                                    # 'Susanna 5' is its verse 5
    elif int(ch) == 1 and v.isdigit() and (v2 is None or v2.isdigit()):
        lo, hi = int(v), int(v2 or v)
    else:
        return _miss(asked, shape, f"{name} is one chapter: its verses are 1 to {size}",
                     standing=standing(canonical), **labels)
    lo, hi = min(lo, hi), max(lo, hi)
    if lo < 1 or lo > size:
        return _miss(asked, shape, f"{name} has verses 1 to {size} in the {layer.name}",
                     standing=standing(canonical), **labels)
    hi = min(hi, size)
    out = _answer(layer, w["book"], int(w["chapter"]), _pick(layer, w["book"], int(w["chapter"]),
                  str(lo + first - 1), str(hi + first - 1)), canonical, asked, shape, labels, None, whole=False)
    if out.get("status") == "ok":
        out["addition_ref"] = name if ch is None else (f"{name} {lo}" if lo == hi else f"{name} {lo}-{hi}")
    return out


def _answer(layer: _Layer, book: str, ch: int, picked: List[str], canonical: str, asked: str, shape: str,
            labels: Dict[str, Any], cite: Optional[str], whole: bool) -> Dict[str, Any]:
    if not picked:
        return _miss(asked, shape, f"{asked.strip()} is not in the {layer.name} ({labels['source']})",
                     standing=standing(canonical), **labels)
    verses: List[Dict[str, Any]] = []
    missing: List[str] = []
    touched: List[str] = []
    for label in picked:
        ref = f"{cite}:{label}" if cite else f"{book} {ch}:{label}"
        text = layer.idx.get((book, ch, label))
        if not text:                                                 # held with no text: a miss, never a find
            missing.append(ref)
            continue
        row: Dict[str, Any] = {"ref": ref, "verse": int(label) if label.isdigit() else label, "text": text}
        span = _span_at(layer, book, ch, label)
        if span:
            row["addition_ref"] = f"{_title(span[0])} {span[2]}"
            if span[0] not in touched:
                touched.append(span[0])
        verses.append(row)
    lead = _span_at(layer, book, ch, picked[0])
    extra: Dict[str, Any] = {"standing": standing(lead[0] if lead else canonical), **labels}
    own = layer.within.get(canonical)
    notes = [{"addition": _title(c), "note": _within_note(c, layer.within[c], layer.name)} for c in touched]
    if own and not own.get("chapter") and canonical not in touched:
        notes.insert(0, {"addition": _title(canonical), "note": _within_note(canonical, own, layer.name)})
    if notes:
        extra["within"] = notes
    if missing:
        said = (f"the {layer.name} holds {', '.join(missing)} with no text, so "
                f"{'it reads' if len(missing) == 1 else 'they read'} as missing, never as found")
        extra.update({"missing": missing, "missing_note": said})
        if not verses:
            return _miss(asked, shape, said[:1].upper() + said[1:], **extra)
    if not verses:
        return _miss(asked, shape, f"{asked.strip()} is not in the {layer.name}", **extra)
    head = f"{cite}" if cite else f"{book} {ch}"
    if whole:
        out_ref = head
    else:
        a, b = picked[0], picked[-1]
        out_ref = (f"{cite}:{a}" if cite else f"{book} {ch}:{a}") + ("" if a == b else f"-{b}")
    tail = _span_at(layer, book, ch, picked[-1])
    if lead and tail and lead[0] == tail[0]:                         # the reading lies within one addition
        extra["addition_ref"] = f"{_title(lead[0])} {lead[2]}" + ("" if lead[2] == tail[2] else f"-{tail[2]}")
    if shape == "ref":
        out = {"ref": out_ref, "text": verses[0]["text"], "status": "ok", "detail": ""}
        out.update(extra)
        return out
    return {"ref": out_ref, "book": book, "chapter": ch, "verses": verses, "count": len(verses), "status": "ok",
            **extra}
