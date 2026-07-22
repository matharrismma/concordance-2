"""Recall — we recall what is important, not everything.

The discipline under test: durable artifacts (seals, scripture, word studies) become cards;
ordinary conversation does not. The chain still holds every word — nothing is deleted — but
only what is worth recalling is promoted.
"""
import os
import tempfile

os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-recall-threads-")
os.environ["CONCORDANCE_STACKS_DIR"] = tempfile.mkdtemp(prefix="nh-recall-stacks-")

from concordance import recall, stacks, threads  # noqa: E402


def _thread():
    tid = threads.new_thread()["thread_id"]
    threads.append(tid, "what does chesed mean in H2617",
                   {"kind": "word_study", "message": "covenant loyalty"})
    threads.append(tid, "read John 3:16", {"kind": "scripture", "message": "For God so loved"})
    threads.append(tid, "is 0.1 + 0.2 = 0.3",
                   {"kind": "verify", "message": "BROKEN",
                    "seal": {"cite_url": "https://narrowhighway.com/s/abc123"}})
    threads.append(tid, "ok thanks, that's helpful", {"kind": "found", "message": "found"})
    return tid


def _thread_with(ref, strongs):
    """A conversation over artifacts unique to one test — these tests share a store, so a
    test that asserts 'nothing held yet' must use something no other test has carded."""
    tid = threads.new_thread()["thread_id"]
    threads.append(tid, f"read {ref} and {strongs}",
                   {"kind": "scripture", "message": "found"})
    return tid


def test_the_important_things_become_cards():
    r = recall.remember(_thread())
    assert r["ok"] and r["count"] >= 3
    assert {"seal", "scripture", "word"} <= {c["kind"] for c in r["kept"]}


def test_a_sealed_receipt_is_recalled():
    seals = [c for c in recall.remember(_thread())["kept"] if c["kind"] == "seal"]
    assert seals and "abc123" in seals[0]["text"]


def test_small_talk_is_not_promoted_to_a_card():
    """'ok thanks, that's helpful' leaves no card — we cannot recall everything."""
    r = recall.remember(_thread())
    assert not any("thanks" in c["text"].lower() for c in r["kept"])


def test_the_chain_still_holds_everything():
    """Nothing is discarded: what is not promoted is still in the record, verbatim."""
    tid = _thread()
    recall.remember(tid)
    said = [e["user"] for e in threads.get(tid)["exchanges"]]
    assert "ok thanks, that's helpful" in said


def test_recalling_twice_adds_nothing():
    tid = _thread()
    first = recall.remember(tid)["count"]
    again = recall.remember(tid)["count"]
    assert first > 0 and again == 0


def test_recalled_reads_back_what_was_stored():
    tid = _thread()
    n = recall.remember(tid)["count"]
    back = recall.recalled(tid)
    assert back["ok"] and back["count"] == n


def test_a_card_lives_once_and_is_referenced():
    """The superposition model: the same verse recalled again is not a second card."""
    tid = _thread()
    recall.remember(tid)
    threads.append(tid, "John 3:16 again", {"kind": "scripture", "message": "again"})
    recall.remember(tid)
    refs = [c for c in recall.recalled(tid)["kept"]
            if c["kind"] == "scripture" and "John 3:16" in c["text"]]
    assert len(refs) == 1


def test_unknown_thread_is_handled():
    assert recall.remember("0" * 32)["ok"] is False


def test_an_empty_conversation_recalls_nothing():
    tid = threads.new_thread()["thread_id"]
    r = recall.remember(tid)
    assert r["ok"] and r["count"] == 0

# ── scope: personal vs what would benefit the group ─────────────────────────────────────────

def test_public_artifacts_are_communal():
    assert recall.classify("John 3:16 — reached for in this conversation.", "scripture") == recall.COMMUNAL
    assert recall.classify("H2617 — studied in this conversation.", "word") == recall.COMMUNAL


def test_a_persons_own_words_are_never_communal():
    for text, kind in (("Mom's surgery is the 14th", "note"),
                       ("call Dad Thursday about the 4111 1111 card", "note"),
                       ("my rent is due", "scripture")):          # kind claims scripture, text is personal
        assert recall.classify(text, kind) == recall.PERSONAL, text


def test_classification_is_conservative_when_unsure():
    """What it cannot prove public it calls personal — the safe direction to be wrong in."""
    assert recall.classify("something vague with no reference at all", "scripture") == recall.PERSONAL
    assert recall.classify("", "scripture") == recall.PERSONAL


def test_scope_is_rechecked_from_the_text_not_the_label():
    """A card claiming to be communal is re-verified from its own content."""
    card = {"text": "my private note", "kind": "scripture", "scope": recall.COMMUNAL}
    assert recall.is_communal(card) is False


# ── we search once, then we land ────────────────────────────────────────────────────────────

def test_nothing_held_yet_means_search():
    """An artifact nothing has carded yet must fall through to a search."""
    assert recall.land("Habakkuk 2:4")["landed"] is False
    assert recall.land("H9999")["landed"] is False


def test_after_a_card_lands_we_land_on_it_instead_of_searching():
    tid = _thread()
    recall.remember(tid)
    r = recall.land("what about John 3:16 again")
    assert r["landed"] is True
    assert any("John 3:16" in c["text"] for c in r["cards"])
    assert "no search was run" in r["note"]


def test_landing_matches_a_strongs_number_too():
    tid = _thread(); recall.remember(tid)
    assert recall.land("H2617")["landed"] is True


# ── usefulness is earned across DISTINCT conversations ──────────────────────────────────────

def test_a_new_conversation_lands_on_the_existing_card_not_a_copy():
    """One card, many stacks — the second conversation does not mint a duplicate."""
    a = _thread(); recall.remember(a)
    first = [c for c in recall.recalled(a)["kept"] if c["kind"] == "scripture"][0]
    b = _thread(); recall.remember(b)
    second = [c for c in recall.recalled(b)["kept"] if c["kind"] == "scripture"][0]
    assert first["id"] == second["id"]
    assert second["conversations"] >= 2


def test_a_card_is_upgraded_by_being_useful_to_more_conversations():
    """Fresh artifact, so the card genuinely starts at KEPT and earns each step."""
    a = _thread_with("Zephaniah 3:17", "H8055"); recall.remember(a)
    ref = [c for c in recall.recalled(a)["kept"] if "Zephaniah" in c["text"]][0]
    assert ref["tier"] == recall.KEPT and ref["conversations"] == 1
    assert recall.note_use(ref["id"], "conv-2")["tier"] == recall.USEFUL     # 2 conversations
    assert recall.note_use(ref["id"], "conv-3")["tier"] == recall.SHARED     # 3 -> the group


def test_only_communal_cards_can_reach_shared():
    """A personal card can be useful many times over and still never be offered to the group."""
    card = stacks.put_card("Mom's surgery is the 14th", kind="note", source="user",
                           extra={"threads_seen": ["t1", "t2", "t3", "t4"]})
    up = recall.note_use(card["id"], "t5")
    assert up["scope"] == recall.PERSONAL
    assert up["tier"] != recall.SHARED


def test_for_the_group_lists_only_earned_communal_cards():
    a = _thread(); recall.remember(a)
    ref = [c for c in recall.recalled(a)["kept"] if c["kind"] == "scripture"][0]
    for t in ("x1", "x2", "x3"):
        recall.note_use(ref["id"], t)
    g = recall.for_the_group()
    assert g["ok"] and any(c["id"] == ref["id"] for c in g["candidates"])
    assert all("personal" not in c.get("text", "").lower() for c in g["candidates"])
    assert "never auto-published" in g["note"]


def test_nothing_is_published_automatically():
    """for_the_group is a candidate list, not an action."""
    a = _thread(); recall.remember(a)
    before = recall.for_the_group()["count"]
    recall.for_the_group()
    assert recall.for_the_group()["count"] == before

