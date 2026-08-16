"""THE PLAYBOOK — the Body's shared memory of faithful obedience. "Canon commands, Playbook remembers."

Matt's Fractal Playbook (01_fractal_playbook.md): the Playbook is NOT Scripture. It cannot create
doctrine or bind conscience. It is the testimony of what the Body did in obedience to the Head, what
came of it, and what was corrected — so wisdom compounds *without becoming doctrine*.

Until now this lived only as read-only teaching cards. This module makes the atomic **Entry** a real,
writable object — the "Playbook remembers" half, standing beside the gate kernel ("Canon commands").
Each Entry carries the seven fields of the fractal unit:

    1. CONFESSION   the humility key — "I may be wrong. I acted in faith according to [anchors]."
                    Required. It is what keeps a testimony from hardening into authority.
    2. ANCHORS      the Scripture refs the action was taken under (≥1).
    3. ACTION       one of OPEN / BUILD / RESERVE / PRUNE / HOLD.
    4. OUTCOME      the fruit, recorded LATER, after it is seen: fruit / mixed / failed.
    5. WITNESSES    brothers who affirm the alignment (≥2 to confirm; never the author — Deut 19:15).
    6. WAIT         a real waiting period before confirmation (no rushing — the GOD gate).
    7. STATUS       quarantine → confirmed / rejected / pruned. Derived, never asserted.

THE FOUR GATES ARE THE KERNEL'S. Confirmation is not re-implemented here — it is routed through
`kernel.gate()`: an Entry is `community` (born quarantined), and reaches CONFIRMED only when ≥2
INDEPENDENT brothers affirm (the evidence of alignment) AND the wait has elapsed — witness ≠ author,
never self-confirm. A confirmed Entry is *confirmed testimony*, affirmed by the Body — it is NOT
Scripture and never becomes doctrine. An entry can be PRUNED (John 15:2): failure is not hidden, it
is used to refine faithfulness.

Signed like every member write (shelves / consent / moderation): the member signs canonical bytes on
their own device and sends only the detached signature; the key never travels. Append-only —
a correction or an outcome or a pruning is a NEW event; the trail of a person learning stays whole.

Store: `data/playbook/entries.jsonl` + `events.jsonl`, append-only, re-read fresh. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ACTIONS = ("OPEN", "BUILD", "RESERVE", "PRUNE", "HOLD")   # the minimal action set (the primer)
OUTCOMES = ("fruit", "mixed", "failed")                   # the fruit, seen after the fact (Mt 12:33)
EVENT_TYPES = ("witness", "outcome", "prune")
REQUIRED_WITNESSES = 2                                     # "two or three witnesses" (Deut 19:15)
DEFAULT_WAIT_S = 86400                                     # a real wait — one day, not the demo hour
MIN_WAIT_S = 3600                                          # never shorter than an hour
SIGNATURE_TTL_S = 900                                     # a signed payload is good for 15 minutes
MAX_CONFESSION = 2000
MAX_BODY = 20000

# The canonical bytes of a CREATE, and of each EVENT — sorted-key JSON, the same discipline shelves
# and consent use. Empty-but-present keeps one canonicalisation for every shape.
_ENTRY_FIELDS = ("action", "anchors", "at", "author", "body", "confession", "nonce", "situation", "wait_seconds")
_WITNESS_FIELDS = ("affirms", "at", "entry_id", "note", "witness")
_OUTCOME_FIELDS = ("at", "by", "entry_id", "note", "outcome")
_PRUNE_FIELDS = ("at", "by", "entry_id", "reason")
_SLUG = re.compile(r"[^a-z0-9]+")

# The one honest authority tier for member testimony — never raised by confirmation, popularity, or a
# steward. A CONFIRMED entry is affirmed BY THE BODY; it is not the library's verified claim.
MEMBER_TIER = "member"


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "playbook"


def _append(name: str, rec: Dict[str, Any]) -> None:
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(name: str) -> List[Dict[str, Any]]:
    p = _dir() / name
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out


def _canon(fields: Dict[str, Any], keys) -> bytes:
    return json.dumps({k: fields.get(k) for k in keys}, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _slug(s: Any, limit: int = 24) -> str:
    return _SLUG.sub("-", str(s or "").lower()).strip("-")[:limit]


def _fresh(at: Any) -> bool:
    try:
        at = int(at or 0)
    except (TypeError, ValueError):
        return False
    now = int(time.time())
    return now - SIGNATURE_TTL_S <= at <= now + 300


def _verify(fields: Optional[Dict[str, Any]], signature: str, keys, signer_key: str) -> Dict[str, Any]:
    """Verify a detached signature over the canonical bytes of `keys`, signed by `signer_key`."""
    if not isinstance(fields, dict) or not isinstance(signature, str) or not signature.strip():
        return {"ok": False, "error": "signed fields and a signature are required — call the "
                                      "matching signable_* first and sign those exact bytes"}
    if "private_key" in fields:
        return {"ok": False, "error": "a detached signature is required — never a private key"}
    missing = [k for k in keys if k not in fields]
    if missing:
        return {"ok": False, "error": f"the signed fields must carry {list(keys)}; missing {missing}"}
    if not _fresh(fields.get("at")):
        return {"ok": False, "error": "these signed bytes are stale — sign a fresh set"}
    signer = str(fields.get(signer_key) or "").strip()
    if not signer:
        return {"ok": False, "error": f"the signed bytes carry no {signer_key} key"}
    from . import signing
    if not signing.verify_bytes(_canon(fields, keys), signature.strip(), signer):
        return {"ok": False, "error": "that signature does not verify against the named key"}
    return {"ok": True, "signer": signer}


# ── create ──────────────────────────────────────────────────────────────────────────────────────
def signable_entry(author: str, confession: str, anchors: List[str], action: str,
                   situation: str = "", body: str = "", wait_seconds: int = DEFAULT_WAIT_S) -> Dict[str, Any]:
    """Step 1: the canonical bytes of a new Playbook Entry, ready to sign ON THE DEVICE. The server
    mints the nonce and the clock so the stored entry and the signed bytes cannot drift."""
    author = (author or "").strip()
    action = (action or "").strip().upper()
    confession = (confession or "").strip()
    anchors = [str(a).strip() for a in (anchors or []) if str(a).strip()]
    if not author:
        return {"ok": False, "error": "an entry needs the member's public key — a testimony belongs "
                                      "to a key, not to an account"}
    if not confession:
        return {"ok": False, "error": "the CONFESSION is required — 'I may be wrong. I acted in faith "
                                      "according to [refs].' It is the humility that keeps a testimony "
                                      "from becoming authority."}
    if not anchors:
        return {"ok": False, "error": "at least one Scripture ANCHOR is required — the word the action "
                                      "was taken under"}
    if action not in ACTIONS:
        return {"ok": False, "error": f"action must be one of {list(ACTIONS)} — the minimal set"}
    try:
        wait_seconds = max(MIN_WAIT_S, int(wait_seconds or DEFAULT_WAIT_S))
    except (TypeError, ValueError):
        wait_seconds = DEFAULT_WAIT_S
    fields = {
        "author": author, "confession": confession[:MAX_CONFESSION], "anchors": anchors,
        "action": action, "situation": (situation or "").strip()[:180],
        "body": (body or "").strip()[:MAX_BODY], "wait_seconds": wait_seconds,
        "at": int(time.time()), "nonce": secrets.token_hex(8),
    }
    return {"ok": True, "signable": fields, "bytes": _canon(fields, _ENTRY_FIELDS).decode("utf-8"),
            "note": "Sign these exact bytes with your key, then POST them with the signature."}


def record(fields: Optional[Dict[str, Any]] = None, signature: str = "",
           display_name: str = "") -> Dict[str, Any]:
    """Step 2: verify the member's signature over those exact bytes, and enter the testimony — born
    QUARANTINE, at the member tier, with the nine-field gate record stamped beside it."""
    v = _verify(fields, signature, _ENTRY_FIELDS, "author")
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    f = dict(fields or {})
    author = v["signer"]
    entry_id = f"pbk_{_slug(author)}_{f['nonce']}"
    entry = {
        "id": entry_id, "author": author, "display_name": (display_name or "").strip()[:80],
        "confession": f["confession"], "anchors": list(f["anchors"]), "action": f["action"],
        "situation": f.get("situation") or "", "body": f.get("body") or "",
        "created_at": int(f["at"]), "wait_seconds": int(f["wait_seconds"]),
        "signature": signature.strip(), "kind": "community", "authority_tier": MEMBER_TIER,
        "generated": False,
    }
    # THE GATE KERNEL — a testimony is the member's own community contribution: born quarantined, no
    # verification yet (no witnesses, no wait). The kernel returns QUARANTINE, stamped as the shared
    # record. It reaches CONFIRMED only later, when the Body affirms and the wait elapses (see _decide).
    from . import kernel as _kernel
    grec = _kernel.gate(entry, entered_as=entry_id, kind_hint="community",
                        authority_in="quarantined", author=author, in_kind_checked=True,
                        assumptions=("a member's own confessed testimony — born quarantined until "
                                     "witnessed and waited",))
    entry["gate_record"] = grec.to_dict()
    _append("entries.jsonl", entry)
    return {"ok": True, "entry_id": entry_id, "status": "quarantine", "record": grec.to_dict(),
            "note": ("Entered, signed by your key. It waits in QUARANTINE — the Body's affirmation "
                     "(two witnesses) and the waiting period must land before it is confirmed "
                     "testimony. Confession keeps it humble; it never becomes Scripture."),
            "confirm_needs": {"witnesses": REQUIRED_WITNESSES, "wait_seconds": entry["wait_seconds"]}}


# ── events: witness · outcome · prune ─────────────────────────────────────────────────────────────
def signable_witness(witness: str, entry_id: str, affirms: bool = True, note: str = "") -> Dict[str, Any]:
    if not (witness or "").strip() or not (entry_id or "").strip():
        return {"ok": False, "error": "witness key and entry_id are required"}
    fields = {"witness": witness.strip(), "entry_id": entry_id.strip(), "affirms": bool(affirms),
              "note": (note or "").strip()[:280], "at": int(time.time())}
    return {"ok": True, "signable": fields, "bytes": _canon(fields, _WITNESS_FIELDS).decode("utf-8")}


def add_witness(fields: Optional[Dict[str, Any]] = None, signature: str = "") -> Dict[str, Any]:
    """A brother signs an affirmation (or a dissent) over an entry. Witness ≠ author is enforced
    when the status is folded (Deut 19:15 / never self-confirm)."""
    v = _verify(fields, signature, _WITNESS_FIELDS, "witness")
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    f = dict(fields or {})
    entry = get(str(f["entry_id"]))
    if not entry.get("ok"):
        return {"ok": False, "error": "no such entry"}
    if v["signer"] == entry["entry"]["author"]:
        return {"ok": False, "error": "the author cannot witness their own testimony — a confirmation "
                                      "needs OTHER brothers (Deut 19:15)"}
    _append("events.jsonl", {"type": "witness", "entry_id": f["entry_id"], "witness": v["signer"],
                             "affirms": bool(f.get("affirms")), "note": f.get("note") or "",
                             "at": int(f["at"]), "signature": signature.strip()})
    return {"ok": True, **get(str(f["entry_id"])).get("entry", {})}


def signable_outcome(by: str, entry_id: str, outcome: str, note: str = "") -> Dict[str, Any]:
    outcome = (outcome or "").strip().lower()
    if outcome not in OUTCOMES:
        return {"ok": False, "error": f"outcome must be one of {list(OUTCOMES)} — the fruit, as seen"}
    if not (by or "").strip() or not (entry_id or "").strip():
        return {"ok": False, "error": "signer key and entry_id are required"}
    fields = {"by": by.strip(), "entry_id": entry_id.strip(), "outcome": outcome,
              "note": (note or "").strip()[:280], "at": int(time.time())}
    return {"ok": True, "signable": fields, "bytes": _canon(fields, _OUTCOME_FIELDS).decode("utf-8")}


def add_outcome(fields: Optional[Dict[str, Any]] = None, signature: str = "") -> Dict[str, Any]:
    """Record the fruit, after it is seen — fruit / mixed / failed. This is the load-bearing act: a
    testimony with no recorded outcome can never be pruned by its fruit (Matthew 12:33)."""
    v = _verify(fields, signature, _OUTCOME_FIELDS, "by")
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    f = dict(fields or {})
    if str(f.get("outcome")) not in OUTCOMES:
        return {"ok": False, "error": f"outcome must be one of {list(OUTCOMES)}"}
    if not get(str(f["entry_id"])).get("ok"):
        return {"ok": False, "error": "no such entry"}
    _append("events.jsonl", {"type": "outcome", "entry_id": f["entry_id"], "by": v["signer"],
                             "outcome": str(f["outcome"]), "note": f.get("note") or "",
                             "at": int(f["at"]), "signature": signature.strip()})
    return {"ok": True, **get(str(f["entry_id"])).get("entry", {})}


def signable_prune(by: str, entry_id: str, reason: str = "") -> Dict[str, Any]:
    if not (by or "").strip() or not (entry_id or "").strip():
        return {"ok": False, "error": "signer key and entry_id are required"}
    fields = {"by": by.strip(), "entry_id": entry_id.strip(), "reason": (reason or "").strip()[:280],
              "at": int(time.time())}
    return {"ok": True, "signable": fields, "bytes": _canon(fields, _PRUNE_FIELDS).decode("utf-8")}


def prune(fields: Optional[Dict[str, Any]] = None, signature: str = "") -> Dict[str, Any]:
    """Remove what bears no fruit (John 15:2). Only the author may prune their own testimony; failure
    is not deleted, it is marked — the trail stays whole so faithfulness can be refined."""
    v = _verify(fields, signature, _PRUNE_FIELDS, "by")
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    f = dict(fields or {})
    got = get(str(f["entry_id"]))
    if not got.get("ok"):
        return {"ok": False, "error": "no such entry"}
    if v["signer"] != got["entry"]["author"]:
        return {"ok": False, "error": "only the author may prune their own testimony"}
    _append("events.jsonl", {"type": "prune", "entry_id": f["entry_id"], "by": v["signer"],
                             "reason": f.get("reason") or "", "at": int(f["at"]),
                             "signature": signature.strip()})
    return {"ok": True, **get(str(f["entry_id"])).get("entry", {})}


# ── fold + decide (pure) ──────────────────────────────────────────────────────────────────────────
def _decide(entry: Dict[str, Any], events: List[Dict[str, Any]], now: Optional[int] = None) -> Dict[str, Any]:
    """Fold an entry's events into its current, DERIVED state and route the four gates through the
    kernel. Pure — pass events directly; no I/O. Status is never asserted, only computed."""
    now = int(time.time()) if now is None else int(now)
    author = entry.get("author")
    affirmers, dissenters, pruned, outcome = set(), set(), False, None
    for e in events:
        if e.get("entry_id") != entry.get("id"):
            continue
        t = e.get("type")
        if t == "witness" and e.get("witness") and e["witness"] != author:   # never self-confirm
            (affirmers if e.get("affirms") else dissenters).add(e["witness"])
        elif t == "outcome" and e.get("outcome") in OUTCOMES:
            outcome = {"outcome": e["outcome"], "note": e.get("note") or "", "by": e.get("by"), "at": e.get("at")}
        elif t == "prune":
            pruned = True
    affirming = affirmers - dissenters
    witnessed = len(affirming) >= REQUIRED_WITNESSES
    waited = (now - int(entry.get("created_at") or 0)) >= int(entry.get("wait_seconds") or DEFAULT_WAIT_S)

    from . import kernel as _kernel
    grec = _kernel.gate(
        {"authority_tier": MEMBER_TIER, "id": entry.get("id"), "claim": entry.get("situation") or entry.get("confession")},
        entered_as=entry.get("id") or "entry", kind_hint="community", authority_in="quarantined",
        author=author,
        # the affirmation of ≥2 independent brothers IS the evidence that this obedience aligned;
        # a lone or absent witness leaves it quarantined (never self-confirmed).
        evidence="HOLDS" if witnessed else None,
        witness=(sorted(affirming)[0] if witnessed else None),
        retracted=pruned,                     # a pruned testimony fails the floor → REJECT verdict
        wait_satisfied=waited, in_kind_checked=True,
    )
    status = "pruned" if pruned else grec.verdict.lower()   # quarantine / confirmed / reject(ed)
    if status == "reject":
        status = "rejected"
    return {
        "status": status, "affirming_witnesses": sorted(affirming), "dissenters": sorted(dissenters),
        "witness_count": len(affirming), "witnessed": witnessed, "waited": waited,
        "wait_remaining_s": max(0, int(entry.get("wait_seconds") or 0) - (now - int(entry.get("created_at") or 0))),
        "outcome": outcome, "pruned": pruned, "gate_record": grec.to_dict(),
    }


def get(entry_id: str) -> Dict[str, Any]:
    entry_id = (entry_id or "").strip()
    entry = next((e for e in reversed(_read("entries.jsonl")) if e.get("id") == entry_id), None)
    if not entry:
        return {"ok": False, "error": "no such entry"}
    state = _decide(entry, _read("events.jsonl"))
    view = {k: entry.get(k) for k in ("id", "author", "display_name", "confession", "anchors",
                                      "action", "situation", "body", "created_at", "wait_seconds")}
    view.update(state)
    view["is_scripture"] = False
    view["note"] = "Confirmed testimony is affirmed BY THE BODY — the Playbook remembers; it is not Scripture and binds no conscience."
    return {"ok": True, "entry": view}


def list_entries(status: str = "", author: str = "", limit: int = 50) -> Dict[str, Any]:
    """The playbook, newest first. `status` filters to quarantine/confirmed/rejected/pruned."""
    status, author = (status or "").strip().lower(), (author or "").strip()
    events = _read("events.jsonl")
    out: List[Dict[str, Any]] = []
    seen = set()
    for entry in reversed(_read("entries.jsonl")):
        eid = entry.get("id")
        if eid in seen:
            continue
        seen.add(eid)
        if author and entry.get("author") != author:
            continue
        st = _decide(entry, events)
        if status and st["status"] != status:
            continue
        out.append({"id": eid, "action": entry.get("action"), "situation": entry.get("situation"),
                    "anchors": entry.get("anchors"), "display_name": entry.get("display_name"),
                    "status": st["status"], "witness_count": st["witness_count"],
                    "outcome": (st["outcome"] or {}).get("outcome"),
                    "created_at": entry.get("created_at")})
        if len(out) >= max(1, min(limit, 200)):
            break
    return {"ok": True, "count": len(out), "entries": out,
            "note": "The Playbook remembers faithful obedience — testimony, not doctrine. Canon commands."}
