"""The Cornerstone — the engine tested against its founding verse, Romans 12:1-2 (dokimazein on itself).

Light clauses run here (fast, forever-green): the sealed clause ('the good') runs the live moat and
lives in tests/test_foundation_integration.py. If any clause here turns false, the engine has stopped
doing what the verse says.
"""
from concordance import foundation


def test_every_light_clause_is_obeyed_now():
    a = foundation.attest(deep=False)
    assert a["reference"] == "Romans 12:1-2"
    for c in a["clauses"]:
        if not c["deep"]:
            assert c["obeyed"], (c["clause"], c["detail"])    # the engine does this clause, verified


def test_the_light_run_is_honest_that_the_seal_is_not_yet_verified():
    # dokimazein on itself: a skipped deep check must NOT be claimed as 'whole'
    a = foundation.attest(deep=False)
    assert a["whole"] is False and "run attest(deep=True)" in a["note"]


def test_each_clause_carries_greek_obedience_and_a_live_check():
    for c in foundation.CLAUSES:
        assert c["greek"] and c["clause"] and c["obeys"] and callable(c["check"])


def test_attest_never_raises_a_failed_check_is_reported_not_hidden():
    a = foundation.attest(deep=False)
    assert isinstance(a["kept"], int) and a["of"] == len(foundation.CLAUSES)
    assert all(isinstance(c["obeyed"], bool) for c in a["clauses"])   # honest booleans, never a crash


def test_the_living_sacrifice_proposes_and_never_confirms_itself():
    a = foundation.attest(deep=False)
    ls = next(c for c in a["clauses"] if "living sacrifice" in c["clause"])
    assert ls["obeyed"] and "gate alone confirms" in ls["detail"]


def test_reasoned_service_reaches_agents_too():
    a = foundation.attest(deep=False)
    rs = next(c for c in a["clauses"] if "reasoned service" in c["clause"])
    assert rs["obeyed"] and "serve agents" in rs["detail"]      # served to all, including bots
