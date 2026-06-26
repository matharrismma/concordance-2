# Calibre 44 — Sourcing & Engineering Calculations

## Rev A — Ready for Supplier Engagement

**Date:** April 7, 2026
**Companion to:** Calibre 44 Movement Spec Rev J.1

---

## 1. Rotor Winding Authority — Verified

### 1.1 Rotor Mass Properties

| Component | Volume | Density | Mass |
|---|---|---|---|
| Brass body (half-moon, Ø30mm × 0.8mm) | 283 mm³ | 8.5 g/cm³ | 2.40 g |
| Tungsten segment (120° arc, R10–15mm × 1.2mm) | 157 mm³ | 17.5 g/cm³ | 2.75 g |
| **Total rotor** | | | **5.15 g** |

### 1.2 Moment of Inertia

| Component | I (g·mm²) | Contribution |
|---|---|---|
| Brass body | 135 | 23% |
| Tungsten segment | 447 | 77% |
| **Total** | **582** | |

The tungsten contributes 77% of the rotational inertia despite being only 53% of the mass. This is exactly the peripheral-mass design working as intended.

### 1.3 Winding Torque

| Parameter | Value |
|---|---|
| Combined center of mass from rotation axis | 8.56 mm |
| Maximum gravitational torque (rotor horizontal) | 0.433 mN·m |
| Torque at barrel arbor (after 10:1 step-up) | 4.33 mN·m |
| Mainspring resistance at full wind | 1.2–1.4 mN·m |
| **Winding margin** | **3.3× mainspring resistance** |

The rotor can comfortably wind against the fully wound mainspring. Even accounting for friction losses in the winding train (typically 30–40%), the delivered torque exceeds the mainspring resistance by approximately 2×. **Winding authority is confirmed.**

### 1.4 Winding Rate

| Parameter | Value |
|---|---|
| Effective rotor oscillations per hour (active wear) | 500–800 |
| Ratchet clicks per rotor oscillation | ~1 |
| Barrel turns per hour | 1.4–2.2 |
| Time to full wind (10 turns) | 4.5–7 hours |
| Daily wear assumption | 8+ hours |
| **Result** | **Full wind achieved during normal daily wear** |

---

## 2. Mainspring Supplier Specification

This is a ready-to-send document for mainspring suppliers.

### 2.1 Application

| Parameter | Value |
|---|---|
| Movement | Calibre 44, 3 Hz (21,600 vph) automatic |
| Barrel drum | 304 SS, cavity ID 11.0mm, depth 2.6mm |
| Barrel arbor | Hardened steel, hook root Ø1.0mm |
| Winding | Automatic only (no manual wind) |

### 2.2 Spring Requirements

| Parameter | Value |
|---|---|
| Alloy | Nivaflex or equivalent Co-Ni-Cr |
| Height | 1.30 mm ±0.02 mm |
| Thickness | 0.09–0.10 mm ±0.003 mm |
| Developed length | 300–330 mm (supplier to optimize) |
| Target turns | 10 effective |
| Target torque | 1.2–1.4 mN·m at full wind |
| Torque curve | Flat across turns 2–8 (±10% variation) |
| Inner hook | Eye type, ID ~0.8mm, chamfered edges |
| Outer hook | T-hook for drum wall slot |
| Power reserve | 57 hours minimum at 3 Hz |

### 2.3 Environmental

| Parameter | Value |
|---|---|
| Operating temperature | –10°C to +50°C |
| Corrosion resistance | 10+ years in sealed barrel |
| Fatigue life | >50 million full cycles |

### 2.4 Delivery

Fully hardened and tempered, ready for assembly. Polished or fine-rolled surfaces, free of pits/burrs. Individual tubes or trays, clean-room compatible packaging.

### 2.5 Quantities

| Stage | Quantity |
|---|---|
| Prototyping | 50 pcs |
| First production | 500 pcs |
| Annual forecast | 2,000–5,000 pcs |

### 2.6 Supplier to Provide

1. Recommended thickness and length for target performance
2. Torque curve data (torque vs turns)
3. Fatigue test data or certification
4. Unit pricing at 50 / 500 / 2,000 / 5,000 qty
5. Lead time for prototype and production

---

## 3. Escapement & Balance Kit — Sourcing Requirements

### 3.1 Kit Contents (11 component groups)

1. Escape wheel + pinion (15T, m0.18, nickel silver + hardened steel)
2. Pallet fork with 2 synthetic ruby pallet stones
3. Impulse jewel (synthetic ruby, Ø0.3mm, in roller table)
4. Roller table (hardened steel)
5. Balance wheel (Glucydur, Ø9–10mm, pre-poised)
6. Balance staff (hardened steel, pivot Ø0.10–0.12mm, mirror-polished)
7. Hairspring (Nivarox, flat, 3 Hz)
8. Collet (nickel silver)
9. Stud + stud screw (steel, M0.6)
10. Regulator index (steel)
11. Incabloc shock protection (upper + lower complete)

### 3.2 Performance Requirements

| Parameter | Target |
|---|---|
| Frequency | 3 Hz / 21,600 vph |
| Amplitude at 1.2–1.4 mN·m barrel torque | 270–310° |
| Beat error | ≤ 0.5 ms |
| Daily rate as delivered | ±8 s/d |
| Daily rate after regulation | ±5 s/d |
| Positional variance | ≤ 8 sec across 5 positions |

### 3.3 Interface

All pivots run in synthetic ruby jewels pressed into phosphor bronze bushings in the unibody and bridge. Bushing bore dimensions provided with order. The kit must work with the Calibre 44 bushing system — supplier will receive bushing spec for pivot compatibility verification.

### 3.4 Quantities

| Stage | Quantity |
|---|---|
| Prototyping | 25 kits |
| First production | 500 kits |
| Annual forecast | 2,000–5,000 kits |

### 3.5 Preferred Suppliers

1. **Sellita** — SW200 escapement/balance components (primary)
2. **Soprod** — equivalent 3 Hz components (alternate)
3. **ETA** — 2824 components (if available outside Swatch Group)
4. **Hangzhou / Seagull** — cost-reduced variant only (backup)

---

## 4. US Supply Chain Directory

### 4.1 Sourced Components (Cannot Be Made at Signal)

| Component | Primary Supplier | Location | Prototype Source |
|---|---|---|---|
| Mainspring (Nivaflex) | Générale Ressorts | Switzerland | Ofrei (USA) |
| Escapement/balance kit | Sellita | Switzerland | Ofrei (USA) |
| Synthetic ruby jewels | Swiss Jewel Co. | Switz./USA | Ofrei (USA) |
| Rotor bearing (ABEC-7) | NMB / MinebeaMitsumi | USA/Japan | Boca Bearings (USA) |
| Sapphire crystals | Stettler Sapphire | Switzerland | Ofrei (USA) |
| Hands (dauphine) | Fiedler / Universo | Switzerland | Ofrei (USA) |
| Hairspring (Nivarox) | NivaroxFAR | Switzerland | Included in kit |
| Incabloc shock system | Incabloc SA | Switzerland | Included in kit |

### 4.2 Raw Materials (Domestic)

| Material | Primary Supplier | Location | Notes |
|---|---|---|---|
| 304 SS bar (case, bridge, barrel) | Ryerson | USA | Production volume |
| Phosphor bronze CDA 510 (bushings) | McMaster-Carr | USA | Rod, any quantity |
| FKM O-rings (gaskets) | Parker Hannifin | USA | Standard AS568 |
| Brass rod (gear blanks) | McMaster-Carr | USA | Free-machining |
| Carbon steel rod (pinions) | McMaster-Carr | USA | 1095 or equiv. |
| Spring steel strip (yoke, click) | McMaster-Carr | USA | 0.1–0.15mm |
| Tungsten alloy (rotor segment) | Buffalo Tungsten | USA | Custom shapes |

### 4.3 Leather (Domestic)

| Material | Supplier | Location | Notes |
|---|---|---|---|
| Shell cordovan | Horween Leather | Chicago, IL | American-made, premium |
| Chromexcel | Horween Leather | Chicago, IL | Alternative, lower cost |

### 4.4 Prototype Quick-Start

For the first 25 prototype movements, **Ofrei (Otto Frei)** in the USA can supply nearly every sourced component in small quantities: mainsprings, escapement parts, jewels, hands, crystals, crowns, spring bars. This is the fastest path to a running prototype without waiting for Swiss OEM lead times.

**Prototype bill of materials — single source:**

| Item | Ofrei Stock | Approx. Cost |
|---|---|---|
| Mainspring (generic 3 Hz) | Yes | $8–15 ea |
| Escape wheel + pallet fork | Yes (ETA/generic) | $15–30 ea |
| Balance complete (wheel+staff+spring) | Yes | $25–50 ea |
| Incabloc shock set | Yes | $10–20 ea |
| Jewels (17 pcs assorted) | Yes | $1–3 ea |
| Sapphire crystal (flat) | Yes | $10–25 ea |
| Hands (dauphine pair) | Yes | $5–15 ea |
| Crown + tube | Yes | $5–10 ea |
| Spring bars | Yes | $2–5 ea |

**Estimated sourced component cost per prototype:** $100–200 (excluding raw materials for machined parts).

---

## 5. Service Kit Definition

### 5.1 Standard 10-Year Service Kit

Everything a watchmaker needs for a complete Calibre 44 overhaul, shipped in one package.

| Item | Qty | Notes |
|---|---|---|
| Bushing set (16 pcs, 5 blanks) | 1 set | Pre-sorted by position |
| Mainspring | 1 | Nivaflex, to spec |
| Crown O-rings | 2 | FKM, Ø3.5 × CS 0.5 |
| Tube O-ring | 1 | FKM, Ø2.8 × CS 0.3 |
| Caseback gasket | 1 | FKM, per case spec |
| Crystal gasket | 1 | Polymer, per case spec |
| Click pawl | 1 | Spring steel, laser-cut |
| Lubricant set | 1 | Moebius 8217, 9010, 941 (applicator vials) |
| Service manual | 1 | 20-page booklet (first service only) |

**Estimated service kit cost:** $40–60 wholesale to watchmaker.

### 5.2 Partial Service Kit (Gaskets + Lube Only)

For water resistance refresh without full movement service.

| Item | Qty |
|---|---|
| Crown O-rings | 2 |
| Tube O-ring | 1 |
| Caseback gasket | 1 |
| Crystal gasket | 1 |
| Lubricant set | 1 |

**Estimated cost:** $15–20 wholesale.

### 5.3 Individual Parts Availability

All bushings, jewels, gaskets, mainspring, click pawl, and rotor bearing available individually by part number. Watchmaker orders what they need, nothing more.

---

## 6. Remaining Open Items (Updated)

| # | Item | Status | Notes |
|---|---|---|---|
| ~~1~~ | ~~Pivot map~~ | **SOLVED** | §11 of movement spec |
| ~~2~~ | ~~Vertical stack~~ | **SOLVED** | §12 of movement spec |
| ~~3~~ | ~~Center distances~~ | **CORRECTED** | §11.2 of movement spec |
| ~~5~~ | ~~Bushings~~ | **SOLVED** | Bushing System Rev A |
| ~~6~~ | ~~Crown/screw-down~~ | **SOLVED** | Crown/Keyless/MW Rev A |
| ~~7~~ | ~~Rotor authority~~ | **SOLVED** | This document §1 |
| ~~8~~ | ~~Mainspring spec~~ | **SOLVED** | This document §2 |
| ~~9~~ | ~~Motion works~~ | **SOLVED** | Crown/Keyless/MW Rev A |
| 4 | Balance kit sourcing | **READY TO SEND** | This document §3 — send to Sellita/Ofrei |
| 10 | Index attachment method | Open | Press-pin vs adhesive — decide at prototype |
| 11 | Lubricant part numbers | **SPECIFIED** | Moebius 8217, 9010, 941 |
| 12 | US supply chain | **MAPPED** | This document §4 |
| 13 | Service kit | **DEFINED** | This document §5 |
| 14 | Service manual | Open | Write after first prototype assembly |
| 15 | Case/bracelet CAD | Open | Signal — start with unibody, then bracelet |
| 16 | End-link interface | Open | Detail design after case CAD |
| 17 | Clasp sourcing | Open | Evaluate at prototype |

**Items fully closed: 11 of 17.** Remaining items are either prototype-stage decisions (10, 14, 16, 17) or CAD work (15). The engineering is substantially complete.

---

*Calibre 44 — Sourcing & Calculations Rev A*
*Provident Precision*
