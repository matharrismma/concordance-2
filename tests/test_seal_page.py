"""Server-rendered citable receipt page — the data is in the markup, crawlable + safe.

A seal at /s/<hash> must render the verdict + trail + hash in server-side HTML (so search
engines and LLMs can read and cite it), 404 cleanly when absent, and HTML-escape claim text.
Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.web.api import render_seal_html  # noqa: E402


def _rec(overall, claim="2+2 = 4"):
    return {
        "overall": overall,
        "gate_results": [{"gate": "RED", "status": overall}],
        "verifier_results": [{"name": "s1",
                              "status": "CONFIRMED" if overall == "PASS" else "MISMATCH",
                              "detail": "checked", "data": {"claim": claim}}],
    }


def test_pass_renders_holds_with_data_in_markup():
    st, html = render_seal_html("abc123def4567890aa", _rec("PASS"))
    assert st == 200
    assert html.startswith("<!doctype html>")
    assert "HOLDS" in html and "abc123def4567890aa" in html and "2+2 = 4" in html
    assert "<title>" in html and "og:description" in html  # crawler/LLM metadata


def test_missing_seal_is_404():
    st, html = render_seal_html("deadbeef", None)
    assert st == 404 and "No such seal" in html


def test_reject_renders_broken():
    st, html = render_seal_html("h", _rec("REJECT"))
    assert st == 200 and "BROKEN" in html


def test_claim_text_is_escaped():
    st, html = render_seal_html("h", _rec("PASS", claim="<script>evil()</script>"))
    assert "<script>evil()</script>" not in html and "&lt;script&gt;" in html


def test_a_card_never_advertises_a_seal_it_does_not_have():
    """A `source_hash` fingerprints the SOURCE TEXT; a seal is a sealed verification record in the
    CAS. They are different objects, and the card renderer used to fall back from one to the other.

    Measured 2026-07-31: 66 cards carried a real seal_hash; **11,084 carried only a source_hash and
    were given an "its seal" link anyway**, every one resolving to 404. Offering a receipt that was
    never minted is worse than offering none — it is a claim of verification we did not perform, on
    the surface built to prove we do not do that. A fingerprint is not a verdict.
    """
    from concordance.web import api

    # a card with ONLY a source_hash must show no seal link at all
    _st, html = api.render_card_html("c1", {
        "id": "c1", "title": "T", "body": "b", "source": {"label": "S"},
        "source_hash": "5d451e97f1b39f72e46f0000000000000000000000000000000000000000aaaa"})
    assert "its seal" not in html, "a source_hash was rendered as a seal"
    assert "/s/5d451e97" not in html

    # a card with a REAL seal keeps it
    _st, html2 = api.render_card_html("c2", {
        "id": "c2", "title": "T", "body": "b", "source": {"label": "S"},
        "extra": {"seal_hash": "809fbaa9498918cf30440000000000000000000000000000000000000000bbbb"}})
    assert "its seal" in html2 and "/s/809fbaa9" in html2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} seal-page tests passed — citable receipts, server-rendered + safe.")


def test_every_addressable_page_names_com_as_its_one_true_address():
    """The card and seal pages used PATH-relative canonicals, so the same card served on .com,
    .tv and api. declared three different "true addresses" and split the library's search
    standing three ways. Matt, 2026-08-01: ".tv isn't the priority. We focus on .com and then
    .org." Whichever door serves the page, the claim of where it LIVES is one address."""
    from concordance.web.api import CANONICAL_HOST, render_card_html, render_seal_html
    assert CANONICAL_HOST == "https://narrowhighway.com"
    card = {"id": "card_x", "title": "T", "body": "B", "shelf": "test",
            "source": {"label": "L", "url": ""}}
    _, html = render_card_html("card_x", card)
    assert 'rel=canonical href="https://narrowhighway.com/card/card_x"' in html
    _, shtml = render_seal_html("a" * 64, {"overall": "HOLDS"})
    # the RECORD's keeper is the witness — cards live on .com, seals live on .org
    assert 'rel=canonical href="https://narrowhighway.org/s/' + "a" * 64 + '"' in shtml
    # and no path-relative canonical survives anywhere in either page
    assert 'rel=canonical href="/' not in html and 'rel=canonical href="/' not in shtml
