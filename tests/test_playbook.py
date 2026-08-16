"""THE PLAYBOOK — the writable testimony Entry, "Canon commands, Playbook remembers."

The atomic fractal unit made a real object: Confession (required humility key) + Anchors + Action +
Outcome/fruit + Witnesses + Wait + Status. Confirmation is the KERNEL's four gates — an Entry is
community (born quarantined) and reaches CONFIRMED only when ≥2 INDEPENDENT brothers affirm and the
wait elapses (never self-confirm). Pure: `_decide` takes events directly; no corpus, no signatures.
"""
from concordance import playbook


def _entry(**kw):
    base = {"id": "pbk_x_1", "author": "AUTHOR", "created_at": 1000, "wait_seconds": 100,
            "situation": "pruned a ministry that bore no fruit", "confession": "I may be wrong."}
    base.update(kw)
    return base


def _wit(w, affirms=True, eid="pbk_x_1"):
    return {"type": "witness", "entry_id": eid, "witness": w, "affirms": affirms}


# ── the confession is the required humility key ───────────────────────────────────────────────────
def test_confession_and_an_anchor_are_required():
    assert not playbook.signable_entry("KEY", "", ["Jn15:2"], "PRUNE")["ok"]        # no confession
    assert not playbook.signable_entry("KEY", "I may be wrong.", [], "PRUNE")["ok"]  # no anchor
    assert not playbook.signable_entry("KEY", "I may be wrong.", ["Jn15:2"], "SPIN")["ok"]  # bad action
    good = playbook.signable_entry("KEY", "I may be wrong. Acted per Jn15:2.", ["Jn15:2"], "prune")
    assert good["ok"] and good["signable"]["action"] == "PRUNE"                     # normalized


# ── the four gates are the kernel's, routed through _decide ───────────────────────────────────────
def test_born_quarantine_no_witnesses_no_wait():
    st = playbook._decide(_entry(), [], now=1000)
    assert st["status"] == "quarantine" and st["witness_count"] == 0 and not st["waited"]


def test_two_independent_brothers_and_the_wait_confirm_it():
    st = playbook._decide(_entry(), [_wit("BRO_1"), _wit("BRO_2")], now=2000)   # now > created+wait
    assert st["status"] == "confirmed" and st["witnessed"] and st["waited"]
    assert st["gate_record"]["verdict"] == "CONFIRMED"


def test_one_witness_is_not_enough():
    st = playbook._decide(_entry(), [_wit("BRO_1")], now=2000)
    assert st["status"] == "quarantine" and st["witness_count"] == 1


def test_the_author_cannot_witness_their_own_testimony():
    # AUTHOR affirming self + one real brother = still only ONE independent witness → not confirmed
    st = playbook._decide(_entry(), [_wit("AUTHOR"), _wit("BRO_1")], now=2000)
    assert st["witness_count"] == 1 and st["status"] == "quarantine"


def test_a_dissent_cancels_an_affirmation():
    st = playbook._decide(_entry(), [_wit("BRO_1"), _wit("BRO_2", affirms=False), _wit("BRO_3")], now=2000)
    assert st["witness_count"] == 2 and "BRO_2" in st["dissenters"] and st["status"] == "confirmed"


def test_wait_must_elapse_even_with_witnesses():
    st = playbook._decide(_entry(wait_seconds=100000), [_wit("BRO_1"), _wit("BRO_2")], now=1050)
    assert not st["waited"] and st["status"] == "quarantine" and st["wait_remaining_s"] > 0


# ── outcome (the fruit) + pruning (John 15:2) ─────────────────────────────────────────────────────
def test_outcome_is_folded_and_a_failed_fruit_can_be_pruned():
    events = [{"type": "outcome", "entry_id": "pbk_x_1", "outcome": "failed", "note": "no fruit"},
              {"type": "prune", "entry_id": "pbk_x_1", "reason": "bore no fruit (Jn15:2)"}]
    st = playbook._decide(_entry(), events, now=2000)
    assert st["outcome"]["outcome"] == "failed" and st["pruned"] and st["status"] == "pruned"


def test_a_confirmed_testimony_is_never_scripture():
    # the doctrine boundary is carried on the read view, not asserted as truth
    st = playbook._decide(_entry(), [_wit("BRO_1"), _wit("BRO_2")], now=2000)
    assert st["gate_record"]["kind"] == "community"     # community testimony, not canon
