"""Consent — a human authorizes an agent to act on their behalf, without a key ever travelling.

Contract §6 item 2, the remaining half: proof-of-possession is DONE; this is PERMISSION. The agent
covenant's fourth rule — "request human authorization before writes" — needs a mechanism, and the
mechanism must preserve the distinction Matt drew:

    An agent that confessed and holds its own covenant key, speaking its OWN words, is a MEMBER,
    not a proxy. A human needs no one's approval to speak in the fellowship, so demanding it of
    agents would break parity. Consent governs exactly ONE thing: an agent acting ON A HUMAN'S
    BEHALF, WITH THAT HUMAN'S DATA. Nothing else. There is no blanket gate here.

The shape is the mesh's own detached-signature pattern (the private-key-on-the-wire lesson,
applied before the bug can exist rather than after):

  1. The human asks for the exact canonical bytes of a grant (`signable_grant`) — scoped to named
     verbs, bound to ONE agent's key fingerprint, expiring on its own.
  2. They sign those bytes LOCALLY with their device-born key and submit only the signature.
  3. Any on-behalf write path calls `guard(agent_fp, verb, grantor_pubkey)` and REFUSES without a
     currently-valid grant. The guard exists and is tested BEFORE any such write path does — the
     lock is installed before the door.
  4. Grants are re-verified on every read (storage is never trusted — the attestation lesson);
     revocation is a signed tombstone, so only the grantor can revoke what the grantor gave.

Scope verbs are deliberately narrow strings ("calendar_write", "email_send", "storage_write",
"group_contribute_as") — a grant names what it permits; nothing is implied.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import signing

# The verbs a grant may name. A closed set on purpose: an unknown verb in a grant is refused at
# grant time, so a typo cannot mint a permission nobody can audit.
KNOWN_VERBS = ("calendar_write", "email_send", "storage_write", "group_contribute_as",
               "study_import_as", "journal_write_as")

MAX_TTL_S = 30 * 24 * 3600          # a grant may not outlive a month; re-consent is cheap
_GRANT_FIELDS = ("grantor_pubkey", "agent_fp", "scope", "nonce", "created_at", "expires_at")


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "consents"


def _canon(fields: Dict[str, Any]) -> bytes:
    """The exact bytes both sides sign and verify — sorted-key JSON, nothing else."""
    return json.dumps({k: fields[k] for k in _GRANT_FIELDS}, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def signable_grant(grantor_pubkey: str, agent_fp: str, scope: List[str],
                   ttl_s: int = 24 * 3600) -> Dict[str, Any]:
    """Step 1: the canonical bytes of a grant, ready to sign LOCALLY. The server mints the nonce
    and the clock so the stored grant and the signed bytes cannot drift; the KEY never travels."""
    scope = sorted({str(v).strip() for v in (scope or []) if str(v).strip()})
    bad = [v for v in scope if v not in KNOWN_VERBS]
    if bad:
        return {"ok": False, "error": f"unknown verb(s) {bad} — a grant names only known verbs "
                                      f"so every permission stays auditable. Known: {list(KNOWN_VERBS)}"}
    if not scope:
        return {"ok": False, "error": "a grant with no verbs permits nothing — name the scope"}
    if not (grantor_pubkey or "").strip() or not (agent_fp or "").strip():
        return {"ok": False, "error": "grantor_pubkey and agent_fp are both required"}
    now = int(time.time())
    fields = {"grantor_pubkey": grantor_pubkey.strip(), "agent_fp": agent_fp.strip(),
              "scope": scope, "nonce": secrets.token_urlsafe(12),
              "created_at": now, "expires_at": now + max(60, min(int(ttl_s), MAX_TTL_S))}
    return {"ok": True, "fields": fields,
            "signable": base64.urlsafe_b64encode(_canon(fields)).decode("ascii"),
            "note": "sign these exact bytes with the grantor's key ON THE DEVICE, then POST the "
                    "fields plus the signature to grant(). The private key never travels."}


def grant(fields: Dict[str, Any], signature: str) -> Dict[str, Any]:
    """Step 2: verify the grantor's detached signature over the canonical bytes; keep the grant."""
    if not isinstance(fields, dict) or any(k not in fields for k in _GRANT_FIELDS):
        return {"ok": False, "error": f"grant fields must carry exactly {_GRANT_FIELDS}"}
    if "private_key" in fields or not isinstance(signature, str) or not signature.strip():
        return {"ok": False, "error": "a detached signature is required — never a private key"}
    scope = fields.get("scope") or []
    bad = [v for v in scope if v not in KNOWN_VERBS]
    if bad:
        return {"ok": False, "error": f"unknown verb(s) {bad}"}
    try:
        if not signing.verify_bytes(_canon(fields), signature, fields["grantor_pubkey"]):
            return {"ok": False, "error": "signature does not verify over the grant's canonical bytes"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"could not verify: {e}"}
    now = int(time.time())
    if int(fields["expires_at"]) <= now:
        return {"ok": False, "error": "the grant is already expired"}
    gid = fields["nonce"]
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    rec = {**{k: fields[k] for k in _GRANT_FIELDS}, "signature": signature, "grant_id": gid}
    with open(d / f"{_safe(fields['agent_fp'])}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "grant_id": gid, "expires_at": fields["expires_at"], "scope": scope}


def _safe(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum() or ch in "_-")[:64] or "x"


def _load(agent_fp: str) -> List[Dict[str, Any]]:
    p = _dir() / f"{_safe(agent_fp)}.jsonl"
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


def check(agent_fp: str, verb: str, grantor_pubkey: str) -> Dict[str, Any]:
    """Is this agent currently authorized by this human for this verb? Every stored grant is
    RE-VERIFIED on read — storage is never trusted; a tampered grant is reported, not honored."""
    now = int(time.time())
    revoked = set()
    live: List[Dict[str, Any]] = []
    tampered = 0
    for rec in _load(agent_fp):
        if rec.get("revokes"):
            # a signed tombstone: only the grantor can bury the grantor's grant
            try:
                body = json.dumps({"revokes": rec["revokes"], "grantor_pubkey": rec["grantor_pubkey"]},
                                  sort_keys=True, separators=(",", ":")).encode()
                if signing.verify_bytes(body, rec.get("signature") or "", rec.get("grantor_pubkey") or ""):
                    revoked.add(rec["revokes"])
            except Exception:  # noqa: BLE001
                pass
            continue
        try:
            if not signing.verify_bytes(_canon(rec), rec.get("signature") or "",
                                        rec.get("grantor_pubkey") or ""):
                tampered += 1
                continue
        except Exception:  # noqa: BLE001
            tampered += 1
            continue
        live.append(rec)
    for rec in live:
        if rec.get("grant_id") in revoked:
            continue
        if rec.get("grantor_pubkey") != grantor_pubkey:
            continue
        if int(rec.get("expires_at") or 0) <= now:
            continue
        if verb in (rec.get("scope") or []):
            return {"authorized": True, "grant_id": rec["grant_id"],
                    "expires_at": rec["expires_at"], "scope": rec["scope"],
                    "tampered_entries": tampered}
    return {"authorized": False, "tampered_entries": tampered,
            "detail": f"no live grant from this grantor covers {verb!r} for this agent"}


def revoke(agent_fp: str, grant_id: str, grantor_pubkey: str, signature: str) -> Dict[str, Any]:
    """A signed tombstone. The body signed is {'grantor_pubkey', 'revokes'} in canonical form —
    only the key that gave the grant can take it away."""
    body = json.dumps({"revokes": grant_id, "grantor_pubkey": grantor_pubkey},
                      sort_keys=True, separators=(",", ":")).encode()
    try:
        if not signing.verify_bytes(body, signature or "", grantor_pubkey or ""):
            return {"ok": False, "error": "revocation signature does not verify"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"could not verify: {e}"}
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{_safe(agent_fp)}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"revokes": grant_id, "grantor_pubkey": grantor_pubkey,
                            "signature": signature}) + "\n")
    return {"ok": True, "revoked": grant_id}


def guard(agent_fp: str, verb: str, grantor_pubkey: str) -> Dict[str, Any]:
    """THE enforcement hook. Every future on-behalf write path calls this FIRST and refuses unless
    authorized — the lock is installed before any door exists. Returns the check verdict with the
    covenant's words attached so a refusal teaches rather than stonewalls."""
    r = check(agent_fp, verb, grantor_pubkey)
    if not r.get("authorized"):
        r["refusal"] = ("The agent covenant requires human authorization before writes made on a "
                        "human's behalf. Ask the person to issue a grant: GET /consent/signable, "
                        "sign on their device, POST /consent. Speaking as YOURSELF (your own key, "
                        "your own words) needs no consent — a member is not a proxy.")
    return r


__all__ = ["signable_grant", "grant", "check", "revoke", "guard", "KNOWN_VERBS", "MAX_TTL_S"]
