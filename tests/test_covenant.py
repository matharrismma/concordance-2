"""Covenant identity — the four verses you stand on, derived to a keypair. Must be deterministic
across devices/spellings, order-independent, and prove possession without revealing the verses."""
import pytest

from concordance import covenant as cov

ME = ["Romans 12:1-2", "Matthew 7:7", "John 1:1", "Psalm 72"]


def test_canonical_is_spelling_and_separator_independent():
    assert cov.canonical("Romans 12:1-2") == cov.canonical("rom 12.1-2") == "45 12:1-2"
    assert cov.canonical("Psalm 72") == cov.canonical("Ps 72") == cov.canonical("psalms 72") == "19 72"
    assert cov.canonical("1 John 4:1") == cov.canonical("1jn 4:1") == "62 4:1"
    with pytest.raises(ValueError):
        cov.canonical("Hesperides 3:4")   # not a book of the 66


def test_same_verses_any_order_or_spelling_same_identity():
    a = cov.public_id(ME)
    b = cov.public_id(["Ps 72", "jn 1:1", "matt 7:7", "rom 12.1-2"])   # another device
    assert a == b and len(a) == 64


def test_one_verse_different_is_a_different_identity():
    assert cov.public_id(ME) != cov.public_id(["Romans 12:1-2", "Matthew 7:7", "John 1:1", "Psalm 73"])


def test_canonical_never_raises_beyond_valueerror_on_bad_types():
    # a non-string ref (a malformed client body field) must fail the SAME documented contract
    # (ValueError), never a raw TypeError — found: "123 or ''" is truthy, so it reached re.match(123)
    for bad in (123, ["John 1:1"], {}, 4.5):
        with pytest.raises(ValueError):
            cov.canonical(bad)


def test_verify_never_raises_on_malformed_or_wrong_type_fields():
    # a security boundary function must FAIL CLOSED (return False), never crash — found:
    # bytes.fromhex(None/int) raises TypeError, which the original except (InvalidSignature,
    # ValueError) did not catch.
    pub = cov.public_id(ME)
    sig = cov.sign(ME, "hello")
    for bad_pub, bad_msg, bad_sig in (
        (None, "hello", sig), (123, "hello", sig),
        (pub, "hello", None), (pub, "hello", 123),
        ("not hex", "hello", sig),
    ):
        assert cov.verify(bad_pub, bad_msg, bad_sig) is False
    # the real, valid case still verifies true
    assert cov.verify(pub, "hello", sig) is True


def test_challenge_response_proves_possession():
    pub = cov.public_id(ME)
    sig = cov.sign(ME, "nh-challenge-xyz")
    assert cov.verify(pub, "nh-challenge-xyz", sig) is True
    assert cov.verify(pub, "a different challenge", sig) is False     # can't replay on another challenge
    assert cov.verify(pub, "nh-challenge-xyz", "00" * 64) is False    # a forged signature fails


def test_passphrase_changes_the_identity():
    assert cov.public_id(ME) != cov.public_id(ME, passphrase="a secret word only I know")


def test_fewer_than_four_is_refused():
    with pytest.raises(ValueError):
        cov.public_id(["John 1:1", "Romans 12:1-2", "Matthew 7:7"])
    with pytest.raises(ValueError):
        cov.public_id(["John 1:1", "John 1:1", "John 1:1", "John 1:1"])   # dupes don't count


def test_strength_advises_without_changing_the_key():
    """The strength advisory is purely additive: it never touches the derivation (same verses ->
    same key), and it nudges toward diversity + a passphrase — the levers a user actually controls
    under the frozen 4-verse design."""
    diverse = ["Romans 12:1-2", "Matthew 7:7", "John 1:1", "Psalm 72:1"]   # four books
    before = cov.public_id(diverse)
    s = cov.strength(diverse)
    assert cov.public_id(diverse) == before, "strength() must not perturb the derivation"
    assert s["level"] == "strong" and s["distinct_books"] == 4 and s["ok"] is True
    # all four from one book is weak — the book ordinal adds ~no entropy
    weak = ["Psalm 1:1", "Psalm 23:1", "Psalm 72:1", "Psalm 119:11"]
    w = cov.strength(weak)
    assert w["level"] == "weak" and w["distinct_books"] == 1
    # ...but a passphrase lifts even a single-book set out of "weak"
    assert cov.strength(weak, passphrase="a word only I know")["level"] == "strong"
    # too few, or unrecognizable, is reported — never raised
    assert cov.strength(["John 1:1"])["ok"] is False
    assert cov.strength(["not a verse", "also not"])["level"] == "invalid"
