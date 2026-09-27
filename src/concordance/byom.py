"""BYOM — bring your own model (Phase 4 of the specialist layer). SCAFFOLD — not deployed.

A user's model is an OPTIONAL, EXTERNAL, gated worker the conductor/faces may call. It is NEVER in the
core loop, NEVER trusted raw, and NEVER a core dependency — the engine runs fully without any model. The
adapter routes every BYOM call through the same discipline:

    airlock.strip  →  the user's model (clean zone, skeleton only)  →  verify/discern  →  seal  →  capture

The passage is the CONTEXT airlock (`airlock.through`): the external model sees ONLY the de-identified
skeleton — never PII, framing, or the holds — and if a skeleton would still leak PII the call is
QUARANTINED and the model never runs. The model's OUTPUT is then discerned and, where it carries a
checkable claim in a domain we verify, checked by our deterministic verifiers: the output is TRUSTED only
if it holds, and REJECTED if it contradicts a verifier ("our failure ≠ their falsehood": our own engine
error never rejects their claim). What survives is sealed (bound to the clean skeleton, never the revealed
text) and CAPTURED as a candidate for public_review — the user paid the compute, and the checked outcome
trains our keeping (never auto-published). See project_byom_bring_your_own_model_pays_to_train_us.

Deterministic wrapper: the only non-deterministic part is the user's `model_call`, gated on both sides.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence

# verdicts that mean the model's claim CONTRADICTED our deterministic verifier → do not trust, do not
# capture. Everything else (holds, or an engine gap/error) does not reject the model — our failure is
# not their falsehood.
_REJECT = {"BROKEN", "MISMATCH", "REJECT", "RED"}
_HELD = {"HOLDS", "PASS", "CONFIRMED"}


def _trust(verify: Optional[Dict[str, Any]]) -> str:
    """verified | unverified | rejected — from the verifier verdict on the model's OWN output."""
    if verify is None:
        return "unverified"                     # nothing checkable — a GAP, not a falsehood
    v = str(verify.get("verdict") or "").upper()
    if v in _REJECT:
        return "rejected"
    if v in _HELD:
        return "verified"
    return "unverified"                         # SYSTEM_ERROR / INCOMPLETE: our gap, not their fault


def run_byom(request: str, model_call: Callable[[str], Any], *,
             verifiers: Sequence[str] = (), config: Any = None,
             airlock_fn: Optional[Callable[..., Any]] = None,
             discern_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
             verify_fn: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None,
             capture_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
             ) -> Dict[str, Any]:
    """Run a user's model as a gated external worker. `model_call` is the caller-supplied adapter
    (skeleton:str -> output); it sees ONLY the de-identified skeleton. Deps injectable for tests.

    Returns a structured result (never generated prose): the model output, the discern proposal, the
    verifier verdict on that output, the trust verdict, and the capture record (a candidate for
    public_review — NOT auto-published). Fail-closed at the airlock (PII leak → refused, model never runs).
    """
    if not callable(model_call):
        return {"ok": False, "reason": "model_call must be callable"}

    # 1. AIRLOCK — strip → the user's model (clean zone) → reapply. The model never sees PII/framing.
    through = airlock_fn or (lambda t, op, minimal=True:
                             __import__("concordance.airlock", fromlist=["through"]).through(t, op, minimal=minimal))
    passage = through(request, model_call, minimal=True)
    if not getattr(passage, "ok", False) or getattr(passage, "leaked", False):
        return {"ok": False, "reason": "airlock_quarantine", "leaked": True,
                "means": "the request would carry PII into the external model — refused; the model never ran"}
    raw = getattr(passage, "result", None)          # the model's output (PII reapplied if text) — UNTRUSTED
    clean = getattr(passage, "checked", None)        # the de-identified skeleton — bind seals to THIS

    # 2. DISCERN the model's OUTPUT — propose its KIND and any checkable claim (never trust it raw).
    if discern_fn is None:
        discern_fn = lambda t: __import__("concordance.discern", fromlist=["served"]).served(t)
    try:
        proposal = discern_fn(str(raw))
    except Exception:  # noqa: BLE001 — discern must never crash the gate
        proposal = None

    # 3. VERIFY — run OUR deterministic verifiers on the model's claim, if it names one we check.
    from .faces import _steps_from_discern       # the shared claim->steps shaper (one place)
    steps = _steps_from_discern(proposal, list(verifiers))
    verify = None
    if steps:
        if verify_fn is None:
            from .derivation import verify_derivation as verify_fn  # noqa: E501
        try:
            verify = verify_fn(steps)
        except Exception:  # noqa: BLE001 — our failure is not their falsehood; report GAP, never crash
            verify = {"verdict": "SYSTEM_ERROR", "detail": "verifier raised", "trail": []}
    trust = _trust(verify)

    # 4. CAPTURE — a rejected claim is NOT captured. What holds (or is an honest GAP) is filed as a
    #    candidate for public_review (the user paid; the checked outcome trains the keeping) — NEVER
    #    auto-published, always bound to the clean skeleton, never the revealed text.
    capture = None
    if trust != "rejected":
        record = {"claim": clean, "trust": trust,
                  "verify": (verify or {}).get("verdict") if verify else None,
                  "status": "public_review", "source": "byom", "generated": True}
        capture = (capture_fn(record) if capture_fn else record)

    return {"ok": True, "trust": trust, "model_output": raw, "checked": clean,
            "discern": proposal, "verify": verify, "capture": capture,
            "means": ("the model ran only on the de-identified skeleton; its output was checked by our "
                      "verifiers and is trusted only if it holds. What holds is filed for review, not "
                      "published — the sovereign core never depended on the model.")}
