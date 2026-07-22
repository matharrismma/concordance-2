"""Your days — what you actually did, counted from your own conversations.

A map of time and concentration. Every number here is COUNTED from exchanges you hold; nothing
is inferred, scored, or generated. No model. If it cannot be counted it is not shown.

Two deliberate refusals:

* **Nothing is enumerated.** This module never lists conversations. The caller supplies the
  thread ids it already holds (the browser keeps its own roster); ids it does not hold return
  nothing. There is no "all users" view and no way to ask for one.
* **Crisis is never charted.** Exchanges routed to crisis are excluded from every count, term
  and total. A person's worst hour does not belong on a dashboard, least of all one they might
  show someone. `excluded_private` reports how many were held back, so the omission is visible
  without the content ever being.
"""
from __future__ import annotations

import re
import time
from collections import Counter
from typing import Any, Dict, Iterable, List

from . import threads
from .distill import _STOP, _WORD

# What each kind means in plain words — the chart labels itself honestly rather than showing
# the engine's internal route names to a person.
KINDS = {
    "verify": "checked something",
    "scripture": "read Scripture",
    "word_study": "studied a word",
    "found": "looked something up",
    "search": "looked something up",
    "ultimate": "asked the big questions",
}

# distill's stopword list is tuned for indexing one thread. A chart of what a person keeps
# returning to needs a little more taken out: bare units, and the verbs every question uses.
_CHART_STOP = {
    "read", "mean", "means", "says", "said", "comes", "come", "tell", "show", "explain",
    "check", "look", "find", "want", "need", "know", "think", "make", "made", "give",
    "hour", "hours", "day", "days", "week", "year", "years", "per", "each", "every",
    "time", "times", "thing", "things", "way", "ways", "much", "many", "again", "also",
    "does", "doing", "done", "help", "please", "thanks", "okay", "yes", "very", "really",
}

_MAX_THREADS = 200          # a personal roster, not a corpus scan
_REF = re.compile(r"\b[1-3]?\s?[A-Za-z]{2,}\.?\s+\d{1,3}:\d{1,3}\b")
_STRONGS = re.compile(r"\b([GHgh]\d{1,4})\b")


def _local(ts: float, offset_minutes: int) -> time.struct_time:
    """The person's own clock. A day boundary in UTC is the wrong day for most of the world."""
    return time.gmtime(float(ts) + offset_minutes * 60)


def _clean_ids(thread_ids: Iterable[str]) -> List[str]:
    out, seen = [], set()
    for tid in thread_ids or []:
        t = str(tid or "").strip()
        if t and t not in seen and threads._valid_id(t):
            seen.add(t)
            out.append(t)
        if len(out) >= _MAX_THREADS:
            break
    return out


def chart(thread_ids: Iterable[str], *, tz_offset_minutes: int = 0,
          terms: int = 14) -> Dict[str, Any]:
    """Count time and concentration across the conversations the caller holds."""
    ids = _clean_ids(thread_ids)
    days: Dict[str, Counter] = {}
    hours = [0] * 24
    weekday = [0] * 7
    words: Counter = Counter()
    word_days: Dict[str, set] = {}
    refs: Counter = Counter()
    strongs: Counter = Counter()
    made = Counter()
    counted = excluded = 0
    found_threads = 0
    first = last = None

    for tid in ids:
        rec = threads.get(tid)
        if not rec:
            continue
        found_threads += 1
        for ex in rec.get("exchanges") or []:
            kind = str(ex.get("kind") or "")
            if kind == "crisis":
                excluded += 1
                continue                      # never charted, never termed, never totalled
            ts = ex.get("at") or rec.get("updated_at") or rec.get("created_at")
            if not ts:
                continue
            counted += 1
            lt = _local(ts, tz_offset_minutes)
            date = time.strftime("%Y-%m-%d", lt)
            days.setdefault(date, Counter())[kind or "other"] += 1
            hours[lt.tm_hour] += 1
            weekday[int(time.strftime("%w", lt))] += 1
            first = min(first or ts, ts)
            last = max(last or ts, ts)

            said = str(ex.get("user") or "")
            for w in (m.lower() for m in _WORD.findall(said)):
                if w in _STOP or w in _CHART_STOP or len(w) < 4:
                    continue
                words[w] += 1
                word_days.setdefault(w, set()).add(date)
            for r in _REF.findall(said):
                refs[r.strip()] += 1
            for s in _STRONGS.findall(said):
                strongs[s.upper()] += 1
            resp = ex.get("response") or {}
            # Checking happens two ways now: you asked for it outright (kind "verify"), or you
            # wrote a sentence carrying a claim and the Auditor checked it without being asked.
            # Counting only the first would under-report the work by most of it.
            if kind == "verify":
                made["checked"] += 1
            made["checked"] += int((resp.get("audit") or {}).get("claims_found") or 0)
            if resp.get("seal"):
                made["sealed"] += 1

    day_rows = [{"date": d, "count": sum(c.values()), "kinds": dict(c)}
                for d, c in sorted(days.items())]
    # Concentration is what you came BACK to: ranked by how many separate days it appears on
    # first, then how often. A word said twenty times in one sitting is a topic; a word said
    # on six different days is a concentration.
    conc = sorted(words.items(), key=lambda kv: (-len(word_days.get(kv[0], ())), -kv[1], kv[0]))
    concentration = [{"term": w, "count": n, "days": len(word_days.get(w, ()))}
                     for w, n in conc[:terms] if len(word_days.get(w, ())) >= 1]

    return {
        "ok": True,
        "threads_held": len(ids),
        "threads_found": found_threads,
        "exchanges": counted,
        "excluded_private": excluded,
        "span": {
            "first": time.strftime("%Y-%m-%d", _local(first, tz_offset_minutes)) if first else None,
            "last": time.strftime("%Y-%m-%d", _local(last, tz_offset_minutes)) if last else None,
            "days_active": len(day_rows),
        },
        "days": day_rows,
        "hours": hours,
        "weekday": weekday,
        "kinds": dict(sum(days.values(), Counter()).most_common()),
        "labels": KINDS,
        "concentration": concentration,
        "scripture": [{"ref": r, "count": n} for r, n in refs.most_common(12)],
        "strongs": [{"strongs": s, "count": n} for s, n in strongs.most_common(12)],
        "made": dict(made),
        # The note never names WHY an exchange was withheld. "1 private exchange left out" plus
        # the word "crisis" would let anyone reading over a shoulder infer the reason — the page
        # is meant to be showable. It says what is true without narrowing it to one cause.
        "note": ("Counted from the conversations this browser holds — nothing was inferred and "
                 "no other person's work is visible here. Some exchanges are kept private and "
                 "are left out of every count on purpose."),
    }
