"""The acting half of the assay must decline rather than guess.

`tools/assay_cards.py` judges and changes nothing; `tools/repair_cards.py` acts. The gap between
them is where this library's two worst mistakes lived, and both are pinned here:

  * A Roman numeral read as a placeholder. `_xxx` in a citation slug is THIRTY. Reading it as
    "unfinished" put 246 cards on a removal list and cost a public retraction. So the numeral
    parser is strict and round-trips: anything it cannot render back to itself is refused.
  * A rule applied to a whole library on one measurement. The truncation rule flagged 157,130
    Scripture verses because a verse is punctuated to carry into the next one.

And one found by the dry-run of this very tool, before a card was written: a connection card is
titled `A → B` with a slug on both sides, and the first version rewrote only the first — leaving
`Meditations 4.33 → Meditations §aur_08_v`, which is worse than not touching it, because it reads
as finished.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import repair_cards as rc  # noqa: E402


def test_xxx_is_thirty():
    """The retraction of 2026-07-30, made into a test."""
    assert rc.roman_to_int("xxx") == 30
    assert rc.roman_to_int("xxiii") == 23
    assert rc.roman_to_int("mcmxciv") == 1994


def test_a_malformed_numeral_is_refused_not_guessed():
    for bad in ("iiii", "xxxx", "viv", "ic", "", "abc", "x1"):
        assert rc.roman_to_int(bad) is None, f"{bad!r} was given a value"


def test_every_slug_in_a_title_or_none_of_them():
    both = "Aurelius, Meditations §aur_04_xxxiii → Aurelius, Meditations §aur_08_v: Tha"
    out, why = rc.render_title(both)
    assert why is None
    assert "§" not in out, f"a slug survived: {out}"
    assert out.startswith("Aurelius, Meditations 4.33 → Aurelius, Meditations 8.5")


def test_a_title_with_one_unreadable_slug_is_declined_whole():
    out, why = rc.render_title("A §aur_01_iiii → B §aur_02_v")
    assert out is None and "unreadable" in why, "a half-rendered title reads as finished"


def test_a_slug_it_cannot_read_is_named_not_invented():
    out, why = rc.render_title("Sermon §som_10_giving_in_secret: on giving")
    assert out is None and why == "no slug this rule can read"


def test_the_plain_cases():
    assert rc.render_title("Aurelius, Meditations §aur_07_xxiii: Out of Plato.")[0] == \
        "Aurelius, Meditations 7.23: Out of Plato."
    assert rc.render_title("La Rochefoucauld §laroch_264: Pity.")[0] == \
        "La Rochefoucauld 264: Pity."


def test_a_title_with_no_slug_is_left_alone():
    for t in ("Revelation 5", "Easton: Slave", ""):
        assert rc.render_title(t)[0] is None


def test_a_retraction_needs_a_reason_and_a_name():
    """A removal without either is a deletion wearing a record's clothes."""
    from concordance import assay
    assert not assay.retraction("card_x", "", "Matt")["ok"]
    assert not assay.retraction("card_x", "it is empty", "")["ok"]
    assert not assay.retraction("", "it is empty", "Matt")["ok"]
    ok = assay.retraction("card_x", "the body only repeats the title", "Matt")
    assert ok["ok"] and ok["card"]["id"] == "card_retract_card_x"


def test_only_one_repair_kind_is_offered_at_a_time():
    """The tool takes ONE --kind. A 'fix everything' switch would apply several different
    arguments about what is wrong on one keystroke."""
    src = (ROOT / "tools" / "repair_cards.py").read_text(encoding="utf-8")
    assert 'choices=sorted(KINDS)' in src, "the kind must be a closed choice"
    assert "--all" not in src and "fix_all" not in src


if __name__ == "__main__":
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in fns:
        fn()
        print(f"  ok  {name}")
    print(f"\n{len(fns)} repair tests passed — the acting half declines rather than guesses.")
