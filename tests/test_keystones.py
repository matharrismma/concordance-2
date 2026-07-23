"""The two keystones of the floor — the Four Gates (HOW) and the Floor of Discovery (WHY).

Matt: "Seeds of knowledge, identified, categorized and mapped to create a floor of reality, and
by seeing the design we will fear God. This is the first step to wisdom."

Guards: the keystones are Matt's own words (author matt, not generated), carry the load-bearing
content (the four gate names; one floor; the fear of the Lord), and their bridges graft them
reciprocally into the existing floor at load — the same overlay the reference→Scripture grafts use.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-keystone-"))

import seed_keystones as sk  # noqa: E402


def test_the_keystones_are_matts_own_seeds_not_generated():
    for s in sk.SEEDS:
        assert s["author"] == "matt" and s["generated"] is False
        assert s["source"]["authority_tier"] == "matt" and s["surface"] == "witness"


def test_four_gates_carries_the_fixed_order():
    fg = next(s for s in sk.SEEDS if s["id"] == "card_k_four_gates")
    for gate in ("RED", "FLOOR", "BROTHERS", "GOD"):
        assert gate in fg["body"]
    assert "never reordered" in fg["body"] and "self-confirm" in fg["body"]


def test_floor_of_discovery_is_one_floor_leading_to_the_fear_of_God():
    fd = next(s for s in sk.SEEDS if s["id"] == "card_k_floor_of_discovery")
    assert "one floor" in fd["body"]
    assert "fear of the LORD is the beginning of wisdom" in fd["body"]
    assert "Proverbs 9:10" in fd["body"] and "idol" in fd["body"]  # never the idol


def test_bridges_graft_the_keystones_into_the_floor_reciprocally():
    """Applied at load through corpus._apply_bridges (droplet-only target ids are skipped locally;
    here we prove the mechanism with a present target)."""
    from concordance import corpus
    d = Path(tempfile.mkdtemp(prefix="nh-keystone-apply-"))
    (d / "cards.jsonl").write_text(
        json.dumps({"id": "card_n_653e4ac3ff00", "kind": "note", "title": "A parable — Fear of god",
                    "shelf": "codex"}) + "\n", encoding="utf-8")
    (d / "keystone_seeds.jsonl").write_text(
        "\n".join(json.dumps(s) for s in sk.SEEDS) + "\n", encoding="utf-8")
    (d / "keystone_bridges.jsonl").write_text(
        json.dumps({"a": "card_k_floor_of_discovery", "b": "card_n_653e4ac3ff00",
                    "relationship": "leads_to", "evidence": "the fear of God (Proverbs 9:10)"})
        + "\n", encoding="utf-8")
    saved = os.environ.get("CONCORDANCE_CARDS_JSONL")
    os.environ["CONCORDANCE_CARDS_JSONL"] = str(d / "cards.jsonl")
    try:
        cards = corpus.load_cards()
    finally:
        if saved is None:
            os.environ.pop("CONCORDANCE_CARDS_JSONL", None)
        else:
            os.environ["CONCORDANCE_CARDS_JSONL"] = saved
    # the floor seed links to the parable...
    assert any(x["to_card_id"] == "card_n_653e4ac3ff00"
               for x in cards["card_k_floor_of_discovery"]["connections"])
    # ...and the parable links back to the floor seed (reciprocal)
    assert any(x["to_card_id"] == "card_k_floor_of_discovery"
               for x in cards["card_n_653e4ac3ff00"]["connections"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} keystone tests passed — the floor's HOW and WHY are seeded and grafted in.")
