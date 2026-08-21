"""Ez-login + profile — sovereign, opt-in, no account, no password.

A human derives their key from a passphrase (their verses); an agent holds a key. Both resolve to one
fingerprint, and the profile follows it. Writes are signed, so only the owner can change it; the default
is anonymous. Pure — profiles write to a temp dir.
"""
import pytest

from concordance import identity, profile, signing


def _sign_put(idn, patch, nonce):
    sig = signing.sign_bytes(profile.signable(idn["public_key"], patch, nonce), idn["private_key"])
    return profile.put(idn["public_key"], patch, nonce, sig)


def test_ez_login_is_deterministic_from_the_passphrase():
    a = identity.derive_identity("in the beginning was the Word and the Word was with God")
    b = identity.derive_identity("in the beginning was the Word  and the Word was with God ")  # spacing differs
    assert a["id"] == b["id"] and a["public_key"] == b["public_key"]   # same verses -> same key, anywhere
    assert a["derived"] is True and a["private_key"]                   # yours to keep, never stored by us


def test_a_different_passphrase_is_a_different_identity():
    a = identity.derive_identity("the Lord is my shepherd I shall not want")
    b = identity.derive_identity("the Lord is my shepherd I shall not fear")
    assert a["id"] != b["id"]


def test_a_weak_passphrase_is_refused():
    with pytest.raises(ValueError):
        identity.derive_identity("short")


def test_the_profile_follows_the_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    me = identity.derive_identity("give us this day our daily bread and forgive us")
    r = _sign_put(me, {"shelf": ["card_1", "card_2"], "display_name": "a pilgrim"}, "n1")
    assert r["ok"] and r["profile"]["shelf"] == ["card_1", "card_2"]
    assert profile.get(me["id"])["display_name"] == "a pilgrim"        # it follows the fingerprint


def test_only_the_owner_can_write(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    me = identity.derive_identity("create in me a clean heart O God renew")
    forger = identity.create_identity()
    sig = signing.sign_bytes(profile.signable(me["public_key"], {"x": 1}, "n1"), forger["private_key"])
    r = profile.put(me["public_key"], {"x": 1}, "n1", sig)             # forger's signature, my key
    assert r["ok"] is False and "signature" in r["error"]


def test_replay_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    me = identity.derive_identity("be still and know that I am God almighty")
    assert _sign_put(me, {"a": 1}, "n1")["ok"]
    assert _sign_put(me, {"a": 2}, "n1")["ok"] is False               # same nonce -> replay refused


def test_anonymous_is_the_default(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    assert profile.get("nobody-has-this-fingerprint") == {}           # no key, no profile, free as ever


def test_agent_and_human_share_one_profile_system(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    agent = identity.create_identity()                                # an agent holds a key
    r = _sign_put(agent, {"wants": ["a manual on digging wells"]}, "n1")
    assert r["ok"] and profile.get(agent["id"])["wants"] == ["a manual on digging wells"]


def test_a_signed_delete_takes_it_back(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    me = identity.derive_identity("the truth will set you free indeed friend")
    _sign_put(me, {"a": 1}, "n1")
    sig = signing.sign_bytes(profile.signable(me["public_key"], {}, "del1"), me["private_key"])
    assert profile.delete(me["public_key"], "del1", sig)["ok"]
    assert profile.get(me["id"]) == {}                                # erased — it was yours to take back
