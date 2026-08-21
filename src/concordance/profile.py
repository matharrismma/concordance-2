"""Profile — your keeping that follows you, keyed by your fingerprint. Opt-in, sovereign, no account.

Everything resolves to a FINGERPRINT (from your public key). A human derives their key from a passphrase
(`identity.derive_identity` — the ez-login); an agent generates and holds one (`identity.create_identity`
— a key). Either way the profile is yours: your shelf, your wants, your prefs, following you across
sessions and devices. Writes are SIGNED — you prove ownership with your key, so there is no password to
store or steal, and no one but the key's owner can change it. The default is untouched: no key, no
profile, free and anonymous as ever. The server keeps only your public key and what you chose to save,
and you can export it (it is just JSON) or erase it with a signed delete.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

from . import identity, signing

_MAX_PATCH = 64 * 1024
_MAX_NONCES = 256


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "profiles"


def _path(fp: str) -> Path:
    safe = "".join(ch for ch in (fp or "") if ch.isalnum() or ch in "-_")
    return _dir() / f"{safe}.json"


def _load(fp: str) -> Dict[str, Any]:
    p = _path(fp)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _public_view(prof: Dict[str, Any]) -> Dict[str, Any]:
    """What a reader sees — the profile without the internal bookkeeping (spent nonces, owner key)."""
    return {k: v for k, v in prof.items() if not k.startswith("_")}


def get(fp: str) -> Dict[str, Any]:
    """Read a profile by fingerprint. Public fields only; empty if none is saved (the anonymous default)."""
    return _public_view(_load(str(fp or "")))


def signable(public_key: str, patch: Dict[str, Any], nonce: str) -> bytes:
    """The exact bytes the owner signs to authorize a write: {public_key, patch, nonce}, canonical. The
    client signs these with its private key; nothing secret ever leaves the device."""
    return signing.canonical_json_bytes({"public_key": public_key, "patch": patch, "nonce": nonce})


def put(public_key: str, patch: Dict[str, Any], nonce: str, signature: str) -> Dict[str, Any]:
    """SIGNED write: merge `patch` into the profile owned by `public_key`. Ownership is proven by the
    signature over `signable(...)` — no password, no account. A used nonce is refused (no replay). The
    default stays anonymous: without a key there is no write."""
    if not isinstance(patch, dict):
        return {"ok": False, "error": "patch must be an object"}
    if len(json.dumps(patch)) > _MAX_PATCH:
        return {"ok": False, "error": "patch too large"}
    nonce = str(nonce or "").strip()
    if not nonce:
        return {"ok": False, "error": "nonce required"}
    try:
        ok = signing.verify_bytes(signable(public_key, patch, nonce), signature, public_key)
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        return {"ok": False, "error": "signature does not verify — only the key's owner may write"}

    fp = identity.fingerprint(public_key)
    prof = _load(fp)
    if nonce in prof.get("_nonces", []):
        return {"ok": False, "error": "nonce already used (replay refused)"}
    for k, v in patch.items():
        if not str(k).startswith("_"):     # internal keys are never writable from a patch
            prof[k] = v
    prof["_owner"] = public_key
    prof["_nonces"] = (prof.get("_nonces", []) + [nonce])[-_MAX_NONCES:]
    prof["updated_at"] = round(time.time(), 3)
    _dir().mkdir(parents=True, exist_ok=True)
    _path(fp).write_text(json.dumps(prof, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "id": fp, "profile": _public_view(prof)}


def delete(public_key: str, nonce: str, signature: str) -> Dict[str, Any]:
    """SIGNED erase — remove your profile entirely. Same proof of ownership as a write; it is yours to
    take back. (Signs over an empty patch, so the one signable path covers both.)"""
    if not identity.fingerprint(public_key):
        return {"ok": False, "error": "public_key required"}
    try:
        ok = signing.verify_bytes(signable(public_key, {}, str(nonce or "")), signature, public_key)
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        return {"ok": False, "error": "signature does not verify — only the key's owner may erase"}
    p = _path(identity.fingerprint(public_key))
    existed = p.is_file()
    if existed:
        p.unlink()
    return {"ok": True, "erased": existed}


__all__ = ["get", "signable", "put", "delete"]
