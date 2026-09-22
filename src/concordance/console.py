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

import datetime as _dt
import os
import re
from typing import Any, Dict, List, Optional

from . import ask as _ask
from . import bookofdays as _book
from . import clarify as _clarify
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
# Learn: start a cube (the coach IS the shepherd — one conversation reaches the lessons too).
_LEARN = ("teach me", "teach us", "teach ", "learn ", "study ", "practice ", "help me learn",
          "i want to learn", "i'd like to learn", "let's learn", "the cube", "the coach")
# Read: read a work aloud, or read Scripture (and, on ask, in the original tongue by the cube).
_READ = ("read me", "read to me", "read us", "read the ", "read a ", "read from ", "read aloud",
         "let's read", "read ")
# Acquire: dictate a want to the STEWARD — an explicit ask to go find what the keeping does not hold.
_ACQUIRE = ("go find", "find me", "acquire ", "get me the", "have the library find", "send the steward",
            "ask the library to find", "go get", "have the steward")

# a language/skill word -> its cube subject (only ones the coach actually teaches are honored later)
_LANG_WORDS = {
    "greek": "grc", "koine": "grc", "hebrew": "he", "latin": "la", "french": "fr", "german": "de",
    "spanish": "es", "español": "es", "espanol": "es", "portuguese": "pt", "mandarin": "zh",
    "chinese": "zh", "japanese": "ja", "english": "en", "phonics": "read", "reading": "read",
    "to read": "read",
}
_REF_RE = re.compile(r"\b((?:[1-3]\s+)?[A-Za-z][A-Za-z.]{1,18}\s+\d{1,3}(?::\d{1,3})?)")
_IN_ORIGINAL = re.compile(r"\bin (?:the )?(original|greek|hebrew|koine|tongue)\b", re.I)


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
    """crisis | dictate | schedule | copies | acquire | learn | read | ask. Crisis outranks
    everything (Mt 25). The coach is the shepherd: one conversation reaches find/verify (ask), the
    lessons (learn), the whole works (read), the record (dictate/schedule/copies) and the steward
    (acquire) — it calls each behind the scenes."""
    t = (text or "").strip().lower()
    if _ask.is_crisis(text):
        return "crisis"
    if any(t.startswith(c) for c in _DICTATE):
        return "dictate"
    # the leading-anchored verbs win over the broad contains-cues below — otherwise "read me a BOOK A-bout
    # carpentry" is swept into schedule by its "book a" cue. A clear opening verb is the strongest signal.
    if any(t.startswith(c) for c in _ACQUIRE):
        return "acquire"
    if any(t.startswith(c) for c in _LEARN) or "the cube" in t or "the coach" in t:
        return "learn"
    if any(t.startswith(c) for c in _READ):
        return "read"
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
    elif r.get("verify"):
        # THE CORE PROMISE on the console door: a checkable claim ("is 17 prime", "12*7 = 84") gets the
        # VERIFIED VERDICT + the worked reasoning — never a false "not in the keeping". Found/computed,
        # not generated (the verify payload carries verdict/detail/trail + a re-checkable seal). Without
        # this branch the payload fell through to the miss below, and the engine's one job read as a gap.
        v = r["verify"]
        verdict = (v.get("verdict") or "").upper()
        detail = _trim(v.get("detail") or "", 420)
        if verdict == "HOLDS":
            headline = "It checks out."
            spoken = ("Verified — it holds. " + detail).strip()
        elif verdict == "BROKEN":
            headline = "That does not hold."
            spoken = ("I checked it, and it does not hold. " + detail).strip()
        elif verdict == "INCOMPLETE":
            headline = "I can only go so far on that."
            spoken = ("I could not fully verify that. " + detail).strip()
        else:  # SYSTEM_ERROR — our failure, never a false verdict on their claim
            headline = "I could not run the check."
            spoken = ("I hit an error checking that — that is my failure, not a false claim. " + detail).strip()
        caption = spoken
        kind = "verify"
        # the re-checkable receipt — attach() stores it as verify["seal"]["cite_url"] (a permanent,
        # content-addressed /s/<hash>). Surface it so the family can VERIFY WITHOUT TRUSTING US — the
        # whole wedge. (This was reading the wrong key, so the seal never reached the console user.)
        seal = v.get("seal") if isinstance(v.get("seal"), dict) else {}
        cu = seal.get("cite_url") or v.get("cite_url") or ""
        if cu:
            source = {"title": "the worked check — re-verify it yourself", "ref": cu}
    else:
        # an honest miss: the keeping does not hold it. We OFFER the tortoise, and OFFER the steward
        # (say "go find it") — but never write a want they did not ask for (bot noise must not fill the
        # queue; the write waits on their clear word — see wants.open_want).
        spoken = ("That is not in the keeping yet. " + _clarify.TORTOISE_OFFER +
                  " Or say \"go find it\" and I'll set the steward to acquire it for the shelf.")
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


# ── deterministic schedule parsing (no LLM): a summary + a time from plain speech ────────────────
_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
             "saturday": 5, "sunday": 6}


def _parse_clock(t: str):
    """(hour, minute) in 24h from a time phrase, or None."""
    if "noon" in t:
        return (12, 0)
    if "midnight" in t:
        return (0, 0)
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)", t)
    if m:
        h = int(m.group(1)) % 12
        return (h + 12 if m.group(3).startswith("p") else h, int(m.group(2) or 0))
    m = re.search(r"\bat (\d{1,2})(?::(\d{2}))?\b", t)
    if m and 0 <= int(m.group(1)) <= 23:
        return (int(m.group(1)), int(m.group(2) or 0))
    return None


def _parse_day(t: str, base):
    if "today" in t or "tonight" in t:
        return base.date()
    if "tomorrow" in t:
        return base.date() + _dt.timedelta(days=1)
    for name, idx in _WEEKDAYS.items():
        if re.search(r"\b" + name + r"\b", t):
            return base.date() + _dt.timedelta(days=((idx - base.weekday()) % 7 or 7))
    return None


def _human_when(w) -> str:
    hh = w.hour % 12 or 12
    ap = "AM" if w.hour < 12 else "PM"
    return w.strftime("%A %b ") + str(w.day) + f", {hh}:{w.minute:02d} {ap}"


def _parse_event(text: str, now) -> Dict[str, Any]:
    """Best-effort {summary, start_iso, when_human}. start_iso is None when there is no clear time — the
    console then ASKS rather than guessing (a wrong time is worse than a question)."""
    t = text.lower()
    when = None
    rel = re.search(r"\bin (\d+)\s*(hour|hr|minute|min|day|week)s?\b", t)
    if rel:
        n = int(rel.group(1))
        when = now + {"hour": _dt.timedelta(hours=n), "hr": _dt.timedelta(hours=n),
                      "minute": _dt.timedelta(minutes=n), "min": _dt.timedelta(minutes=n),
                      "day": _dt.timedelta(days=n), "week": _dt.timedelta(weeks=n)}[rel.group(2)]
    else:
        day, clk = _parse_day(t, now), _parse_clock(t)
        day_explicit = day is not None
        if clk and not day:
            day = now.date()                                  # a time with no day => today
        if day and clk:
            when = _dt.datetime(day.year, day.month, day.day, clk[0], clk[1])
            if not day_explicit and when < now:
                when += _dt.timedelta(days=1)                 # today's time already passed => tomorrow
        elif day and "tonight" in t:
            when = _dt.datetime(day.year, day.month, day.day, 19, 0)
    summ = _strip_prefix(text, _SCHEDULE)
    summ = re.sub(r"\s*(?:\b(?:on|at|by|in|this|next|tonight|today|tomorrow)\b.*|"
                  r"\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b.*)$", "", summ, flags=re.I).strip()
    summ = re.sub(r"^(?:to|that|for|the)\b\s*", "", summ, flags=re.I).strip()
    return {"summary": _trim(summ, 120) or "reminder",
            "start_iso": when.strftime("%Y%m%dT%H%M%S") if when else None,
            "when_human": _human_when(when) if when else None}


def _schedule(text: str) -> Dict[str, Any]:
    """Parse the event, then WRITE it into the calendar the operator named. Two honest paths:

      * The OPERATOR'S OWN node (NH_CALENDAR_WRITE set) — the common case. The operator writing to
        their own calendar is their own act, not a proxy, so it needs no consent grant (consent.guard's
        own words: a member speaking as themselves needs no one's approval). One value turns it on.
      * An on-behalf PROXY (CONSOLE_SCHEDULE_AGENT + _GRANTOR named) — a node scheduling for ANOTHER
        human. That is the one case the consent lock governs: create_event calls consent.guard FIRST
        and refuses without a live signed grant.

    With no calendar named at all, it hands back the parsed proposal (an event the person can add
    themselves — sovereign, no account) and the one-line setup. No clear time -> it asks, never guesses."""
    ev = _parse_event(text, _dt.datetime.now())
    base = {"intent": "schedule", "kind": "schedule", "caption": text.strip(),
            "proposed": ev, "connections": [], "generated": False}
    if not ev["start_iso"]:
        return {**base, "headline": "When?",
                "spoken": f"I can schedule '{ev['summary']}', but I didn't catch a clear time. "
                          f"When should it be — a day and a time?"}
    agent = os.environ.get("CONSOLE_SCHEDULE_AGENT", "").strip()
    grantor = os.environ.get("CONSOLE_SCHEDULE_GRANTOR", "").strip()
    dest = os.environ.get("NH_CALENDAR_WRITE", "").strip()
    if agent and grantor and dest:
        # On-behalf proxy: a node scheduling for another human -> the consent lock applies.
        try:
            from . import connect_write
            r = connect_write.create_event(grantor, agent, ev["summary"], ev["start_iso"])
        except Exception:  # noqa: BLE001 — a calendar hiccup must not crash the console
            r = {"ok": False, "error": "the calendar is unreachable right now"}
        if r.get("ok"):
            return {**base, "kind": "scheduled", "headline": "Scheduled.",
                    "spoken": f"Scheduled: {ev['summary']}, {ev['when_human']}. It's on your calendar.",
                    "receipt": {"uid": r.get("uid"), "target": r.get("target_kind")}}
        return {**base, "headline": "Your say-so first", "needs": "consent",
                "why": r.get("refusal") or r.get("error"),
                "spoken": f"I have it ready — {ev['summary']}, {ev['when_human']} — but I need that "
                          f"person's authorization before I write to their calendar."}
    if dest:
        # The operator's own calendar on their own node — their own act, no grant needed.
        try:
            from . import connect_write
            r = connect_write.create_event_direct(ev["summary"], ev["start_iso"])
        except Exception:  # noqa: BLE001 — a calendar hiccup must not crash the console
            r = {"ok": False, "error": "the calendar is unreachable right now"}
        if r.get("ok"):
            return {**base, "kind": "scheduled", "headline": "Scheduled.",
                    "spoken": f"Scheduled: {ev['summary']}, {ev['when_human']}. It's on your calendar.",
                    "receipt": {"uid": r.get("uid"), "target": r.get("target_kind")}}
        return {**base, "headline": "Couldn't write it", "why": r.get("error"),
                "spoken": f"I have it as: {ev['summary']}, {ev['when_human']}, but I couldn't write to "
                          f"your calendar just now. Take it as an event to add yourself for now."}
    return {**base, "headline": "Ready to schedule",
            "spoken": f"I have it as: {ev['summary']}, {ev['when_human']}. Take it as an event to add, "
                      f"or point the console at your calendar once and I'll keep your days for you."}


def _copies(text: str) -> Dict[str, Any]:
    """Make N copies of a note. 'make 3 copies of the water plan' -> three edge copies to distribute.
    What to copy is the words after 'copies of'; with none, it asks. Store-nothing: the copies are handed
    back for the edge to keep and send, never kept on the server."""
    m = re.search(r"\bmake\s+(\d+)\s+cop", text.lower()) or re.search(r"\b(\d+)\b", text)
    n = max(1, min(int(m.group(1)), 50)) if m else 1
    plural = "y" if n == 1 else "ies"
    what = re.sub(r"^.*?\bcop(?:y|ies)\b\s*(?:of\s+)?", "", text, flags=re.I).strip()
    what = re.sub(r"^(?:this|that|the following)\b[\s:,\-]*", "", what, flags=re.I).strip()
    if not what:
        return {"intent": "copies", "kind": "copies", "headline": "Copy what?", "count": n,
                "spoken": f"Ready to make {n} cop{plural} — say what to copy.",
                "caption": text.strip(), "connections": [], "generated": False}
    return {"intent": "copies", "kind": "copies", "headline": f"{n} cop{plural}.", "count": n,
            "copies": [{"n": i + 1, "text": what} for i in range(n)],
            "spoken": f"Made {n} cop{plural} of: {_trim(what, 90)}. Yours to send.",
            "caption": what, "connections": [], "generated": False}


# ── the coach reaches the lessons, the works, and the steward — behind the scenes ────────────────
def _subject_from_text(text: str) -> Optional[str]:
    """The cube a request names ('teach me Biblical Greek' -> grc), or None. Longest phrase first so
    'to read' beats 'read'."""
    t = " " + (text or "").lower() + " "
    for word in sorted(_LANG_WORDS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(word) + r"\b", t):
            return _LANG_WORDS[word]
    return None


def _learn(text: str) -> Dict[str, Any]:
    """The coach as teacher: start the cube the person named, spoken — or, when no tongue is named,
    offer the tongues it teaches. Found curriculum, never generated (see coach.py)."""
    from . import coach as _coachmod
    present = set(_coachmod._discover())
    subj = _subject_from_text(text)
    if subj and subj in present:
        u = (_coachmod.next_unit(None, subj) or {}).get("unit") or {}    # next_unit nests the unit
        label = _coachmod._LABELS.get(subj, subj)
        title = (u.get("title") or "").strip()
        rule = _trim((u.get("rule") or "").split(". ")[0], 180)
        spoken = (f"Let's learn {label}, by the cube. We begin here — {title}. {rule} "
                  f"Open the cube and we'll walk it together, one step at a time.")
        return {"intent": "learn", "kind": "lesson", "headline": f"{label} — the cube",
                "spoken": spoken, "caption": (u.get("rule") or title),
                "source": {"title": "the cube", "ref": f"/read.html?subject={subj}"},
                "next": [{"label": f"Begin {label}", "ref": f"/read.html?subject={subj}"}],
                "unit": {"id": u.get("id"), "subject": subj, "title": title}, "generated": False}
    subs = [s for s in _coachmod.subjects().get("subjects", []) if s.get("id") in present]
    nexts = [{"label": s["title"], "ref": f"/read.html?subject={s['id']}"} for s in subs[:8]]
    names = ", ".join(s["title"] for s in subs[:8])
    return {"intent": "learn", "kind": "lesson_pick", "headline": "What shall we learn?",
            "spoken": ("I can be your coach in many tongues and skills — " + names +
                       ", and more. Which shall we learn? We learn it by the cube — you speak it; "
                       "I don't do it for you."),
            "caption": names, "source": {"title": "the coach", "ref": "/read.html"},
            "next": nexts, "generated": False}


def _read(text: str, config: Any, gate_open: bool) -> Dict[str, Any]:
    """The coach as reader: read a passage of Scripture — and, when asked, in the ORIGINAL tongue,
    each word to its Strong's (decoding it by the cube) — or find a whole public-domain WORK and open
    the reading room. Found and verbatim; the book is the tortoise, fetched on the person's say."""
    ref_m = _REF_RE.search(text)
    if ref_m:
        from .verifiers import scripture as _sc
        ref = ref_m.group(1).strip()
        ps = _sc.read_passage(ref)
        verses = ps.get("verses") or []
        eng = _trim(" ".join(v.get("text", "") for v in verses), 420) if verses else ""
        shown = (ps.get("ref") or ref)
        if _IN_ORIGINAL.search(text):
            ow = _sc.original_words(ref)
            words = ow.get("words") or []
            tongue = "Greek" if (words and str(words[0].get("strongs", "")).startswith("G")) else "Hebrew"
            orig = " ".join(w.get("word", "") for w in words)
            spoken = ((f"{eng} — {shown}. " if eng else "") +
                      (f"In the {tongue} it was given, {len(words)} words. Open it to read each one to "
                       f"its Strong's — the very tongue, by the cube." if words else
                       "I could not reach the original words just now."))
            return {"intent": "read", "kind": "scripture_original", "headline": f"{shown} — in the {tongue}",
                    "spoken": spoken, "caption": (orig or eng or shown),
                    "source": {"title": f"{shown} — the original", "ref": f"/bible.html?ref={shown}"},
                    "next": [{"label": "Read it in the original", "ref": f"/bible.html?ref={shown}"},
                             {"label": f"Learn {tongue} by the cube",
                              "ref": "/read.html?subject=" + ("grc" if tongue == "Greek" else "he")}],
                    "original": {"tongue": tongue, "count": len(words)}, "generated": False}
        if eng:
            return {"intent": "read", "kind": "scripture", "headline": shown, "spoken": f"{eng} — {shown}.",
                    "caption": eng, "source": {"title": shown, "ref": f"/bible.html?ref={shown}"},
                    "next": [{"label": "Read the chapter", "ref": f"/bible.html?ref={shown}"},
                             {"label": "Hear it in the original", "ref": f"/bible.html?ref={shown}"}],
                    "generated": False}

    # a whole WORK — strip the read cue, find a readable public-domain book, open the reading room
    from . import tortoise as _tortoise
    topic = _strip_prefix(text, _READ)
    topic = re.sub(r"^(?:me|us|to me|aloud|a book (?:about|on)|the book (?:about|on)|about|on|from|the|a)\b[\s:,\-]*",
                   "", topic, flags=re.I).strip() or text
    results = _corpus.search(topic, limit=10) or []
    work = next((c for c in results if isinstance(c, dict) and _tortoise.readable(c)), None)
    if work:
        title = (work.get("title") or "").strip()
        lang = (work.get("language") or (work.get("extra") or {}).get("language") or "").lower()
        withcube = _LANG_WORDS.get(lang if lang in _LANG_WORDS else "english", "en")
        rurl = f"/reader.html?card={work.get('id')}"
        spoken = (f"I found {title} — a public-domain work, held in the ark. Open it and I'll read it "
                  f"with you, sentence by sentence, by the cube.")
        return {"intent": "read", "kind": "work", "headline": title, "spoken": spoken,
                "caption": _trim(work.get("body") or title, 300),
                "source": {"title": title, "ref": rurl},
                "next": [{"label": "Open the reading room", "ref": rurl},
                         {"label": "Read it with the coach", "ref": rurl + "&subject=" + withcube}],
                "work": {"id": work.get("id"), "readable": True}, "generated": False}
    # nothing readable held — the coach turns to the steward (offered; the write waits on their say)
    return {"intent": "read", "kind": "miss", "headline": "Not on the shelf yet",
            "spoken": (f"I don't hold a readable work on {_trim(topic, 60)} yet. Say \"go find it\" and "
                       f"I'll set the steward to acquire it for the shelf."),
            "caption": topic, "source": None,
            "next": [{"label": "Ask the steward to find it", "ref": None}], "generated": False}


def _acquire(text: str) -> Dict[str, Any]:
    """The coach dictates to the STEWARD: an EXPLICIT ask to acquire what the keeping does not hold.
    Opening a want is queuing, not executing — the steward's own gated rounds do the fetching. Only on
    the person's clear word (this intent), never on its own; nothing bot-driven writes the queue."""
    from . import wants as _wants
    q = _strip_prefix(text, _ACQUIRE)
    q = re.sub(r"^(?:me|us|the|a|an|some|about|on|for)\b[\s:,\-]*", "", q, flags=re.I).strip() or text
    r = _wants.open_want(query=q, kind="missing", plane="human")
    if r.get("ok"):
        return {"intent": "acquire", "kind": "want", "headline": "Sent to the steward.",
                "spoken": (f"I've asked the library's steward to go find \"{_trim(q, 80)}\". It will "
                           f"forage the public-domain sources and, when it holds something true, keep "
                           f"it on the shelf for you and everyone."),
                "caption": q, "source": None, "want": {"id": r.get("id") or r.get("want_id"), "query": q},
                "next": [], "generated": False}
    return {"intent": "acquire", "kind": "want_refused", "headline": "Couldn't open that request",
            "spoken": "I couldn't send that to the steward — " + _trim(r.get("error") or "", 120),
            "caption": q, "source": None, "next": [], "generated": False}


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
    if intent == "acquire":
        return _acquire(text)
    if intent == "learn":
        return _learn(text)
    if intent == "read":
        return _read(text, config, gate_open)
    return _ask_path(text, config, owner, gate_open)


def _ask_path(text: str, config: Any, owner: Optional[str], gate_open: bool) -> Dict[str, Any]:
    """The ask path, through the FORM GATE (Prov 18:13 — never answer before hearing). Route to the
    ask-form (look-up / verify / learn); if the request carries no topic, the HARE is the clarifying
    question and we look nothing up. Otherwise the keeping answers — that verified answer IS the hare,
    fast and free — and the TORTOISE is OFFERED alongside it: the cheap, chosen trip to the full source,
    which the user takes on their own need and access. Nothing is fetched or written without their say."""
    gate = _clarify.run(_clarify.FORMS[_clarify.route_ask(text)], text)
    if not gate.get("complete"):
        return _hare_question(gate)
    r = _coach(text, config, gate_open)
    r["cost"] = "free"                       # the hare — the keeping's answer — costs the family nothing
    # the tortoise is OFFERED (never auto-fired) alongside a keeping answer or a miss — but NOT a verify
    # verdict, which is a computed result with no external source to go and fetch.
    if r.get("kind") != "verify":
        r["tortoise"] = {"offered": True, "spoken": _clarify.TORTOISE_OFFER, "cost": "cheap",
                         "form": gate.get("form"), "subject": gate.get("filled")}
    return r


def _hare_question(gate: Dict[str, Any]) -> Dict[str, Any]:
    """The hare when the form is not yet complete: ask the one blank, in plain speech, and fetch
    nothing. A question is a valid instant answer — the one thing an engine that 'just runs' never says."""
    return {
        "intent": "ask", "kind": "clarify", "headline": "One thing first —",
        "spoken": gate.get("ask", ""), "caption": gate.get("ask", ""),
        "source": None, "connections": [], "next": [], "frame": [],
        "form": gate.get("form"), "cost": "free", "generated": False,
    }


# ── INTAKE — accept anything; keep the LOCATION and the usable form, never the blob ──────────────
def intake_artifact(*, source_location: str, kind: str = "file", title: str = "",
                    extracted_text: str = "", sha256: str = "",
                    pdf_bytes: Optional[bytes] = None,
                    at: Optional[str] = None) -> Dict[str, Any]:
    """Form a light, LOCATED artifact card from anything dropped in. The heavy source stays where it is
    (the location); we keep only what is usable and searchable. 'We don't need the image, we need the
    image location.' For a PDF we extract its TEXT here and then DISCARD the bytes — we keep the location
    and the usable text, never the blob. Extraction is best-effort and honest: a scanned/image PDF (or an
    encoding the floor can't read) yields no text, and the card still points to where the source lives."""
    loc = (source_location or "").strip()
    if not loc:
        return {"ok": False, "error": "a source location is required (we keep the location, not the blob)"}
    if pdf_bytes:
        try:
            import hashlib
            from . import pdf_extract
            sha256 = sha256 or hashlib.sha256(pdf_bytes).hexdigest()
            if not (extracted_text or "").strip():
                extracted_text = pdf_extract.text(pdf_bytes)
            kind = "pdf"
        except Exception:  # noqa: BLE001 — intake must never crash on a bad or huge file
            pass
        finally:
            pdf_bytes = None  # the blob is never kept
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
