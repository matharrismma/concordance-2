"""THE LIVE CARD COUNT (run 2026-11-15-live-card-count, step count-add-card) — a live add leaves the corpus as a
fresh load of the same files holds it, safely for readers, and keeps the substance memo equal to a recount.

Before this step Corpus.add_card replaced or inserted the dict but never touched _public_sorted or the call
tree, appended to buckets and postings out of the load's order, grew in place the dicts request threads iterate,
and left the memoized substance split as it was at the first walk: so no in-process addition moved card_count(),
browse, stats() or /capabilities until a restart (measured at 119dcc3, run ledger line 3).

Every pin here runs over a scratch keeping (CONCORDANCE_DATA_DIR and CONCORDANCE_CORPUS_CACHE_DIR in a temporary
directory), deterministically, with no thread and no sleep. "Equals a fresh load" is read for exactly the list
the plan names: card_count(), _public_sorted, every bucket, every _call_tree count, _n, each added card's dict and
its tokens' postings, and the substance split. The fresh load reads the same files with each added card's line
appended to an extra card source, built the way default_corpus builds (load_cards, then Corpus)."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from concordance import corpus, find, ops  # noqa: E402

BODY = "the river runs over the stone and the rope holds fast through the long night " * 2   # >= 120 chars
SEED = "2026-11-15"


def _card(cid: str, title: str, shelf: str, body: str = BODY, **kw) -> dict:
    c = {"id": cid, "kind": "note", "title": title, "shelf": shelf, "surface": "secular", "body": body}
    c.update(kw)
    return c


def _rows(p: Path, rows) -> None:
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _seed(d: Path, extra=()) -> None:
    """The keeping. Shelf `alpha` has no box, so each title gets its own call `alpha.<letter>.<pair>.<slug>`:
    'Tied' (c_t3) and 'tied' (c_t1) share the call alpha.t.ti.tied, so one call holds two titles whose id order
    (c_t1 first) is not their title order ('Tied' first); c_m is written before c_a, so the cards dict's order is
    not the id order either. c_z rides an extra card source; c_held is withheld (public_review)."""
    _rows(d / "cards.jsonl", [_card("c_m", "Mid", "alpha"), _card("c_a", "Alpha", "alpha"),
                              _card("c_t3", "Tied", "alpha"), _card("c_t1", "tied", "alpha"),
                              _card("c_held", "Held", "alpha", lifecycle_stage="public_review"), *extra])
    _rows(d / "reference_cards.jsonl", [_card("c_z", "Zeta", "omega")])


@pytest.fixture
def keeping(tmp_path, monkeypatch):
    d = tmp_path / "keeping"
    d.mkdir()
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(d))
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE_DIR", str(tmp_path / "cache"))
    for k in ("CONCORDANCE_CARDS_JSONL", "CONCORDANCE_PROPHECY_DIR", "CONCORDANCE_FREEZE_SHELVES",
              "CONCORDANCE_CORPUS_SHARDS", "CONCORDANCE_CORPUS_DB", "CONCORDANCE_CAS_DIR"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(corpus, "_DEFAULT", None)
    monkeypatch.setattr(ops, "_SUBSTANCE_CACHE", None)
    monkeypatch.setattr(ops, "_SUBSTANCE_PENDING", None, raising=False)
    return d


def _boot(monkeypatch, restored: bool) -> corpus.Corpus:
    """The default corpus, built — or restored from the corpus cache, a hit asserted."""
    if restored:
        monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "1")
        corpus._DEFAULT = None
        corpus.default_corpus()
        assert corpus.LOAD_PHASES["corpus_cache"] == "miss" and corpus.LOAD_PHASES["corpus_cache_saved"] is True
        corpus._DEFAULT = None
    else:
        monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", "0")
    cp = corpus.default_corpus()
    assert corpus.LOAD_PHASES["corpus_cache"] == ("hit" if restored else "off"), corpus.LOAD_PHASES
    return cp


def _fresh_load(monkeypatch, src: Path, appended=()) -> corpus.Corpus:
    """A corpus loaded from a copy of the keeping's files with each added card's line appended to an extra card
    source, the way default_corpus builds one."""
    d = src.parent / "fresh"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(src, d)
    if appended:
        with open(d / "acquired_cards.jsonl", "a", encoding="utf-8") as fh:
            for c in appended:
                fh.write(json.dumps(c) + "\n")
    with monkeypatch.context() as m:
        m.setenv("CONCORDANCE_DATA_DIR", str(d))
        df: dict = {}
        fz: dict = {}
        fe: dict = {}
        cards = corpus.load_cards(_df_out=df, _frozen_out=fz, _bridges_out=fe)
        return corpus.Corpus(cards, df_extra=df, frozen_idx=fz, frozen_edges=fe)


def _tree_counts(tree: dict, path: tuple = ()) -> dict:
    out = {}
    for seg, e in tree.items():
        p = path + (seg,)
        out[p] = e["n"]
        out.update(_tree_counts(e["kids"], p))
    return out


def _assert_equals_fresh(live: corpus.Corpus, fresh: corpus.Corpus, added_ids) -> None:
    assert corpus.card_count() == len(fresh._public_sorted)
    assert live._public_sorted == fresh._public_sorted
    assert {k: list(v) for k, v in live._cids_by_call.items()} == {k: list(v) for k, v in fresh._cids_by_call.items()}
    assert _tree_counts(live._call_tree) == _tree_counts(fresh._call_tree)
    assert live._n == fresh._n
    for cid in added_ids:
        assert live.cards[cid] == fresh.cards[cid], cid
        for t in set(corpus._tokens(corpus._card_text(live.cards[cid]))):
            assert live._by_token.get(t) == fresh._by_token.get(t), (cid, t)
    assert {t: list(v) for t, v in live._by_token.items()} == {t: list(v) for t, v in fresh._by_token.items()}
    assert ops.substance_if_cached() == ops.substance(fresh.cards)


# ── (1) an add equals a fresh load ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("restored", [False, True], ids=["built", "restored"])
def test_an_add_equals_a_fresh_load(keeping, monkeypatch, restored):
    _seed(keeping)
    cp = _boot(monkeypatch, restored)
    ops.substance_of_the_keeping()                                  # the memo exists before the adds
    assert cp._public_sorted == ["c_a", "c_m", "c_t3", "c_t1", "c_z"]
    assert cp._cids_by_call["alpha.t.ti.tied"] == ["c_t1", "c_t3"]  # id order is not the title order
    count = corpus.card_count()
    # c_t2 ties c_t3 on (call, title) and breaks the tie by sorting first: strictly inside _public_sorted, inside
    # its bucket [c_t1, c_t3] and inside the postings of 'tied' and of every common body word
    t2 = _card("c_t2", "Tied", "alpha")
    lines = [json.loads(json.dumps(t2))]                            # each added card's line, as written
    corpus.add_to_default(t2)
    assert corpus.card_count() == count + 1
    assert cp._public_sorted == ["c_a", "c_m", "c_t2", "c_t3", "c_t1", "c_z"]
    assert cp._cids_by_call["alpha.t.ti.tied"] == ["c_t1", "c_t2", "c_t3"]
    assert cp._by_token["tied"] == ["c_t1", "c_t2", "c_t3"] and cp._by_token["river"].index("c_t2") == 3
    # a batch: a public card on a new call (a new segment under alpha) and a withheld one, held as a load holds it
    beta = _card("c_beta", "Beta", "alpha")
    priv = _card("c_priv", "Private draft", "alpha", lifecycle_stage="private")
    lines += [json.loads(json.dumps(beta)), json.loads(json.dumps(priv))]
    assert cp.add_cards([beta, priv]) == 2
    assert corpus.card_count() == count + 2 and "c_priv" in cp.cards and "c_priv" not in cp._public_sorted
    fresh = _fresh_load(monkeypatch, keeping, lines)
    _assert_equals_fresh(cp, fresh, ["c_t2", "c_beta", "c_priv"])
    # a listed card replaced under another call and title keeps its old place (until a restart, by name), and
    # every later new card still gets its own place: still public, and turned withheld
    _displaced_case(monkeypatch, keeping.parent / "displaced_public", restored, withheld=False)
    _displaced_case(monkeypatch, keeping.parent / "displaced_withheld", restored, withheld=True)


def _displaced_case(monkeypatch, d: Path, restored: bool, withheld: bool) -> None:
    """15 public cards B00, B02 ... B28 on one shelf; c_b14 sits at the first place bisect probes. It is re-added
    under title Z99 (a new call and title; still public, or withheld), so it keeps the place it was placed with.
    Then B25, B21, B13 and B15 are added, each search reaching it: _public_sorted must be the fresh load's order
    with c_b14 back at its old place, which needs the replaced card compared under the key it was placed with."""
    d.mkdir()
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(d))
    monkeypatch.setattr(ops, "_SUBSTANCE_CACHE", None)
    _rows(d / "cards.jsonl", [_card("c_" + t.lower(), t, "alpha") for t in ("B%02d" % i for i in range(0, 30, 2))])
    corpus._DEFAULT = None                       # a fresh default corpus over this keeping
    cp = _boot(monkeypatch, restored)
    x = cp._public_sorted[len(cp._public_sorted) // 2]
    assert x == "c_b14"
    placed = (cp._call_of(x), cp._title_of(x), x)
    repl = _card(x, "Z99", "alpha", **({"lifecycle_stage": "private"} if withheld else {}))
    lines = [json.loads(json.dumps(repl))]
    corpus.add_to_default(repl)
    new = [_card("c_n" + t[1:], t, "alpha") for t in ("B25", "B21", "B13", "B15")]
    lines += [json.loads(json.dumps(c)) for c in new]
    for c in new:
        corpus.add_to_default(c)
    fresh = _fresh_load(monkeypatch, d, lines)
    others = [c for c in fresh._public_sorted if c != x]
    order = sorted(others + [x], key=lambda c: placed if c == x else (fresh._call_of(c), fresh._title_of(c), c))
    assert cp._public_sorted == order, (withheld, [cp._title_of(c) for c in cp._public_sorted])
    assert corpus.card_count() == len(fresh._public_sorted) + (1 if withheld else 0)
    for c in new:
        assert cp._cids_by_call[c["call"]] == fresh._cids_by_call[c["call"]]


# ── (2) a second add of the same id ─────────────────────────────────────────────────────────────────────────────

def test_a_second_add_of_the_same_id_still_equals_a_fresh_load(keeping, monkeypatch):
    _seed(keeping)
    cp = _boot(monkeypatch, False)
    ops.substance_of_the_keeping()
    line = _card("c_t2", "Tied", "alpha")
    corpus.add_to_default(json.loads(json.dumps(line)))
    count = corpus.card_count()
    corpus.add_to_default(json.loads(json.dumps(line)))               # the same id again, a fresh dict
    assert corpus.card_count() == count
    fresh = _fresh_load(monkeypatch, keeping, [line, line])
    _assert_equals_fresh(cp, fresh, ["c_t2"])


# ── (3) a held card released live (find._promote_to_public, the path find._set_stage takes) ────────────────────

def test_a_held_card_released_live_equals_a_fresh_load_of_the_rewritten_file(keeping, monkeypatch):
    _seed(keeping)
    store = keeping / "web_cache.jsonl"
    _rows(store, [_card("c_acq", "Acquired", "alpha", lifecycle_stage="public_review"),
                  _card("c_kept", "Kept", "alpha")])
    cp = _boot(monkeypatch, False)
    ops.substance_of_the_keeping()
    assert corpus.get_card("c_acq") is None and "c_acq" in cp.cards
    count = corpus.card_count()
    assert find._promote_to_public(store, "c_acq") is True
    got = corpus.get_card("c_acq")
    assert got is not None and got["lifecycle_stage"] == "public"
    assert corpus.card_count() == count + 1
    fresh = _fresh_load(monkeypatch, keeping)                         # the same files, the store rewritten
    assert fresh.cards["c_acq"]["lifecycle_stage"] == "public"
    _assert_equals_fresh(cp, fresh, ["c_acq"])


# ── (4) readers stay safe ───────────────────────────────────────────────────────────────────────────────────────

class _AddsOnTouch(list):
    """A bucket or posting list that makes one live add each time a walk touches it (its length or its items,
    as `on` names), while `cards` last: the add lands INSIDE that walk, between its first and second step,
    deterministically and with no thread. `touches` counts the walks that reached it, `adds` the adds made."""

    def __init__(self, items, cards, on=("len", "iter")):
        super().__init__(items)
        self.cards, self.on, self.touches, self.adds = list(cards), on, 0, 0

    def _touch(self, how):
        if how in self.on:
            self.touches += 1
            if self.adds < len(self.cards):
                self.adds += 1
                corpus.add_to_default(self.cards[self.adds - 1])

    def __len__(self):
        self._touch("len")
        return super().__len__()

    def __iter__(self):
        self._touch("iter")
        return super().__iter__()

    def __sizeof__(self):                            # sys.getsizeof reads a list through this
        self._touch("sizeof")
        return super().__sizeof__()

    def plain(self) -> list:
        return list.copy(self)                       # no touch


def test_readers_iterating_the_dicts_finish_with_the_old_contents_across_an_add_on_a_new_call(keeping, monkeypatch):
    """The dicts an add copies and swaps (the cards for a new id, a _call_tree level for a new segment): an iterator
    advanced once finishes on the old contents. The dict an add grows in place (_cids_by_call): an add bringing a
    new token and a new call lands inside cids_for_call's walk, which restarts and returns every id it held before
    plus at most the new one; with an add inside each of four walks in a row it ends in the snapshot walk."""
    _seed(keeping)
    cp = _boot(monkeypatch, False)
    cards_before = list(cp.cards.values())
    tree_before = list(cp._call_tree)
    it_cards = iter(cp.cards.values())
    it_tree = iter(cp._call_tree.items())
    first_card, first_seg = next(it_cards), next(it_tree)
    new = _card("c_new", "Novel", "zshelf")              # call zshelf.n.no.novel: a new call, a new first segment
    assert "zshelf" not in cp._call_tree and not any(k.startswith("zshelf") for k in cp._cids_by_call)
    count = corpus.card_count()
    corpus.add_to_default(new)
    rest_cards, rest_tree = list(it_cards), list(it_tree)                   # no RuntimeError
    assert [first_card] + rest_cards == cards_before
    assert [first_seg[0]] + [k for k, _ in rest_tree] == tree_before
    assert corpus.card_count() == count + 1 and corpus.get_card("c_new") is not None
    assert cp._call_tree["zshelf"]["n"] == 1 and cp._cids_by_call["zshelf.n.no.novel"] == ["c_new"]

    first_call = next(iter(cp._cids_by_call))
    assert first_call.startswith("alpha.") and len(cp._cids_by_call) > 1    # the walk has a step after the hook
    # one add inside the walk: a new token ('quokka') and a new call (alpha.q.qu.quokka)
    before = cp.cids_for_call("alpha")
    hook = _AddsOnTouch(cp._cids_by_call[first_call], [_card("c_quokka", "Quokka", "alpha", body="quokka")],
                        on=("iter",))
    cp._cids_by_call[first_call] = hook
    got = cp.cids_for_call("alpha")                                          # no RuntimeError
    cp._cids_by_call[first_call] = hook.plain()
    assert hook.adds == 1 and "alpha.q.qu.quokka" in cp._cids_by_call and "quokka" in cp._by_token
    assert set(before) <= set(got) and set(got) - set(before) <= {"c_quokka"} and len(got) <= len(before) + 1
    # an add inside each of four walks in a row: four direct walks, each restarted, then the snapshot walk
    before = cp.cids_for_call("alpha")
    four = [_card("c_w%d" % i, "Wombat %d" % i, "alpha", body="wombat%s" % "abcd"[i]) for i in range(4)]
    hook = _AddsOnTouch(cp._cids_by_call[first_call], four, on=("iter",))
    cp._cids_by_call[first_call] = hook
    got = cp.cids_for_call("alpha")
    assert hook.adds == 4 and hook.touches == 5
    cp._cids_by_call[first_call] = hook.plain()
    assert got == cp.cids_for_call("alpha")                     # the same result a walk no add lands in gives
    assert set(got) == set(before) | {c["id"] for c in four}
    # the bound, seen: an add inside the fifth walk too raises nothing there, and that walk holds only the calls
    # its snapshot of the keys held (taken after the fourth add) — so it was the snapshot, not a fifth direct walk
    before = cp.cids_for_call("alpha")
    six = [_card("c_k%d" % i, "Kiwi %d" % i, "alpha", body="kiwi%s" % "abcdef"[i]) for i in range(6)]
    hook = _AddsOnTouch(cp._cids_by_call[first_call], six, on=("iter",))
    cp._cids_by_call[first_call] = hook
    got = cp.cids_for_call("alpha")
    cp._cids_by_call[first_call] = hook.plain()
    assert hook.adds == 5 and hook.touches == 5
    assert set(got) == set(before) | {c["id"] for c in six[:4]}
    assert set(cp.cids_for_call("alpha")) == set(before) | {c["id"] for c in six[:5]}


def test_the_loops_over_the_token_index_survive_a_new_token_between_their_steps(keeping, monkeypatch):
    """Each walk over _by_token outside __init__ (footprint's two, _index_card_ids, gauges) with an add bringing a
    new token and a new call landing inside it: no RuntimeError; and with an add inside each of four walks in a
    row, the snapshot walk ends it with the result a walk no add lands in gives. Footprint's second walk (its
    sampled key and list sizes) reads each list through sys.getsizeof, so its hook counts __sizeof__."""
    _seed(keeping)
    cp = _boot(monkeypatch, False)
    def footprint_index():               # footprint's two walks over the index (it reads the cards before them)
        f = cp.footprint()
        return f["tokens"], f["postings"]

    loops = (("footprint", footprint_index, "quokkaplume"),
             ("_index_card_ids", cp._index_card_ids, "zyxomantic"),
             ("gauges", corpus.gauges, "brindlewort"))
    for name, run, word in loops:
        first = next(iter(cp._by_token))
        assert len(cp._by_token) > 1 and word not in cp._by_token
        hook = _AddsOnTouch(cp._by_token[first], [_card("c_" + word, word.title(), "alpha", body=word)])
        cp._by_token[first] = hook                              # each walk's first step touches the hook
        run()                                                   # no RuntimeError: the walk restarted
        cp._by_token[first] = hook.plain()
        assert hook.adds == 1 and cp._by_token[word] == ["c_" + word], name
        assert ("alpha.%s.%s.%s" % (word[0], word[:2], word)) in cp._cids_by_call, name
        four = [_card("c_%s%d" % (word, i), word.title(), "beta", body="%s%s" % (word, "abcd"[i])) for i in range(4)]
        hook = _AddsOnTouch(cp._by_token[first], four)
        cp._by_token[first] = hook
        got = run()
        assert hook.adds == 4 and hook.touches == 5, name       # four direct walks, then the snapshot walk
        cp._by_token[first] = hook.plain()
        assert got == run(), name
        assert all((word + "abcd"[i]) in cp._by_token for i in range(4)), name

    first = next(iter(cp._by_token))

    def sizes():                         # footprint's second walk over the index: the sampled key and list sizes
        dict_size = sys.getsizeof(cp._by_token)          # what footprint reads before its two walks
        f = cp.footprint()
        return f["bytes"]["token_index"] - f["postings"] * 8 - dict_size

    hook = _AddsOnTouch(cp._by_token[first], [_card("c_sizeofword", "Sizeofword", "alpha", body="sizeofword")],
                        on=("sizeof",))
    cp._by_token[first] = hook
    got = sizes()                                               # no RuntimeError: the second walk restarted
    assert hook.adds == 1 and hook.touches == 2, "footprint's second walk"
    assert cp._by_token["sizeofword"] == ["c_sizeofword"] and "alpha.s.si.sizeofword" in cp._cids_by_call
    assert got == sizes()
    cp._by_token[first] = hook.plain()
    four = [_card("c_sz" + ch, "Sizeword " + ch, "alpha", body="sizeword" + ch) for ch in "abcd"]
    hook = _AddsOnTouch(cp._by_token[first], four, on=("sizeof",))
    cp._by_token[first] = hook
    got = sizes()
    assert hook.adds == 4 and hook.touches == 5, "footprint's second walk"   # four direct walks, then the snapshot
    assert got == sizes()
    cp._by_token[first] = hook.plain()
    assert all(("sizeword" + ch) in cp._by_token and ("alpha.s.si.sizeword_" + ch) in cp._cids_by_call for ch in "abcd")


# ── (5) the substance memo ──────────────────────────────────────────────────────────────────────────────────────

def test_the_substance_memo_equals_a_recount_after_adds(keeping, monkeypatch):
    _seed(keeping)
    cp = _boot(monkeypatch, False)
    memo0 = ops.substance_of_the_keeping()
    assert memo0 == ops.substance(cp.cards)
    corpus.add_to_default(_card("c_sub", "Substance", "alpha"))                     # new: substance
    corpus.add_to_default(_card("c_stub", "Stub", "alpha", body="a pointer"))       # new: a stub
    corpus.add_to_default(_card("c_m", "Mid", "alpha", body="now a pointer"))       # replaced: its old share out
    corpus.add_to_default({"id": "e_1", "kind": "connection", "title": "an edge", "shelf": "alpha"})   # excluded
    corpus.add_to_default(_card("c_wh", "Withheld", "alpha", lifecycle_stage="private"))   # withheld, resident
    assert ops.substance_if_cached() == ops.substance(corpus.default_corpus().cards)
    assert ops.substance_if_cached()["total"] == memo0["total"] + 3
    cp.add_cards([_card("c_b1", "Batch one", "alpha"), _card("c_b2", "Batch two", "alpha", body="short")])
    assert ops.substance_if_cached() == ops.substance(corpus.default_corpus().cards)


def test_an_add_during_the_substance_walk_is_not_lost(keeping, monkeypatch):
    _seed(keeping)
    _boot(monkeypatch, False)
    real = ops.substance

    def walk(cards):
        corpus.add_to_default(_card("c_early", "Early", "alpha", body="a pointer"))   # after the snapshot
        corpus.add_to_default(_card("c_m", "Mid", "alpha", body="now a pointer"))    # a replaced dict, mid-walk
        s = real(cards)
        corpus.add_to_default(_card("c_late", "Late", "alpha"))                       # after the count, before the memo
        return s

    monkeypatch.setattr(ops, "substance", walk)
    got = ops.substance_of_the_keeping()
    monkeypatch.setattr(ops, "substance", real)
    assert {"c_early", "c_late"} <= set(corpus.default_corpus().cards)
    assert got == real(corpus.default_corpus().cards)
    assert ops.substance_if_cached() == got


# ── (6) the frozen index ────────────────────────────────────────────────────────────────────────────────────────

def test_an_id_in_the_frozen_index_is_skipped(keeping, monkeypatch):
    _seed(keeping, extra=[_card("f_1", "Frozen one", "frozenshelf")])
    monkeypatch.setattr(corpus, "frozen_shelves", lambda: frozenset({"frozenshelf"}))
    cp = _boot(monkeypatch, False)
    assert "f_1" in cp._frozen and "f_1" not in cp.cards
    ops.substance_of_the_keeping()

    def state():
        return (corpus.card_count(), list(cp._public_sorted), {k: list(v) for k, v in cp._cids_by_call.items()},
                _tree_counts(cp._call_tree), cp._n, {t: list(v) for t, v in cp._by_token.items()},
                dict(cp.cards), ops.substance_if_cached())

    before = state()
    corpus.add_to_default(_card("f_1", "Frozen one", "frozenshelf", body="a live copy of the frozen card " * 5))
    assert "f_1" not in cp.cards
    assert state() == before


# ── (7) the card of the day (a guard: green at the base by design, which never moves the list) ─────────────────

@pytest.mark.parametrize("restored", [False, True], ids=["built", "restored"])
def test_the_card_of_the_day_holds_through_adds(keeping, monkeypatch, restored):
    _seed(keeping)
    cp = _boot(monkeypatch, restored)
    loaded = list(cp._public_sorted)
    h = int(hashlib.sha256(SEED.encode("utf-8")).hexdigest(), 16)
    expected = loaded[h % len(loaded)]
    assert corpus.daily(SEED)["id"] == expected
    adds = [_card("c_aa%d" % i, "Aardvark %d" % i, "aaa") for i in range(3)]       # each sorts before every card
    # the guard can see a move: over the loaded ids plus these, in the load's order, the seed picks another card
    grown = ["c_aa0", "c_aa1", "c_aa2"] + loaded
    assert grown[h % len(grown)] != expected
    for c in adds:
        corpus.add_to_default(c)
    assert corpus.daily(SEED)["id"] == expected
