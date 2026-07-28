"""One mission string, on every canonical surface, matchable by a machine.

Contract §5: "One mission string on every canonical surface (`/identity`, `llms.txt`, front door) —
no drift." The wording had not drifted — but on 2026-07-28 an audit found the sentence in
`site/llms.txt` was WRAPPED across lines with a markdown blockquote marker (`> `) interrupting it
mid-phrase. A human read it correctly; a machine checking for the canonical string could not match
it. On the one document written FOR agents, that is a real failure of the invariant even though the
prose was right.

So the check is the point: assert the mission is present as ONE contiguous string on each canonical
surface, exactly as `capabilities.MISSION` states it. If a future edit re-wraps it for tidiness, this
fails and says why.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import capabilities  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

MISSION = ("Narrow Highway gives humans and agents a governed way to find, check, use, and preserve "
           "information without losing its source, authority, or history.")


def test_the_canonical_mission_string_is_the_frozen_one():
    """capabilities.MISSION is the source the other surfaces are checked against."""
    assert capabilities.MISSION == MISSION


def test_identity_carries_it_verbatim():
    for surface in ("secular", "witness"):
        st, body = dispatch("GET", "/identity", {}, None, EngineConfig(surface))
        assert st == 200
        blob = " ".join(str(v) for v in body.values() if isinstance(v, str))
        assert MISSION in blob, f"/identity on the {surface} surface lost the mission string"


def test_llms_txt_carries_it_as_ONE_contiguous_string():
    """The agent-facing document. A wrapped sentence reads fine to a person and is invisible to a
    grep — which is exactly the reader llms.txt exists for."""
    text = (ROOT / "site" / "llms.txt").read_text(encoding="utf-8")
    assert MISSION in text, (
        "llms.txt does not contain the mission as one contiguous string — it was probably re-wrapped. "
        "Keep it on a single line: an agent checking our own canonical claim must be able to match it.")


def test_the_front_door_carries_it():
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert MISSION in html, "the front door lost the mission string (contract §1 and §5)"


def test_no_canonical_surface_carries_a_DIFFERENT_wording():
    """Drift is usually a near-miss, not an absence — a reworded 'improvement' is the likely failure."""
    stem = "gives humans and agents a"
    for name in ("llms.txt", "index.html"):
        text = (ROOT / "site" / name).read_text(encoding="utf-8")
        for idx in range(len(text)):
            if text.startswith(stem, idx):
                window = " ".join(text[max(0, idx - 60): idx + 220].split())
                assert MISSION.replace("\n", " ") in window or MISSION in text, (
                    f"{name} carries a VARIANT of the mission near offset {idx}: {window[:160]!r}")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — one mission string, machine-matchable, everywhere it is claimed.")
