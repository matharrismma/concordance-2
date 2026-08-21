"""Discern — the one door to DISCERNMENT, the twin of the verify moat.

Matt, 2026-08-20: *"What is necessary? This at its core should do two things. It should verify and
discern."* Verify has a single door already — `check` / the moat: a claim in, a sealed three-state
verdict out. Discernment did not; it was scattered across the router, the auditor's extractor, the
relevance floor, the context loop, the candidate engine, the kernel lattice, the crisis net. This is
its single door.

The whole machine in two primitives: **discern proposes, verify disposes.** Discern decides *what* is
worth checking and *what it means*; the gate decides *whether it holds* and proves it. Everything else
is delivery wrapped around the two.

    proposal = discern(anything)          # what KIND · the necessary CLAIM · which MEMBER · the trail
    verdict  = check(proposal["claim"])   # the gate confirms — never discern

The contract, load-bearing:
  * PROPOSES, NEVER CONFIRMS. discern hands candidates to the gate; it returns no verdict. Authority is
    only ever "proposed" here — quarantined < cited < verified is earned at the gate, never granted at
    the door.
  * CRISIS OUTRANKS EVERYTHING. A cry for help is discerned first and routed to real people — never
    reduced to a claim, never sent to the gate.
  * NOTHING IS GENERATED. Discernment is separation over what is given — the necessary is kept, the
    incidental is set aside, the kind is named. No invention.
  * IT EXPLAINS ITSELF. Every proposal carries its `why` — the trail, like router.route.
  * IT FAILS SAFE. When it cannot discern a single answer (nothing brought, a genuine routing tie), it
    says so and asks — it never guesses.

This is a SEED. It unifies the front of discernment — kind (crisis vs claim), the necessity extraction
(the context loop's discriminator: reduce to only what is necessary to check, de-identified), and the
route (which member should verify). The remaining facets — the relevance floor, the candidate
narrowing, the auditor's multi-claim extraction, the moral RED/FLOOR scan — are named in the inventory
and fold in here one at a time, each keeping this contract. Pure: is_crisis, the context loop, and
router.route are all rule-based, no corpus, no model.
"""
from __future__ import annotations

from typing import Any, Dict

# The kinds discern names, and what to do with each.
KINDS = ("empty", "crisis", "claim", "question", "field")
NEXT = ("ask_user", "real_help", "check", "retrieve", "miss", "narrow")


def _relevant(query: str, search_fn=None, relevant_fn=None) -> list:
    """The RELEVANCE floor (folded from ask): from a search over the keeping, keep only the cards whose
    TITLE genuinely names the subject — a real match, not a word-collision ("start a fire" must not
    answer with a knots card that merely says 'fire' once). Returns [] on a genuine gap; a miss stays a
    miss. Injectable so the seed stays pure in tests; defaults to the real corpus + ask's own floor."""
    if search_fn is None:
        from . import corpus
        search_fn = corpus.search
    if relevant_fn is None:
        from . import ask
        relevant_fn = ask._title_names_subject
    try:
        hits = search_fn(query, 5) or []
    except Exception:  # noqa: BLE001 — a missing/partial corpus is a gap, never a crash
        hits = []
    out = []
    for c in hits:
        try:
            if relevant_fn(query, c):
                out.append({"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf")})
        except Exception:  # noqa: BLE001
            continue
    return out


def _extract(claim: str, extract_fn=None) -> list:
    """The structured claim EXTRACTOR (folded from audit): what in the discerned claim is a checkable
    claim, and its structured (domain, spec) — exactly what the gate verifies. Pure and conservative
    (it would rather miss a claim than structure the wrong one). Injectable so the seed stays pure."""
    if extract_fn is None:
        from . import audit
        extract_fn = audit.extract
    try:
        return extract_fn(claim) or []
    except Exception:  # noqa: BLE001 — a non-extractable claim is simply not structured
        return []


def discern(text: str, *, search_fn=None, relevant_fn=None, extract_fn=None,
            lens_fn=None, cloud_fn=None) -> Dict[str, Any]:
    """Propose what matters. Given anything, name its KIND, reduce it to the necessary CLAIM
    (de-identified, framing held home), and either hand the gate the STRUCTURED checkable claim(s) it
    will verify, or discern the genuinely-relevant kept cards (a retrieval). Returns a proposal — never
    a verdict. Crisis is discerned first and routed to real people.

    The WAY OF SEEING is two witnesses, and it is not one man's:
      `lens_fn`  (e.g. lens.see) — the NEAR witness, Matt's own writing. The proposal carries `lens`.
      `cloud_fn` (e.g. the cloud assembler) — the FAR witnesses, the CLOUD: the wise men whose craft bears
                 on this, and their VERBATIM public-domain words. The proposal carries `cloud`.
    Both PROPOSE a way of seeing; neither ever changes the verdict — the gate still disposes, authority is
    still earned. Injected here so the seed stays pure in tests; `served()` binds the real witnesses."""
    from . import ask, context, router

    def _seen(of: str):
        return lens_fn(of) if lens_fn else None

    def _cloud(of: str):
        return cloud_fn(of) if cloud_fn else None

    t = (str(text) if text else "").strip()
    if not t:
        return {"input": text, "kind": "empty", "claim": None, "held": None, "route": None,
                "authority": "proposed", "proposes": True, "confirms": False,
                "why": "nothing was brought", "next": "ask_user"}

    # 1. FRONT DOOR — crisis outranks all. Never a claim, never the gate; always real people.
    if ask.is_crisis(t):
        return {"input": t, "kind": "crisis", "claim": None, "held": t,
                "route": {"member": "crisis", "why": "someone may be in danger — real people first"},
                "resources": list(ask._CRISIS_RESOURCES),
                "authority": "proposed", "proposes": True, "confirms": False,
                "why": "discerned as a cry for help — routed to real people, not the gate",
                "next": "real_help"}

    # 2. NECESSITY — reduce to the necessary, de-identified claim; hold the framing home. (The context
    #    loop's discriminator: only what could change the verdict travels.)
    stripped = context.decontextualize(t, minimal=True)
    claim = stripped.travels()
    held = stripped.framing().strip()      # for display; reattach still uses the full holds, exact

    # 3. EXTRACTION (folded) — the precise claim detector: the STRUCTURED (domain, spec) the gate
    #    verifies. And ROUTE for the trail + the retrieval branch (routed on the claim, not the framing).
    claims = _extract(claim, extract_fn)
    route = router.route(claim or t)
    member = route.get("member")

    # 4. A checkable CLAIM — structured extraction found one, or the router named a specialist. Hand the
    #    gate the structured claim(s); it verifies exactly these (no re-parsing a bare string).
    if claims or (member not in ("search", "ask_user")):
        return {"input": t, "kind": "claim", "claim": claim, "held": held or None,
                "route": route, "claims": claims, "lens": _seen(claim), "cloud": _cloud(claim),
                "authority": "proposed", "proposes": True, "confirms": False,
                "why": ("discerned %d structured claim(s) for the gate to verify" % len(claims) if claims
                        else "discerned the necessary claim %r; the %s should verify it (%s)" % (
                            claim, member, route.get("why"))),
                "next": "check"}

    # 5. RELEVANCE (folded) — a member of "search" is a RETRIEVAL, not a checkable claim. Discern the
    #    genuinely-matching cards (real match vs a word-collision) and propose those; a gap stays a gap.
    if member == "search":
        candidates = _relevant(claim or t, search_fn, relevant_fn)
        return {"input": t, "kind": "question", "claim": claim, "held": held or None,
                "route": route, "candidates": candidates, "lens": _seen(claim or t),
                "cloud": _cloud(claim or t), "authority": "proposed",
                "proposes": True, "confirms": False,
                "why": ("discerned a retrieval; %d kept card(s) genuinely name the subject" % len(candidates)
                        if candidates else
                        "discerned a retrieval, but no kept card genuinely names the subject — a gap"),
                "next": ("retrieve" if candidates else "miss")}

    # 6. A genuine routing tie — ask, never guess.
    return {"input": t, "kind": "claim", "claim": claim, "held": held or None, "route": route,
            "claims": [], "authority": "proposed", "proposes": True, "confirms": False,
            "why": "more than one member fits — %s" % route.get("why"), "next": "ask_user"}


def field(query: str, candidates, *, generator: str = "human",
          generation_method: str = "human", policy_version: str = "v0.1") -> Dict[str, Any]:
    """Discern's DEEP MODE — the archetype (folded #6). When there is not one claim but a WIDE FIELD of
    candidate answers, discern proposes the narrowing: it mints the candidate set, COMMITS it (no
    verification before commitment), and routes each candidate to a verifier under a FIXED, PRE-REGISTERED
    policy that is BLIND to the generator's proposal_weight. It hands back the committed, routed field —
    the gate (candidates.narrow) then eliminates to a survivor. Discern proposes the field; verify
    disposes of it. Everything is born quarantined; a lone winner exists only when exactly one passes.

    `candidates`: raw strings, or {raw_text, proposal_weight?} — the weight is carried verbatim and read
    by NOTHING in the routing, so a confident-but-wrong candidate gets no easier path to survival."""
    from . import candidates as _cand
    cset = _cand.create_set(query, list(candidates), generator, generation_method)
    cset = _cand.commit(cset)
    routing = _cand.route(cset, policy_version=policy_version)
    routes = routing.get("routes", {})
    routable = sum(1 for r in routes.values() if r.get("mode"))
    n = len(cset.get("candidates", []))
    return {"query": query, "kind": "field", "n_candidates": n, "committed": True,
            "policy_version": policy_version, "routing": routing, "routable": routable,
            "authority": "proposed", "proposes": True, "confirms": False,
            "why": "proposed a field of %d candidate(s), committed and routed under policy %s "
                   "(blind to the generator's weight); %d have a verifier — the gate narrows" % (
                       n, policy_version, routable),
            "next": "narrow", "cset": cset}


def _lens_see(text: str):
    """The NEAR witness — Matt's OWN writing. His writing is NEVER published, so it is served only on a
    SOVEREIGN node (CONCORDANCE_SOVEREIGN_NODE set — his own machine). On the shared/public surface it is
    never served, even if a corpus file were somehow present: a structural guard for the frozen invariant,
    fail-closed, not left to the file's absence (mirrors the /context/run gate). Honest-None where not
    served or not gathered; proposes, never confirms."""
    import os
    # An EXPLICIT truthy allowlist — never "any non-empty string". Otherwise an operator who sets the flag
    # to "0"/"false"/"off" intending to DISABLE sovereign mode would inadvertently serve the private lens.
    if os.environ.get("CONCORDANCE_SOVEREIGN_NODE", "").strip().lower() not in ("1", "true", "yes", "on"):
        return None                                  # a shared node never serves his private writing
    from . import lens
    try:
        return lens.see(text)
    except Exception:  # noqa: BLE001 — an ungathered lens is a trailhead, never a crash
        return None


def _cloud_see(text: str):
    """The FAR witnesses — the CLOUD. Which wise men's craft bears on this (their characterized gift and
    the discern note that weighs it), and their VERBATIM public-domain words that frame it (Ellen G. White
    and the rest, PD-gated). It is not one man's seeing. Proposes a way of seeing; the Word disposes —
    never confirmed past what a witness earned. Nothing generated; honest-empty where the cloud does not
    reach."""
    from . import mentors, witness
    try:
        craft = mentors.for_text(text)
    except Exception:  # noqa: BLE001
        craft = None
    try:
        voice = witness.see(text, k=2)
    except Exception:  # noqa: BLE001
        voice = None
    return {"mentors": craft, "voice": voice, "proposes": True, "confirms": False,
            "note": "how the cloud of witnesses sees this — the wise men's craft and their verbatim "
                    "public-domain words, weighed against the Source, never confirmed past what they earned"}


def served(text: str, **kw) -> Dict[str, Any]:
    """Discern with the full WAY OF SEEING wired — the NEAR witness (Matt's lens) AND the FAR witnesses
    (the cloud). This is what the served surfaces call; the bare `discern()` stays pure for tests. Extra
    kwargs (search_fn, extract_fn…) pass through. It isn't just one man's seeing — the cloud extends it."""
    kw.setdefault("lens_fn", _lens_see)
    kw.setdefault("cloud_fn", _cloud_see)
    return discern(text, **kw)


__all__ = ["discern", "served", "field", "KINDS", "NEXT"]
