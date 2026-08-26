"""THE PLAYBOOK — the writable testimony Entry, "Canon commands, Playbook remembers."

The atomic fractal unit made a real object: Confession (required humility key) + Anchors + Action +
Outcome/fruit + Witnesses + Wait + Status. Confirmation is the KERNEL's four gates — an Entry is
community (born quarantined) and reaches CONFIRMED only when ≥2 INDEPENDENT brothers affirm and the
wait elapses (never self-confirm). Pure: `_decide` takes events directly; no corpus, no signatures.
"""
import pytest

from concordance import playbook, signing


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


# ── the SIGNED WRITE PATH — record / witness / outcome / prune, keys never travel ─────────────────
# The tests above are pure (_decide/signable). These drive the real append-only store with real
# Ed25519 signatures, so the whole "Playbook remembers" half is exercised, not just the decision fold.
@pytest.fixture
def author(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    try:
        return signing.generate_keypair()          # (priv, pub)
    except Exception:  # noqa: BLE001
        pytest.skip("signing unavailable in this build")


def _sign(resp, priv):
    return signing.sign_bytes(resp["bytes"].encode("utf-8"), priv)


def _record(author, wait_seconds=3600):
    priv, pub = author
    s = playbook.signable_entry(pub, "I may be wrong. Acted per Jn 15:2.", ["John 15:2"], "PRUNE",
                                situation="pruned a fruitless ministry", wait_seconds=wait_seconds)
    return playbook.record(s["signable"], _sign(s, priv), display_name="Matt")


def test_signed_entry_records_and_reads_back(author):
    _priv, pub = author
    r = _record(author)
    assert r["ok"] and r["status"] == "quarantine"
    g = playbook.get(r["entry_id"])
    assert g["ok"] and g["entry"]["author"] == pub and g["entry"]["action"] == "PRUNE"
    assert g["entry"]["is_scripture"] is False


def test_two_brothers_witness_over_the_signed_path(author):
    r = _record(author)
    eid = r["entry_id"]
    for _ in range(2):
        wp, wpub = signing.generate_keypair()
        ws = playbook.signable_witness(wpub, eid, affirms=True, note="aligns")
        assert playbook.add_witness(ws["signable"], _sign(ws, wp))["ok"]
    g = playbook.get(eid)["entry"]
    assert g["witness_count"] == 2
    assert g["status"] == "quarantine"      # the 1h wait has not elapsed, so not yet confirmed


def test_author_cannot_witness_over_the_signed_path(author):
    priv, pub = author
    eid = _record(author)["entry_id"]
    ws = playbook.signable_witness(pub, eid, affirms=True)     # the author's own key
    assert not playbook.add_witness(ws["signable"], _sign(ws, priv))["ok"]


def test_outcome_recorded_then_only_the_author_prunes(author):
    priv, pub = author
    eid = _record(author)["entry_id"]
    ou = playbook.signable_outcome(pub, eid, "failed", note="no fruit")
    assert playbook.add_outcome(ou["signable"], _sign(ou, priv))["ok"]
    # a stranger cannot prune another's testimony
    op, opub = signing.generate_keypair()
    pother = playbook.signable_prune(opub, eid, "meddling")
    assert not playbook.prune(pother["signable"], _sign(pother, op))["ok"]
    # the author prunes their own (John 15:2)
    ps = playbook.signable_prune(pub, eid, "bore no fruit")
    assert playbook.prune(ps["signable"], _sign(ps, priv))["ok"]
    g = playbook.get(eid)["entry"]
    assert g["status"] == "pruned" and g["outcome"]["outcome"] == "failed"


def test_verify_guards_refuse_missing_stale_and_a_private_key(author):
    priv, pub = author
    s = playbook.signable_entry(pub, "I may be wrong.", ["Jn 1:1"], "HOLD")
    sig = _sign(s, priv)
    assert not playbook.record(s["signable"], "")["ok"]                       # no signature
    assert not playbook.record({**s["signable"], "private_key": "x"}, sig)["ok"]  # key on the wire
    assert not playbook.record({**s["signable"], "at": 1}, sig)["ok"]         # stale bytes
    assert playbook.add_witness({"witness": pub, "entry_id": "nope"}, "s")["ok"] is False


def test_list_entries_filters_by_author_and_status(author):
    _priv, pub = author
    _record(author)
    assert playbook.list_entries()["count"] >= 1
    assert playbook.list_entries(author=pub)["count"] >= 1
    assert playbook.list_entries(author="a-stranger")["count"] == 0
    assert playbook.list_entries(status="confirmed")["count"] == 0   # nothing waited out yet


def test_signable_event_validation():
    assert not playbook.signable_witness("", "e")["ok"]
    assert not playbook.signable_outcome("KEY", "e", "not-an-outcome")["ok"]
    assert not playbook.signable_prune("", "e")["ok"]
    assert playbook.get("no-such-entry")["ok"] is False
