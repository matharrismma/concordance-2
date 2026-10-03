"""The SI unit normalizer (R4): parse to a dimension and a factor; convert within a dimension; say nothing for
what it does not know. Every unit the constants table stores must parse. (verifiers/units.py — the CONV_VERIFY
door — is a different module and keeps its own tests.)"""
import math

import pytest

from concordance.verifiers import si_units as units
from concordance.verifiers.physical_constants import _CONSTANTS


def test_every_stored_constant_unit_parses():
    for name, rec in _CONSTANTS.items():
        assert units.parse(rec["unit"]) is not None, (name, rec["unit"])


@pytest.mark.parametrize("a,b", [
    ("km/s", "m/s"), ("m s^-1", "m/s"), ("m·s⁻¹", "m/s"), ("meters per second", "m/s"), ("mph", "m/s"),
    ("J/K/mol", "J/(mol*K)"), ("J K^-1 mol^-1", "J/(mol*K)"), ("J mol-1 K-1", "J/(mol*K)"),
    ("N m^2/kg^2", "m^3/(kg*s^2)"), ("m3 kg-1 s-2", "m^3/(kg*s^2)"), ("N*m^2*kg^-2", "m^3/(kg*s^2)"),
    ("1/mol", "mol^-1"), ("/mol", "1/mol"), ("per mole", "1/mol"), ("J s", "J*s"), ("J·s", "J*s"), ("eV s", "J*s"),
    ("coulombs", "C"), ("F/m", "C/(V*m)"), ("W/(m^2*K^4)", "W m-2 K-4"), ("Pa", "N/m^2"), ("kg", "g"), ("1/m", "m^-1"),
])
def test_same_dimension_across_spellings(a, b):
    assert units.same_dimension(a, b) is True, (a, b)


def test_conversion_factors():
    assert units.convert(150000, "km/s", "m/s") == pytest.approx(1.5e8)
    assert units.convert(299792.458, "km/s", "m/s") == pytest.approx(299792458.0)
    assert units.convert(670616629, "mph", "m/s") == pytest.approx(299792458.0, rel=1e-6)
    assert units.convert(8.314, "J/K/mol", "J/(mol*K)") == pytest.approx(8.314)
    assert units.convert(1, "eV", "J") == pytest.approx(1.602176634e-19)
    assert units.convert(1, "km", "m") == 1000.0 and units.convert(1, "cm", "m") == pytest.approx(0.01)
    assert units.convert(1, "h", "s") == 3600.0 and units.convert(1, "min", "s") == 60.0   # min is minutes, not milli-inch
    assert units.convert(1, "Pa", "N/m^2") == 1.0 and units.convert(1, "mi", "m") == pytest.approx(1609.344)


def test_wrong_dimension_and_unknown_units():
    assert units.same_dimension("kg", "m/s") is False                 # a real unit of the wrong kind
    assert units.convert(3e8, "kg", "m/s") is None
    assert units.same_dimension("furlongs/fortnight", "m/s") is None   # unknown: say nothing
    assert units.parse("°C") is None and units.parse("") is None and units.parse("banana") is None
    assert units.parse("dimensionless") == ({}, 1.0) and units.parse("1") == ({}, 1.0)


def test_longest_unit_prefix_from_prose():
    assert units.longest_unit_prefix(["m", "s^-1", "in", "vacuum"], "m/s") == ("m s^-1", 2)
    assert units.longest_unit_prefix(["m/s", "in", "vacuum"], "m/s") == ("m/s", 1)
    assert units.longest_unit_prefix(["km", "per", "second", "roughly"], "m/s") == ("km per second", 3)
    assert units.longest_unit_prefix(["kg", "which", "is"], "m/s") == ("kg", 1)             # wrong dimension, still a claim
    assert units.longest_unit_prefix(["particles", "per", "mole"], "1/mol") is None          # not a unit it knows
    assert units.longest_unit_prefix([], "m/s") is None


def test_describe_is_readable():
    assert units.describe({"m": 1, "s": -1}) == "m·s^-1" and units.describe({}) == "dimensionless"
    assert math.isclose(units.parse("N")[1], 1.0)
