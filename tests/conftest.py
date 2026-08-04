"""Test-wide guards.

The tortoise (find.py) reaches the open web only in production. Tests must NEVER touch the network,
so web-find is disabled here by default. test_find re-enables it per-test with STUBBED providers
(never real HTTP) and restores this default afterward.
"""
import os
from pathlib import Path

import pytest

os.environ["WEB_FIND_DISABLED"] = "1"

ROOT = Path(__file__).resolve().parent.parent

_REAL_CARDS: dict = {}
_REAL_CORPUS = None


def real_cards() -> dict:
    """The REAL keeping, for the few tests whose whole point is to measure it.

    WHY THIS EXISTS. 53 test modules open with a line like

        os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(...)

    which is right for them — they want a scratch corpus to write into. But the variable is
    process-wide and corpus.default_corpus() is memoized on first touch, so WHICH corpus the
    singleton ends up holding is settled by a race between module imports and the first read.

    MEASURED 2026-08-03 with tools/vacuity_plugin.py across the whole suite: in a FULL run the
    singleton holds the real keeping. 182 tests called default_corpus() and not one received an
    empty corpus; 155 saw more than 100k cards. The gate is NOT reading an empty library. An
    earlier draft of this docstring asserted that it was, from a subset run — that was wrong, and
    the correction is recorded here rather than quietly deleted.

    The race is real in SUBSET runs, which is how anyone actually develops:

        pytest tests/test_floor.py tests/test_reachable_from_the_floor.py

    collects a hijacking module early, its temp dir wins, and the corpus is empty. A file whose
    whole claim is about the keeping then iterates zero cards and passes. Not hypothetical: it is
    exactly how the missing teardown in tests/test_floor.py stayed invisible. Run alone the
    reachability file passed; run in that pair it failed; which answer you got depended on your
    command line, and neither answer announced which corpus it had measured.

    So the few files whose verdict IS the keeping load the real cards here instead of inheriting
    the race, and assert on the count they got. Their answer must not depend on what else
    happened to be collected.
    """
    global _REAL_CARDS
    if not _REAL_CARDS:
        from concordance import corpus
        prior = os.environ.get("CONCORDANCE_DATA_DIR")
        os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data")
        try:
            _REAL_CARDS = corpus.load_cards()      # no path: also pulls the sibling card sources
        finally:
            if prior is None:
                os.environ.pop("CONCORDANCE_DATA_DIR", None)
            else:
                os.environ["CONCORDANCE_DATA_DIR"] = prior
    return _REAL_CARDS


def real_corpus_object():
    """A Corpus over the real cards, built once, THE SAME WAY default_corpus() builds it.

    The df_extra argument is not optional decoration. load_cards(_df_out=df) streams each frozen
    card's document frequencies during the read so no per-card token list ever materialises, and
    Corpus(cards, df_extra=df) takes them pre-computed. Building `Corpus(cards)` without it makes
    the index the naive way over 548k cards: the first draft of this helper did exactly that and
    three test files had not finished after nine minutes. Measured, then fixed — a check nobody
    can afford to run is a check that gets deleted.
    """
    global _REAL_CORPUS
    if _REAL_CORPUS is None:
        from concordance import corpus
        prior = os.environ.get("CONCORDANCE_DATA_DIR")
        os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data")
        try:
            df: dict = {}
            cards = corpus.load_cards(_df_out=df)
            _REAL_CORPUS = corpus.Corpus(cards, df_extra=df)
            global _REAL_CARDS
            if not _REAL_CARDS:
                _REAL_CARDS = cards            # one read serves both helpers
        finally:
            if prior is None:
                os.environ.pop("CONCORDANCE_DATA_DIR", None)
            else:
                os.environ["CONCORDANCE_DATA_DIR"] = prior
    return _REAL_CORPUS


@pytest.fixture
def real_corpus():
    """Install the REAL keeping as the process corpus for one test, then put back exactly what
    was there.

    For the checks whose whole point is that the library actually answers -- "a how-to question
    reaches the field library", "wayfind stays on topic". Those were written as

        if not corpus.search("survival shelter", limit=1):
            return          # 'positive check guarded on a provisioned corpus'

    which reports a pass without having checked anything. MEASURED 2026-08-03: under the FULL
    gate the corpus is provisioned, so those assertions do run — an earlier claim here that they
    "had never once executed" was wrong and is corrected. What is true is that the guard makes
    them conditional on a race nobody can see: in any subset run the search comes back empty, the
    body is skipped, and the test still reports green.

    Asking for a real corpus outright removes the condition. The check either runs or fails; it
    can no longer half-run and call that success.

    Restores corpus._DEFAULT and graph._GRAPH on the way out, so this fixture cannot become the
    next thing that leaves a global changed behind it.
    """
    from concordance import corpus, graph
    prior_corpus = corpus._DEFAULT
    prior_graph = getattr(graph, "_GRAPH", None)
    corpus._DEFAULT = real_corpus_object()
    graph._GRAPH = None
    try:
        yield corpus._DEFAULT
    finally:
        corpus._DEFAULT = prior_corpus
        graph._GRAPH = prior_graph


@pytest.fixture
def corpus_left_as_found():
    """For tests that REPLACE the corpus singleton with a small fixture of their own.

    Five files assign `corpus._DEFAULT = corpus.Corpus({...})` directly, which is a reasonable way
    to test against a known tiny graph. AUDITED 2026-08-03, and most of them are already correct:

      * test_graph.py, test_privacy.py -- pytest's `teardown_function` hook, which runs after
        every test in the module including on failure. Robust. Left alone.
      * test_corpus_freeze.py, test_wants.py -- restore explicitly. Left alone.
      * test_library.py -- cleans up in a `test_cleanup()` that asserts nothing and relies on
        being defined last. It works today because pytest runs a file in definition order, and it
        breaks silently the day someone appends a test below it.

    A first pass of this audit grepped for `yield|finally|monkeypatch`, saw none of those in
    test_graph/test_privacy, and concluded all three "never put the singleton back". That was
    wrong -- the grep did not know about teardown_function -- and it was written into this
    docstring before being checked. Recorded here because a false accusation in a comment outlives
    the person who made it.

    Ask for this fixture and the restore is automatic, with no ordering assumption.
    """
    from concordance import corpus, graph
    prior_corpus = corpus._DEFAULT
    prior_graph = getattr(graph, "_GRAPH", None)
    try:
        yield
    finally:
        corpus._DEFAULT = prior_corpus
        graph._GRAPH = prior_graph
