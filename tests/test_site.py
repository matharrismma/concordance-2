"""Site test — the front door's files exist and call the right endpoints.

Lightweight (no live server — the integrated server is exercised in dev via
`python -m concordance serve`; the dispatcher is covered by test_api). Guards that the
site is present, named, positioned, wired to the API, and honestly links to the witness.
Runnable with `pytest` OR `python tests/test_site.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
SITE = _ROOT / "site"


def test_site_files_exist():
    for f in ("index.html", "seal.html", "styles.css"):
        assert (SITE / f).is_file(), f"missing site file: {f}"


def test_index_named_positioned_and_wired():
    t = (SITE / "index.html").read_text(encoding="utf-8")
    assert "Narrow" in t and "narrowing the possibilities" in t, "name + positioning"
    assert "/verify" in t and "/search" in t, "the demo must call the API"
    assert "narrowhighway.org" in t, "honest link to the witness — not hiding"
    assert "witness-banner" in t and "/identity" in t, "surface-aware: name the foundation on .org"


def test_seal_page_calls_seal_endpoint():
    t = (SITE / "seal.html").read_text(encoding="utf-8")
    assert "/seal" in t


def test_cli_entrypoint_importable():
    sys.path.insert(0, str(_ROOT / "src"))
    import concordance.__main__ as m
    assert hasattr(m, "main")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} site tests passed — the front door is built, named, and wired.")
