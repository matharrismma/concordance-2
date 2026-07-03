"""Seeds pass — the guardrails, as tests. The discipline is load-bearing, so it is enforced here."""
from __future__ import annotations

from concordance import seeds


def test_every_seed_has_the_required_shape():
    for r in seeds._load():
        for field in ("id", "fragment", "source", "tradition", "rating", "concordance",
                      "refuse", "turn_to_christ"):
            assert r.get(field), f"seed {r.get('id')!r} missing {field}"
        assert isinstance(r["concordance"], list) and r["concordance"], "seed needs >=1 concordance ref"
        for c in r["concordance"]:
            assert c.get("ref"), "each concordance entry needs a Scripture ref"


def test_rating_is_always_concordant_never_holds():
    # CONCORDANT / signpost, NEVER HOLDS — religious material is never sealed as math.
    for r in seeds._load():
        assert r.get("rating") == "CONCORDANT", f"{r.get('id')} must be CONCORDANT"
        assert r.get("rating") != "HOLDS"
    # And the get() path preserves it.
    one = seeds.get("epimenides-in-him-we-live")
    assert one is not None and one["rating"] == "CONCORDANT"


def test_grief_not_syncretism_every_seed_refuses_an_idol():
    # The idol/distortion must be named and refused — mining, not blending.
    for r in seeds._load():
        assert len(r.get("refuse", "").strip()) > 10, f"{r.get('id')} must name what it refuses"


def test_every_seed_points_to_christ():
    for r in seeds._load():
        turn = r.get("turn_to_christ", "").lower()
        assert ("christ" in turn or "logos" in turn or "son" in turn or "jesus" in turn), \
            f"{r.get('id')} must turn toward Christ"


def test_method_is_pauls_seven_steps():
    m = seeds.method()
    assert len(m["steps"]) == 7, "the Areopagus sequence is seven steps"
    for s in m["steps"]:
        assert s.get("step") and s.get("ref") and s.get("do")
    # Acts 17 is the charter.
    assert any("17:23" in s["ref"] for s in m["steps"]), "the unknown-god naming must be present"


def test_note_holds_the_line():
    n = seeds.NOTE.lower()
    assert "not a proof" in n or "never holds" in n
    assert "syncretism" in n
    assert "christ" in n


def test_lookup_paths():
    assert seeds.get("nope-not-a-seed") is None
    assert seeds.list_seeds()["total"] >= 3
    assert seeds.list_seeds(tradition="stoic")["total"] >= 1
    assert seeds.search("offspring")["total"] >= 1
