"""The Gate refuses nothing. It invites.

Matt, 2026-07-31, in three passes:
  *"I think seeing them is fine. Understanding the deeper meaning comes after the gate."*
  *"We don't need to refuse use. We refuse abuse."*
  *"We don't hide knowledge. We aren't a secret society. Everyone is a part of the group. They
   experience what they want of it."*

Found by following a citation. 2,619 cards cite the Bible Dictionary, and a reader on the secular
surface who followed one met `gate_closed` instead of the entry — while the cards themselves were
public on that very surface. We were publishing the content and gating the page that shows it.

Twenty paths came out. Fifteen in the first pass — the text and its reference apparatus. Then the
last five, the exposition, because a person is not made ready by being refused.

This test pins it shut in the only direction left: nothing may drift back behind the Gate, on
EITHER door. The agent's door is checked against the human's, because the first pass fixed the
HTTP surface and left twenty MCP tools closed — correct server-side, invisible to the caller.

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

OPEN = ("/passage", "/original", "/canon", "/character", "/characters", "/cross_refs",
        "/tsk", "/word_study", "/word_occurrences", "/resolve", "/places", "/harmony",
        "/timeline", "/backmatter", "/study_find",
        "/commentary", "/prophecy", "/seeds", "/narratives", "/teachings")


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


def test_no_knowledge_is_behind_the_gate():
    assert _gated_paths() == set() == set(api.AFTER_THE_GATE), (
        f"knowledge went back behind the Gate: {sorted(_gated_paths())}")


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


def test_no_path_of_knowledge_can_be_refused():
    cfg = EngineConfig("secular")
    refused = []
    for path in OPEN:
        status, body = api.dispatch("GET", path, {"ref": "John 3:16", "name": "Aaron",
                                                  "q": "grace", "word": "grace"}, None, cfg)
        if "gate_closed" in str(body):
            refused.append(path)
    assert not refused, f"these refuse USE: {refused}"


def test_both_doors_agree():
    """The HTTP surface opened on 2026-07-31 and the AGENT surface did not — twenty tools an agent
    could not even see, on the surface agents actually read (ClaudeBot: 58% of api.). Correct server-side and
    invisible to the caller is the failure this project keeps meeting, so the two doors are
    checked against each other from now on."""
    from concordance.mcp import server as mcp
    sec = {t["name"] for t in mcp._tools_for(EngineConfig("secular"))}
    wit = {t["name"] for t in mcp._tools_for(EngineConfig("witness"))}
    assert not (wit - sec), f"tools an agent cannot see on the secular surface: {sorted(wit - sec)}"


def test_the_refusal_helper_is_unreachable_and_says_so():
    """Kept, not deleted: gate.js still recognises the shape, and the wording records what we
    stopped doing. Nothing in dispatch() can produce it any more — that is what the first test
    proves."""
    status, body = api._gate_closed()
    assert status == 404 and body["gate"] == "closed"
    assert "text itself is already yours" in body["detail"]


if __name__ == "__main__":
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in fns:
        fn()
        print(f"  ok  {name}")
    print(f"\n{len(fns)} gate tests passed — nothing is hidden, on either door.")
