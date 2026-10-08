"""THE FAILURE REPORT (Matt, 2026-10-08): 7 wrong verdicts in 37 verify calls, 4 of them false confirmations. Each
row of the report is pinned here through the same door it came in by (audit.audit, sealing off), so the four
critical defects cannot return:

  C1  the elapsed-year check allowed a one-year miss ("2024 to 2028 is 3 years" HELD)       -> judged exactly
  C2  a negation or attitude governing the claim was ignored ("It is false that 2 + 2 = 4")  -> DECLINED, INCOMPLETE
  C3  decimals compared as floats ("0.1 + 0.2 = 0.3" BROKEN); "$29.3 million" read as 29.3   -> exact rationals,
      stated precision, scale words
  C4  a top-level HOLDS covered text that was never checked                                   -> PARTIAL

and the High rows the fixes touched: the reversed percent, hourly -> annual, the third compound ordering, the site's
own molar-mass demo, pi, and "1 mile is 1.6 km" at its stated precision."""
from __future__ import annotations

import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-report-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)

from concordance.audit import audit  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.verifiers import mathematics as M  # noqa: E402
from concordance.verifiers import history_chronology as H  # noqa: E402
from concordance.verifiers.base import literal_scale  # noqa: E402

CFG = EngineConfig("secular")


def _run(text: str):
    return audit(text, CFG, seal=False, index=False, card=False)


def _verdict(text: str) -> str:
    return _run(text)["verdict"]


# ── C1 ────────────────────────────────────────────────────────────────────────────────────────────
def test_c1_elapsed_years_are_judged_exactly():
    assert _verdict("From 2024 to 2028 is 4 years") == "HOLDS"
    assert _verdict("From 2024 to 2028 is 3 years") == "BROKEN"
    assert _verdict("From 2024 to 2028 is 5 years") == "BROKEN"
    assert _verdict("From 2020 to 2021 is 2 years") == "BROKEN"
    r = H.verify_year_arithmetic({"from_year": 2024, "to_year": 2028, "claimed_elapsed_years": 5})
    assert r.status == "MISMATCH" and r.data["tolerance"] == 0 and "inclusive" in r.detail
    assert H.verify_year_arithmetic({"from_year": 1900, "to_year": 2000, "claimed_elapsed_years": 100}).status == "CONFIRMED"


# ── C2 ────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_a_governed_claim_is_declined_never_checked_as_asserted():
    for text in ("It is false that 2 + 2 = 4",
                 "Nobody believes that 15% of 200 is 30",
                 "He denies that 2 + 2 = 4",
                 "2 + 2 = 4 is false",
                 "Suppose 2 + 2 = 5"):
        r = _run(text)
        assert r["verdict"] == "INCOMPLETE", (text, r["verdict"])
        assert r["results"][0]["status"] == "DECLINED" and r["results"][0].get("governed_by"), text
        assert r["coverage"]["governed"] and not r["coverage"]["complete"]
    # the bare claim, and benign framing, still hold
    assert _verdict("2 + 2 = 4") == "HOLDS"
    assert _verdict("It is true that 2 + 2 = 4") == "HOLDS"
    assert _verdict("Check: 2 + 2 = 4") == "HOLDS"


# ── C3 ────────────────────────────────────────────────────────────────────────────────────────────
def test_c3_decimals_are_exact_and_the_stated_precision_sets_the_bar():
    assert _verdict("0.1 + 0.2 = 0.3") == "HOLDS"
    assert _verdict("1.1 + 2.2 = 3.3") == "HOLDS"
    assert _verdict("0.1 + 0.2 = 0.4") == "BROKEN"
    r = M.verify_equality({"expr_a": "0.1 + 0.2", "expr_b": "0.3"})
    assert r.status == "CONFIRMED" and "exact rational" in r.detail
    # the structured door with no literal stays exact: 1/3 is not 0.333
    assert M.verify_equality({"expr_a": "1/3", "expr_b": "0.333"}).status == "MISMATCH"
    # the prose door hands the literal over: three stated figures earn half a unit in the last place
    ok = M.verify_equality({"expr_a": "1/3", "expr_b": "0.333", "claimed_literal": "0.333"})
    assert ok.status == "CONFIRMED" and ok.data.get("stated_sigfigs") == 3
    assert M.verify_equality({"expr_a": "1/3", "expr_b": "0.3", "claimed_literal": "0.3"}).status == "MISMATCH"   # 1 figure, no window
    assert M.verify_equality({"expr_a": "1/3", "expr_b": "0.334", "claimed_literal": "0.334"}).status == "MISMATCH"


def test_c3_scale_words_are_read_and_the_future_value_is_judged_at_its_stated_precision():
    assert literal_scale("$29.3 million") == ("29.3", 1e6)
    assert literal_scale("$5k") == ("5", 1e3)
    assert literal_scale("41,600") == ("41,600", 1.0)
    assert literal_scale("5 m") == ("5", 1.0)                        # a spaced m is metres, not millions
    r = _run("$18 million invested at 5% compounded annually for 10 years grows to $29.3 million")
    assert r["verdict"] == "HOLDS", r
    assert "29,320" in r["results"][0]["detail"].replace(",", ",") or "29320" in r["results"][0]["detail"]
    assert _verdict("$18 million invested at 5% compounded annually for 10 years grows to $31.3 million") == "BROKEN"
    # the third ordering (H2)
    assert _verdict("$18 million at 5% compounded annually grows to $29.3 million over 10 years") == "HOLDS"


# ── C4 ────────────────────────────────────────────────────────────────────────────────────────────
def test_c4_a_top_level_holds_requires_the_checked_claims_to_cover_the_text():
    r = _run("2 + 2 = 4, therefore vaccines cause autism and the earth is 6,000 km in diameter")
    assert r["verdict"] == "PARTIAL" and r["held"] == 1
    assert not r["coverage"]["complete"] and any("vaccines" in x for x in r["coverage"]["unchecked_text"])
    assert "Not checked" in r["note"]
    r = _run("100 + 50 = 150 dollars, which is 40% more than 100")
    assert r["verdict"] == "PARTIAL" and any("40%" in x for x in r["coverage"]["unchecked_text"])
    # a false claim is false whatever surrounds it
    assert _verdict("2 + 2 = 5, therefore the sky is green and grass is blue") == "BROKEN"
    # a unit word or a short tail after the claim is not material
    assert _verdict("100 + 50 = 150 dollars.") == "HOLDS"
    assert _verdict("The speed of light is 299792458 m/s.") == "HOLDS"
    assert _verdict("Indeed, 2 + 2 = 4, of course.") == "HOLDS"
    # two covered claims, nothing else -> complete
    r = _run("2 + 2 = 4 and 3 + 3 = 6")
    assert r["verdict"] == "HOLDS" and r["coverage"]["complete"] and r["held"] == 2


# ── the High rows the criticals touched ──────────────────────────────────────────────────────────
def test_high_rows_the_fixes_reach():
    assert _verdict("27 is 71% of 42") == "BROKEN"                                  # 64.3%
    assert _verdict("$27 million is 71% of $42 million") == "BROKEN"
    assert _verdict("30 is 15% of 200") == "HOLDS"
    assert _verdict("$20 per hour is $41,600 per year") == "HOLDS"
    assert _verdict("$20 per hour is $45,000 per year") == "BROKEN"
    assert _verdict("aspirin C9H8O4 is 180.16 g/mol") == "HOLDS"                     # the site's own demo claim
    assert _verdict("aspirin C9H8O4 is 190.16 g/mol") == "BROKEN"
    assert _verdict("pi is 3.14") == "HOLDS"                                          # three stated figures
    assert _verdict("pi is 3.15") == "BROKEN"
    assert _verdict("pi is 3") == "BROKEN"                                            # one figure earns no window
    assert _verdict("the golden ratio is 1.618") == "HOLDS"
    assert _verdict("1 mile is 1.6 km") == "HOLDS"                                   # two stated figures
    assert _verdict("1 mile is 1.7 km") == "BROKEN"
    assert _verdict("100 kilometers is 62.14 miles") == "HOLDS"


# ── H6: the one tolerance rule ───────────────────────────────────────────────────────────────────
def test_h6_one_rule_the_stated_figures_set_the_window_and_only_a_hedge_widens_it():
    """H6: "about 10 years" passed for 10.29, a one-year miss passed, "approximately 300,000 km/s" and
    "1 mile is 1.6 km" were BROKEN — four windows, four rules. Now one (verifiers.base.stated_window): two or
    more stated figures earn half a unit in the last place; a hedge word doubles it and grants it to a
    one-figure claim; nothing else widens a prose claim. Structured calls (no literal) keep their own defaults."""
    from concordance.verifiers.base import stated_window, hedged_before
    assert stated_window("9.81") == 0.005 and stated_window("9.81", hedged=True) == 0.01
    assert stated_window("10") is None and stated_window("10", hedged=True) == 5.0
    assert stated_window("300,000", hedged=True, unit_factor=1000) == 5e7
    assert hedged_before("the speed of light is about ") and hedged_before("roughly") and hedged_before("~")
    assert not hedged_before("the speed of light is ")
    # rule of 72 at 7% (10.29): "about 10 years" holds by its hedge; a bare one-figure "10" is judged exactly
    assert _verdict("at 7% money doubles in about 10 years") == "HOLDS"
    r = _run("at 7% money doubles in 10 years")
    assert r["verdict"] == "BROKEN" and "about 10 years" in r["results"][0]["detail"]
    assert _verdict("at 7% money doubles in 10.3 years") == "HOLDS"
    # value-first constant: a one-figure claim granted its window by the hedge, and only by the hedge
    assert _verdict("approximately 300,000 km/s is the speed of light") == "HOLDS"
    assert _verdict("300,000 km/s is the speed of light") == "BROKEN"
    assert _verdict("approximately 400,000 km/s is the speed of light") == "BROKEN"
    # a hedge doubles a stated window to a full unit in the last place: "about 1.7 km" (1.609 is one unit off)
    # holds by the hedge, "1.7 km" bare does not, and "about 1.8 km" is out either way
    assert _verdict("1 mile is about 1.6 km") == "HOLDS"
    assert _verdict("1 mile is about 1.7 km") == "HOLDS" and _verdict("1 mile is 1.7 km") == "BROKEN"
    assert _verdict("1 mile is about 1.8 km") == "BROKEN"
    # molar mass through the same rule: two figures hold, one figure is exact, a hedged one figure earns ±5
    assert _verdict("the molar mass of water is 18 g/mol") == "HOLDS"
    assert _verdict("the molar mass of water is 20 g/mol") == "BROKEN"
    assert _verdict("the molar mass of water is about 20 g/mol") == "HOLDS"
    assert _verdict("the molar mass of water is about 30 g/mol") == "BROKEN"
    # the structured door carries no literal and keeps its own default
    from concordance.verifiers import economics as E
    assert E.verify_rule_of_72({"rate_percent": 7, "claimed_doubling_years": 10}).status == "CONFIRMED"


# ── H7: no dead end for a numeric claim ──────────────────────────────────────────────────────────
def test_h7_an_unparsed_numeric_claim_gets_a_structured_template_not_a_want():
    """H7: arithmetic the extractors could not parse was routed to "open a want" — a want is for a missing
    SOURCE, and arithmetic needs none. The door now hands back a template for the structured form, built from
    the words and never evaluated; a lookup-shaped numeric claim keeps the find path and gets the template too."""
    from concordance import factfind
    from concordance.audit import structured_hint, looks_arithmetic
    text = "the total of 3 widgets at 4 dollars comes to 12 dollars"
    assert _verdict(text) == "NOTHING_TO_CHECK" and looks_arithmetic(text)
    fb = factfind.verify_fallback(text, search=lambda q, limit=3: [])
    assert "want" not in fb and fb["structured"]["template"]["mode"] == "equality"
    assert fb["structured"]["template"]["params"]["expr_b"] == "12"
    assert fb["structured"]["template"]["params"]["expr_a"].startswith("<")      # a slot to fill, never a guess
    assert "structured form" in fb["note"]
    h = structured_hint("40 hours at $18.50/hr = $800.00")
    assert h["template"]["mode"] == "equality" and h["template"]["params"]["expr_b"] == "800.00"
    assert h["template"]["params"]["expr_a"].startswith("<")                      # "40 18.50 /" is not arithmetic
    assert structured_hint("twelve divided by three is four") is None            # no number, no template
    assert structured_hint("3 times 4 plus 1 equals 13")["template"]["params"] == {"expr_a": "3 * 4 + 1", "expr_b": "13"}
    fb2 = factfind.verify_fallback("the mayor of Springfield is 55 years old", search=lambda q, limit=3: [])
    assert "want" in fb2 and fb2["structured"]["template"]["mode"] == "numeric"

