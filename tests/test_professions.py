"""Professions of faith, witnessed and kept (2026-10-06).

A profession is sealed as a record; the confessor self-attests and fellow believers bear witness (two or
three establish a matter, Deut 19:15); the lineage roots at Polycarp, the disciple of a disciple; and the
engine keeps but never judges — a non-confession is met with the invitation, not stored."""
import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-prof-")
os.environ["CONCORDANCE_DATA_DIR"] = TMP

import pytest                                                   # noqa: E402

from concordance import professions as P                        # noqa: E402
from concordance import identity, signing                       # noqa: E402

_HAVE_CRYPTO = identity.signing_available()
_needs_crypto = pytest.mark.skipif(not _HAVE_CRYPTO, reason="ed25519 signing unavailable")

CONF = "Jesus Christ is Lord and Messiah"


def test_the_root_is_polycarp_the_disciple_of_a_disciple():
    h = P.ensure_root()
    assert h == P.root_hash()                                   # content-addressed: sealed once, same hash
    pro = P.profession(h)
    assert pro["ok"] and pro["root"] is True
    assert pro["witness"] == "Polycarp of Smyrna"
    assert "86" in pro["confession"] or "Eighty" in pro["confession"]
    assert pro["lineage"]["chain"][-1]["root"] is True
    assert pro["lineage"]["head"] == "Jesus Christ"


def test_a_non_confession_is_invited_never_stored():
    _priv, pub = signing.generate_keypair() if _HAVE_CRYPTO else ("", "k" * 43)
    r = P.seal(pub, "I think the universe is interesting")
    assert r.get("ok") is False and r.get("gated") is True       # the gate invites; it does not store


def test_confession_is_permissive_on_wording():
    _priv, pub = signing.generate_keypair() if _HAVE_CRYPTO else ("", "k" * 43)
    r = P.seal(pub, "I believe Jesus is Lord and the Messiah who saved me", callsign="seeker")
    assert r["ok"] and r["sealed"] is True


@_needs_crypto
def test_seal_binds_the_self_signature_and_joins_the_root():
    priv, pub = signing.generate_keypair()
    sig = signing.sign_bytes(CONF.encode("utf-8"), priv)
    r = P.seal(pub, CONF, callsign="grok", confession_sig=sig)
    assert r["ok"] and r["self_signed"] is True
    assert r["lineage_root"] == P.root_hash()
    pro = P.profession(r["content_hash"])
    assert pro["discipled_by"] == P.root_hash()                  # joins the lineage at Polycarp by default
    # the lineage walks child -> Polycarp root
    assert pro["lineage"]["chain"][-1]["witness"] == "Polycarp of Smyrna"


@_needs_crypto
def test_two_or_three_witnesses_begin_to_establish_it():
    priv, pub = signing.generate_keypair()
    r = P.seal(pub, CONF, callsign="grok")
    h = r["content_hash"]
    # the confessor self-attests (witness #1): signs the SEAL with their own key
    w1 = P.witness(h, signing.sign_seal(h, priv))
    assert w1["ok"] and w1["witnesses"] == 1 and w1["established"] is False
    # a fellow believer bears witness (#2): now it begins to be established
    priv2, _pub2 = signing.generate_keypair()
    w2 = P.witness(h, signing.sign_seal(h, priv2))
    assert w2["ok"] and w2["witnesses"] == 2 and w2["established"] is True
    # the same witness repeating adds nothing (no self-multiplying witness)
    again = P.witness(h, signing.sign_seal(h, priv2))
    assert again.get("already") is True and again["witnesses"] == 2
    pro = P.profession(h)
    assert pro["witnesses"] == 2 and pro["established"] is True


@_needs_crypto
def test_the_witness_gate_is_not_borrowed_for_other_records():
    from concordance import cas
    other = cas.store({"kind": "not_a_profession", "text": "hello"})
    priv, _pub = signing.generate_keypair()
    r = P.witness(other, signing.sign_seal(other, priv))
    assert r["ok"] is False and "not a profession" in r["error"]
