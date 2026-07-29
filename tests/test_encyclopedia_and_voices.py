"""The Encyclopedia as Cards, and the voices of the traditions — nested, honest, resolving to Christ.

Two decks minted this session, both pinned here:

ENCYCLOPEDIA (contract §6 item 9): Easton's 3,962 entries carded into the keeping — stub+link,
boxed by Easton's own categories (the card-catalog drawers), every card member_of the spine, the
spine part_of the Floor. Built AS cards in the existing system, not a separate structure.

VOICES (Matt, 2026-07-27/28): one major voice per tradition, chosen by THEIR reckoning, honest on
both ends, always resolving to Christ — under the frame "a knowledge logistical system... meant to
unify the church. all of the church." A broker never manufactures the goods: each voice carries
its waybill (the gift, the honest note, the Christ-ward resolution, the PD status). Ellen G. White
carries BOTH positions on her prophetic role, neither flattened. Billy Graham carries facts and a
pointer, never his copyrighted text.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _cards():
    from concordance import corpus
    return corpus.default_corpus().cards


def test_the_encyclopedia_is_nested_in_the_keeping():
    """The reference section holds TWO encyclopedias since D5 (Easton 1897 + ISBE 1915) —
    the invariant is not 'one spine' but ZERO ORPHANS: every entry hangs member_of a spine,
    and every spine roots in the Floor."""
    cards = _cards()
    spines = {"card_spine_encyclopedia", "card_spine_isbe"}
    for sid in spines:
        spine = cards.get(sid)
        if spine is None and sid == "card_spine_isbe":
            spines = {"card_spine_encyclopedia"}   # ISBE data not minted on this machine — Easton still gates
            continue
        assert spine is not None, f"{sid} must exist"
        assert any(l.get("to_card_id") == "card_k_floor_of_discovery" and
                   l.get("relationship") == "part_of" for l in spine["connections"]), \
            f"{sid} roots in the Floor of Discovery"
    enc = [c for c in cards.values() if c.get("shelf") == "encyclopedia"]
    assert len(enc) >= 3900, f"expected the encyclopedias carded; found {len(enc)}"
    stray = [c["id"] for c in enc
             if not any(l.get("to_card_id") in spines and
                        l.get("relationship") == "member_of" for l in c.get("connections") or [])]
    assert not stray, f"{len(stray)} encyclopedia card(s) not nested under a spine: {stray[:4]}"


def test_the_drawers_match_the_sources_own_categories():
    """Easton's entries keep Easton's own four drawers; ISBE entries sit in the isbe drawer.
    No source's categories are ever remixed into another's (found, never re-authored)."""
    from collections import Counter
    cards = _cards()
    easton = Counter(c.get("box") for c in cards.values()
                     if c.get("shelf") == "encyclopedia" and str(c.get("id", "")).startswith("card_enc_"))
    assert set(easton) == {"person", "place", "concept", "object"}, easton
    assert easton["person"] >= 900 and easton["place"] >= 900 and easton["concept"] >= 2000
    isbe = [c for c in cards.values()
            if c.get("shelf") == "encyclopedia" and str(c.get("id", "")).startswith("card_isbe_")]
    if isbe:   # minted only where the acquisition ran
        assert all(c.get("box") == "isbe" for c in isbe), "ISBE entries keep their own drawer"
        assert len(isbe) > 9000, f"the whole ISBE came across (got {len(isbe)})"


def test_the_catalog_drawer_filter_serves():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, body = dispatch("GET", "/characters",
                        {"category": "place", "letter": "B", "limit": "10"}, None,
                        EngineConfig("witness"))
    assert st == 200 and body["items"], "the place drawer at B must not be empty (Bethlehem...)"
    assert all(i["category"] == "place" for i in body["items"])


def test_every_voice_is_honest_on_both_ends_and_resolves_to_christ():
    cards = _cards()
    voices = [c for c in cards.values() if c.get("box") == "voice"]
    assert len(voices) == 14, f"fourteen voices expected; found {len(voices)}"
    for v in voices:
        ex = v.get("extra") or {}
        assert ex.get("gift"), f"{v['id']}: the gift the whole church receives must be named"
        assert ex.get("honest_note"), f"{v['id']}: honest on BOTH ends — the contested part is named"
        assert ex.get("resolves_to_christ"), f"{v['id']}: every voice ends at the same Person"
        assert ex.get("pd_status"), f"{v['id']}: the waybill carries the licensing truth"
        # figure_of must point at a tradition card that exists — no dangling grafts
        figs = [l for l in v["connections"] if l["relationship"] == "figure_of"]
        assert figs and figs[0]["to_card_id"] in cards, f"{v['id']}: figure_of dangles"


def test_white_carries_both_positions_and_graham_reproduces_nothing():
    cards = _cards()
    white = next(c for c in cards.values() if c["id"] == "card_voice_ellen_g_white")
    note = white["extra"]["honest_note"].lower()
    assert "adventists hold" in note and "wider church does not" in note, \
        "both positions stated, neither flattened — the nuance is the point"
    graham = next(c for c in cards.values() if c["id"] == "card_voice_billy_graham")
    assert "not public domain" in graham["extra"]["pd_status"].lower()
    assert "no text reproduced" in graham["extra"]["pd_status"].lower() or \
           "never his text" in graham["body"].lower()


def test_every_voice_ref_resolves():
    from concordance.verifiers.scripture import read_passage
    cards = _cards()
    bad = [(c["id"], c["extra"]["ref"]) for c in cards.values() if c.get("box") == "voice"
           if read_passage(c["extra"]["ref"]).get("status") != "ok"]
    assert not bad, f"voice refs that do not resolve: {bad}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the reference section is carded, and every voice ends at Christ.")
