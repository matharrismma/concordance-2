"""Web-hardening regressions (Phase-2 red-team fixes).

- CAS hash validation blocks path traversal via /seal, /s/, /b/.
- URL-scheme allowlist keeps javascript:/data: out of any href.
- render_card_html never emits a script-scheme URL even from a hostile card.source.url.
"""
from concordance import cas
from concordance.web.api import _safe_url, render_card_html


def test_cas_rejects_traversal_and_non_hashes():
    assert cas.fetch("../../../../etc/passwd") is None
    assert cas.fetch("../../secrets") is None
    assert cas.fetch("not a hash") is None
    assert cas.fetch("ABCDEF0123") is None          # too short
    assert cas.fetch("g" * 64) is None              # 64 chars but not hex
    assert cas.fetch("A" * 64) is None              # uppercase (hashes are lowercase)
    assert cas.exists("../../etc/passwd") is False
    assert cas.exists("g" * 64) is False
    assert cas.fetch("a" * 64) is None              # well-formed but absent -> clean None


def test_safe_url_blocks_script_schemes():
    for bad in ("javascript:alert(1)", "data:text/html,<script>1</script>", "vbscript:x",
                "  javascript:alert(1)", "JaVaScRiPt:alert(1)", "java\tscript:alert(1)"):
        assert _safe_url(bad) == "", bad
    for ok in ("https://example.org", "http://x.io", "/card/y", "#top", "mailto:a@b.co",
               "/canon.html?ref=John 1"):
        assert _safe_url(ok) == ok, ok


def test_card_page_never_emits_script_url():
    card = {"id": "card_n_x", "kind": "note", "lifecycle_stage": "public", "title": "T", "body": "b",
            "source": {"label": "L", "ref": "R", "url": "javascript:alert(document.cookie)"}}
    _st, html = render_card_html("card_n_x", card)
    assert "javascript:" not in html and 'href="javascript' not in html
