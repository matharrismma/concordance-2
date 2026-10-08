"""The frozen cache (2026-10-08): the frozen-shelf DF table + compact index, persisted and keyed on exactly the
inputs that produce them. The pins that make it honest: the key moves when a contributor file, the freeze set
or the format changes; a wrong key, a corrupt file or a foreign version is a miss, never a partial read; the
roundtrip is exact; the safety valve turns it off."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import frozen_cache as FC  # noqa: E402


def _touch(p: Path, text: str) -> Path:
    p.write_text(text, encoding="utf-8")
    return p


def test_key_is_stable_and_sensitive(tmp_path):
    a = _touch(tmp_path / "a.jsonl", "x\n")
    b = _touch(tmp_path / "b.jsonl", "yy\n")
    k1 = FC.make_key([a, b], {"dictionary", "gutenberg"})
    assert k1 == FC.make_key([b, a], {"gutenberg", "dictionary"})          # order-free
    assert k1 != FC.make_key([a], {"dictionary", "gutenberg"})              # a contributor dropped
    assert k1 != FC.make_key([a, b], {"dictionary"})                        # the freeze set changed
    time.sleep(0.01)
    _touch(a, "x changed\n")                                                # size + mtime change
    assert k1 != FC.make_key([a, b], {"dictionary", "gutenberg"})


def test_roundtrip_is_exact_and_wrong_key_is_a_miss(tmp_path):
    p = FC.cache_path(tmp_path)
    df = {"light": 3, "salt": 1, "shepherd": 2}
    fz = {"c3": ("scripture.psalms", "Shepherd", "witness"), "c9": ("dictionary.source", "Zymurgy", "secular")}
    assert FC.save(p, "key-A", df, fz, ["cards.jsonl", "dictionary_cards.jsonl"])
    got = FC.load(p, "key-A")
    assert got and got["df"] == df and got["fz"] == fz and got["contributors"] == ["cards.jsonl", "dictionary_cards.jsonl"]
    assert FC.peek_contributors(p) == ["cards.jsonl", "dictionary_cards.jsonl"]
    assert FC.load(p, "key-B") is None                                      # built from other inputs: miss


def test_corrupt_truncated_or_foreign_is_a_miss_never_an_error(tmp_path):
    p = FC.cache_path(tmp_path)
    assert FC.load(p, "k") is None and FC.peek_contributors(p) is None      # absent
    p.write_bytes(b"\x00\x01garbage")
    assert FC.load(p, "k") is None and FC.peek_contributors(p) is None      # corrupt
    FC.save(p, "k", {"a": 1}, {}, ["x.jsonl"])
    data = p.read_bytes()
    p.write_bytes(data[: len(data) // 2])                                   # truncated
    assert FC.load(p, "k") is None
    import marshal
    p.write_bytes(marshal.dumps({"version": FC.VERSION + 1, "key": "k", "df": {}, "fz": {}, "contributors": []}))
    assert FC.load(p, "k") is None                                          # foreign format version


def test_safety_valve(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_FROZEN_CACHE", raising=False)
    assert FC.enabled()
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE", "0")
    assert not FC.enabled()
