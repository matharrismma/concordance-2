# Calibre 44 — Crown, Keyless Works & Motion Works

## Detailed Subsystem Specification — Rev A

**Date:** April 7, 2026
**Companion to:** Calibre 44 Movement Spec Rev J.1

---

## 1. System Overview

The crown system has one function: set the time. Pull the crown, turn to set, push in to run. No manual winding position. Three independent seals achieve 100m water resistance.

The setting force path is: crown → stem → sliding pinion → setting wheel → minute wheel → cannon pinion → hands. The same path works in reverse (minute wheel drives hour wheel at 12:1 for the hour hand).

---

## 2. Crown Head

| Parameter | Value |
|---|---|
| Diameter | 6.5 mm |
| Height above case | 2.5 mm (screwed down) |
| Recess depth in case band | 0.5 mm |
| Material | 316L SS |
| Top | Polished, engraved logo |
| Sides | Knurled for grip |
| Thread | M2.0 × 0.25 fine (engages tube) |
| Stem attachment | Tap 0.9 — stem screws into crown base |

When screwed down, the crown head sits in the case band recess. The upper O-ring compresses against the tube exterior, creating the primary water seal. The crown profile is nearly flush with the case band — clean side view on both bracelet and strap.

---

## 3. Crown Tube

| Parameter | Value |
|---|---|
| OD | 2.5 mm |
| ID | 1.2 mm |
| Length | 2.5 mm (extends slightly past inner wall for stem guide) |
| Material | 316L SS |
| External thread | M2.5 × 0.35 (engages crown head) |
| Installation | Threaded into case wall bore with thread-locking compound |
| Static seal | FKM O-ring at tube OD to case bore interface |

The tube is a permanent installation — it stays in the case during service. The stem pulls out through it. The tube bore is polished to Ra 0.4 µm to minimize stem drag and O-ring wear.

### 3.1 Case Bore (at 3 o'clock)

| Parameter | Value |
|---|---|
| Bore diameter | 2.55 mm (clears tube OD with thread) |
| Bore length | 2.0 mm (case wall thickness) |
| O-ring groove | Machined into bore wall, Ø2.8 × 0.3 mm cross-section |
| Position | Radial, perpendicular to case wall at 3 o'clock |
| Axis height | Centered vertically in the movement cavity zone |

---

## 4. Gasket System (100m WR)

Three independent seals. Water must defeat all three to reach the movement.

| Seal | Type | Size | Location | Function |
|---|---|---|---|---|
| Upper crown O-ring | Dynamic | Ø3.5 × CS 0.5 mm, FKM | Crown body groove, seats against tube OD | Primary seal — compressed when crown screwed down |
| Lower crown O-ring | Dynamic | Ø3.5 × CS 0.5 mm, FKM | Crown body groove, seats against tube OD | Secondary seal — wipes stem during pull/push |
| Tube-to-case O-ring | Static | Ø2.8 × CS 0.3 mm, FKM | Groove in case bore wall | Seals tube into case permanently |

All O-rings are standard AS568 or metric sizes, available from any industrial seal supplier. Replacement at every service.

---

## 5. Setting Stem

| Parameter | Value |
|---|---|
| Diameter | 1.0 mm |
| Total length | 9.0 mm |
| Material | Hardened steel |
| Finish | Polished, Ra 0.2 µm |
| Crown end | Tap 0.9 thread (screws into crown base) |
| Movement end | Square section for sliding pinion engagement |

### 5.1 Stem Zones

| Zone | Length | Function |
|---|---|---|
| Crown (external) | 3.0 mm | Inside crown body, screwed in at tap 0.9 |
| Tube (through wall) | 2.0 mm | Passes through crown tube bore |
| Movement (internal) | 4.0 mm | Square section engages sliding pinion and yoke |

### 5.2 Pull Positions

| Position | Stem State | Function |
|---|---|---|
| Pushed in (normal) | Fully seated, crown screwed down | Run — movement operating |
| Crown unscrewed | Crown threads disengaged, stem still seated | Transition — preparing to set |
| Pulled out (1.5 mm) | Stem pulled, sliding pinion engages setting wheel | Set — crown rotation moves hands |

The setting lever provides a tactile click at the set position. The yoke spring returns the stem when pushed back in.

---

## 6. Keyless Works — Inside the Movement

All keyless components sit at the periphery of the movement cavity, near the 3 o'clock case wall, in the space between the center wheel and the case interior.

### 6.1 Components

| Part | Material | Position | Function |
|---|---|---|---|
| Sliding pinion | Hardened steel, Ø2.0 × 3.0 mm | On stem, r ≈ 17 mm from center | Slides along stem to engage setting wheel |
| Setting lever | Steel | Pivot at r ≈ 16 mm | Detent — holds stem in run or set position |
| Yoke | Steel | r ≈ 16.5 mm | Translates stem pull into sliding pinion axial movement |
| Yoke spring | Spring steel, laser-cut | Attached to bridge or unibody | Returns yoke to run position |

### 6.2 Operation

**Run position (crown in):** Sliding pinion is disengaged from the setting wheel. The stem sits freely in the tube. The yoke spring holds the yoke in the run detent. The train runs. The cannon pinion friction-drives the hands.

**Set position (crown pulled 1.5 mm):** The yoke moves the sliding pinion axially along the stem square. The sliding pinion teeth engage the setting wheel. Crown rotation turns the stem, which turns the sliding pinion, which drives the setting wheel, which meshes with the minute wheel, which drives the cannon pinion and hour wheel. Hands move. The train continues to run (no hacking).

**Return to run (crown pushed in):** The yoke spring returns the yoke and sliding pinion to the disengaged position. The setting lever clicks into the run detent. The crown screws down onto the tube, compressing the upper O-ring.

### 6.3 No Hacking

The Calibre 44 does not hack (stop the balance when setting). This eliminates the stop lever, stop lever spring, and the balance contact interface — three parts and a potential damage point on the balance rim. The tradeoff: setting to the second is not possible. For a two-hand watch with no seconds display, this is irrelevant.

---

## 7. Motion Works — Dial Underside Recess

The motion works sit in a 1.0 mm deep recess machined into the underside of the unibody dial surface. They are retained by a thin dial-side plate (304 SS, 0.4 mm thick, two screws).

### 7.1 Gear Data

| Part | Teeth | Module | PD (mm) | Position |
|---|---|---|---|---|
| Cannon pinion | 12T | 0.20 | 2.40 | Center (0, 0) — friction on center arbor |
| Minute wheel | 36T | 0.20 | 7.20 | 9 o'clock, 4.80 mm from center |
| Minute pinion | 10T | 0.20 | 2.00 | Same arbor as minute wheel |
| Hour wheel | 40T | 0.20 | 8.00 | Center (0, 0) — concentric, rides on cannon tube |
| Setting wheel | 24T | 0.20 | 4.80 | ~4 o'clock, 3.60 mm from center |

### 7.2 Ratio

Cannon (12T) → minute wheel (36T) = 3:1 step-up. Minute pinion (10T) → hour wheel (40T) = 4:1 step-up. Total: **12:1** — hour hand makes one revolution per twelve minute-hand revolutions. ✓

### 7.3 Center Distances

| Mesh | Distance |
|---|---|
| Cannon → Minute wheel | 4.80 mm |
| Minute pinion → Hour wheel | 5.00 mm |
| Sliding pinion → Setting wheel | Variable (engaged only when crown pulled) |

### 7.4 Recess Geometry

| Parameter | Value |
|---|---|
| Shape | Irregular pocket, follows wheel extents |
| Maximum radial extent | 8.40 mm from center |
| Depth | 1.00 mm |
| Center bore (through dial) | Ø5.0 mm |
| Retaining plate | 304 SS, 0.4 mm thick, 2 × M0.6 screws |

The center bore passes the cannon pinion tube (minute hand) and the hour wheel pipe (hour hand) from the movement cavity through the dial to the hand side. Both pipes extend approximately 0.5 mm above the dial surface for hand press-fit.

### 7.5 Motion Works Arbor Support

The minute wheel arbor runs in plain bores in the unibody recess floor and the retaining plate — no jewels needed at these low speeds. The setting wheel arbor similarly runs in plain bores. The cannon pinion and hour wheel are self-locating on the center arbor.

---

## 8. Hand Attachment

| Hand | Fits On | Method | Height Above Dial |
|---|---|---|---|
| Hour hand | Hour wheel pipe | Friction press-fit | 0.3 mm |
| Minute hand | Cannon pinion tube | Friction press-fit | 0.6 mm (above hour hand) |

Hands are pressed on after the crystal is removed (or before crystal installation during initial assembly). Standard hand-removal levers for service.

The 0.3 mm clearance between hour hand base and dial surface, plus 0.3 mm between hour and minute hands, gives comfortable clearance in the 0.8 mm hands zone within the crystal step.

---

## 9. Setting Wheel / Crown Interface Detail

When the crown is pulled, the sliding pinion moves axially and its teeth engage the setting wheel. The setting wheel meshes directly with the minute wheel (which is also meshed with the cannon pinion). This means crown rotation drives the minute wheel → cannon pinion → minute hand, and simultaneously the minute wheel → minute pinion → hour wheel → hour hand, maintaining the 12:1 relationship.

The setting wheel is positioned at ~4 o'clock (3.60 mm from center) so that:
- It meshes cleanly with the minute wheel at 9 o'clock when engaged
- The sliding pinion travel path from the 3 o'clock stem position reaches it
- It clears the center wheel below in the movement cavity

Setting torque at the crown: approximately 20–40 mN·m (light, positive feel). Cannon pinion pull-off force: 20–30 N (holds hands during normal operation, releases for hand-setting pressure).

---

## 10. Parts Summary — Crown & Setting System

| Part | Qty | Material | New or Existing |
|---|---|---|---|
| Crown head | 1 | 316L SS | Per case spec |
| Crown tube | 1 | 316L SS | Per case spec |
| Crown O-rings | 2 | FKM | Consumable |
| Tube O-ring | 1 | FKM | Consumable |
| Setting stem | 1 | Hardened steel | Existing (movement spec #6) |
| Sliding pinion | 1 | Hardened steel | Existing (#35) |
| Setting lever | 1 | Steel | Existing (#36) |
| Yoke | 1 | Steel | Existing (#37) |
| Yoke spring | 1 | Spring steel | Existing (#38) |
| Setting wheel | 1 | Brass | Existing (#19) |
| Cannon pinion | 1 | Brass | Existing (#16) |
| Minute wheel | 1 | Brass | Existing (#17) |
| Hour wheel | 1 | Brass | Existing (#18) |
| Retaining plate | 1 | 304 SS | Existing (#20) |

No new parts — this spec details components already counted in the movement manifest.

---

## 11. Service Notes

### 11.1 Crown and Gaskets

Replace all three O-rings at every service (10–15 years). Inspect crown thread for wear or cross-threading. Inspect tube bore for scoring. If tube is damaged, it can be unscrewed and replaced without affecting the unibody.

### 11.2 Stem

Inspect stem for bending or wear at the square section. Replace if the sliding pinion engagement feels loose. Stem is a commodity part — hardened steel rod, turned to spec.

### 11.3 Cannon Pinion

If hands slip during normal wear (cannon pinion friction too low), replace the cannon pinion. If hands are too tight to set (friction too high), the cannon tube can be slightly opened with a broach. Target pull-off force: 20–30 N tested with a spring gauge.

### 11.4 Water Resistance Test

After any service involving the crown, tube, or caseback: full ISO 22810 wet test or condensation test to verify 100m rating before returning to owner.

---

## 12. Open Items (Crown/Keyless Specific)

| # | Item | Status |
|---|---|---|
| 1 | Crown head detailed drawing — knurl pattern, logo engraving | Detail design |
| 2 | Crown tube thread engagement length — verify 100m seal | Engineering |
| 3 | Sliding pinion tooth profile — engagement feel and backlash | Detail design |
| 4 | Setting lever detent geometry — click force and overtravel | Detail design |
| 5 | Yoke spring rate — sufficient return force without excessive pull effort | Engineering |
| 6 | Cannon pinion friction specification — pull-off force 20–30 N | Prototype |
| 7 | Setting wheel position confirmation — verify mesh with minute wheel | CAD |

---

*Calibre 44 — Crown, Keyless & Motion Works Rev A*
*Provident Precision*
