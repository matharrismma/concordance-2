"""The component map, computed live (2026-10-06): the engine as a vacuum-tube computer.

One authority chain (Main → Steward → Conductor → Reflex → Scribe → Witness); every part carries
primitive · plane · layer · status; status is earned (downgraded to reality, never upgraded); the
regulators fire in order and each reading is honest (real or `pending`, never a crash)."""
import os
import tempfile

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-comp-"))

from concordance import components as C                       # noqa: E402


def test_the_authority_chain_is_one_ordered_line_with_the_conductor():
    planes = [p["plane"] for p in C.report()["chain"]]
    assert planes == ["Main", "Steward", "Conductor", "Reflex", "Scribe", "Witness"]
    # the Conductor (Matt: "Motion executive is conductor") sits below Steward and above Reflex
    assert planes.index("Conductor") == planes.index("Steward") + 1 < planes.index("Reflex")


def test_every_part_carries_the_four_tags_and_names_real_code():
    r = C.report()
    assert r["counts"]["components"] >= 12            # the dozen primitives, at least
    for c in r["components"]:
        assert c["primitive"] and c["plane"] and c["layer"] and c["status"]
        assert c["status"] in C.STATUS_LADDER
    # grounded: every component resolves its modules on this node (no metaphor-only rows)
    assert r["counts"]["wired"] == r["counts"]["components"], \
        [c["name"] for c in r["components"] if not c["wired"]]


def test_status_is_downgraded_to_reality_never_upgraded():
    # a part whose module cannot import is Concept here, whatever it declares
    assert C._status_live("Production-ready", wired=False) == "Concept"
    assert C._status_live("Verified", wired=True) == "Verified"


def test_regulators_fire_in_order_and_every_reading_is_honest():
    regs = C.report()["regulators"]
    names = {g["slug"] for g in regs}
    assert {"crisis", "pd", "alignment", "diode", "gauges", "kernel", "balance", "gate"} <= names
    # crisis fires first; the fire order is monotonic
    idx = [C._FIRE_ORDER.index(g["fires_at"]) for g in regs]
    assert idx == sorted(idx) and regs[0]["slug"] == "crisis"
    for g in regs:
        assert isinstance(g["reading"], dict)        # a reading is real or {pending:true} — never a raise
        assert g["fallback"]                         # every regulator closes against a fallback


def test_crisis_and_kernel_read_live_not_pending():
    regs = {g["slug"]: g for g in C.report()["regulators"]}
    assert regs["crisis"]["reading"].get("resources", 0) >= 1        # real resources, wired
    assert regs["kernel"]["reading"].get("five_moves", 0) >= 1       # the doctrine is live
