"""FLOOR attestation validators — the "reference not advice" guardrail, GATE-enforced.

Health and financial domains carry a protective rule: their output is REFERENCE, not
professional advice. 1.0 stated this only in verifier docstrings; here it is enforced at the
FLOOR gate — a packet in one of these domains that does not carry the required attestation is
REJECTed before it can seal. The attestation is the author AFFIRMING the framing (and that the
user is pointed to a licensed professional / real help); the engine itself never gives advice.

A packet attests via an `attestations` list of keys, e.g.
    {"domain": "medicine", "attestations": ["not_medical_advice"], "MED_VERIFY": {...}}

Which domains carry which attestation is a deliberate, conservative default (medicine/nutrition/
herb -> not_medical_advice; giving -> not_financial_advice). Extend in domains/base.py.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..gates import ok, reject
from ..packet import GateResult

_NOT_MEDICAL = ("this is reference, not medical advice — the author affirms it directs the user "
                "to a licensed clinician (and 988 / emergency services in a crisis)")
_NOT_FINANCIAL = ("this is reference, not personalized financial advice — the user discerns and "
                  "may consult a professional")


class AttestationValidator:
    """Requires the packet to carry the domain's protective attestation(s) at FLOOR.

    RED (does the artifact hold) stays the verifier's job; this validator adds nothing there.
    FLOOR (did the author affirm the protective framing) is enforced here."""

    domain: str = ""
    required: tuple = ()
    rule: str = ""

    def validate_red(self, packet: Dict[str, Any]) -> List[GateResult]:
        return []  # attestation is a FLOOR concern; RED is the artifact's

    def validate_floor(self, packet: Dict[str, Any]) -> List[GateResult]:
        raw = packet.get("attestations")
        attested = {str(a).strip().lower() for a in raw} if isinstance(raw, list) else set()
        missing = [a for a in self.required if a not in attested]
        if missing:
            return [reject("FLOOR",
                           f"{self.domain}: missing required attestation(s) {missing}",
                           details={"required": list(self.required), "rule": self.rule,
                                    "how": "add these keys to the packet's 'attestations' list"})]
        return [ok("FLOOR", {"attested": sorted(set(self.required) & attested), "rule": self.rule})]


class MedicineValidator(AttestationValidator):
    domain, required, rule = "medicine", ("not_medical_advice",), _NOT_MEDICAL


class NutritionValidator(AttestationValidator):
    domain, required, rule = "nutrition", ("not_medical_advice",), _NOT_MEDICAL


class HerbValidator(AttestationValidator):
    domain, required, rule = "herb", ("not_medical_advice",), _NOT_MEDICAL


class GivingValidator(AttestationValidator):
    domain, required, rule = "giving", ("not_financial_advice",), _NOT_FINANCIAL
