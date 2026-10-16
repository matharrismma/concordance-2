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


def test_new_capabilities_reach_their_verify_domain():
    # 2026-10-13 gap fix #2: chirality / Born rule / double slit were front-door invisible
    # (resolve_domain returned None). The cues route them to the domain whose verifier checks them.
    checks = [
        ("the enantiomeric excess of a 99 to 1 mixture of R and S is 98 percent", "chemistry"),
        ("the product's enantiomeric excess exceeds the catalyst's in asymmetric autocatalysis", "chemistry"),
        ("the born rule gives the probability as the amplitude squared", "quantum_computing"),
        ("in a double slit the fringe spacing is 5 mm", "optics"),
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


def test_witness_verifiers_route_only_on_the_witness_surface():
    """Reach sprint (2026-10-16): the three witness verifiers were registered only in WITNESS_VERIFIERS, which
    the resolver never read — a verse question on narrowhighway.org could not reach the scripture verifier.
    They now route from a SEPARATE index on surface="witness" only; the secular face is untouched (the Gate
    opens inward, never outward)."""
    witness_domains = {"scripture", "theology_doctrine", "witness"}
    checks = [
        ("what does john 3:16 say about the world", "scripture"),
        ("read me the passage in psalm 23", "scripture"),
        ("is the trinity a doctrine of the nicene creed", "theology_doctrine"),
        ("the apostles bore witness and gave their testimony of the gospel", "witness"),
    ]
    for q, dom in checks:
        wit = [c["domain"] for c in resolve_domain(q, k=5, surface="witness")["candidates"]]
        assert dom in wit, (q, wit)
        sec = [c["domain"] for c in resolve_domain(q, k=5)["candidates"]]
        assert not (set(sec) & witness_domains), ("a witness verifier routed on the secular face", q, sec)


def test_the_secular_index_is_unchanged_by_the_witness_index():
    # one query, one answer: naming the default surface changes nothing, and the witness index never leaks in
    for q in ("is 17 a prime number", "what are the odds of rolling two sixes", "name the notes in a c major chord"):
        assert resolve_domain(q, k=5) == resolve_domain(q, k=5, surface="secular")


def test_curated_synonyms_are_stored_as_queries_tokenize():
    """Issue #22: _add stored curated _SYNONYMS raw while _phrases tokenizes a query (3+ letter words, at most
    3 of them), so 20 of 550 everyday phrases ("speed of light", "day of the week", "equivalent to") could never
    match — silent dead entries. The build now normalizes them. Pin: every curated term's normalized form is in
    the index, and the formerly dead phrasings route to the domain the curator meant."""
    from concordance import domain_resolver as dr
    dr._build()
    for terms in dr._SYNONYMS.values():
        for term in terms:
            n = " ".join(dr._WORD.findall(term.lower()))
            if n and len(n.split()) <= 3:
                assert n in dr._INDEX, term
    checks = [("what day of the week was july 4 1776", "calendar_time"),
              ("how many ways to choose 3 from 10", "combinatorics"),
              ("the number of divisors of 12 is 6", "number_theory"),
              ("2 to the power of 10 is 1024", "mathematics"),
              ("how much do i make an hour at 50000 a year", "labor"),
              ("the speed of light is 299792458 m/s", "physical_constants")]
    for q, dom in checks:
        assert dom in _menu(q), (q, _menu(q))


def test_the_twenty_nine_domains_with_no_everyday_vocabulary_now_route():
    """Reach (issue #11, 2026-10-16): 29 registered domains had no _SYNONYMS entry — a person's plain words could
    not reach their verifier (13 were unreachable on every axis). Each now has everyday vocabulary, written as
    queries tokenize and avoiding words other domains own. Pin: a representative phrasing DECIDES each domain,
    and three controls still decide as before (no cross-talk regression)."""
    checks = [
        ("what is the determinant of a 3x3 identity matrix", "linear_algebra"),
        ("is methane tetrahedral with 109.5 degree bond angles", "molecular_geometry"),
        ("is 978-0-306-40615-7 a valid isbn", "document_validation"),
        ("carbon dating a sample with 25 percent carbon left", "archaeology"),
        ("the free spectral range of a ring resonator", "photonics"),
        ("the shannon entropy of a fair coin is 1 bit", "information_theory"),
        ("the youngs modulus of steel is 200 gpa", "materials_science"),
        ("which element has atomic number 26", "periodic_table"),
        ("a straw man argument misrepresents the position", "rhetoric"),
        ("diagonalize the matrix and solve in the eigenbasis", "spectral"),
        ("the elo rating expected score for 1600 vs 1400", "sports_analytics"),
        ("a knight on e4 attacks 8 squares in chess", "chess"),
        ("ballpark estimate within 10 percent", "approximation"),
        ("the floor area ratio of the building", "architecture"),
        ("search precision at 10 for the query", "retrieval"),
        ("what is the nash equilibrium of the prisoners dilemma", "game_theory"),
        ("how strong is a 12 character password entropy", "cybersecurity"),
        ("the fermi energy of copper is 7 ev", "condensed_matter"),
        ("is utilitarianism a consequentialist ethical framework", "philosophy"),
        ("grimms law shifts p to f in proto germanic", "sound_law"),
        ("the critical path of this project schedule", "operations_research"),
        ("what is the cpk of a process with these control limits", "manufacturing"),
        ("the action potential resting membrane potential of a neuron", "neuroscience"),
        ("the rational roots of x^3 - 6x^2 + 11x - 6", "polynomial"),
        ("how many solar panels for 10 kwh per day off grid", "energy"),
        ("what is the cell potential of a zinc copper galvanic cell", "electrochemistry"),
        # controls — unchanged routing
        ("is 17 prime", "number_theory"),
        ("what are the odds of rolling two sixes", "probability"),
        ("the molar mass of water is 18", "chemistry"),
    ]
    for q, dom in checks:
        r = resolve_domain(q, k=5)
        assert r["decision"] == dom, (q, r["decision"], [c["domain"] for c in r["candidates"]])


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
        print("  ok ", fn.__name__)
    print("domain-resolver tests passed.")


def test_born_confidence_and_entropy_are_surfaced_and_separate_confident_from_ambiguous():
    """Matt's seed (2026-10-12): the resolver surfaces a Born-rule confidence (amplitude squared,
    normalized) and its entropy (logs). A confident route reads high confidence / low entropy; a tie
    reads low confidence / high entropy. The DECISION is unchanged (the pairwise margin); this is the
    signal exposed for the FIND door and a future measured rework."""
    c = resolve_domain("is 17 prime")
    assert c["decision"] == "number_theory"
    assert c["confidence"] >= 0.70 and c["entropy"] <= 1.0
    # "the speed of light..." USED to be this test's tie — only because the curated synonym "speed of light"
    # was stored raw and could never match (issue #22). Normalized, it decides physical_constants as the
    # curator intended; a real near-tie (three domains with a claim on a watt-hour bill) is the ambiguous case.
    s = resolve_domain("the speed of light is 299792458 m/s")
    assert s["decision"] == "physical_constants" and s["confidence"] >= 0.5
    a = resolve_domain("a 60 watt bulb for 10 hours uses 0.6 kwh")
    assert a["decision"] is None                        # a genuine tie still asks
    assert a["confidence"] <= 0.5 and a["entropy"] >= 1.2
    # every candidate-bearing result carries the three signals
    for field in ("confidence", "entropy", "crosstalk"):
        assert field in c and field in a
