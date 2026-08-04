"""A pytest plugin that records, per test, HOW MANY CARDS IT ACTUALLY SAW.

    PYTHONPATH=src python -m pytest -q -p tools.vacuity_plugin

WHY THIS EXISTS. On 2026-08-03 two tests were found passing while proving nothing: they asserted
things about the keeping ("nothing is isolated", "everything walks back to the Floor") while the
corpus they read held zero cards, because 53 test modules point CONCORDANCE_DATA_DIR at a scratch
temp directory and the first one collected wins the whole process. An assertion that iterates an
empty collection passes. It looks identical to a real guarantee from the outside, and the gate
reported it as green for months.

GREP CANNOT FIND THE REST. A test reaches corpus content through many doors -- default_corpus,
get_card, search, graph.overview, and any helper that calls one of those two layers down. Reading
165 files for that would be guesswork with a confident tone. So this measures instead: it wraps
the doors, and for every test records whether the test walked through one and how many cards were
on the other side.

WHAT IT REPORTS, and what it deliberately does NOT conclude:
  * SAW-NOTHING -- the test read the corpus and the corpus was empty. That is a CANDIDATE, not a
    verdict. Some tests legitimately read an empty corpus in order to write into it
    (test_science_cards mints a card and then looks for it); for those, empty is the point.
  * SAW-CARDS   -- read the corpus and found content. Not at risk.
  * (silent)    -- never touched the corpus. Nothing to say about it.

Deciding which SAW-NOTHING tests are actually vacuous needs a human reading the assertion, and
this tool is careful not to pretend otherwise. Its job is to make the candidate list COMPLETE and
COUNTABLE so the reading is bounded, instead of a sweep of 165 files that "found nothing".
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_CURRENT = None                      # nodeid of the test being executed
_OBS: dict = {}                      # nodeid -> {"doors": set, "cards": int}
# Default OUTSIDE the repo: the first draft defaulted to ROOT, which meant every gate run dropped
# an untracked report file into the working tree — an instrument dirtying the thing it measures.
import tempfile  # noqa: E402
_OUT = os.environ.get("VACUITY_OUT") or os.path.join(tempfile.gettempdir(), "nh-vacuity-report.json")


def _note(door: str, n_cards: int) -> None:
    if _CURRENT is None:
        return                       # import-time / collection-time touches are not a test's fault
    rec = _OBS.setdefault(_CURRENT, {"doors": set(), "cards": -1})
    rec["doors"].add(door)
    # the LARGEST corpus the test ever saw: a test that starts empty and loads real cards later
    # is not vacuous, and taking the max is the reading that cannot slander it
    rec["cards"] = max(rec["cards"], n_cards)


def _corpus_size() -> int:
    try:
        from concordance import corpus
        c = corpus._DEFAULT
        return len(getattr(c, "cards", {}) or {}) if c is not None else 0
    except Exception:                # noqa: BLE001 — instrumentation must never break a test
        return -1


def pytest_configure(config):
    """Wrap the doors. Module-attribute patching, because that is how the tests call them."""
    config.addinivalue_line(
        "markers",
        'empty_corpus_ok(reason): this test reads an empty corpus ON PURPOSE (e.g. it mints into '
        'one). Requires a reason; the vacuity gate rejects a bare marker.')
    from concordance import corpus

    for name in ("default_corpus", "get_card", "search", "load_cards"):
        orig = getattr(corpus, name, None)
        if orig is None:
            continue

        def make(fn, label):
            def wrapper(*a, **k):
                out = fn(*a, **k)
                if label == "default_corpus":
                    _note(label, len(getattr(out, "cards", {}) or {}))
                elif label == "load_cards":
                    # what it RETURNED, not the singleton. conftest.real_cards() loads the real
                    # keeping into a local dict without ever touching the singleton, and scoring
                    # that by singleton size would report the honest path as the vacuous one.
                    _note(label, len(out or {}))
                else:
                    _note(label, _corpus_size())
                return out
            return wrapper

        setattr(corpus, name, make(orig, name))

    try:
        from concordance import graph
        for name in ("overview", "constellation"):
            orig = getattr(graph, name, None)
            if orig is None:
                continue

            def gmake(fn, label):
                def wrapper(*a, **k):
                    out = fn(*a, **k)
                    _note("graph." + label, _corpus_size())
                    return out
                return wrapper

            setattr(graph, name, gmake(orig, name))
    except Exception:                # noqa: BLE001
        pass


def pytest_runtest_protocol(item, nextitem):
    global _CURRENT
    _CURRENT = item.nodeid
    # Read the exemption off the test itself. A marker carrying no reason is NOT an exemption:
    # "@empty_corpus_ok" alone would let the next silent pass through on someone's say-so, and
    # the reason is the only part a later reader can weigh.
    mark = item.get_closest_marker("empty_corpus_ok")
    if mark is not None:
        reason = (mark.args[0] if mark.args else "").strip()
        rec = _OBS.setdefault(item.nodeid, {"doors": set(), "cards": -1})
        rec["exempt"] = bool(reason)
        rec["exempt_reason"] = reason or "(NO REASON GIVEN — not accepted as an exemption)"
    return None                      # let pytest run it normally


def pytest_runtest_logreport(report):
    if report.when == "call" and report.nodeid in _OBS:
        _OBS[report.nodeid]["outcome"] = report.outcome


def pytest_sessionfinish(session, exitstatus):
    """Report, and — when asked to enforce — FAIL the session on an unexplained vacuous pass.

    ENFORCEMENT IS OPT-IN VIA VACUITY_ENFORCE=1 so the plugin stays usable as a plain instrument.
    tools/check.py sets it, which is what turns this from a thing someone remembers to run into a
    property the gate holds.

    THE EXEMPTION IS A MARKER WITH A REASON, NOT A LIST IN THIS FILE:

        @pytest.mark.empty_corpus_ok("mints a card and then looks for it")

    A test that legitimately reads an empty corpus says so at the point of the fact, in one line,
    and the reason travels with the test instead of rotting in a registry somewhere else. A bare
    marker with no reason is refused — an exemption nobody had to justify is how the next silent
    pass gets in.
    """
    global _CURRENT
    _CURRENT = None
    rows = []
    for nodeid, rec in sorted(_OBS.items()):
        rows.append({"nodeid": nodeid, "doors": sorted(rec["doors"]),
                     "cards_seen": rec["cards"], "outcome": rec.get("outcome", "?"),
                     "exempt": rec.get("exempt"), "exempt_reason": rec.get("exempt_reason")})
    saw_nothing = [r for r in rows if r["cards_seen"] <= 0 and r["outcome"] == "passed"]
    violations = [r for r in saw_nothing if not r["exempt"]]
    exempted = [r for r in saw_nothing if r["exempt"]]

    with open(_OUT, "w", encoding="utf-8") as fh:
        json.dump({"tests_touching_the_corpus": len(rows),
                   "saw_nothing_and_passed": len(saw_nothing),
                   "exempted": len(exempted), "violations": len(violations),
                   "rows": rows}, fh, indent=2)

    enforce = os.environ.get("VACUITY_ENFORCE") == "1"
    print("\n" + "=" * 78)
    print(f"VACUITY AUDIT — {len(rows)} test(s) read the corpus at all")
    print(f"  passed while the corpus they read held ZERO cards : {len(saw_nothing)}")
    print(f"    ...declared @pytest.mark.empty_corpus_ok        : {len(exempted)}")
    print(f"    ...UNEXPLAINED                                   : {len(violations)}")
    print("=" * 78)
    for r in exempted:
        print(f"  ok  {r['nodeid'].split('::')[-1][:58]:58s} — {r['exempt_reason']}")
    for r in violations:
        print(f"  !!  {r['nodeid']}")
        print(f"        doors: {', '.join(r['doors'])}")
        print( "        It asserted against a corpus it never populated. Either give it a real")
        print( "        corpus (conftest's real_corpus / real_cards) or declare why empty is")
        print( "        correct: @pytest.mark.empty_corpus_ok(\"...reason...\")")
    print(f"\nfull report -> {_OUT}")

    if enforce and violations:
        print(f"\nVACUITY GATE FAIL: {len(violations)} test(s) passed without measuring anything.")
        session.exitstatus = 1
    elif enforce:
        print("\nVACUITY GATE PASS: every test that read the corpus either saw cards or said why not.")
