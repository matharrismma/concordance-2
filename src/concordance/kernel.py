"""THE GATE KERNEL — the five moves and the nine-field record, as one pure runtime decision.

Matt, 2026-07-25, "This must remain in all decisions":
  1. FIND what is relevant (retrieval + discernment — met in kind).
  2. DISTINGUISH what KIND of thing it is (type every artifact).
  3. VERIFY what can actually be verified — DECLINE the rest plainly; a system ERROR is never a
     false verdict (our failure is not their falsehood).
  4. PRESERVE the trail (provenance, receipts, audit — re-checkable).
  5. Never SILENTLY UPGRADE authority (MONOTONIC: saving, repeating, citing, hashing, sealing,
     popularity, agent-confidence NEVER raise authority — only a real, witnessed, evidenced gate
     does; imports and community ENTER quarantined).

The enforcement ARMS already exist and are NOT duplicated here: shelves.curate (steward != author),
candidates (born quarantined; a lone winner only when exactly one passes), moderation (three signed
witnesses), corpus.is_public (an allowlist, not a denylist), ledger (a PASS-only hash chain),
consent.guard (human authorization for on-behalf writes). This module is the DOCTRINE those arms
embody — named once, typed, pure, and testable — so any path, old or new, can route a state-change
through ONE place and get back a verdict plus the auditable nine-field gate record.

Pure by design: no corpus, no I/O, no clock, no randomness. It decides from the artifact and the
declared evidence; the caller does the persistence (and its OWN signature / consent checks, which
this never replaces) and keeps the returned record. Convergent with the ChatGPT red team's "seven
laws" (default-closed, typed entry/exit, no self-certification, no authority laundering, auditable,
safe failure) — convergence is confirmation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# ── move 2: the KINDS every artifact is typed into ──────────────────────────────────────────────
# One classifier, reconciling the scattered vocabulary (authority_tier / layer / generated /
# acquired_by_plane / record_type / generation_method) into six names the whole engine can share.
KINDS = ("claim", "source", "user_note", "generated_draft", "community", "executable")

# ── move 5: the authority LATTICE (low -> high). Nothing but a witnessed, evidenced gate may RAISE.
AUTHORITY = ("quarantined", "cited", "verified")
_RANK = {a: i for i, a in enumerate(AUTHORITY)}

# Operations that must NEVER raise authority — the anti-laundering law made a list. Saving a card,
# repeating it, citing it, hashing it, sealing it, its popularity, an agent's confidence: none of
# these is evidence, so none may move the needle. Only op == "gate" (an evidenced, witnessed
# transition) is permitted to raise.
NON_UPGRADING = frozenset({
    "save", "store", "repeat", "restate", "cite", "hash", "seal", "sign", "popularity",
    "agent_confidence", "import", "generate", "rename", "copy", "mirror", "cache"})

# Kinds that ENTER quarantined no matter what authority they claim to carry (imports and community
# enter quarantined; generation lives in a labeled draft lane; user notes and executables are never
# self-authoritative). They can still be RAISED later — but only by a real witnessed gate.
BORN_QUARANTINED = frozenset({"generated_draft", "community", "user_note", "executable", "import"})

VERDICTS = ("REJECT", "QUARANTINE", "CONFIRMED")

# The doctrine text, for the read surface (agents READ the law: llms.txt, /identity, the MCP server
# instructions) — the covenant enforced here, in one paragraph each.
FIVE_MOVES = (
    "find what is relevant",
    "distinguish what kind of thing it is",
    "verify what can be verified — decline the rest; a system error is never a false verdict",
    "preserve the trail",
    "never silently upgrade authority",
)
AGENT_COVENANT = (
    "retrieve from the keeping first",
    "distinguish citation from proof",
    "quarantine generated material",
    "request human authorization before writes",
    "produce a receipt for consequential actions",
    "carry provenance through every transformation",
    "respect local data and identity boundaries",
    "stop when the evidence is incomplete",
)


# ── the nine-field gate record ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class GateRecord:
    """What every pass / reject / quarantine must ANSWER (Matt, 2026-07-25) — the auditable decision,
    the provenance envelope made concrete. Nine fields, plus the verdict and the authority the gate
    actually earned (never silently upgraded)."""
    entered: str                       # 1. what entered
    kind: str                          # 2. what kind of object it was
    authority_in: str                  # 3. what authority it carried
    passed: Tuple[str, ...]            # 4. which gates it passed
    failed: Tuple[str, ...]            # 5. which it failed
    assumptions: Tuple[str, ...]       # 6. what assumptions were used
    changed: str                       # 7. what changed
    preserved: str                     # 8. what was preserved
    safe_next: Tuple[str, ...]         # 9. what can safely happen next
    verdict: str                       # REJECT | QUARANTINE | CONFIRMED
    authority_out: str                 # the resulting authority — capped by the monotonic law
    warnings: Tuple[str, ...] = ()      # FLOOR 'warn' concerns — named, not a veto (the advisory channel)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entered": self.entered, "kind": self.kind, "authority_in": self.authority_in,
            "passed": list(self.passed), "failed": list(self.failed),
            "assumptions": list(self.assumptions), "changed": self.changed,
            "preserved": self.preserved, "safe_next": list(self.safe_next),
            "verdict": self.verdict, "authority_out": self.authority_out,
            "warnings": list(self.warnings),
        }


# ── move 5 helpers ──────────────────────────────────────────────────────────────────────────────
def _rank(a: str) -> int:
    return _RANK.get(a, 0)


def _cap(a: str) -> str:
    return a if a in _RANK else "quarantined"


def monotonic_ok(op: str, authority_in: str, authority_out: str) -> bool:
    """The monotonic law, protecting the boundary that matters — VERIFIED (proof). Only a real
    evidenced, witnessed gate (op == 'gate') may REACH 'verified'. Every other op — save, repeat,
    CITE, hash, seal, popularity, agent-confidence, import, generate — may set the lower tiers
    (quarantined / cited assert no proof) but can NEVER reach verified. Citing makes a thing cited,
    never proven; that is the whole 'distinguish citation from proof' law, mechanized."""
    if _cap(authority_out) == "verified" and _cap(authority_in) != "verified":
        return op == "gate"
    return True


# ── move 2: the classifier ──────────────────────────────────────────────────────────────────────
def classify(artifact: Optional[Dict[str, Any]], hint: str = "") -> str:
    """TYPE the artifact into one of the six KINDS. A caller may pass an explicit `hint` (already
    known) which wins if valid; otherwise read the fields, reconciling the scattered vocabulary.
    Order matters — generation and executability are checked before provenance, so a generated draft
    that also carries a source is still a draft (never launder generation into a citation)."""
    if hint in KINDS:
        return hint
    a = artifact or {}
    src = a.get("source") if isinstance(a.get("source"), dict) else {}
    if a.get("generated") is True:
        return "generated_draft"
    if a.get("code") or a.get("command") or a.get("executable") or a.get("script"):
        return "executable"
    tier = str(a.get("authority_tier") or src.get("authority_tier") or "").lower()
    if tier == "user" or a.get("acquired_by_plane") == "user" or a.get("visibility") == "private":
        return "user_note"
    if tier == "member" or a.get("ring") == "commons" or a.get("lifecycle_stage") == "public_review":
        return "community"
    if tier in ("primary", "primary_pd", "secondary", "tertiary", "reference") or a.get("url") or src.get("url"):
        return "source"
    return "claim"


def _has_provenance(artifact: Dict[str, Any]) -> bool:
    a = artifact or {}
    src = a.get("source") if isinstance(a.get("source"), dict) else {}
    return bool(a.get("url") or src.get("url") or src.get("label") or a.get("cite_url") or a.get("ref"))


def _evidence_holds(evidence: Any) -> bool:
    """Did a real verification PASS? Accept the engine's and the verifiers' vocabularies. A bare
    truthy value is NOT enough — a verdict must say so."""
    if evidence is None:
        return False
    if isinstance(evidence, str):
        return evidence.upper() in ("HOLDS", "PASS", "CONFIRMED", "OK")
    if isinstance(evidence, dict):
        v = str(evidence.get("verdict") or evidence.get("overall") or evidence.get("status") or "").upper()
        return v in ("HOLDS", "PASS", "CONFIRMED", "OK")
    return False


def _is_error(evidence: Any, error: Any) -> bool:
    """A SYSTEM error (ours) — never a false verdict. INCOMPLETE / SYSTEM_ERROR / ERROR quarantine."""
    if error:
        return True
    if isinstance(evidence, str):
        return evidence.upper() in ("ERROR", "SYSTEM_ERROR", "INCOMPLETE")
    if isinstance(evidence, dict):
        v = str(evidence.get("verdict") or evidence.get("overall") or evidence.get("status") or "").upper()
        return v in ("ERROR", "SYSTEM_ERROR", "INCOMPLETE")
    return False


def _mismatch(evidence: Any) -> bool:
    """A real verification that FAILED — the claim is broken (a true negative, not our error)."""
    if isinstance(evidence, str):
        return evidence.upper() in ("BROKEN", "MISMATCH", "FAIL", "FALSE")
    if isinstance(evidence, dict):
        v = str(evidence.get("verdict") or evidence.get("overall") or evidence.get("status") or "").upper()
        return v in ("BROKEN", "MISMATCH", "FAIL", "FALSE", "REJECT")
    return False


# ── the gate ────────────────────────────────────────────────────────────────────────────────────
def gate(artifact: Optional[Dict[str, Any]] = None, *,
         entered_as: str = "", authority_in: str = "quarantined", kind_hint: str = "",
         evidence: Any = None, witness: Any = None, author: Any = None,
         contradicts: bool = False, retracted: Optional[bool] = None, error: Any = None,
         assumptions: Tuple[str, ...] = (), wait_satisfied: bool = True,
         in_kind_checked: bool = False, content: str = "") -> GateRecord:
    """Route one state-change through the five moves and return the nine-field record.

    Exactly one verdict:
      REJECT     — a hard floor failed: retracted, or a real verification found it BROKEN, or the
                   caller reports it contradicts what is held. (Never on OUR error — see QUARANTINE.)
      QUARANTINE — the default, and the safe landing for everything uncertain: born-quarantined kinds
                   on entry, a verification that could not run (a system error is NOT a rejection),
                   evidence without an independent witness, or the wait unmet. Citable as UNVERIFIED,
                   never counted as verified.
      CONFIRMED  — only when a real verification HELD, an INDEPENDENT witness (witness != author)
                   corroborated it, and the wait is satisfied. This is the sole path that RAISES
                   authority to 'verified'; nothing else may.
    """
    a = artifact or {}
    kind = classify(a, kind_hint)
    entered = entered_as or str(a.get("id") or a.get("title") or a.get("claim") or "artifact")
    authority_in = _cap(authority_in)
    notes = tuple(assumptions) + (() if in_kind_checked else ("in-kind lookup NOT recorded — caller must find first",))
    passed: list = []
    failed: list = []

    # move 3, first arm: a SYSTEM ERROR is never a false verdict. Hold; do not reject.
    if _is_error(evidence, error):
        return GateRecord(
            entered, kind, authority_in, tuple(passed), ("VERIFY(error)",), notes,
            changed="held — a system error is not a verdict (our failure is not their falsehood)",
            preserved="the artifact and the error, untouched",
            safe_next=("retry when the system recovers", "read as UNVERIFIED — never as a 'no'"),
            verdict="QUARANTINE", authority_out="quarantined")

    # MORAL CONTENT — scan the decision's own words for the RED non-negotiables and FLOOR boundaries
    # (constraints.py). Authority discipline is not the only floor: a well-TYPED proposal can still
    # DESCRIBE a wrong (fake testimonials, preying on the vulnerable). Only scanned when `content` is
    # given (the governance path) — never on arbitrary text. A RED hit or a FLOOR 'error' REJECTS; a
    # FLOOR 'warn' rides along as a named concern, not a veto.
    warn_notes: Tuple[str, ...] = ()
    moral = None
    if content:
        from . import constraints as _con
        cs = _con.scan(content)
        warn_notes = tuple("%s %s: %s" % (h["id"], h["name"], h["cite"]) for h in cs["warnings"])
        if cs["red"]:
            moral = ("RED", cs["red"][0])
        elif cs["floor_error"]:
            moral = ("FLOOR", cs["floor_error"][0])

    # RED / FLOOR — the hard floors. A retraction, a contradiction, a proven mismatch, or a moral
    # constraint hit REJECTS.
    is_retracted = a.get("retracted") if retracted is None else retracted
    reject_reason = ("retracted" if is_retracted else
                     "contradicts what is held" if contradicts else
                     "verification found it BROKEN" if _mismatch(evidence) else
                     ("%s %s — %r" % (moral[1]["id"], moral[1]["name"], moral[1]["matched"]) if moral else ""))
    if reject_reason:
        failed.append("RED" if (moral and moral[0] == "RED") or _mismatch(evidence) else "FLOOR")
        return GateRecord(
            entered, kind, authority_in, tuple(passed), tuple(failed), notes + (reject_reason,),
            changed="refused entry — a floor failed",
            preserved="the artifact and the reason, in the append-only trail",
            safe_next=("do NOT cite, serve, or seal", "a corrected version must re-enter and be re-gated"),
            verdict="REJECT", authority_out="quarantined", warnings=warn_notes)
    passed.extend(("RED", "FLOOR"))

    verified = _evidence_holds(evidence)
    independent = bool(witness) and witness != author
    if witness and witness == author:
        notes = notes + ("witness == author — self-confirmation refused",)

    # CONFIRMED — the only door that RAISES to verified. Witnessed, evidenced, waited.
    if verified and independent and wait_satisfied:
        passed.extend(("VERIFY", "WITNESS", "WAIT"))
        out = "verified"
        assert monotonic_ok("gate", authority_in, out)      # the raise is legitimate (op == gate)
        return GateRecord(
            entered, kind, authority_in, tuple(passed), tuple(failed), notes,
            changed=f"authority {authority_in} -> verified (evidenced + witnessed gate)",
            preserved="the evidence, the witness, and the prior authority",
            safe_next=("may be cited AS verified", "may be sealed to the PASS-only ledger"),
            verdict="CONFIRMED", authority_out=out, warnings=warn_notes)

    # QUARANTINE — everything else lands here, safely. Record which arm was missing.
    if verified:
        passed.append("VERIFY")
    if not independent:
        failed.append("WITNESS")
    if not wait_satisfied:
        failed.append("WAIT")

    # The authority a QUARANTINE may hold. VERIFIED is NEVER asserted here — it is re-earned each
    # gate by CONFIRMED (a seal is a property of an evaluation, re-checkable, not a permanent stamp;
    # to hold verified, re-present the evidence). Born-quarantined kinds — imports, community,
    # generated drafts, user notes, executables — are quarantined, never even cited (Matt: "imports/
    # community enter QUARANTINED, never cited/verified"). A curated SOURCE with real provenance is
    # CITED: citable, but a citation is not a proof (move 2). Everything else is quarantined.
    if kind in BORN_QUARANTINED:
        out = "quarantined"
    elif kind == "source" or _has_provenance(a):
        out = "cited"
    else:
        out = "quarantined"
    assert out in ("quarantined", "cited") and monotonic_ok("quarantine", authority_in, out)

    changed = (f"authority held at {out}" if out == authority_in
               else f"authority {authority_in} -> {out} (a citation is not proof; verified needs the gate)")
    return GateRecord(
        entered, kind, authority_in, tuple(passed), tuple(failed), notes,
        changed=changed,
        preserved="the artifact, its provenance, and every gate outcome",
        safe_next=(("may be cited AS UNVERIFIED" if out == "cited" else "may be held, not served"),
                   "reaches 'verified' only via an independent, evidenced gate"),
        verdict="QUARANTINE", authority_out=out, warnings=warn_notes)


def doctrine() -> Dict[str, Any]:
    """The law, for the read surfaces (agents read it at llms.txt / identity / the MCP instructions)."""
    try:
        from . import constraints as _con
        moral = _con.catalog()
    except Exception:  # noqa: BLE001
        moral = {}
    return {
        "five_moves": list(FIVE_MOVES),
        "agent_covenant": list(AGENT_COVENANT),
        "kinds": list(KINDS),
        "authority_lattice": list(AUTHORITY),
        "verdicts": list(VERDICTS),
        "born_quarantined": sorted(BORN_QUARANTINED),
        "never_upgrades": sorted(NON_UPGRADING),
        "moral_constraints": moral,
        "gate_record_fields": ["entered", "kind", "authority_in", "passed", "failed",
                               "assumptions", "changed", "preserved", "safe_next"],
        "note": "This finds, types, verifies-what-can-be, preserves the trail, and refuses to "
                "launder low authority into high. Conduit, not oracle. A system error is never a "
                "false verdict.",
    }
