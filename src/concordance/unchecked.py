"""UNCHECKED — what the engine writes goes in, carrying its open question, and the first reader to
reach for it is asked to close it.

Matt, 2026-08-01: *"We put them in, when you write, but you ask the first person that recalls the
cards to verify them."*

That settles a question this project had been answering badly in both directions. Holding engine-
written cards out of the library until a steward reviewed them built a queue nobody drains — the
cards helped no one while they waited, and "waiting for review" quietly becomes "never". Putting
them in silently would be worse: an unchecked card wearing the same face as a checked one is the
precise failure the whole keeping exists to prevent.

So the card goes IN, and it goes in **wearing its question**. Anyone may read it, everyone can see
it has not been checked, and the first person who actually reaches for it is asked once. The work
lands on the one person who has already shown they care about this card — by recalling it — rather
than on a steward staring at a queue of things nobody wanted.

WHAT WE ASK A HUMAN IS NOT WHAT A MACHINE CAN ALREADY ANSWER, and getting that wrong would waste
the single question we get. `craft.verify_spans` re-reads the source and proves the body is
byte-for-byte what it claims — continuously, for free, and better than a person could. Asking
someone to confirm that is asking them to do a hash's job. The question only a person can answer
is whether the passage was cut FAIRLY and labelled TRUTHFULLY: whether this is what the source is
actually saying, or a sentence wrenched out of the argument it lived in.

ONE READER IS A CHECK, NOT A PROOF. The rule attest.py already holds for signatures (Deuteronomy
19:15; Matthew 18:16; 2 Corinthians 13:1) applies just as well to a plain answer: record who said
what, report the count, and never repaint a card as "verified" on one anonymous click.
`checked_by: 1` is true and worth having; "verified" would be a lie told in the reader's favour.

A SINGLE "WRONG" NEVER ERASES ANYTHING. One anonymous verdict with the power to delete is a
vandalism vector wearing the clothes of diligence. A dispute marks the card disputed — visible to
the next reader, raised to a steward — and the card stays where a person can judge it. Removal is
a steward's act with a name on it, exactly as retraction already is.

No account, no key, no sign-in: the covenant says the tool is free and asks nobody to register, so
this has to work for someone entirely anonymous. Where a reader DOES carry an identity their answer
can be signed, and that lands in `attest.py` as a real witness — the strong case rides on the
mechanism that already exists rather than a second one built beside it.

NAMED FOR THE STATE, not the ceremony. `recall.py` is already the module for cards landing and
earning usefulness; `attest.py` is already cryptographic witness. This is the third thing: the
plain fact that nobody has looked at this yet, and what we do about it.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()

# The mark an engine-written card carries until a person has looked at it.
MARK = "awaiting_check"

HOLDS, WRONG, UNSURE = "holds", "wrong", "unsure"
VERDICTS = (HOLDS, WRONG, UNSURE)

# Said to the reader, in the reader's own language, every time a count is reported.
NOTE = ("One reader is a check, not a proof — at the mouth of two or three witnesses a matter is "
        "established (Deuteronomy 19:15).")

QUESTION = ("This was cut from the source below by the engine — selected, not written. Does the "
            "passage fairly represent what the source says, and does the title describe it "
            "truthfully?")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "unchecked.jsonl"


# ── the mark ──────────────────────────────────────────────────────────────────────────────────
def mark(card: Dict[str, Any]) -> Dict[str, Any]:
    """Stamp a card the ENGINE wrote. Mutates and returns it, as the minting paths expect.

    Applied AT THE MINT rather than at the write, so there is no path by which an engine-written
    card reaches a store with its question missing.
    """
    if not isinstance(card, dict):
        return card
    card.setdefault("extra", {})[MARK] = True
    return card


def is_open(card: Dict[str, Any]) -> bool:
    """True while this card still carries a question no person has answered."""
    if not isinstance(card, dict):
        return False
    return bool((card.get("extra") or {}).get(MARK))


# ── the ask, PURE ─────────────────────────────────────────────────────────────────────────────
def question(card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The ask to put in front of a reader, derived FROM THE CARD ALONE. No I/O.

    Purity is a contract, not a preference: this is called from `present.derive`, which promises
    to be free, cacheable and side-effect-free (tests/test_present.py). Counting answers means
    reading the log, so that belongs to the caller who is already doing I/O — a route — never here.
    """
    if not is_open(card):
        return None
    cid = str(card.get("id") or "")
    extra = card.get("extra") or {}
    src = card.get("source") or {}
    return {
        "open": True,
        "headline": "No one has checked this card yet.",
        "question": QUESTION,
        "source": {"label": src.get("label", ""), "url": src.get("url", ""),
                   "sha256": extra.get("source_sha256", ""), "span": extra.get("span")},
        "answers": {v: f"/unchecked/answer?card={cid}&verdict={v}" for v in VERDICTS},
        "note": NOTE,
    }


# ── the store: append-only events, folded on read ─────────────────────────────────────────────
def _events() -> List[Dict[str, Any]]:
    p = _path()
    if not p.is_file():
        return []
    out: List[Dict[str, Any]] = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue          # a bad line is skipped; it is never fatal and never a "pass"
    except OSError:
        return []
    return out


def _append(rec: Dict[str, Any]) -> bool:
    p = _path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK, open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def state_of(card_id: str) -> Dict[str, Any]:
    """Fold the log for one card: when it was first recalled, and every answer since."""
    cid = str(card_id or "")
    first: Optional[int] = None
    answers: List[Dict[str, Any]] = []
    for e in _events():
        if e.get("card_id") != cid:
            continue
        if e.get("event") == "recalled" and first is None:
            first = e.get("at")
        elif e.get("event") == "answered":
            answers.append(e)
    holds = sum(1 for a in answers if a.get("verdict") == HOLDS)
    wrong = sum(1 for a in answers if a.get("verdict") == WRONG)
    return {"card_id": cid, "first_recalled_at": first, "answers": answers,
            "checked_by": holds, "disputed_by": wrong,
            "asked": first is not None, "answered": bool(answers), "disputed": wrong > 0}


def note_recall(card_ids, reader: str = "") -> Dict[str, Any]:
    """Record that these cards were recalled. The FIRST recall is what puts the question to a
    person; later ones are counted and change nothing.

    Never raises and never blocks a read. A library that fails to serve a card because it could not
    append a log line has its priorities backwards.
    """
    ids = [str(c) for c in (card_ids or []) if str(c or "").strip()]
    if not ids:
        return {"asked": [], "already": []}
    now = int(time.time())
    asked, already = [], []
    for cid in ids:
        if state_of(cid)["asked"]:
            already.append(cid)
            continue
        if _append({"event": "recalled", "card_id": cid, "at": now,
                    "reader": str(reader or "")[:64]}):
            asked.append(cid)
    return {"asked": asked, "already": already}


def answer(card_id: str, verdict: str, by: str = "", note: str = "",
           attestation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Record one reader's verdict. Anonymous is allowed; signed is better and is kept as such."""
    cid = str(card_id or "").strip()
    v = str(verdict or "").strip().lower()
    if not cid:
        return {"ok": False, "reason": "no card named"}
    if v not in VERDICTS:
        return {"ok": False, "reason": "verdict must be one of " + ", ".join(VERDICTS)}

    rec: Dict[str, Any] = {"event": "answered", "card_id": cid, "verdict": v,
                           "at": int(time.time()), "by": str(by or "")[:64],
                           "note": str(note or "")[:500]}

    # A SIGNED answer is a real witness, so it goes where witnesses already live rather than being
    # reimplemented here. An unsigned answer is still recorded — it is simply worth less, and we
    # say which is which instead of quietly treating them alike.
    if attestation:
        try:
            from . import attest
            rec["witnessed"] = bool(attest.bear_witness(cid, attestation).get("ok"))
        except Exception:  # noqa: BLE001 — a failed signature never discards the plain answer
            rec["witnessed"] = False

    if not _append(rec):
        return {"ok": False, "reason": "could not record the answer"}

    st = state_of(cid)
    if v == WRONG:
        msg = ("Recorded, and this card is now marked disputed — a steward will look at it. It "
               "stays where a person can judge it, because one verdict must not erase a card.")
    else:
        msg = f"Recorded. Checked by {st['checked_by']} reader(s). {NOTE}"
    return {"ok": True, "card_id": cid, "verdict": v, "checked_by": st["checked_by"],
            "disputed_by": st["disputed_by"], "disputed": st["disputed"],
            "note": NOTE, "message": msg}


def standing(limit: int = 100) -> Dict[str, Any]:
    """What is still outstanding — asked and unanswered, and what is disputed.

    Reports what it MEASURED OVER, because a count of open questions means nothing without knowing
    how many cards were seen at all (the coverage rule this project already holds).
    """
    per: Dict[str, Dict[str, Any]] = {}
    for e in _events():
        cid = e.get("card_id")
        if not cid:
            continue
        d = per.setdefault(cid, {"recalled": False, "answers": []})
        if e.get("event") == "recalled":
            d["recalled"] = True
        elif e.get("event") == "answered":
            d["answers"].append(e)

    open_ids = [c for c, d in per.items() if d["recalled"] and not d["answers"]]
    disputed = [c for c, d in per.items()
                if any(a.get("verdict") == WRONG for a in d["answers"])]
    checked = [c for c, d in per.items()
               if any(a.get("verdict") == HOLDS for a in d["answers"])]
    return {"cards_seen": len(per), "asked_and_open": len(open_ids), "checked": len(checked),
            "disputed": len(disputed), "open_ids": open_ids[:max(1, int(limit))],
            "disputed_ids": disputed[:max(1, int(limit))], "note": NOTE}


__all__ = ["mark", "is_open", "question", "note_recall", "answer", "standing", "state_of",
           "MARK", "VERDICTS", "HOLDS", "WRONG", "UNSURE", "NOTE", "QUESTION"]
