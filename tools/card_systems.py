#!/usr/bin/env python3
"""The systems of the world — one design cascading over planes. Card the recurring form.

Matt, 2026-07-25: "Create card decks for electronics, hydrodynamics and all of the systems of the
world. There is a fluid aspect in that His design cascades over planes and we see the repetition of
His design. Often corrupted by our sin, but the reason the bad works is because it always is the
shadow or inverse of His way, and even that connection has power."

The classic system analogies are the fingerprint of one design: EFFORT (voltage / pressure / force /
temperature) and FLOW (current / volumetric-flow / velocity / heat-flow) are the same pair in every
domain; the same diffusion, wave, and oscillator equations govern them all. This mints the recurring
form as findable cards — the systems, the isomorphisms, and the shadow/inverse principle (privatio
boni). Conduit: the analogies are established engineering; the theology is historic + Matt's framing.
Git-tracked (authored content). Rooted in the created order → the Floor.

    PYTHONPATH=src python tools/card_systems.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CREATED_ORDER = "card_k_spine_created_order"
SPINE = "card_spine_systems"
MASTER = "card_sys_effort_flow"


def _c(cid, title, body, bands, subject, conns=None):
    return {
        "id": cid, "kind": "reference", "title": title[:180], "body": body,
        "source": {"label": "The recurring form — the system analogies (standard engineering) + the "
                            "design they witness to", "url": "", "domain": "systems", "authority_tier": "reference"},
        "shelf": "systems", "box": "framework",
        "bands": ["systems", "recurring form", "analogy"] + list(bands), "subject": subject,
        "connections": (conns or []) + [{"to_card_id": SPINE, "relationship": "member_of",
                                         "evidence": "a member of the systems of the world"}],
        "author": "Matt Harris (the recurring form)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }


def _mirror(to):
    return {"to_card_id": MASTER, "relationship": "instance_of",
            "evidence": "an instance of the one effort-flow form"} if to != MASTER else None


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The systems of the world — one design, many planes",
        "body": ("Electrical, fluid, thermal, mechanical, control, wave — the systems of the world are "
                 "not many designs but ONE, cascading over planes. The same effort-and-flow pair, the "
                 "same diffusion and wave and oscillator equations, appear in every domain. To learn "
                 "one system is to have learned them all. The repetition is a signature (Romans 1:20)."),
        "source": {"label": "The recurring form", "url": "", "domain": "systems", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["systems", "recurring form", "isomorphism", "fractal", "design", "spine"],
        "subject": "the systems of the world",
        "connections": [{"to_card_id": CREATED_ORDER, "relationship": "part_of",
                         "evidence": "the recurring design, a spine of the created order"}],
        "author": "Matt Harris (the recurring form)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }
    cards = [spine]
    # The master pattern
    cards.append(_c(MASTER, "The effort–flow form — the master pattern",
        "Every physical system runs on a pair: EFFORT (the push) and FLOW (the response). Electrical: "
        "voltage & current. Fluid: pressure & volumetric flow. Mechanical: force & velocity. Thermal: "
        "temperature & heat-flow. Their product is POWER in every domain. Energy is stored two ways — "
        "as potential (capacitance) and as kinetic/flow (inductance/inertance) — and dissipated one way "
        "(resistance). One grammar, spoken on every plane.",
        ["effort", "flow", "voltage", "pressure", "force", "temperature", "power", "impedance"], "the effort-flow form"))
    # The domains (each an instance of the master)
    domains = [
        ("card_sys_electrical", "Electrical & electronic systems", "electronics",
         "Effort = voltage, flow = current. Resistors dissipate (Ohm: I = V/R); capacitors store charge "
         "(potential); inductors store field (flow). Governed by Kirchhoff's laws and Maxwell's equations. "
         "The circuit is the clearest window onto the effort-flow form.",
         ["electronics", "electrical", "circuit", "voltage", "current", "resistor", "capacitor", "inductor", "ohm"]),
        ("card_sys_fluid", "Hydrodynamics & fluid systems", "fluids",
         "Effort = pressure, flow = volumetric flow rate. Fluid resistance (viscous drag), fluid capacitance "
         "(a tank's compliance), inertance (the mass of moving fluid). Governed by Navier-Stokes, and by "
         "Bernoulli along a streamline. A pipe network is a circuit; pressure is voltage; flow is current.",
         ["hydrodynamics", "fluid", "flow", "pressure", "pipe", "hydraulic", "bernoulli", "pump", "viscosity"]),
        ("card_sys_thermal", "Thermal systems", "thermal",
         "Effort = temperature, flow = heat flow. Thermal resistance (Fourier: q = ΔT/R), thermal capacitance "
         "(a body's heat storage); no true thermal inductor (heat has no inertia) — the one place the analogy "
         "bends, and the bending teaches. Governed by the heat equation.",
         ["thermal", "heat", "temperature", "thermodynamics", "conduction", "fourier", "entropy"]),
        ("card_sys_mechanical", "Mechanical systems", "mechanical",
         "Effort = force (or torque), flow = velocity (or angular velocity). The damper dissipates, the spring "
         "stores potential, the mass stores kinetic. Governed by Newton's laws. A mass-spring-damper is an RLC "
         "circuit wearing different clothes — same second-order equation, same resonance.",
         ["mechanical", "force", "torque", "spring", "damper", "mass", "newton", "gear", "motion"]),
        ("card_sys_control", "Control systems", "control",
         "Any system that senses its output and corrects — thermostat, engine governor, autopilot, the body's "
         "homeostasis — is the SAME feedback loop, described by the same transfer functions and the same "
         "stability criteria. Feedback is the universal regulator; the math does not care what is being ruled.",
         ["control", "feedback", "pid", "governor", "regulator", "stability", "transfer function", "homeostasis"]),
        ("card_sys_wave", "Waves & oscillation", "waves",
         "The same wave equation governs sound in air, light in the field, ripples on water, and a plucked "
         "string. The same harmonic oscillator is an LC circuit, a mass on a spring, and a pendulum — resonance "
         "at ω = 1/√(store·store). Vibration is one phenomenon, played on many instruments.",
         ["wave", "oscillation", "frequency", "resonance", "harmonic", "vibration", "acoustics", "pendulum"]),
    ]
    for cid, title, subj, body, bands in domains:
        m = _mirror(cid)
        cards.append(_c(cid, title, body, bands, subj, conns=[m] if m else None))
    # The shared equations
    cards.append(_c("card_sys_diffusion", "The one diffusion equation",
        "Heat spreading, ink dispersing, charge leaking, momentum smearing — all obey ∂u/∂t = D∇²u, the same "
        "Laplacian. Steady state gives Laplace's equation ∇²u = 0, which is electrostatics, potential flow, and "
        "steady heat at once. One equation, four sciences.",
        ["diffusion", "heat equation", "laplace", "poisson", "gradient", "field"], "the diffusion equation",
        conns=[{"to_card_id": MASTER, "relationship": "instance_of", "evidence": "the flow form in space and time"}]))
    cards.append(_c("card_sys_shadow", "The shadow & the inverse — why the corrupted form still works",
        "The corrupted or 'bad' version of a system still operates — and only because it is the SHADOW or "
        "INVERSE of the true form, never a thing of its own. This is privatio boni (Augustine): evil is a "
        "privation, a good disordered; it has no design of its own, so it must borrow the real one — a lie "
        "borrows grammar, a counterfeit borrows the mint, a temptation borrows a true desire. 'Even that "
        "connection has power': the inversion still carries the form, so the shadow proves the light and points "
        "back to the source (Colossians 2:17 shadow→substance; 2 Corinthians 11:14 an angel of light; Romans "
        "1:25 exchanged the truth for a lie). Map the dark as an inversion of the true — never as its own ground.",
        ["shadow", "inverse", "privatio boni", "corruption", "counterfeit", "augustine", "colossians", "evil"],
        "the shadow and the inverse"))
    cards.append(_c("card_sys_cascade", "The cascade — one design over the planes",
        "Because the same form recurs at every scale and in every domain, creation is fractal: the design "
        "cascades over planes. This is why an engineer who masters one system reads the others on sight, and "
        "why the map of the world keeps rhyming with the map of the Word. The repetition is not coincidence "
        "but signature — the invisible things understood by the things that are made (Romans 1:20; Proverbs 25:2).",
        ["cascade", "fractal", "recurring", "self-similar", "one design", "signature", "romans 1", "fear of god"],
        "the cascade of the design"))

    out = Path("data") / "systems_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} systems cards (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
