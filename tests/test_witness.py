"""Witness — the Cloud of Witnesses' actual words, voiced only where public domain.

The strict-PD gate is structural: a copyrighted passage is NEVER voiced, even if injected. Voiced passages
are verbatim, attributed (witness + work + ref + source), scoped by witness, and honestly empty where the
cloud does not reach. Pure — the corpus is injected here; the fixtures are NEUTRAL placeholders, never any
real witness's actual words.
"""
from concordance import witness, mentors

# Neutral placeholders — deliberately not any real witness's words. Two public-domain, one copyrighted.
FIXTURE = [
    {"text": "a lamp trimmed and burning is tended before the dark comes, not after it has fallen",
     "witness": "TEST-WITNESS", "work": "TEST-WORK", "ref": "ch.1", "id": "w1",
     "source": "test://pd", "public_domain": True},
    {"text": "the plainest fare, taken in gratitude, feeds a body better than a feast eaten in strife",
     "witness": "TEST-WITNESS", "work": "TEST-WORK", "ref": "ch.2", "id": "w2",
     "source": "test://pd", "public_domain": True},
    {"text": "this passage names a living author and is under copyright — it must never be voiced here",
     "witness": "TEST-LIVING", "work": "X", "ref": "1", "id": "c1",
     "source": "test://©", "public_domain": False},
]


def test_only_public_domain_text_is_ever_voiced():
    # The copyrighted passage is relevant by words, but the gate holds — it is never returned.
    r = witness.see("a living author under copyright", corpus=FIXTURE)
    assert all(p["witness"] != "TEST-LIVING" for p in r["seeing"])
    assert witness.witnesses(corpus=FIXTURE) == ["TEST-WITNESS"]      # the non-PD witness is not voiced


def test_voice_leads_with_verbatim_attributed_words():
    r = witness.voice("how do I tend a lamp in the dark", corpus=FIXTURE)
    assert r["frame"] == FIXTURE[0]["text"]           # the witness's ACTUAL words — verbatim
    assert r["witness"] == "TEST-WITNESS" and r["work"] == "TEST-WORK" and r["ref"] == "ch.1"
    assert r["source"] == "test://pd"                 # provenance carried
    assert r["verbatim"] is True and r["generated"] is False
    assert r["proposes"] is True and r["confirms"] is False


def test_see_scopes_to_one_witness():
    assert witness.see("lamp", corpus=FIXTURE, witness="TEST-WITNESS")["seeing"]
    assert witness.see("lamp", corpus=FIXTURE, witness="NOBODY")["seeing"] == []


def test_honest_where_the_cloud_does_not_reach():
    r = witness.see("quantum chromodynamics", corpus=FIXTURE)
    assert r["seeing"] == [] and "still being gathered" in r["note"]


def test_empty_cloud_is_honest_not_fabricated():
    r = witness.voice("anything at all", corpus=[])
    assert r["frame"] is None and r["gathered"] == 0 and r["generated"] is False
    assert "stands on its own" in r["note"]


def test_mentors_voice_bridges_to_the_witness_layer(tmp_path, monkeypatch):
    # mentors.voice is the verbatim voice beside for_text's characterized gift. Point the corpus at an
    # empty path so the bridge is honestly empty here regardless of any locally-gathered data, and confirm
    # the gift still stands in for_text.
    monkeypatch.setenv("CONCORDANCE_WITNESSES", str(tmp_path / "none.jsonl"))
    r = mentors.voice("health and temperance", name="Ellen G. White")
    assert r["proposes"] is True and r["confirms"] is False and r["seeing"] == []
    assert mentors.for_text("health and temperance")["mentors"]      # the gift is still proposed
