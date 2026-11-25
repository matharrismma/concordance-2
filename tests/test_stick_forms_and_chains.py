"""SYSTEMS ARE FRACTALS ON PLANES (Matt, 2026-11-25: "Don't make them artificial but look for cross links and down
chain. Go back to the idea that systems are fractals on planes. Different planes will have the same fractal." then
"Build both").

  FORMS  - src/concordance/stick_forms.json: the same form (a ratio read as its logarithm, a bounded thing ringing at its
           modes, change in proportion to amount, ...) on different planes. A stick is a member only where a verbatim
           piece of its OWN sealed or cited mark carries the form; the graph checks it against the ledger and a note
           never counts.
  CHAINS - the lineage the chain map records (a work builds on a work), drawn as itself; a stick joins it where its own
           card builds on or cites a work, or its cited text names the work's author and year.
  TOPIC  - src/concordance/stick_link_kinds.json: links that share only a topic, drawn faint, never a cross-link.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from concordance import stick_graph as G, tickstick as TS

ROOT = Path(__file__).resolve().parent.parent
FORMS = json.loads((ROOT / "src" / "concordance" / "stick_forms.json").read_text(encoding="utf-8"))["forms"]
KINDS = json.loads((ROOT / "src" / "concordance" / "stick_link_kinds.json").read_text(encoding="utf-8"))


def _golden_claims():
    out = {}
    for f in (ROOT / "tests" / "fixtures" / "tick_golden").glob("*.json"):
        for sid, s in (json.loads(f.read_text(encoding="utf-8")).get("sticks") or {}).items():
            out.setdefault(sid, []).extend((t.get("kind"), t.get("claim") or "") for t in s.get("ticks") or [])
    return out


def test_every_form_member_is_proved_by_its_own_sealed_or_cited_mark():
    claims = _golden_claims()
    ids = [f["id"] for f in FORMS]
    assert len(ids) == len(set(ids)) == 13
    for f in FORMS:
        assert f["title"] and f["law"] and len(f["members"]) >= 3, f["id"]
        for m in f["members"]:
            ok = any(m["evidence"] in c for k, c in claims.get(m["stick"], []) if k != "note")
            assert ok, (f["id"], m["stick"], m["evidence"])


def test_the_topic_pairs_name_real_sticks_and_say_why():
    claims = _golden_claims()
    box_only = {"stick_the_fine_tuned_constants_intelligent_design_and_engineering",
                "stick_matrices_are_graphs_tensors_are_tensor_networks_the_score_is"}
    assert len(KINDS["topic"]) == 9
    for pr in KINDS["topic"]:
        assert pr["a"] in claims or pr["a"] in box_only, pr
        assert pr["b"] in claims or pr["b"] in box_only, pr
        assert pr["why"]


def _keeping():
    keep = Path(tempfile.mkdtemp(prefix="nh-forms-"))
    h = "0" * 64
    rec = {"schema_version": "2.0", "overall": "PASS", "verdict": "HOLDS", "n": 1}
    from concordance import cas
    h = cas.content_hash_of(rec)
    p = cas._record_path(keep / "cas", h)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, sort_keys=True), encoding="utf-8")
    a = TS.create("A sealed member", data_dir=keep)["id"]
    b = TS.create("A member only in a note", data_dir=keep)["id"]
    c = TS.create("A stick that cites Shannon", data_dir=keep)["id"]
    d = TS.create("A neighbour by topic only", data_dir=keep)["id"]
    assert TS.tick(a, "witness", "the decibel: 20 log10(20) = 26.0 dB here", seal=h, data_dir=keep)["ok"]
    TS.tick(b, "note", "the decibel: 20 log10(20) = 26.0 dB here", data_dir=keep)
    assert TS.tick(c, "equivalence", "entropy is the measure of a message", source="C. E. Shannon (1948), Bell System Tech. J.", data_dir=keep)["ok"]
    TS.tick(d, "note", f"next to {a}", data_dir=keep)
    cards = [{"id": "card_floor_logarithm", "title": "Logarithm", "connections": []},
             {"id": "card_chain_boltzmann_1877", "title": "Boltzmann 1877 - entropy", "connections": []},
             {"id": "card_chain_shannon_1948", "title": "Shannon 1948 - A mathematical theory of communication", "connections": []}]
    bridges = [{"a": "card_chain_boltzmann_1877", "b": "card_floor_logarithm", "relationship": "part_of"},
               {"a": "card_chain_shannon_1948", "b": "card_chain_boltzmann_1877", "relationship": "builds_on"},
               {"a": "card_floor_logarithm", "b": "card_k_floor_of_discovery", "relationship": "part_of"}]
    (keep / "chain_cards.jsonl").write_text("\n".join(json.dumps(x) for x in cards) + "\n", encoding="utf-8")
    (keep / "chain_bridges.jsonl").write_text("\n".join(json.dumps(x) for x in bridges) + "\n", encoding="utf-8")
    return keep, a, b, c, d


def test_a_form_member_must_be_sealed_or_cited_never_a_note(monkeypatch):
    keep, a, b, c, d = _keeping()
    table = [{"id": "log_ratio", "title": "A ratio read as its logarithm", "law": "level = k log(ratio)",
              "members": [{"stick": a, "evidence": "20 log10(20) = 26.0 dB"}, {"stick": b, "evidence": "20 log10(20) = 26.0 dB"}]}]
    monkeypatch.setattr(G, "_tables", lambda: (table, {frozenset((d, a))}))
    g = G.graph(keep)
    form_links = {(l["source"], l["target"]) for l in g["links"] if l["kind"] == "form"}
    assert form_links == {(a, "form:log_ratio")}                       # the sealed mark proves it
    assert g["unverified_forms"] == [{"form": "log_ratio", "stick": b}]  # the note does not
    assert g["counts"]["forms"] == 1 and g["counts"]["unverified_forms"] == 1


def test_a_topic_link_is_kept_faint_and_never_a_cross_link(monkeypatch):
    keep, a, b, c, d = _keeping()
    monkeypatch.setattr(G, "_tables", lambda: ([], {frozenset((d, a))}))
    g = G.graph(keep)
    kinds = {frozenset((l["source"], l["target"])): l["kind"] for l in g["links"]}
    assert kinds[frozenset((d, a))] == "topic"
    cross = {x for l in g["links"] if l["kind"] not in ("nested", "topic") for x in (l["source"], l["target"])}
    assert d not in cross


def test_a_cited_work_joins_its_chain_and_the_chain_runs_down_from_its_floor(monkeypatch):
    keep, a, b, c, d = _keeping()
    monkeypatch.setattr(G, "_tables", lambda: ([], set()))
    g = G.graph(keep)
    e = {frozenset((l["source"], l["target"])): l["kind"] for l in g["links"]}
    assert e[frozenset((c, "card_chain_shannon_1948"))] == "chain"                          # the stick cites the work
    assert e[frozenset(("card_chain_shannon_1948", "card_chain_boltzmann_1877"))] == "chain"  # Shannon builds on Boltzmann
    assert e[frozenset(("card_chain_boltzmann_1877", "card_floor_logarithm"))] == "nested"    # the root sits under its floor
    kinds = {n["id"]: n["kind"] for n in g["nodes"]}
    assert kinds["card_chain_shannon_1948"] == "chain" and kinds["card_chain_boltzmann_1877"] == "chain"
    assert g["counts"]["chain_works"] == 2 and g["counts"]["sticks_on_a_chain"] == 1


def test_the_map_draws_forms_and_chains():
    html = (ROOT / "site" / "map.html").read_text(encoding="utf-8")
    js = (ROOT / "site" / "graph.js").read_text(encoding="utf-8")
    assert "fractals on planes" in html and 'n.kind==="form"' in html and "c.chain_works" in html
    assert 'form: "#e07b9a"' in js and 'chain: "#6fa8dc"' in js and 'topic: "#3e4552"' in js
