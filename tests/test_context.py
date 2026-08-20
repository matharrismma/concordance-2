"""Context floor — the no-op round-trip must stay green forever (build plan, Step 1).

    reattach(*strip(text)) == text, exactly, on a corpus of real messy claims.

If any case here ever fails, the bug is in the handle/mapping substrate, not in any discernment layered
above it — and nothing else in the context loop can be trusted until it is green again. This is the
floor of the context process.
"""
import pytest

from concordance import context

# A corpus of real, messy claims-with-context — the kind of text that actually flows through the loop.
MESSY = [
    "The boiling point of water is 100 C at sea level.",
    "content → context → application: the three-process loop.",              # unicode arrow
    "email me at matt@example.com about SSN 123-45-6789",                     # PII that redact WOULD strip
    "card 4532015112830366 from 10.0.0.1 via https://narrowhighway.com/x",    # card + IP + URL
    "line one\r\nline two\r\nline three",                                     # CRLF (must not be lost)
    "tabs\tand\tspaces   and\n\nnewlines",
    "   leading and trailing whitespace   ",
    "a    b     c",                                                           # runs of spaces
    "",                                                                        # empty
    "   \n\t  ",                                                               # only whitespace
    "🔥 the fire-drill 🔥 keep warm",                                          # emoji
    "⟦0⟧ looks like a handle but is just text ⟦1⟧",                            # adversarial: handle-shaped
    "ἐν ἀρχῇ ἦν ὁ λόγος — In the beginning was the Word",                     # Greek + em dash
    "בְּרֵאשִׁית בָּרָא אֱלֹהִים",                                              # Hebrew (RTL)
    "repeat repeat repeat repeat",                                            # stability: reused handle
    "Mixed 123 numbers, punctuation!!! and (parens) + symbols=%$#@",
    "x" * 5000,                                                                # long single token
    "word " * 1000,                                                            # long repetitive
]


@pytest.mark.parametrize("text", MESSY)
def test_no_op_round_trip_is_byte_identical(text):
    skeleton, holds = context.strip(text)
    assert context.reattach(skeleton, holds) == text        # exact, byte-for-byte
    assert context.round_trips(text) is True


@pytest.mark.parametrize("text", MESSY)
def test_the_spans_tile_the_text_with_no_gaps_or_overlaps(text):
    assert "".join(context.spans(text)) == text


def test_handles_are_stable_same_value_same_handle():
    text = "the cat and the dog and the bird"
    skeleton, holds = context.strip(text)
    # three "the" spans and two " and " spans reuse their handles → fewer holds than skeleton entries
    assert len(holds) < len(skeleton)
    the_handles = [h for h, v in holds.items() if v == "the"]
    assert len(the_handles) == 1                             # exactly one handle for the repeated word
    assert skeleton.count(the_handles[0]) == 3


def test_reattach_is_pure_lookup_a_missing_handle_fails_loudly():
    # A handle absent from holds is a substrate bug — it must raise, never silently vanish.
    with pytest.raises(KeyError):
        context.reattach(["⟦0⟧", "⟦999⟧"], {"⟦0⟧": "hi"})


def test_strip_defends_its_contract_against_non_str():
    with pytest.raises(TypeError):
        context.strip(1234)                                 # not str
    with pytest.raises(TypeError):
        context.spans(None)


def test_holds_never_carry_more_than_the_distinct_spans():
    text = "a b a b a"
    skeleton, holds = context.strip(text)
    assert set(holds.values()) == {"a", " ", "b"}           # exactly the distinct spans
    assert context.reattach(skeleton, holds) == text
