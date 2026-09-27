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

import ipaddress
import json
import socket
import urllib.request
from urllib.parse import urlparse
from typing import Any, Callable, Dict, List, Optional, Sequence


def _guard_url(url: str) -> str:
    """SSRF guard: only http(s) to a PUBLIC host — never localhost/private/link-local/reserved. Defense
    in depth behind the CONCORDANCE_BYOM_ENABLED flag: a user's model lives on a public endpoint (their
    cloud API or server), so nothing internal is ever a legitimate BYOM target."""
    u = urlparse(url or "")
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("model base_url must be an http(s) URL with a host")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80))
    except OSError as e:  # noqa: BLE001
        raise ValueError(f"model host does not resolve: {u.hostname}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("model base_url must be a PUBLIC host (no localhost/private/internal targets)")
    return url


def openai_adapter(model_cfg: Dict[str, Any]) -> Callable[[str], str]:
    """Build a `model_call(skeleton)->str` for any OpenAI-compatible endpoint (OpenAI, Anthropic-compat,
    a local server exposed publicly, Sakana Fugu, …) from the user's own {base_url, api_key, model}. The
    caller pays; the airlock has already stripped PII from the skeleton before it reaches this. SSRF-
    guarded. This is the ONE place BYOM touches an external model; run_byom gates it on both sides."""
    base = _guard_url(str(model_cfg.get("base_url") or ""))
    key = str(model_cfg.get("api_key") or "")
    model = str(model_cfg.get("model") or "")
    if not model:
        raise ValueError("model name required")

    def model_call(skeleton: str) -> str:
        payload = json.dumps({"model": model, "temperature": 0,
                              "messages": [{"role": "user", "content": skeleton}]}).encode("utf-8")
        req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=payload,
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return str(((d.get("choices") or [{}])[0].get("message") or {}).get("content") or "")

    return model_call

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
            "had_pii": bool(getattr(passage, "held_pii", ())),
            "discern": proposal, "verify": verify, "capture": capture,
            "means": ("the model ran only on the de-identified skeleton; its output was checked by our "
                      "verifiers and is trusted only if it holds. What holds is filed for review, not "
                      "published — the sovereign core never depended on the model.")}


def ingest(query: str, model_call: Callable[[str], Any], *, config: Any = None,
           verifiers: Sequence[str] = (), keep_fn: Optional[Callable[[list], int]] = None,
           **run_kw) -> Dict[str, Any]:
    """Fill a GAP the keeping does not hold with a user's model, then KEEP the checked answer as a card —
    "you have it in your own once ingested". Model-derived, so it enters `public_review` (withheld from
    public reads until a human reviews SOURCE + QUALITY), generated=True, tagged with the model as source
    and the verifier verdict as its quality tier. NOT kept when the answer was REJECTED (our verifier
    broke it) or when the query carried PII (personal — answered for the caller, never written to the
    shared corpus). The same acquire→public_review path as `expand` (one mechanism); `keep_fn` injectable."""
    r = run_byom(query, model_call, verifiers=verifiers, config=config, **run_kw)
    if not r.get("ok"):
        return {**r, "status": "refused"}
    if r.get("trust") == "rejected":
        return {**r, "status": "rejected",
                "message": "the model's answer contradicted our verifier — not ingested"}
    if r.get("had_pii"):
        return {**r, "status": "not_ingested",
                "message": "the question carried personal context — answered for you, never written to "
                           "the shared corpus (a gap-fill is general knowledge, not a private matter)"}
    card = _ingest_card(query, r)
    if keep_fn is None:
        from .expand import _keep as keep_fn
    try:
        kept = keep_fn([card])
    except Exception as e:  # noqa: BLE001 — a keep failure must not lose the answer for the caller
        return {**r, "status": "answered_keep_failed", "card_id": card["id"], "error": str(e)}
    return {"status": "ingested", "card_id": card["id"], "trust": r["trust"],
            "lifecycle_stage": "public_review", "quality_tier": card["source"]["authority_tier"],
            "kept": kept, "model_output": r["model_output"], "verify": r["verify"],
            "means": ("filled a gap and KEPT the checked answer as a review candidate — model-derived, so "
                      "held in public_review (source + quality reviewed before it is shared); once cleared, "
                      "recall serves it and no model is called for it again")}


def _ingest_card(query: str, r: Dict[str, Any]) -> Dict[str, Any]:
    """A public_review card from a checked BYOM answer, BOUND TO THE CLEAN SKELETON (never revealed PII).
    generated=True (a model produced it); quality tier = the verifier verdict on the model's own claim."""
    import hashlib
    clean = str(r.get("checked") or query)
    answer = str(r.get("model_output") or "")
    sha = hashlib.sha256((clean + "\n" + answer).encode("utf-8")).hexdigest()
    tier = {"verified": "byom_verified"}.get(r.get("trust"), "byom_unverified")
    subj = " ".join(clean.split())[:120]
    return {
        "id": "card_byom_" + sha[:16], "kind": "reference",
        "title": subj or "a gap the keeping did not hold",
        "body": answer[:2400],
        "source": {"label": "BYOM — a user-attached model; the engine checked this answer",
                   "url": "", "domain": "", "authority_tier": tier},
        "shelf": "sources", "box": "byom", "subject": subj,
        "bands": sorted({w for w in subj.lower().split() if len(w) > 2})[:10] + ["byom", "public-review"],
        "connections": [{"to_card_id": "card_spine_sources", "relationship": "member_of",
                         "evidence": "an answer a user's model gave to fill a gap the keeping did not hold"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public_review",   # model-derived: never auto-public; a human reviews source+quality
        "volatility": "permanent", "surface": "secular", "generated": True,
        "extra": {"byom": True, "trust": r.get("trust"),
                  "verify": (r.get("verify") or {}).get("verdict") if r.get("verify") else None,
                  "skeleton_sha256": sha},
    }
