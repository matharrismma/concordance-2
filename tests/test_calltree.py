"""The library, walked — graph.calltree descends the call-tree section -> ... -> card.

Proves the browse UI the call-tree never had: each level lists the drawers directly below
(sized by the cards under them), a leaf lists its cards, counts are honest, private cards never
appear, and the walk is deterministic and FOUND (every node is a real call node or a real card —
nothing generated). Runs with a tiny synthetic corpus, so it needs none of the box's data.
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from concordance import corpus, graph  # noqa: E402


def _card(cid, shelf, call, title, **extra):
    c = {"id": cid, "kind": "note", "shelf": shelf, "call": call, "title": title}
    c.update(extra)
    return c


def _corpus():
    cards = {
        "austin": _card("austin", "geography", "geography.us.a.austin", "Austin"),
        "dallas": _card("dallas", "geography", "geography.us.d.dallas", "Dallas"),
        "london": _card("london", "geography", "geography.gb.l.london", "London"),
        "john316": _card("john316", "greek_nt", "greek_nt.john.3.16", "John 3:16"),
        # a withheld card — quarantined — must never appear in the stacks
        "secret": _card("secret", "geography", "geography.us.s.secret", "Secret",
                        lifecycle_stage="quarantine"),
    }
    return corpus.Corpus(cards)


def test_root_lists_the_sections():
    c = _corpus()
    r = graph.calltree("", c=c)
    assert r["scope"] == "calltree" and r["shows"] == "folders"
    kids = {n["call"]: n for n in r["nodes"] if n["kind"] == "folder"}
    assert set(kids) == {"geography", "greek_nt"}, kids
    # geography holds the three PUBLIC places; the quarantined one is not counted
    assert kids["geography"]["count"] == 3
    assert kids["greek_nt"]["count"] == 1
    assert r["total_here"] == 4  # 4 public cards, secret withheld
    assert r["parent"] is None


def test_it_descends_a_drawer_at_a_time():
    c = _corpus()
    assert {n["call"] for n in graph.calltree("geography", c=c)["nodes"] if n["kind"] == "folder"} \
        == {"geography.us", "geography.gb"}
    assert {n["call"] for n in graph.calltree("geography.us", c=c)["nodes"] if n["kind"] == "folder"} \
        == {"geography.us.a", "geography.us.d"}
    # parent points back up the stack
    assert graph.calltree("geography.us", c=c)["parent"] == "geography"


def test_a_leaf_lists_its_cards():
    c = _corpus()
    r = graph.calltree("geography.us.a.austin", c=c)
    assert r["shows"] == "cards"
    cards = [n for n in r["nodes"] if n["kind"] == "card"]
    assert [n["id"] for n in cards] == ["austin"]
    assert r["total_here"] == 1


def test_deterministic_and_found_only():
    c = _corpus()
    a, b = graph.calltree("geography", c=c), graph.calltree("geography", c=c)
    assert a == b, "same prefix must give the same walk"
    # every node is a real call node or a real card id — nothing invented
    for n in a["nodes"]:
        assert n["id"].startswith("call:") or n["id"] in c.cards, n


if __name__ == "__main__":  # runnable without pytest
    for fn in (test_root_lists_the_sections, test_it_descends_a_drawer_at_a_time,
               test_a_leaf_lists_its_cards, test_deterministic_and_found_only):
        fn()
        print("ok:", fn.__name__)
    print("all passed")
