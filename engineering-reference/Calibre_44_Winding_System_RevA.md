# Calibre 44 — Automatic Winding System

## Detailed Subsystem Specification — Rev A

**Date:** April 7, 2026
**Companion to:** Calibre 44 Movement Spec Rev J.1

---

## 1. Architecture

The winding system converts oscillating rotor motion into one-directional barrel winding through a three-stage path: rotor → reduction gear → ratchet on barrel arbor. Unidirectional winding with a freewheel mechanism at the rotor and a backwind prevention click at the ratchet.

### 1.1 Power Flow

```
Rotor (wrist motion)
    ↓ freewheel (drives in one direction only)
Driving gear (14T, on rotor post)
    ↓ mesh
Reduction wheel (31T)  ←  same shaft  →  Reduction pinion (8T)
    ↓ mesh
Ratchet wheel (36T, on barrel arbor)
    ↓
Barrel arbor → winds mainspring

[Ratchet click prevents backwinding]
```

### 1.2 Ratio

| Stage | Input | Output | Step-Down |
|---|---|---|---|
| Rotor → Reduction | 14T | 31T | 2.21:1 |
| Reduction → Ratchet | 8T | 36T | 4.50:1 |
| **Total** | | | **10.0:1** |

For every 10 rotor turns, the barrel arbor turns once. Full wind (10 barrel turns) requires approximately 100 effective rotor turns. During normal daily wear (8+ hours), the rotor easily accumulates this through wrist oscillation.

Torque multiplication: the rotor generates approximately 0.1–0.3 mN·m from gravity and wrist acceleration. The 10:1 step-down multiplies this to 1.0–3.0 mN·m at the barrel arbor — comfortably exceeding the mainspring resistance of 1.2–1.4 mN·m at full wind.

---

## 2. Components

### 2.1 Rotor Assembly

The rotor body, tungsten segment, and bearing are unchanged from the movement spec. The driving gear is integral to the rotor hub — teeth machined directly onto the underside of the rotor post, below the bearing.

| Parameter | Value |
|---|---|
| Rotor body | Brass (Ni-plated), Ø30 mm, 0.8 mm thick |
| Tungsten segment | ~120° arc, 1.2 mm max thickness at rim |
| Bearing | ABEC-7, 3×7×2 mm, sealed, at movement center |
| Driving gear | 14T, m0.18, integral to rotor post |
| Driving gear PD | 2.52 mm |

### 2.2 Freewheel Mechanism

The driving gear sits freely on the rotor post (not rigidly attached). A small click pawl, laser-cut from spring steel and pinned to the bridge, engages the driving gear teeth.

**Winding direction:** The pawl catches a tooth on the driving gear. Rotor torque transmits through the pawl into the gear, which drives the reduction train.

**Reverse direction:** The pawl deflects over the teeth. The driving gear stays stationary. The rotor freewheels. No torque reaches the reduction train.

| Parameter | Value |
|---|---|
| Click pawl | Laser-cut spring steel, 0.15 mm thick |
| Pawl mounting | Pinned to bridge post |
| Pawl engagement | Asymmetric tooth profile on driving gear |
| Tooth profile | Sawtooth (steep drive face, shallow release face) |
| Freewheel sound | Faint ticking in non-winding direction (normal) |

### 2.3 Reduction Wheel + Pinion

A single intermediate wheel with an integral pinion, mounted on a steel arbor between the rotor center and the barrel position.

| Parameter | Value |
|---|---|
| Wheel | 31T, m0.18, PD 5.58 mm |
| Pinion | 8T, m0.18, PD 1.44 mm |
| Arbor | Hardened steel, Ø0.8 mm |
| Material | Brass wheel (Ni-plated), steel pinion |
| Pivot | Runs in bronze bushings (bridge + unibody) |
| Position | X = –3.98, Y = –0.76 mm from center (~9 o'clock) |

**Manufacturing note:** The 8T pinion is the same cutter setup and stock as the third wheel, fourth wheel, and escape wheel pinions. One pinion geometry, four applications in the movement, now five including the reduction pinion.

### 2.4 Ratchet Wheel

Mounted on the barrel arbor upper extension, above the bridge. Receives winding torque from the reduction pinion and transfers it to the barrel arbor to wind the mainspring.

| Parameter | Value |
|---|---|
| Tooth count | 36T, m0.18, PD 6.48 mm |
| Material | Hardened steel |
| Mounting | Press-fit or keyed to barrel arbor upper extension |
| Position | On barrel arbor axis: X = –5.97, Y = –4.18 mm |
| Thickness | 0.5 mm |

### 2.5 Ratchet Click

Prevents the barrel from unwinding backwards through the auto train. Integral flexure machined into the bridge — not a separate part. The flexure bears against the ratchet wheel teeth and allows forward rotation only.

| Parameter | Value |
|---|---|
| Type | Integral bridge flexure |
| Material | 304 SS (same as bridge) |
| Engagement | Spring pressure against ratchet tooth flanks |
| Part count | 0 (integral) |

---

## 3. Center Distances

| Mesh | Distance | Module |
|---|---|---|
| Rotor driving gear → Reduction wheel | 4.05 mm | 0.18 |
| Reduction pinion → Ratchet wheel | 3.96 mm | 0.18 |

Both meshes sit between the movement center (0,0) and the barrel position (–5.97, –4.18), in the 9–10 o'clock zone. This keeps the winding train on the opposite side of the movement from the escapement and balance, avoiding interference.

---

## 4. Vertical Position

The entire winding train sits in the **ratchet + rotor zone** of the vertical stack, between the bridge and the caseback:

| Layer | Thickness | Contents |
|---|---|---|
| Bridge upper surface | — | Click pawl pinned here |
| Ratchet wheel | 0.50 mm | On barrel arbor, above bridge |
| Clearance | 0.15 mm | Gap between ratchet and rotor |
| Rotor + driving gear | 1.20 mm | Rotor body + tungsten at rim |
| Clearance | 0.15 mm | Gap to caseback |
| Caseback | 0.80 mm | Threaded ring |

The reduction wheel+pinion arbor passes through the bridge vertically. The wheel meshes with the driving gear (below bridge) and the pinion meshes with the ratchet (above bridge). The arbor runs in bronze bushings at both ends — same bushing family as the train pivots.

**Bushing update:** Two additional bushings needed for the reduction wheel arbor (one in bridge, one in unibody floor). These use Family B (2.8 mm OD), same as the third/fourth/escape bushings. Total bushing count goes from 14 to 16.

---

## 5. Parts Impact

### 5.1 New Parts

| Part | Qty | Material | Notes |
|---|---|---|---|
| Driving gear (click wheel) | 1 | Brass (Ni-plated) | 14T, free on rotor post |
| Click pawl | 1 | Spring steel, 0.15 mm | Laser-cut, pinned to bridge |
| Reduction wheel + pinion | 1 | Brass + steel | 31T/8T, m0.18 |
| Reduction arbor bushings | 2 | Phosphor bronze CDA 510 | Family B, same as train |

### 5.2 Updated Totals

| Category | Previous | Updated |
|---|---|---|
| Functional parts (line items) | 44 | 46 |
| Bushings | 14 | 16 |
| Total physical pieces | ~57 | ~61 |
| Unique pinion geometries | 2 (9T + 8T) | 2 (unchanged — 8T reused) |
| Gear cutting setups | 5 | 6 (+31T wheel, +14T driving gear, but 14T is small enough for micro-milling) |

The Calibre 44 name stays — it refers to the core movement. The winding module is a functional addition that sits above the bridge, like an automatic module on any movement.

---

## 6. Assembly Sequence (Winding Components)

After the bridge is seated and secured (step 8 in the main assembly sequence):

1. Install reduction wheel arbor through bridge, engage in lower bushing
2. Press ratchet wheel onto barrel arbor upper extension
3. Verify reduction pinion meshes cleanly with ratchet
4. Place click pawl on bridge post, verify engagement with driving gear clearance
5. Place driving gear (click wheel) on rotor post
6. Install rotor bearing into seat
7. Place rotor onto bearing, verify driving gear engages click pawl
8. Spin rotor by hand: winding direction should transmit to barrel (audible mainspring tension); reverse should freewheel with faint click

---

## 7. Service Notes

The winding train is fully accessible from the caseback side after removing the rotor and ratchet wheel. Components are standard: brass wheel, steel pinion, spring steel pawl. The click pawl is the highest-wear item — it should be inspected at every service and replaced if the tip shows rounding or if freewheel engagement becomes inconsistent.

The ratchet click (integral bridge flexure) should be checked for fatigue cracking at service. If cracked, the bridge is replaced — this is the one scenario where a bridge replacement is needed, but bridges are far less expensive than the unibody.

---

## 8. Open Items (Winding-Specific)

| # | Item | Status |
|---|---|---|
| 1 | Driving gear tooth profile — sawtooth angle and relief | Detail design |
| 2 | Click pawl spring rate — must exceed freewheel friction | Engineering |
| 3 | Reduction arbor diameter — finalize for bushing family B | Detail design |
| 4 | Ratchet attachment — press-fit vs keyed vs screw | Detail design |
| 5 | Winding authority test — verify 100 rotor turns achievable in 8h wear | Prototype |
| 6 | Freewheel noise level — acceptable click volume | Prototype |

---

*Calibre 44 — Winding System Rev A*
*Provident Precision*
