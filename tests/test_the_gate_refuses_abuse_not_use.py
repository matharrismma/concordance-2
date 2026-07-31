"""The Gate holds the deeper reading, never the text.

Matt, 2026-07-31: *"I think seeing them is fine. Understanding the deeper meaning comes after the
gate."* · *"We don't need to refuse use. We refuse abuse."*

Found by following a citation. 2,619 cards cite the Bible Dictionary, and a reader on the secular
surface who followed one met `gate_closed` instead of the entry — while the cards themselves were
public on that very surface. We were publishing the content and gating the page that shows it.

Fifteen paths came out from behind the Gate: the passage, the original tongues, the dictionary,
the canon, the cross-references, the concordance, the places, the dates, the tables. Every one of
them is the text or its reference apparatus — seeing. Five stayed: exposition and the tracing of
meaning — understanding.

This test pins the line in both directions, because both directions can fail. A path that drifts
back behind the Gate refuses use; a path of exposition that drifts out of it hands someone the
second layer before they asked for it.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402

SEEING = ("/passage", "/original", "/canon", "/character", "/characters", "/cross_refs",
          "/tsk", "/word_study", "/word_occurrences", "/resolve", "/places", "/harmony",
          "/timeline", "/backmatter", "/study_find")


def _gated_paths():
    """AST-free but exact: walk dispatch() line by line, tracking the path each `_gate_closed()`
    sits under. The ground truth is the code, not a list someone remembered to update."""
    src = (ROOT / "src" / "concordance" / "web" / "api.py").read_text(encoding="utf-8")
    cur, found = None, set()
    for ln in src.splitlines():
        m = re.search(r'path (?:==|in) \(?["\']([/a-z_]+)', ln)
        if m:
            cur = m.group(1)
        if "_gate_closed()" in ln and "def " not in ln and cur:
            found.add(cur)
    return found


def test_only_the_deeper_reading_is_behind_the_gate():
    assert _gated_paths() == set(api.AFTER_THE_GATE), (
        f"the Gate drifted: extra={sorted(_gated_paths() - set(api.AFTER_THE_GATE))} "
        f"missing={sorted(set(api.AFTER_THE_GATE) - _gated_paths())}")


def test_the_text_is_never_refused_on_the_secular_surface():
    """A reader who asks for a verse gets the verse. The whole point of a free library."""
    cfg = EngineConfig("secular")
    status, body = api.dispatch("GET", "/passage", {"ref": "John 3:16"}, None, cfg)
    assert status == 200, f"the Word was refused: {body}"
    assert "gate_closed" not in str(body)


def test_the_dictionary_answers_the_citation_that_points_at_it():
    """2,619 cards cite /characters?search=... — the destination has to answer on the surface
    those cards are published on."""
    cfg = EngineConfig("secular")
    for path, q in (("/characters", {"search": "Aaron", "limit": "5"}),
                    ("/character", {"name": "Aaron"})):
        status, body = api.dispatch("GET", path, q, None, cfg)
        # What is under test is the GATE, not whether Aaron is in the store: another test may
        # have swapped the corpus, and "not found in Easton's" is a truthful answer. A refusal
        # is not.
        assert "gate_closed" not in str(body), f"{path} refuses use on the secular surface"


def test_no_seeing_path_can_be_refused():
    cfg = EngineConfig("secular")
    refused = []
    for path in SEEING:
        status, body = api.dispatch("GET", path, {"ref": "John 3:16", "name": "Aaron",
                                                  "q": "grace", "word": "grace"}, None, cfg)
        if "gate_closed" in str(body):
            refused.append(path)
    assert not refused, f"these refuse USE: {refused}"


def test_the_deeper_reading_still_waits_to_be_sought():
    """The other half of the line. Exposition is not withheld because it is precious — it is
    withheld because it only lands when it is sought."""
    cfg = EngineConfig("secular")
    open_early = []
    for path in api.AFTER_THE_GATE:
        status, body = api.dispatch("GET", path, {"ref": "John 3:16"}, None, cfg)
        if "gate_closed" not in str(body):
            open_early.append(path)
    assert not open_early, f"the second layer opened before it was sought: {open_early}"


def test_the_refusal_still_tells_the_reader_the_text_is_theirs():
    status, body = api._gate_closed()
    assert status == 404 and body["gate"] == "closed"
    assert "text itself is already yours" in body["detail"], (
        "a refusal that does not say what IS available reads as a locked door")


if __name__ == "__main__":
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in fns:
        fn()
        print(f"  ok  {name}")
    print(f"\n{len(fns)} gate tests passed — the deeper reading waits; the text never does.")
