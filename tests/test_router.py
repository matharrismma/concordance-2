"""The Router — the one who knows whom to call.

Guards the two non-negotiables: crisis outranks everything, and a genuine tie asks rather
than guesses. Plus the property that makes the whole body cheap: routing is deterministic,
so the same input always names the same member, with no model in the path.
"""
from concordance import router


# --- 1. Crisis outranks everything, always -------------------------------------------------

def test_crisis_is_routed_to_real_people():
    r = router.route("i want to kill myself")
    assert r["member"] == "crisis"


def test_crisis_outranks_every_other_signal():
    """A crisis message that also carries a verse ref, a Strong's number and an equation
    must still route to crisis. Safety is not a tiebreak."""
    for noisy in (
        "John 3:16 but i want to die",
        "H1234 i want to die",
        "2+2=4 and i want to end my life",
        "teach me phonics, also i want to hurt myself",
    ):
        assert router.route(noisy)["member"] == "crisis", noisy


# --- 2. Structured signals ------------------------------------------------------------------

def test_strongs_goes_to_word_study():
    assert router.route("what does H2617 mean")["member"] == "word_study"


def test_reference_goes_to_scripture():
    assert router.route("read John 3:16")["member"] == "scripture"


def test_equation_goes_to_verify():
    assert router.route("0.1 + 0.2 = 0.3")["member"] == "verify"


def test_structured_outranks_keywords():
    """A verse reference is a stronger signal than a domain keyword."""
    assert router.route("commentary on Romans 8:28")["member"] == "scripture"


# --- 3. Domain keywords ---------------------------------------------------------------------

def test_money_goes_to_steward():
    assert router.route("when is my rent bill due")["member"] == "steward"


def test_teaching_goes_to_coach():
    assert router.route("what is her next phonics lesson")["member"] == "coach"


# --- 4. Ambiguity asks, it does not guess ---------------------------------------------------

def test_tie_asks_the_person():
    """Two different members at the same priority must produce a question, not a coin flip."""
    r = router.route("the budget for her homework curriculum and the invoice")
    assert r["member"] == "ask_user"
    assert set(r["alternatives"]) == {"coach", "steward"}


def test_empty_input_asks():
    assert router.route("")["member"] == "ask_user"
    assert router.route("   ")["member"] == "ask_user"


# --- 5. Fallback ----------------------------------------------------------------------------

def test_unknown_falls_back_to_the_keeping():
    assert router.route("tell me about cohesion")["member"] == "search"


# --- 6. The Router never answers, and always explains itself --------------------------------

def test_router_never_answers():
    for t in ("", "John 3:16", "my rent bill", "i want to die", "tell me about bees"):
        assert router.route(t)["answered_here"] is False, t


def test_every_decision_explains_itself():
    for t in ("John 3:16", "my rent bill", "H2617", "tell me about bees"):
        assert router.route(t)["why"], t


def test_routing_is_deterministic():
    """No model in the path: the same input names the same member every time."""
    for t in ("John 3:16", "my rent bill due", "0.1 + 0.2 = 0.3", "who was Barnabas"):
        first = router.route(t)["member"]
        assert all(router.route(t)["member"] == first for _ in range(5)), t


def test_members_are_all_real():
    """Every member the Router can name must be a module that actually exists."""
    import importlib
    known = set(router.members())
    assert {"crisis", "search", "ask_user"} <= known
    for mod in ("steward", "coach", "teachings", "almanac", "characters", "prophecy", "xrefs"):
        importlib.import_module(f"concordance.{mod}")
