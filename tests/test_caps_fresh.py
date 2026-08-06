"""The numbers on the site must equal the live engine — the enforcement arm of the mechanism that
keeps every public statement factual as the corpus and fleet grow (Matt, 2026-08-06: "make sure
every statement is factual and we have a mechanism to update as we add more").

HTML pages self-update at runtime via nh-caps.js + data-cap attributes; this test guards their
FALLBACK literals and the non-HTML surfaces (llms.txt, the JSON descriptors) that JS cannot touch,
so a stale hardcoded count becomes a red gate rather than a quiet lie. It also forbids the return of
unbounded "the engine is never wrong" phrasing — every 0-false-positive claim must stay bounded to
the benchmark/assay. Runnable with pytest OR `python tests/test_caps_fresh.py`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from concordance import capabilities  # noqa: E402


def _verifier_counts():
    """Live verifier counts, computed WITHOUT touching the corpus (registry-only, always available)."""
    v = capabilities._verifiers()
    return v["secular_modules"]["count"], v["distinct_modules_total"]["count"]


def _resolve(tree: dict, path: str):
    node = tree
    for part in path.split("."):
        node = node[part]
    if isinstance(node, dict) and "count" in node:
        node = node["count"]
    return node


def test_domain_counts_on_surfaces_match_live():
    """Any surface that states "<N> domains" as a bare integer must use the live module count
    (secular, or the distinct total incl. witness). Catches the "60 domains" drift class."""
    secular, distinct = _verifier_counts()
    ok = {secular, distinct}
    surfaces = ["site/proof.html", "site/connect.html", "site/.well-known/mcp.json",
                "docs/registry/server.json"]
    bad = []
    for rel in surfaces:
        text = (_ROOT / rel).read_text(encoding="utf-8")
        for m in re.finditer(r"(\d+)\s+domains", text):
            n = int(m.group(1))
            if n not in ok:
                bad.append(f"{rel}: '{n} domains' — live secular={secular}, distinct={distinct}")
    assert not bad, "stale domain counts (wire to /capabilities or correct):\n  " + "\n  ".join(bad)


def test_data_cap_fallbacks_match_live():
    """Every data-cap fallback literal in the HTML must equal the live value it will be replaced
    with — so JS-off readers and crawlers never see a stale number."""
    tree = {"verifiers": capabilities._verifiers()}
    bad = []
    for p in (_ROOT / "site").glob("*.html"):
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r'data-cap="([^"]+)"[^>]*>([\d,]+)<', text):
            path, literal = m.group(1), int(m.group(2).replace(",", ""))
            try:
                live = int(_resolve(tree, path))
            except Exception:  # noqa: BLE001
                # a path outside the verifiers subtree (e.g. substrate.cards) isn't checked here —
                # those are volatile and rendered qualitatively; skip rather than fail.
                continue
            if live != literal:
                bad.append(f"{p.name}: data-cap={path} fallback {literal} != live {live}")
    assert not bad, "stale data-cap fallbacks:\n  " + "\n  ".join(bad)


def test_no_unbounded_infallibility_claims():
    """No served surface may claim the engine cannot be wrong. '0 false positives' must always be
    bounded (to the benchmark or an assay), never 'ever' / 'never sealed a falsehood' /
    'across every domain'. Matt, 2026-08-06: 'I don't want to have any lie on the site.'"""
    banned = ["never sealed a falsehood", "false positives · ever", "every falsehood caught",
              "benchmark runs across every domain", "can never be wrong", "cannot be wrong",
              "never wrong"]
    surfaces = list((_ROOT / "site").glob("*.html")) + [
        _ROOT / "site" / "llms.txt",
        _ROOT / "site" / ".well-known" / "mcp.json",
        _ROOT / "docs" / "registry" / "server.json",
    ]
    bad = []
    for p in surfaces:
        low = p.read_text(encoding="utf-8").lower()
        for phrase in banned:
            if phrase in low:
                bad.append(f"{p.name}: '{phrase}'")
    assert not bad, "unbounded infallibility claims (scope to the benchmark):\n  " + "\n  ".join(bad)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} capability-freshness checks passed — the site's numbers match the engine.")
