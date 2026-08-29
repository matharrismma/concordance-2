"""THE CONSOLE — the deterministic router of an audio-native coach & scribe.

You speak (or type, or drop a file); the console hears, decides WHAT KIND of thing it is, does it, and
hands back a SMALL payload the edge can speak immediately and a LoRa link could carry:

    { intent, kind, headline, spoken, caption, source, connections, record }

  spoken   — the few words to say aloud NOW (a host's line; short by design)
  caption  — the full text, for the deaf and for the transcript (ADA: nothing is audio-only)
  source   — a WAYBILL to the full document (delivered later — the tortoise), never the blob
  record   — for dictation, the verbatim note that was kept

Crisis-first, always: the one hardened matcher (ask.is_crisis) runs before any routing — a cry is met
with real help spoken plainly (988, a real person) before dictation, before a schedule, before anything.

Conduit, not source: the console SPEAKS found and verified words and keeps yours verbatim; it never
generates the facts it answers with. Deterministic — no LLM in the router. See docs/CONSOLE.md.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import ask as _ask
from . import bookofdays as _book
from . import corpus as _corpus

# ── intent cues (deterministic; leading-anchored where a bare word would over-match) ─────────────
# Dictation: "keep these words, verbatim." Anchored to the start so "make a note of the meeting" is a
# note but "the note he played" (mid-sentence) is not swept.
_DICTATE = (
    "note that", "note to self", "note down", "take a note", "make a note", "jot down", "jot this",
    "write down", "write this down", "write that down", "for the record", "dictate", "dictation",
    "remember that", "record that", "log that", "note this",
)
# Schedule: a calendar act. "remind me" lives here (a reminder is a scheduled thing), distinct from
# "remember that" (a kept note above).
_SCHEDULE = (
    "schedule", "put on my calendar", "add to my calendar", "on my calendar", "remind me",
    "set a reminder", "make an appointment", "book an appointment", "book a", "add an event",
)
# Copies / distribution.
_COPIES = ("make copies", "make a copy", "copy this", "duplicate this", "send copies", "distribute this")


def _strip_prefix(text: str, cues) -> str:
    """Remove a leading dictation/command cue so the KEPT words are the content, not the command.
    'note that the well is dry' -> 'the well is dry'. Only strips at the very start."""
    t = text.strip()
    low = t.lower()
    for c in sorted(cues, key=len, reverse=True):
        if low.startswith(c):
            rest = t[len(c):]
            rest = re.sub(r"^[\s:,\-]+", "", rest)                # drop the joiner after the cue
            rest = re.sub(r"^(that|to|the following|this)\b[\s:,\-]*", "", rest, flags=re.I)
            return rest.strip() or t
    return t


def classify_intent(text: str) -> str:
    """crisis | dictate | schedule | copies | ask. Crisis outranks everything (Mt 25)."""
    t = (text or "").strip().lower()
    if _ask.is_crisis(text):
        return "crisis"
    if any(t.startswith(c) for c in _DICTATE):
        return "dictate"
    if re.search(r"\bmake\s+\d+\s+cop(y|ies)\b", t) or "copies of" in t or any(c in t for c in _COPIES):
        return "copies"
    if any(t.startswith(c) or c in t for c in _SCHEDULE):
        return "schedule"
    return "ask"


def _trim(s: str, n: int = 320) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


# Meet them in THEIR frame (Matt: "use their frame to focus what we say — their vocabulary"). The
# person's own words carry their frame; we use it to SELECT which found threads resonate and to phrase
# in their terms — NEVER to bend the truth. Frame shapes delivery and selection; the room is unchanged.
_STOP = frozenset((
    "the a an of to and but in on for is are was were be his her my your their our its he she it they we "
    "you i do does did how what when where why who which that this these those can could would should "
    "will with from about into over under out up down want need get got make made new old very just some "
    "any not no know tell show find give me us them him there here have has had a").split())


def _frame(text: str) -> List[str]:
    """The person's own vocabulary, in their order — the frame we meet them in. Their words, not ours."""
    out: List[str] = []
    for w in re.findall(r"[a-zA-Z]{3,}", (text or "").lower()):
        if w not in _STOP and w not in out:
            out.append(w)
    return out


# Title hygiene for the "what's next" threads. The keeping is a large, partly-OCR'd public-domain
# corpus, so a few card titles are rough (mojibake, mid-sentence fragments, OCR garble). We do NOT
# repair the stored titles — that would risk damaging the many LEGITIMATE unusual ones (acronyms like
# FRS/CVSS, accents like Schrödinger, Hebrew prefixes like "Ben-", long descriptive shelf titles).
# Instead we (a) hard-drop only the UNAMBIGUOUSLY broken from being offered, and (b) softly prefer
# cleaner titles so a rough one only surfaces when nothing cleaner is as relevant. Selection, not repair.
_FRAG_WORDS = {"for", "the", "a", "an", "and", "of", "in", "with", "to", "by", "as", "that",
               "this", "from", "but", "or", "if", "when", "while", "because"}


def _tidy_title(t: str) -> str:
    """Cosmetic only: collapse OCR double-spacing and trim. Never changes the words."""
    return re.sub(r"\s+", " ", t).strip()


def _title_offerable(t: str) -> bool:
    """Reject only the unambiguously broken: mojibake, or a long prose FRAGMENT — one that starts with
    a function word, runs several words, and lacks the 'title — subtitle' or 'Prefix: entry' structure
    that real titles use (so Matt's long descriptive titles and 'ISBE: Ben-' style entries are kept)."""
    if "�" in t:
        return False
    w = _tidy_title(t).split()
    if w and w[0].lower() in _FRAG_WORDS and len(w) > 6 and " — " not in t and ": " not in t:
        return False
    return True


def _title_penalty(t: str) -> float:
    """A soft roughness score so cleaner titles surface first — a preference, never a repair."""
    p = 0.0
    if len(t.split()) > 10:
        p += 1.0                                        # a sentence, not a title
    if t.rstrip().endswith((",", ";")):
        p += 0.5
    for tok in re.findall(r"[A-Za-z']{4,}", t):         # a mid-title no-vowel garble word (not an acronym)
        s = re.sub(r"[^A-Za-z]", "", tok)
        if len(s) >= 4 and not re.search(r"[aeiou]", s.lower()) and not s.isupper():
            p += 0.5
            break
    return p


def _threads_from_results(results: Any, frame: List[str]) -> List[Dict[str, str]]:
    """The 'what's next' threads are the OTHER cards the keeping surfaced for THEIR query — relevant by
    construction (they matched their own words) and already in their frame. Rank them by how much each
    title shares the person's vocabulary (frame first), then prefer the cleaner title for ties. Found,
    never invented; corpus.connections gives only alphabetical shelf-mates, which are not real threads."""
    fset = set(frame)
    scored = []
    for h in (results[1:] if isinstance(results, list) else []):
        if isinstance(h, dict):
            cid = (h.get("id") or "").strip()
            title = (h.get("title") or "").strip()
            if cid and title and _title_offerable(title):
                ov = len(set(re.findall(r"[a-z]{3,}", title.lower())) & fset)
                scored.append((ov, -_title_penalty(title), cid, _tidy_title(title)))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)   # frame overlap first, then cleaner title
    return [{"id": c, "title": t} for _, _, c, t in scored]


def _coach(text: str, config: Any, gate_open: bool) -> Dict[str, Any]:
    """The coach faculty: a verified answer, spoken short, a connection woven in, the source deferred."""
    r = _ask.respond(text, config, gate_open=gate_open)
    kind = r.get("kind", "search")

    # crisis is handled upstream, but respond() is the one source of truth — honor it if it fires here.
    if kind == "crisis":
        return _spoken_crisis(r)

    # a spoken message the router already has (comfort/ultimate/define/date/compute) — say it, plainly.
    msg = (r.get("message") or "").strip()
    scripture = r.get("scripture") or r.get("romans_road")
    results = r.get("results") or []
    frame = _frame(text)                                # their vocabulary — the frame we meet them in
    connections: List[Dict[str, str]] = []
    nexts: List[Dict[str, Any]] = []
    source: Optional[Dict[str, str]] = None
    headline = ""

    if results:
        top = results[0]
        title = (top.get("title") or "").strip()
        snippet = _trim(top.get("snippet") or top.get("surface") or "", 260)
        headline = title
        spoken = f"On {_trim(text.strip().rstrip('?'), 80)}, the keeping holds this. {snippet}"
        source = {"title": title, "ref": f"/card/{top.get('id','')}"}
        # frame-focus: the other cards the keeping found for their query, most in-their-frame first
        threads = _threads_from_results(results, frame)
        if threads:
            connections = threads[:1]
            spoken += f" A thread worth following: {threads[0]['title']}."
            nexts = [{"label": t["title"], "ref": f"/card/{t['id']}"} for t in threads[:2]]
        caption = f"{title}\n\n{top.get('snippet') or ''}"
    elif scripture:
        v = scripture[0] if isinstance(scripture, list) and scripture else {}
        ref = (v.get("ref") or "").strip()
        body = _trim(v.get("web") or v.get("text") or msg)
        headline = ref
        spoken = f"{body}" + (f" — {ref}." if ref else "")
        source = {"title": ref, "ref": f"/read.html?ref={ref}"} if ref else None
        caption = f"{ref}\n\n{v.get('web') or body}"
    elif msg:
        spoken = _trim(msg, 480)
        caption = msg
    else:
        # an honest miss: say so, and let the want-loop carry it (the tortoise brings it later)
        spoken = ("That is not in the keeping yet. I have written down the want, and the answer will "
                  "follow when it is found.")
        caption = spoken
        kind = "miss"

    # ALWAYS offer the next step — and ALWAYS a way to a new path. Paced (at most two threads, never a
    # wall) and never forced: the final choice is theirs (the Gate — we present, we do not cross).
    nexts.append({"label": "Or ask about anything else — your choice", "ref": None})
    if len(nexts) > 1:
        opts = "; ".join(n["label"] for n in nexts[:-1])
        spoken += f" Where next — {opts}; or somewhere else entirely? Your choice."

    return {
        "intent": "ask", "kind": kind, "headline": headline, "spoken": spoken, "caption": caption,
        "source": source, "connections": connections, "next": nexts, "frame": frame[:8],
        "resources": r.get("resources"), "note": r.get("note"), "generated": False,
    }


def _spoken_crisis(r: Dict[str, Any]) -> Dict[str, Any]:
    msg = (r.get("message") or
           "You matter, and you don't have to carry this alone. Please reach a real person right now.")
    res = r.get("resources") or []
    aloud = msg + " " + " ".join(x.get("label", "") for x in res if x.get("label"))
    return {
        "intent": "crisis", "kind": "crisis", "headline": "You are not alone.",
        "spoken": aloud.strip(), "caption": aloud.strip(), "source": None,
        "connections": [], "resources": res, "note": r.get("note"), "generated": False,
    }


def _dictate(text: str, owner: Optional[str]) -> Dict[str, Any]:
    """The scribe: keep the words VERBATIM. To your book of days when a covenant key is proven; else the
    console hands the record back for the edge to keep (store-nothing on the server, no account)."""
    note = _strip_prefix(text, _DICTATE)
    record: Dict[str, Any] = {"text": note, "kept": "edge"}
    if owner:
        w = _book.write(owner, note)
        if w.get("ok"):
            record = {"text": note, "kept": "book_of_days", "entry_id": w["entry"]["id"],
                      "at": w["entry"]["at"]}
    spoken = "Written down: " + _trim(note, 160)
    return {"intent": "dictate", "kind": "note", "headline": "Kept.", "spoken": spoken,
            "caption": note, "record": record, "source": None, "connections": [], "generated": False}


def _schedule(text: str) -> Dict[str, Any]:
    """Parse the calendar intent and hand it back for confirmation. The actual write is the consent-
    gated /connect/event pilot — the console never writes a calendar without an explicit grant."""
    spoken = ("I can put that on the calendar you named. Confirm the event and I will write it — "
              "nothing is scheduled without your say.")
    return {"intent": "schedule", "kind": "schedule", "headline": "Ready to schedule.",
            "spoken": spoken, "caption": text.strip(), "proposed": {"summary": _trim(text, 120)},
            "source": None, "connections": [], "generated": False}


def _copies(text: str) -> Dict[str, Any]:
    m = re.search(r"\b(\d+)\b", text)
    n = max(1, min(int(m.group(1)), 50)) if m else 1
    spoken = f"Ready to make {n} cop{'y' if n == 1 else 'ies'}. Tell me what to copy and where it goes."
    return {"intent": "copies", "kind": "copies", "headline": "Copies.", "spoken": spoken,
            "caption": text.strip(), "count": n, "source": None, "connections": [], "generated": False}


def dispatch(text: str, config: Any, *, owner: Optional[str] = None,
             gate_open: bool = False) -> Dict[str, Any]:
    """The one entry. Crisis-first, then route. Returns the small, speakable, LoRa-ready payload."""
    text = (text or "").strip()
    if not text:
        return {"intent": "empty", "kind": "empty", "spoken": "", "caption": "",
                "source": None, "connections": [], "generated": False}
    intent = classify_intent(text)
    if intent == "crisis":
        return _spoken_crisis(_ask.respond(text, config))
    if intent == "dictate":
        return _dictate(text, owner)
    if intent == "schedule":
        return _schedule(text)
    if intent == "copies":
        return _copies(text)
    return _coach(text, config, gate_open)


# ── INTAKE — accept anything; keep the LOCATION and the usable form, never the blob ──────────────
def intake_artifact(*, source_location: str, kind: str = "file", title: str = "",
                    extracted_text: str = "", sha256: str = "",
                    at: Optional[str] = None) -> Dict[str, Any]:
    """Form a light, LOCATED artifact card from anything dropped in. The heavy source stays where it is
    (the location); we keep only what is usable and searchable. 'We don't need the image, we need the
    image location.' Extraction (OCR / PDF text) happens at the caller/edge; this shapes the card."""
    loc = (source_location or "").strip()
    if not loc:
        return {"ok": False, "error": "a source location is required (we keep the location, not the blob)"}
    title = (title or "").strip() or (loc.rsplit("/", 1)[-1] or loc)[:120]
    card = {
        "kind": "artifact",
        "artifact_kind": kind,                          # image | pdf | screenshot | text | link | …
        "title": title,
        "extracted_text": _trim(extracted_text, 4000),  # the usable form (may be empty until OCR'd)
        "source_location": loc,                          # the waybill — where the source actually lives
        "sha256": (sha256 or "").strip(),
        "at": at,
    }
    return {"ok": True, "artifact": card}
