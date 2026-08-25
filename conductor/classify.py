"""M1 — the shop-work classifier (Conductor Canon, genuine gap one).

Rule-based, confidence-scored, CRISIS-first. Nine types. Unknown or weak work is CLARIFY (below
0.7), never a silent guess. The load-bearing component: it learns the SHOP's tongue, not textbook
phrasing, so it ships only at 100% on Matt's 50 hand-labeled orders (SOP-02 — Matt only, not
delegated). This module is the classifier and the harness; the real benchmark labels are Matt's.

CRISIS detection DELEGATES to the kernel's matcher (concordance.ask.is_crisis) — connect, don't
rebuild — and degrades to a local list when run standalone. A cry for help halts autonomous action
and routes to the crisis path, per the kernel's crisis doctrine (never to a quoting agent).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

try:  # reuse the kernel's crisis doctrine when connected; degrade standalone
    from concordance.ask import is_crisis as _kernel_is_crisis
except Exception:  # noqa: BLE001
    _kernel_is_crisis = None

CLARIFY_THRESHOLD = 0.7

# Human-safety crisis only (a downed MACHINE is MAINTENANCE, not CRISIS). Fallback list; the kernel
# matcher is preferred and is tense-hole-hardened.
_LOCAL_CRISIS = (
    "injured", "is hurt", "got hurt", "bleeding", "unconscious", "not breathing",
    "can't breathe", "cant breathe", "call 911", "someone is down", "amputat",
    "severed", "chemical in his eye", "chemical in her eye", "gas leak", "on fire", "caught fire",
    "trapped in", "crushed his", "crushed her", "cut his hand", "cut her hand",
)

# Nine-type taxonomy. Each type: (strong, weak). A strong hit scores 0.9; only weak hits score 0.62
# (-> CLARIFY). CRISIS is handled first and is never scored here.
TYPES: Tuple[str, ...] = (
    "CRISIS", "QUOTE", "TOOLING", "SCHEDULE", "QUALITY",
    "MATERIAL", "MAINTENANCE", "PROCESS", "HISTORICAL",
)

_STRONG = {
    "QUOTE": ("quote", "quotation", "bid on", "estimate for", "how much", "price it", "pricing", "rfq", "ballpark"),
    "TOOLING": ("end mill", "endmill", "insert", "drill bit", "reamer", "tool life", "tooling", "cutter", "tap ", "worn tool"),
    "SCHEDULE": ("schedule", "lead time", "due date", "delivery date", "when can", "book the", "time slot", "capacity", "backlog", "get it out by"),
    "QUALITY": ("first article", "inspection", "out of spec", "out-of-spec", "nonconformance", "non-conformance", "cmm", "gauge", "tolerance", "deviation", "ppap", "scrap", "reject", "rework"),
    "MATERIAL": ("material cert", "mill cert", "raw material", "bar stock", "plate stock", "order material", "6061", "4140", "titanium", "inconel", "stock for"),
    "MAINTENANCE": ("preventive maintenance", "pm on", "calibrate", "calibration", "way oil", "spindle repair", "machine down", "coolant change", "breakdown", "won't power", "alarm on the"),
    "PROCESS": ("setup sheet", "fixture", "work instruction", "cam program", "speeds and feeds", "process for", "how do we make", "work holding", "workholding", "program the"),
    "HISTORICAL": ("last time", "previous job", "prior job", "what did we quote", "ran this before", "history on", "job number", "we made these before"),
}
_WEAK = {
    "QUOTE": ("quote", "price", "cost", "bid"),
    "TOOLING": ("tool", "bit", "insert"),
    "SCHEDULE": ("when", "book", "due", "slot"),
    "QUALITY": ("quality", "measure", "check the part", "inspect"),
    "MATERIAL": ("material", "stock", "steel", "aluminum"),
    "MAINTENANCE": ("maintenance", "repair", "service", "down"),
    "PROCESS": ("process", "setup", "program", "fixture"),
    "HISTORICAL": ("before", "previous", "history", "last"),
}
# Tie-break order when two types hit equally: the safety/quality-leaning ones first, catch-alls last.
_PRIORITY = ("QUALITY", "TOOLING", "MATERIAL", "MAINTENANCE", "SCHEDULE", "PROCESS", "HISTORICAL", "QUOTE")


@dataclass(frozen=True)
class Classification:
    work_type: str            # one of TYPES, or "CLARIFY"
    confidence: float
    note: str = ""
    secondary: Optional[str] = None

    @property
    def clarify(self) -> bool:
        return self.work_type == "CLARIFY" or self.confidence < CLARIFY_THRESHOLD

    @property
    def crisis(self) -> bool:
        return self.work_type == "CRISIS"


def is_crisis(text: str) -> bool:
    # Either kind of emergency halts: a shop PHYSICAL-injury cry (local list) OR the kernel's PASTORAL
    # crisis (concordance.ask.is_crisis — a different, narrower notion). OR, never defer to one.
    t = (text or "").lower()
    if any(w in t for w in _LOCAL_CRISIS):
        return True
    if _kernel_is_crisis is not None:
        try:
            return bool(_kernel_is_crisis(text))
        except Exception:  # noqa: BLE001 — a matcher error must never suppress a cry for help
            pass
    return False


def _hits(text: str, table) -> list:
    return [t for t in TYPES if t != "CRISIS" and any(k in text for k in table.get(t, ()))]


def classify(request: str) -> Classification:
    """Return the primary work type and a confidence. CRISIS first; unknown/weak -> CLARIFY."""
    text = (request or "").lower()
    if is_crisis(request):
        return Classification("CRISIS", 1.0, "crisis language — halt autonomous action and surface to a human")

    strong = _hits(text, _STRONG)
    if strong:
        scored = [(t, 0.9) for t in strong]
    else:
        weak = _hits(text, _WEAK)
        if not weak:
            return Classification("CLARIFY", 0.0, "no recognizable shop-work pattern — ask the requester")
        scored = [(t, 0.62) for t in weak]

    scored.sort(key=lambda ts: (-ts[1], _PRIORITY.index(ts[0]) if ts[0] in _PRIORITY else 99))
    primary, conf = scored[0]
    secondary = scored[1][0] if len(scored) > 1 and scored[1][1] == conf else None
    # Below the threshold the DISPOSITION is CLARIFY (ask, don't guess) — the weak guess is kept.
    if conf < CLARIFY_THRESHOLD:
        return Classification("CLARIFY", conf, f"weak signal — best guess {primary}", primary)
    note = f"compound — also {secondary}" if secondary else ""
    return Classification(primary, conf, note, secondary)


def run_benchmark(cases) -> dict:
    """Score the classifier against labeled cases [{text, primary}]. 100% is the ship gate (SOP-02).

    A miss is the classifier's fault, never the label's (unless Matt rules the label wrong, SOP-12).
    Returns {n, correct, accuracy, misses:[{text, expected, got}]}.
    """
    misses = []
    for c in cases:
        got = classify(c["text"]).work_type
        if got != c["primary"]:
            misses.append({"text": c["text"], "expected": c["primary"], "got": got})
    n = len(cases)
    correct = n - len(misses)
    return {"n": n, "correct": correct, "accuracy": (correct / n if n else 0.0), "misses": misses}
