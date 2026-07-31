"""Content-addressable store (CAS) — permanent receipt storage.

Every sealed record is stored by its SHA-256 content hash. The hash is both the
address and the integrity proof: fetch-by-hash and you know immediately whether
the content was tampered with. No external dependency, no tokens — works offline,
over LoRa, on a microSD. (Serviceability + sovereignty: the watch discipline.)

Storage layout:
    <base_dir>/<hash[:2]>/<hash[2:]>.json
  The 2-char prefix shards into 256 subdirectories so listings stay manageable.

Environment:
    CONCORDANCE_CAS_DIR   — override default storage path
    CONCORDANCE_DATA_DIR  — parent for default path

Ported as-is from 1.0 — stdlib only, already clean.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _cas_dir() -> Path:
    env = os.environ.get("CONCORDANCE_CAS_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "cas"
    return Path("data") / "cas"


def content_hash_of(record_dict: Dict[str, Any]) -> str:
    """Canonical SHA-256 of a record dict, excluding self-referential fields
    (`content_hash`, `permanent_ref`) so the hash is stable. Uses the ONE shared
    canonicalizer (validate.content_hash, ensure_ascii=False) — see validate.py."""
    from .validate import content_hash as _canonical
    return _canonical(record_dict, exclude=("content_hash", "permanent_ref"))


import re as _re
# A content hash is always 64 lowercase hex (SHA-256). Validating the caller-supplied hash
# BEFORE it touches the filesystem blocks path traversal via /seal?hash=../.., /s/<h>, /b/<h>
# — this was the one store that took a raw hash straight into a path (the others validate ids).
_HASH_RE = _re.compile(r"[0-9a-f]{64}\Z")


def _valid_hash(h: str) -> bool:
    return bool(_HASH_RE.match(h or ""))


def _record_path(base: Path, h: str) -> Path:
    return base / h[:2] / f"{h[2:]}.json"


def store(record_dict: Dict[str, Any], *, base_dir: Optional[Path] = None,
          overwrite: bool = False) -> str:
    """Store a record dict. Returns its content_hash. Idempotent, append-only.

    A MINTED RECEIPT ALSO BECOMES A CARD — see `_mint_receipt_card`. This is the one place a seal
    is born (badges, the ledger and receipts.py all come through here), so it is the one place the
    obligation belongs.
    """
    base = base_dir or _cas_dir()
    h = content_hash_of(record_dict)
    path = _record_path(base, h)
    if path.exists() and not overwrite:
        _mint_receipt_card(h, record_dict)   # idempotent; heals a seal whose card never landed
        return h
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = dict(record_dict)
    stored["content_hash"] = h
    from .validate import canonical_json_bytes
    path.write_bytes(canonical_json_bytes(stored))  # same canonical form (ensure_ascii=False)
    _mint_receipt_card(h, stored)
    return h


# ── the receipt is also a card ────────────────────────────────────────────────────────────────
#
# Matt, 2026-07-31: *"When we mint a receipt, it needs to become a card as well. That would allow
# us to have both and not change a ton."*
#
# Measured the same day: of the twenty receipts the Codex advertises as "backed by a live,
# re-checkable receipt", NINETEEN answered 404. Across the whole access log, 16,146 requests for
# 5,394 distinct receipt hashes found nothing — more than every other 404 on the box combined. The
# strongest claim this project makes ("re-check it yourself") was failing in public.
#
# The cause is structural, not a bug: `data/cas/` is not deployed and not backed up. A seal minted
# on one machine exists only there, while the card that cites it travels everywhere. So the receipt
# now ALSO lands in the keeping, which is deployed, sharded, replicated and archived — and `/s/`
# reads the card when the CAS object is not on this node. Two stores, one truth, and the hash still
# arbitrates: the card carries the record verbatim, so re-hashing it must give back the same
# address or it is not that record.
_RECEIPT_SHELF = "seals"
_RECEIPT_SPINE = "card_spine_seals"


def _receipt_spine() -> Dict[str, Any]:
    """The anchor every receipt hangs from.

    NOTHING IN THE KEEPING IS ISOLATED, and the gate caught the first version of this code minting
    receipt cards with no connections at all — a whole shelf of orphans. A receipt is not a loose
    fact: it is a record OF something, held by the same library, so it is rooted like every other
    spine.
    """
    return {
        "id": _RECEIPT_SPINE,
        "kind": "reference",
        "shelf": "spine",
        "surface": "secular",
        "title": "The seals — every sealed record, kept as a card",
        "body": ("Every receipt this engine mints is stored twice: as a content-addressed object "
                 "under its SHA-256 hash, and as a card on this spine. The object is fast; the "
                 "card is durable — it travels with the keeping, so a receipt outlives the machine "
                 "that minted it. The hash arbitrates either way."),
        "source": {"label": "Narrow Highway engine", "url": "/corpus.html?shelf=seals",
                   "ref": "seals", "authority_tier": "engine_derived"},
        "connections": [{"to_card_id": "card_k_floor_of_discovery", "relationship": "part_of",
                         "evidence": "a spine of the keeping, rooted in the Floor of Discovery"}],
    }


def receipt_card_id(content_hash: str) -> str:
    return "card_seal_" + content_hash


def card_to_record(card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The sealed record carried inside a receipt card, or None. Verifies the hash before
    returning it: a card claiming to hold a receipt proves it the same way the CAS does."""
    rec = ((card or {}).get("extra") or {}).get("record")
    if not isinstance(rec, dict):
        return None
    claimed = str(((card or {}).get("extra") or {}).get("seal_hash") or "")
    bare = {k: v for k, v in rec.items() if k != "content_hash"}
    if not _valid_hash(claimed) or content_hash_of(bare) != claimed:
        return None            # never hand back a record whose address does not recompute
    return rec


def _mint_receipt_card(content_hash: str, record: Dict[str, Any]) -> None:
    """Best-effort, and deliberately so: a seal must never fail because the keeping is busy.

    Writes to `data/receipt_cards.jsonl` (loaded with the rest of the keeping) and inserts into the
    live corpus so the receipt is findable in the same breath it is minted — not after a restart.
    """
    try:
        from . import corpus
        cid = receipt_card_id(content_hash)
        if corpus.get_card(cid) is not None:
            return                                            # idempotent
        rec = dict(record)
        rec.pop("content_hash", None)
        verdict = str(rec.get("verdict") or rec.get("status") or "").strip()
        subject = str(rec.get("claim") or rec.get("mode") or rec.get("kind") or "record").strip()
        card = {
            "id": cid,
            "kind": "receipt",
            "shelf": _RECEIPT_SHELF,
            "surface": "secular",
            "title": (f"Receipt {content_hash[:12]}… — {verdict or 'sealed'}: {subject}")[:180],
            "body": json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=1)[:20000],
            "source": {"label": "Narrow Highway engine — sealed record",
                       "url": "/s/" + content_hash,
                       "ref": content_hash,
                       "authority_tier": "engine_derived"},
            "extra": {"seal_hash": content_hash, "record": rec},
            # rooted, never an orphan — and to the SUBJECT too when the record names one, so the
            # receipt is reachable from the very thing it is a receipt for
            "connections": [{"to_card_id": _RECEIPT_SPINE, "relationship": "part_of",
                             "evidence": "a sealed record, kept as a card"}],
        }
        subj = str(rec.get("card_id") or rec.get("subject_card") or "").strip()
        if subj and subj != cid and corpus.get_card(subj) is not None:
            card["connections"].append({"to_card_id": subj, "relationship": "seals",
                                        "evidence": "this receipt seals that card's claim"})
        path = _cas_dir().parent / "receipt_cards.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        to_write = [card]
        if corpus.get_card(_RECEIPT_SPINE) is None:
            to_write.insert(0, _receipt_spine())   # the anchor, minted once, before its first child
        with open(path, "a", encoding="utf-8") as fh:
            for c in to_write:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        for c in to_write:
            corpus.add_to_default(c)
    except Exception:  # noqa: BLE001 — the seal is the promise; the card is the durability
        pass


def fetch_anywhere(content_hash: str, *, base_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """The receipt, from EITHER store — the CAS object, or the card that carries it.

    `data/cas/` is not deployed and not backed up, so a seal minted on one machine lived only
    there while the card citing it travelled everywhere: 16,146 requests for 5,394 receipt hashes
    found nothing. The card is the durable copy. The hash still arbitrates — `card_to_record`
    refuses any card whose record does not recompute to the address it claims.
    """
    rec = fetch(content_hash, base_dir=base_dir)
    if rec is not None:
        return rec
    try:
        from . import corpus
        card = corpus.get_card(receipt_card_id(content_hash))
        rec = card_to_record(card) if card else None
        if rec is not None:
            out = dict(rec)
            out["content_hash"] = content_hash
            out["_from"] = "card"      # named, never silent: this came from the keeping, not the CAS
            return out
    except Exception:  # noqa: BLE001
        pass
    return None


def fetch(content_hash: str, *, base_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Fetch a record by its content hash, or None if not found."""
    if not _valid_hash(content_hash):
        return None
    base = base_dir or _cas_dir()
    path = _record_path(base, content_hash)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def exists(content_hash: str, *, base_dir: Optional[Path] = None) -> bool:
    if not _valid_hash(content_hash):
        return False
    base = base_dir or _cas_dir()
    return _record_path(base, content_hash).exists()


def verify(content_hash: str, *, base_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """Verify a stored record's integrity by recomputing its hash."""
    record = fetch(content_hash, base_dir=base_dir)
    if record is None:
        return False, f"not found: {content_hash}"
    actual = content_hash_of(record)
    if actual != content_hash:
        return False, f"hash mismatch: stored={content_hash} computed={actual}"
    return True, "ok"


def list_hashes(*, base_dir: Optional[Path] = None) -> List[str]:
    base = base_dir or _cas_dir()
    hashes: List[str] = []
    if not base.exists():
        return hashes
    for prefix_dir in sorted(base.iterdir()):
        if not prefix_dir.is_dir() or len(prefix_dir.name) != 2:
            continue
        for f in sorted(prefix_dir.glob("*.json")):
            hashes.append(prefix_dir.name + f.stem)
    return hashes


def delete(content_hash: str, *, base_dir: Optional[Path] = None) -> bool:
    """Remove a record. Returns True if it existed. (Use sparingly — append-only by design.)"""
    if not _valid_hash(content_hash):
        return False
    base = base_dir or _cas_dir()
    path = _record_path(base, content_hash)
    if not path.exists():
        return False
    path.unlink()
    return True


def stats(*, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    base = base_dir or _cas_dir()
    hashes = list_hashes(base_dir=base)
    total_bytes = 0
    for h in hashes:
        p = _record_path(base, h)
        try:
            total_bytes += p.stat().st_size
        except OSError:
            pass
    return {
        "count": len(hashes),
        "total_bytes": total_bytes,
        "base_dir": str(base.resolve()) if base.exists() else str(base),
    }


__all__ = ["content_hash_of", "store", "fetch", "exists", "verify",
           "list_hashes", "delete", "stats"]
