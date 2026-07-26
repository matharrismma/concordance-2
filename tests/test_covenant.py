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
