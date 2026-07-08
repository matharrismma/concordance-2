"""The Auditor — conservative extraction, honest coverage, the moat unchanged underneath.

Locks the auditor's contract: (1) every v1 shape extracts from a true document and HOLDS;
(2) planted falsehoods are CAUGHT; (3) the over-extraction guard — ambiguous phrasings are
NOT extracted (the moat's asymmetry applied to reading: rather miss a claim than check the
wrong one); (4) dedup + the claim cap; (5) an uncheckable text reports NOTHING_TO_CHECK with
no seal; (6) the HTTP route serves it.

Runnable with pytest OR `python tests/test_audit.py` (sovereign — no pytest needed).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import audit as A  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

CFG = EngineConfig("secular")

TRUE_DOC = """
Regular: 40 hours at $18.50/hr = $740.00. Deductions: 12.50 + 8.75 + 33.05 = 54.30.
A 15% of 80 is 12 discount applied. Your salary of $52,000 a year is $25.00 an hour.
$1,000 at 5% compounded annually for 10 years grows to $1,628.89.
At 6% your money doubles in 12 years. The war lasted 4 years (1914-1918).
July 4, 1776 was a Thursday. 2024 was a leap year.
Nutrition Facts: Calories 230, Total Fat 10g, Total Carbohydrates 30g, Protein 5g.
"""

AMBIGUOUS_DOC = """
I walked 40 hours at the park. 5% of the people agreed with him. It was 3 years ago.
$1,000 at 5% for 10 years grows to $1,628.89.
Calories 250 and some protein.
"""  # pay needs $rate; percent needs a base+claim; interest needs the word "compound";
# a nutrition label needs all four figures. None of these may extract.


def test_true_document_all_hold():
    r = A.audit(TRUE_DOC, CFG, seal=False)
    assert r["claims_found"] == 10, [x["extractor"] for x in r["results"]]
    assert r["held"] == 10 and r["broken_or_unchecked"] == 0, r["results"]
    assert r["verdict"] == "HOLDS"
    kinds = {x["extractor"] for x in r["results"]}
    assert {"sum", "percent", "gross_pay", "annual_hourly", "compound_interest",
            "rule_of_72", "elapsed_years", "day_of_week", "leap_year",
            "nutrition_label"} <= kinds


def test_planted_falsehoods_are_caught():
    doc = ("Overtime: 40 hours at $18.50/hr = $800.00. 1900 was a leap year. "
           "Total: 3 x $4.50 = $14.50. Note 12.50 + 8.75 = 21.30.")
    r = A.audit(doc, CFG, seal=False)
    assert r["claims_found"] == 4
    assert r["held"] == 0 and r["broken_or_unchecked"] == 4, r["results"]
    assert all(x["status"] == "MISMATCH" for x in r["results"])


def test_over_extraction_guard():
    """Ambiguity must NOT extract — no claim, no verdict, no guess."""
    assert A.extract(AMBIGUOUS_DOC) == []
    r = A.audit(AMBIGUOUS_DOC, CFG, seal=False)
    assert r["claims_found"] == 0 and r["verdict"] == "NOTHING_TO_CHECK"
    assert "seal" not in r  # emptiness is never sealed


def test_compound_word_is_required():
    with_word = "$1,000 at 5% compounded annually for 10 years grows to $1,628.89."
    without = "$1,000 at 5% for 10 years grows to $1,628.89."
    assert len(A.extract(with_word)) == 1
    assert A.extract(without) == []


def test_dedup_and_cap():
    doc = "1 + 1 = 2. " * 5
    assert len(A.extract(doc)) == 1  # identical claims collapse
    many = " ".join(f"{i} + {i} = {2 * i}." for i in range(1, 60))
    assert len(A.extract(many)) == A.MAX_CLAIMS  # the cap holds


def test_every_result_quotes_its_source():
    r = A.audit(TRUE_DOC, CFG, seal=False)
    squeezed = " ".join(TRUE_DOC.split()).lower()
    for x in r["results"]:
        frag = " ".join(x["claim"].split()).lower()[:40]
        assert frag in squeezed, f"claim quote not from the source text: {x['claim']!r}"


def test_http_route_serves_audit():
    from concordance.web.api import dispatch
    status, payload = dispatch("POST", "/audit", {"seal": "0"},
                               {"text": "12.50 + 8.75 = 21.25"}, CFG)
    assert status == 200 and payload["claims_found"] == 1 and payload["verdict"] == "HOLDS"
    status, payload = dispatch("POST", "/audit", {}, {"text": "   "}, CFG)
    assert status == 400


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} auditor tests passed — conservative extraction, honest coverage, falsehoods caught.")
