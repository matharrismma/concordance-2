# Calibre 44 — Serviceable Bushing System

## Detailed Specification — Rev A

**Date:** April 7, 2026
**Companion to:** Calibre 44 Movement Spec Rev J.1

---

## 1. Purpose

Every pivot bore and jewel seat in the Calibre 44 uses a removable phosphor bronze bushing. This makes the unibody case and bridge effectively immortal — any wear or damage to a pivot interface is repaired by driving out the old bushing and pressing in a new one. Standard staking tools. No special equipment. No factory return.

---

## 2. Material — All Bushings

| Parameter | Value |
|---|---|
| Alloy | Phosphor bronze CDA 510 |
| Hardness | ~95 HRB (as-drawn) |
| Condition | Cold-drawn tube or rod, stress-relieved |
| Self-lubricating | Yes (copper-tin matrix) |
| Corrosion resistance | Excellent — no plating required |

---

## 3. Tolerances — All Bushings

| Dimension | Tolerance |
|---|---|
| OD (press into case/bridge) | Nominal +0.005 / +0.010 mm |
| ID (jewel seat) | Nominal +0.000 / +0.005 mm |
| ID (plain bore, no jewel) | Nominal +0.005 / +0.015 mm |
| Length | ±0.02 mm |
| Concentricity (ID to OD) | ≤ 0.005 mm TIR |
| Bore cylindricity | ≤ 0.003 mm |
| Bore finish (jewel seat) | Ra 0.2–0.4 µm |
| Bore finish (plain) | Ra 0.4–0.8 µm |
| OD finish | Ra 0.4–0.8 µm |
| Chamfer (both ends) | 0.05 mm × 45° |
| Edge break | < 0.02 mm |

---

## 4. Bushing Families

Only **two external diameters** exist. This means only two recess sizes in the unibody and bridge CNC programs.

| Family | Bushing OD | Case/Bridge Recess | Used At |
|---|---|---|---|
| A (large) | 3.50 mm | 3.50 +0.000/–0.005 mm | Barrel, center, balance |
| B (medium) | 2.80 mm | 2.80 +0.000/–0.005 mm | Third, fourth, escape, pallet, reduction |

Interference fit: 0.005–0.010 mm on all press-fits.

---

## 5. Bushing Schedule — All 16 Positions

### 5.1 Family A — OD 3.50 mm

| Position | Location | Bushing ID | Jewel OD | Jewel ID | Length | Notes |
|---|---|---|---|---|---|---|
| BA-upper | Bridge | 2.05 | 2.00 | 1.00 | 1.40 | Barrel arbor upper |
| BA-lower | Unibody | 2.05 | 2.00 | 1.00 | 1.40 | Barrel arbor lower |
| CW-upper | Bridge | 2.05 | 2.00 | 0.90 | 1.40 | Center wheel upper |
| CW-lower | Unibody | 2.05 | 2.00 | 0.90 | 1.40 | Center wheel lower |
| BAL-upper | Bridge | 2.80 | — | — | 1.80 | Balance shock setting (Incabloc seats inside) |
| BAL-lower | Unibody | 2.80 | — | — | 1.80 | Balance shock setting (Incabloc seats inside) |

Balance bushings have a larger bore (2.80mm) to house the complete Incabloc shock assembly (cap jewel + hole jewel + spring + setting). The shock unit is a drop-in module — the bushing holds the outer setting ring.

### 5.2 Family B — OD 2.80 mm

| Position | Location | Bushing ID | Jewel OD | Jewel ID | Length | Notes |
|---|---|---|---|---|---|---|
| TW-upper | Bridge | 1.65 | 1.60 | 0.80 | 1.20 | Third wheel upper |
| TW-lower | Unibody | 1.65 | 1.60 | 0.80 | 1.20 | Third wheel lower |
| FW-upper | Bridge | 1.65 | 1.60 | 0.80 | 1.20 | Fourth wheel upper — **same part as TW** |
| FW-lower | Unibody | 1.65 | 1.60 | 0.80 | 1.20 | Fourth wheel lower — **same part as TW** |
| EW-upper | Bridge | 1.45 | 1.40 | 0.70 | 1.20 | Escape wheel upper |
| EW-lower | Unibody | 1.45 | 1.40 | 0.70 | 1.20 | Escape wheel lower |
| PF-upper | Bridge | 1.45 | 1.40 | 0.60 | 1.20 | Pallet fork upper |
| PF-lower | Unibody | 1.45 | 1.40 | 0.60 | 1.20 | Pallet fork lower |
| RW-upper | Bridge | 1.05 | — | — | 1.00 | Reduction arbor upper (plain bore, no jewel) |
| RW-lower | Unibody | 1.05 | — | — | 1.00 | Reduction arbor lower (plain bore, no jewel) |

Reduction wheel arbor runs in plain bronze bores — no jewels needed. The self-lubricating phosphor bronze provides adequate bearing quality for the low-speed, low-load winding train.

---

## 6. Unique Part Numbers (7 Types)

| PN | Family | OD | ID | Length | Jewel | Qty/Movement | Used At |
|---|---|---|---|---|---|---|---|
| B-01 | A | 3.50 | 2.05 | 1.40 | OD 2.00 | 4 | BA-upper, BA-lower, CW-upper, CW-lower |
| B-02 | A | 3.50 | 2.80 | 1.80 | Incabloc | 2 | BAL-upper, BAL-lower |
| B-03 | B | 2.80 | 1.65 | 1.20 | OD 1.60 | 4 | TW-upper, TW-lower, FW-upper, FW-lower |
| B-04 | B | 2.80 | 1.45 | 1.20 | OD 1.40 | 4 | EW-upper, EW-lower, PF-upper, PF-lower |
| B-05 | B | 2.80 | 1.05 | 1.00 | None | 2 | RW-upper, RW-lower |
| | | | | | | **16** | |

**Note on B-01:** Barrel and center wheel bushings share the same external and bore dimensions. The jewels pressed into them differ (barrel jewel ID 1.00 vs center jewel ID 0.90), but the bushing itself is the same part. The jewel is pressed in during assembly, not pre-installed. This reduces unique bushing types to **5** if jewels are installed separately.

**Note on B-04:** Escape wheel and pallet fork bushings share the same dimensions. The jewels differ slightly (escape ID 0.70 vs pallet ID 0.60), but again the bushing is the same part. Same logic — 5 truly unique bushing blanks if jewels are pressed separately.

### 6.1 Minimum Unique Bushing Blanks: 5

| Blank | OD | ID | Length | Qty/Movement |
|---|---|---|---|---|
| Blank 1 | 3.50 | 2.05 | 1.40 | 4 |
| Blank 2 | 3.50 | 2.80 | 1.80 | 2 |
| Blank 3 | 2.80 | 1.65 | 1.20 | 4 |
| Blank 4 | 2.80 | 1.45 | 1.20 | 4 |
| Blank 5 | 2.80 | 1.05 | 1.00 | 2 |
| | | | **Total** | **16** |

Five CNC turning setups produce all 16 bushings for the entire movement. Two blanks (1 and 3) each produce 4 identical pieces — batch efficiency.

---

## 7. Case/Bridge Recess Specifications

### 7.1 Recess Geometry

| Parameter | Family A | Family B |
|---|---|---|
| Nominal diameter | 3.50 mm | 2.80 mm |
| Tolerance | +0.000 / –0.005 mm | +0.000 / –0.005 mm |
| Depth | Bushing length + 0.05 mm | Bushing length + 0.05 mm |
| Bottom | Flat, Ra 0.8 µm | Flat, Ra 0.8 µm |
| Entry chamfer | 0.10 mm × 30° | 0.10 mm × 30° |
| Axis perpendicularity to surface | ≤ 0.01 mm | ≤ 0.01 mm |

The +0.05mm extra depth ensures the bushing sits flush or slightly sub-flush with the cavity surface. This prevents the bushing from proud-standing and interfering with wheel endshake.

### 7.2 Recess Count

| Location | Family A | Family B | Total |
|---|---|---|---|
| Unibody (case top / mainplate side) | 3 | 5 | 8 |
| Bridge | 3 | 5 | 8 |
| **Total** | **6** | **10** | **16** |

Only two recess diameters in each CNC program. Depths vary by position but the bore tool is the same.

---

## 8. Manufacturing Process

### 8.1 Bushing Production

1. Start with CDA 510 phosphor bronze rod (for Family A: Ø3.6mm, Family B: Ø2.9mm)
2. CNC Swiss-turn or automatic lathe
3. Turn OD to tolerance (+0.005/+0.010 over nominal recess)
4. Bore ID to tolerance
5. Part off at length ±0.02mm
6. Chamfer both ends (0.05 × 45°)
7. Deburr
8. Inspect: OD, ID, length, concentricity (100% for prototype, statistical for production)
9. Ultrasonic clean
10. Package in labeled trays by part number

### 8.2 Bushing Installation (New Production)

1. Verify recess diameter and depth with pin gauges
2. Apply light press lubricant (isopropyl alcohol — evaporates clean)
3. Align bushing with recess using staking tool guide
4. Press bushing flush with staking press (controlled force — not hammer)
5. Verify flush seating under magnification
6. Press jewel into bushing bore (for jeweled positions)
7. Verify jewel seating and concentricity

### 8.3 Bushing Replacement (Service)

1. Support case/bridge on staking anvil with appropriate die
2. Select flat punch slightly smaller than bushing OD
3. Drive bushing out from opposite side — steady, even pressure
4. Inspect recess for damage (unlikely — bronze is softer than steel)
5. Press new bushing per §8.2 above
6. Re-press jewel if reusing (or install new jewel)
7. Verify endshake and side shake of associated wheel
8. Re-lubricate pivot

---

## 9. Service Kit — Bushing Sets

### 9.1 Complete Service Kit (All 16 Bushings)

For full movement overhaul. Includes all 16 bushings (5 blanks × quantities), pre-sorted in labeled compartments. Jewels shipped separately (customer may reuse existing jewels if undamaged).

| Contents | Qty |
|---|---|
| Blank 1 (3.50 × 2.05 × 1.40) | 4 |
| Blank 2 (3.50 × 2.80 × 1.80) | 2 |
| Blank 3 (2.80 × 1.65 × 1.20) | 4 |
| Blank 4 (2.80 × 1.45 × 1.20) | 4 |
| Blank 5 (2.80 × 1.05 × 1.00) | 2 |
| **Total** | **16** |

### 9.2 Partial Service Kit (Balance + Escapement Only)

For targeted service of the regulating organ. Covers the highest-wear positions.

| Contents | Qty |
|---|---|
| Blank 2 (balance shock settings) | 2 |
| Blank 4 (escape + pallet) | 4 |
| **Total** | **6** |

### 9.3 Individual Bushing (Any Position)

Available individually by part number for single-position replacement.

---

## 10. Compatibility Notes

All bushings are specific to the Calibre 44 movement. They are NOT interchangeable with:
- Calibre 72 (different architecture, direct jewel press-fit)
- Standard ETA/Sellita movements (different bushing concept)
- Any third-party movement

However, a competent watchmaker CAN turn custom replacement bushings on a lathe if Provident Precision stock is unavailable. The material (phosphor bronze) and dimensions are conventional. This is intentional — the watch remains serviceable even if Provident Precision ceases operations. The specifications in this document are sufficient to reproduce any bushing from raw stock.

---

*Calibre 44 — Bushing System Rev A*
*Provident Precision*
