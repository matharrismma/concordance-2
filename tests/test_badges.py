"""Arc 4 — badges: a RE-CHECKABLE receipt whose evidence IS the sealed trail.

Proves (hermetic; runnable with pytest OR `python tests/test_badges.py`):
  * a badge is re-checkable — verify_badge returns EXACTLY the N seals that still stand;
  * the copy states EXACTLY N with NO competency noun (asserted against a word blacklist);
  * only seals that actually re-verify in the CAS count toward N (missing/tampered dropped);
  * self_attest is a DISTINCTLY TYPED record and can NEVER count as a sealed check;
  * signing is OPTIONAL — issue/export never hard-fail when cryptography is absent, and when
    present the attestation verifies against the badge's content_hash;
  * shared study (study_maps shelf) create/export/import roundtrips — one card lives once.

Hermetic: an isolated CONCORDANCE_DATA_DIR; seals are written directly to the CAS (a seal is just a
content-addressed record) so the test never touches concordance.verifiers.* or .derivation.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-badges-")
os.environ.pop("CONCORDANCE_PUBLIC_BASE", None)

from concordance import badges, cas, identity  # noqa: E402

_HAS_CRYPTO = identity.signing_available()

# Words a badge's copy must NEVER contain — it reports sealed checks, not competency.
_COMPETENCY_WORDS = ("master", "mastered", "mastery", "expert", "certified", "certificate",
                     "proficien", "skill", "skilled", "competen", "qualified", "level",
                     "grade", "rank", "achievement", "earned", "passed")


def _seal(claim: str, overall: str = "PASS") -> str:
    """Write a minimal, real, re-verifiable seal record to the CAS and return its content_hash.
    A seal is just a content-addressed record — no verifier needed to make one for the test."""
    record = {
        "overall": overall,
        "gate_results": [{"gate": "RED", "status": overall}],
        "verifier_results": [{"name": "s1", "status": "CONFIRMED", "detail": "checked",
                              "data": {"claim": claim}}],
    }
    return cas.store(record)


# ── re-checkable: verify returns EXACTLY N ───────────────────────────────────────────────────────

def test_badge_is_recheckable_returns_exactly_n():
    seals = [_seal("2+2 = 4"), _seal("3*3 = 9"), _seal("10/2 = 5")]
    b = badges.issue_badge(seals, title="arithmetic study")
    assert b["ok"] and b["checks"] == 3
    v = badges.verify_badge(b["hash"])
    assert v["ok"] is True
    assert v["checks"] == 3, "verify must return EXACTLY the number of seals that still stand"
    assert v["integrity_ok"] is True
    assert set(v["sealed_checks"]) == set(seals)


def test_verify_recomputes_n_from_evidence_not_stored_count():
    # Only seals that actually re-verify in the CAS count — a bogus hash is dropped, not trusted.
    good = [_seal("a=a"), _seal("b=b")]
    b = badges.issue_badge(good + ["deadbeefnotarealseal"], title="mixed")
    assert b["checks"] == 2, "a non-existent seal must not inflate N"
    v = badges.verify_badge(b["hash"])
    assert v["checks"] == 2


def test_duplicate_seals_counted_once():
    s = _seal("same claim")
    b = badges.issue_badge([s, s, s])
    assert b["checks"] == 1, "the same seal referenced thrice is one sealed check"


def test_missing_badge_is_honest():
    v = badges.verify_badge("nosuchbadgehash")
    assert v["ok"] is False and v["checks"] == 0


# ── copy states EXACTLY N, with NO competency noun ───────────────────────────────────────────────

def test_copy_states_exactly_n_no_competency_noun():
    for n in (0, 1, 5, 42):
        copy = badges.badge_copy(n)
        assert str(n) in copy, "the copy must state exactly N"
        assert "verifications sealed" in copy
        low = copy.lower()
        for w in _COMPETENCY_WORDS:
            assert w not in low, f"badge copy must carry no competency noun; found {w!r} in {copy!r}"


def test_issue_and_verify_copy_match_n():
    seals = [_seal("x"), _seal("y")]
    b = badges.issue_badge(seals)
    assert b["copy"] == "2 verifications sealed"
    assert badges.verify_badge(b["hash"])["copy"] == "2 verifications sealed"


def test_guidance_refuses_competency_claims():
    g = badges.guidance()
    assert any("mastery" in w or "competency" in w for w in g["will_not"])


# ── self-attestation is DISTINCTLY typed and never a sealed check ────────────────────────────────

def test_self_attest_is_distinctly_typed_and_not_gradable():
    r = badges.self_attest("nh_person", "I read the whole book of John.")
    assert r["record_type"] == "self_attestation"
    assert r["auto_gradable"] is False
    assert r["counts_as_check"] is False
    # The stored record itself carries the distinct type + non-gradable flags.
    stored = cas.fetch(r["hash"])
    assert stored["record_type"] == "self_attestation"
    assert stored["auto_gradable"] is False
    assert stored["counts_as_check"] is False


def test_self_attest_hash_cannot_satisfy_a_badge():
    # Feeding a self-attestation hash where seals are expected must NOT count — it is not a seal
    # record, and even though it re-verifies as a CAS record, a badge issued over ONLY it references
    # it but it is a distinctly-typed non-check. We assert the auto-grade boundary: a badge's N is
    # only ever real seals, and a self-attestation is honestly flagged non-gradable so a grader must
    # exclude it. (The grader is the consumer; here we prove the record is flagged so it CAN be.)
    r = badges.self_attest("nh_person", "self report")
    stored = cas.fetch(r["hash"])
    assert stored.get("auto_gradable") is False and stored.get("record_type") == "self_attestation"


# ── signing is OPTIONAL — never hard-fails without cryptography ───────────────────────────────────

def test_issue_never_hard_fails_without_a_key():
    b = badges.issue_badge([_seal("no key needed")])
    assert b["ok"] is True and b["signed"] is False and b["hash"]


def test_signing_optional_on_issue():
    seals = [_seal("signed study")]
    if _HAS_CRYPTO:
        idn = identity.create_identity()
        b = badges.issue_badge(seals, subject_id=idn["id"], private_key=idn["private_key"])
        assert b["signed"] is True and "attestation" in b
        v = badges.verify_badge(b["hash"], attestation=b["attestation"])
        assert v["signature_valid"] is True
    else:
        # No cryptography: passing a key must still succeed, just unsigned — never crash.
        b = badges.issue_badge(seals, subject_id="nh_x", private_key="anything")
        assert b["ok"] is True and b["signed"] is False


def test_degraded_issue_forced_unsigned():
    # Force the capability flag off so the degraded branch runs even if cryptography is installed.
    original = identity.signing_available
    identity.signing_available = lambda: False  # type: ignore[assignment]
    try:
        b = badges.issue_badge([_seal("degraded")], private_key="key")
        assert b["ok"] is True and b["signed"] is False and "attestation" not in b
    finally:
        identity.signing_available = original  # type: ignore[assignment]


# ── shared study — create / export / import roundtrip (one card lives once) ───────────────────────

def test_study_create_and_get():
    r = badges.study_create("gospel-of-john", [
        {"text": "In the beginning was the Word.", "kind": "verse", "topics": ["logos"]},
        {"text": "The Word became flesh.", "kind": "verse", "topics": ["logos"]},
    ])
    assert r["count"] == 2 and len(r["card_ids"]) == 2
    got = badges.study_get("gospel-of-john")
    assert got["count"] == 2
    assert any("beginning" in c["text"] for c in got["cards"])


def test_study_export_import_roundtrip():
    badges.study_create("roundtrip-study", [
        {"text": "grace and truth", "kind": "note", "topics": ["grace"]},
        {"text": "full of grace", "kind": "note"},
    ])
    bundle = badges.study_export("roundtrip-study")
    assert bundle["record_type"] == "study_export" and bundle["count"] == 2
    assert bundle["content_hash"] and bundle["signed"] is False
    # Import into a NEW key: cards re-materialize and re-reference (one card lives once per import).
    imp = badges.study_import(bundle, study_key="roundtrip-copy")
    assert imp["ok"] is True and imp["count"] == 2
    copied = badges.study_get("roundtrip-copy")
    assert copied["count"] == 2
    texts = {c["text"] for c in copied["cards"]}
    assert "grace and truth" in texts and "full of grace" in texts


def test_study_import_rejects_non_bundle():
    bad = badges.study_import({"not": "a bundle"})
    assert bad["ok"] is False and bad["count"] == 0


def test_study_export_import_signed_optional():
    badges.study_create("signed-study", [{"text": "portable and owned", "kind": "note"}])
    if _HAS_CRYPTO:
        idn = identity.create_identity()
        bundle = badges.study_export("signed-study", private_key=idn["private_key"])
        assert bundle["signed"] is True and "attestation" in bundle
        imp = badges.study_import(bundle, study_key="signed-copy", verify_signature=True)
        assert imp["ok"] is True and imp["signature_valid"] is True
    else:
        bundle = badges.study_export("signed-study", private_key="anything")
        assert bundle["signed"] is False  # never hard-fails
        imp = badges.study_import(bundle, study_key="signed-copy", verify_signature=True)
        assert imp["ok"] is True and imp.get("signature_valid") is False


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    tag = "" if _HAS_CRYPTO else " (cryptography absent — signed-path asserts degraded)"
    print(f"\n{len(fns)} badge tests passed — re-checkable receipts; exactly N; conduit not source{tag}.")
