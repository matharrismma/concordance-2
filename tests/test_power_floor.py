"""THE POWER FLOOR: an Integer or Rational power past the bound is refused where sympy computes it, and
compute's arithmetic holds the same bound. The numbers here are neutral, and every call is sympy's own
power or compute's own function, called directly. The floor stands at those two powers and no others.

A stuck power runs in a child with a kill, because big-integer work holds Python's global lock: nothing
in the process that runs it can stop it, so only the process above it can. Every other power in this
file is past the bound by one step and cheap to compute, so a floor taken away reads red and nothing
hangs."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
import sympy

import concordance.engine as E
from concordance import compute
from concordance import derivation as D
from concordance.config import EngineConfig
from concordance.verifiers import base as B
from concordance.verifiers import mathematics as M
from concordance.verifiers import spec as S

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
KILL_S = 5
JUST_UNDER = 2 ** 19            # a two-bit base at this exponent measures exactly _MAX_POW_BITS
LOAD_MATHEMATICS = "from concordance.verifiers import mathematics as M; M._ensure_sympy()"
# Every module under src/concordance that loads sympy, and how it does. A new one fails until it is here.
LOADERS = {
    "src/concordance/verifiers/mathematics.py": LOAD_MATHEMATICS,
    "src/concordance/verifiers/physics.py": "from concordance.verifiers import physics as P; P._ensure_sympy()",
    "src/concordance/derivation.py": "from concordance import derivation as D; D.warm()",
}
# One prime once and one prime many times, so a root multiplies out what the exponent's denominator leaves of each. The
# numerator is under the bound and the exponent under one, so only that measure can refuse these.
UNEVEN, NUMERATOR, DENOMINATOR = "2*3**1024", 3 * 2 ** 18 + 1, 2 ** 29 + 3
ROOT = f"sympy.Rational({NUMERATOR}, {DENOMINATOR})"
ROUGH = "3**(2**17) + 2"        # no small factor, so trial division leaves sympy nearly all of it to prove
STUCK_POWERS = ["sympy.Integer(3) ** sympy.Integer(2**27)", "sympy.Rational(3, 2) ** sympy.Integer(2**27)",
                "sympy.Integer(3) ** sympy.Integer(-2**27)", "sympy.Integer(3) ** sympy.Rational(2**28 + 1, 2)",
                f"sympy.Integer({UNEVEN}) ** {ROOT}", f"sympy.Integer({UNEVEN}) ** ({ROOT} - 1)",
                f"sympy.Rational({UNEVEN}, 5) ** {ROOT}", f"sympy.Rational(5, {UNEVEN}) ** (1 - {ROOT})",
                f"sympy.Integer({ROUGH}) ** sympy.S.Half", f"sympy.Rational({ROUGH}, 5) ** sympy.S.Half",
                f"sympy.Rational(5, {ROUGH}) ** sympy.S.Half",
                "sympy.Integer(144) ** sympy.Rational(2**40 + 1, 2**42 + 1)"]   # a perfect power hands 12 on, and 12 is uneven
CHILD = """
import time
{load}
import sympy
print("LOADED", flush=True)
start = time.perf_counter()
try:
    {power}
    print("COMPUTED", time.perf_counter() - start, flush=True)
except BaseException as refused:
    print(type(refused).__name__, time.perf_counter() - start, flush=True)
"""


@pytest.fixture(scope="module", autouse=True)
def floor():
    assert M._ensure_sympy()


def run_with_a_kill(load: str, power: str) -> tuple:
    """What became of one power in a fresh process, and how long it took. The bound starts when sympy
    has loaded, so a slow import on a loaded machine never reads as a stuck power."""
    code = CHILD.format(load=load, power=power)
    with subprocess.Popen([sys.executable, "-c", code], env={**os.environ, "PYTHONPATH": str(SRC)},
                          stdout=subprocess.PIPE, text=True) as child:
        try:
            assert child.stdout.readline().strip() == "LOADED"
            out, _ = child.communicate(timeout=KILL_S)
        except subprocess.TimeoutExpired:
            pytest.fail(f"{power} was still running at the {KILL_S} s kill")
        finally:
            child.kill()
    outcome, elapsed = out.split()
    return outcome, float(elapsed)


def past_the_bound(*_args, **_kwargs):
    return sympy.Integer(3) ** sympy.Integer(JUST_UNDER + 1)


def free_slots() -> int:
    held = 0
    while D._SLOTS.acquire(blocking=False):
        held += 1
    for _ in range(held):
        D._SLOTS.release()
    return held


def loads_sympy(source: str) -> bool:
    """An import of sympy, or a literal naming it, as a dynamic import must."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "sympy" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "sympy":
            return True
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.split(".")[0] == "sympy":
            return True
    return False


# ── the floor ──

@pytest.mark.parametrize("power", STUCK_POWERS)
def test_a_stuck_power_is_refused_in_well_under_a_second(power):
    outcome, elapsed = run_with_a_kill(LOAD_MATHEMATICS, power)
    assert outcome == "PowerFloorRefused"
    assert elapsed < 1


def test_the_modules_that_load_sympy_are_the_ones_named_here():
    found = {path.relative_to(REPO).as_posix() for path in SRC.rglob("*.py")
             if loads_sympy(path.read_text(encoding="utf-8"))}
    assert found == set(LOADERS)


@pytest.mark.parametrize("module", sorted(LOADERS))
def test_every_module_that_loads_sympy_gets_the_floor_on_its_own(module):
    outcome, _elapsed = run_with_a_kill(LOADERS[module], STUCK_POWERS[0])
    assert outcome == "PowerFloorRefused"


@pytest.mark.parametrize("base", [sympy.Integer(3), sympy.Rational(3, 2), sympy.Integer(-3), sympy.Rational(-3, 2)])
@pytest.mark.parametrize("exponent", [JUST_UNDER + 1, -(JUST_UNDER + 1)])
def test_the_bound_is_the_one_power_bits_measures(base, exponent):
    assert M._power_bits(base, sympy.Integer(exponent)) == M._MAX_POW_BITS + 2
    with pytest.raises(B.PowerFloorRefused):
        base ** sympy.Integer(exponent)


PAST = sympy.Rational(M._MAX_POW_BITS + 1, 2 * M._MAX_POW_BITS + 1)     # leaves 12 one 2 and that many 3s
UNDER = sympy.Rational(JUST_UNDER // 2, JUST_UNDER // 2 + 1)            # leaves 12 just under the bound


@pytest.mark.parametrize("base, exponent", [
    (sympy.Integer(12), PAST), (sympy.Integer(-12), PAST), (sympy.Integer(12), PAST - 1),
    (sympy.Rational(12, 5), PAST),          # the numerator's side: Integer(12) ** PAST
    (sympy.Rational(5, 12), 1 - PAST),      # the denominator's side: Integer(12) ** (1 - (1 - PAST))
])
def test_what_a_root_multiplies_out_past_the_bound_is_refused(base, exponent):
    assert M._left_under_the_root(12, PAST) > M._MAX_POW_BITS
    with pytest.raises(B.PowerFloorRefused):
        base ** exponent


@pytest.mark.parametrize("base, exponent", [
    (sympy.Integer(12), UNDER), (sympy.Rational(12, 5), UNDER), (sympy.Rational(5, 12), 1 - UNDER),
])
def test_what_a_root_multiplies_out_under_the_bound_reads(base, exponent):
    assert M._left_under_the_root(12, UNDER) <= M._MAX_POW_BITS
    assert (base ** exponent).is_positive


@pytest.mark.parametrize("n, p, q, coefficient, radicand, root", [
    (12, 5, 7, 2, 1944, sympy.Rational(1, 7)),      # 12 = 2**2 * 3, so 2**(10 % 7) * 3**(5 % 7)
    (72, 5, 11, 2, 972, sympy.Rational(2, 11)),     # the remainders 4 and 10 share 2
])
def test_the_measure_reads_what_sympy_multiplies_out(n, p, q, coefficient, radicand, root):
    assert sympy.Integer(n) ** sympy.Rational(p, q) == coefficient * sympy.Integer(radicand) ** root
    assert M._left_under_the_root(n, sympy.Rational(p, q)) == radicand.bit_length()


def test_a_denominator_no_float_can_hold_is_still_measured():
    exponent = sympy.Rational(7 * 10 ** 400 + 1, 10 ** 401 + 3)     # past half, so 2's remainder wraps and 3's does not
    assert M._left_under_the_root(12, exponent) > M._MAX_POW_BITS


@pytest.mark.parametrize("n", [12, 18, 24, 72, 288, 360, 4374])
@pytest.mark.parametrize("q", [7, 11, 13, 101])
def test_no_radicand_sympy_builds_passes_the_measure(n, q):
    for p in range(1, q):
        measured = M._left_under_the_root(n, sympy.Rational(p, q))
        for factor in sympy.Mul.make_args(sympy.Integer(n) ** sympy.Rational(p, q)):
            base, exponent = factor.as_base_exp()
            if not exponent.is_Integer:
                assert int(base).bit_length() <= max(measured, n.bit_length())


@pytest.mark.parametrize("base", [sympy.Integer(2), sympy.Integer(10), sympy.Integer(100), sympy.Rational(3, 2)])
def test_a_numerator_sympy_never_multiplies_by_reads_past_the_bound(base):
    """A prime alone, primes that each appear once, and a perfect power of those: each leaves a small integer under the root."""
    exponent = sympy.Rational(2 ** 40 + 1, 2 ** 42 + 1)
    assert exponent.p > M._MAX_POW_BITS
    assert (base ** exponent).is_positive


def test_a_shipped_text_with_a_long_decimal_exponent_reads_as_it_did():
    """tools/tick.py builds this: the half-power identity in decibels, a numerator past the bound on 2 * 5."""
    value = M.parse_expression("10**((3.010299956639812)/10)", rational=True, word_mod=True)
    assert value.is_positive and abs(value.evalf() - 2) < 1e-9


def test_a_size_past_the_root_bound_is_refused_and_one_at_it_is_left_to_sympy():
    past, at = (1 << M._MAX_ROOT_BITS) + 1, (1 << (M._MAX_ROOT_BITS - 1)) + 1
    assert (past.bit_length(), at.bit_length()) == (M._MAX_ROOT_BITS + 1, M._MAX_ROOT_BITS)
    assert M._past_the_floor(sympy.Integer(past), sympy.S.Half)
    assert not M._past_the_floor(sympy.Integer(at), sympy.S.Half)


def test_the_root_bound_reads_what_trial_division_leaves():
    assert M._unfactored_bits(2 ** 5 * 3 ** 7) == 1
    assert M._unfactored_bits(32749 ** 2 * 7) == 1              # the last prime under 2**15
    assert M._unfactored_bits(2 ** 5 * 32771) == 16             # the first past it stays
    assert M._unfactored_bits(2 ** 20000 * ((1 << M._MAX_ROOT_BITS) + 1)) == M._MAX_ROOT_BITS + 1


def test_the_floor_refuses_before_sympy_is_asked_to_prove_anything(monkeypatch):
    def asked(*_args, **_kwargs):
        raise AssertionError("sympy's root was reached")
    monkeypatch.setattr(sympy.ntheory.factor_, "perfect_power", asked)
    monkeypatch.setattr(sympy, "perfect_power", asked)
    monkeypatch.setattr(sympy.Integer, "factors", asked)
    with pytest.raises(B.PowerFloorRefused):
        sympy.Integer(3 ** 2 ** 14 + 2) ** sympy.S.Half


def test_a_numerator_that_is_whole_powers_is_what_power_bits_measures():
    """Only the fraction is left to the numerator's own bound, so a power under the bound still reads."""
    exponent = sympy.Rational(5 * M._MAX_POW_BITS + 1, 1000)
    assert exponent.p > M._MAX_POW_BITS
    assert M._power_bits(sympy.Integer(3), exponent) <= M._MAX_POW_BITS
    whole, fraction = divmod(exponent.p, exponent.q)
    assert sympy.Integer(3) ** exponent == 3 ** whole * sympy.Integer(3) ** sympy.Rational(fraction, 1000)


# ── nothing else moves ──

@pytest.mark.parametrize("base, exponent", [
    (Fraction(2), 100), (Fraction(3), JUST_UNDER), (Fraction(-3), JUST_UNDER), (Fraction(3, 2), JUST_UNDER),
    (Fraction(3), -JUST_UNDER), (Fraction(3, 2), -100),
])
def test_a_large_legal_power_reads_exactly(base, exponent):
    built = sympy.Rational(base.numerator, base.denominator)
    assert M._power_bits(built, sympy.Integer(exponent)) <= M._MAX_POW_BITS
    value = built ** sympy.Integer(exponent)
    exact = base ** exponent
    assert (value.p, value.q) == (exact.numerator, exact.denominator)


def test_a_large_integer_with_nothing_left_to_prove_reads_as_it_did():
    """Far past the root bound, and sympy reads each at once: an exact root, a perfect power, and small primes alone."""
    assert sympy.Integer(3 ** 40000) ** sympy.S.Half == 3 ** 20000
    assert sympy.Integer(3 ** 20000) ** sympy.Rational(1, 7) == 3 ** 2857 * sympy.Integer(3) ** sympy.Rational(1, 7)
    assert sympy.Integer(3 * 2 ** 20000) ** sympy.S.Half == 2 ** 10000 * sympy.sqrt(3)
    assert sympy.Rational(3 * 2 ** 20000, 5) ** sympy.S.Half == 2 ** 10000 * sympy.sqrt(15) / 5


def test_a_legal_root_reads_as_it_did():
    assert sympy.sqrt(sympy.Integer(16)) == 4
    assert sympy.Integer(8) ** sympy.Rational(2, 3) == 4
    assert sympy.Rational(4, 9) ** sympy.Rational(3, 2) == sympy.Rational(8, 27)
    assert str(sympy.Integer(2) ** sympy.Rational(1, 2)) == "sqrt(2)"


def test_exponents_the_floor_does_not_read_go_straight_on():
    x = sympy.Symbol("x")
    assert str(sympy.Integer(2) ** x) == "2**x"
    assert sympy.Integer(2) ** sympy.oo == sympy.oo
    assert sympy.Integer(4) ** sympy.Float(0.5) == sympy.Float(2.0)


@pytest.mark.parametrize("base, value", [(0, 0), (1, 1), (-1, 1)])
def test_a_base_that_never_grows_keeps_its_own_power(base, value):
    assert sympy.Integer(base) ** sympy.Integer(2 ** 40) == value


def test_a_true_claim_with_a_large_legal_power_still_holds():
    claim = {"mode": "equality", "params": {"expr_a": "2**100", "expr_b": str(2 ** 100)}}
    assert D.verify(claim)["verdict"] == "HOLDS"


# ── the refusal is never an answer ──

def test_the_refusal_is_a_base_exception_and_no_exception():
    assert issubclass(B.PowerFloorRefused, BaseException)
    assert not issubclass(B.PowerFloorRefused, Exception)


def test_it_passes_through_a_verifier_handler_that_catches_exception(monkeypatch):
    monkeypatch.setattr(M, "simplify", past_the_bound)
    with pytest.raises(B.PowerFloorRefused):
        M.verify_equality({"expr_a": "x", "expr_b": "x", "variables": ["x"]})


def test_the_worker_reads_a_math_claim_as_not_checkable_and_gives_the_slot_back(monkeypatch):
    free = free_slots()
    claim = {"mode": "equality", "params": {"expr_a": "x", "expr_b": "x", "variables": ["x"]}}
    with monkeypatch.context() as patch:
        patch.setattr(M, "simplify", past_the_bound)
        for _ in range(3 * D._MAX_WORKERS):        # a slot held by each refusal would run out here
            result = D.verify(claim)
            assert result["verdict"] == "INCOMPLETE", result
            assert result["trail"][0]["status"] == "NOT_APPLICABLE"
            assert result["trail"][0]["detail"].startswith("not checkable")
    assert free_slots() == free
    assert D.verify(claim)["verdict"] == "HOLDS"    # and nothing of it stays behind


def test_the_worker_reads_a_domain_claim_as_not_checkable_and_gives_the_slot_back(monkeypatch):
    free = free_slots()
    with monkeypatch.context() as patch:
        patch.setattr(D._verifiers, "run_for_domain", past_the_bound)
        for _ in range(3 * D._MAX_WORKERS):
            result = D.verify({"MATH_VERIFY": {}}, domain="statistics")
            assert result["verdict"] == "INCOMPLETE", result
            assert result["trail"][0]["detail"].startswith("not checkable")
    assert free_slots() == free


def test_a_refused_step_leaves_the_derivation_incomplete_and_never_broken(monkeypatch):
    monkeypatch.setattr(M, "simplify", past_the_bound)
    steps = [{"id": "a", "domain": "mathematics", "uses": [], "spec": {
        "mode": "equality", "params": {"expr_a": "x", "expr_b": "x", "variables": ["x"]}}},
        {"id": "b", "domain": "mathematics", "uses": ["a"], "spec": {
            "mode": "numeric", "params": {"numeric_expr": "2+2", "claimed_value": "4"}}}]
    result = D.verify_derivation(steps)
    assert result["verdict"] == "INCOMPLETE", result
    assert result["gap_at"] == "a" and result["broken_at"] is None and result["error_at"] is None


def test_the_engine_reads_a_refusal_on_its_own_thread(monkeypatch):
    """engine._run_validation calls the verifiers outside the worker: the one caller that does."""
    monkeypatch.setattr(M, "simplify", past_the_bound)
    packet = {"domain": "mathematics", "created_epoch": 1,
              "MATH_VERIFY": {"expr_a": "x", "expr_b": "x", "variables": ["x"]}}
    config = EngineConfig(skip_schema_validation=True)
    result = E.validate_packet(packet, now_epoch=10 ** 9, config=config)
    assert result.overall == "QUARANTINE"
    assert [g.status for g in result.gate_results if g.gate == "RED"][-1] == "QUARANTINE"
    record = E.validate_and_seal(packet, now_epoch=10 ** 9, config=config)
    assert record.overall == "QUARANTINE"
    assert [v.status for v in record.verifier_results] == ["NOT_APPLICABLE"]


def test_the_engine_still_passes_and_rejects_what_it_read(monkeypatch):
    config = EngineConfig(skip_schema_validation=True)
    packet = {"domain": "mathematics", "created_epoch": 1,
              "MATH_VERIFY": {"expr_a": "2+2", "expr_b": "4", "variables": []}}
    assert E.validate_packet(packet, now_epoch=10 ** 9, config=config).overall == "PASS"
    packet["MATH_VERIFY"]["expr_b"] = "5"
    assert E.validate_packet(packet, now_epoch=10 ** 9, config=config).overall == "REJECT"


# ── sympy's own power stays with the tests ──

def test_nothing_but_the_floor_names_the_unfloored_power():
    """tests/test_parse_differential.py lifts the floor by this name. Nothing the engine or a tool runs does."""
    named = {path.relative_to(REPO).as_posix() for folder in (SRC, REPO / "tools") for path in folder.rglob("*.py")
             if "unfloored" in path.read_text(encoding="utf-8", errors="ignore")}
    assert named == {"src/concordance/verifiers/mathematics.py"}


def test_the_engine_sets_the_unfloored_power_and_never_reads_it():
    tree = ast.parse((SRC / "concordance" / "verifiers" / "mathematics.py").read_text(encoding="utf-8"))
    attributes = [node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "unfloored"]
    assert [type(node.ctx) for node in attributes] == [ast.Store]
    literals = [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == "unfloored"]
    assert len(literals) == 1           # the hasattr that keeps a second install from wrapping twice


def test_no_evaluator_under_src_reads_an_attribute():
    assert [path for path in SRC.rglob("*.py") if "ast.Attribute" in path.read_text(encoding="utf-8")] == []


@pytest.mark.parametrize("text", ["Integer._eval_power.unfloored", "Integer.unfloored", "(2).unfloored", "getattr(Integer,1)"])
def test_no_text_can_ask_for_an_attribute(text):
    with pytest.raises(M.ExpressionRefused):
        M.parse_expression(text)
    with pytest.raises(S.SpecError):
        S.safe_eval(text, {"Integer": 1})
    assert compute.answer(text) is None


# ── the arithmetic ──

@pytest.mark.parametrize("text", [
    "((2**1000)**1000)**2 % 7",                 # a power of a power, each exponent small in the text
    "2**(1000*1100) % 7",                       # an exponent the text does not show as a number
    "(2**1000)**1000 * (2**1000)**1000 % 7",    # a product of two results under the bound
])
def test_arithmetic_declines_past_the_bound_however_it_is_written(text):
    assert compute.answer(text) is None


@pytest.mark.parametrize("text, reading", [
    ("(2**1000)**1000 % 7", "(2 ^ 1000) ^ 1000 mod 7 = 2"),
    ("3**(512*1024) % 7", "3 ^ (512 × 1024) mod 7 = 2"),                        # at the bound exactly
    ("2**(512*1024-1)*2**(512*1024-1) % 7", "2 ^ (512 × 1024 - 1) × 2 ^ (512 × 1024 - 1) mod 7 = 4"),
    ("2**100", "2 ^ 100 = 1267650600228229401496703205376"),
    ("1**(1000*1000)", "1 ^ (1000 × 1000) = 1"),                               # one bit, however high
    ("(-1)**(1000*1001)", "(-1) ^ (1000 × 1001) = 1"),
    ("0**(1000*1000)", "0 ^ (1000 × 1000) = 0"),
    ("2**-2", "2 ^ (-2) = 0.25"),
    ("2.5*4", "2.5 × 4 = 10"),
])
def test_arithmetic_under_the_bound_reads_as_it_did(text, reading):
    assert compute.answer(text) == reading


@pytest.mark.parametrize("text", ["3**(512*1024+1) % 7", "2**(512*1024)*2**(512*1024-1) % 7"])
def test_arithmetic_declines_one_step_past_the_bound(text):
    assert compute.answer(text) is None


def test_the_text_check_stays_as_a_first_line():
    """A base of one is under the bound at any height, so only the text check can decline this."""
    assert compute.answer("1**2000") is None


class Unspent(int):
    """An integer whose arithmetic fails the test, so a size measured after the work reads red."""

    def __pow__(self, _other, _mod=None):
        raise AssertionError("the power was computed before it was measured")

    def __mul__(self, _other):
        raise AssertionError("the product was computed before it was measured")


def test_a_power_is_measured_before_it_is_computed():
    with pytest.raises(ValueError, match="power too large"):
        compute._bounded_power(Unspent(3), 2 ** 33)


def test_a_product_is_measured_before_it_is_computed():
    with pytest.raises(ValueError, match="product too large"):
        compute._bounded_product(Unspent(1 << M._MAX_POW_BITS), 2)


def test_the_arithmetic_holds_the_mathematics_bound():
    assert compute._MAX_POW_BITS is M._MAX_POW_BITS


# ── the text ──

def test_a_text_past_the_length_is_declined_before_any_reading(monkeypatch):
    seen = []
    for reader in ("_denumber", "_convert", "_temperature", "_arith", "_worded"):
        monkeypatch.setattr(compute, reader, lambda text, name=reader: seen.append(name))
    assert compute.answer("1" * (compute._MAX_TEXT_CHARS + 1)) is None
    assert seen == []


def test_the_length_is_read_on_the_text_and_not_on_what_surrounds_it():
    padded = " " * compute._MAX_TEXT_CHARS + "what is 1 + 1?" + " " * compute._MAX_TEXT_CHARS
    assert compute.answer(padded) == "1 + 1 = 2"


def test_a_text_at_the_length_reads_and_one_past_it_declines():
    sum_of = "+".join(["1"] * (compute._MAX_TEXT_CHARS // 2 + 1))
    assert len(sum_of) == compute._MAX_TEXT_CHARS + 1
    assert compute.answer(sum_of) is None
    assert compute.answer(sum_of[:-2]).endswith(f"= {compute._MAX_TEXT_CHARS // 2}")


def probe_texts() -> list:
    texts = []
    for line in (REPO / "eval" / "live_probes.jsonl").read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("{"):
            body = json.loads(line).get("body")
            if isinstance(body, dict) and isinstance(body.get("text"), str):
                texts.append(body["text"])
    return texts


def test_the_length_loses_no_real_question():
    """Five times the longest question this repo probes the live engine with, and an average of a
    hundred numbers, the one reading here whose length grows with what is asked."""
    texts = probe_texts()
    assert texts and 5 * max(len(text) for text in texts) <= compute._MAX_TEXT_CHARS
    numbers = ", ".join(str(n) for n in range(10, 110))
    assert compute.answer(f"average of {numbers}") == f"average of {numbers} = 59.5"
    question = ("I am doubling my grandmother's bread recipe for the church supper this weekend and I only "
                "have a small scoop in the kitchen drawer, so tell me plainly, how many teaspoons in a tablespoon?")
    assert compute.answer(question) == "1 tablespoon = 3 teaspoons"
