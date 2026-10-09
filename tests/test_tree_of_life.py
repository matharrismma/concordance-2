"""THE TREE OF LIFE on the one map (Matt, 2026-10-09: "We will cover every domain. Starting with genomics").
Phylogeny is the comparative method for genes - the exact parallel of the Indo-European floor. Pinned on the seed
alone: the floor's parts are the three domains of life, its confluences are the universal genes (where domains meet),
the seed validates and merges idempotently; and the genetic-code checks the genomics stick seals are themselves sound
(0 FP) in the live verifiers."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-tol-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import seed_tree_of_life as TOL  # noqa: E402
from concordance import chains, corpus  # noqa: E402


def _graph():
    cards = {c["id"]: json.loads(json.dumps(c)) for c in TOL.CARDS}
    cards.setdefault("card_k_floor_of_discovery", {"id": "card_k_floor_of_discovery", "title": "Floor", "connections": []})
    ov = Path(TMP) / "o.jsonl"
    ov.write_text("\n".join(json.dumps(e) for e in TOL.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, ov)
    return cards


def test_the_floor_has_domains_as_trees_and_universal_genes_as_confluences():
    assert TOL._validate() == [] and "card_floor_tree_of_life" in chains.FLOORS
    g = _graph()
    m = chains.floor_map("card_floor_tree_of_life", get_card=g.get)
    assert {p["id"] for p in m["parts"]} == {TOL._did(s) for s, _, _ in TOL.DOMAINS}
    conf_at = {c["at"] for c in m["confluences"]}
    assert TOL._gid("ssu_rrna") in conf_at                 # the domains meet at the ribosomal RNA
    merged = {x["id"] for x in m["merges"]}
    assert {TOL._gid("ssu_rrna"), TOL._gid("ef_tu"), TOL._gid("atp_synthase")} <= merged


def test_the_seed_merges_idempotently(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-tol-seed-"))
    monkeypatch.setattr(TOL, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    assert TOL.main() == 0
    before = (d / "chain_cards.jsonl").read_bytes()
    assert TOL.main() == 0 and (d / "chain_cards.jsonl").read_bytes() == before
    assert TOL.FLOOR in {json.loads(l)["id"] for l in before.decode().splitlines() if l.strip()}


def test_the_genetic_code_checks_are_sound():
    # the facts the genomics stick seals are 0-FP in the live verifiers
    from concordance.verifiers import genetics as G, biology as B
    assert G.run({"GENETICS_VERIFY": {"codon": "ATG", "claimed_amino_acid": "M"}})[0].status == "CONFIRMED"
    assert G.run({"GENETICS_VERIFY": {"codon": "ATG", "claimed_amino_acid": "W"}})[0].status == "MISMATCH"   # caught
    assert G.run({"GENETICS_VERIFY": {"sequence": "ATGGCCTAA", "claimed_protein": "MA*"}})[0].status == "CONFIRMED"
    assert G.run({"GENETICS_VERIFY": {"sequence": "ATGGCCTAA", "claimed_protein": "MAK"}})[0].status == "MISMATCH"
    assert B.run({"BIO_VERIFY": {"hardy_weinberg": {"counts": [360, 480, 160]}}})[0].status == "CONFIRMED"
