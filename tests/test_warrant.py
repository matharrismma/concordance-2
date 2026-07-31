"""THE WARRANT — steward authority that ends, rotates, and says who acted.

`docs/LESSONS_AND_HARDENING.md` H1, closing the gap C1b left. Closing L1 ("a typed name is not
authority") introduced a token, and that token was **one permanent secret, no expiry, no rotation,
no record of who held it** — the precise opposite of L11, taken from Matt's own The Way v0.2:
*"startup authority sunsets into the ordinary governance system."*

What is pinned:

  * a term that has ENDED refuses, and says *ended* rather than *wrong* — a steward whose warrant
    expired is not an impostor and must not be sent hunting for a typo;
  * ROTATION never leaves a gap: two live warrants at once, old and new both working;
  * the record names WHO acted and never the secret;
  * an unreadable expiry drops the entry rather than defaulting to `never`, because a guessed date
    is an authority that outlives its grant;
  * it fails closed.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import warrant  # noqa: E402

GOOD = "matt-secret-long-enough"
OTHER = "ruth-secret-long-enough"


@pytest.fixture(autouse=True)
def _clean_env():
    keep = {k: os.environ.get(k) for k in (warrant.ENV, warrant.LEGACY_ENV,
                                           "CONCORDANCE_DATA_DIR")}
    os.environ.pop(warrant.ENV, None)
    os.environ.pop(warrant.LEGACY_ENV, None)
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    for k, v in keep.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_a_warrant_names_who_acted_and_never_the_secret():
    os.environ[warrant.ENV] = f"matt:{GOOD}:2099-01-01"
    r = warrant.identify(GOOD)
    assert r["ok"] and r["name"] == "matt" and r["sunsets"] is True
    assert GOOD not in repr(r), "the secret came back in the answer"


def test_an_ended_term_is_refused_AND_told_apart_from_a_bad_token():
    os.environ[warrant.ENV] = f"matt:{GOOD}:2020-01-01"      # long past
    ended = warrant.identify(GOOD)
    assert ended["ok"] is False and ended.get("expired") is True
    assert "ended" in ended["error"] and "2020-01-01" in ended["error"]
    assert "not a bad token" in ended["error"], "an expired steward must not be called an impostor"

    wrong = warrant.identify("some-other-secret-entirely")
    assert wrong["ok"] is False and not wrong.get("expired"), \
        "a wrong token and an ended term must be different answers"


def test_rotation_leaves_no_gap():
    """Two live warrants at once — grant the next before the current ends."""
    os.environ[warrant.ENV] = f"matt:{GOOD}:2099-01-01, ruth:{OTHER}:2099-06-30"
    assert warrant.identify(GOOD)["name"] == "matt"
    assert warrant.identify(OTHER)["name"] == "ruth"
    r = warrant.roster()
    assert set(r["active"]) == {"matt", "ruth"} and r["all_sunset"] is True


def test_the_roster_carries_no_secret():
    os.environ[warrant.ENV] = f"matt:{GOOD}:2099-01-01, ruth:{OTHER}:2020-01-01"
    r = warrant.roster()
    assert GOOD not in repr(r) and OTHER not in repr(r), "the roster leaked a secret"
    assert r["active"] == ["matt"] and r["expired"] == ["ruth"]


def test_an_unreadable_date_drops_the_entry_rather_than_lasting_forever():
    """The failure mode of a guessed date is an authority that outlives its grant."""
    os.environ[warrant.ENV] = f"matt:{GOOD}:not-a-date"
    assert warrant.warrants() == []
    assert warrant.identify(GOOD)["ok"] is False


def test_it_fails_closed_and_refuses_a_feeble_secret():
    assert warrant.identify("")["ok"] is False
    assert warrant.identify("anything")["ok"] is False, "no config must mean no steward"
    os.environ[warrant.ENV] = "matt:short:2099-01-01"
    assert warrant.warrants() == [], "a secret short enough to guess is not a secret"


def test_the_legacy_token_still_works_and_says_it_does_not_sunset():
    """The live box must not lose its steward mid-change — but the weakness lands in the record
    instead of hiding in the environment."""
    os.environ[warrant.LEGACY_ENV] = "legacy-secret-long-enough"
    r = warrant.identify("legacy-secret-long-enough")
    assert r["ok"] and r["name"] == warrant.LEGACY_NAME
    assert r["sunsets"] is False and "no end date" in r["note"]
    assert warrant.roster()["legacy_token_in_use"] is True


# ───────────────────────────────────── through the shelf

def _key():
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001
        pytest.skip("signing unavailable in this build")


def _commons_drop():
    from concordance import shelves, signing
    priv, pub = _key()
    sg = shelves.signable_drop(pub, "note", "For the commons",
                               "A drop offered to the whole fellowship, in the member's words.",
                               "commons")
    sig = signing.sign_bytes(base64.urlsafe_b64decode(sg["signable"]), priv)
    return shelves.drop(sg["fields"], sig, display_name="A member")


def test_the_curation_record_names_the_steward_not_the_secret():
    from concordance import shelves
    os.environ[warrant.ENV] = f"matt:{GOOD}:2099-01-01"
    r = _commons_drop()
    act = shelves.curate(r["card_id"], "promoted", "matt", "sound and useful", token=GOOD)
    assert act["ok"] and act["by"] == "steward"
    assert act["by_identity"] == "matt", "the record cannot say WHO acted"
    assert act["authority_sunsets"] is True

    raw = (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "shelves" / "curation.jsonl") \
        .read_text(encoding="utf-8")
    assert '"by_identity": "matt"' in raw
    assert GOOD not in raw, "the steward's secret was written into the record"


def test_an_expired_steward_cannot_promote_and_is_told_why():
    from concordance import shelves
    os.environ[warrant.ENV] = f"matt:{GOOD}:2020-01-01"
    r = _commons_drop()
    act = shelves.curate(r["card_id"], "promoted", "matt", "still trying", token=GOOD)
    assert act["ok"] is False and act.get("expired") is True
    assert "ended" in act["error"]
    assert shelves.commons()["count"] == 0, "an ended warrant amplified something"


def test_nothing_about_the_store_leaks_before_authority_is_shown():
    """Found on the LIVE box: no token, a wrong token, and a valid token all answered "no such
    drop", because existence was checked before authority. Two faults in one ordering — every
    refusal was misleading, and comparing errors told an unauthenticated caller WHICH card ids
    exist."""
    from concordance import shelves
    os.environ[warrant.ENV] = f"matt:{GOOD}:2099-01-01"
    real = _commons_drop()["card_id"]

    for cid in (real, "card_that_does_not_exist"):
        bare = shelves.curate(cid, "promoted", "m", "why")
        assert "not authorized" in bare["error"], f"leaked store state for {cid}: {bare}"
    # the two are indistinguishable to an unauthorized caller
    a = shelves.curate(real, "promoted", "m", "why")["error"]
    b = shelves.curate("card_that_does_not_exist", "promoted", "m", "why")["error"]
    assert a == b, "an unauthorized caller can tell a real card from a fake one"
    # and WITH authority, the real answer comes back
    assert shelves.curate("card_nope", "promoted", "m", "why", token=GOOD)["error"] == "no such drop"
    assert shelves.curate(real, "promoted", "m", "why", token=GOOD)["ok"] is True


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
