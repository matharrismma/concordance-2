"""Detached attestation — bind an identity to a record you already hold, without ever sending a key.

This closes the last shape of the private-key-on-the-wire problem (see the drift ledger in
docs/COMPLETION_CONTRACT.md). Badges, study bundles and group contributions all sign a
`content_hash` of a record the SERVER builds — and those records carry a server timestamp, so a
client cannot pre-compute the hash and therefore could not pre-sign it. The old answer was to hand
the server a private key. The right answer is two phases:

    1. do the thing (unsigned) -> you receive its content_hash
    2. sign THAT hash on your own machine -> submit only the attestation

`signing.sign_seal(content_hash, private_key)` builds the attestation locally (it is a plain dict:
alg, over, content_hash, pubkey, sig) and `signing.verify_seal` checks it. Nothing here ever takes
a private key, and there is no parameter to pass one.

WHY A SEPARATE STORE, AND WHY THAT IS BETTER. A CAS record is immutable: fold a signature into it
and the hash changes, so the signature would be over a different record than the one it names.
Attestations therefore live beside the record, keyed by its hash — which turns a limitation into the
right shape. The old embedded-signature design could hold exactly ONE signature (the issuer's). A
store holds MANY, so several parties can independently bear witness to the same record. That is the
witness gate this project already applies to history (Deuteronomy 19:15; Matthew 18:16;
2 Corinthians 13:1 — "at the mouth of two or three witnesses"), now applied to its own records:
one signature is a claim, two or three begin to establish a matter. We report the count and let the
reader weigh them; we never call a matter established for them.

DISTINCT from two neighbours that share the word "attest":
  * `badges.self_attest` — a person's own WORDS about their study; deliberately never evidence.
  * the FLOOR attestation (`tests/test_attestation.py`) — a packet affirming protective framing.
Neither is cryptographic. This module is: a signature over a content hash, re-verified on every read.

Sovereign: stdlib only, no network, and storage is never trusted — every attestation is verified
again when read, so a tampered file is caught at read time rather than believed.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import cas, signing

_LOCK = threading.Lock()

NOTE = ("One signature is a claim; two or three witnesses begin to establish a matter "
        "(Deuteronomy 19:15). We count the witnesses and show their keys — we do not tell you the "
        "matter is settled. Every attestation is re-verified as it is read; storage is not trusted.")


def _dir() -> Path:
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(d) if d else Path("data")) / "attestations"


def _path(content_hash: str) -> Path:
    # 2-char prefix shard, mirroring cas.py, so directory listings stay manageable.
    h = content_hash.strip()
    return _dir() / h[:2] / f"{h}.jsonl"


def bear_witness(content_hash: str, attestation: Dict[str, Any]) -> Dict[str, Any]:
    """Record a verified attestation over a record we actually hold. Never takes a private key.

    Refuses when: the hash is malformed, the record is not in the CAS (attesting to something we do
    not have is unverifiable, so we decline rather than store a dangling claim), or the signature
    does not verify. An identical attestation twice is idempotent, not a second witness — the same
    key cannot become two witnesses by repeating itself.
    """
    h = str(content_hash or "").strip()
    if not h:
        return {"ok": False, "error": "content_hash required"}
    if not isinstance(attestation, dict):
        return {"ok": False, "error": "attestation must be an object from signing.sign_seal"}
    if attestation.get("private_key") or attestation.get("privateKey"):
        return {"ok": False, "error": ("do not send a private key — an attestation carries only a "
                                       "public key and a signature. Sign locally.")}
    if not cas.exists(h):
        return {"ok": False, "error": ("no record with that content_hash is held here — attesting to "
                                       "a record we do not have could never be checked, so it is "
                                       "declined rather than stored")}
    ok, detail = signing.verify_seal(h, attestation)
    if not ok:
        return {"ok": False, "error": f"attestation does not verify: {detail}"}

    entry = {"content_hash": h, "alg": attestation.get("alg", "ed25519"),
             "pubkey": attestation.get("pubkey"), "sig": attestation.get("sig"),
             "over": attestation.get("over", "content_hash"),
             "fingerprint": _fingerprint(attestation.get("pubkey", ""))}
    p = _path(h)
    with _LOCK:
        existing = _read(h)
        if any(e.get("pubkey") == entry["pubkey"] and e.get("sig") == entry["sig"] for e in existing):
            return {"ok": True, "already": True, "witnesses": len(existing),
                    "note": "This exact attestation was already recorded — repeating it adds no witness."}
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        total = len(existing) + 1
    return {"ok": True, "content_hash": h, "witnesses": total,
            "fingerprint": entry["fingerprint"],
            "established": total >= 2,     # honest wording: "begins to be established", see NOTE
            "note": NOTE}


def _fingerprint(public_key: str) -> Optional[str]:
    try:
        from . import identity
        return identity.fingerprint(public_key) if public_key else None
    except Exception:  # noqa: BLE001 — a fingerprint is a convenience, never load-bearing
        return None


def _read(content_hash: str) -> List[Dict[str, Any]]:
    p = _path(content_hash)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict) and e.get("sig"):
                out.append(e)
    except OSError:
        return []
    return out


def witnesses(content_hash: str) -> Dict[str, Any]:
    """Who has borne witness to this record — each signature re-verified as it is read.

    A stored entry that no longer verifies is reported as `valid: False` rather than dropped
    silently: a reader is owed the fact that something was tampered with, not a tidier list.
    """
    h = str(content_hash or "").strip()
    if not h:
        return {"ok": False, "error": "content_hash required"}
    entries = _read(h)
    checked: List[Dict[str, Any]] = []
    for e in entries:
        ok, detail = signing.verify_seal(h, e)
        checked.append({"pubkey": e.get("pubkey"), "fingerprint": e.get("fingerprint"),
                        "alg": e.get("alg"), "valid": bool(ok), "detail": detail})
    valid = [c for c in checked if c["valid"]]
    return {"ok": True, "content_hash": h, "record_held": cas.exists(h),
            "witnesses": len(valid), "attestations": checked,
            "invalid": len(checked) - len(valid),
            "established": len(valid) >= 2,
            "note": NOTE}


__all__ = ["bear_witness", "witnesses", "NOTE"]
