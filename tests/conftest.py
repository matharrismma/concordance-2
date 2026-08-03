"""Test-wide guards.

The tortoise (find.py) reaches the open web only in production. Tests must NEVER touch the network,
so web-find is disabled here by default. test_find re-enables it per-test with STUBBED providers
(never real HTTP) and restores this default afterward.
"""
import os
from pathlib import Path

os.environ["WEB_FIND_DISABLED"] = "1"

ROOT = Path(__file__).resolve().parent.parent

_REAL_CARDS: dict = {}


def real_cards() -> dict:
    """The REAL keeping, for the few tests whose whole point is to measure it.

    WHY THIS EXISTS. 53 test modules open with

        os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(...))

    which is correct for them — they want a scratch corpus they can write into. But pytest
    imports every module before running anything, the variable is process-wide, and
    corpus.default_corpus() is memoized on first touch. So the FIRST module collected wins for
    the whole run (alphabetically: tests/test_apothecary.py), and every later test that reads
    the singleton sees an EMPTY corpus.

    For most tests that is harmless. For the handful that assert things ABOUT the corpus --
    "nothing is isolated", "everything walks back to the Floor" -- it is fatal in the quietest
    possible way: the assertion iterates zero cards and passes. Measured 2026-08-03, two such
    files were passing vacuously under the gate, and one of them was only passing at all because
    tests/test_floor.py left a five-card fake floor in the singleton behind it.

    So: load the real cards directly, once, with the data directory pointed at the repo's own
    data/ for the duration of the load and put back exactly as found. No test that uses this can
    be made vacuous by what a sibling did to the environment.
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
