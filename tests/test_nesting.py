"""The Nesting — the floor is one instrument, not a pile of parts.

Matt: "It needs a complete recalibration to optimize the system. It's currently a bunch of parts."

Guards: every reference seed hangs from a domain spine; every spine roots in the one floor (both
halves — the created order and the Word); crops of a family are siblings; and a verified seed is
born already nested, so new verifications never re-orphan the floor.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-nest-"))

import nest_the_floor as nf  # noqa: E402


def _cards():
    return [
        {"id": "card_ref_el_001", "shelf": "chemistry", "kind": "reference"},
        {"id": "card_ref_pc_speed_of_light", "shelf": "physics", "kind": "reference"},
        {"id": "card_ref_crop_tomato", "shelf": "agriculture", "kind": "reference"},
        {"id": "card_ref_crop_potato", "shelf": "agriculture", "kind": "reference"},
        {"id": nf.PERIODIC, "shelf": "science", "kind": "note", "title": "The periodic table"},
        {"id": nf.CHEMISTRY, "shelf": "science", "kind": "note", "title": "Chemistry"},
        {"id": nf.FLOOR, "shelf": "codex", "kind": "note", "title": "The Floor of Discovery"},
        {"id": "card_n_essay1", "shelf": "science", "kind": "note", "connections": []},
        {"id": "card_n_jonah", "shelf": "reference", "box": "archetypes", "connections": []},
        {"id": "card_n_parable", "shelf": "codex", "kind": "note", "connections": []},
    ] + [nf._spine_seed(s) for s in nf.SPINES]


def test_reference_seeds_hang_from_their_spine():
    edges = {(e["a"], e["b"]): e for e in nf.compute(_cards())}
    assert edges[("card_ref_el_001", nf.PERIODIC)]["relationship"] == "member_of"
    assert ("card_ref_pc_speed_of_light", "card_k_spine_constants") in edges
    assert ("card_ref_crop_tomato", "card_k_spine_crops") in edges


def test_both_halves_root_in_the_one_floor():
    edges = {(e["a"], e["b"]) for e in nf.compute(_cards())}
    # created order (general revelation) -> the floor
    assert (nf.CREATED_ORDER, nf.FLOOR) in edges
    # the Word (special revelation) -> the floor
    assert (nf.THE_WORD, nf.FLOOR) in edges
    # the chemistry spine chain climbs to the created order
    assert (nf.CHEMISTRY, nf.CREATED_ORDER) in edges
    # an archetype is a figure of the Word
    assert ("card_n_jonah", nf.ARCHETYPES) in edges
    # an orphan codex seed roots in the Word
    assert ("card_n_parable", nf.THE_WORD) in edges


def test_crops_of_a_family_are_siblings():
    edges = {(e["a"], e["b"]): e for e in nf.compute(_cards())}
    e = edges.get(("card_ref_crop_potato", "card_ref_crop_tomato")) \
        or edges.get(("card_ref_crop_tomato", "card_ref_crop_potato"))
    assert e and e["relationship"] == "same_family"      # both solanaceae


def test_nothing_is_left_off_the_floor():
    """The catch-all: any remaining orphan roots in the floor (created order or the Word)."""
    cards = _cards() + [{"id": "card_v_stray", "shelf": "labor", "surface": "secular",
                         "connections": []}]
    edges = {(e["a"], e["b"]) for e in nf.compute(cards)}
    assert ("card_v_stray", nf.CREATED_ORDER) in edges


def test_verified_seeds_are_born_nested():
    """The seam fix: a newly minted verified seed already hangs from the created order, so live
    verification never re-orphans the floor."""
    from concordance import science_cards
    seal = {"cite_url": "https://narrowhighway.com/s/x"}
    result = {"verdict": "HOLDS",
              "trail": [{"claim": "the labor rate holds", "detail": "40h × $18.50 = $740",
                         "status": "CONFIRMED"}]}
    card = science_cards.card_for(result, "labor", seal)
    assert card is not None
    assert any(l["to_card_id"] == "card_k_spine_created_order" for l in card["connections"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} nesting tests passed — one floor, one root; nothing left as a loose part.")
