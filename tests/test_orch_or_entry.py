"""THE MEANING TEST of data/sticks/orch_or.json and its chart, tools/seed_orch_or.py (2026-11-27: the receiver chart
read quantum - Penrose and Hameroff's Orch OR).

A golden pins what an entry mints, by content hash, and not what its seals mean. This file holds the entry's nine
sealed expressions to their sources: each constant is stated once below with the source it was read from (public reads
of 2026-11-27: the SI's exact constants; the abstracts of Tegmark 2000, Hagan-Hameroff-Tuszynski 2002 and Hameroff-
Penrose 2014; the Anesthesiology abstract of Li et al. 2018, isotopes read with their superscripts), and each seal's
expr must be exactly its template applied to those constants, its value the expression's own float. Each seal holds
through verify_derivation in the numeric shape while a claim moved by one part in 1e6 does not. The marks are the nine
sealed instances once each, one cited postulate and three notes, and the receiver stick gains ONE note and no sealed
mark (its live probe pins verified_instances at 2). The chart lands on the mind floor beside the receiver chart, and no
field is longer than tickstick keeps, since it cuts a longer one without a word."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
ENTRY = ROOT / "data" / "sticks" / "orch_or.json"
STICK = "stick_orch_or_consciousness_as_quantum_vibrations_in_microtubules"
RECEIVER = "stick_consciousness_as_a_receiver_the_crystal_radio"

# THE CONSTANTS, each stated once, with the source it was read from.
H = "6.62607015e-34"        # the Planck constant in J s, exact (BIPM, the SI Brochure, 9th edition, 2019)
KB = "1.380649e-23"         # the Boltzmann constant in J/K, exact (the same)
E = "1.602176634e-19"       # the elementary charge in C, exact: J per eV (the same)
C = "299792458"             # the speed of light in m/s, exact (the same)
T = "310.15"                # 37 C in kelvin (the kelvin and the degree Celsius differ by 273.15 exactly)
GAMMA_HZ = "40"             # the gamma rhythm Orch OR ties to conscious moments (Hameroff and Penrose 2014)
TAU = "0.025"               # one 40 Hz cycle, 25 ms, the reduction time for one conscious moment
E_G_UNIT = "1e-33"          # the unit E_G is sealed in: 1e-33 joule (see the zero-claim test below for why)
TRP_M = "280e-9"            # tryptophan's ultraviolet absorption band near 280 nm (protein UV spectroscopy)
TEGMARK_S = "1e-13"         # Tegmark's longest decoherence time, microtubule kinks (Phys. Rev. E 61, 4194, 2000)
REPLY_S = "1e-4"            # the reply's recalculated upper figure, 1e-5 to 1e-4 s (Phys. Rev. E 65, 061901, 2002)
ED50 = {"132": "70", "134": "72", "131": "99", "129": "105"}   # calculated LORR ED50 in %, Li et al. 2018

TEMPLATES = {
    "thermal_energy": f"{KB}*{T}/{E}",
    "thermal_frequency": f"{KB}*{T}/{H}/1e12",
    "gamma_quanta": f"{KB}*{T}/({H}*{GAMMA_HZ})",
    "tryptophan_ratio": f"{H}*{C}/({TRP_M}*{KB}*{T})",
    "reduction_energy": f"{H}/(2*pi)/{TAU}/{E_G_UNIT}",
    "tegmark_gap": f"{TAU}/{TEGMARK_S}",
    "recalculated_gap": f"{TAU}/{REPLY_S}",
    "xenon_129": f"{ED50['132']}/{ED50['129']}",
    "xenon_131": f"{ED50['132']}/{ED50['131']}",
}
KEYS = list(TEMPLATES)
# What each claim says the seal is, to the figures it prints: the meaning must match the number.
PRINTED = {"thermal_energy": (0.02673, 5e-6), "thermal_frequency": (6.46, 5e-3), "gamma_quanta": (1.6e11, 5e9),
           "tryptophan_ratio": (166, 0.5), "reduction_energy": (4.2183, 5e-4), "tegmark_gap": (2.5e11, 1),
           "recalculated_gap": (250, 1e-9), "xenon_129": (0.667, 5e-4), "xenon_131": (0.707, 5e-4)}


def entry() -> dict:
    return json.loads(ENTRY.read_text(encoding="utf-8"))


def seals() -> dict:
    return {s["key"]: s for s in entry()["seals"]}


def verdict(seal: dict, claimed: float) -> str:
    """The seal path's own check (sticks.seal_numeric): verify_derivation on the numeric shape."""
    from concordance.derivation import verify_derivation
    return verify_derivation([{"id": seal["nid"], "domain": seal["domain"], "spec": {"mode": "numeric", "params": {
        "numeric_expr": seal["expr"], "claimed_value": claimed, "rel_tol": seal["tol"]}}}])["verdict"]


def test_the_entry_holds_exactly_the_nine_numeric_seals_in_order():
    e = entry()
    assert (e["schema"], e["name"], e["aliases"]) == (1, "orch_or", ["orch_or", "quantum_consciousness"])
    assert list(seals()) == KEYS
    for key, s in seals().items():
        assert set(s) == {"key", "nid", "expr", "value", "tol", "domain"}, key
        assert (s["nid"], s["domain"], s["tol"]) == ("orch_or_" + key, "mathematics", 1e-9), key


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_expr_is_exactly_its_template_applied_to_the_stated_constants(key):
    assert seals()[key]["expr"] == TEMPLATES[key]


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_value_is_its_expressions_own_float(key):
    from concordance.verifiers import mathematics
    s = seals()[key]
    assert s["value"] == float(mathematics._parse(s["expr"], []).evalf())


@pytest.mark.parametrize("key", KEYS)
def test_each_claim_prints_its_seal_to_the_figures_it_shows(key):
    want, within = PRINTED[key]
    assert abs(seals()[key]["value"] - want) <= within, key


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_holds_through_verify_derivation_and_a_claim_moved_by_one_part_in_1e6_does_not(key):
    s = seals()[key]
    assert verdict(s, s["value"]) == "HOLDS"
    assert verdict(s, s["value"] * (1 + 1e-6)) == "BROKEN"


@pytest.mark.parametrize("key", KEYS)
def test_no_seal_here_would_hold_a_claim_of_zero(key):
    """THE WINDOW IS RELATIVE ONLY ABOVE 1. mathematics.verify_numeric compares with
    threshold = rel_tol * max(1.0, abs(computed)), so for a value far below the tolerance the window is ABSOLUTE and
    swallows everything, zero included: E_G = hbar / 0.025 s is 4.2e-33 J, and claiming it is 0 - or a thousand times
    itself - returned HOLDS. That is why E_G is sealed in units of 1e-33 J, where the window is relative again. No
    seal on this stick may be vacuous in that way; a seal whose own value is zero would be, so none here is."""
    s = seals()[key]
    assert s["value"] != 0.0, key
    assert verdict(s, 0.0) == "BROKEN", key
    assert verdict(s, s["value"] * 1000) == "BROKEN", key


def test_the_physics_reads_the_way_the_marks_say():
    """The EEG is classical (h nu far below k_B T), tryptophan's UV is quantum (far above), the crossover sits in the
    terahertz, and both spin-carrying isotopes are weaker than spin-zero xenon while spin-zero 134Xe is not."""
    s = {k: v["value"] for k, v in ((k, seals()[k]) for k in KEYS)}
    assert s["gamma_quanta"] > 1e11 and s["tryptophan_ratio"] > 100
    assert 1 < s["thermal_frequency"] < 10                                  # THz
    assert s["recalculated_gap"] > 1 and s["tegmark_gap"] > 1e11            # both figures short of 25 ms
    assert 1e-2 <= float(TAU) <= 1e-1                                       # inside the reply's shielded 1e-2..1e-1 s
    assert s["xenon_129"] < s["xenon_131"] < 1 and float(ED50["134"]) / float(ED50["132"]) < 1.03


def test_the_marks_are_the_nine_seals_once_each_one_postulate_and_three_notes():
    st = entry()["sticks"]
    assert [x["question"] for x in st] == ["Orch OR - consciousness as quantum vibrations in microtubules",
                                           "Consciousness as a receiver - the crystal radio"]
    marks = st[0]["marks"]
    assert [(m["kind"], m.get("seal")) for m in marks] == ([("instance", k) for k in KEYS] + [("postulate", None)]
                                                           + [("note", None)] * 3)
    assert st[0]["field"] == "biophysics"
    post = marks[len(KEYS)]
    assert "DECLINED" in post["claim"] and "card_question_the_hard_problem" in post["claim"] and RECEIVER in post["claim"]
    assert "Physics of Life Reviews 11 (2014) 39-78" in post["source"]
    assert all(len(m.get("source", "")) >= 8 for m in marks[len(KEYS):])     # every cited mark and note names its source


def test_the_receiver_stick_gains_one_note_and_no_sealed_mark():
    """eval/live_probes.jsonl pins the receiver stick at verified_instances == 2: a sealed mark here would break it."""
    rec = entry()["sticks"][1]
    assert [m["kind"] for m in rec["marks"]] == ["note"]
    assert STICK in rec["marks"][0]["claim"]
    assert not {"statement", "field", "references"} & set(rec)               # create() finds the live stick as it is
    probes = [json.loads(line) for line in (ROOT / "eval" / "live_probes.jsonl").read_text(encoding="utf-8").splitlines()
              if line.strip() and not line.lstrip().startswith("#")]
    by_id = {p["id"]: p for p in probes}
    assert {"at": "fit.verified_instances", "eq": 2} in by_id["consciousness.receiver.crystal.radio.sealed"]["expect"]
    assert {"at": "fit.verified_instances", "eq": len(KEYS)} in by_id["orch.or.stick.sealed.and.declined"]["expect"]
    assert by_id["orch.or.stick.sealed.and.declined"]["query"] == {"id": STICK}
    assert {"at": "charts[*].stick", "has": STICK} in by_id["map.orch.or.on.mind.floor"]["expect"]


def test_the_stick_id_is_stick_orch_or_and_no_other_entry_states_it():
    from concordance import tickstick
    assert "stick_" + tickstick._slug(entry()["sticks"][0]["question"]) == STICK
    assert "stick_" + tickstick._slug(entry()["sticks"][1]["question"]) == RECEIVER
    for path in sorted(ENTRY.parent.glob("*.json")):
        if path != ENTRY:
            other = json.loads(path.read_text(encoding="utf-8"))
            assert all("stick_" + tickstick._slug(st.get("question", "")) != STICK
                       for st in other.get("sticks", [])), path.name


def test_the_aliases_resolve_to_this_entry_and_collide_with_no_other():
    from concordance import sticks
    cat = sticks.load_catalog()
    for alias in entry()["aliases"]:
        assert cat.resolve(alias)["name"] == "orch_or", alias


def test_no_field_is_cut_on_the_way_in():
    """tickstick.create keeps question[:300], statement[:2000], field[:80] and references[:12], each [:300], and tick
    keeps claim[:CLAIM_CAP], source[:300] and by[:80], all without a word: every field here fits, so nothing is cut."""
    from concordance import tickstick
    st, rec = entry()["sticks"]
    assert len(st["question"]) <= 300 and 0 < len(st["statement"]) <= 2000
    assert 0 < len(st["field"]) <= 80 and 0 < len(st["by"]) <= 80 and 0 < len(rec["by"]) <= 80
    assert 0 < len(st["references"]) <= 12 and all(0 < len(r) <= 300 for r in st["references"])
    for m in st["marks"] + rec["marks"]:
        assert 8 <= len(m["claim"].strip()) == len(m["claim"]) <= tickstick.CLAIM_CAP
        assert len(m.get("source", "")) <= 300


def test_the_listing_names_this_entry_by_its_hash_with_every_seal_in_order():
    lines = (ROOT / "tools" / "stick_mints.txt").read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if line.startswith("orch_or "))
    assert lines[i - 1].startswith("# orch_or: ")
    name, sha, *rest = lines[i].split()
    assert sha == hashlib.sha256(ENTRY.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert [kv.split("=")[0] for kv in rest] == KEYS
    golden = json.loads((ROOT / "tests" / "fixtures" / "tick_golden" / "orch_or.json").read_text(encoding="utf-8"))
    by_nid = {v["verifiers"][0]: h for h, v in golden["seals"].items()}
    assert [kv.split("=")[1] for kv in rest] == [by_nid["orch_or_" + k] for k in KEYS]


def test_the_chart_lands_on_the_mind_floor_beside_the_receiver_chart():
    """Pinned on the seeds alone: the chart validates, charts the mind floor, connects to its open end, the receiver
    chart and the quantum floor, and floor_map reads both receivers' sticks among the mind floor's charts."""
    import seed_consciousness_receiver as RECV
    import seed_orch_or as S
    import seed_the_mind as MIND
    from concordance import chains, corpus
    assert S._validate() == []
    rel = {(e["b"], e["relationship"]) for e in S.BRIDGES}
    assert rel == {("card_floor_the_mind", "charts"), ("card_question_the_hard_problem", "connects_at"),
                   ("card_chart_consciousness_receiver", "connects_at"), ("card_floor_quantum_mechanics", "connects_at"),
                   ("card_k_floor_of_discovery", "part_of")}
    card = S.CARDS[0]
    assert card["source"]["ref"] == STICK and card["generated"] is False and card["surface"] == "secular"
    assert "DECLINED" in card["body"]
    cards = {c["id"]: json.loads(json.dumps(c)) for c in MIND.CARDS + RECV.CARDS + S.CARDS}
    for cid in ("card_floor_physical_chemistry", "card_floor_biology", "card_floor_the_instruments",
                "card_floor_thermodynamics", "card_floor_the_capstone", "card_k_floor_of_discovery",
                "card_floor_quantum_mechanics"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-orch-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in MIND.BRIDGES + RECV.BRIDGES + S.BRIDGES) + "\n",
                       encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_the_mind", get_card=cards.get)
    assert m is not None
    assert {STICK, RECEIVER} <= {c["stick"] for c in m["charts"]}
