"""Badges — a RE-CHECKABLE receipt whose evidence IS the sealed trail. (Arc 4: multiplication.)

A badge is NOT a competency claim and NOT a new trust primitive. It is a small, content-addressed
record that POINTS at N seals already in the store — each seal a real, re-fetchable verification the
person accumulated. Its whole worth is that anyone can re-check it from the existing floor: fetch the
badge by its hash (integrity proof), then re-verify every seal it references (cas.verify). If a
referenced seal is missing or tampered, that check does not count. So the number a badge states is
never "trust me" — it is exactly the count of sealed checks that STILL STAND when you re-run them.

WHAT A BADGE MAY SAY (load-bearing honesty): the copy states EXACTLY the N sealed checks —
"N verifications sealed" — and NOTHING about mastery, skill, level, or competency. We never certify a
person is good at anything; we only report, re-checkably, how many verifications they sealed. Success
is the person needing the tool LESS (John 3:30); a badge is a receipt they OWN and can carry away, not
a rank we grant.

SELF-ATTESTATION is a DISTINCTLY TYPED record (record_type="self_attestation", auto_gradable=False). A
person may attach their own words to a study, but a self-attestation can NEVER be counted as a sealed
check and can NEVER satisfy an auto-graded requirement — only real seals in the CAS count toward N.

SIGNING is OPTIONAL (identity.py). When cryptography is present a badge/export can carry an Ed25519
attestation binding an identity to the content_hash; when it is absent, issuance and export NEVER
hard-fail — the badge is still content-addressed, re-checkable, and portable (signed=False, honestly
labeled). The evidence (the seals) is what matters; the signature only says who is pointing at it.

SHARED STUDY reuses the superposition stack model (stacks.py): a study is a "study_maps" shelf — one
card lives ONCE and is referenced, never copied. Exports are self-contained and (optionally) signed;
import re-materializes the cards and re-references them, so a study travels between people/devices
without duplication and without inventing a new store.

Sovereign: stdlib + the existing floor only (cas, ledger, stacks, identity, signing). Imports NOTHING
from concordance.verifiers.* or concordance.derivation — it seals only via the public helpers
receipts.py uses (cas.store / cas.verify / cas.fetch, and best-effort ledger.seal_to_ledger). Conduit,
not source: a badge finds and re-checks sealed evidence; it never generates a verdict.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional

from . import cas, identity, signing, stacks

# Content-address record kinds, so a badge / self-attestation / study-export are self-describing in
# the store and can never be mistaken for a sealed verification record.
_BADGE_TYPE = "badge"
_SELF_ATTEST_TYPE = "self_attestation"
_STUDY_EXPORT_TYPE = "study_export"

# The ONE phrasing template. It states exactly N sealed checks and carries NO competency noun. Keeping
# the copy in one place (and asserting it in the tests) is how the honesty stays load-bearing.
_BADGE_COPY = "{n} verifications sealed"

# The shelf (stacks kind) that holds shared-study cards. One card lives once; a study references it.
_STUDY_KIND = "study_maps"

# Best-effort ledger chaining is read-then-write; serialize within the process (mirrors receipts.py).
_LOCK = threading.Lock()


def _public_base() -> str:
    """The re-checkable base URL for a badge's cite_url. Overridable; defaults to the secular reach
    (the badge surface is world-facing). Mirrors receipts._public_base's env override."""
    env = os.environ.get("CONCORDANCE_PUBLIC_BASE", "").strip()
    if env:
        return env.rstrip("/")
    return "https://narrowhighway.com"


def _standing_seals(seal_hashes: List[str]) -> List[str]:
    """Return, in order and de-duplicated, exactly the referenced seals that STILL STAND: present in
    the CAS AND re-verifying (recomputed hash matches). A missing or tampered seal is dropped — the
    evidence must survive a re-check to count. This is the whole basis of a badge's N."""
    out: List[str] = []
    seen: set = set()
    for h in (seal_hashes or []):
        if not isinstance(h, str) or not h or h in seen:
            continue
        seen.add(h)
        try:
            ok, _ = cas.verify(h)
        except Exception:  # noqa: BLE001 — a store hiccup must never inflate the count
            ok = False
        if ok:
            out.append(h)
    return out


def badge_copy(n: int) -> str:
    """The badge's human copy for N sealed checks. States EXACTLY N with NO competency noun — the one
    place the phrasing lives, so the honesty is testable."""
    return _BADGE_COPY.format(n=int(n))


def issue_badge(seal_hashes: List[str], *, subject_id: Optional[str] = None,
                title: str = "", private_key: Optional[str] = None,
                ledger_it: bool = True) -> Dict[str, Any]:
    """Issue a badge over already-sealed checks. RE-CHECKABLE by construction, NEVER hard-fails.

    `seal_hashes` are content hashes of seals already in the CAS (each a real verification). We keep
    only the ones that still stand (present + re-verifying), content-address the resulting badge
    record, and return {hash, checks: N, copy, ...}. `copy` states EXACTLY N ("N verifications
    sealed") with no competency claim. If `private_key` is given AND signing is available, the badge
    carries an Ed25519 attestation over its content_hash (signed=True); otherwise signed=False and
    issuance still succeeds — the evidence, not the signature, is the badge.
    """
    checks = _standing_seals(seal_hashes)
    n = len(checks)
    record: Dict[str, Any] = {
        "record_type": _BADGE_TYPE,
        "schema": "nh-badge-1",
        "title": str(title or ""),
        "subject_id": str(subject_id) if subject_id else None,
        "sealed_checks": checks,          # the evidence: hashes of seals that re-verify in the CAS
        "checks": n,                      # exactly the count that still stands
        "copy": badge_copy(n),            # states EXACTLY N — no competency noun
        "generated": False,               # conduit: a badge is found+re-checked, never generated
        "issued_at": round(time.time(), 3),
    }
    # Content-address the badge (integrity proof + the address). Idempotent: same evidence -> same hash.
    content_hash = cas.store(record)

    attestation: Optional[Dict[str, Any]] = None
    signed = False
    if private_key:
        try:
            if identity.signing_available():
                attestation = signing.sign_seal(content_hash, private_key)
                signed = True
        except Exception:  # noqa: BLE001 — signing is optional; never fail issuance because of it
            attestation, signed = None, False

    # Best-effort: chain the badge as a lightweight precedent so it appears in the audit trail. The
    # badge stands on the CAS regardless (mirrors receipts.py: the seal is real even if ledger fails).
    ledgered = False
    if ledger_it and n > 0:
        try:
            ledgered = _chain_badge(content_hash, n)
        except Exception:  # noqa: BLE001 — ledger append is availability, not correctness
            ledgered = False

    out = {
        "ok": True,
        "hash": content_hash,
        "checks": n,
        "copy": record["copy"],
        "sealed_checks": checks,
        "signed": signed,
        "ledgered": ledgered,
        # /b/<hash> is the server-rendered, crawlable badge page (mirrors /s/<hash> for seals).
        "cite_url": f"{_public_base()}/b/{content_hash}",
    }
    if attestation is not None:
        out["attestation"] = attestation
    return out


def _chain_badge(content_hash: str, n: int) -> bool:
    """Best-effort: record a badge breadcrumb in the audit chain via the PUBLIC receipts helper
    (the same helper steward's endpoint uses to seal) — NOT a new trust primitive and NOT a verifier.

    We hand receipts.mint a small derivation-shaped result describing "N sealed checks confirmed"; it
    builds+content-addresses+chains its own PASS precedent. This is only an audit breadcrumb: the
    badge's OWN hash, copy, and re-checkability (the referenced seals) are independent of whether this
    succeeds — so the module imports nothing from concordance.verifiers.* or .derivation. Returns
    whether a precedent was chained."""
    from . import receipts
    from .config import EngineConfig

    trail = [{"id": "badge", "domain": "mathematics", "status": "CONFIRMED",
              "claim": f"{n} sealed checks re-verified in the CAS", "uses": [content_hash]}]
    result = {"verdict": "HOLDS", "steps": n, "confirmed_steps": n, "trail": trail}
    with _LOCK:
        try:
            minted = receipts.mint(result, config=EngineConfig("secular"),
                                   domain="mathematics", summary=badge_copy(n)[:200])
            return bool(minted.get("ok") and minted.get("ledgered"))
        except Exception:  # noqa: BLE001 — audit breadcrumb only; never fail issuance for it
            return False


def verify_badge(badge_hash: str, *, attestation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Re-check a badge from the store. Returns {ok, checks: N, ...}.

    Re-fetches the badge record by its hash (integrity proof), then re-verifies EVERY seal it
    references (cas.verify). `checks` is EXACTLY the number of referenced seals that still stand — the
    same N the copy states, recomputed independently from the evidence, not read from a stored count.
    If an `attestation` is supplied and signing is available, `signature_valid` reports whether it
    binds to this badge's content_hash; a bad/absent signature never changes the re-checkable N.
    """
    record = cas.fetch(badge_hash)
    if record is None:
        return {"ok": False, "error": f"no such badge: {badge_hash}", "checks": 0}
    if record.get("record_type") != _BADGE_TYPE:
        return {"ok": False, "error": "not a badge record", "checks": 0}
    # Integrity of the badge record itself.
    integrity_ok, _ = cas.verify(badge_hash)
    # Re-check the evidence independently — N is recomputed, never trusted from the stored field.
    standing = _standing_seals(list(record.get("sealed_checks") or []))
    n = len(standing)
    result: Dict[str, Any] = {
        "ok": integrity_ok,
        "hash": badge_hash,
        "checks": n,                       # EXACTLY the re-verified count
        "copy": badge_copy(n),             # states EXACTLY N — no competency noun
        "sealed_checks": standing,
        "record_type": _BADGE_TYPE,
        "integrity_ok": integrity_ok,
    }
    if attestation is not None:
        try:
            ok, detail = signing.verify_seal(badge_hash, attestation)
        except Exception:  # noqa: BLE001 — verification is total; never raise
            ok, detail = False, "signature could not be verified"
        result["signature_valid"] = ok
        result["signature_detail"] = detail
    return result


def self_attest(subject_id: str, statement: str, *, study: Optional[str] = None) -> Dict[str, Any]:
    """Record a person's OWN words about their study — a DISTINCTLY TYPED record that can NEVER count
    as a sealed check and NEVER satisfy an auto-graded requirement.

    record_type="self_attestation" and auto_gradable=False are load-bearing: this record carries no
    seal hashes and is excluded from every badge's N by construction. It is content-addressed (so it
    is stable and re-fetchable) but it is honestly NOT evidence of verification — only real seals in
    the CAS are. Verbatim (the person's words); conduit, never generated.
    """
    record = {
        "record_type": _SELF_ATTEST_TYPE,   # distinct type — never a badge, never a seal
        "schema": "nh-self-attest-1",
        "auto_gradable": False,              # can NEVER satisfy an auto-graded requirement
        "counts_as_check": False,            # explicit: excluded from any badge's sealed-check count
        "subject_id": str(subject_id or ""),
        "statement": str(statement or ""),   # the person's own words, verbatim
        "study": str(study) if study else None,
        "generated": False,
        "attested_at": round(time.time(), 3),
    }
    content_hash = cas.store(record)
    return {"ok": True, "hash": content_hash, "record_type": _SELF_ATTEST_TYPE,
            "auto_gradable": False, "counts_as_check": False}


# ── Shared study — a "study_maps" shelf (superposition): one card lives once, referenced ──────────

def study_create(study_key: str, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create/extend a shared study as a study_maps stack. Each entry mints ONE card (lives once via
    stacks.put_card) and is referenced into the study by key — no duplication (superposition model).

    `cards` is a list of {text, kind?, topics?}. Returns {study, count, card_ids}. Conduit: the card
    holds the person's own (or found/verified) material, verbatim — nothing generated.
    """
    card_ids: List[str] = []
    for c in (cards or []):
        if not isinstance(c, dict):
            continue
        text = str(c.get("text", ""))
        kind = str(c.get("kind", "study"))
        topics = list(c.get("topics") or [])
        card = stacks.put_card(text, kind=kind, topics=topics, source="study")
        stacks.add_to_stack(_STUDY_KIND, study_key, card["id"])
        card_ids.append(card["id"])
    st = stacks.get_stack(_STUDY_KIND, study_key)
    return {"study": study_key, "count": st["count"], "card_ids": card_ids}


def study_export(study_key: str, *, private_key: Optional[str] = None) -> Dict[str, Any]:
    """Export a study as a self-contained, portable bundle (optionally signed).

    The bundle carries each referenced card in full (so it travels without our store) plus a
    content_hash over its contents. If `private_key` is given AND signing is available, it also
    carries an Ed25519 attestation over that hash (signed=True); otherwise signed=False and export
    still succeeds — a study is meant to be OWNED and carried, signature or not (John 3:30).
    """
    st = stacks.get_stack(_STUDY_KIND, study_key)
    cards: List[Dict[str, Any]] = []
    for brief in st.get("cards", []):
        cid = brief.get("id")
        full = stacks.get_card(cid, bump=False) if cid else None
        if full:
            # Export the portable card content, not our internal tiering bookkeeping.
            cards.append({"kind": full.get("kind", "study"), "text": full.get("text", ""),
                          "topics": full.get("topics") or [], "source": full.get("source", "study")})
    bundle: Dict[str, Any] = {
        "record_type": _STUDY_EXPORT_TYPE,
        "schema": "nh-study-1",
        "study": study_key,
        "cards": cards,
        "count": len(cards),
        "generated": False,
        "exported_at": round(time.time(), 3),
    }
    content_hash = cas.content_hash_of(bundle)
    bundle["content_hash"] = content_hash

    signed = False
    if private_key:
        try:
            if identity.signing_available():
                bundle["attestation"] = signing.sign_seal(content_hash, private_key)
                signed = True
        except Exception:  # noqa: BLE001 — signing optional; export never hard-fails without it
            signed = False
    bundle["signed"] = signed
    return bundle


def study_import(bundle: Dict[str, Any], *, study_key: Optional[str] = None,
                 verify_signature: bool = False) -> Dict[str, Any]:
    """Import an exported study bundle: re-materialize its cards (each lives once) and reference them
    into the target study_maps stack. Returns {study, count, card_ids, signature_valid?}.

    Roundtrips with study_export. If `verify_signature` is set and signing is available, the bundle's
    attestation is checked against its content_hash and reported — but a study still imports whether
    or not it is signed (the cards are the substance)."""
    if not isinstance(bundle, dict) or bundle.get("record_type") != _STUDY_EXPORT_TYPE:
        return {"ok": False, "error": "not a study export bundle", "count": 0, "card_ids": []}
    target = study_key or str(bundle.get("study") or "imported")

    sig_valid: Optional[bool] = None
    if verify_signature:
        att = bundle.get("attestation")
        ch = bundle.get("content_hash")
        if att is not None and ch:
            try:
                ok, _ = signing.verify_seal(ch, att)
            except Exception:  # noqa: BLE001 — verification is total
                ok = False
            sig_valid = ok
        else:
            sig_valid = False

    card_ids: List[str] = []
    for c in (bundle.get("cards") or []):
        if not isinstance(c, dict):
            continue
        card = stacks.put_card(str(c.get("text", "")), kind=str(c.get("kind", "study")),
                               topics=list(c.get("topics") or []), source="study")
        stacks.add_to_stack(_STUDY_KIND, target, card["id"])
        card_ids.append(card["id"])
    st = stacks.get_stack(_STUDY_KIND, target)
    out: Dict[str, Any] = {"ok": True, "study": target, "count": st["count"], "card_ids": card_ids}
    if sig_valid is not None:
        out["signature_valid"] = sig_valid
    return out


def study_get(study_key: str) -> Dict[str, Any]:
    """Resolve a study to its cards (a view over the study_maps stack — the cards live once)."""
    return stacks.get_stack(_STUDY_KIND, study_key)


def guidance() -> Dict[str, Any]:
    """What a badge is — and, load-bearing, what it will NOT claim."""
    return {
        "identity": "A badge is a re-checkable receipt: it points at N seals that still stand.",
        "is": [
            "content-addressed and re-checkable from the existing floor (fetch, then re-verify seals)",
            "a receipt the person OWNS and can carry away (portable; optionally signed)",
            "stated as EXACTLY N sealed checks — 'N verifications sealed'",
        ],
        "will_not": [
            "claim mastery, skill, level, or competency of any kind",
            "count a self-attestation as a sealed check (self-attestation is a distinct type)",
            "invent a new trust primitive — the seals ARE the evidence",
        ],
        "note": ("Success is you needing the tool LESS (John 3:30). A badge reports, re-checkably, how "
                 "many verifications you sealed — nothing about how good you are."),
    }


__all__ = [
    "badge_copy",
    "issue_badge",
    "verify_badge",
    "self_attest",
    "study_create",
    "study_export",
    "study_import",
    "study_get",
    "guidance",
]
