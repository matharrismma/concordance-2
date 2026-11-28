"""THE WINDOW IS THE SCALE OF THE QUANTITY, NEVER A FLAT FLOOR (2026-11-27).

Numeric mode compared with `threshold = rel_tol * max(1.0, abs(computed))`, which is relative above 1 and a flat
ABSOLUTE 1e-9 below it. For a quantity far under the tolerance that window swallowed every claim: the live public door
confirmed "the Planck constant is 0", "is 7e-34", "is 1e-20" and "is 1e-9" alike - twenty-five orders of magnitude of
wrong, inside the 0-FP spine. The same idiom sat in `base.window_for`, whose default ten verifiers inherit,
`physical_constants` and `units` among them, so "the elementary charge is 0 coulombs" HELD.

The window is now PEP 485's weak form, which is `math.isclose(claimed, computed, rel_tol, abs_tol=0.0)`: relative to
the LARGER of the two, with NO absolute floor. PEP 485 considered a non-zero default absolute tolerance of about 1e-8
and refused it - a floor near 1e-9 "might be appropriate" for values of order one but "would be far too large if
expected values are on order of 1e-9 or smaller". Our floor was 1e-9; our smallest seal is 2.08e-43.

And a claim of ZERO is settled EXACTLY, never by a window, because (PEP 485 again) "by definition, no value is small
relative to zero", so no relative window can judge it and the flat floor that used to judge it confirmed every tiny
quantity as zero. The exact question is asked with the rational parse the calc chain ALREADY uses
(`_parse(..., rational=True)`, which reads decimals as exact rationals), so `0.1*(5/6) - 0.5*(1/6)` IS zero though its
float is 1.39e-17, while hbar is not though its float is 1.05e-34.

What must not move: every seal in the catalog still holds its own claim, and the stated-precision window still widens
a claim to the figures its author actually wrote.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concordance.verifiers import mathematics as M          # noqa: E402
from concordance.verifiers import physical_constants as PC  # noqa: E402
from concordance.verifiers.base import stated_precision, stated_window, window_for           # noqa: E402

H = 6.62607015e-34          # the Planck constant, J s, exact by the 2019 SI redefinition
E_CHARGE = 1.602176634e-19  # the elementary charge, C, exact by the same
HBAR = H / (2 * math.pi)


def numeric(expr, claimed, rel_tol=1e-9, literal=None):
    spec = {"numeric_expr": expr, "claimed_value": claimed, "rel_tol": rel_tol}
    if literal is not None:
        spec["claimed_literal"] = literal
    return M.verify_numeric(spec).status


# ---------------------------------------------------------------------------------------------------
# 1. THE LIVE TABLE. Every row measured on the public door on 2026-11-27, before the fix.
#    Four of these six returned HOLDS then; all four were false.
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("claimed,want,why", [
    (6.62607015e-34, "CONFIRMED", "the true value, to every figure"),
    (7e-34,          "MISMATCH",  "wrong by 5.6% - HELD before the fix"),
    (1e-33,          "MISMATCH",  "wrong by 51% - HELD before the fix"),
    (1e-20,          "MISMATCH",  "wrong by 14 orders - HELD before the fix"),
    (1e-9,           "MISMATCH",  "wrong by 25 orders - HELD before the fix"),
    (0.0,            "MISMATCH",  "zero - HELD before the fix"),
    (9.9e-34,        "MISMATCH",  "wrong by 49% - HELD before the fix through the structured door"),
    (2e-9,           "MISMATCH",  "wrong by 25 orders, and refused before the fix too: it clears the 1e-9 floor"),
])
def test_the_planck_constant_takes_only_its_own_value(claimed, want, why):
    assert numeric("6.62607015e-34", claimed) == want, why


@pytest.mark.parametrize("literal,want,why", [
    ("6.62607015e-34", "CONFIRMED", "every figure right"),
    ("6.626e-34",      "CONFIRMED", "four figures, right to all four: the stated window earns it"),
    ("9.9e-34",        "MISMATCH",  "two figures, wrong at the second: refused before the fix AND after"),
    ("1e-33",          "MISMATCH",  "ONE figure, so it earns no window - and before the fix it fell onto the "
                                   "flat 1e-9 floor and HELD. Stating MORE figures got you refused; stating one "
                                   "got you confirmed. That inversion is what this row pins."),
    ("7e-34",          "MISMATCH",  "one figure - HELD before the fix"),
    ("0",              "MISMATCH",  "one figure - HELD before the fix"),
])
def test_the_prose_door_inversion_is_gone(literal, want, why):
    """The live door of 2026-11-27 refused 9.9e-34 and confirmed 1e-33, because a two-figure literal earns a tight
    stated window while a one-figure literal earns none and landed on the floor. With the floor gone, a one-figure
    claim is judged against the quantity's own scale, so fewer figures can no longer buy a wider window."""
    assert numeric("6.62607015e-34", float(literal), literal=literal) == want, why


def test_the_elementary_charge_is_not_zero_through_the_constants_door():
    """base.window_for's `exact` default is what made this HOLD: a one-figure literal earns no stated window,
    so it fell back to a flat 1e-9 - eleven orders wider than the charge itself."""
    spec = {"constant": "elementary_charge", "claimed_value": 0.0, "claimed_literal": "0"}
    assert PC.verify_physical_constant(spec).status == "MISMATCH"
    ok = {"constant": "elementary_charge", "claimed_value": E_CHARGE, "claimed_literal": "1.602176634e-19"}
    assert PC.verify_physical_constant(ok).status == "CONFIRMED"


def test_the_window_for_default_is_the_scale_of_the_quantity_not_a_floor():
    """The lever itself: ten verifiers inherit this default."""
    tiny, _ = window_for({"claimed_literal": "0"}, "claimed_literal", 1e-9, 1.0, E_CHARGE)
    assert tiny < abs(E_CHARGE), "the window must be narrower than the quantity it judges"
    assert tiny == pytest.approx(1e-9 * E_CHARGE, rel=1e-12)
    big, _ = window_for({"claimed_literal": "3"}, "claimed_literal", 1e-9, 1.0, 299792458.0)
    assert big == pytest.approx(1e-9 * 299792458.0, rel=1e-12)


# ---------------------------------------------------------------------------------------------------
# 2. A CLAIM OF ZERO IS SETTLED EXACTLY. Decimal true zeros must keep holding.
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("expr,float_value", [
    ("0.1+0.2-0.3",            5.551115123125783e-17),
    ("1.1*1.1-1.21",           2.220446049250313e-16),
    ("0.3-0.1-0.2",           -2.7755575615628914e-17),
    ("0.1*(5/6) - 0.5*(1/6)",  1.3877787807814457e-17),   # change_of_domain's live seal
])
def test_a_decimal_true_zero_still_holds_a_claim_of_zero(expr, float_value):
    """These are zero as mathematics and non-zero as IEEE-754. A pure relative window would call them BROKEN,
    which is why the zero branch asks the exact question instead of widening the window back out."""
    assert float(M._parse(expr, []).evalf()) == float_value, "the float is still the float"
    assert numeric(expr, 0.0) == "CONFIRMED", expr


@pytest.mark.parametrize("expr", ["sin(pi)", "exp(I*pi)+1", "cos(pi/2)", "sqrt(2)**2-2", "7-7"])
def test_a_symbolic_true_zero_still_holds_a_claim_of_zero(expr):
    assert numeric(expr, 0.0) == "CONFIRMED", expr


def test_the_one_live_seal_that_a_pure_relative_window_would_have_broken():
    """THE COST, named. change_of_domain.markov_detailed_balance_lambda_1_eigenvector is a MINTED seal whose
    stored claim is 0.0 and whose expression recomputes to 1.39e-17 as a float. PEP 485's window alone calls
    that BROKEN - a false negative on a live seal, and a minted one, which is why the zero branch settles the
    question exactly instead. If this test ever fails, the exact path has been lost and a minted seal is being
    called false."""
    entry = json.loads((ROOT / "data" / "sticks" / "change_of_domain.json").read_text(encoding="utf-8"))
    seal = next(s for s in entry["seals"]
                if s["key"] == "markov_detailed_balance_lambda_1_eigenvector")
    assert seal["value"] == 0.0 and seal["expr"] == "0.1*(5/6) - 0.5*(1/6)"
    assert float(M._parse(seal["expr"], []).evalf()) == 1.3877787807814457e-17, "the float is still the float"
    assert not math.isclose(0.0, 1.3877787807814457e-17, rel_tol=seal["tol"], abs_tol=0.0), \
        "a pure relative window really does refuse it - that is the cost this branch pays"
    assert numeric(seal["expr"], 0.0, rel_tol=seal["tol"]) == "CONFIRMED", "and the seal still holds"


@pytest.mark.parametrize("literal", ["0", "0.0", "0.00", "0.000"])
def test_zero_earns_one_significant_figure_however_it_is_written(literal):
    """WHY THE BUG EXISTED AT ALL. stated_precision reads every written form of zero as ONE significant figure, so
    stated_window is None for all of them and a claim of zero NEVER earned a window of its own - anywhere in the
    engine. The flat floor was therefore the only thing judging any claim of zero, which is why one bad default
    confirmed "the Planck constant is 0" and "the elementary charge is 0 coulombs" alike. There is no trade-off
    here to weigh: "0.00 coulombs" was never a three-figure claim, before this change or after."""
    assert stated_precision(literal)[0] == 1, "zero is one significant figure however many places are written"
    assert stated_window(literal, False, 1.0) is None, "and so it earns no stated window"
    spec = {"numeric_expr": "1.602176634e-19", "claimed_value": 0.0, "rel_tol": 1e-9,
            "claimed_literal": literal}
    assert M.verify_numeric(spec).status == "MISMATCH", literal


def test_zero_equals_zero():
    assert numeric("0", 0.0) == "CONFIRMED"
    assert numeric("0.0", 0.0) == "CONFIRMED"


@pytest.mark.parametrize("expr,why", [
    ("6.62607015e-34/(2*pi)",                   "hbar"),
    ("1.380649e-23*310.15/(6.62607015e-34*40)", "the thermal quanta in a 40 Hz mode"),
    ("1.380649e-23*300*log(2)",                 "Landauer's cost of one bit at 300 K"),
    ("2+2-5",                                   "a control that was never near zero"),
])
def test_a_tiny_but_non_zero_quantity_refuses_a_claim_of_zero(expr, why):
    assert numeric(expr, 0.0) == "MISMATCH", why


# ---------------------------------------------------------------------------------------------------
# 3. WHAT MUST NOT MOVE: stated precision still widens a claim to the figures its author wrote.
# ---------------------------------------------------------------------------------------------------
def test_stated_precision_still_widens_earth_gravity():
    """2026-10-07: "earth gravity is 9.81 m/s^2" was refused by a flat 1e-4 - right to every figure stated,
    called false. It must stay right."""
    spec = {"constant": "standard_gravity", "claimed_value": 9.81, "claimed_literal": "9.81"}
    assert PC.verify_physical_constant(spec).status == "CONFIRMED"


def test_stated_precision_still_widens_a_rounded_planck_constant():
    assert numeric("6.62607015e-34", 6.626e-34, literal="6.626e-34") == "CONFIRMED"
    assert numeric("6.62607015e-34", 6.7e-34, literal="6.7e-34") == "MISMATCH"


def test_a_one_figure_claim_still_earns_no_window():
    """"3e8" never passes as the speed of light, and now "7e-34" never passes as the Planck constant for the
    same reason: one significant figure earns nothing, and the fallback is the quantity's own scale."""
    assert numeric("299792458", 3e8, literal="3e8") == "MISMATCH"
    assert numeric("6.62607015e-34", 7e-34, literal="7e-34") == "MISMATCH"


def test_display_rounding_still_holds_at_the_default_tolerance():
    assert M.verify_numeric({"numeric_expr": "sqrt(2)+1", "claimed_value": 2.41421356}).status == "CONFIRMED"
    assert M.verify_numeric({"numeric_expr": "2**10", "claimed_value": 1024}).status == "CONFIRMED"
    assert M.verify_numeric({"numeric_expr": "2**10", "claimed_value": 1000}).status == "MISMATCH"


# ---------------------------------------------------------------------------------------------------
# 4. THE WHOLE KEEPING: every numeric seal still holds its own claim, and none accepts zero unless it IS zero.
# ---------------------------------------------------------------------------------------------------
def _numeric_seals():
    out = []
    for p in sorted((ROOT / "data" / "sticks").glob("*.json")):
        entry = json.loads(p.read_text(encoding="utf-8"))
        for s in entry.get("seals", []):
            if s.get("domain") != "mathematics" or "expr" not in s:
                continue
            v = s.get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(pytest.param(p.stem, s.get("key"), s["expr"], float(v),
                                        float(s.get("tol") or 1e-9), s.get("variables") or [],
                                        id=f"{p.stem}.{s.get('key')}"))
    return out


SEALS = _numeric_seals()


@pytest.mark.parametrize("name,key,expr,claim,tol,variables", SEALS)
def test_every_seal_still_holds_its_own_claim(name, key, expr, claim, tol, variables):
    """The cost, measured the only way that CAN fail: the seal's STORED claim against a FRESH recompute of its
    expression. Comparing a value with itself cannot fail and proves nothing
    (feedback_a_metric_that_cannot_tell_my_hypothesis_from_something_else)."""
    spec = {"numeric_expr": expr, "claimed_value": claim, "rel_tol": tol}
    if variables:
        spec["variables"] = variables
    assert M.verify_numeric(spec).status == "CONFIRMED", f"{name}.{key} stopped holding its own claim"


@pytest.mark.parametrize("name,key,expr,claim,tol,variables", SEALS)
def test_no_seal_accepts_zero_unless_it_is_exactly_zero(name, key, expr, claim, tol, variables):
    spec = {"numeric_expr": expr, "claimed_value": 0.0, "rel_tol": tol}
    if variables:
        spec["variables"] = variables
    status = M.verify_numeric(spec).status
    if claim == 0.0:
        assert status == "CONFIRMED", f"{name}.{key} is zero and must accept zero"
    else:
        assert status == "MISMATCH", f"{name}.{key} = {claim!r} must refuse a claim of zero"


# ---------------------------------------------------------------------------------------------------
# 5. ONE CONTRACT AT EVERY MAGNITUDE. Before the fix this held only above 1; at 1e-34 the window the
#    engine actually gave was 1e25 instead of the 1e-9 the contract promises.
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("value", [1e-43, 1e-34, 1e-26, 1e-21, 1e-17, 1e-12, 1e-7, 1e-4, 0.027, 0.5, 1.0, 7.0, 1e6])
def test_the_window_tracks_the_quantity_at_every_scale(value):
    expr = repr(value)
    assert numeric(expr, value) == "CONFIRMED", "the truth must hold"
    assert numeric(expr, value * (1 + 1e-12)) == "CONFIRMED", "one part in 1e12 is inside a 1e-9 window"
    assert numeric(expr, value * (1 + 1e-6)) == "MISMATCH", "one part in 1e6 is outside it"
    assert numeric(expr, 0.0) == "MISMATCH", "zero is not this quantity"
    assert numeric(expr, value * 1000) == "MISMATCH", "a thousand times it is not it"

# ---------------------------------------------------------------------------------------------------
# 6. A FLOAT THAT UNDERFLOWED IS NOT A ZERO. The second road to the same false positive: a quantity
#    below the smallest double evaluates to 0.0, so the relative window around it is 0.0 too and a
#    claim of 0 matched it EXACTLY. Closing the floor did not close this; it is settled exactly.
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("expr,true_value", [
    ("10**-400",  "1e-400"),
    ("exp(-1000)", "5.08e-435"),
    ("2**-1100",   "7.36e-332"),          # "the chance of 1100 heads in a row is 0" - a family-sized case
])
def test_a_quantity_below_the_double_range_is_not_zero(expr, true_value):
    assert float(M._parse(expr, []).evalf()) == 0.0, "its float really does underflow to 0.0"
    assert numeric(expr, 0.0) == "MISMATCH", f"{expr} is about {true_value}, not zero"


def test_a_claim_below_the_double_range_is_judged_at_that_scale_when_it_carries_its_literal():
    """float("1e-400") and float("2e-400") are BOTH 0.0, so a structured claim this small arrives carrying
    nothing and is read as a claim of zero. Only the claim's own literal can be judged at that scale - and then
    it is judged exactly, so the right value holds and a wrong one does not."""
    assert numeric("10**-400", 0.0, literal="1e-400") == "CONFIRMED"
    assert numeric("10**-400", 0.0, literal="2e-400") == "MISMATCH"
    assert numeric("10**-400", 0.0, literal="0") == "MISMATCH"
    assert numeric("exp(-1000)", 0.0, literal="5.075958897549457e-435") == "CONFIRMED"


@pytest.mark.parametrize("expr", ["10**-400 - 10**-400", "exp(-1000)-exp(-1000)", "2**-1100 * 0"])
def test_a_true_zero_below_the_double_range_still_holds(expr):
    assert numeric(expr, 0.0) == "CONFIRMED", expr


def test_subnormals_need_no_special_care():
    """Measured: 10**-320 keeps a real float (1e-320), so the RELATIVE WINDOW refuses a claim of zero on it -
    it is the window fix that does this, not the underflow branch (before both, 10**-320 == 0 was CONFIRMED).
    The underflow branch is for a float that really reached 0.0, and deliberately reaches no further: widening
    it to subnormals would buy nothing and would put a sixty-digit comparison on a path that does not need one."""
    assert float(M._parse("10**-320", []).evalf()) == 1e-320
    assert numeric("10**-320", 0.0) == "MISMATCH"
    assert numeric("10**-320", 1e-320) == "CONFIRMED"

# ---------------------------------------------------------------------------------------------------
# 7. THE ZERO PATH MUST NOT CHANGE A SEAL'S CONTENT HASH. A seal's hash is computed over this result,
#    and ten MINTED seals are provably-zero expressions. A first attempt returned its own confirm()
#    with an extra data field, and all ten stopped reproducing their goldens - caught only by the
#    full suite's 203-entry mint check, 27 minutes in. This pins it in milliseconds instead.
# ---------------------------------------------------------------------------------------------------
# The provably-zero seals this would have broken - read from the catalog itself, not written from memory,
# every one of them MINTED and live.
PROVABLY_ZERO_SEALS = [
    ("bombelli.bombelli_real_root", "4**3 - 15*4 - 4"),
    ("change_of_domain.markov_detailed_balance_lambda_1_eigenvector", "0.1*(5/6) - 0.5*(1/6)"),
    ("dirichlet.roots_of_unity_sum_zero", "1 + (-0.5) + (-0.5)"),
    ("fourier.test_note_cancels", "1 + 0 + (-1) + 0"),
    ("game_theory.matching", "0.5*1 + 0.5*(-1)"),
    ("imaginary_numbers.imaginary_parts_cancel_on_return", "2 + (-2)"),
    ("lebesgue.lebesgue_dirichlet_integral", "1*0 + 0*1"),
    ("navier_stokes.ns_energy_critical_2d", "2 - 2"),
    ("smith_chart.smith_matched", "(1 - 1) / (1 + 1)"),
    ("tesseract.euler4d", "16 - 32 + 24 - 8"),
]


def test_the_minted_zero_list_is_still_what_the_catalog_says():
    """Read from the entries, so this guard cannot drift away from the seals it protects."""
    found = []
    for path in sorted((ROOT / "data" / "sticks").glob("*.json")):
        for s in json.loads(path.read_text(encoding="utf-8")).get("seals", []):
            if s.get("domain") == "mathematics" and "expr" in s and s.get("value") == 0.0:
                found.append((f"{path.stem}.{s['key']}", s["expr"]))
    assert found == PROVABLY_ZERO_SEALS, "the catalog's provably-zero seals have changed: re-read them and update"


PROVABLY_ZERO = [e for _, e in PROVABLY_ZERO_SEALS]


def _data(r):
    return getattr(r, "data", {}) or {}


def _ordinary_keys():
    """The keys the ORDINARY confirm path produces, read from the engine itself rather than written down here:
    the two engines carry different sets (V3 adds band/actual_value/claimed_value) and either may grow more."""
    r = M.verify_numeric({"numeric_expr": "1e-20", "claimed_value": 1e-20, "rel_tol": 1e-12})
    assert r.status == "CONFIRMED"
    return set(_data(r))


@pytest.mark.parametrize("expr", PROVABLY_ZERO)
def test_a_provably_zero_claim_is_reported_by_the_ordinary_path(expr):
    """THE INVARIANT: the zero finding only widens the window and lets the ordinary path speak. It adds no key
    the ordinary path would not add and writes no sentence of its own, so the bytes a seal hashes are the bytes
    it hashed before. Measured 2026-11-27: a first attempt returned its own confirm() with an extra field, and
    all ten of the keeping's provably-zero MINTED seals stopped reproducing their goldens."""
    r = M.verify_numeric({"numeric_expr": expr, "claimed_value": 0.0, "rel_tol": 1e-12})
    assert r.status == "CONFIRMED", expr
    extra = set(_data(r)) - _ordinary_keys()
    assert not extra, f"the zero path added {extra} to a result a seal's content hash is computed over"
    assert _data(r).get("exact") is True
    detail = getattr(r, "detail", "") or ""
    assert detail.endswith("is exact."), detail
    assert "exactly zero" not in detail, "a wording of its own would change every minted zero seal's hash"
    assert "settled_exactly" not in _data(r)


def test_the_catalogs_ten_provably_zero_seals_are_the_ones_at_stake():
    """Named so the next person knows what this guard protects. These ten entries' goldens all broke on the
    first attempt; tools/tick_golden.py check is the slow authority, this is the fast warning."""
    at_stake = {"bombelli", "change_of_domain", "dirichlet", "fourier", "game_theory",
                "imaginary_numbers", "lebesgue", "navier_stokes", "smith_chart", "tesseract"}
    present = {p.stem for p in (ROOT / "data" / "sticks").glob("*.json")}
    missing = at_stake - present
    assert not missing, f"these entries carry a provably-zero seal and are gone: {missing}"
