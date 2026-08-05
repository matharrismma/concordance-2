"""Tasks #126 + #127: the benchmark is a package, the seal has an independent witness.

The load-bearing test is the AGREEMENT test: tools/verify_seal.py re-implements the canonical
form from the spec alone (stdlib, no concordance imports). If it and the engine ever hash the
same record differently, one of them broke canonical form — and this fails.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import pytest


def test_the_independent_verifier_agrees_with_the_engine():
    """Mint a record through the engine's own canonicalizer; verify with the outsider."""
    from concordance import cas
    import verify_seal
    rec = {"verdict": "HOLDS", "claim": "2+2=4", "trail": [{"step": 1}],
           "greek": "λόγος", "hebrew": "דָּבָר"}          # ensure_ascii=False is load-bearing
    engine_hash = cas.content_hash_of(rec)
    ok, computed, line = verify_seal.verify(dict(rec, content_hash=engine_hash))
    assert ok and computed == engine_hash, line
    # tamper one character -> TAMPERED, both hashes shown
    ok2, _, line2 = verify_seal.verify(dict(rec, claim="2+2=5", content_hash=engine_hash))
    assert not ok2 and "TAMPERED" in line2
    # no claim to check against is NOT a pass — three states, never two
    ok3, _, line3 = verify_seal.verify(rec)
    assert not ok3 and "NO_CLAIM" in line3


def test_the_verifier_is_genuinely_independent():
    """No concordance import — the whole point is verification without trusting us."""
    import ast as _ast
    src = (ROOT / "tools" / "verify_seal.py").read_text(encoding="utf-8")
    tree = _ast.parse(src)
    imported = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, _ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert "concordance" not in imported, "the independent verifier imports the thing it audits"
    assert {"hashlib", "json"} <= imported


def test_the_benchmark_package_is_machine_readable_and_versioned():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "benchmark.py"), "--json"],
                         capture_output=True, text=True, cwd=str(ROOT),
                         env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), timeout=300)
    d = json.loads(out.stdout)
    assert d["benchmark_version"].count(".") == 2
    assert d["totals"]["cases"] == 60
    assert d["totals"]["false_positives"] == 0, d["false_positives"]
    assert "reproduce" in d
    for row in d["cases"]:
        for k in ("case", "mode", "expected_holds", "verdict", "correct"):
            assert k in row
    # FP and FN are separate fields — a missed truth is never hidden inside accuracy
    assert "false_negatives" in d


def test_every_public_claim_is_benchmark_bounded():
    """The wording sweep, pinned: no public surface may claim a bare universal zero again."""
    for f in ("README.md", "site/connect.html", "site/proof.html"):
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace").lower()
        if "false positive" in text or "false-positive" in text:
            assert "benchmark" in text, f"{f} claims 0 FP without naming the bound"


def test_the_specs_exist_and_state_the_essentials():
    seal = (ROOT / "docs" / "SEAL_SPEC.md").read_text(encoding="utf-8")
    for must in ("sorted keys", "ensure_ascii=False", "SHA-256", "content_hash",
                 "permanent_ref", "verify_seal.py"):
        assert must in seal, f"SEAL_SPEC.md missing: {must}"
    auth = (ROOT / "docs" / "AUTH_POSTURE.md").read_text(encoding="utf-8")
    for must in ("anonymous-open", "consent", "Rate limits", "explicit client authentication"):
        assert must in auth, f"AUTH_POSTURE.md missing: {must}"
