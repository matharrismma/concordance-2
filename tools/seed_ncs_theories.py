#!/usr/bin/env python3
"""Seed + nest the five spine theories of the Nested Control-Systems Framework.

Matt's "Closest Theories" packet (the Nested Control-Systems Framework) had exactly ONE card in
the keeping — card_k_ncs_validation — while its five spine theories were absent. That is an
under-integrated framework: its own thesis is "theories NEST, not compete," yet the theories
themselves were not on the map. This puts them there, and nests them.

Five secular science seeds (gathered + attributed to the real literature — not authored, not
generated), each a LEVEL of the one causal stack, all nested under the framework keystone, chained
in causal order, and bound to the sealed Works demonstration of the framework's validity rules.
Biblical framing is deliberately withheld here: per the packet's own guardrail, Scripture is an
ethics/design heuristic for this material, never scientific evidence — so these seeds stay secular.

Git-tracked (data/ncs_seeds.jsonl + data/ncs_bridges.jsonl); loaded + applied by corpus.

    PYTHONPATH=src python tools/seed_ncs_theories.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

KEYSTONE = "card_k_ncs_validation"          # the framework keystone (already in keystone_seeds)
DEMO = "card_works_nested_control"          # the sealed Works demonstration of its validity rules


def _seed(cid, level, title, role, cite, bands):
    body = (f"Level {level} of the Nested Control-Systems stack. {role} "
            f"These layers do not compete; they nest — each operates at a different level of one "
            f"causal system, which is why treating them as rivals was a decades-long error. "
            f"Source: {cite}")
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": cite, "url": "", "domain": "biology", "authority_tier": "reference"},
        "shelf": "regulation", "box": "nested control systems",
        "bands": ["nested control systems", "regulation", "control theory", f"level {level}"] + bands,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "subject": title,
    }


SEEDS = [
    _seed("card_ncs_l1_predictive_processing", 1,
          "Predictive Processing / Active Inference",
          "The computational frame: the brain minimizes prediction error and selects policies; "
          "autonomic shifts are action policies, meltdowns a cascading precision-arbitration failure.",
          "Friston (2005), Phil. Trans. R. Soc. B 360:815; Lawson, Rees & Friston (2014), "
          "Front. Hum. Neurosci. 8:302 (aberrant precision account of autism).",
          ["predictive processing", "active inference", "Friston", "prediction error", "precision"]),
    _seed("card_ncs_l2_lc_ne_adaptive_gain", 2,
          "LC-NE Adaptive Gain",
          "Precision & arousal gating: tonic locus-coeruleus / norepinephrine sets baseline arousal, "
          "phasic bursts boost task precision; high-tonic/low-phasic = overload and poor transitions.",
          "Aston-Jones & Cohen (2005), Annu. Rev. Neurosci. 28:403.",
          ["LC-NE", "locus coeruleus", "norepinephrine", "arousal", "adaptive gain", "RAS"]),
    _seed("card_ncs_l3_neurovisceral_integration", 3,
          "Neurovisceral Integration / Central Autonomic Network",
          "The executive-autonomic control loop: the prefrontal-vagal brake governs state switching; "
          "HRV/RSA is a direct efficiency index of that inhibitory loop (low HRV = rigid states).",
          "Thayer & Lane (2000), J. Affect. Disord. 61:201; Thayer & Lane (2009), "
          "Neurosci. Biobehav. Rev. 33:81.",
          ["neurovisceral integration", "central autonomic network", "vagal brake", "HRV", "Thayer"]),
    _seed("card_ncs_l4_autonomic_actuators", 4,
          "Autonomic Nervous System — the actuators",
          "The physical state actuators: sympathetic/parasympathetic branches are the downstream "
          "effectors of hierarchical command, not the primary drivers of dysregulation.",
          "Autonomic physiology (sympathetic/parasympathetic effectors); downstream of L1–L3 control.",
          ["autonomic nervous system", "sympathetic", "parasympathetic", "actuator", "effector"]),
    _seed("card_ncs_l5_allostatic_interoception", 5,
          "Predictive Allostatic Interoception",
          "The dashboard & feedback: the brain predicts bodily energy needs by interoceptive "
          "inference; the gut is a load READOUT, not primary causation — gut dysregulation is failed "
          "anticipatory regulation, not microbial cause.",
          "Barrett & Simmons (2015), Nat. Rev. Neurosci. 16:419; Stephan et al. (2023), "
          "Front. Hum. Neurosci. 16:1032319 (allostatic self-efficacy).",
          ["allostatic", "interoception", "Barrett", "dashboard", "gut", "feedback"]),
]

LEVELS = [s["id"] for s in SEEDS]


def main() -> int:
    edges = []
    seen = set()

    def add(a, b, rel, ev, a_title=""):
        key = (a, b, rel)
        if a == b or key in seen:
            return
        seen.add(key)
        edges.append({"a": a, "b": b, "relationship": rel, "evidence": ev, "a_title": a_title})

    by_id = {s["id"]: s for s in SEEDS}
    # (1) nest every spine theory under the framework keystone — "they nest, they do not compete"
    for s in SEEDS:
        lvl = s["bands"][-1] if False else s["title"]
        add(s["id"], KEYSTONE, "member_of",
            "a spine theory (a level of the one nested control-systems stack)", s["title"])
    # (2) the causal stack, top-down: each level modulates the one below (computational → actuator)
    for i in range(len(LEVELS) - 1):
        add(LEVELS[i], LEVELS[i + 1], "modulates",
            "the next level down in the control stack (higher command → lower effector)",
            by_id[LEVELS[i]]["title"])
    # (3) the dashboard feeds back to the computational frame (interoception → prediction)
    add(LEVELS[4], LEVELS[0], "feeds_back",
        "interoceptive load is fed back as prediction (the loop closes)", by_id[LEVELS[4]]["title"])
    # (4) the sealed Works demonstration demonstrates the framework's validity rules
    add(DEMO, KEYSTONE, "demonstrates",
        "the nested-control validity rules, worked and sealed in The Works", "The nested control-systems rule")

    d = Path("data")
    d.mkdir(parents=True, exist_ok=True)
    (d / "ncs_seeds.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in SEEDS) + "\n", encoding="utf-8")
    (d / "ncs_bridges.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in edges) + "\n", encoding="utf-8")
    print(f"seeded {len(SEEDS)} spine theories + {len(edges)} nesting edges "
          f"(under {KEYSTONE}, chained, bound to {DEMO})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
