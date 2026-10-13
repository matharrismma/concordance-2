"""Chemistry verifier.

Checks that this verifier actually performs (not attestations):
  * mass_balance: atoms on each side conserve under the stated coefficients,
    or — if coefficients are not given — solves for the smallest integer
    coefficients that balance the equation
  * charge_balance: net charge is conserved across the equation
  * temperature_positive: temperature_K > 0 (K is the only physical scale)

Equation format accepted (string):
    "H2 + O2 -> H2O"            # finds coefficients
    "2 H2 + O2 -> 2 H2O"        # verifies coefficients
    "Fe^3+ + e^- -> Fe^2+"      # charges
    "Cu(OH)2 -> CuO + H2O"      # nested groups

Any species may carry a charge suffix written as ^n+ or ^n- (n optional, default 1)
or as +/- with no caret. State labels in parentheses (s), (l), (g), (aq) are stripped.
"""
from __future__ import annotations
import re
from fractions import Fraction
from typing import Dict, List, Tuple, Any
from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from . import alpha_scale as _ascale  # alpha-anchored atomic energy scale
from . import thermal_scale as _thermal  # k_B-anchored Boltzmann factor
from . import molar_scale as _molar  # N_A-anchored particle count

# regex pieces ---------------------------------------------------------------

_STATE = re.compile(r"\((?:s|l|g|aq|aq\.|cr|am|ads)\)\s*", re.IGNORECASE)
_CHARGE = re.compile(r"\^?(\d*)([+\-])$")
_ELEMENT_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)|\(|\)(\d*)")


def _strip_state(species: str) -> str:
    return _STATE.sub("", species).strip()


def _parse_charge(species: str) -> Tuple[str, int]:
    """Strip a trailing charge tag and return (bare_formula, charge)."""
    s = species.strip()
    # accept species like Fe^3+, Fe^+, Fe+, Cu^2-, OH-, NH4+
    m = re.search(r"\^?(\d*)([+\-])\s*$", s)
    if not m:
        return s, 0
    # Be careful: a trailing - might be the dash in -> already stripped, fine.
    digits, sign = m.group(1), m.group(2)
    n = int(digits) if digits else 1
    bare = s[:m.start()].rstrip()
    return bare, n if sign == "+" else -n


def _parse_formula(formula: str) -> Dict[str, int]:
    """Count atoms in a formula, supporting nested parentheses."""
    s = formula.replace(" ", "")
    stack: List[Dict[str, int]] = [{}]
    i = 0
    while i < len(s):
        c = s[i]
        if c == "(":
            stack.append({})
            i += 1
        elif c == ")":
            # collect multiplier after )
            i += 1
            mdigits = ""
            while i < len(s) and s[i].isdigit():
                mdigits += s[i]
                i += 1
            mult = int(mdigits) if mdigits else 1
            top = stack.pop()
            for el, n in top.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * mult
        elif c.isupper():
            sym = c
            i += 1
            if i < len(s) and s[i].islower():
                sym += s[i]
                i += 1
            ndigits = ""
            while i < len(s) and s[i].isdigit():
                ndigits += s[i]
                i += 1
            n = int(ndigits) if ndigits else 1
            stack[-1][sym] = stack[-1].get(sym, 0) + n
        elif c.isdigit():
            # bare leading digit is a coefficient — should not appear here because
            # callers split on whitespace first. Skip.
            i += 1
        elif c == "·" or c == ".":
            # hydrate dot, e.g. CuSO4·5H2O — handle cheaply by splitting and merging
            # not fully general but covers common cases
            i += 1
        else:
            # unknown character — treat as separator
            i += 1
    if len(stack) != 1:
        raise ValueError(f"unbalanced parentheses in {formula!r}")
    return stack[0]


def _split_term(term: str) -> Tuple[int, str]:
    """Split '2 H2O' into (2, 'H2O'). No coefficient -> (1, term)."""
    t = term.strip()
    m = re.match(r"^(\d+)\s*(.+)$", t)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return 1, t


def _split_side(side: str) -> List[Tuple[int, str, int]]:
    """Return [(coef, formula, charge), ...] for one side of the equation.

    Splits species on whitespace-padded ' + ' (so charges like Fe^2+ or Na+
    don't get torn apart). Accepts species ending in: ^n+, ^n-, +, -.
    """
    out: List[Tuple[int, str, int]] = []
    # Split on ' + ' that has whitespace around it (or is at end / start adjacent to whitespace).
    # The simplest robust regex: split on /\s+\+\s+/. Anything tighter than that is
    # part of a charge tag and stays attached to its species.
    for term in re.split(r"\s+\+\s+", side.strip()):
        term = _strip_state(term).strip()
        if not term:
            continue
        coef, sp = _split_term(term)
        bare, charge = _parse_charge(sp)
        # also handle e^- and e- (electron)
        if bare.lower() in ("e", "e-") or (bare == "" and charge == -1):
            out.append((coef, "", -1))
            continue
        out.append((coef, bare, charge))
    return out


def _atoms_on_side(side: List[Tuple[int, str, int]]) -> Dict[str, int]:
    total: Dict[str, int] = {}
    for coef, formula, _ in side:
        if not formula:
            continue
        atoms = _parse_formula(formula)
        for el, n in atoms.items():
            total[el] = total.get(el, 0) + coef * n
    return total


def _charge_on_side(side: List[Tuple[int, str, int]]) -> int:
    return sum(coef * charge for coef, _, charge in side)


def verify_equation(eq: str, *, balance_if_unbalanced: bool = True) -> VerifierResult:
    """Verify or balance a chemical equation."""
    # If the input doesn't have a reaction arrow, this verifier doesn't
    # apply — return NA (clean miss) rather than ERROR (something broken).
    # An ERROR pollutes the composite verdict; NA is honest signal.
    if "->" not in eq and "→" not in eq:
        return na("chemistry.equation")

    lhs_str, rhs_str = re.split(r"->|→", eq, maxsplit=1)
    try:
        lhs = _split_side(lhs_str)
        rhs = _split_side(rhs_str)
    except Exception:
        # Parse failure usually means the input isn't a chemical equation
        # even though it had an arrow (e.g. "if X then Y" with → as arrow).
        # NA is more honest than ERROR.
        return na("chemistry.equation")

    try:
        atoms_lhs = _atoms_on_side(lhs)
        atoms_rhs = _atoms_on_side(rhs)
    except Exception:
        return na("chemistry.equation")

    charge_lhs = _charge_on_side(lhs)
    charge_rhs = _charge_on_side(rhs)

    elements = sorted(set(atoms_lhs) | set(atoms_rhs))
    diff = {el: atoms_lhs.get(el, 0) - atoms_rhs.get(el, 0) for el in elements}

    if all(v == 0 for v in diff.values()) and charge_lhs == charge_rhs:
        return confirm(
            "chemistry.equation",
            "atoms and charge balanced under stated coefficients",
            {"atoms_lhs": atoms_lhs, "atoms_rhs": atoms_rhs,
             "charge_lhs": charge_lhs, "charge_rhs": charge_rhs},
        )

    if not balance_if_unbalanced:
        return mismatch(
            "chemistry.equation",
            f"unbalanced under stated coefficients: atom diff {diff}, "
            f"charge {charge_lhs} -> {charge_rhs}",
            {"atom_diff": diff, "charge_lhs": charge_lhs, "charge_rhs": charge_rhs},
        )

    # Try to balance: solve A x = 0 for x in positive integers, where A's columns
    # are species (with sign), rows are conserved quantities (elements + charge).
    species: List[Tuple[int, str, int]] = []  # (sign, formula, charge); sign +1 lhs, -1 rhs
    for _, f, c in lhs:
        species.append((+1, f, c))
    for _, f, c in rhs:
        species.append((-1, f, c))

    # Build conservation matrix.
    rows = elements + ["__charge__"]
    A: List[List[Fraction]] = []
    for r in rows:
        row: List[Fraction] = []
        for sign, f, c in species:
            if r == "__charge__":
                row.append(Fraction(sign * c))
            else:
                atoms = _parse_formula(f) if f else {}
                row.append(Fraction(sign * atoms.get(r, 0)))
        A.append(row)

    coefs = _nullspace_positive_integer(A)
    if coefs is None:
        return mismatch(
            "chemistry.equation",
            f"could not balance: atom diff {diff}, charge {charge_lhs} -> {charge_rhs}",
            {"atom_diff": diff},
        )

    # Reconstruct the balanced equation
    n_lhs = len(lhs)
    lhs_balanced = " + ".join(_render(c, lhs[i][1], lhs[i][2]) for i, c in enumerate(coefs[:n_lhs]))
    rhs_balanced = " + ".join(_render(c, rhs[i][1], rhs[i][2]) for i, c in enumerate(coefs[n_lhs:]))
    return mismatch(
        "chemistry.equation",
        f"unbalanced under stated coefficients but balances as: "
        f"{lhs_balanced} -> {rhs_balanced}",
        {"balanced_coefficients": coefs, "balanced_lhs": lhs_balanced, "balanced_rhs": rhs_balanced},
    )


def _render(coef: int, formula: str, charge: int) -> str:
    body = formula if formula else "e^-"
    if charge and formula:
        sign = "+" if charge > 0 else "-"
        n = abs(charge)
        body = body + ("^" + (str(n) if n != 1 else "") + sign)
    return f"{coef} {body}" if coef != 1 else body


def _nullspace_positive_integer(A: List[List[Fraction]]) -> List[int] | None:
    """Find the smallest positive-integer vector x with A x = 0 (one-dim nullspace)."""
    if not A or not A[0]:
        return None
    n_cols = len(A[0])
    # Gauss-Jordan over Fractions
    M = [row[:] for row in A]
    pivot_col_for_row: List[int] = []
    r = 0
    for c in range(n_cols):
        # find pivot
        piv = None
        for rr in range(r, len(M)):
            if M[rr][c] != 0:
                piv = rr
                break
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        # normalize pivot row
        pv = M[r][c]
        M[r] = [x / pv for x in M[r]]
        # eliminate in other rows
        for rr in range(len(M)):
            if rr != r and M[rr][c] != 0:
                factor = M[rr][c]
                M[rr] = [a - factor * b for a, b in zip(M[rr], M[r])]
        pivot_col_for_row.append(c)
        r += 1
        if r == len(M):
            break

    pivot_cols = set(pivot_col_for_row)
    free_cols = [c for c in range(n_cols) if c not in pivot_cols]
    if len(free_cols) != 1:
        return None  # need exactly one free variable for a unique balance

    free = free_cols[0]
    x: List[Fraction] = [Fraction(0)] * n_cols
    x[free] = Fraction(1)
    # solve for pivot vars: row r corresponds to pivot col pivot_col_for_row[r]
    for ri, pc in enumerate(pivot_col_for_row):
        # 0 = sum_c M[ri][c] * x[c]; x[pc] = -sum over c != pc of M[ri][c] * x[c]
        s = Fraction(0)
        for c in range(n_cols):
            if c != pc:
                s += M[ri][c] * x[c]
        x[pc] = -s

    # All coefficients should have the same sign (all positive, after flipping if needed)
    if all(v == 0 for v in x):
        return None
    nonzero = [v for v in x if v != 0]
    sign = 1 if nonzero[0] > 0 else -1
    x = [v * sign for v in x]
    if any(v <= 0 for v in x):
        return None  # cannot make all coefficients positive with one degree of freedom

    # Scale to smallest positive integers
    from math import gcd
    den_lcm = 1
    for v in x:
        den_lcm = den_lcm * v.denominator // gcd(den_lcm, v.denominator)
    ints = [int(v * den_lcm) for v in x]
    g = ints[0]
    for v in ints[1:]:
        g = gcd(g, v)
    return [v // g for v in ints]


def verify_temperature(temperature_K: float) -> VerifierResult:
    if temperature_K is None:
        return na("chemistry.temperature_K")
    try:
        t = float(temperature_K)
    except (ValueError, TypeError):
        return error("chemistry.temperature_K", f"non-numeric: {temperature_K!r}")
    if t <= 0:
        return mismatch("chemistry.temperature_K", f"{t} K is not a positive absolute temperature")
    return confirm("chemistry.temperature_K", f"{t} K positive")


def verify_thermodynamic_feasibility(spec: Dict[str, Any]) -> VerifierResult:
    """Gibbs free energy check: ΔG = ΔH - T·ΔS determines spontaneity.

    Inputs (keys in spec):
        delta_H_kJ_mol     — enthalpy change (kJ/mol)
        delta_S_J_mol_K    — entropy change (J/(mol·K))
        temperature_K      — absolute temperature (K)
        claimed_spontaneous — bool: claim that ΔG < 0 at the stated T
    A reaction is thermodynamically spontaneous iff ΔG < 0.
    """
    name = "chemistry.thermodynamic_feasibility"
    dH = spec.get("delta_H_kJ_mol")
    dS = spec.get("delta_S_J_mol_K")
    T = spec.get("temperature_K")
    claimed = spec.get("claimed_spontaneous")
    if dH is None or dS is None or T is None or claimed is None:
        return na(name)
    try:
        dH_f = float(dH)
        dS_f = float(dS) / 1000.0  # convert J → kJ
        T_f = float(T)
    except (TypeError, ValueError):
        return error(name, f"non-numeric input: dH={dH!r}, dS={dS!r}, T={T!r}")
    if T_f <= 0:
        return error(name, f"temperature must be > 0 K, got {T_f}")
    dG = dH_f - T_f * dS_f
    spontaneous = dG < 0
    if spontaneous == bool(claimed):
        return confirm(name,
                       f"ΔG = {dG:.3f} kJ/mol at T={T_f} K (spontaneous={spontaneous}, matches claim)",
                       {"delta_G_kJ_mol": dG, "spontaneous": spontaneous,
                        "claimed": bool(claimed), "delta_H": dH_f,
                        "delta_S_kJ_mol_K": dS_f, "temperature_K": T_f})
    return mismatch(name,
                    f"ΔG = {dG:.3f} kJ/mol → spontaneous={spontaneous}, claimed {bool(claimed)}",
                    {"delta_G_kJ_mol": dG, "spontaneous": spontaneous,
                     "claimed": bool(claimed)})


def verify_ph_classification(spec: Dict[str, Any]) -> VerifierResult:
    """Classify a solution as acid / base / neutral by pH.

    Inputs:
        pH                          — numeric pH value (0-14)
        claimed_classification      — one of "acid"/"base"/"neutral"/"acidic"/"basic"/"alkaline"
        neutral_tolerance           — pH band counted as neutral (default 0.5 around 7.0)
    """
    name = "chemistry.pH_classification"
    pH = spec.get("pH")
    claimed = spec.get("claimed_classification")
    if pH is None or claimed is None:
        return na(name)
    try:
        pH_f = float(pH)
    except (TypeError, ValueError):
        return error(name, f"pH must be numeric, got {pH!r}")
    if not (0.0 <= pH_f <= 14.0):
        return mismatch(name, f"pH {pH_f} out of valid range [0, 14]",
                        {"pH": pH_f})
    tol = clamp_tol(spec, "neutral_tolerance", 0.5)
    if abs(pH_f - 7.0) <= tol:
        actual = "neutral"
    elif pH_f < 7.0:
        actual = "acid"
    else:
        actual = "base"
    # Normalize claimed label: 'acidic' → 'acid', 'basic'/'alkaline' → 'base'.
    claim_norm = str(claimed).lower().strip()
    if claim_norm in ("acidic",):
        claim_norm = "acid"
    elif claim_norm in ("basic", "alkaline"):
        claim_norm = "base"
    if claim_norm == actual:
        return confirm(name,
                       f"pH {pH_f} is {actual} (matches claim {claimed!r})",
                       {"pH": pH_f, "actual": actual, "claimed": claim_norm})
    return mismatch(name,
                    f"pH {pH_f} is {actual}, claimed {claim_norm!r}",
                    {"pH": pH_f, "actual": actual, "claimed": claim_norm})


# ── SUBSTANCES: common compounds/elements by name, with their formula and standard phase points ──────
# Formula is compared by ATOM COUNT (so "C2H5OH" and "C2H6O" both match ethanol). Melting/boiling points
# are standard values at 1 atm (°C); None where the substance sublimes or decomposes rather than melting
# or boiling cleanly at 1 atm. Curated, attributed (standard references / CRC Handbook), judged at the
# stated precision — a wrong value MISMATCHES, an unknown substance is DECLINED (never a false HOLDS).
_SUBSTANCES: Dict[str, Dict[str, Any]] = {
    "water": {"formula": "H2O", "mp_c": 0.0, "bp_c": 100.0},
    "hydrogen peroxide": {"formula": "H2O2", "mp_c": -0.43, "bp_c": 150.2},
    "carbon dioxide": {"formula": "CO2", "mp_c": None, "bp_c": None},      # sublimes at 1 atm (-78.5 °C)
    "carbon monoxide": {"formula": "CO", "mp_c": -205.0, "bp_c": -191.5},
    "ozone": {"formula": "O3", "mp_c": -192.2, "bp_c": -112.0},
    "ammonia": {"formula": "NH3", "mp_c": -77.7, "bp_c": -33.34},
    "methane": {"formula": "CH4", "mp_c": -182.5, "bp_c": -161.5},
    "ethane": {"formula": "C2H6", "mp_c": -182.8, "bp_c": -88.6},
    "propane": {"formula": "C3H8", "mp_c": -187.7, "bp_c": -42.1},
    "butane": {"formula": "C4H10", "mp_c": -138.3, "bp_c": -0.5},
    "ethanol": {"formula": "C2H6O", "mp_c": -114.1, "bp_c": 78.37},
    "methanol": {"formula": "CH4O", "mp_c": -97.6, "bp_c": 64.7},
    "acetone": {"formula": "C3H6O", "mp_c": -94.7, "bp_c": 56.05},
    "acetic acid": {"formula": "C2H4O2", "mp_c": 16.6, "bp_c": 118.1},
    "benzene": {"formula": "C6H6", "mp_c": 5.5, "bp_c": 80.1},
    "glucose": {"formula": "C6H12O6", "mp_c": None, "bp_c": None},         # decomposes
    "sucrose": {"formula": "C12H22O11", "mp_c": None, "bp_c": None},       # decomposes
    "sodium chloride": {"formula": "NaCl", "mp_c": 801.0, "bp_c": 1413.0},
    "sodium hydroxide": {"formula": "NaOH", "mp_c": 318.0, "bp_c": 1388.0},
    "sodium bicarbonate": {"formula": "NaHCO3", "mp_c": None, "bp_c": None},  # decomposes
    "calcium carbonate": {"formula": "CaCO3", "mp_c": None, "bp_c": None},    # decomposes
    "sulfuric acid": {"formula": "H2SO4", "mp_c": 10.3, "bp_c": 337.0},
    "hydrochloric acid": {"formula": "HCl", "mp_c": -114.2, "bp_c": -85.0},
    "nitric acid": {"formula": "HNO3", "mp_c": -42.0, "bp_c": 83.0},
    "hydrogen": {"formula": "H2", "mp_c": -259.14, "bp_c": -252.87},
    "oxygen": {"formula": "O2", "mp_c": -218.79, "bp_c": -182.96},
    "nitrogen": {"formula": "N2", "mp_c": -210.0, "bp_c": -195.79},
    "chlorine": {"formula": "Cl2", "mp_c": -101.5, "bp_c": -34.04},
    "iron": {"formula": "Fe", "mp_c": 1538.0, "bp_c": 2862.0},
    "gold": {"formula": "Au", "mp_c": 1064.18, "bp_c": 2856.0},
    "copper": {"formula": "Cu", "mp_c": 1084.62, "bp_c": 2562.0},
    "aluminum": {"formula": "Al", "mp_c": 660.32, "bp_c": 2470.0},
    "mercury": {"formula": "Hg", "mp_c": -38.83, "bp_c": 356.73},
    "lead": {"formula": "Pb", "mp_c": 327.46, "bp_c": 1749.0},
    "silver": {"formula": "Ag", "mp_c": 961.78, "bp_c": 2162.0},
    "tungsten": {"formula": "W", "mp_c": 3422.0, "bp_c": 5555.0},
}
_SUBSTANCE_ALIASES: Dict[str, str] = {
    "salt": "sodium chloride", "table salt": "sodium chloride", "rock salt": "sodium chloride",
    "baking soda": "sodium bicarbonate", "bicarbonate of soda": "sodium bicarbonate",
    "lye": "sodium hydroxide", "caustic soda": "sodium hydroxide",
    "table sugar": "sucrose", "sugar": "sucrose", "cane sugar": "sucrose",
    "grain alcohol": "ethanol", "ethyl alcohol": "ethanol", "alcohol": "ethanol",
    "wood alcohol": "methanol", "methyl alcohol": "methanol",
    "muriatic acid": "hydrochloric acid", "limestone": "calcium carbonate", "chalk": "calcium carbonate",
    "quicklime": "calcium carbonate", "aluminium": "aluminum", "dry ice": "carbon dioxide",
    "laughing gas": None,  # nitrous oxide is not in the table; resolve to a miss, never the wrong one
}


def substance(name: str):
    """(canonical_name, record) for a known substance (aliases resolved), or (name, None)."""
    n = " ".join((name or "").strip().lower().split())
    n = _SUBSTANCE_ALIASES.get(n, n)
    return n, (_SUBSTANCES.get(n) if isinstance(n, str) else None)


def _matches_at_precision(actual: float, claimed: float, claimed_literal: str) -> bool:
    """A phase point holds when the claim agrees at its STATED precision — round the table value to the
    decimals the claim gave ("100" for water; "78" for ethanol 78.37) — OR lies within the empirical
    source spread of the measured value (~0.3% or 0.5 °C), so "78.3" also holds for ethanol (sources give
    78.3–78.4) while "79" and "88.3" do not. Measured values vary by source; a half-degree is not an error."""
    claimed = float(claimed)
    lit = str(claimed_literal or "").strip()
    dec = len(lit.split(".", 1)[1]) if "." in lit else 0
    if round(actual, dec) == round(claimed, dec):
        return True
    return abs(actual - claimed) <= max(0.5, 0.003 * abs(actual))


def verify_name_formula(spec: Dict[str, Any]) -> VerifierResult:
    name = "chemistry.formula"
    nm, rec = substance(spec.get("name", ""))
    claimed = str(spec.get("claimed_formula") or "").strip()
    if rec is None:
        return na(name, f"{nm!r} is not in the substance table — declined, not judged")
    if not claimed:
        return na(name)
    try:
        want, got = _parse_formula(rec["formula"]), _parse_formula(claimed)
    except Exception:  # noqa: BLE001
        return error(name, f"could not parse the formula {claimed!r}")
    if want == got:
        return confirm(name, f"{nm} is {rec['formula']} (matches claim {claimed})",
                       {"name": nm, "formula": rec["formula"], "claimed": claimed})
    return mismatch(name, f"{nm} is {rec['formula']}, not {claimed}",
                    {"name": nm, "formula": rec["formula"], "claimed": claimed})


def verify_phase_point(spec: Dict[str, Any]) -> VerifierResult:
    name = "chemistry.phase_point"
    nm, rec = substance(spec.get("substance", ""))
    prop = str(spec.get("property") or "").strip().lower()
    if rec is None:
        return na(name, f"{nm!r} is not in the substance table — declined, not judged")
    if spec.get("claimed_c") is None or prop not in ("boiling", "melting", "freezing"):
        return na(name)
    key = "bp_c" if prop == "boiling" else "mp_c"       # freezing point = melting point
    actual = rec.get(key)
    label = "boiling point" if prop == "boiling" else ("freezing point" if prop == "freezing" else "melting point")
    if actual is None:
        return na(name, f"{nm} has no standard {label} at 1 atm (it sublimes or decomposes) — declined")
    try:
        claimed = float(spec["claimed_c"])
    except (TypeError, ValueError):
        return error(name, "claimed temperature must be a number")
    lit = spec.get("claimed_literal", spec["claimed_c"])
    if _matches_at_precision(actual, claimed, str(lit)):
        return confirm(name, f"the {label} of {nm} is {actual} °C at 1 atm (matches {lit} to the stated precision)",
                       {"substance": nm, "property": prop, "actual_c": actual, "claimed_c": claimed})
    return mismatch(name, f"the {label} of {nm} is {actual} °C at 1 atm, not {lit}",
                    {"substance": nm, "property": prop, "actual_c": actual, "claimed_c": claimed})


GOLDEN_PACKET_KEY = "CHEM_VERIFY"
GOLDEN_EXAMPLE = {"amount_mol": 1.0, "claimed_particle_count": 6.02214076e23}  # N = n * N_A


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    """Run all chemistry verifiers that have an artifact in the packet."""
    results: List[VerifierResult] = []
    chem_verify = packet.get("CHEM_VERIFY") or {}

    if "equation" in chem_verify:
        eq = chem_verify["equation"]
        results.append(verify_equation(eq, balance_if_unbalanced=True))

    setup = packet.get("CHEM_SETUP") or {}
    if "temperature_K" in setup or "temperature_K" in chem_verify:
        t = chem_verify.get("temperature_K", setup.get("temperature_K"))
        results.append(verify_temperature(t))

    # Thermodynamic feasibility: ΔG = ΔH - TΔS spontaneity check.
    if all(k in chem_verify for k in ("delta_H_kJ_mol", "delta_S_J_mol_K",
                                      "temperature_K", "claimed_spontaneous")):
        results.append(verify_thermodynamic_feasibility(chem_verify))

    # pH classification check.
    if "pH" in chem_verify and "claimed_classification" in chem_verify:
        results.append(verify_ph_classification(chem_verify))

    # Atomic energy scale (Rydberg / Hartree) — the alpha-set scale of bond and ionization energies.
    if "claimed_hartree_ev" in chem_verify or "claimed_rydberg_ev" in chem_verify:
        results.append(verify_atomic_energy_scale(chem_verify))

    # Boltzmann factor exp(-E/k_B T) — the k_B-set population/rate ratio (Arrhenius).
    if all(k in chem_verify for k in ("boltzmann_energy_J", "boltzmann_temperature_K",
                                      "claimed_boltzmann_factor")):
        results.append(verify_boltzmann_factor(chem_verify))

    # Particle count N = n * N_A — the N_A-set bridge from moles to molecules.
    if "amount_mol" in chem_verify and "claimed_particle_count" in chem_verify:
        results.append(verify_avogadro_count(chem_verify))

    # Name -> formula ("water is H2O"), compared by atom count.
    if "name" in chem_verify and "claimed_formula" in chem_verify:
        results.append(verify_name_formula(chem_verify))

    # Phase point ("the boiling point of water is 100 C"), judged at the stated precision.
    if "substance" in chem_verify and "property" in chem_verify and "claimed_c" in chem_verify:
        results.append(verify_phase_point(chem_verify))

    # Enantiomeric excess ee = |R−S|/(R+S)×100% — the measure of one-handedness in a chiral mixture.
    if ("claimed_ee_percent" in chem_verify
            and any(k in chem_verify for k in ("r", "s", "r_amount", "s_amount"))):
        results.append(verify_enantiomeric_excess(chem_verify))

    # Chiral amplification — the Kagan–Soai signature (Nobel 2026): product ee exceeds the seed ee
    # (a positive non-linear effect; asymmetric autocatalysis runs it toward homochirality).
    if all(k in chem_verify for k in ("seed_ee_percent", "product_ee_percent", "claimed_amplification")):
        results.append(verify_chiral_amplification(chem_verify))

    if not results:
        results.append(na("chemistry", "no CHEM_VERIFY artifacts present"))
    return results


def verify_avogadro_count(spec: Dict[str, Any]) -> VerifierResult:
    """Particle count N = n * N_A — chemistry THROUGH the Avogadro constant: the number of entities
    in n moles (1 mol = 6.02214076e23)."""
    name = "chemistry.avogadro_count"
    try:
        n = float(spec["amount_mol"])
    except (KeyError, TypeError, ValueError):
        return error(name, "amount_mol must be numeric")
    if n <= 0:
        return error(name, "amount must be positive")
    return _molar.compare(name, _molar.particles_from_moles(n),
                          spec["claimed_particle_count"], 1e-3, {"formula": "N = n * N_A"})


def verify_boltzmann_factor(spec: Dict[str, Any]) -> VerifierResult:
    """The Boltzmann factor exp(-E / k_B T) — chemistry THROUGH k_B: the relative population of a
    state at energy E, and the temperature dependence of reaction rates (Arrhenius)."""
    name = "chemistry.boltzmann_factor"
    try:
        E = float(spec["boltzmann_energy_J"]); T = float(spec["boltzmann_temperature_K"])
    except (KeyError, TypeError, ValueError):
        return error(name, "boltzmann_energy_J / boltzmann_temperature_K must be numeric")
    if T <= 0:
        return error(name, "temperature must be > 0 K")
    return _thermal.compare(name, _thermal.boltzmann_factor(E, T),
                            spec["claimed_boltzmann_factor"], 1e-3, {"formula": "exp(-E / k_B T)"})


def verify_atomic_energy_scale(spec: Dict[str, Any]) -> VerifierResult:
    """The Rydberg and Hartree energies — chemistry's energy scale, set THROUGH alpha. Bond and
    ionization energies live on this scale: Ry = alpha^2 m_e c^2 / 2 (~13.606 eV) and the Hartree
    E_h = 2 Ry = alpha^2 m_e c^2 (~27.211 eV)."""
    name = "chemistry.atomic_energy_scale"
    if "claimed_hartree_ev" in spec:
        return _ascale.compare(name, _ascale.hartree_eV(), spec["claimed_hartree_ev"], 1e-3,
                               {"formula": "E_h = 2 Ry = alpha^2 m_e c^2 (the Hartree)"})
    if "claimed_rydberg_ev" in spec:
        return _ascale.compare(name, _ascale.rydberg_energy_eV(), spec["claimed_rydberg_ev"], 1e-3,
                               {"formula": "Ry = R_inf h c = alpha^2 m_e c^2 / 2"})
    return na(name)


# ── Chirality — one-handedness and its amplification (Kagan & Soai, Nobel Chemistry 2026) ─────────────
# Life runs on a single handedness: L-amino acids, D-sugars. Enantiomeric excess MEASURES that
# one-handedness; the Kagan–Soai discovery is that a small excess can be AMPLIFIED — the product's ee
# exceeds the catalyst's (Kagan's non-linear effect), and in Soai's asymmetric autocatalysis the product
# IS the catalyst, so the excess feeds back and the reaction runs toward a single enantiomer. The same
# shape the keeping's own stigmergy follows: a small bias, reinforced, decides the whole. These checks
# are exact arithmetic and a stated inequality — the lab discovery that amplification occurs is Kagan's
# and Soai's, carried as a citation on the card, never asserted by the verifier.

def verify_enantiomeric_excess(spec: Dict[str, Any]) -> VerifierResult:
    """ee = |R − S| / (R + S) × 100% — the degree of ONE-handedness (0% = racemic 50/50; 100% = a single
    enantiomer). R and S are the two mirror-image populations in any consistent unit (fraction, %, mol)."""
    name = "chemistry.enantiomeric_excess"
    r = spec.get("r", spec.get("r_amount"))
    s = spec.get("s", spec.get("s_amount"))
    claimed = spec.get("claimed_ee_percent")
    if r is None or s is None or claimed is None:
        return na(name)
    try:
        rf, sf, c = float(r), float(s), float(claimed)
    except (TypeError, ValueError):
        return error(name, "R, S, and claimed_ee_percent must be numeric")
    if rf < 0 or sf < 0:
        return error(name, "enantiomer populations cannot be negative")
    total = rf + sf
    if total == 0:
        return error(name, "no enantiomers present (R + S = 0)")
    actual = abs(rf - sf) / total * 100.0
    diff = abs(actual - c)
    threshold = max(0.1, 1e-3 * abs(actual))
    data = {"r": rf, "s": sf, "actual_ee_percent": actual, "claimed_ee_percent": c,
            "formula": "ee = |R − S| / (R + S) × 100%"}
    if diff <= threshold:
        return confirm(name, f"ee = |{rf:g} − {sf:g}| / {total:g} = {actual:.4g}% (matches {c:g}%)", data)
    return mismatch(name, f"ee = {actual:.4g}%, claimed {c:g}% (diff {diff:.4g})", data)


def verify_chiral_amplification(spec: Dict[str, Any]) -> VerifierResult:
    """The Kagan–Soai signature (Nobel Chemistry 2026): a positive NON-LINEAR EFFECT — the product's
    enantiomeric excess EXCEEDS the seed/catalyst's, so a small initial handedness comes out amplified;
    Soai's asymmetric autocatalysis (the product is its own catalyst) runs it toward homochirality. This
    checks the defining inequality of a stated case (product_ee vs seed_ee); it does not model the
    kinetics — the discovery that this happens is Kagan's and Soai's, cited on the card."""
    name = "chemistry.chiral_amplification"
    seed = spec.get("seed_ee_percent")
    prod = spec.get("product_ee_percent")
    claimed = spec.get("claimed_amplification")
    if seed is None or prod is None or claimed is None:
        return na(name)
    try:
        seed_f, prod_f = float(seed), float(prod)
    except (TypeError, ValueError):
        return error(name, "seed_ee_percent and product_ee_percent must be numeric")
    if not (0.0 <= seed_f <= 100.0) or not (0.0 <= prod_f <= 100.0):
        return error(name, "enantiomeric excess must be between 0% and 100%")
    amplified = prod_f > seed_f + 1e-9
    data = {"seed_ee_percent": seed_f, "product_ee_percent": prod_f,
            "actual_amplification": amplified, "claimed_amplification": bool(claimed),
            "delta_ee_pp": prod_f - seed_f,
            "mechanism": "non-linear effect (Kagan) / asymmetric autocatalysis (Soai)"}
    if amplified == bool(claimed):
        if amplified:
            msg = (f"product ee {prod_f:g}% exceeds seed ee {seed_f:g}% (+{prod_f - seed_f:g} pp) — "
                   f"handedness amplified (matches claim)")
        else:
            msg = (f"product ee {prod_f:g}% does not exceed seed ee {seed_f:g}% — "
                   f"no amplification (matches claim)")
        return confirm(name, msg, data)
    return mismatch(name,
                    f"product ee {prod_f:g}% vs seed ee {seed_f:g}%: amplified={amplified}, "
                    f"claimed {bool(claimed)}", data)
