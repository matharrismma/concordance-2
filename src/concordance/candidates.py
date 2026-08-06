"""Candidates — the CandidateSet: a governed narrowing layer between generators and the moat.

Task #135, adopted from the external red-team assessment
(docs/RED_TEAM_CANDIDATE_ENGINE_2026-08-05.md). Matt's go, verbatim: "the point of narrow
highway is to narrow the possibilities. The candidate engine is what we've been missing, but
was originally a part of the project."

A generative model is Zone B — untrusted, proposal-only (assessment §1.1). What it emits is a
CANDIDATE SET: several raw alternatives, each carrying whatever weight the generator chose to
verbalize. This module is Zone C — it governs candidate-set INTEGRITY (commitment, fixed
routing, complete retention, the receipt); it never decides truth. Truth stays in Zone D, the
derivation moat, which knows nothing about candidates and so cannot be shopped after the fact.

THE INVARIANT (assessment §5.2, quoted verbatim — every function below serves it):

    "No candidate may move from proposal to verified fact merely because it has a high
    proposal_weight, appears in several correlated samples, or wins a model-based ranking."

Made structural, not aspirational:
  * proposal_weight is stored VERBATIM as untrusted metadata and read by NOTHING here — a
    test greps route()'s and narrow()'s source to prove the field name never appears in the
    deciding code (§6, probability laundering).
  * commit() hashes the COMPLETE raw set BEFORE any evaluation; route()/narrow()/receipt()
    refuse an uncommitted or altered set (§6, selective disclosure).
  * routing is a FIXED, PRE-REGISTERED policy: the verifier is chosen by claim SHAPE before
    outcomes are observed, never per-candidate after them (§6, verification shopping).
  * narrow() preserves EVERY candidate — the rejected and the quarantined ride in the trace
    and the receipt beside the selected (§4.2, winner-only retention refused).

The stage order is the report's own (§5): create → commit → route → narrow → receipt. Each
stage refuses to run out of order — combined surfaces obscure where nondeterminism ended and
deterministic checking began (§8.2).

Deterministic on purpose: every id and hash is CONTENT-ADDRESSED through the ONE canonical
form (validate.canonical_json_bytes — the same bytes tools/verify_seal.py rechecks with no
Narrow Highway code), and no clock is read anywhere in this module, so the same input always
mints the same set id and the same commitment.

Sovereign: stdlib + the floor (validate, cas, derivation, receipts) only. No I/O except the
best-effort seal in receipt(); everything else is pure functions over dicts.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from . import cas, validate
from .config import EngineConfig

# Version tag baked into every hashed material so future schema revisions can coexist
# without collision — the same discipline as identity._FP_VERSION and cas's layout.
SCHEMA_VERSION = "cset0.1"
_SET_PREFIX = "cset_"
# Length (hex chars) of the digest kept in the set id. 32 hex = 128 bits — identity.py's
# fingerprint discipline (_FP_HEX_LEN): ample collision resistance, short enough to show.
_ID_HEX = 32

# Cost-denial guards (assessment §6: "Attacker forces large k, recursion, or expensive
# verifiers"). Bounded at BIRTH, before anything downstream pays for the set. The raw-text
# ceiling matches the moat's own _MAX_SPEC_CHARS and the MCP schema floor's _STR_MAXLEN —
# one ceiling, three doors.
_MAX_CANDIDATES = 64
_MAX_RAW_CHARS = 4000

# The generator provenance vocabulary, from the assessment's own schema row (§5.1:
# "direct, VS, multi-agent, retrieval-guided, adversarial") plus the human submissions §14
# names among the replaceable generators. Unknown methods are REFUSED, not stored — a typed
# name is not authority, and an unclassifiable provenance is no provenance at all.
GENERATION_METHODS = ("direct", "vs", "multi-agent", "retrieval-guided", "adversarial", "human")

# Bounded per-candidate vocabularies (assessment §5.1). Declared here so a reader — or a
# schema — can see the whole space of things a candidate may ever be called.
SAFETY_STATUSES = ("allow", "restrict", "reject", "human-review")
VERIFICATION_STATUSES = ("pass", "reject", "quarantine", "not-applicable")
SELECTION_STATUSES = ("selected", "rejected", "retained-alternative")

# THE DECLARED SELECTION RULE — registered here, in code, before any outcome exists, because
# a narrowing policy declared after outcomes can rationalize any preferred answer (§7).
SELECTION_RULE = (
    "v0.1: every verification-passing candidate is selected-eligible; one candidate is marked "
    "'selected' only when EXACTLY ONE passes. More than one pass -> all passing candidates stay "
    "'retained-alternative' (the decision is underdetermined and material alternatives must be "
    "presented, assessment §7.1). Failing -> 'rejected'. Unresolved -> 'retained-alternative'."
)

# ── THE PRE-REGISTERED ROUTING POLICY (assessment §6, verification shopping) ─────────────────
# The whole table, in one literal, registered WITH the module — never assembled at call time,
# never influenced by a candidate's content beyond its SHAPE, never chosen after outcomes.
# ORDER MATTERS: first match wins, and inequality is tested before equality because '<=' and
# '>=' contain '='. Modes are validated against derivation._MATH_MODES at route() time —
# sourced from the moat, never copied (the vine, not a photograph; same discipline as the MCP
# server's _enum_wiring) — so the policy cannot silently name a verifier that no longer exists.
ROUTING_POLICY: Dict[str, Dict[str, Any]] = {
    "v0.1": {
        "registered": "2026-08-05",   # the day the red team specified it; before any outcome
        "rules": (
            # (rule name, verifier mode, what the claim must look like)
            ("inequality", "inequality", "two arithmetic sides joined by < <= > or >="),
            ("equality", "equality", "two arithmetic sides joined by = or =="),
        ),
        "default": "quarantine",      # the unroutable is HELD, never judged
    },
}

_INEQ_RE = re.compile(r"(<=|>=|<|>)")
# A multi-letter token is a WORD, not a symbol. sympy would happily read 'kingdom' and
# 'heaven' as free symbols and return MISMATCH — minting a REJECT on a sentence that was
# never arithmetic. Routing a value/prose claim to a truth verifier is exactly the mis-typing
# the assessment prohibits (§7.1: "do not apply truth verifiers to values, creative options,
# or preferences"), so prose defaults to quarantine, not judgement.
_WORD_RE = re.compile(r"[A-Za-z]{2,}")
_SIDE_RE = re.compile(r"[0-9A-Za-z+\-*/^() .,%]+")
_VAR_RE = re.compile(r"\b[A-Za-z]\b")


def _normalize(text: str) -> str:
    """v0.1 query/prompt normalization: strip + collapse whitespace runs. Deliberately
    minimal — anything cleverer (case folding, punctuation stripping) starts changing what
    the person actually asked, and the hash must witness THEIR request."""
    return " ".join(str(text).split())


def _hash_text(text: str) -> str:
    """SHA-256 over the normalized UTF-8 text — integrity metadata per the report schema
    (§5.1: query_hash, prompt_hash). The raw query/prompt is deliberately NOT stored in the
    set: copying sensitive input across candidates, logs and receipts is the privacy
    multiplication the threat model names (§6)."""
    return validate.sha256_bytes(_normalize(text).encode("utf-8"))


def _raw_material(cset: Dict[str, Any]) -> Dict[str, Any]:
    """The canonical RAW set — exactly what was generated, nothing that was later derived.

    Both the set id and the commitment are computed over this material, so the two can be
    cross-checked against each other. The generator's proposal_weight values are INSIDE the
    material on purpose: the commitment freezes them with the text, or an operator could
    re-weight candidates after seeing verdicts and present the rewrite as the original
    generation. Statuses, routing, evidence and trace are all EXCLUDED — they are Zone C/D
    products, and hashing them here would let evaluation reach back into the commitment.
    """
    raw: List[Dict[str, Any]] = []
    for c in cset["candidates"]:
        entry: Dict[str, Any] = {"candidate_id": c["candidate_id"], "raw_text": c["raw_text"]}
        if "proposal_weight" in c:
            entry["proposal_weight"] = c["proposal_weight"]
        raw.append(entry)
    return {"schema": SCHEMA_VERSION,
            "query_hash": cset["query_hash"],
            "generator": cset["generator"],
            "generation_method": cset["generation_method"],
            "prompt_hash": cset["prompt_hash"],
            "candidates": raw}


def create_set(query: str, candidates: List[Union[str, Dict[str, Any]]], generator: str,
               generation_method: str, prompt: Optional[str] = None) -> Dict[str, Any]:
    """Mint a CandidateSet from RAW generator output. Zone B ends at this door.

    `candidates` is a list of raw strings, or dicts {raw_text, proposal_weight?} ("text" is
    accepted as an alias for raw_text). The weight is copied VERBATIM and never normalized,
    defaulted, or read again by this module — an absent weight stays absent, because inventing
    one would be this module authoring the very metadata it has sworn not to trust (§4.2:
    "Verbalized probability as confidence" is a concept NOT to inherit).

    Everything is born quarantined: verification_status 'quarantine', selection_status
    'retained-alternative'. Nothing is verified at birth, whatever the generator claimed and
    however many correlated samples agreed with each other (§4.2, single-model diversity).

    The set id is content-addressed over the canonical raw material — no clock, no counter,
    no randomness — so the same generation always mints the same id, and commit() can later
    prove membership never moved between birth and commitment.

    Fails closed on anything malformed: empty query, no candidates, more than
    _MAX_CANDIDATES (cost denial, §6), oversized raw_text, an unregistered generation
    method, or unknown candidate keys. A field we did not declare is a field we cannot
    account for in the hash, so it is refused rather than silently carried.
    """
    q = str(query or "").strip()
    if not q:
        raise ValueError("query is required — a candidate set answers a stated request")
    gen = str(generator or "").strip()
    if not gen:
        raise ValueError("generator is required — provenance is not optional (assessment §5.1)")
    method = str(generation_method or "").strip().lower()
    if method not in GENERATION_METHODS:
        raise ValueError(f"generation_method must be one of {sorted(GENERATION_METHODS)}, "
                         f"got {generation_method!r} — an unregistered method is unaccountable "
                         f"provenance, refused")
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("candidates is required — a non-empty list of raw strings or "
                         "{raw_text, proposal_weight?} dicts")
    if len(candidates) > _MAX_CANDIDATES:
        raise ValueError(f"at most {_MAX_CANDIDATES} candidates per set — an unbounded k is "
                         f"the cost-denial attack (assessment §6); split the generation")

    born: List[Dict[str, Any]] = []
    for i, item in enumerate(candidates):
        if isinstance(item, str):
            raw, weight, has_weight = item, None, False
        elif isinstance(item, dict):
            unknown = set(item) - {"raw_text", "text", "proposal_weight"}
            if unknown:
                raise ValueError(f"candidate {i} carries unknown keys {sorted(unknown)} — "
                                 f"only raw_text (or text) and proposal_weight are declared; "
                                 f"an undeclared field cannot be accounted for in the hash")
            if "raw_text" in item and "text" in item:
                raise ValueError(f"candidate {i} names its text twice (raw_text AND text) — "
                                 f"give it one name")
            raw = item.get("raw_text", item.get("text"))
            has_weight = "proposal_weight" in item
            weight = item.get("proposal_weight")
        else:
            raise ValueError(f"candidate {i} must be a raw string or a dict, "
                             f"got {type(item).__name__}")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"candidate {i} has no raw_text — an empty candidate is not a "
                             f"proposal")
        if len(raw) > _MAX_RAW_CHARS:
            raise ValueError(f"candidate {i} raw_text exceeds {_MAX_RAW_CHARS} chars — a "
                             f"candidate is a claim, not a document")
        if has_weight:
            try:
                validate.canonical_json_bytes(weight)
            except TypeError:
                raise ValueError(f"candidate {i} proposal_weight is not JSON-serializable — "
                                 f"the set must stay content-addressable") from None
        cand: Dict[str, Any] = {
            # Stable positional id within the set (§5.1). Zero-padded so ids sort as they
            # were generated; 3 digits covers _MAX_CANDIDATES with room for growth.
            "candidate_id": f"c{i:03d}",
            "raw_text": raw,
        }
        if has_weight:
            cand["proposal_weight"] = weight   # VERBATIM; untrusted metadata, never evidence
        cand.update({
            "cluster_id": None,                     # v0.1: no dedup pass; reversible
                                                    # lineage-keeping clustering is a later stage
            "safety_status": "allow",               # v0.1: no safety prefilter wired yet; the
                                                    # field is first-class so the gate (§6,
                                                    # tail-risk) has a declared place to land
            "verification_status": "quarantine",    # nothing is verified at birth
            "selection_status": "retained-alternative",
            "parent_ids": [],                       # lineage for recursive rounds; v0.1 mints
                                                    # only first-round sets
        })
        born.append(cand)

    cset: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "query_hash": _hash_text(q),
        "generator": gen,
        "generation_method": method,
        "prompt_hash": _hash_text(prompt) if prompt is not None and str(prompt).strip() else None,
        "candidates": born,
    }
    cset["candidate_set_id"] = _SET_PREFIX + validate.content_hash(_raw_material(cset))[:_ID_HEX]
    return cset


def commit(cset: Dict[str, Any]) -> Dict[str, Any]:
    """Hash the COMPLETE raw candidate set before any evaluation — the commitment (§5 stage 2).

    This is the anti-selective-disclosure gate (§6): once the full membership is committed,
    an unfavorable candidate cannot be quietly dropped after checking, and a favorable
    late-comer cannot be quietly added. The commitment is the full canonical SHA-256 over the
    raw material; the set id minted at birth is a truncation of the same digest, so commit()
    cross-checks them and REFUSES if membership moved between birth and commitment.

    Also refuses if any evaluation already happened (routing or trace present, or any
    candidate out of quarantine): a commitment made after outcomes are observed commits to
    nothing. Idempotent — committing twice over unchanged membership is a no-op.

    Membership is then frozen two ways. The candidates list becomes a TUPLE, so append and
    remove raise structurally; and every later stage recomputes this hash and refuses on
    mismatch — the authoritative check, which a swapped-in list cannot sneak past.
    """
    if "routing" in cset or "trace" in cset:
        raise ValueError("commitment must precede evaluation — this set has already been "
                         "routed or narrowed, and committing now would bless outcomes already "
                         "observed (assessment §5 stage 2)")
    for c in cset["candidates"]:
        if c.get("verification_status") != "quarantine":
            raise ValueError(f"commitment must precede evaluation — {c.get('candidate_id')} "
                             f"already carries verification_status "
                             f"{c.get('verification_status')!r}")
    full = validate.content_hash(_raw_material(cset))
    if cset.get("candidate_set_id") != _SET_PREFIX + full[:_ID_HEX]:
        raise ValueError("membership changed between creation and commitment — the raw set no "
                         "longer hashes to its own candidate_set_id; refusing to commit an "
                         "altered set")
    prior = cset.get("commitment")
    if prior is not None and prior != full:
        raise ValueError("the set already carries a different commitment — refusing to "
                         "overwrite one commitment with another")
    cset["commitment"] = full
    cset["candidates"] = tuple(cset["candidates"])
    return cset


def _assert_committed_and_intact(cset: Dict[str, Any], stage: str) -> None:
    """The doorkeeper for every stage after commit: NO VERIFICATION BEFORE COMMITMENT, and no
    verification of a set whose membership no longer matches what was committed. Recomputed
    fresh at every stage — the stored hash is a claim, and storage is never trusted (the same
    posture attest.witnesses takes toward stored signatures)."""
    commitment = cset.get("commitment")
    if not commitment:
        raise ValueError(f"{stage} refused: the set is not committed — commit() must hash the "
                         f"complete raw set before any evaluation (assessment §5.2)")
    if validate.content_hash(_raw_material(cset)) != commitment:
        raise ValueError(f"{stage} refused: membership no longer matches the commitment — a "
                         f"candidate was added, removed, or edited after commit; the narrowing "
                         f"stops here (assessment §6, selective disclosure)")


def _arithmetic_side(side: str) -> bool:
    """True iff one side of a claim is something the math moat can honestly judge: digits,
    operators, parens, and SINGLE-letter symbols. Any multi-letter token makes the side prose
    and the claim unroutable — held, never judged (see _WORD_RE's constraint note)."""
    s = side.strip()
    if not s or _WORD_RE.search(s):
        return False
    return _SIDE_RE.fullmatch(s) is not None


def _route_one(raw: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """Apply the fixed v0.1 shape rules to ONE candidate's raw text. Returns
    (rule, mode, spec) on a match, None when no registered rule applies. Reads the SHAPE of
    the claim and nothing else — no status, no metadata, no other candidate."""
    text = str(raw)
    m = _INEQ_RE.search(text)
    if m:
        lhs, _, rhs = text.partition(m.group(1))
        if _arithmetic_side(lhs) and _arithmetic_side(rhs):
            found = _VAR_RE.findall(text)
            return ("inequality", "inequality",
                    {"lhs": lhs.strip(), "rhs": rhs.strip(), "op": m.group(1),
                     "variable": found[0] if found else "x"})
        return None
    if "=" in text:
        lhs, _, rhs = text.replace("==", "=", 1).partition("=")
        if "=" in rhs:
            return None   # more than one '=': not a single checkable claim — held, not judged
        if _arithmetic_side(lhs) and _arithmetic_side(rhs):
            return ("equality", "equality",
                    {"expr_a": lhs.strip(), "expr_b": rhs.strip(),
                     "variables": sorted(set(_VAR_RE.findall(text)))})
    return None


def route(cset: Dict[str, Any], policy_version: str = "v0.1") -> Dict[str, Any]:
    """Assign verifiers under the FIXED, PRE-REGISTERED policy — before outcomes exist.

    Refuses an uncommitted set (the invariant: no verification before commitment), an altered
    set, and an unregistered policy version — a policy version chosen after outcomes is
    verification shopping wearing a version string (assessment §6). Records the policy
    version and its registration date on the set, so the receipt names exactly which rules
    governed the narrowing.

    Deliberately blind: this function reads each candidate's raw_text and NOTHING else — not
    the generator's weight, not any status — so the verifier plan cannot bend toward a
    favored candidate. A test greps this function's source to hold that promise.

    v0.1 routes only arithmetic equality/inequality shapes to the sympy moat; everything else
    is assigned the default: quarantine, held and never judged.
    """
    _assert_committed_and_intact(cset, "route")
    policy = ROUTING_POLICY.get(str(policy_version))
    if policy is None:
        raise ValueError(f"routing must be pre-registered: unknown policy version "
                         f"{policy_version!r} (registered: {sorted(ROUTING_POLICY)})")
    # The policy's modes must exist in the moat NOW — sourced at call time, never copied, so
    # the policy and the verifier fleet cannot drift apart silently.
    from .derivation import _MATH_MODES
    for rule, mode, _shape in policy["rules"]:
        if mode not in _MATH_MODES:
            raise ValueError(f"routing rule {rule!r} names mode {mode!r} which the moat does "
                             f"not serve ({sorted(_MATH_MODES)}) — the policy is broken, and a "
                             f"broken policy must be loud, not lenient")
    routes: Dict[str, Dict[str, Any]] = {}
    for c in cset["candidates"]:
        hit = _route_one(c["raw_text"])
        if hit is None:
            routes[c["candidate_id"]] = {
                "mode": None, "rule": policy["default"],
                "why": "no registered rule matched this claim's shape — held in quarantine, "
                       "never judged"}
        else:
            rule, mode, spec = hit
            routes[c["candidate_id"]] = {"mode": mode, "rule": rule, "spec": spec}
    cset["routing"] = {"policy_version": str(policy_version),
                       "registered": policy["registered"], "routes": routes}
    return cset["routing"]


# Moat verdict -> bounded per-candidate status (§5.1's verification_status vocabulary).
# INCOMPLETE and SYSTEM_ERROR both land in quarantine, NEVER reject: OUR failure is not THEIR
# falsehood — the same mapping receipts._VERDICT_TO_OVERALL makes when it seals, for the same
# reason (contract §5.6). Only a genuine MISMATCH may reject a candidate.
_VERDICT_TO_STATUS = {"HOLDS": "pass", "BROKEN": "reject",
                      "INCOMPLETE": "quarantine", "SYSTEM_ERROR": "quarantine"}


def narrow(cset: Dict[str, Any], config: Optional[EngineConfig] = None) -> List[Dict[str, Any]]:
    """Run the routed deterministic checks and apply the DECLARED selection rule. Returns the
    ordered narrowing trace (also stored on the set for receipt()).

    For each candidate, in generation order: the route's spec goes to the derivation moat and
    the composite verdict maps onto the bounded status (see _VERDICT_TO_STATUS's constraint
    note — an engine failure quarantines, it never rejects). Every candidate is PRESERVED
    whatever happens to it; the count going in equals the count coming out, always.

    Selection follows SELECTION_RULE, declared at module top before any outcome existed:
    a single 'selected' only when exactly one candidate passes; several survivors all stay
    retained alternatives, because presenting material alternatives beats manufacturing a
    winner (assessment §7.1).

    Deliberately blind, same as route(): raw claim in, route in, verdict out — nothing else
    about a candidate is consulted, and a test greps this function's source to hold that
    promise. `config` is accepted for signature stability with the MCP layer (unused by the
    v0.1 math-only routing; non-math domain verifiers will need its surface when a later
    policy version routes to them).
    """
    _assert_committed_and_intact(cset, "narrow")
    if "routing" not in cset:
        raise ValueError("narrow refused: route() has not assigned verifiers — the stages run "
                         "in the registered order (commit, route, narrow, receipt), never "
                         "combined (assessment §8.2)")
    from . import derivation
    routing = cset["routing"]
    trace: List[Dict[str, Any]] = [{
        "event": "narrow_begin",
        "candidate_set_id": cset["candidate_set_id"],
        "commitment": cset["commitment"],
        "policy_version": routing["policy_version"],
        "selection_rule": SELECTION_RULE,
    }]
    for c in cset["candidates"]:
        r = routing["routes"][c["candidate_id"]]
        if r["mode"] is None:
            c["verification_status"] = "quarantine"
            trace.append({"event": "quarantined", "candidate_id": c["candidate_id"],
                          "why": r["why"]})
            continue
        res = derivation.verify({"mode": r["mode"], "params": r["spec"]})
        verdict = str(res.get("verdict") or "SYSTEM_ERROR")
        status = _VERDICT_TO_STATUS.get(verdict, "quarantine")
        detail = ""
        for e in (res.get("trail") or []):
            if e.get("detail"):
                detail = str(e["detail"])[:300]
                break
        c["verification_status"] = status
        c["evidence"] = {"checked_by": "concordance.derivation.verify", "mode": r["mode"],
                         "verdict": verdict, "detail": detail}
        trace.append({"event": "checked", "candidate_id": c["candidate_id"],
                      "mode": r["mode"], "verdict": verdict,
                      "verification_status": status, "detail": detail})
    passing = [c["candidate_id"] for c in cset["candidates"]
               if c["verification_status"] == "pass"]
    single = len(passing) == 1
    for c in cset["candidates"]:
        if c["verification_status"] == "reject":
            c["selection_status"] = "rejected"
        elif c["verification_status"] == "pass" and single:
            c["selection_status"] = "selected"
        else:
            c["selection_status"] = "retained-alternative"
    trace.append({"event": "selection", "rule": SELECTION_RULE, "passing": passing,
                  "selected": passing if single else [],
                  "note": ("exactly one candidate survived deterministic checking — selected"
                           if single else
                           "no single survivor — nothing is selected; every passing candidate "
                           "is retained as a material alternative")})
    trace.append({"event": "narrow_end", "retained": len(cset["candidates"]),
                  "means": "every candidate is preserved — the rejected and the quarantined "
                           "ride beside the selected, always"})
    cset["trace"] = trace
    return trace


def receipt(cset: Dict[str, Any], config: Optional[EngineConfig] = None) -> Dict[str, Any]:
    """Seal the FULL set — never the winner alone (assessment top decision: "do not seal only
    the winning answer").

    Builds the candidate-set record — every candidate with its statuses and its untrusted
    metadata verbatim, the commitment, the routing policy version, the declared selection
    rule, and the whole ordered trace — and content-addresses it with THE one canonical form
    (cas.content_hash_of → validate.content_hash: sorted keys, (",",":") separators,
    ensure_ascii=False, UTF-8; the same bytes tools/verify_seal.py rechecks with no Narrow
    Highway code). Then best-effort stores it through the existing CAS seal path, so the
    receipt is re-fetchable at /s/<hash> and lands in the keeping as a card like every other
    seal (cas._mint_receipt_card).

    Honest by construction, the receipts.mint doctrine: `sealed` is True only if the object
    actually landed and the store's address agrees with ours. On a storage failure the record
    and its content_hash still return — engine-sealable by any caller that holds them — with
    the failure NAMED, never hidden. And the seal proves PROCESS integrity, never truth:
    presenting it otherwise is the receipt laundering the threat model warns of (§6).
    """
    _assert_committed_and_intact(cset, "receipt")
    if "trace" not in cset:
        raise ValueError("receipt refused: narrow() has not run — a receipt seals the "
                         "narrowing path, and there is no path yet")
    record: Dict[str, Any] = {
        "kind": "candidate_set",
        "schema_version": cset["schema_version"],
        "candidate_set_id": cset["candidate_set_id"],
        "query_hash": cset["query_hash"],
        "generator": cset["generator"],
        "generation_method": cset["generation_method"],
        "prompt_hash": cset["prompt_hash"],
        "commitment": cset["commitment"],
        "policy_version": cset["routing"]["policy_version"],
        "selection_rule": SELECTION_RULE,
        "candidates": [dict(c) for c in cset["candidates"]],   # ALL of them, statuses and all
        "trace": list(cset["trace"]),
        "means": ("a sealed narrowing path: what was proposed, how it was routed under a "
                  "pre-registered policy, what survived deterministic checking, and what was "
                  "preserved anyway. The seal proves process integrity, never truth."),
    }
    content_hash = cas.content_hash_of(record)
    out: Dict[str, Any] = {"content_hash": content_hash, "record": record}
    try:
        stored = cas.store(record)
        if stored != content_hash:
            # If the store and this module ever disagree about an address, one of them has
            # broken canonical form — and the disagreement itself is the alarm
            # (tools/verify_seal.py's own doctrine). Surfaced as an unsealed receipt, named.
            raise RuntimeError(f"canonical form disagreement: computed {content_hash[:16]}… "
                               f"but the store addressed {stored[:16]}…")
        out["sealed"] = True
        from . import receipts as _receipts
        out["cite_url"] = f"{_receipts._public_base(config or EngineConfig())}/s/{content_hash}"
    except Exception as exc:  # noqa: BLE001 — never lose the record because sealing failed
        out["sealed"] = False
        out["seal_error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
    return out


__all__ = [
    "SCHEMA_VERSION",
    "GENERATION_METHODS",
    "SAFETY_STATUSES",
    "VERIFICATION_STATUSES",
    "SELECTION_STATUSES",
    "SELECTION_RULE",
    "ROUTING_POLICY",
    "create_set",
    "commit",
    "route",
    "narrow",
    "receipt",
]
