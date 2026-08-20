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


# ── Step 2a — the PII discriminator over the floor substrate (round-trip still closes; no leak) ─────
from concordance import redact  # noqa: E402


@pytest.mark.parametrize("text", MESSY)
def test_decontextualize_still_reattaches_the_input_exactly(text):
    # The floor invariant must survive the PII layer: the local holds reattach to EXACTLY the input.
    assert context.decontextualize(text).reattach() == text


@pytest.mark.parametrize("text", MESSY)
def test_nothing_private_travels(text):
    # The de-identified skeleton that may reach the verifier carries no PII.
    s = context.decontextualize(text)
    assert context.leaks(s.travels()) is False


@pytest.mark.parametrize("text", MESSY)
def test_the_traveling_skeleton_equals_the_redactor_output(text):
    # Proof the substrate is UNIFIED, not a second reattach path: projecting PII spans over the floor
    # reproduces redact()'s clean text exactly, placeholder numbering and all.
    assert context.decontextualize(text).travels() == redact.redact(text)[0]


def test_the_email_is_held_home_and_the_checkable_claim_travels():
    claim = "my mother in Dayton wrote matt@example.com - is 100 C the boiling point of water"
    s = context.decontextualize(claim)
    travels = s.travels()
    assert "matt@example.com" not in travels and "[EMAIL_1]" in travels   # private held
    assert "100 C the boiling point of water" in travels                  # checkable claim travels
    assert s.reattach() == claim                                          # local round-trip exact


def test_a_spaced_card_is_caught_as_one_atom_and_reattaches():
    claim = "charge it to 4532 0151 1283 0366 tomorrow"
    s = context.decontextualize(claim)
    assert "4532 0151 1283 0366" not in s.travels() and "[CARD_1]" in s.travels()
    assert s.reattach() == claim
    assert context.leaks(s.travels()) is False


def test_no_pii_text_travels_unchanged_with_no_labels():
    claim = "is 17 a prime number"
    s = context.decontextualize(claim)
    assert s.travels() == claim and s.labels == {} and s.reattach() == claim


def test_a_repeated_private_value_gets_one_stable_placeholder():
    claim = "mail a@b.com then a@b.com again"
    s = context.decontextualize(claim)
    assert s.travels().count("[EMAIL_1]") == 2 and "[EMAIL_2]" not in s.travels()
    assert s.reattach() == claim


def test_reveal_reattaches_a_verdict_by_putting_private_values_back():
    s = context.decontextualize("verify a@b.com for me")
    verdict = "checked [EMAIL_1]: the address is well-formed"
    assert s.reveal(verdict) == "checked a@b.com: the address is well-formed"


# ── Step 2b — the necessity discriminator: keep only what is needed to check (Matt's rule) ──────────
def test_attribution_is_dropped_and_the_bare_claim_travels():
    # "the fact that it's his/her mom is irrelevant in this context"
    s = context.decontextualize("my mom said water boils at 100C", minimal=True)
    assert s.travels() == "water boils at 100C"
    assert s.reattach() == "my mom said water boils at 100C"      # floor: nothing lost locally


def test_a_truth_bearing_location_is_kept():
    # "If she said it was 100C in Dayton, we'd need to add the location."
    s = context.decontextualize("she said it was 100C in Dayton", minimal=True)
    assert s.travels() == "it was 100C in Dayton"
    assert "Dayton" in s.travels() and "she" not in s.travels()
    assert s.reattach() == "she said it was 100C in Dayton"


@pytest.mark.parametrize("q", [
    "does water boil at 100C",                       # "just does water boil at 100C"
    "is 17 a prime number",
    "water boils at 100C at sea level",              # a condition, not framing — kept
])
def test_a_bare_claim_is_unchanged_by_minimal(q):
    assert context.decontextualize(q, minimal=True).travels() == q


def test_a_passive_or_non_frame_is_not_stripped():
    # "is said to" has no person/pronoun subject before a speech verb — not an attribution frame.
    q = "100C is said to be the boiling point of water"
    assert context.decontextualize(q, minimal=True).travels() == q


def test_pii_inside_the_kept_claim_is_still_placeheld_under_minimal():
    s = context.decontextualize("the doctor said email me at a@b.com", minimal=True)
    assert s.travels() == "email me at [EMAIL_1]"                 # frame dropped, PII placeheld
    assert context.leaks(s.travels()) is False
    assert s.reattach() == "the doctor said email me at a@b.com"


def test_claim_convenience_matches_minimal_travels():
    assert context.claim("she told me that water boils at 100C") == "water boils at 100C"


def test_the_held_context_is_kept_for_the_response_not_discarded():
    # Matt: the framing is held home, "but we would add it back in our response ideally."
    s = context.decontextualize("my mom said water boils at 100C", minimal=True)
    assert "mom" not in s.travels()                              # does NOT reach the verifier
    assert "mom" in s.reattach() and "mom" in s.text            # IS still held, for the response
    # the response side can reveal a verdict AND still has the local framing available to weave back
    assert s.reveal("CONFIRMED: water boils at 100C") == "CONFIRMED: water boils at 100C"


@pytest.mark.parametrize("q", [
    "my mom said water boils at 100C",
    "she said it was 100C in Dayton",
    "according to Dr Smith, the dose is 500mg",
    "does water boil at 100C",
    "email a@b.com — she said the code is 4532015112830366",
])
def test_the_floor_survives_the_discriminator(q):
    assert context.decontextualize(q, minimal=True).reattach() == q   # round-trip still exact
