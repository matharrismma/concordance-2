"""Dates — verified answers to "when did X happen / what year did X" for major, unambiguous events.

Matt, 2026-07-27: "We are at 95%. Work to reach 99%." The lone real-life gap was historical dates:
the history corpus holds granular sub-events (e.g. "World War II in Albania, 1942"), not the entity
itself, so answering from them would be a GUESS — and this engine never states a date it cannot
stand behind. So this is a small, HAND-VERIFIED reference of the dates people actually ask for,
drawn from the established historical record. It answers ONLY on a confident match to a known event;
for anything else it returns None and the front door politely points to sources (never a wrong date).

Each entry: (canonical name, [aliases], start_year, end_year|None, note). Years are AD unless the
note says otherwise. Curated + attributed; generated=False in spirit.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

# (canonical, aliases (lowercase, distinctive), start, end|None, note)
_EVENTS: List[Tuple[str, List[str], int, Optional[int], str]] = [
    ("World War II", ["world war ii", "world war 2", "world war two", "wwii", "ww2", "second world war"],
     1939, 1945, "began September 1, 1939; ended September 2, 1945"),
    ("World War I", ["world war i", "world war 1", "world war one", "wwi", "ww1", "first world war", "the great war"],
     1914, 1918, "the armistice was November 11, 1918"),
    ("the American Civil War", ["american civil war", "us civil war", "the civil war"], 1861, 1865, ""),
    ("the American Revolutionary War", ["american revolution", "revolutionary war", "american revolutionary war", "war of independence"],
     1775, 1783, "independence was declared in 1776"),
    ("the Korean War", ["korean war"], 1950, 1953, ""),
    ("the Vietnam War", ["vietnam war"], 1955, 1975, "Saigon fell in 1975"),
    ("the Cold War", ["cold war"], 1947, 1991, ""),
    ("the French Revolution", ["french revolution"], 1789, 1799, ""),
    ("the Napoleonic Wars", ["napoleonic wars"], 1803, 1815, "ended at Waterloo, 1815"),
    ("the Spanish Civil War", ["spanish civil war"], 1936, 1939, ""),
    ("the Thirty Years' War", ["thirty years war", "thirty years' war"], 1618, 1648, ""),
    ("the Hundred Years' War", ["hundred years war", "hundred years' war"], 1337, 1453, ""),
    ("the Great Depression", ["great depression"], 1929, 1939, "the Wall Street Crash was October 1929"),
    # single-moment events (end = None)
    ("the signing of the U.S. Declaration of Independence", ["declaration of independence", "american independence", "us independence", "declared independence"],
     1776, None, "July 4, 1776"),
    ("the ratification of the U.S. Constitution", ["us constitution", "constitution ratified", "constitution was signed"],
     1788, None, "signed 1787, ratified 1788, in effect 1789"),
    ("the first Moon landing", ["moon landing", "apollo 11", "land on the moon", "landed on the moon", "man on the moon", "walk on the moon"],
     1969, None, "Apollo 11, July 20, 1969"),
    ("Columbus reaching the Americas", ["columbus", "columbus reach america", "columbus discover america", "columbus sail"],
     1492, None, ""),
    ("the fall of the Berlin Wall", ["berlin wall", "fall of the berlin wall"], 1989, None, "November 9, 1989"),
    ("the sinking of the Titanic", ["titanic", "titanic sink", "titanic sank"], 1912, None, "April 15, 1912"),
    ("the Wright brothers' first powered flight", ["wright brothers", "first flight", "first airplane", "first powered flight"],
     1903, None, "December 17, 1903"),
    ("the start of the Protestant Reformation", ["protestant reformation", "the reformation", "95 theses", "ninety-five theses"],
     1517, None, "Luther's 95 Theses, October 1517"),
    ("the fall of the Western Roman Empire", ["fall of rome", "fall of the roman empire", "rome fell", "western roman empire fell"],
     476, None, "the Western Roman Empire, AD 476"),
    ("the September 11 attacks", ["september 11", "9/11", "nine eleven"], 2001, None, "September 11, 2001"),
    ("the invention of the telephone", ["telephone was invented", "invention of the telephone", "invented the telephone"],
     1876, None, "Alexander Graham Bell, 1876"),
    ("Gutenberg's printing press", ["printing press", "gutenberg press", "gutenberg invented"], 1440, None, "c. 1440"),
    ("the discovery of penicillin", ["penicillin"], 1928, None, "Alexander Fleming, 1928"),
    ("the French storming of the Bastille", ["storming of the bastille", "bastille"], 1789, None, "July 14, 1789"),
    ("the Norman Conquest (Battle of Hastings)", ["battle of hastings", "norman conquest"], 1066, None, ""),
    ("the Magna Carta", ["magna carta"], 1215, None, ""),
    ("the Emancipation Proclamation", ["emancipation proclamation"], 1863, None, "January 1, 1863"),
    ("the abolition of slavery in the U.S. (13th Amendment)", ["13th amendment", "thirteenth amendment", "slavery abolished", "abolition of slavery"],
     1865, None, "the Thirteenth Amendment, 1865"),
]

_START_WORDS = ("start", "begin", "began", "begun", "outbreak", "found", "founded", "invent", "declared", "sign")
_END_WORDS = ("end", "ended", "over", "finish", "fall", "fell", "collapse", "conclude", "stop", "abolish")
_WHEN = re.compile(r"\b(when (?:did|was|were|is)|what year (?:did|was|were|is)|in what year|"
                   r"what (?:date|year))\b", re.I)


def _fmt_year(y: int) -> str:
    return f"{y} BC" if y < 0 else str(y)


def answer(text: str) -> Optional[str]:
    """A verified date for a major event, or None (decline) — never a guess for the unknown."""
    t = " ".join((text or "").lower().split())
    if not _WHEN.search(t):
        return None
    # find the best matching event: the longest alias that appears in the query wins (most specific)
    best = None
    best_len = 0
    for canonical, aliases, start, end, note in _EVENTS:
        for a in aliases:
            if a in t and len(a) > best_len:
                best, best_len = (canonical, start, end, note), len(a)
    if not best:
        return None
    canonical, start, end, note = best
    tail = f" ({note})" if note else ""
    if end is None:
        return f"{canonical}: {_fmt_year(start)}.{(' ' + note + '.') if note else ''}"
    wants_end = any(w in t for w in _END_WORDS)
    wants_start = any(w in t for w in _START_WORDS)
    if wants_end and not wants_start:
        return f"{canonical} ended in {_fmt_year(end)} (it lasted {_fmt_year(start)}–{_fmt_year(end)}).{tail}"
    if wants_start and not wants_end:
        return f"{canonical} began in {_fmt_year(start)} (it lasted {_fmt_year(start)}–{_fmt_year(end)}).{tail}"
    return f"{canonical}: {_fmt_year(start)}–{_fmt_year(end)}.{tail}"
