"""THE CLAIM GRAMMAR (Gen 3 · 3, 2026-10-04) — one deterministic parser for arithmetic claims. The four
regex extractors (sum, product, quotient, word arithmetic) became labels of one grammar; a mixed or
parenthesised expression is a verdict now, not a miss; the zero-false-positive discipline moved into the
tokenizer (adjacency, a binary minus needs its spaces, "/" and "x" only between numbers)."""
import os
import tempfile

os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-grammar-")

from concordance.audit import audit, extract  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402

CFG = EngineConfig()


def _v(text):
    return audit(text, CFG, seal=False)["verdict"]


def _x(text):
    return [(s["extractor"], s["spec"]["params"]["expr_a"], s["spec"]["params"]["expr_b"]) for s in extract(text)
            if s["extractor"] in ("sum", "product", "quotient", "arith_words", "expression")]


def test_mixed_and_parenthesised_expressions_are_verdicts_now():
    assert _v("2 + 3 * 4 = 14.") == "HOLDS" and _v("2 + 3 * 4 = 20.") == "BROKEN"      # precedence, not left-to-right
    assert _v("(2 + 3) * 4 = 20.") == "HOLDS" and _v("10 - 2 * 3 = 4.") == "HOLDS"
    assert _v("100 / 5 + 2 = 22.") == "HOLDS" and _v("2 * 3 + 4 = 10.") == "HOLDS"
    assert _v("-2 * 3 = -6.") == "HOLDS" and _v("3 - 5 = -2.") == "HOLDS"
    assert _v("2 plus 3 times 4 is 14.") == "HOLDS"                                     # words and symbols mix
    assert _x("2 + 3 * 4 = 14") == [("expression", "2 + 3 * 4", "14")]


def test_the_old_labels_survive_for_the_shapes_the_pins_know():
    assert _x("12.50 + 8.75 = 21.30") == [("sum", "12.50 + 8.75", "21.30")]
    assert _x("$620 + $2,090 = $2,710") == [("sum", "620 + 2090", "2710")]
    assert _x("2 * 2 * 3 = 12") == [("product", "2 * 2 * 3", "12")]
    assert _x("Total: 3 x $4.50 = $14.50") == [("product", "3 * 4.50", "14.50")]
    assert _x("72 / 2 = 36") == [("quotient", "72 / 2", "36")] and _x("144 ÷ 12 = 12") == [("quotient", "144 / 12", "12")]
    assert _x("10 divided by 2 is 5") == [("arith_words", "10 / 2", "5")]
    assert _x("64 mod 9 is 1") == [("arith_words", "64 % 9", "1")]
    assert _v("2 plus 2 equals 5") == "BROKEN" and _v("12 * 12 * 1000 = 144,000") == "HOLDS"


def test_the_discipline_moved_into_the_tokenizer():
    assert _x("2 plus a few more, is 4 enough?") == []                  # no second number adjacent to 'plus'
    assert _x("I called 3 times and 4 people answered") == []           # 'times' with no number after it
    assert _x("5 minus the discount, roughly 2 left") == []
    assert _x("pages 3-5 is 2 pages") == []                             # a hyphenated range is not a subtraction
    assert _x("40 hours at $18.50/hr = $800.00") == []                  # "/hr" is a rate, not a division
    assert _x("there are 5280 feet in a mile") == []                    # no operator: the unit-fact extractor's
    assert _x("2^10 = 1024") == [] and _x("10% of 50 = 5") == []         # power and percent own those
    assert _x("1 / 0 = 0") == []                                        # division by zero: a gap, never a verdict
    assert _x("1 + 1 = 2 and 2 * 3 = 6") == [("sum", "1 + 1", "2"), ("product", "2 * 3", "6")]
    r = audit("3 x 4 = 12. The 5 x 5 grid has 25 cells.", CFG, seal=False)
    # "5 x 5 grid" carries no claim verb, so one claim is found — and since 2026-10-08 (the failure report, C4) the
    # top-level verdict is PARTIAL, not HOLDS: the grid sentence holds numbers nobody checked, and the headline says so.
    assert r["verdict"] == "PARTIAL" and r["claims_found"] == 1 and r["held"] == 1
    assert any("25 cells" in x for x in r["coverage"]["unchecked_text"])
