# The Seal, Specified — canonical form, replay, standing (2026-08-04)

Task #127 (assessment F-12). This is the NORMATIVE description of how a Narrow Highway seal is
minted and how anyone re-checks one without trusting us. The reference implementation is
`src/concordance/validate.py` (`canonical_json_bytes`, `content_hash`); the independent verifier
is `tools/verify_seal.py` (~60 lines, stdlib only, no concordance imports).

## Canonical form
1. Take the record as a JSON object.
2. **Exclude** the self-referential fields `content_hash` and `permanent_ref` (a hash cannot
   contain itself).
3. Serialize: JSON, **sorted keys**, separators `(",", ":")` (no whitespace),
   `ensure_ascii=False` — Greek and Hebrew stay human-readable in stored seals AND hash
   identically everywhere. Encode UTF-8.
4. **SHA-256** over those bytes; lowercase hex. That is the `content_hash`.

One canonical form for the whole floor: CAS records, the ledger, badges, and receipts all pass
through `cas.store()`, the one place a seal is born.

## What a seal binds
The record holds the claim, the verdict, the worked trail, verifier identity, and timestamps —
the hash binds ALL of it. Alter one character of the trail and the hash moves; `verify_seal.py`
reports TAMPERED-OR-WRONG with both hashes shown.

## Replay
`GET https://narrowhighway.org/s/<content_hash>` returns the record; re-run the four steps above
and compare. Or offline: `python tools/verify_seal.py record.json`. Three outcomes, never two:
MATCHES / TAMPERED-OR-WRONG / NO_CLAIM (nothing to verify against is not a pass).

## Standing
Seals are append-only (CAS is idempotent; the ledger chains records). A superseded or retracted
finding is recorded by a LATER record — the old seal still verifies over its own bytes; standing
is a ledger question, not a hash question. Ask `witnesses`/`attest_record` for who has borne
witness to a record since.

## Algorithm agility
Current and only algorithm: SHA-256. A future algorithm change adds a version field to new
records; existing seals keep verifying under the rules above — a seal's rules are frozen at mint.
