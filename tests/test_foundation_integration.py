"""The Cornerstone, verified WHOLE against the live moat (the sealed clause).

Slow: 'the good and acceptable and perfect' runs the real verifier and mints a re-checkable seal, so it
lives apart from the instant foundation suite. This is the founding verse as a passing test, end to end.
"""
from concordance import foundation


def test_the_engine_does_the_whole_verse_seal_and_all():
    a = foundation.attest(deep=True)
    assert a["whole"] is True, a["note"]
    for c in a["clauses"]:
        assert c["obeyed"], (c["clause"], c["detail"])
    good = next(c for c in a["clauses"] if "good" in c["clause"])
    assert "/s/" in good["detail"]                    # the good is proven with a live, re-checkable seal
