"""The domain resolver — the verify member's next hop: a plain claim -> a CONFIRM-menu of fine
verify domains, deterministic and model-free. Pins the routing for a handful of everyday questions
(a regression guard, not the full benchmark Matt owns), and the three invariants: crisis is never
routed to a domain, a no-vocabulary request declines cleanly, and every suggestion explains itself.
"""
from concordance.domain_resolver import resolve_domain


def _menu(q):
    return [c["domain"] for c in resolve_domain(q, k=5)["candidates"]]


def test_everyday_questions_reach_the_right_domain_menu():
    checks = [
        ("can my 20 amp circuit handle a 1500 watt heater", "electrical"),
        ("convert 350 fahrenheit to celsius for my bread", "units"),
        ("what are the odds of rolling two sixes", "probability"),
        ("is 17 a prime number", "number_theory"),
        ("how many 2x4 studs for a 16 foot wall on center", "construction"),
        ("name the notes in a c major chord", "music_theory"),
        ("what's the monthly payment on a 30 year home loan", "real_estate"),
        ("how much nitrogen does an acre of corn need", "agriculture"),
    ]
    for q, dom in checks:
        assert dom in _menu(q), (q, _menu(q))


def test_crisis_is_never_routed_to_a_domain():
    r = resolve_domain("i want to end my life")
    assert r["crisis"] is True and r["candidates"] == []


def test_no_vocabulary_match_declines_cleanly():
    r = resolve_domain("tell me a story about a quiet morning")
    # no verifier vocabulary -> no false route: either no candidates, or it asks rather than names one
    assert r["candidates"] == [] or r["ask"] is True


def test_every_suggestion_explains_itself_and_is_deterministic():
    r1 = resolve_domain("what are the odds of rolling two sixes")
    assert r1["candidates"] and all(c["why"] for c in r1["candidates"])
    r2 = resolve_domain("what are the odds of rolling two sixes")
    assert [c["domain"] for c in r1["candidates"]] == [c["domain"] for c in r2["candidates"]]


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("domain-resolver tests passed.")
