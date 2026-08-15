"""THE GATE KERNEL, WIRED — the write paths now EMIT the nine-field record into their own trails.

Matt, 2026-07-25: the kernel is "the doctrine those arms embody." It was reachable (GET /kernel,
POST /kernel/gate, MCP) but the real state-changes still wrote their own per-subsystem records and
never routed through it. These tests hold each wired path to two things at once:

  1. the record is COMPLETE — all nine fields, a real verdict, an authority the monotonic law
     allows (never 'verified' on any of these paths — a save, a promote, a fetch, a seal may not
     launder low authority into high); and
  2. the record AGREES with what the path already does — a member drop and a fetched acquisition
     land QUARANTINE (held at the member/quarantined tier); a steward promote/refuse amplifies or
     withholds but never verifies (QUARANTINE); a member withdrawal is a retraction (REJECT); a
     sealed candidate set is proposals, born quarantined (QUARANTINE).

Pure: signing is real Ed25519 (skipped if unavailable), the tortoise's providers are stubbed so no
network is touched, and every store is a fresh temp dir. Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import kernel  # noqa: E402

NINE = ("entered", "kind", "authority_in", "passed", "failed",
        "assumptions", "changed", "preserved", "safe_next")
STEWARD_TOKEN = "steward-token-for-this-test-only"


def _assert_record(rec: dict) -> None:
    """Every emitted record is the WHOLE nine-field trail, with a real verdict and a lawful
    authority — and NEVER 'verified' on a write path (only a witnessed, evidenced gate raises)."""
    assert isinstance(rec, dict), rec
    for f in NINE:
        assert f in rec, f"missing gate-record field {f!r}"
    assert rec["verdict"] in kernel.VERDICTS
    assert rec["authority_out"] in kernel.AUTHORITY
    assert rec["authority_out"] != "verified", "no write path may reach 'verified' (monotonic law)"


# ── the shelves: a member drop, and a steward/member curation ────────────────────────────────────
@pytest.fixture()
def _shelf_env():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    prior_tok = os.environ.get("CONCORDANCE_KEEP_TOKEN")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-kw-")
    os.environ["CONCORDANCE_KEEP_TOKEN"] = STEWARD_TOKEN
    yield
    for k, v in (("CONCORDANCE_DATA_DIR", prior), ("CONCORDANCE_KEEP_TOKEN", prior_tok)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _key():
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001 — no cryptography on this box
        pytest.skip("signing unavailable in this build")


def _make_drop(ring="commons", body="A drop the whole fellowship should see, in the member's own "
                                    "words, long enough to be a real drop.", name="Matt Harris"):
    from concordance import shelves, signing
    priv, pub = _key()
    sg = shelves.signable_drop(pub, "note", "On patience", body, ring)
    assert sg.get("ok"), sg
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    return shelves.drop(sg["fields"], sig, display_name=name), pub, priv


def test_a_member_drop_emits_a_quarantine_record_on_the_card_and_the_wire(_shelf_env):
    """A commons drop is COMMUNITY work: it lands QUARANTINE at the member tier, and the record
    rides both on the persisted card (drops.jsonl -> shelf view) and in the drop response."""
    from concordance import shelves
    r, pub, _ = _make_drop(ring="commons")
    assert r["ok"] and r["authority_tier"] == shelves.MEMBER_TIER
    # on the wire
    _assert_record(r["record"])
    assert r["record"]["verdict"] == "QUARANTINE" and r["record"]["authority_out"] == "quarantined"
    assert r["record"]["kind"] == "community", "a commons drop is shared -> community"
    # and persisted on the card itself
    card = shelves.shelf_of(pub, viewer=pub)["cards"][0]
    persisted = card["extra"]["gate_record"]
    _assert_record(persisted)
    assert persisted == r["record"], "the card's record and the wire's record are one and the same"


def test_a_private_drop_is_typed_a_user_note_still_quarantined(_shelf_env):
    """A `shelf`/`private` drop is the member's own note — user_note, still born quarantined."""
    r, _pub, _ = _make_drop(ring="shelf", body="Something for my own shelf, in my own words, kept.")
    _assert_record(r["record"])
    assert r["record"]["kind"] == "user_note"
    assert r["record"]["verdict"] == "QUARANTINE" and r["record"]["authority_out"] == "quarantined"


def test_a_steward_promote_records_amplification_never_verification(_shelf_env):
    """The library carrying a voice is not the library agreeing with it: a promote AMPLIFIES but
    the record stays QUARANTINE and never reaches 'verified' — the monotonic law, on the act."""
    from concordance import shelves
    r, _pub, _ = _make_drop(ring="commons")
    act = shelves.curate(r["card_id"], "promoted", "matt", "sound, and useful to a beginner",
                         token=STEWARD_TOKEN)
    assert act["ok"]
    _assert_record(act["record"])
    assert act["record"]["verdict"] == "QUARANTINE"
    # and the same record is in the append-only curation trail
    trail = shelves.history(r["card_id"])["acts"][0]["record"]
    assert trail == act["record"]


def test_a_steward_refusal_records_a_withholding_quarantine(_shelf_env):
    from concordance import shelves
    r, _pub, _ = _make_drop(ring="commons")
    act = shelves.curate(r["card_id"], "refused", "matt", "not checkable, reads as advice",
                         token=STEWARD_TOKEN)
    assert act["ok"]
    _assert_record(act["record"])
    assert act["record"]["verdict"] == "QUARANTINE"


def test_a_member_withdrawal_records_a_retraction_reject(_shelf_env):
    """A withdrawal is a retraction — a floor — so the kernel REJECTS it: do not cite, serve, seal."""
    from concordance import shelves, signing
    r, pub, priv = _make_drop(ring="shelf")
    sg = shelves.signable_curate(r["card_id"], pub)
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    act = shelves.curate(r["card_id"], "withdrawn", "Matt Harris", "changed my mind",
                         fields=sg["fields"], signature=sig)
    assert act["ok"] and act["by"] == "member"
    _assert_record(act["record"])
    assert act["record"]["verdict"] == "REJECT", "a retraction is a floor failure"


# ── the tortoise: a fetched acquisition lands a QUARANTINE record ─────────────────────────────────
def test_a_tortoise_acquisition_carries_a_quarantine_record():
    """find._mint_doc keeps a fetched PD source in `public_review`, withheld until a human looks.
    The minted card must carry the nine-field record, typed community (held), verdict QUARANTINE."""
    import tempfile as _tf
    from concordance import find
    from concordance.config import EngineConfig
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    prior_dis = os.environ.get("WEB_FIND_DISABLED")
    os.environ["CONCORDANCE_DATA_DIR"] = _tf.mkdtemp(prefix="nh-kw-find-")
    os.environ.pop("WEB_FIND_DISABLED", None)
    saved = (find.internet_archive, find.project_gutenberg, find.library_of_congress)
    find.internet_archive = lambda q, limit=3, practical=None: []
    find.project_gutenberg = lambda q, limit=3, practical=None: []
    find.library_of_congress = lambda q, limit=3, practical=None: [
        {"title": "The sinking of the Titanic", "url": "http://www.loc.gov/item/titanic/",
         "format": "book", "source": "Library of Congress", "license": "PD", "tier": "primary"}]
    try:
        r = find.find_and_check("what year did the Titanic sink", EngineConfig("secular"))
        assert r is not None
        cards = [json.loads(l) for l in find._store_path().read_text(encoding="utf-8").splitlines()
                 if l.strip()]
        card = next(c for c in cards if c["title"] == "The sinking of the Titanic")
        assert card["lifecycle_stage"] == "public_review"
        rec = card["gate_record"]
        _assert_record(rec)
        assert rec["verdict"] == "QUARANTINE" and rec["authority_out"] == "quarantined"
        assert rec["kind"] == "community", "a card held in public_review types as held/community"
    finally:
        find.internet_archive, find.project_gutenberg, find.library_of_congress = saved
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        if prior_dis is None:
            os.environ.pop("WEB_FIND_DISABLED", None)
        else:
            os.environ["WEB_FIND_DISABLED"] = prior_dis


# ── candidates: the receipt seals a QUARANTINE record over the whole set ──────────────────────────
def test_a_candidate_receipt_seals_a_quarantine_record_and_stays_content_addressed():
    """A candidate set is Zone B — proposals, born quarantined. Sealing is process integrity,
    never truth: the receipt carries a QUARANTINE record, typed generated_draft, and the record
    is content-addressed WITH the rest of the receipt (the seal stays reproducible)."""
    from concordance import candidates as cand
    from concordance import cas as _cas
    cs = cand.create_set("2 + 2 and a claim",
                         ["2+2=4", "2+2=5", "the kingdom = heaven"],
                         generator="model-x/1.0", generation_method="direct")
    cand.commit(cs)
    cand.route(cs)
    cand.narrow(cs)
    out = cand.receipt(cs)
    rec = out["record"]
    grec = rec["gate_record"]
    _assert_record(grec)
    assert grec["kind"] == "generated_draft"
    assert grec["verdict"] == "QUARANTINE" and grec["authority_out"] == "quarantined"
    # the gate record is INSIDE the sealed, content-addressed record — re-checkable by anyone
    assert _cas.content_hash_of(rec) == out["content_hash"]
    # winning the narrowing did not verify the set: even a lone survivor stays unverified here
    assert all(c["verification_status"] in ("pass", "reject", "quarantine")
               for c in rec["candidates"])


# ── the crosscut: none of these paths may EVER reach 'verified' (the monotonic law) ───────────────
def test_no_write_path_launders_authority_to_verified():
    """The whole point, stated once more as a law over the module surface: a save, a promote, a
    refuse, a fetch, and a seal are all NON-UPGRADING — only op=='gate' with real evidence AND an
    independent witness reaches 'verified'. None of the wired calls pass evidence, so none can."""
    for op in ("save", "store", "cite", "seal", "sign", "import", "generate", "popularity"):
        assert not kernel.monotonic_ok(op, "quarantined", "verified"), op
        assert not kernel.monotonic_ok(op, "cited", "verified"), op
    assert kernel.monotonic_ok("gate", "quarantined", "verified"), "only the gate raises"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
