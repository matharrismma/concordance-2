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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} seal-page tests passed — citable receipts, server-rendered + safe.")
