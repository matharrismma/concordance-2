"""The moderation floor — report and block, before any public community. Never auto-judged.

Contract §6 item 4: "Import/community quarantine + a minimal moderation floor (report/block)
before any public community." The floor is deliberately minimal and deliberately honest, and it
reuses the house's own witness doctrine (Deuteronomy 19:15) instead of inventing a new court:

  * ONE report is a claim. It hides nothing, and it is never discarded.
  * THREE distinct reporters HOLD the item for review — quarantined from public reads, not
    deleted, not judged. The word shown is "held for review", because that is what is true.
  * Judgement belongs to a human steward, never to the counter. The counter only decides when a
    human must look.
  * BLOCK is viewer-side and sovereign: blocking a handle filters what YOU see. It is not a
    verdict on them, it is a boundary of yours — so it needs no threshold, no review, and no
    appeal. Your eyes are your own.

Stores are data-only (reports.jsonl, blocks.jsonl under the data dir), append-only, re-read
fresh on every call — this is a floor, not a scale.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HOLD_AT = 3          # distinct reporters that HOLD an item for human review (Deut 19:15)
REASONS = ("harmful", "spam", "impersonation", "false_teaching_claim", "private_info", "other")

_KINDS = ("group_contribution", "mesh_message", "door_note")


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "moderation"


def _append(name: str, rec: Dict[str, Any]) -> None:
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(name: str) -> List[Dict[str, Any]]:
    p = _dir() / name
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out


def report(kind: str, target_id: str, reason: str, reporter: str,
           note: str = "") -> Dict[str, Any]:
    """File a report. Anyone may report; nobody's report is a verdict. The same reporter
    repeating themselves stays ONE witness — the mesh's own rule."""
    kind = (kind or "").strip()
    if kind not in _KINDS:
        return {"ok": False, "error": f"kind must be one of {_KINDS}"}
    if not (target_id or "").strip() or not (reporter or "").strip():
        return {"ok": False, "error": "target_id and reporter are both required"}
    reason = (reason or "other").strip()
    if reason not in REASONS:
        reason = "other"
    _append("reports.jsonl", {"kind": kind, "target_id": target_id.strip(),
                              "reason": reason, "reporter": reporter.strip(),
                              "note": (note or "")[:500], "at": int(time.time())})
    st = status(kind, target_id)
    return {"ok": True, **st,
            "note": ("Received. One report is a claim, never a verdict; at "
                     f"{HOLD_AT} distinct reporters the item is held for a human steward's review.")}


def status(kind: str, target_id: str) -> Dict[str, Any]:
    """The item's standing: how many DISTINCT witnesses, and whether it is held for review."""
    reporters = {r["reporter"] for r in _read("reports.jsonl")
                 if r.get("kind") == kind and r.get("target_id") == target_id}
    resolved = [r for r in _read("resolutions.jsonl")
                if r.get("kind") == kind and r.get("target_id") == target_id]
    verdict = resolved[-1]["action"] if resolved else None
    held = verdict is None and len(reporters) >= HOLD_AT
    return {"kind": kind, "target_id": target_id, "reporters": len(reporters),
            "held_for_review": held, "steward_action": verdict,
            "means": ("held_for_review means quarantined from public reads pending a HUMAN "
                      "steward — the counter never judges, it only decides when a person must look")}


def held(kind: str, target_id: str) -> bool:
    """The one-line check a public read path calls: should this item be withheld right now?
    A steward's 'restore' beats the counter; a steward's 'remove' is final until changed."""
    st = status(kind, target_id)
    if st["steward_action"] == "remove":
        return True
    if st["steward_action"] == "restore":
        return False
    return st["held_for_review"]


def resolve(kind: str, target_id: str, action: str, steward: str, note: str = "") -> Dict[str, Any]:
    """A human steward's decision — restore (visible again, reports stand recorded) or remove.
    Recorded, attributed, reversible by a later resolution. The floor never forgets who decided."""
    if action not in ("restore", "remove"):
        return {"ok": False, "error": "action must be restore or remove"}
    if not (steward or "").strip():
        return {"ok": False, "error": "a resolution carries its steward's name — no anonymous judgement"}
    _append("resolutions.jsonl", {"kind": kind, "target_id": target_id, "action": action,
                                  "steward": steward.strip(), "note": (note or "")[:500],
                                  "at": int(time.time())})
    return {"ok": True, **status(kind, target_id)}


def review_queue() -> Dict[str, Any]:
    """Everything currently held and waiting on a human — the steward's inbox."""
    by_target: Dict[tuple, set] = {}
    for r in _read("reports.jsonl"):
        by_target.setdefault((r.get("kind"), r.get("target_id")), set()).add(r.get("reporter"))
    items = []
    for (kind, tid), reps in sorted(by_target.items()):
        st = status(kind, tid)
        if st["held_for_review"]:
            items.append({"kind": kind, "target_id": tid, "reporters": len(reps)})
    return {"held": items, "count": len(items), "hold_at": HOLD_AT}


# ── Block: a viewer's own boundary, sovereign and threshold-free ────────────────────────────────

def block(viewer: str, blocked_handle: str) -> Dict[str, Any]:
    if not (viewer or "").strip() or not (blocked_handle or "").strip():
        return {"ok": False, "error": "viewer and blocked_handle are both required"}
    _append("blocks.jsonl", {"viewer": viewer.strip(), "blocked": blocked_handle.strip(),
                             "at": int(time.time()), "on": True})
    return {"ok": True, "blocked": blocked_handle.strip(),
            "note": "This filters what YOU see. It is a boundary of yours, not a verdict on them."}


def unblock(viewer: str, blocked_handle: str) -> Dict[str, Any]:
    _append("blocks.jsonl", {"viewer": (viewer or "").strip(), "blocked": (blocked_handle or "").strip(),
                             "at": int(time.time()), "on": False})
    return {"ok": True, "unblocked": (blocked_handle or "").strip()}


def blocked_by(viewer: str) -> set:
    """The viewer's current block list — last write per handle wins."""
    state: Dict[str, bool] = {}
    for r in _read("blocks.jsonl"):
        if r.get("viewer") == (viewer or "").strip():
            state[r.get("blocked")] = bool(r.get("on"))
    return {h for h, on in state.items() if on}


def filter_for(viewer: Optional[str], items: List[Dict[str, Any]],
               handle_key: str = "handle") -> List[Dict[str, Any]]:
    """Apply a viewer's block list to a list of items. No viewer → nothing filtered (public
    reads stay public; blocking is personal, not global)."""
    if not viewer:
        return items
    hidden = blocked_by(viewer)
    if not hidden:
        return items
    return [it for it in items if (it.get(handle_key) or "") not in hidden]


__all__ = ["report", "status", "held", "resolve", "review_queue",
           "block", "unblock", "blocked_by", "filter_for", "HOLD_AT", "REASONS"]
