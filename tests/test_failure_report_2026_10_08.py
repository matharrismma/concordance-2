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
