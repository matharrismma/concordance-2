"""The calculator must be exact, and must DECLINE what it cannot compute (never a wrong number)."""
from concordance import compute


def test_arithmetic_and_percentages():
    assert compute.answer("what is 8 times 7") == "8 times 7 = 56"
    assert compute.answer("what is 15 percent of 240") == "15% of 240 = 36"
    assert compute.answer("what is 12 divided by 4") == "12 divided by 4 = 3"
    assert compute.answer("what is 2 to the power of 10").endswith("= 1024")
    assert compute.answer("what is the square root of 144").endswith("= 12")


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


def test_no_arbitrary_code_execution():
    # the evaluator is ast-numeric only — names/calls other than sqrt/cbrt never execute
    for q in ["__import__('os').system('x')", "what is open('x')", "what is a.b.c"]:
        assert compute.answer(q) is None
