"""clarify.py — THE FORM GATE. Question until the blanks are filled, and only then run.

Matt, 2026-08-29: "Right now engines just run and it is a waste of time. We should basically be
filling out a form on each request. Question until each blank is filled." — and: "Everything routes
through each gate."

The inversion of an LLM. "He that answereth a matter before he heareth it, it is folly and shame
unto him" (Proverbs 18:13). An engine that answers before it has heard produces plausible, ungrounded
noise. This gate refuses to run until the matter is heard: every request is a FORM, we ask ONE
question per unfilled blank — Socratically, in the person's own frame — and the deterministic engine
runs only when the load-bearing blanks are full. Then, and only then, can it actually verify anything.

The reduction (Matt): "we are just creating forms/templates … we build a new schema for each unique,
but the variance will be minimal at a certain point." The variance collapses because forms share
SLOTS — a `when`, a `where`, a `subject`, a `claim`, a `domain` recur across every form like a
standard footprint recurs across every board. So there are two small libraries: SLOTS (the parts) and
FORMS (their arrangements). Once the slot library spans, a new form is just routing existing parts.

A form is DATA, never an answer template. The template governs the QUESTIONS and the SHAPE; the
answer always comes up out of the keeping through the bound VERIFIER. Template the blanks, never the
truth (that is the line between us and a mad-libs generator).

PURE by design, exactly like kernel.gate: no corpus, no I/O, no clock, no randomness. It decides from
the request text and the declared form. The CALLER supplies the real parsers (some already exist —
console._parse_event), the coach's prefill (the relationship is the autofill: a stranger fills the
whole form, someone we know answers one blank), and the lexicon `resolver` that says whether a value
is even understood — because "we don't understand it" is itself a blank, and the honest move is to
ask, not to guess. I/O lives with the caller; the doctrine lives here.

Where this sits in the one pipeline every request traverses (Matt: "everything routes through each
gate"): CRISIS/FLOOR first — a cry shortcuts everything, it never fills a form — then THIS gate
(is the form complete?), then the VERIFIER runs (PATH), then kernel.gate preserves the trail on any
state-change. Nothing skips a gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

# A slot parser pulls a value out of the request, or None if the request does not carry it.
Parser = Callable[[str], Optional[str]]
# A resolver answers, for the caller who holds the keeping: is this value understood/valid? The pure
# gate cannot know (no corpus here) — so when a resolver is given and says no, that blank is unfilled.
Resolver = Callable[[str, str], bool]


@dataclass(frozen=True)
class Slot:
    """One blank. `parse` pulls its value from the request; `question` is what we ask, in-frame, when
    the blank cannot be filled. `known_values`, when set, is a closed set — a parsed value outside it
    is treated as AMBIGUOUS and asked about rather than silently accepted (a wrong slot is worse than
    a question). An optional slot that stays empty is simply skipped — we only ask load-bearing blanks."""
    name: str
    question: str
    parse: Parser
    required: bool = True
    known_values: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Form:
    """An arrangement of slots bound to the check it runs when complete. `verifier` names that check —
    and the check is ITSELF a form (Matt: "including verifiers"): the filled slots of a complete
    request-form become the input to a verifier-form, which routes through this same gate. The system
    is homogeneous — forms all the way down, every one routed through the one approval process. For now
    `verifier` is a faculty name (search / check / coach / …); the truer resolution is a form in the
    same registry. `keep` names what is preserved (the elimination trail, the book of days, or nothing).
    The form governs questions and shape; never the answer."""
    name: str
    slots: Tuple[Slot, ...]
    verifier: str
    keep: str


def run(form: Form, text: str, known: Optional[Dict[str, str]] = None,
        resolver: Optional[Resolver] = None) -> Dict[str, object]:
    """Fill the form from what we already know, then from the request; return the FIRST unfilled
    load-bearing blank as a question, or — when every required blank is filled — the complete form
    ready for its verifier. One question at a time (Socratic, not a wall of fields)."""
    known = known or {}
    filled: Dict[str, str] = {}
    for slot in form.slots:
        val = known.get(slot.name)                      # 1) the coach's prefill — the relationship autofills
        val = val.strip() if isinstance(val, str) else val
        if not val:                                     # 2) else parse it out of the request
            got = slot.parse(text)
            val = got.strip() if isinstance(got, str) else got
        if not val:                                     # 3) an empty required blank -> ask; optional -> skip
            if slot.required:
                return _ask(form, slot, filled, "missing")
            continue
        if slot.known_values and val not in slot.known_values:   # 4) outside a closed set -> ambiguous
            return _ask(form, slot, filled, "ambiguous")
        if resolver is not None and not resolver(slot.name, val):  # 5) the keeping can't place it -> ask
            return _ask(form, slot, filled, "unresolved")
        filled[slot.name] = val
    return {"complete": True, "form": form.name, "verifier": form.verifier,
            "keep": form.keep, "filled": filled}


def _ask(form: Form, slot: Slot, filled: Dict[str, str], why: str) -> Dict[str, object]:
    return {"complete": False, "form": form.name, "slot": slot.name, "why": why,
            "ask": slot.question, "filled": filled}


# ── the slot library (parts) ────────────────────────────────────────────────────────────────────
# Small, self-contained parsers for the text slots. The complex time parser (console._parse_event)
# is not duplicated here — the schedule form will inject it when it is folded in. These are the parts
# the three new ask-path forms need, and they add NO new primitive beyond subject / claim / domain.

# Lead-ins we strip to reach the real topic — the command word is not part of what they mean.
_LOOKUP_LEADS = (
    "tell me about", "tell me", "look up", "lookup", "look for", "find me", "find",
    "what is the", "what is", "what's the", "what's", "what are", "who is the", "who is",
    "who was", "where is the", "where is", "show me", "search for", "search",
)
_LEARN_LEADS = (
    "i want to learn about", "i want to learn", "i'd like to learn about", "i'd like to learn",
    "help me understand", "teach me about", "teach me", "explain to me", "explain",
    "i want to understand", "learn about", "learn", "study",
)
_VERIFY_LEADS = (
    "is it true that", "is it true", "isn't it true that", "fact check", "fact-check",
    "verify that", "verify", "prove that", "prove", "check whether", "check that",
    "check if", "confirm that", "confirm", "did", "was", "is", "are", "does",
)

# Domains are inferred, not usually stated — so `domain` is an OPTIONAL, prefilled slot. A closed set
# so a value we can't place is asked about, never silently accepted.
KNOWN_DOMAINS = ("scripture", "doctrine", "history", "science", "language",
                 "health", "law", "math", "geography", "nature")
_DOMAIN_HINTS = {
    "scripture": ("bible", "verse", "scripture", "gospel", "psalm", "testament", "chapter"),
    "doctrine": ("doctrine", "theology", "salvation", "trinity", "sin", "grace", "faith"),
    "history": ("history", "historical", "ancient", "century", "war", "king", "empire", "dated"),
    "science": ("science", "physics", "chemistry", "biology", "atom", "energy", "cell", "gravity"),
    "language": ("hebrew", "greek", "word", "meaning", "translate", "translation", "lexicon"),
    "health": ("health", "disease", "body", "medicine", "herb", "nutrition", "illness"),
    "law": ("law", "legal", "rights", "statute", "court", "constitution"),
    "math": ("math", "equation", "number", "geometry", "algebra", "calculate"),
    "geography": ("where", "country", "city", "map", "river", "mountain", "region"),
    "nature": ("plant", "animal", "tree", "bird", "species", "weather", "soil", "seed"),
}


def _strip_leads(text: str, leads: Tuple[str, ...]) -> str:
    """Remove one leading command/question phrase (longest first) and trailing punctuation, keeping
    the original casing of what remains — that remainder is what they actually mean."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    low = s.lower()
    for lead in sorted(leads, key=len, reverse=True):
        if low.startswith(lead + " "):
            s = s[len(lead) + 1:]
            break
        if low == lead:
            return ""
    return s.strip(" ?.!,:;\"'")


def subject_of(text: str) -> Optional[str]:
    """The topic of a look-up or a learning request — the words after the command word."""
    s = _strip_leads(text, _LOOKUP_LEADS + _LEARN_LEADS)
    s = re.sub(r"^(the|a|an)\s+", "", s, flags=re.I).strip()
    return s or None


def claim_of(text: str) -> Optional[str]:
    """The proposition a verify request wants tested — the statement itself, lead-in removed. A claim
    must have some substance (more than a bare word) to be testable; too thin -> None, so we ask."""
    s = _strip_leads(text, _VERIFY_LEADS)
    return s if len(s.split()) >= 2 else None


def domain_of(text: str) -> Optional[str]:
    """A best-effort classifier prefill — the domain is usually implied, not stated. None -> we simply
    do not ask (it is optional); the verifier can route without it."""
    low = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    for dom, hints in _DOMAIN_HINTS.items():
        if any(f" {h}" in low or h in low for h in hints):
            return dom
    return None


# ── the form library (arrangements) ─────────────────────────────────────────────────────────────
# The three new must-haves Matt greenlit — the decomposed ask path. They add NO new slot primitive;
# each is subject/claim + domain, bound to a verifier we already own. The four built forms
# (scribe / schedule / copies / intake) fit this identical shape and get folded in next, so the gate
# is universal by construction — every request routes through it.

LOOKUP = Form(
    name="look-up", verifier="search", keep="trail",
    slots=(
        Slot("subject", "What would you like me to find?", subject_of, required=True),
        Slot("domain", "Which kind — scripture, history, science…?", domain_of,
             required=False, known_values=KNOWN_DOMAINS),
    ),
)

VERIFY = Form(
    name="verify", verifier="check", keep="trail",
    slots=(
        Slot("claim", "What's the claim you'd like me to test — as a statement?", claim_of, required=True),
        Slot("domain", "Is this scripture, history, science…?", domain_of,
             required=False, known_values=KNOWN_DOMAINS),
    ),
)

LEARN = Form(
    name="learn", verifier="coach", keep="trail",
    slots=(
        Slot("subject", "What would you like to learn?", subject_of, required=True),
        Slot("domain", "Which area — scripture, history, science…?", domain_of,
             required=False, known_values=KNOWN_DOMAINS),
    ),
)

FORMS: Dict[str, Form] = {f.name: f for f in (LOOKUP, VERIFY, LEARN)}


# ── routing the ask path to its form ─────────────────────────────────────────────────────────────
# console.classify_intent already routes crisis/dictate/schedule/copies vs. ask. When it lands on
# "ask", THIS decides which of the three ask-forms — verify (test a claim) vs. learn (walk a subject)
# vs. look-up (retrieve). Kept small and honest; ties fall to look-up, the least presumptuous.
# Verify cues that may appear anywhere in the request.
_VERIFY_CUES = ("is it true", "true that", "fact check", "fact-check", "verify", "prove",
                "really happen", "confirm", "debunk", "a myth")
# Auxiliary openers: a YES/NO question ("Was manna real?") is a verify — but only when the sentence
# STARTS with the auxiliary. "Who/what/when/where was …" is a WH-question, which is a look-up.
_VERIFY_STARTS = ("was ", "were ", "did ", "does ", "is ", "are ", "has ", "have ", "can ")
# Existence questions read like a yes/no but are really retrieval ("is there a verse about rest").
_LOOKUP_STARTS = ("is there", "are there", "is it possible", "do you have", "does the")
_LEARN_CUES = ("teach me", "learn", "understand", "explain", "how does", "how do", "how a",
               "study", "walk me through", "help me grasp")


def route_ask(text: str) -> str:
    """Which ask-form: 'verify' | 'learn' | 'look-up'. Only reached once classify_intent said 'ask'.
    Ties fall to look-up, the least presumptuous — we retrieve rather than presume a claim to test."""
    s = re.sub(r"\s+", " ", (text or "").lower()).strip()
    low = " " + s + " "
    if not s.startswith(_LOOKUP_STARTS):
        if any(c in low for c in _VERIFY_CUES) or s.startswith(_VERIFY_STARTS):
            return "verify"
    if any(c in low for c in _LEARN_CUES):
        return "learn"
    return "look-up"


def clarify_ask(text: str, known: Optional[Dict[str, str]] = None,
                resolver: Optional[Resolver] = None) -> Dict[str, object]:
    """Convenience for the caller: route the ask text to its form and run the gate over it."""
    return run(FORMS[route_ask(text)], text, known=known, resolver=resolver)


# ── the response envelope — the hare gives the keeping, the tortoise goes to the source ───────────
# Matt, 2026-08-29: "The hare gives what is in the keeping. The quick response. The tortoise will go
# to the source. The user can choose if they need the tortoise or if they have access at that moment."
# And: "Don't say 24-48 automatically. Just look it up and get a good source. It may be 30 seconds."
#
# The two are DIFFERENT reaches, not two speeds of one fetch — and they cost differently: the hare is
# FAST AND FREE, the tortoise SLOW AND CHEAP.
#   HARE  — the quick response FROM THE KEEPING (what we already hold, verified + cited). Always
#           instant, always local, and FREE — it works fully off-grid, because the keeping lives on the
#           node and costs the family nothing. Its honest faces: the clarifying QUESTION (form not yet
#           complete — we don't look until we have heard, Prov 18:13), the ANSWER (the keeping holds
#           it), or the MISS (the keeping does not hold it — said plainly, still instant, never faked).
#   TORTOISE — a trip OUT TO THE SOURCE (the full original). Slow and CHEAP (a metered reach, low cost
#           but not free). OFFERED, never auto-run: the user chooses whether they need the source and
#           whether they have access at that moment — online now, or queued to the want-list for when a
#           connection returns. No clock is ever promised.
#
# THE LOOP (Matt: "Tortoise produces for the keeping. Hare tends the keeping."): the hare TENDS —
# serving from the keeping and, in serving, revealing the gaps (a miss is a want). The tortoise
# PRODUCES — a chosen trip out brings the source IN, entering THROUGH THE GATE (born quarantined,
# never silently trusted — the anti-laundering law), so the keeping GROWS and next time the hare
# serves it FREE. Cheap once, free forever; the garden dressed and kept (Gen 2:15). This is the
# keeping trained continuously — experience (the misses the hare finds) drives production.
#
# Production has TWO inflows (Matt: "Or BYOS — bring your own source"): the tortoise reaching OUT to a
# source, AND the user's OWN material brought in — we craft cards on their drive, THEY set where each
# card may reside, and only the ones they mark PUBLIC become candidate cards for the keeping.
# Private/shared cards stay at the residence they chose; both public inflows enter as candidates
# through the same gate. Sovereignty: their material, their permission — the keeping never takes what
# was not offered. (BYOS lives in the intake/candidate/shelf machinery; the tortoise's produce() hook
# below is the SAME production door — a source becomes a candidate, gated.)
#
# The tortoise never contradicts the hare, only completes it. keeping()/fetch()/produce()/open_want()
# are injected — the I/O lives with the caller; this module stays pure, like kernel.gate.

_MISS_LINE = "I don't have that in the keeping yet."
TORTOISE_OFFER = "Want me to go to the source for the full of it?"
_TORTOISE_QUEUED = "No connection right now — I'll fetch a good source the moment there is one."


def envelope(gate: Dict[str, object],
             keeping: Optional[Callable[[Dict[str, object]], Optional[Dict[str, object]]]] = None
             ) -> Dict[str, object]:
    """The HARE from a clarify result — the quick response from the keeping, or the clarifying
    question when the form is not yet complete. Alongside a real answer OR a miss the TORTOISE is
    OFFERED (never fired here): the user chooses it via send_tortoise. Nothing is sourced until we
    have heard, so an incomplete form offers no tortoise."""
    if not gate.get("complete"):
        return {"hare": {"kind": "question", "spoken": gate.get("ask", ""), "cost": "free"},
                "tortoise": None, "form": gate.get("form")}
    k = keeping(gate) if keeping else None
    if k and k.get("found"):
        hare = {"kind": "answer", "spoken": k.get("spoken", ""), "source": k.get("source"), "cost": "free"}
    else:
        hare = {"kind": "miss", "spoken": _MISS_LINE, "source": None, "cost": "free"}
    # the hare is fast and FREE (the local keeping); the tortoise is slow and CHEAP (a metered reach)
    # so an off-grid surface can show the cost before the user chooses to spend it.
    return {"hare": hare, "tortoise": {"offered": True, "spoken": TORTOISE_OFFER, "cost": "cheap"},
            "form": gate.get("form"), "filled": gate.get("filled")}


def send_tortoise(gate: Dict[str, object], *,
                  fetch: Optional[Callable[[Dict[str, object]], Optional[Dict[str, object]]]] = None,
                  produce: Optional[Callable[[Dict[str, object]], object]] = None,
                  open_want: Optional[Callable[[Dict[str, object]], str]] = None,
                  online: bool = True) -> Dict[str, object]:
    """The user CHOSE the tortoise. With access it goes to the source, hands back a good one, and —
    the loop — PRODUCES for the keeping: the fetched source is passed to produce(), which enters it
    through the gate (born quarantined, never silently trusted), so next time the hare serves it FREE.
    With no access, the errand is queued on the want-list for when a connection returns. A good source
    is the goal either way, and no ETA is promised."""
    if online and fetch:
        r = fetch(gate)
        if r and r.get("found"):
            produced = produce(r) if produce else None    # grow the keeping — through the gate, quarantined
            return {"status": "ready", "source": r.get("source"),
                    "spoken": r.get("spoken", ""), "produced": produced}
    want_id = open_want(gate) if open_want else None
    return {"status": "queued", "want_id": want_id, "spoken": _TORTOISE_QUEUED}


__all__ = ["Slot", "Form", "run", "FORMS", "LOOKUP", "VERIFY", "LEARN",
           "route_ask", "clarify_ask", "envelope", "send_tortoise", "TORTOISE_OFFER",
           "subject_of", "claim_of", "domain_of", "KNOWN_DOMAINS", "Parser", "Resolver"]
