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


def test_verify_warm_preimports_heavy_deps():
    """warm() must pre-import the heavy verify C-extensions so the first heavy verification
    never pays a cold import inside the per-verification timeout (the assay's cold-start finding:
    a TRUE claim transiently sheds to ERROR — errs safe, but a false negative)."""
    import sys as _sys
    from concordance import derivation
    derivation.warm()
    # sympy backs the math moat and is a hard dep — it must be resident after warm().
    assert "sympy" in _sys.modules, "warm() did not import sympy"
    derivation.warm()  # idempotent — a second warm must not raise


def test_verify_saturation_sheds_to_error_and_logs():
    """When the pool is saturated the load-shed must (a) return ERROR — never a false HOLDS on a
    TRUE claim — and (b) LOG a warning, so the transient is observable in production, not silent.
    Saturation is forced deterministically by draining every slot."""
    import logging as _logging
    from concordance import derivation as D

    msgs = []

    class _Cap(_logging.Handler):
        def emit(self, r):
            msgs.append(r.getMessage())

    lg = _logging.getLogger("concordance")
    h = _Cap()
    lg.addHandler(h)
    held = 0
    try:
        while D._SLOTS.acquire(blocking=False):   # drain every verify slot
            held += 1
        # a claim that WOULD confirm now has no slot -> must shed to ERROR, and say so
        res = D.verify_domain("statistics", {"STAT_VERIFY": {"estimate": 1.0, "ci_low": 0.0, "ci_high": 2.0}})
        assert res["status"] == "ERROR", res              # errs safe — never HOLDS/MISMATCH
        assert any("saturated" in m for m in msgs), msgs  # and it was logged
        msgs.clear()
        res2 = D.verify_math({"mode": "equality", "params": {"expr_a": "x", "expr_b": "x", "variables": ["x"]}})
        assert res2["status"] == "ERROR" and any("saturated" in m for m in msgs)
    finally:
        for _ in range(held):
            D._SLOTS.release()
        lg.removeHandler(h)
