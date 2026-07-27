"""CAS — content-addressed store (permanent, hash-keyed records).

Proves the basic store/fetch/exists/delete round trip, and guards the one gap found this
sweep: delete() built its path straight from the caller's content_hash with no validation,
unlike fetch()/exists() in the same module which both already check _valid_hash() first.
Hermetic: everything runs against a throwaway base_dir. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from concordance import cas


def _base():
    return Path(tempfile.mkdtemp(prefix="nh-cas-"))


def test_store_fetch_exists_round_trip():
    base = _base()
    h = cas.store({"hello": "world"}, base_dir=base)
    assert cas._valid_hash(h)
    assert cas.exists(h, base_dir=base) is True
    assert cas.fetch(h, base_dir=base)["hello"] == "world"


def test_delete_removes_a_real_record():
    base = _base()
    h = cas.store({"a": 1}, base_dir=base)
    assert cas.delete(h, base_dir=base) is True
    assert cas.exists(h, base_dir=base) is False
    assert cas.delete(h, base_dir=base) is False        # already gone — not an error


def test_fetch_and_exists_refuse_malformed_hashes():
    base = _base()
    for bad in ("../../../etc/passwd", "not-hex", "a" * 63, "g" * 64, "", None):
        assert cas.fetch(bad, base_dir=base) is None
        assert cas.exists(bad, base_dir=base) is False


def test_delete_refuses_malformed_hashes_without_touching_the_filesystem():
    # found: delete(content_hash) built _record_path(base, content_hash) with ZERO validation —
    # the one function in this module that didn't match fetch()/exists()'s own discipline — and
    # then called path.unlink() if it existed. _record_path splits as base/h[:2]/f"{h[2:]}.json",
    # so h="..important" (h[:2]==".." , h[2:]=="important") resolves to base.parent/"important.json"
    # — a real, confirmed escape one directory up. A traversal-shaped hash must never delete a
    # file outside the CAS store.
    base = _base()
    target = base.parent / "important.json"
    target.write_text('{"secret": true}', encoding="utf-8")

    assert cas.delete("..important", base_dir=base) is False
    assert target.exists(), "a traversal-shaped hash deleted a file outside the CAS store"

    for bad in ("../../../etc/passwd", "not-hex", "a" * 63, "g" * 64, "", None):
        assert cas.delete(bad, base_dir=base) is False


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} cas tests passed.")
