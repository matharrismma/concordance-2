"""The Cloud of Witnesses — our mentors, one or more per subject (Heb 12:1-2).

Each carries a GIFT (the true fragment) and a DISCERN note (how to weigh it, tested against the Source).
A mentor proposes a way of seeing; the gate and the Word dispose. Pure — a curated, editable seed.
"""
from concordance import mentors


def test_every_witness_has_a_gift_and_a_discernment():
    for m in mentors.MENTORS:
        assert m["name"] and m["subjects"] and isinstance(m["subjects"], list)
        assert m["gift"] and m["discern"]                  # a gift, and how to weigh it
        assert isinstance(m["public_domain"], bool)


def test_ellen_white_is_a_witness_for_the_body_and_the_walk():
    m = mentors.find("Ellen G. White")
    assert m is not None and m["public_domain"] is True    # her works are PD — her text may be gathered
    assert "health" in m["subjects"] and "education" in m["subjects"]
    assert "Bible" in m["discern"]                         # weighed on her own terms, under Scripture


def test_by_subject_gathers_the_right_witnesses():
    health = {m["name"] for m in mentors.by_subject("health")}
    assert "Ellen G. White" in health
    systems = {m["name"] for m in mentors.by_subject("systems")}
    assert {"Jacques Ellul", "Ivan Illich"} <= systems


def test_for_text_proposes_the_witnesses_whose_craft_bears_on_it():
    r = mentors.for_text("how should we teach a child at home")
    names = {m["name"] for m in r["mentors"]}
    assert ("Charlotte Mason" in names or "Ellen G. White" in names)
    assert r["proposes"] is True and r["confirms"] is False  # a witness proposes; the gate disposes


def test_the_gated_witnesses_carry_where_their_star_stops():
    jung = mentors.find("Carl Jung")
    assert jung and jung["public_domain"] is False          # copyright: characterized, not ingested
    assert "not Christ" in jung["discern"] or "Gnostic" in jung["discern"]  # the honest stopping point


def test_the_ancients_who_saw_from_afar_are_public_domain():
    for name in ("Heraclitus", "Plato", "Augustine", "Blaise Pascal"):
        m = mentors.find(name)
        assert m and m["public_domain"] is True             # their text is gatherable, like the lens


def test_subjects_lists_the_crafts_we_have_a_mentor_for():
    subs = mentors.subjects()
    assert "health" in subs and "systems" in subs and "the soul" in subs
