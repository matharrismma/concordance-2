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


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


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
    act = shelves.curate(r["card_id"], "promoted", "matt", "sound, and useful to a beginner")
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
    assert shelves.curate(r["card_id"], "promoted", "", "because")["ok"] is False
    assert shelves.curate(r["card_id"], "promoted", "matt", "")["ok"] is False
    assert shelves.curate(r["card_id"], "banished", "matt", "why")["ok"] is False
    assert shelves.curate("card_nope", "promoted", "matt", "why")["ok"] is False


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
    act = shelves.curate(r["card_id"], "refused", "matt", "not checkable, and it reads as advice")
    assert act["ok"]
    assert shelves.commons()["count"] == 0
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 1, \
        "refusing to amplify never removes a member's own words from their own shelf"
    h = shelves.history(r["card_id"])
    assert h["count"] == 1 and h["acts"][0]["reason"]


def test_append_only_withdrawal_keeps_the_record():
    from concordance import shelves
    r, pub, _ = _drop()
    shelves.curate(r["card_id"], "withdrawn", "matt", "the member asked for it to come down")
    assert shelves.shelf_of(pub, viewer=pub)["count"] == 0, "gone from the view"
    assert shelves.history(r["card_id"])["count"] == 1, "and still in the record, with its reason"


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
