# COMPONENTS — the engine as a vacuum-tube computer

Matt, 2026-10-06: *"Think of a vacuum tube computer. That's an easy concept. We need the components …
regulators, capacitors, diodes, transistors, Antennae, Vacuum tubes … I see it kind of steam punk."*

This is the engine's subsystem map, in the shape of the Calibre 72 / 40U-72 movement map and the Prism and
Humanoid-Robot design bibles — **one vocabulary across the whole design system** (the robot bible's Design
Lineage already names Narrow Highway / Concordance, The Keeping, the Gradient Manifold, Programmable Fabric
and Pressure Fighting as its own source concepts; the engine is a member of that family, built in software
instead of titanium).

It is deliberately factual. Where a part is not yet proven, it is marked with its real evidence status
rather than implied. No part is a metaphor only: every row names code that exists.

The method and the vocabulary are adapted from Matt's own hardware design bibles (private IP). Only the
*patterns* are used here; none of those documents' specifications are reproduced.

---

## 1. The authority chain (the orchestration)

Nothing in the engine acts on its own authority. Force flows down one chain and only one; each plane may
do less than the plane above it, never more. This is the robot bible's authority chain, mapped to the
engine part-for-part.

```
request → Authority gate → Main PROPOSES → Steward ADMITS a bounded corridor
        → Conductor RUNS it (deterministic, cannot enlarge the corridor)
        → Reflex ENFORCES the live envelope (overrides nothing above it; nothing overrides it)
        → Scribe RECORDS → witness + seal, OUTSIDE the requesting process → Steward closes the corridor
```

| Plane | Owns | Cannot do | The engine's part |
|---|---|---|---|
| **Main** | perceive, reason, propose a bounded action | self-authorize; emit a verdict | the agent / LLM → `discern` (proposes, never decides) |
| **Steward** | admit a bounded capability; **fails closed** | run the work itself; relax a hard limit | `kernel` / `kernel_gate` + `alignment` + the PD gate + the deploy **Gate** |
| **Conductor** *(the robot bible's Motion Executive)* | deterministic, bounded execution of an approved corridor | enlarge the mission / force / corridor; author a tactic | `lead` (THE LEAD — composes the discerned tool/technique/strategy) + the verifiers + the composition/chaining layer run it, bounded |
| **Reflex** | the hard envelope, in real time | be overridden by Main or Conductor | **crisis** backstop + the **gauges** (tolerances) + the **diode/airlock** |
| **Scribe** | capture events, prepare receipts | alter authority or state | the activity log + `receipts` |
| **witness + seal** | verify independently, seal permanently | run inside the requester | `attest` (two-or-three, Deut 19:15) + the **CAS seal** |

Two gate levels, both `RED → FLOOR → WAY → EXECUTION`:
- **Authority** — *may this be attempted at all?* RED (prohibition: crisis, the liberty/free-will line) →
  FLOOR (minimums) → witness & consent → final authority.
- **Execution** — *given authority, how?* RED (hard envelope) → FLOOR (readiness) → WAY (an approved,
  bounded primitive) → EXECUTION.

**Law (from the robot bible, already ours):** *Physical truth outranks software truth* (the math outranks
the model's claim) · *Commands are not proof* (narrowing is evidence; a success needs a witness) · *The
core is immutable; the edge is configurable* · *Every claim earns validation* (the gate; evidence, not
enthusiasm) · *Locate with datums, clamp with fasteners* · *Interfaces are products.*

---

## 2. The layers (what may wear, what may not)

From the movement map and Prism's permanent-vs-renewable rule. **The permanent structure locates and
protects; it must never become the wear part.**

| Layer | Meaning | In the engine |
|---|---|---|
| **Permanent structure** | carries load; establishes the master datums; survives service | the immutable core: the kernel, the seal/CAS/ledger schema, the five-door spine, the mission |
| **Precision cartridge** | removable, positively located; alignment survives replacement | the verifiers, the composition layer, the gate — swappable without moving the datum |
| **Wear element** | takes predictable wear; inspectable; scheduled | the keeping's stock, the semantic index, the atlas edges, the caches |
| **Consumable** | replaced at intervals without redesign | an individual card, a want, a probe, a traffic rollup |

= immutable core / validation boundary / surface, in the movement's words.

---

## 3. Evidence status (how real is this part)

From the robot bible §14.1 — the one honest ladder, used instead of vaguer words. A part advertises the
status it has **earned**, never the one intended.

`Concept` · `Prototype-pending` · `Experimental` · `Verified` · `Supplier-dependent` · `Production-ready`

A part is **Verified** only against a defined test with repeatable pass evidence (a golden, a probe, a
benchmark). `Supplier-dependent` marks a part that leans on an outside source (a PD corpus, a CODATA
constant, an ingested dataset) — true until that source is itself re-checked by calculation.

---

## 4. The parts, by primitive

Every part carries four tags: **primitive · layer · plane · status**. A part may serve more than one plane;
its primary plane is named, the span noted. Grounded in `src/concordance/` and `systems.py`.

| Primitive | What it is | Real parts (modules) | Plane | Layer | Status |
|---|---|---|---|---|---|
| **Vacuum tube** | the active logic: a claim in, an amplified verdict out | the verifiers, `derivation`, `receipts` | Conductor | Precision | Verified (80/80 domains) |
| **Transistor** | a small control signal switches a large flow | `discern`, `router` (Main side); `gates`, `kernel_gate` (Steward side) | Main / Steward | Precision | Verified |
| **Diode** | one-way flow; blocks the reverse | `airlock`, the composition **diode** | Reflex | Permanent | Verified |
| **Regulator** | governs level/rate; holds it in spec | the Gate, the Balance, the Gauges, `alignment`, the PD gate, the `kernel` covenant | Steward + Reflex | Permanent/Precision | see §5 |
| **Capacitor** | stores charge, smooths, releases on demand | the **keeping** (reservoir), `candidates`, the **wants** queue, caches | Plant | Wear | Experimental (stock thin) |
| **Antenna** | receive + transmit across the gap | the five **doors**, the **mesh** (LoRa, literal), the **MCP**, the forage/want loop, **.tv** | Main (intake) / Scribe (out) | Precision | Verified (doors) / Experimental (tv) |
| **Resistor** | limits / damps the flow | `ratelimit` buckets, the alignment ×0.6 down-weight | Reflex | Precision | Verified |
| **Transformer** | couples two circuits; steps a signal across | the **bridges** (cross-domain), the reader's **tongue** / tortoise | Conductor | Precision | Experimental |
| **Relay** | one circuit switches another, at a distance | the mesh relay + **node sync** (a signed bundle trips a far node) | Scribe / Steward | Precision | Verified (sync) |
| **Clock / escapement** | the beat that paces each checked step | the **tick** stick, the escapement's "one checked step", the timers | cross-cutting | Permanent | Verified (Riemann to T=1000) |
| **Fuse / breaker** | fails safe on overload | the **crisis** backstop (fails to real people), the fail-closed gates (PD, quarantine) | Reflex | Permanent | Verified |
| **Bus / backplane** | wires every part to every part | the **fascia** (concordance graph) + the import graph (`systems.subsystem_graph`) | cross-cutting | Permanent | Verified (isolation detected) |

---

## 5. The regulators (defined and orchestrated)

The regulators are the Steward and Reflex parts — the ones that govern what passes rather than compute
data. Firing order is the authority chain: **crisis first, then ingest, then verify, then deploy, with
balance and the diode continuous.** Each closes against a number, an owner, and a fallback (Prism's gate
discipline); each has a live reading the Bridge will show.

| Regulator | Plane | Governs | Fires at | Closes against (number) | Fallback |
|---|---|---|---|---|---|
| **Crisis backstop** | Reflex | a cry for help outranks everything → real people | first, always | is_crisis wired; resources present | the semantic backstop catches the near-miss |
| **PD / License gate** | Steward | only public-domain text is voiced/served | ingest | withheld-by-license count | hold to reference, never voice |
| **Alignment gate** | Steward | the tier a source enters at (aligned / reference ×0.6 / sectioned) | ingest | tier counts | down-weight, then explicit-only |
| **Diode / airlock** | Reflex | one-way flow — proof can't exit, a miss can't pass as a hit | ingest + continuous | airlock rejections | refuse, quarantine |
| **Gauges** | Reflex | the tolerance on every verdict — the door's width | verify | WIDE/FIXED gauge count, loosest door | tighten to scaled tolerance |
| **Kernel** | Steward | a proposed state-change vs the five moves + covenant | verify | gate decisions | refuse; born-quarantined |
| **Balance (governance)** | Steward | the true rate — a discordance indicts the method | continuous | Birge ratio; benchmark regressions | suspect the method before the world |
| **Gate (deploy)** | Steward | what change is admitted to the live engine | deploy | domains N/80, assay floor, false-positives | revert to the pre-deploy snapshot |

---

## 6. The Bridge (the console)

The Bridge (`site/keep.html` → renamed, route `/bridge`, token-gated) is the front panel of this machine:
a row of **component** lights (primitive · layer · plane · status, from `components.py` over `systems.py`)
and a row of **regulator** meters (§5, live readings), each read **live and on trend**. Steampunk — brass
and glass, tubes that glow when a part is Verified and live, needle gauges for the regulators, the
authority chain drawn as the backplane. Its purpose is the movement map's purpose, in Matt's words: *"one
place to check what's real and what is still open."*

---

## 7. Honest ceiling

- **No part is a metaphor only.** Every row names code that exists; a row with no module is not added.
- **Status is earned, never claimed.** A part reads Verified only against a defined, repeatable test.
- **The permanent structure never wears.** The immutable core locates and protects; it is not the
  sacrificial part.
- **Build the smallest complete system, then attack it** (the bibles' closing rule = Smallest Faithful
  Step): the next step is `components.py` computing this map live, and the Bridge rendering it — not a
  larger diagram.
