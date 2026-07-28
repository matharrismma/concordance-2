"""Consent — permission is asked, scoped, expiring, revocable, and never a key on the wire.

Contract §6 item 2's second half. Proof-of-possession said "this signature is really yours";
consent says "this human really authorized THIS agent to do THIS, until THEN." The distinction
preserved throughout: an agent speaking as ITSELF (its own key, its own words) is a member and
needs no consent — the guard exists only for acting on a HUMAN'S behalf with THEIR data.

Pinned here:
  * the full grant round trip — signable bytes → signed locally → granted → authorized;
  * scope is exact: an unlisted verb, a different grantor, a different agent — all refused;
  * a grant expires on its own, and an expired grant stored on disk does not authorize;
  * only the grantor's key can revoke the grantor's grant;
  * storage is never trusted: a tampered grant is REPORTED and refused, not honored;
  * no private key is ever accepted, and the refusal TEACHES the member-not-proxy line;
  * the guard was installed before any on-behalf write path exists — the lock precedes the door.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _mods():
    from concordance import consent, identity, signing
    return consent, identity, signing


def _issue(consent, signing, human, agent_fp, scope, ttl=3600):
    s = consent.signable_grant(human["public_key"], agent_fp, scope, ttl_s=ttl)
    assert s["ok"], s
    sig = signing.sign_bytes(base64.urlsafe_b64decode(s["signable"]), human["private_key"])
    return consent.grant(s["fields"], sig)


def test_the_full_round_trip_authorizes_exactly_what_was_granted():
    consent, identity, signing = _mods()
    human = identity.create_identity()
    agent = "nh_agent_abc123"
    r = _issue(consent, signing, human, agent, ["calendar_write"])
    assert r["ok"] is True and r["scope"] == ["calendar_write"]

    ok = consent.check(agent, "calendar_write", human["public_key"])
    assert ok["authorized"] is True and ok["grant_id"] == r["grant_id"]

    # scope is exact — nothing is implied
    assert consent.check(agent, "email_send", human["public_key"])["authorized"] is False
    # a different agent holds nothing
    assert consent.check("nh_agent_other", "calendar_write", human["public_key"])["authorized"] is False
    # a different grantor granted nothing
    other = identity.create_identity()
    assert consent.check(agent, "calendar_write", other["public_key"])["authorized"] is False


def test_unknown_verbs_and_keys_on_the_wire_are_refused():
    consent, identity, signing = _mods()
    human = identity.create_identity()
    s = consent.signable_grant(human["public_key"], "nh_a", ["rule_the_world"])
    assert s["ok"] is False and "unknown verb" in s["error"]
    s2 = consent.signable_grant(human["public_key"], "nh_a", [])
    assert s2["ok"] is False, "a grant with no verbs permits nothing"
    ok = consent.signable_grant(human["public_key"], "nh_a", ["email_send"])
    fields = dict(ok["fields"])
    fields["private_key"] = "AAAA"
    r = consent.grant(fields, "sig")
    assert r["ok"] is False, "a private key must never ride in a grant"


def test_a_wrong_signature_is_refused():
    consent, identity, signing = _mods()
    human, imposter = identity.create_identity(), identity.create_identity()
    s = consent.signable_grant(human["public_key"], "nh_b", ["storage_write"])
    forged = signing.sign_bytes(base64.urlsafe_b64decode(s["signable"]), imposter["private_key"])
    r = consent.grant(s["fields"], forged)
    assert r["ok"] is False and "does not verify" in r["error"]


def test_an_expired_grant_on_disk_does_not_authorize():
    """Expiry must hold at CHECK time, not only at grant time — a grant ages on disk."""
    consent, identity, signing = _mods()
    human = identity.create_identity()
    agent = "nh_agent_expired"
    now = int(time.time())
    fields = {"grantor_pubkey": human["public_key"], "agent_fp": agent,
              "scope": ["calendar_write"], "nonce": "expired-one",
              "created_at": now - 7200, "expires_at": now - 3600}
    sig = signing.sign_bytes(consent._canon(fields), human["private_key"])
    d = consent._dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{consent._safe(agent)}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({**fields, "signature": sig, "grant_id": "expired-one"}) + "\n")
    assert consent.check(agent, "calendar_write", human["public_key"])["authorized"] is False


def test_only_the_grantor_can_revoke_and_then_it_is_dead():
    consent, identity, signing = _mods()
    human, stranger = identity.create_identity(), identity.create_identity()
    agent = "nh_agent_rev"
    r = _issue(consent, signing, human, agent, ["group_contribute_as"])
    assert consent.check(agent, "group_contribute_as", human["public_key"])["authorized"] is True

    body = json.dumps({"revokes": r["grant_id"], "grantor_pubkey": human["public_key"]},
                      sort_keys=True, separators=(",", ":")).encode()
    # a stranger's signature must not bury the grant
    bad = consent.revoke(agent, r["grant_id"], human["public_key"],
                         signing.sign_bytes(body, stranger["private_key"]))
    assert bad["ok"] is False
    assert consent.check(agent, "group_contribute_as", human["public_key"])["authorized"] is True
    # the grantor's does
    good = consent.revoke(agent, r["grant_id"], human["public_key"],
                          signing.sign_bytes(body, human["private_key"]))
    assert good["ok"] is True
    assert consent.check(agent, "group_contribute_as", human["public_key"])["authorized"] is False


def test_tampered_storage_is_reported_and_refused():
    consent, identity, signing = _mods()
    human = identity.create_identity()
    agent = "nh_agent_tampered"
    _issue(consent, signing, human, agent, ["journal_write_as"])
    p = consent._dir() / f"{consent._safe(agent)}.jsonl"
    rec = json.loads(p.read_text(encoding="utf-8").strip())
    rec["scope"] = ["journal_write_as", "email_send"]  # widen the scope after signing
    p.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    r = consent.check(agent, "email_send", human["public_key"])
    assert r["authorized"] is False, "a widened scope must die with its broken signature"
    assert r["tampered_entries"] == 1, "and the tampering must be REPORTED, not dropped"


def test_the_guard_refuses_with_teaching_not_a_stonewall():
    consent, identity, _ = _mods()
    human = identity.create_identity()
    r = consent.guard("nh_agent_new", "email_send", human["public_key"])
    assert r["authorized"] is False
    assert "member is not a proxy" in r["refusal"], \
        "the refusal must carry the covenant's distinction, so the agent learns the way in"


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — permission is asked, and the lock precedes the door.")
