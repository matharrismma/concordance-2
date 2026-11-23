"""THE VERDICT WORDS — one register, every page that shows a verdict reads it.

2026-11-23 (the improvement plan's integrity release). Four public renderers — the homepage verifier,
the business auditor (checkit), the .com front page and the embeddable widget — each computed its OWN
headline from the counts: broken > 0 → "does not hold", anything else → "HOLDS" / "Every number checked
out." / "Verified by Narrow Highway". So a PARTIAL — a checked claim standing beside text that was never
checked — was shown to the public as an all-clear. The counts could not even see it: `unchecked` counts
checks that failed to run, not leftover text, so a PARTIAL arrives with unchecked = 0.

The fix is that the verdict is the ENGINE'S, word for word. This table says how each engine verdict is
headlined and in what tone; each page carries a one-line JSON copy of it (`var NH_VERDICTS = {...};`),
and tests/test_integrity_release.py fails if any copy differs from this one or if any page goes back to
deriving a verdict from counts. A verdict missing from the table is shown as ITSELF in the idle tone —
never promoted to a pass.

Tones are abstract; each page maps them to its own colours: pass (held), broken (a finding about the
claim), idle (a fact about US — nothing checked, part checked, could not run).
"""
from __future__ import annotations

from typing import Dict, List

# verdict -> [headline, tone]. Every verdict any verify door can return (audit.py, derivation.py, the
# plain-claim door in web/api.py). PARTIAL is NOT a pass: what was checked held; the rest was not checked.
VERDICTS: Dict[str, List[str]] = {
    "HOLDS": ["HOLDS", "pass"],
    "PARTIAL": ["PARTIAL", "idle"],
    "BROKEN": ["DOES NOT HOLD", "broken"],
    "INCOMPLETE": ["NOT CHECKED", "idle"],
    "NOTHING_TO_CHECK": ["NOTHING TO CHECK", "idle"],
    "SYSTEM_ERROR": ["COULD NOT RUN", "idle"],
    "QUARANTINE": ["NOT SENT", "idle"],
}

TONES = ("pass", "broken", "idle")


def headline(verdict: str) -> List[str]:
    """[headline, tone] for an engine verdict; an unknown verdict is itself, idle — never a pass."""
    return list(VERDICTS.get(str(verdict or ""), [str(verdict or "NOT CHECKED"), "idle"]))
