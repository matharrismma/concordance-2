"""The media plane — graph.formats groups the keeping by artifact format.

Proves the shelf->format mapping is deterministic and single-source, the section counts are real
call-tree totals (not invented), a quarantined card is not counted, and every declared format is
present in the output. Synthetic corpus, so it needs none of the box's data.
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
        "london": _card("london", "geography", "geography.gb.l.london", "London"),
        "gdp": _card("gdp", "economics", "economics.us.gdp", "US GDP"),
        "john316": _card("john316", "greek_nt", "greek_nt.john.3.16", "John 3:16"),
        "moby": _card("moby", "gutenberg", "gutenberg.melville.moby-dick", "Moby-Dick"),
        "secret": _card("secret", "geography", "geography.zz.secret", "Secret",
                        lifecycle_stage="quarantine"),
    }
    return corpus.Corpus(cards)


def test_the_mapping_is_deterministic_and_defaults_to_text():
    assert graph.format_of_shelf("geography") == "map"
    assert graph.format_of_shelf("economics") == "data"
    assert graph.format_of_shelf("pronunciation") == "audio"
    assert graph.format_of_shelf("greek_nt") == "text"   # default
    assert graph.format_of_shelf("gutenberg") == "text"


def test_formats_groups_the_keeping_by_media():
    d = graph.formats(c=_corpus())
    assert d["scope"] == "formats"
    by = {f["format"]: f for f in d["formats"]}
    # geography -> map (2 public places; the quarantined one is not counted)
    assert by["map"]["count"] == 2
    assert [s["shelf"] for s in by["map"]["sections"]] == ["geography"]
    # economics -> data
    assert by["data"]["count"] == 1
    # greek_nt + gutenberg -> text
    assert by["text"]["count"] == 2
    # total is the real public count (secret withheld)
    assert d["total"] == 5


def test_every_declared_format_is_present_even_when_empty():
    d = graph.formats(c=_corpus())
    present = {f["format"] for f in d["formats"]}
    assert present == set(graph.FORMATS)   # text, data, map, audio, film, microfilm, link
    # a format we hold nothing in is honestly zero, not omitted
    by = {f["format"]: f for f in d["formats"]}
    assert by["microfilm"]["count"] == 0 and by["film"]["count"] == 0


if __name__ == "__main__":  # runnable without pytest
    for fn in (test_the_mapping_is_deterministic_and_defaults_to_text,
               test_formats_groups_the_keeping_by_media,
               test_every_declared_format_is_present_even_when_empty):
        fn()
        print("ok:", fn.__name__)
    print("all passed")
