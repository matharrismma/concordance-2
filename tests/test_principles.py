"""Principles — identify (maxim shape, verbatim), tag (Strategy Concordance patterns, lexical),
prove (a count: figures × arenas × cases), apply (a situation → ranked patterns with the figures'
own words). Gathered, never generated; found=False when nothing matches."""
import json
from pathlib import Path

from concordance import principles as P

NAPOLEON = (
    "MAXIM XXIX.\n\nWhen you have resolved to fight a battle, collect your whole force. Dispense with "
    "nothing. A single battalion sometimes decides the day.\n\nNOTE.\n\nThis maxim was followed by the Emperor."
)
FORD = ("The man who has the largest capacity for work and thought is the man who is bound to succeed. "
        "Nothing is more dangerous than a cheap product that does not serve. It is a mistake to suppose that "
        "the customer will not notice. The weather was fine on Tuesday and we went to the lake with the "
        "children for a picnic by the water.")


def test_identify_keeps_maxim_shaped_sentences_verbatim_and_drops_prose():
    found = P.identify(FORD)
    quotes = [f["quote"] for f in found]
    assert any(q.startswith("Nothing is more dangerous") for q in quotes)
    assert any(q.startswith("It is a mistake") for q in quotes)
    assert not any("picnic" in q for q in quotes)            # no cue, not a principle
    for f in found:
        assert f["quote"] in FORD                              # verbatim, never paraphrased
        assert f["cues"]                                        # the selecting cue rides along


def test_labelled_maxims_are_accepted_by_construction():
    blk = NAPOLEON.split("MAXIM XXIX.", 1)[1].split("\nNOTE", 1)[0].strip()
    found = P.identify("", labelled_blocks=[blk])
    assert found and found[0]["labelled"] and found[0]["quote"].startswith("When you have resolved")
    assert "concentrate_force" in found[0]["patterns"]       # "whole force" / "collect" names the move? see tag


def test_tag_is_lexical_and_names_the_stem():
    t = P.tag("Concentrate your forces at the decisive point and lose no time.")
    assert "concentrate_force" in t and "tempo" in t
    assert "decisive point" in t["concentrate_force"] and "lose no time" in t["tempo"]
    assert P.tag("We had tea and a nap.") == {}


def _fixture(tmp_path: Path):
    pats = [{"id": "card_pattern_tempo", "kind": "strategy_pattern", "title": "Tempo", "extra": {"gist": "speed"}},
            {"id": "card_case_1", "kind": "strategy_case", "extra": {"pattern": "tempo", "arena": "war",
                                                                    "who": "Caesar", "when": "49 BC", "move": "crossed"}},
            {"id": "card_case_2", "kind": "strategy_case", "extra": {"pattern": "tempo", "arena": "business",
                                                                    "who": "SpaceX", "when": "2010s", "move": "iterated"}}]
    prs = [{"id": "p1", "kind": "principle", "body": "Lose no time.", "source": {"url": "u1"},
            "extra": {"figure": "Napoleon Bonaparte", "arena": "war", "patterns": ["tempo"]}},
           {"id": "p2", "kind": "principle", "body": "Speed is the essence of war.", "source": {"url": "u2"},
            "extra": {"figure": "Sun Tzu", "arena": "war", "patterns": ["tempo"]}},
           {"id": "p3", "kind": "principle", "body": "Keep the customer.", "source": {"url": "u3"},
            "extra": {"figure": "Henry Ford", "arena": "business", "patterns": ["distribution_over_product"]}}]
    (tmp_path / "strategy_cards.jsonl").write_text("\n".join(json.dumps(c) for c in pats), encoding="utf-8")
    (tmp_path / "principle_cards.jsonl").write_text("\n".join(json.dumps(c) for c in prs), encoding="utf-8")
    return tmp_path


def test_proof_is_a_count_of_distinct_figures_arenas_and_cases(tmp_path):
    d = _fixture(tmp_path)
    prs = P.load_principles(d)
    _pats, cases = P.load_patterns(d)
    pr = P.proof("tempo", prs, cases)
    assert pr["figures"] == 2 and set(pr["arenas"]) == {"war", "business"} and pr["cases"] == 2
    assert pr["proven"] is True
    one = P.proof("distribution_over_product", prs, cases)
    assert one["figures"] == 1 and one["proven"] is False      # one witness, one arena: not yet proven


def test_apply_resolves_a_situation_and_hands_back_the_figures_words(tmp_path):
    d = _fixture(tmp_path)
    r = P.apply("the incumbent is slow and we must move at once before they react", data_dir=d)
    assert r["found"] and r["patterns"][0]["pattern"] == "tempo"
    top = r["patterns"][0]
    assert top["proof"]["proven"] and top["proof"]["figures"] == 2
    figs = [p["figure"] for p in top["principles"]]
    assert figs[:2] == ["Napoleon Bonaparte", "Sun Tzu"]       # one per figure first — breadth of witness
    assert all(p["quote"] and p["url"] for p in top["principles"])
    assert {c["who"] for c in top["cases"]} == {"Caesar", "SpaceX"}


def test_apply_never_guesses(tmp_path):
    d = _fixture(tmp_path)
    r = P.apply("tea and a nap", data_dir=d)
    assert r["found"] is False and r["patterns"] == []


def test_precision_pins_from_the_first_mint():
    # "the United States" is not "unite your forces": a proper noun must not name the move
    assert "concentrate_force" not in P.tag("The United States had passed the stage of venturing to hope.")
    # a memoir line with "always" is narrative, not a rule — dropped
    assert P.identify("I could always sleep, never knowing horrid night, the child of hell, in those days.") == []
    # but a general rule with a first-person RULE-FRAME survives
    kept = P.identify("The first rule I learned in business is that the customer must be served before the owner.")
    assert kept and kept[0]["quote"].startswith("The first rule")


def test_every_pattern_in_the_lexicon_exists_in_the_strategy_concordance():
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_strategy", Path(__file__).resolve().parent.parent / "tools" / "seed_strategy.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    ids = {p["id"] for p in mod.PATTERNS}
    assert set(P.PATTERN_LEXICON) == ids, set(P.PATTERN_LEXICON) ^ ids
