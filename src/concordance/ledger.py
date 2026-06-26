"""Ledger — the append-only audit chain of sealed records.

Each sealed PASS record becomes a precedent file linked into a SHA-256 hash chain:
every file's `prev_hash` is the prior file's `content_hash` (GENESIS for the first).
Tamper with any file and `verify_chain` catches it — the chain is the integrity proof.

Chain order is by `sealed_at` (not filename), so inserting a file later never changes
an earlier file's position. Ported from 1.0 src/concordance_engine/ledger.py — the
chain essentials. `find_closest` (precedent search) needs the grid and ports later.

`seal_record` wires the floor together: validate_and_seal -> CAS (content-addressed
store) -> ledger (the chain). Sovereign: stdlib only, a directory of JSON files.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import cas
from .record import WitnessRecord, with_permanent_ref
from .validate import canonical_json_bytes, sha256_bytes

GENESIS_HASH = "GENESIS"
# Chain-layer fields excluded from content_hash (the hash is over the content).
_CHAIN_FIELDS = ("content_hash", "prev_hash")


def _default_ledger_dir() -> Path:
    override = os.environ.get("CONCORDANCE_LEDGER_DIR")
    if override:
        return Path(override)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "ledger"
    return Path("data") / "ledger"


def _read_precedent_file(p: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(p, encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _load_precedents(ledger_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Read precedents from the ledger directory, de-duped by precedent_id."""
    d = ledger_dir or _default_ledger_dir()
    seen: set = set()
    out: List[Dict[str, Any]] = []
    if not d.exists() or not d.is_dir():
        return out
    for f in sorted(d.glob("*.json")):
        p = _read_precedent_file(f)
        if isinstance(p, dict) and p.get("precedent_id") and p["precedent_id"] not in seen:
            seen.add(p["precedent_id"])
            out.append(p)
    return out


def list_precedents(ledger_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Every precedent currently in the ledger."""
    return _load_precedents(ledger_dir)


# ── Hash chain ─────────────────────────────────────────────────────────

def compute_content_hash(precedent: Dict[str, Any]) -> str:
    """SHA-256 of the precedent's canonical JSON, excluding the chain fields so the
    hash is stable across re-sealing."""
    payload = {k: v for k, v in precedent.items() if k not in _CHAIN_FIELDS}
    return sha256_bytes(canonical_json_bytes(payload))


def _ledger_chain_files(ledger_dir: Optional[Path] = None) -> List[Path]:
    """Files in chain order — by `sealed_at` ascending, filename as tiebreaker."""
    d = ledger_dir or _default_ledger_dir()
    if not d.exists() or not d.is_dir():
        return []

    def _sort_key(f: Path):
        data = _read_precedent_file(f)
        if data and isinstance(data.get("sealed_at"), (int, float)):
            return (data["sealed_at"], f.name)
        try:
            return (f.stat().st_mtime, f.name)
        except OSError:
            return (0.0, f.name)

    return sorted(d.glob("*.json"), key=_sort_key)


def verify_chain(ledger_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Walk the ledger in chain order and verify integrity: recompute each
    content_hash and confirm each prev_hash links to the prior file's hash."""
    files = _ledger_chain_files(ledger_dir)
    report: Dict[str, Any] = {
        "ok": True, "total": len(files), "verified": 0,
        "unsigned": [], "tampered": [], "broken_links": [],
    }
    expected_prev = GENESIS_HASH
    for f in files:
        precedent = _read_precedent_file(f)
        if precedent is None:
            report["tampered"].append({"file": f.name, "error": "could not parse JSON"})
            report["ok"] = False
            continue
        stored_hash = precedent.get("content_hash")
        if stored_hash is None:
            report["unsigned"].append(f.name)
            expected_prev = compute_content_hash(precedent)
            continue
        recomputed = compute_content_hash(precedent)
        if recomputed != stored_hash:
            report["tampered"].append({
                "file": f.name,
                "error": f"content_hash mismatch: stored {stored_hash[:12]}..., "
                         f"recomputed {recomputed[:12]}...",
            })
            report["ok"] = False
            expected_prev = stored_hash
            continue
        stored_prev = precedent.get("prev_hash", GENESIS_HASH)
        if stored_prev != expected_prev:
            report["broken_links"].append({
                "file": f.name,
                "expected_prev": expected_prev[:12] + "..." if expected_prev != GENESIS_HASH else GENESIS_HASH,
                "got_prev": stored_prev[:12] + "..." if stored_prev != GENESIS_HASH else GENESIS_HASH,
            })
            report["ok"] = False
            expected_prev = stored_hash
            continue
        report["verified"] += 1
        expected_prev = stored_hash
    return report


def _slugify(value: str) -> str:
    """Filesystem-safe slug for precedent file names."""
    out = []
    for c in value.lower():
        if c.isalnum():
            out.append(c)
        elif c in (" ", "-", "_", ".", "/", ":"):
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "untitled"


def seal_to_ledger(record: WitnessRecord, *, summary: str,
                   precedent_id: Optional[str] = None,
                   ledger_dir: Optional[Path] = None,
                   sealed_at: Optional[float] = None,
                   overwrite: bool = False) -> Path:
    """Append a sealed PASS record to the chain as a new precedent. Returns the path.

    Only PASS records seal — the ledger records *resolved* decisions; rejected or
    quarantined packets are not precedents. `summary` is a required one-line human
    framing. Raises ValueError on a non-PASS record or empty summary."""
    if record.overall != "PASS":
        raise ValueError(f"only PASS records seal to the ledger; got {record.overall}")
    if not summary or not summary.strip():
        raise ValueError("`summary` is required (one-line human description)")

    axis = record.axis_coords.axis if record.axis_coords else "unknown"
    dimensions = sorted(record.axis_coords.dimensions) if record.axis_coords else []

    if precedent_id is None:
        slug_base = record.packet_id or _slugify(summary)[:60]
        precedent_id = f"ledger://{axis}/{_slugify(slug_base)}"

    overlay: Dict[str, str] = {}
    step = 1
    for gr in record.gate_results:
        if gr.status == "PASS":
            details_msg = ""
            if gr.details and isinstance(gr.details, dict):
                verified = gr.details.get("verified") or []
                if verified:
                    details_msg = "; ".join(str(v) for v in verified[:3])
            overlay[f"step_{step}_{gr.gate.lower()}"] = details_msg or f"{gr.gate} gate confirmed"
            step += 1

    precedent_payload = {
        "precedent_id": precedent_id,
        "axis": axis,
        "dimensions": dimensions,
        "summary": summary.strip(),
        "anchors": [a.to_dict() for a in record.anchors],
        "reasoning_overlay": overlay,
        "sealed_at": sealed_at if sealed_at is not None else time.time(),
    }

    d = ledger_dir or _default_ledger_dir()
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"{_slugify(precedent_id.replace('ledger://', ''))}.json"
    if target.exists() and not overwrite:
        raise FileExistsError(f"precedent file already exists at {target}")

    existing = [f for f in _ledger_chain_files(d) if f != target]
    if not existing:
        prev_hash = GENESIS_HASH
    else:
        last_data = _read_precedent_file(existing[-1])
        if last_data and "content_hash" in last_data:
            prev_hash = last_data["content_hash"]
        elif last_data:
            prev_hash = compute_content_hash(last_data)
        else:
            prev_hash = GENESIS_HASH

    precedent_payload["prev_hash"] = prev_hash
    precedent_payload["content_hash"] = compute_content_hash(precedent_payload)

    with open(target, "w", encoding="utf-8") as f:
        json.dump(precedent_payload, f, indent=2)
        f.write("\n")
    return target


def seal_record(record: WitnessRecord, *, summary: str,
                ledger_dir: Optional[Path] = None,
                cas_base: Optional[Path] = None,
                sealed_at: Optional[float] = None) -> Dict[str, Any]:
    """Wire the floor: store the sealed record in the CAS (content-addressed), then
    append it to the ledger chain. Returns {content_hash, ledger_path, precedent}."""
    content_hash = cas.store(record.to_dict(), base_dir=cas_base)
    record = with_permanent_ref(record, content_hash)
    path = seal_to_ledger(record, summary=summary, ledger_dir=ledger_dir, sealed_at=sealed_at)
    return {"content_hash": content_hash, "ledger_path": str(path),
            "precedent": _read_precedent_file(path)}
