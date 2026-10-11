#!/usr/bin/env python3
"""WARM A BOOK OF SCRIPTURE into the operator's voice (Matt, 2026-10-10: "Psalms and proverbs
would be the first I'd focus on"). Like tools/warm_voice.py for the curriculum, but for whole
books: it voices each verse ONCE through voice.speak (the content-addressed cache means the paid
API is touched at most once per distinct verse; a verse already voiced is a free hit). The engine
SPEAKS the kept, verified WEB text - it does not generate a word of it.

    PYTHONPATH=src python tools/warm_scripture.py --book Proverbs --dry-run   # counts, spends nothing
    ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=... PYTHONPATH=src python tools/warm_scripture.py --book Proverbs
    ...                                             ... --book Psalms --limit 200

Runs where the keys and the bible live (the box). A dry run needs no key and spends nothing.
Idempotent, bounded, honest: it reports verses, characters, new (spent) vs hits.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance import voice  # noqa: E402
from concordance.verifiers import scripture as S  # noqa: E402

# book -> chapter count (the whole-book warmers we support; extend as needed)
CHAPTERS = {"Psalms": 150, "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8,
            "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21,
            "Genesis": 50, "Isaiah": 66, "Romans": 16}


def verses_of_redletter():
    """The WORDS IN RED - Jesus's spoken words, per verse, from the WEB \\wj markers sourced into
    data/red_letter.json (see tools parse of the USFX). Voices the kept red-letter text itself."""
    import json
    import os
    data = Path(os.environ.get("CONCORDANCE_DATA_DIR") or "data")
    rl = data / "red_letter.json"
    if not rl.is_file():
        raise SystemExit("data/red_letter.json not found - source the words in red first")
    for ref, t in json.loads(rl.read_text(encoding="utf-8")).items():
        t = " ".join(str(t or "").split()).strip()
        if t:
            yield ref, t


def _verses_of_ref(ref: str):
    r = S.read_passage(ref)
    for v in (r.get("verses") or []):
        t = " ".join((v.get("text") or "").split()).strip()
        if t:
            yield v.get("ref") or ref, t


def verses_of(book: str):
    n = CHAPTERS.get(book)
    if not n:
        raise SystemExit(f"unknown book {book!r}; known: {', '.join(sorted(CHAPTERS))}")
    for ch in range(1, n + 1):
        yield from _verses_of_ref(f"{book} {ch}")


def verses_of_refs(refs):
    """Warm an explicit set of passage refs (a chapter or a verse range each), e.g. a named
    passage like the Sermon on the Mount = Matthew 5, 6, 7."""
    for ref in refs:
        yield from _verses_of_ref(ref)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="a whole book: " + ", ".join(sorted(CHAPTERS)))
    ap.add_argument("--ref", action="append", default=[],
                    help="a passage ref (chapter or verse range), repeatable; e.g. --ref 'Matthew 5'")
    ap.add_argument("--label", default="", help="a name for the --ref set, e.g. 'Sermon on the Mount'")
    ap.add_argument("--redletter", action="store_true", help="the Words in Red (data/red_letter.json)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    if not a.book and not a.ref and not a.redletter:
        raise SystemExit("give --book <Book>, one or more --ref <passage>, or --redletter")

    cache = voice._cache_dir()
    if a.redletter:
        items = list(verses_of_redletter()); a.book = "Words in Red"
    elif a.book:
        items = list(verses_of(a.book))
    else:
        items = list(verses_of_refs(a.ref)); a.book = a.label or " + ".join(a.ref)
    total_chars = sum(len(t) for _, t in items)
    cached = sum(1 for _, t in items if (cache / (voice._digest(t) + ".mp3")).is_file())
    new = len(items) - cached
    new_chars = sum(len(t) for _, t in items if not (cache / (voice._digest(t) + ".mp3")).is_file())
    print(f"{a.book}: {len(items)} verses, {total_chars} chars; already voiced {cached}, "
          f"NEW {new} ({new_chars} chars ~= credits)")
    if a.dry_run:
        print("dry run - nothing synthesized, nothing spent.")
        return 0
    if not voice.configured():
        print("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set - cannot synthesize; aborting.")
        return 2
    done = spent = fail = 0
    for ref, t in items:
        if a.limit and spent >= a.limit:
            break
        res = voice.speak(t)
        if res is None:
            fail += 1
            continue
        _, how = res
        done += 1
        if how != "hit":
            spent += 1
            if spent % 25 == 0:
                print(f"  [{done}/{len(items)}] synthesized {spent} new ... {ref}")
            time.sleep(0.2)                        # gentle on the API
    print(f"done · {done} voiced · {spent} newly synthesized · {fail} unavailable. "
          f"The kept verses now speak instantly and free, in the operator's voice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
