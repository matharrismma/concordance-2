"""THE BAND SWITCH — which components an intent engages, and which it must never touch (Matt, 2026-10-08).

"Are all pieces in the correct place and serving the correct purpose? The engine doesn't run until we have a
system that connects all subsystems and engages only the correct components for the intended purpose."

The receiver (receiver.py) proves every stage functions; the subsystem graph (systems.py) proves they connect.
Neither proves that a component is engaged ONLY for its purpose — and two violations of exactly that were found
by accident the same day (a verifier building the corpus inside its verify budget; the coach grading by substring).
So this is the map, intent by intent, in the doors' own names: the entry the code has, the components it engages,
and the components it MUST NOT engage — each a `module.function` that exists, checked by `verify_names()` so the map
cannot drift from the code — and tests/test_engagement.py runs every intent with its forbidden components armed to
raise. The map is data; the proof is the pins; nothing here is typed as true.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, List

INTENTS: List[Dict[str, Any]] = [
    {"intent": "CHECK", "purpose": "verify a claim: the verdict, the worked trail, the seal",
     "entry": "audit.audit",
     "engages": ["audit.extract", "derivation.verify_derivation", "verifiers.base.dispatch", "ask.is_crisis", "receipts.attach"],
     "engages_note": "receipts.attach only when seal=True; the crisis net runs first on every text",
     "must_not": ["corpus.default_corpus", "corpus.Corpus.search", "faces.compose", "coach.check_answer"],
     "must_not_note": "a cold check never builds the keeping (a shelf lookup declines when none is loaded); a verifier never "
                      "ranks; a check is not a face and not a lesson",
     "stages": ["antenna", "preselector", "mixer + local oscillator", "IF filter", "limiter", "discriminator", "AGC", "audio stage", "squelch"]},
    {"intent": "FIND", "purpose": "find it in the keeping: a word, a card, a found fact",
     "entry": "dictionary.define",
     "engages": ["dictionary.define", "lookup.lookup", "corpus.Corpus.search", "corpus.Corpus.full"],
     "engages_note": "the keeping is FIND's own instrument",
     "must_not": ["derivation.verify_derivation", "receipts.attach", "ledger.seal_to_ledger", "coach.check_answer"],
     "must_not_note": "a find never judges, never seals, never grades",
     "stages": ["antenna", "mixer + local oscillator", "audio stage", "power supply (cathode)"]},
    {"intent": "WALK", "purpose": "a situation in, one next step out",
     "entry": "ask.respond",
     "engages": ["ask.respond", "ask.is_crisis", "corpus.Corpus.search", "derivation.verify_derivation"],
     "engages_note": "crisis first, always; a checkable claim inside the situation may be verified",
     "must_not": ["receipts.attach", "ledger.seal_to_ledger", "coach.check_answer"],
     "must_not_note": "ask never seals and never grades",
     "stages": ["antenna", "preselector", "mixer + local oscillator", "audio stage", "speaker"]},
    {"intent": "KEEP", "purpose": "seal a verified result so it can be fetched and re-verified",
     "entry": "receipts.attach",
     "engages": ["receipts.attach", "cas.store", "ledger.seal_to_ledger"],
     "engages_note": "the index step is deferrable (index=False on a cold mint)",
     "must_not": ["corpus.default_corpus", "derivation.verify_derivation", "coach.check_answer"],
     "must_not_note": "a cold mint never builds the keeping; a keep seals what was verified, it does not verify again",
     "stages": ["audio stage", "duplexer"]},
    {"intent": "WORD", "purpose": "Scripture at depth: the passage, the cross-references, the original words",
     "entry": "verifiers.scripture.read_passage",
     "engages": ["verifiers.scripture.read_passage"],
     "engages_note": "read, cited, verbatim",
     "must_not": ["derivation.verify_derivation", "receipts.attach", "ledger.seal_to_ledger", "faces.compose"],
     "must_not_note": "a passage is read, never judged, never sealed, never spoken for",
     "stages": ["antenna", "audio stage", "speaker", "power supply (cathode)"]},
    {"intent": "LEARN", "purpose": "the coach: the next authored unit, the authored check",
     "entry": "coach.check_answer",
     "engages": ["coach.next_unit", "coach.check_answer", "coach.recommend"],
     "engages_note": "judged only against the operator's authored check, by the answer law",
     "must_not": ["corpus.Corpus.search", "derivation.verify_derivation", "receipts.attach", "faces.compose"],
     "must_not_note": "the coach never searches to grade, never judges the child by a verifier, never seals a lesson",
     "stages": ["AGC", "audio stage", "speaker"]},
    {"intent": "OPERATE", "purpose": "the systems read: the course, the roll-call, the receiver",
     "entry": "systems.report",
     "engages": ["systems.report", "receiver.status"],
     "engages_note": "pure over files and the import graph",
     "must_not": ["corpus.default_corpus", "derivation.verify_derivation", "receipts.attach"],
     "must_not_note": "the report never loads the keeping, never verifies, never seals",
     "stages": ["speaker"]},
]


def _resolve(dotted: str) -> bool:
    """`module.attr` or `module.Class.method` under concordance — True when it exists."""
    parts = dotted.split(".")
    for i in range(len(parts) - 1, 0, -1):
        try:
            mod = importlib.import_module("concordance." + ".".join(parts[:i]))
        except Exception:  # noqa: BLE001
            continue
        obj: Any = mod
        try:
            for a in parts[i:]:
                obj = getattr(obj, a)
            return True
        except AttributeError:
            return False
    return False


def verify_names() -> Dict[str, Any]:
    """Every name in the map resolves to code that exists — the map cannot drift from the code."""
    missing = []
    for it in INTENTS:
        for name in [it["entry"]] + list(it["engages"]) + list(it["must_not"]):
            if not _resolve(name):
                missing.append(f"{it['intent']}: {name}")
    return {"ok": not missing, "missing": missing, "intents": len(INTENTS)}


def engagement_map() -> Dict[str, Any]:
    names = verify_names()
    return {
        "intents": [{k: v for k, v in it.items()} for it in INTENTS],
        "names": names,
        "proof": "tests/test_engagement.py runs every intent with its forbidden components armed to raise",
        "read": (f"{len(INTENTS)} intents mapped; every name resolves" if names["ok"] else
                 f"{len(INTENTS)} intents mapped; names NOT resolving: {', '.join(names['missing'])}"),
    }
