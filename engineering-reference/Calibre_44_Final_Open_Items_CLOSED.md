# Calibre 44 — Final Open Items Resolution

## All Items Closed — Rev A

**Date:** April 7, 2026

---

## Item 4: Balance Kit Sourcing — DECIDED

**Two-track approach.**

**Prototype (25 units):** Source from Ofrei (Otto Frei, USA). Generic 3 Hz Swiss lever components — ETA 2824-compatible balance complete, pallet fork, escape wheel, Incabloc shock sets. Ships in days, no MOQ. Order now.

**Production (500+):** Engage Sellita directly for SW200 escapement component sets. Provide Calibre 44 bushing bore specs for pivot compatibility verification. Alternate: Soprod if Sellita pricing is prohibitive.

**Critical step before CAD freeze:** Test-fit prototype Ofrei components in the first machined unibody. If standard SW200 pivot spacing doesn't match the Calibre 44 pivot map, adjust the pivot map before freezing production CAD. This is cheaper than requesting custom geometry from a Swiss supplier.

---

## Item 10: Index Attachment — DECIDED

**Press-pin. No adhesive.**

Each applied index (12, 3, 6, 9) has two integral Ø0.40mm pins that press into Ø0.39mm blind holes in the dial surface. Interference fit — mechanical retention that survives 50+ years without degradation. Assembly with a brass drift. Removal with a flat blade. No chemistry.

| Detail | Value |
|---|---|
| Pin diameter | 0.40 mm |
| Blind hole diameter | 0.39 +0.000/+0.005 mm |
| Pin length | 0.6 mm |
| Hole depth | 0.7 mm |
| Pins per index | 2 |
| Total pin holes in dial | 8 |

Remaining 8 hour markers: laser-engraved directly into the dial surface, 0.03–0.05mm deep, filled with white lacquer or BGW9 luminous compound.

---

## Item 14: Service Manual — OUTLINED

20 pages. Written after first prototype assembly (needs real photos and verified procedures). Structure:

| Pages | Content |
|---|---|
| 1 | Cover — logo, serial field, revision |
| 2 | Movement overview — architecture diagram, specs table |
| 3 | Required tools — staking set, screwdrivers, timing machine, NO proprietary tools |
| 4–5 | Disassembly — step-by-step with numbered photos |
| 6–7 | Cleaning — ultrasonic protocol, inspection checklist |
| 8–9 | Bushing service — when to replace, removal/installation, endshake verification |
| 10–11 | Reassembly — lubrication points diagram, cannon pinion friction check |
| 12–13 | Lubrication chart — Moebius 8217, 9010, 941 with application diagram |
| 14–15 | Regulation — 5 positions, regulator adjustment, ±5 s/d target |
| 16 | Winding system — click pawl inspection, freewheel test |
| 17 | Water resistance — O-ring replacement, wet test protocol |
| 18 | Troubleshooting — stops, poor rate, winding failure, water ingress |
| 19 | Parts reference — bushings, jewels, gaskets, mainspring, service kit ordering |
| 20 | Back cover — contact info, warranty, "Built in Tennessee. Serviced anywhere." |

---

## Item 15: Case CAD / Machining Guidance — SPECIFIED

### Three Setups from Ø48mm 304 SS Bar

**Setup 1 — Exterior (3-axis):** Face top, turn exterior profile (bezel step, case band, caseback thread), cut crystal step and gasket grooves, cut crown recess.

**Setup 2 — Interior + Hidden Channels (5-axis):** Rough movement cavity, mill barrel pocket, precision bore all 8 bushing recesses per pivot map, mill rotor cavity, mill motion works recess, bore center hole and crown tube bore, drill and tap all screw holes, drill index pin holes, machine hidden lug channels (undercut from caseback side), drill spring bar bores and detent dimples.

**Setup 3 — Lug Profiles (5-axis):** Profile lug extensions at 12 and 6, blend into case band, chamfer bezel edge.

**Finishing:** Deburr → electropolish exterior (masked) → brush flanks (horizontal) → brush mid-zone (vertical) → polish bezel chamfer → laser sunburst dial → bead-blast interior → ultrasonic clean.

~35 precision features total. Well within Signal's 5-axis capability.

---

## Item 16: End-Link Interface — DETAILED

### Channel (in case)

| Parameter | Value |
|---|---|
| Width | 22.0 ±0.05 mm |
| Depth | 2.0 mm |
| Height (12–6 direction) | 3.0 mm |
| Spring bar bores | Ø1.2 mm × 1.5 mm deep, each side |
| Detent dimple | Ø1.0 mm × 0.3 mm deep, in channel floor |

### End-Link Body

| Parameter | Value |
|---|---|
| Width | 21.90 ±0.03 mm (0.05–0.13 mm clearance in channel) |
| Length (extends from case) | 6.0 mm |
| Thickness | ~4 mm tapering to 2.5 mm |
| Spring bar hole | Ø1.2 mm through-bore |
| Detent pin | Ø0.9 mm, spring-loaded, ~0.5N preload |
| Exterior | Two angled facets (15° from horizontal), brushed, polished chamfer edges |
| Material | 304 SS (same stock as case) |

### Strap Mode

Standard quick-release spring bar sits in the same bores. Strap end tucks into channel. Detent dimple is invisible. Maximum strap thickness at attachment: 2.0 mm.

---

## Item 17: Clasp — DECIDED

**V1: Source modified off-shelf butterfly deployant.** Custom clasp is a V2 item.

| Parameter | Value |
|---|---|
| Type | Butterfly deployant, dual push-button |
| Width | 18 mm (bracelet tapers 22 → 18) |
| Micro-adjust | 3 positions, ~2 mm per step |
| Source (V1) | Hadley-Roma or equivalent, laser-engrave logo |
| Cost | $8–15 per unit |
| Finish | Brushed body, polished buttons |

**V2 (after first production):** In-house CNC at Signal — full design control over button profile, micro-adjust detents, branding. Better margin, better product, but not worth the delay for launch.

---

## Status: ALL 17 ITEMS CLOSED

| # | Item | Status |
|---|---|---|
| 1 | Pivot map | **SOLVED** — Movement Spec §11 |
| 2 | Vertical stack | **SOLVED** — Movement Spec §12 |
| 3 | Center distances | **CORRECTED** — Movement Spec §11.2 |
| 4 | Balance kit sourcing | **DECIDED** — Ofrei prototype, Sellita production |
| 5 | Bushings | **SOLVED** — Bushing System Rev A |
| 6 | Crown / screw-down | **SOLVED** — Crown/Keyless/MW Rev A |
| 7 | Rotor mass / winding | **VERIFIED** — Sourcing doc §1, 3.3× margin |
| 8 | Mainspring spec | **READY TO SEND** — Sourcing doc §2 |
| 9 | Motion works recess | **SOLVED** — Crown/Keyless/MW Rev A |
| 10 | Index attachment | **DECIDED** — Press-pin, this document |
| 11 | Lubricant part numbers | **SPECIFIED** — Moebius 8217, 9010, 941 |
| 12 | US supply chain | **MAPPED** — Sourcing doc §4 |
| 13 | Service kit | **DEFINED** — Sourcing doc §5 |
| 14 | Service manual | **OUTLINED** — 20 pages, this document |
| 15 | Case CAD guidance | **SPECIFIED** — 3 setups, this document |
| 16 | End-link interface | **DETAILED** — This document |
| 17 | Clasp | **DECIDED** — Off-shelf V1, in-house V2 |

---

## Next Actions

1. **Order prototype parts from Ofrei** — escapement kits, mainsprings, jewels, crystals, hands, crowns
2. **Order 304 SS bar stock** — Ø48mm × 300mm lengths for first unibody machining
3. **Order CDA 510 phosphor bronze rod** — for bushing prototypes
4. **Send mainspring spec to Générale Ressorts** — for production quotation
5. **Contact Sellita** — for SW200 component kit pricing at volume
6. **Program Setup 1 at Signal** — exterior profile, start making chips
7. **Test-fit escapement components** — verify pivot compatibility before CAD freeze

---

*Calibre 44 — Engineering complete. Time to build.*
*Provident Precision*
