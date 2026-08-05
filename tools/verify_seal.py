#!/usr/bin/env python3
"""Independent seal verifier — re-check a Narrow Highway receipt with NO Narrow Highway code.

    python tools/verify_seal.py record.json
    python tools/verify_seal.py record.json --expect <content_hash>

Task #127, assessment F-12: "the receipt carries trust without trusting us." This file imports
ONLY the standard library — no concordance module — so a stranger can copy these ~60 lines
anywhere and independently confirm that a record's bytes still hash to the seal that cites them.
If this script and the engine ever disagree about a hash, one of them has broken canonical form,
and the disagreement itself is the alarm.

THE CANONICAL FORM (docs/SEAL_SPEC.md, normative): JSON with sorted keys, separators (",", ":"),
ensure_ascii=False, UTF-8 encoded; the self-referential fields `content_hash` and
`permanent_ref` are excluded before hashing (a hash cannot contain itself); SHA-256 over those
bytes, lowercase hex.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

EXCLUDED = ("content_hash", "permanent_ref")


def canonical_bytes(record: dict) -> bytes:
    trimmed = {k: v for k, v in record.items() if k not in EXCLUDED}
    return json.dumps(trimmed, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def verify(record: dict, expect: str | None = None) -> tuple[bool, str, str]:
    """(ok, computed_hash, verdict_line). Three states: MATCHES / TAMPERED / NO_CLAIM."""
    computed = hashlib.sha256(canonical_bytes(record)).hexdigest()
    claimed = expect or record.get("content_hash") or ""
    if not claimed:
        return False, computed, ("NO_CLAIM: the record carries no content_hash and none was "
                                 "given with --expect — nothing to verify against")
    if computed == claimed:
        return True, computed, f"MATCHES: the bytes still hash to {computed[:16]}… — unaltered"
    return False, computed, (f"TAMPERED-OR-WRONG: computed {computed[:16]}… but the seal claims "
                             f"{claimed[:16]}… — the record has been altered, or this is not "
                             f"the record that seal was minted over")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("record", help="path to the record JSON (or - for stdin)")
    ap.add_argument("--expect", help="content_hash to check against (else the record's own)")
    a = ap.parse_args()
    raw = sys.stdin.read() if a.record == "-" else open(a.record, encoding="utf-8").read()
    ok, computed, line = verify(json.loads(raw), a.expect)
    print(line)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
