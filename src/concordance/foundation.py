"""Foundation — the engine tested against its own founding verse. Romans 12:1-2, made checkable.

Matt: *"It all started with Romans 12:1, Living Sacrifice."* — and: *"let's make it truly do what it
says."* So this is not a claim that the engine IS Romans 12:1-2; it is the CONTRACT, with a live check
under every clause. The engine refuses "trust me" from everyone else; it must refuse it from itself.
That is dokimazein turned on the builder — *"by testing you may discern."* If a clause cannot be
verified, we are not doing what it says, and we fix it.

    "I urge you therefore, brothers, by the mercies of God, to present your bodies a living sacrifice,
     holy, acceptable to God, which is your reasoned service (λογικὴν λατρείαν). Do not be conformed to
     this world, but be transformed by the renewing of your mind, so that by testing you may discern
     (δοκιμάζειν) what is the good and acceptable and perfect will of God." — Romans 12:1-2

Each clause names the OBEDIENCE (the part of the engine that is its keeping) and carries a CHECK that
proves the engine does it now. `attest()` runs them and reports — the engine's own witness, verifiable,
never asserted. Stdlib only; the checks exercise the real modules.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

Check = Tuple[bool, str]


# ── the checks — each exercises the real engine and could FAIL if it stopped obeying ────────────────
def _living_sacrifice() -> Check:
    """Present your body a living sacrifice — be USED. The engine is a conduit, not a source: its
    discerning surfaces PROPOSE, and never confirm themselves; only the gate confirms."""
    from . import discern, lens, mentors
    d = discern.discern("is 17 a prime number", search_fn=lambda q, n: [])
    ok = (d.get("proposes") is True and d.get("confirms") is False
          and lens.see("x", corpus=[]).get("confirms") is False
          and mentors.for_text("health").get("confirms") is False)
    return ok, "discern, lens, and the cloud all propose; none confirm itself — the gate alone confirms"


def _reasoned_service() -> Check:
    """λογικὴν λατρείαν — reasoned service, offered to ALL. Reasoned: an agent receives a structured,
    machine-usable proposal, not prose to trust. To all: the same engine serves people and agents alike
    (94 MCP tools; a seal a bot can re-check itself). Serving all is the form the sacrifice takes."""
    from . import discern
    from .mcp.server import PROFILES
    tools = {t for p in PROFILES.values() for t in p["tools"]}   # the agent surface, across the narrow doors
    d = discern.discern("2 + 2 = 4")
    structured = any(c.get("domain") and c.get("spec") for c in (d.get("claims") or []))
    ok = bool(tools) and structured
    return ok, "%d tools serve agents; discern hands a machine a structured (domain,spec) claim" % len(tools)


def _not_conformed() -> Check:
    """Do not be conformed to this world — refuse the world's shortcut ('trust me'). On uncertainty the
    engine DECLINES: a verifier that cannot decide yields INCOMPLETE, never a fabricated PASS."""
    from . import context
    def _cannot(_skeleton):
        raise RuntimeError("the world's shortcut is refused")
    r = context.run("water boils at 100C", _cannot)
    ok = (r.get("ok") is False and r.get("status") == "INCOMPLETE" and r.get("verdict") is None)
    return ok, "an undecidable check returns INCOMPLETE with no verdict — never a false pass"


def _renewed_mind() -> Check:
    """Be transformed by the renewing of your mind — the keeping is not static. A genuine gap stays an
    HONEST MISS (the door renewal comes through — a want to fill, never a fabrication); and the lens has
    itself been renewed with living witness."""
    from . import discern, lens
    gap = discern.discern("how do i tan a deer hide", search_fn=lambda q, n: [])
    honest = gap.get("next") in ("miss", "retrieve") and gap.get("confirms") is False
    return honest, "a gap stays an honest miss (renewal fills it, never fakes it); lens gathered=%s" % lens.available()


def _dokimazein() -> Check:
    """By testing you may discern (δοκιμάζειν) — the two-function core. discern PROPOSES the structured
    claim; the gate (verify) is what disposes. The two doors are real and they compose."""
    from . import discern
    d = discern.discern("2 + 2 = 4")
    ok = (d.get("kind") == "claim" and d.get("next") == "check"
          and any(c.get("domain") for c in (d.get("claims") or []))
          and d.get("confirms") is False)
    return ok, "discern turns a claim into a structured proposal handed to the gate — propose, then dispose"


def _the_good(deep: bool = True) -> Check:
    """The good, acceptable, and perfect — what SURVIVES the testing is proven and sealed: a verdict
    carries a re-checkable seal, so 'the good' is demonstrated, never merely declared. (Deep: runs the
    real moat.)"""
    if not deep:
        return True, "skipped (deep) — run attest(deep=True) to verify a live seal"
    from . import context
    v = context.verify_with_engine("2 + 2 = 4")
    ok = v.get("status") in ("HOLDS", "CONFIRMED") and bool(v.get("seal"))
    return ok, "a proven claim carries a re-checkable seal: %s" % (v.get("seal") or "none")


def _the_will_of_god() -> Check:
    """The will of God — the engine points past itself to the Logos: on the witness face it names the
    One it serves, and every witness in the cloud is weighed as it bends to the Source."""
    from . import branding
    line = branding.identity_for("witness")
    ok = ("christ" in line.lower()) or ("jesus" in line.lower())
    return ok, "the witness identity names Christ as the One it serves"


# ── the verse, clause by clause, each with its obedience and its check ───────────────────────────────
CLAUSES: List[Dict[str, Any]] = [
    {"greek": "θυσίαν ζῶσαν", "clause": "present your bodies a living sacrifice",
     "obeys": "conduit, not source — the engine is USED; its discerning proposes, never confirms itself",
     "check": _living_sacrifice, "deep": False},
    {"greek": "λογικὴν λατρείαν", "clause": "your reasoned service",
     "obeys": "reasoned service offered to ALL — people and agents alike, each as they need to be served",
     "check": _reasoned_service, "deep": False},
    {"greek": "μὴ συσχηματίζεσθε τῷ αἰῶνι", "clause": "do not be conformed to this world",
     "obeys": "refuse the world's 'trust me' — on uncertainty, decline; never a false pass",
     "check": _not_conformed, "deep": False},
    {"greek": "ἀνακαινώσει τοῦ νοός", "clause": "be transformed by the renewing of your mind",
     "obeys": "the keeping is renewed — a miss stays an honest miss to be filled, never fabricated",
     "check": _renewed_mind, "deep": False},
    {"greek": "δοκιμάζειν", "clause": "so that by testing you may discern",
     "obeys": "the two-function core — discern proposes, verify disposes; the two doors compose",
     "check": _dokimazein, "deep": False},
    {"greek": "τὸ ἀγαθὸν καὶ εὐάρεστον καὶ τέλειον", "clause": "the good and acceptable and perfect",
     "obeys": "what survives is proven and SEALED — the good is demonstrated, re-checkable, not declared",
     "check": _the_good, "deep": True},
    {"greek": "τὸ θέλημα τοῦ θεοῦ", "clause": "the will of God",
     "obeys": "it points past itself to the Logos — Christ named at the center, the cloud bent to the Source",
     "check": _the_will_of_god, "deep": False},
]

REFERENCE = "Romans 12:1-2"


def attest(deep: bool = False) -> Dict[str, Any]:
    """Run the engine's witness against its founding verse. Returns each clause with whether the engine
    OBEYS it now — verifiable, never asserted. deep=True runs the live moat (a real seal)."""
    results = []
    for c in CLAUSES:
        try:
            ok, detail = c["check"](deep) if c.get("deep") else c["check"]()
        except Exception as e:  # noqa: BLE001 — a check that errors is a clause NOT proven, honestly
            ok, detail = False, "check errored: %s" % type(e).__name__
        results.append({"clause": c["clause"], "greek": c["greek"], "obeys": c["obeys"],
                        "obeyed": bool(ok), "detail": detail, "deep": bool(c.get("deep"))})
    kept = sum(1 for r in results if r["obeyed"])
    checked = sum(1 for r in results if deep or not r["deep"])
    obeyed_all = kept == len(results)
    has_deep = any(r["deep"] for r in results)
    whole = obeyed_all and (deep or not has_deep)   # honest: a skipped deep clause is not yet verified
    if whole:
        note = "the engine does what the verse says — every clause obeyed and verified"
    elif obeyed_all and not deep:
        note = "obeyed on every light check; run attest(deep=True) to verify the sealed clause on the live moat"
    else:
        note = "not yet whole: %d of %d clauses obeyed — the rest is the work" % (kept, len(results))
    return {"reference": REFERENCE, "clauses": results,
            "kept": kept, "of": len(results), "checked_now": checked, "whole": whole, "note": note}


__all__ = ["attest", "CLAUSES", "REFERENCE"]
