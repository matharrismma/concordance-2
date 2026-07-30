"""THE COMMONS · C1a — the member shelf, as behaviour.

Matt: *"Think of it like a giant library with everyone having their own shelf to stock."* And:
*"We can curate and evaluate before we make available."*

What is pinned here is what protects a member:

  * **nobody can put words on your shelf** — a drop without your signature is refused, and a
    signature over different bytes does not transfer;
  * **the gate is on amplification, not speech** — a shelf drop is live the moment it is signed;
    only a `commons` drop waits, and only for a HUMAN steward;
  * **member tier is never upgraded** — promotion carries the words to the commons without
    turning them into the library's claim;
  * **private stays private** — another member's view never contains it, and the public
    boundary (`corpus.is_public`) agrees;
  * **no anonymous judgement, no reasonless act** — every curation carries a steward and a why;
  * **append-only** — a withdrawal hides the card from the shelf view and keeps the record.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


STEWARD_TOKEN = "steward-token-for-this-test-only"


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    prior_tok = os.environ.get("CONCORDANCE_KEEP_TOKEN")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
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


def _drop(kind="note", subject="On patience", body="A long enough body to be a real drop, "
                                                   "written by a member in their own words.",
          ring="shelf", name="Matt Harris", key=None):
    from concordance import shelves, signing
    priv, pub = key or _key()
    sg = shelves.signable_drop(pub, kind, subject, body, ring)
    assert sg.get("ok"), sg
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    return shelves.drop(sg["fields"], sig, display_name=name), pub, (priv, pub)


def test_a_member_stocks_their_own_shelf_and_it_carries_their_name():
    from concordance import shelves
    r, pub, _ = _drop()
    assert r["ok"] and r["ring"] == "shelf"
    view = shelves.shelf_of(pub, viewer=pub)
    assert view["count"] == 1
    card = view["cards"][0]
    assert card["author"] == "member"
    assert card["source"]["authority_tier"] == shelves.MEMBER_TIER
    assert "Matt Harris" in card["source"]["label"], "the words have a name on them"
    assert card["generated"] is False


def test_nobody_can_put_words_on_another_members_shelf():
    from concordance import shelves, signing
    priv_a, pub_a = _key()
    _priv_b, pub_b = _key()
    sg = shelves.signable_drop(pub_b, "note", "not mine",
                               "Words attributed to someone who never wrote them.", "shelf")
    forged = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv_a)  # A signs B's
    r = shelves.drop(sg["fields"], forged)
    assert r["ok"] is False and "does not verify" in r["error"]
    assert shelves.shelf_of(pub_b, viewer=pub_b)["count"] == 0
    # and an unsigned drop is refused with the way in
    assert shelves.drop(sg["fields"], "")["ok"] is False
    # and a private key is never an acceptable substitute for a signature
    bad = shelves.drop(dict(sg["fields"], private_key=priv_a), "x" * 40)
    assert bad["ok"] is False and "never a private key" in bad["error"]


def test_the_gate_is_on_amplification_not_speech():
    from concordance import shelves
    shelf_r, pub, key = _drop(ring="shelf")
    commons_r, pub2, _ = _drop(ring="commons", body="A drop the member wants the whole "
                                                    "fellowship to see, in their own words.")
    # the shelf drop is LIVE immediately — no steward, no wait
    assert shelf_r["stage"] == "private" and shelves.shelf_of(pub)["count"] == 1
    # the commons drop waits, and it waits for a HUMAN
    assert commons_r["stage"] == "public_review"
    assert shelves.commons()["count"] == 0, "nothing reaches the commons uncurated"
    q = shelves.review_queue()
    assert q["count"] == 1 and q["items"][0]["card_id"] == commons_r["card_id"]
    # meanwhile the author still sees their own drop, and a stranger sees it is held
    assert shelves.shelf_of(pub2, viewer=pub2)["count"] == 1
    assert shelves.shelf_of(pub2)["awaiting_review"] == 1


def test_promotion_never_upgrades_the_authority():
    from concordance import shelves
    r, pub, _ = _drop(ring="commons")
    act = shelves.curate(r["card_id"], "promoted", "matt", "sound, and useful to a beginner",
                           token=STEWARD_TOKEN)
    assert act["ok"] and act["steward"] == "matt" and act["reason"]
    c = shelves.commons()
    assert c["count"] == 1 and c["authority"] == shelves.MEMBER_TIER
    card = c["cards"][0]
    assert card["source"]["authority_tier"] == shelves.MEMBER_TIER, \
        "the library amplified it; the library did not verify it"
    assert card["extra"]["promoted_by"] == "matt" and card["extra"]["promoted_reason"]
    assert card["lifecycle_stage"] == "public"


def test_no_anonymous_and_no_reasonless_judgement():
    from concordance import shelves
    r, _pub, _ = _drop(ring="commons")
    assert shelves.curate(r["card_id"], "promoted", "", "because", token=STEWARD_TOKEN)["ok"] is False
    assert shelves.curate(r["card_id"], "promoted", "matt", "", token=STEWARD_TOKEN)["ok"] is False
    assert shelves.curate(r["card_id"], "banished", "matt", "why", token=STEWARD_TOKEN)["ok"] is False
    assert shelves.curate("card_nope", "promoted", "matt", "why", token=STEWARD_TOKEN)["ok"] is False


def test_private_stays_private_and_the_public_boundary_agrees():
    from concordance import corpus, shelves
    r, pub, _ = _drop(ring="private", body="Something written only for myself, kept and not shown.")
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 1, "the member sees their own"
    assert shelves.shelf_of(pub)["count"] == 0, "a stranger never sees a private drop"
    card = shelves.shelf_of(pub, viewer=pub)["cards"][0]
    assert corpus.is_public(card) is False, \
        "the ONE public boundary must withhold it too — not just this reader"


def test_a_refusal_withholds_amplification_and_keeps_the_shelf():
    from concordance import shelves
    r, pub, _ = _drop(ring="commons")
    act = shelves.curate(r["card_id"], "refused", "matt", "not checkable, and it reads as advice",
                           token=STEWARD_TOKEN)
    assert act["ok"]
    assert shelves.commons()["count"] == 0
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 1, \
        "refusing to amplify never removes a member's own words from their own shelf"
    h = shelves.history(r["card_id"])
    assert h["count"] == 1 and h["acts"][0]["reason"]


def test_append_only_withdrawal_keeps_the_record():
    from concordance import shelves
    r, pub, _ = _drop()
    shelves.curate(r["card_id"], "withdrawn", "matt", "the member asked for it to come down",
                   token=STEWARD_TOKEN)
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 0, "gone from the view"
    assert shelves.history(r["card_id"])["count"] == 1, "and still in the record, with its reason"


def test_a_typed_name_is_not_authority():
    """THE HOLE, pinned. C1a took the steward's name on faith and C1b shipped that live for a few
    minutes: `steward` is a string anyone can type, so any passer-by could have promoted their own
    drop into the commons or pulled someone else's card down. Promoting and refusing decide what
    the whole library amplifies — they need the steward token, and they FAIL CLOSED without it."""
    from concordance import shelves
    r, pub, _ = _drop(ring="commons")
    for action in ("promoted", "refused"):
        bare = shelves.curate(r["card_id"], action, "matt", "looks fine to me")
        assert bare["ok"] is False and "not authorized" in bare["error"], (action, bare)
        wrong = shelves.curate(r["card_id"], action, "matt", "looks fine to me", token="guess")
        assert wrong["ok"] is False, (action, wrong)
    assert shelves.commons()["count"] == 0, "nothing was amplified by an unauthorized act"
    assert shelves.review_queue()["count"] == 1, "and it is still waiting for a real steward"
    ok = shelves.curate(r["card_id"], "promoted", "matt", "sound", token=STEWARD_TOKEN)
    assert ok["ok"] and ok["by"] == "steward"


def test_no_token_configured_means_no_promotion_at_all():
    """Fail closed, not open. An unconfigured deployment must not become an open commons."""
    from concordance import shelves
    r, _pub, _ = _drop(ring="commons")
    os.environ.pop("CONCORDANCE_KEEP_TOKEN", None)
    assert shelves.curate(r["card_id"], "promoted", "matt", "why", token="")["ok"] is False
    assert shelves.curate(r["card_id"], "promoted", "matt", "why", token="anything")["ok"] is False


def test_a_member_withdraws_their_own_card_with_their_own_key():
    """A member never needs permission to take their own words down — Matt's whole point about
    ownership. The proof is the same key that signed the drop, never a name and never the token."""
    from concordance import shelves, signing
    r, pub, key = _drop()
    priv = key[0]
    sg = shelves.signable_curate(r["card_id"], pub)
    assert sg.get("ok"), sg
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    act = shelves.curate(r["card_id"], "withdrawn", "Matt Harris", "changed my mind",
                         fields=sg["fields"], signature=sig)
    assert act["ok"] and act["by"] == "member", act
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 0
    assert shelves.history(r["card_id"])["count"] == 1, "and the act is in the record, with its why"


def test_one_member_cannot_pull_down_anothers_card():
    """The mirror of "nobody can put words on your shelf": nobody can take them off it either."""
    from concordance import shelves, signing
    r_a, pub_a, key_a = _drop()
    priv_b, pub_b = _key()
    # B asks to withdraw A's card, and signs correctly — for B.
    sg = shelves.signable_curate(r_a["card_id"], pub_b)
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv_b)
    bad = shelves.curate(r_a["card_id"], "withdrawn", "someone else", "I don't like it",
                         fields=sg["fields"], signature=sig)
    assert bad["ok"] is False and "not authorized" in bad["error"], bad
    # and B cannot simply name A either — the signature must verify against the named key
    sg2 = shelves.signable_curate(r_a["card_id"], pub_a)
    sig2 = signing.sign_bytes(base64.urlsafe_b64decode(sg2["signable"]), priv_b)
    assert shelves.curate(r_a["card_id"], "withdrawn", "someone else", "still not mine",
                          fields=sg2["fields"], signature=sig2)["ok"] is False
    assert shelves.shelf_of(pub_a, viewer=pub_a)["count"] == 1, "A's card is untouched"
    # a member's signature does NOT buy a promotion — that is a different authority
    r_c, pub_c, key_c = _drop(ring="commons")
    sg3 = shelves.signable_curate(r_c["card_id"], pub_c)
    sig3 = signing.sign_bytes(base64.urlsafe_b64decode(sg3["signable"]), key_c[0])
    assert shelves.curate(r_c["card_id"], "promoted", "me", "promote my own words",
                          fields=sg3["fields"], signature=sig3)["ok"] is False
    assert shelves.signable_curate(r_c["card_id"], pub_c, "promoted")["ok"] is False


def test_a_stale_withdrawal_signature_is_refused():
    from concordance import shelves, signing
    r, pub, key = _drop()
    sg = shelves.signable_curate(r["card_id"], pub)
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), key[0])
    stale = dict(sg["fields"], at=sg["fields"]["at"] - (shelves.SIGNATURE_TTL_S + 60))
    assert shelves.curate(r["card_id"], "withdrawn", "me", "too late",
                          fields=stale, signature=sig)["ok"] is False
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 1


def test_stale_signatures_and_bad_shapes_are_refused():
    from concordance import shelves, signing
    priv, pub = _key()
    sg = shelves.signable_drop(pub, "note", "s", "A body long enough to count as a real drop.", "shelf")
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    stale = dict(sg["fields"], at=sg["fields"]["at"] - (shelves.SIGNATURE_TTL_S + 60))
    assert shelves.drop(stale, sig)["ok"] is False, "stale bytes are refused"
    assert shelves.signable_drop(pub, "nonsense", "s", "body", "shelf")["ok"] is False
    assert shelves.signable_drop(pub, "note", "s", "", "shelf")["ok"] is False
    assert shelves.signable_drop(pub, "note", "s", "body", "everywhere")["ok"] is False
    assert shelves.signable_drop("", "note", "s", "body", "shelf")["ok"] is False


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
