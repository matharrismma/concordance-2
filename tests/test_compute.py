"""The calculator must be exact, and must DECLINE what it cannot compute (never a wrong number)."""
from concordance import compute


def test_arithmetic_and_percentages():
    # output is CANONICAL — phrasing is normalized to one statement (× ÷ ^), not echoed back
    assert compute.answer("what is 8 times 7") == "8 × 7 = 56"
    assert compute.answer("what is 15 percent of 240") == "15% of 240 = 36"
    assert compute.answer("what is 12 divided by 4") == "12 ÷ 4 = 3"
    assert compute.answer("what is 2 to the power of 10").endswith("= 1024")
    assert compute.answer("what is the square root of 144").endswith("= 12")


def test_flexible_phrasing():
    # real people say it many ways — each must compute EXACTLY, or decline
    assert compute.answer("add 3 and 4") == "3 + 4 = 7"
    assert compute.answer("the product of 6 and 7") == "6 × 7 = 42"
    assert compute.answer("subtract 4 from 10") == "10 − 4 = 6"
    assert compute.answer("half of 60") == "half of 60 = 30"
    assert compute.answer("double 21") == "double 21 = 42"
    assert compute.answer("20% off 50") == "20% off 50 = 40"
    assert compute.answer("increase 200 by 15%") == "200 increased by 15% = 230"
    assert compute.answer("average of 2, 4, 6") == "average of 2, 4, 6 = 4"
    assert compute.answer("what is 1,000 + 2,500") == "1000 + 2500 = 3500"   # thousands commas
    assert compute.answer("$50 + $20") == "50 + 20 = 70"                       # currency signs


def test_phrasing_is_consistent():
    """The method for consistent parsing: equivalence classes — many phrasings, ONE canonical
    statement (and therefore ONE seal). Widen the normalizer until each class collapses to a point."""
    classes = [
        ["3 + 4", "3+4", "3  +  4", "add 3 and 4", "3 plus 4", "sum of 3 and 4"],
        ["8 * 7", "8x7", "8 times 7", "multiply 8 by 7", "the product of 8 and 7", "8 × 7"],
        ["12 / 4", "12 divided by 4", "divide 12 by 4", "12 ÷ 4"],
    ]
    for group in classes:
        outs = {compute.answer(q) for q in group}
        assert len(outs) == 1, f"phrasings did not converge: {group} -> {outs}"
        assert None not in outs, f"a phrasing failed to compute: {group}"


def test_unit_conversion():
    assert compute.answer("convert 10 miles to kilometers") == "10 miles = 16.0934 kilometers"
    assert compute.answer("how many ounces in a pound") == "1 pound = 16 ounces"
    assert compute.answer("how many minutes in an hour") == "1 hour = 60 minutes"


def test_temperature():
    assert compute.answer("what is 100 fahrenheit in celsius") == "100 °F = 37.78 °C"
    assert compute.answer("0 celsius in fahrenheit") == "0 °C = 32 °F"


def test_declines_non_math_and_nonsense():
    # a calculator that guesses is worse than none — these MUST return None (fall through to search)
    for q in ["how far away is the moon", "the sky is blue", "what does agape mean",
              "convert 10 miles to grams", "what is the meaning of life", ""]:
        assert compute.answer(q) is None, q


def test_declines_absurd_results_instead_of_crashing():
    # a result too large to represent must DECLINE, never raise (found live: a raw 500 on /ask)
    assert compute.answer("what is 2 to the power of 99999999") is None
    assert compute.answer("what is 2**99999999") is None
    assert compute.answer("what is 2 to the power of 100000000000") is None
    # ordinary powers must still compute exactly
    assert compute.answer("what is 2 to the power of 10").endswith("= 1024")


def test_worded_and_convert_phrasings_decline_on_overflow_instead_of_crashing():
    # found: _worded() ("double X", "multiply X by Y", ...), _temperature(), and _do_convert()
    # each call _fmt() directly on a caller-supplied number with no finiteness check — unlike
    # _arith()'s ast-expression path, which already declines on inf/nan before formatting. A
    # large-enough literal (300+ digits) overflows float() to inf, and _fmt()'s round(x)
    # (single-arg -> int) then raises OverflowError. Confirmed live via POST /ask.
    huge = "9" * 320
    for q in (f"double {huge}", f"triple {huge}", f"multiply {huge} by {huge}",
              f"add {huge} and {huge}", f"{huge} percent of {huge}",
              f"convert {huge} miles to kilometers", f"{huge} fahrenheit to celsius"):
        assert compute.answer(q) is None, q          # decline, never raise
    # ordinary worded/convert phrasings still compute exactly
    assert compute.answer("double 21").endswith("= 42")
    assert compute.answer("100 fahrenheit in celsius") is not None


def test_no_arbitrary_code_execution():
    # the evaluator is ast-numeric only — names/calls other than sqrt/cbrt never execute
    for q in ["__import__('os').system('x')", "what is open('x')", "what is a.b.c"]:
        assert compute.answer(q) is None
