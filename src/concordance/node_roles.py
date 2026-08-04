"""NODE BY CHOICE — reader, carrier, node. Every tier is opt-in; the center stays small.

Task #103: DISTRIBUTED — airlock intake (path-not-payload, already in airlock.py) + corpus node
roles. This is the roles half.

Matt, 2026-08-01: readers become carriers become nodes BY CHOICE, never by default — and nodes
act as CAPACITORS, holding charge (shards) close to the people who need it so the center never
has to grow. Two-tier distribution: cards spread cheap; sources anchor on drives, and the
waybill (origin + sha256) means you can heal a copy from what you already hold.

THE THREE ROLES, DECLARED IN CODE. Runtime structure lives in a tracked file, not a data blob a
fresh box would be missing:

  reader   — the default, and the only role nobody has to choose. Uses the library; holds
             nothing beyond their own device's cache; owes nothing.
  carrier  — CHOSE to hold shard files (the frozen corpus tiers) on their own disk or drive.
             A capacitor: the charge travels with them, offline, and each held file carries its
             sha256 so a damaged copy is detected and healed from any peer holding the same hash.
  node     — CHOSE to serve the shards they hold to peers around them. A carrier with a door
             open. Serving is a separate consent from holding — carrying a drive to a friend
             must never silently make your machine a server.

OPT-IN IS A WRITTEN CHOICE. The role is read from a small record the person's own action wrote;
the ABSENCE of that record means reader. Nothing here upgrades anyone: there is no code path
from reader to carrier that does not pass through choose(), and choose() only ever runs because
a person asked. A typed name is not authority — but a role is not an authority claim, it is a
statement of what this installation has agreed to hold and serve, verifiable against the disk:
hold_manifest() reports what is ACTUALLY held, so a claimed carrier with an empty shard dir is
visible as exactly that.

Sovereign: stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROLES: Dict[str, Dict[str, str]] = {
    "reader": {
        "holds": "nothing beyond the device's own cache",
        "serves": "nobody — and owes nobody anything",
        "chosen_by": "nobody; reader is the absence of a choice, never a downgrade",
    },
    "carrier": {
        "holds": "shard files (frozen corpus tiers) on the person's own disk or drive",
        "serves": "nobody over the wire; the charge travels physically, offline",
        "chosen_by": "an explicit choose('carrier') by the person",
    },
    "node": {
        "holds": "everything a carrier holds",
        "serves": "the held shards to peers who ask — a capacitor with a door open",
        "chosen_by": "an explicit choose('node'); serving is a SEPARATE consent from holding",
    },
}

_ROLE_FILE = "node_role.json"


def _role_path() -> Path:
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / _ROLE_FILE


def current_role() -> str:
    """The role this installation chose. Absence of a record IS the answer: reader.

    A torn or tampered record also reads as reader — failing closed here means failing to the
    tier that owes nothing, which is the only safe direction to fail.
    """
    p = _role_path()
    if not p.exists():
        return "reader"
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
        role = str(rec.get("role") or "")
        return role if role in ROLES else "reader"
    except (json.JSONDecodeError, OSError):
        return "reader"


def choose(role: str) -> Dict[str, Any]:
    """Write the person's choice. The only path from reader to anything else.

    Refuses unknown roles instead of guessing, and records WHEN the choice was made so the
    record is a small piece of history, not a bare flag. Choosing 'reader' deletes the record —
    reader is the absence of a choice, and a written 'reader' record would imply someone had to
    opt into owing nothing.
    """
    role = str(role).strip().lower()
    if role not in ROLES:
        raise ValueError(f"unknown role '{role}' — the roles are {sorted(ROLES)}")
    p = _role_path()
    if role == "reader":
        if p.exists():
            p.unlink()
        return {"role": "reader", "note": "the record is removed; absence of a choice is the choice"}
    rec = {"role": role, "chosen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "holds": ROLES[role]["holds"], "serves": ROLES[role]["serves"]}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    try:
        from . import ops
        ops.log("role_chosen", role=role)
    except Exception:                                          # noqa: BLE001 — the choice stands
        pass                                                   # even if the log cannot be reached
    return rec


def _shards_dir(explicit: Optional[Path] = None) -> Optional[Path]:
    if explicit is not None:
        return explicit if explicit.exists() else None
    try:
        from . import corpus_db
        return corpus_db._shards_dir()
    except Exception:                                          # noqa: BLE001
        env = os.environ.get("CONCORDANCE_CORPUS_SHARDS", "").strip()
        return Path(env) if env and Path(env).exists() else None


def hold_manifest(shards_dir: Optional[Path] = None, *, digest: bool = False) -> Dict[str, Any]:
    """What this installation ACTUALLY holds — measured from disk, never asserted from the role.

    COVERAGE FIRST: the manifest opens with where it looked and how many files it found, so an
    empty answer is distinguishable from a wrong path. digest=True computes each file's sha256 —
    the waybill hash a peer heals from. It is off by default because hashing gigabytes is a cost
    the caller must choose, not a surprise; without it the manifest still names and sizes every
    held file.
    """
    d = _shards_dir(shards_dir)
    if d is None:
        return {"looked_in": "no shard directory configured or present", "files": [],
                "held_files": 0, "held_bytes": 0,
                "means": "a claimed carrier with nothing here is holding nothing — visibly"}
    files: List[Dict[str, Any]] = []
    total = 0
    for f in sorted(d.iterdir()):
        if not f.is_file() or f.name.startswith("."):
            continue
        size = f.stat().st_size
        total += size
        entry: Dict[str, Any] = {"name": f.name, "bytes": size}
        if digest:
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            entry["sha256"] = h.hexdigest()
        files.append(entry)
    return {"looked_in": str(d), "files": files, "held_files": len(files), "held_bytes": total,
            "digested": digest,
            "means": "files actually on disk in the shard directory; the role claims nothing this does not show"}


def status() -> Dict[str, Any]:
    """Role + reality in one answer: what was chosen, and what the disk actually holds."""
    role = current_role()
    m = hold_manifest()
    return {"role": role, "declared": ROLES[role], "holding": m,
            "consistent": (role == "reader") or (m["held_files"] > 0),
            "means": ("consistent=False flags a chosen carrier/node holding zero shard files — "
                      "a claim the disk does not back")}
