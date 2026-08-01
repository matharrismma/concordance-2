"""A minted receipt becomes a card, so the promise survives leaving this machine.

CORRECTED 2026-08-01: the original justification ("19 of 20 advertised receipts answered 404")
was a broken measurement — a CRLF artifact, retracted in docs/OPERATIONS_LOG.md. All 20 resolve.

What stands is structural: `data/cas/` is node-local — not deployed, not backed up — so a seal
minted on one machine lives only there while the card citing it travels everywhere. 127 seals
existed only on the operator's machine. Matt's fix:
*"When we mint a receipt, it needs to become a card as well. That would allow us to have both and
not change a ton."*

So `cas.store()` — the ONE place a seal is born — also lands it in the keeping, which is deployed,
sharded, replicated and archived. What this file pins:

  * minting writes both, and the card carries the record verbatim;
  * `/s/<hash>` and `/seal` read EITHER store;
  * the hash still arbitrates — a card whose record does not recompute to the address it claims is
    refused, exactly as a tampered CAS object would be. The card is a second copy, never a second
    authority;
  * a failure to card NEVER fails the seal.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())

from concordance import cas, corpus  # noqa: E402

RECORD = {"kind": "verification", "verdict": "HOLDS", "claim": "2 + 2 = 4",
          "trail": [{"step": "equality", "status": "CONFIRMED"}]}


def test_minting_a_receipt_also_mints_a_card():
    h = cas.store(dict(RECORD))
    card = corpus.get_card(cas.receipt_card_id(h))
    assert card is not None, "the seal was minted and the keeping never heard about it"
    assert card["kind"] == "receipt" and card["shelf"] == "seals"
    assert card["source"]["url"] == "/s/" + h
    assert h[:12] in card["title"] and "HOLDS" in card["title"]


def test_the_card_carries_the_record_and_the_hash_still_arbitrates():
    h = cas.store(dict(RECORD))
    card = corpus.get_card(cas.receipt_card_id(h))
    rec = cas.card_to_record(card)
    assert rec is not None and rec["claim"] == "2 + 2 = 4"
    assert cas.content_hash_of(rec) == h, "the carried record must recompute to its own address"


def test_a_tampered_card_is_refused_like_a_tampered_object():
    """The card is a second COPY, never a second authority."""
    h = cas.store(dict(RECORD))
    card = dict(corpus.get_card(cas.receipt_card_id(h)))
    card["extra"] = dict(card["extra"])
    card["extra"]["record"] = dict(card["extra"]["record"], verdict="BROKEN")
    assert cas.card_to_record(card) is None, "a rewritten receipt passed as genuine"


def test_the_receipt_resolves_when_the_cas_object_is_gone():
    """The whole point: 5,394 hashes were being asked for on a node whose CAS never had them."""
    h = cas.store(dict(RECORD))
    assert cas.fetch(h) is not None
    assert cas.delete(h) is True                      # the object leaves; the card stays
    assert cas.fetch(h) is None, "the object did not actually go"
    rec = cas.fetch_anywhere(h)
    assert rec is not None, "the receipt died with its CAS object"
    assert rec["claim"] == "2 + 2 = 4"
    # The two stores must be BYTE-IDENTICAL. A `_from` marker here once broke the published
    # contract — "re-fetch and the bytes must match" — for clients re-hashing /seal responses.
    assert "_from" not in rec, "the card-served record differs from the CAS-served record"
    assert cas.content_hash_of(rec) == h, "the fallback record does not recompute to its address"


def test_an_unknown_hash_is_still_honestly_absent():
    assert cas.fetch_anywhere("f" * 64) is None
    assert cas.fetch_anywhere("not-a-hash") is None


def test_carding_never_fails_the_seal():
    """A seal is a promise. If the keeping cannot be written, the promise is still kept."""
    import concordance.corpus as _c
    broken = _c.add_to_default
    _c.add_to_default = lambda card: (_ for _ in ()).throw(RuntimeError("keeping is busy"))
    try:
        h = cas.store({"kind": "verification", "verdict": "HOLDS", "claim": "3 + 3 = 6"})
        assert cas.fetch(h) is not None, "a carding failure took the seal down with it"
    finally:
        _c.add_to_default = broken


def test_both_read_paths_use_the_two_store_fetch():
    """Server-side and invisible to the reader is this project's most repeated failure — so the
    HTML receipt page and the JSON seal endpoint are both checked, not just the module."""
    src = (ROOT / "src" / "concordance" / "web" / "api.py").read_text(encoding="utf-8")
    assert "render_seal_html(h, cas.fetch_anywhere(h))" in src, "/s/ still reads only the CAS"
    assert "rec = cas.fetch_anywhere(h)" in src, "/seal still reads only the CAS"


if __name__ == "__main__":
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in fns:
        fn()
        print(f"  ok  {name}")
    print(f"\n{len(fns)} receipt tests passed — the promise survives leaving this machine.")
