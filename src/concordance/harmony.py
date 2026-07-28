"""Harmony of the Gospels — one event of Christ's life, its witnesses laid side by side.

The classic "back of the study Bible" table: every published harmony (Robertson, Broadus,
Thomas/Gundry, the appendices bound into most study Bibles) agrees on which passages narrate the
SAME event across Matthew, Mark, Luke, and John — that agreement is the harmony. This module holds
that mapping and, for each entry, fetches the WEB text of every gospel that records it straight from
the corpus (found, never generated) — nothing here is a paraphrase or a guess at sequence beyond what
is textually and traditionally uncontested.

Where the four accounts genuinely differ in order (chiefly within Passion Week, and the exact
sequence of the Galilean healings/parables), no single row claims to settle it — the "period" grouping
states the phase of the ministry, not a disputed day-by-day timetable. We live in the nuance: this is
a study aid for reading the same event four ways, not a claim to have resolved every harmonization
question scholarship still holds open.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("Every gospel that records this event, side by side — found in the Word itself, never "
        "generated. Where sequence is genuinely disputed among harmonies, the period names the phase "
        "of the ministry, not a settled day-by-day order.")

_GOSPELS = ("matthew", "mark", "luke", "john")

# (id, period, event, matthew, mark, luke, john) — a "" means that gospel does not record this event.
_HARMONY: List[Dict[str, Any]] = [
    # ── Prologue & genealogies ──────────────────────────────────────────────────────────────
    {"id": "h001", "period": "Prologue", "event": "The Word became flesh",
     "matthew": "", "mark": "", "luke": "", "john": "John 1:1-18"},
    {"id": "h002", "period": "Prologue", "event": "The genealogy of Jesus",
     "matthew": "Matthew 1:1-17", "mark": "", "luke": "Luke 3:23-38", "john": ""},
    # ── Birth and infancy ───────────────────────────────────────────────────────────────────
    {"id": "h003", "period": "Birth and Infancy", "event": "Gabriel foretells John's birth to Zechariah",
     "matthew": "", "mark": "", "luke": "Luke 1:5-25", "john": ""},
    {"id": "h004", "period": "Birth and Infancy", "event": "Gabriel foretells Jesus' birth to Mary",
     "matthew": "", "mark": "", "luke": "Luke 1:26-38", "john": ""},
    {"id": "h005", "period": "Birth and Infancy", "event": "Mary visits Elizabeth; the Magnificat",
     "matthew": "", "mark": "", "luke": "Luke 1:39-56", "john": ""},
    {"id": "h006", "period": "Birth and Infancy", "event": "Birth of John the Baptist",
     "matthew": "", "mark": "", "luke": "Luke 1:57-80", "john": ""},
    {"id": "h007", "period": "Birth and Infancy", "event": "The angel appears to Joseph",
     "matthew": "Matthew 1:18-25", "mark": "", "luke": "", "john": ""},
    {"id": "h008", "period": "Birth and Infancy", "event": "Birth of Jesus at Bethlehem",
     "matthew": "", "mark": "", "luke": "Luke 2:1-7", "john": ""},
    {"id": "h009", "period": "Birth and Infancy", "event": "The shepherds and the angels",
     "matthew": "", "mark": "", "luke": "Luke 2:8-20", "john": ""},
    {"id": "h010", "period": "Birth and Infancy", "event": "Circumcision and presentation in the Temple",
     "matthew": "", "mark": "", "luke": "Luke 2:21-40", "john": ""},
    {"id": "h011", "period": "Birth and Infancy", "event": "The Magi and the star",
     "matthew": "Matthew 2:1-12", "mark": "", "luke": "", "john": ""},
    {"id": "h012", "period": "Birth and Infancy", "event": "Flight into Egypt; the innocents",
     "matthew": "Matthew 2:13-18", "mark": "", "luke": "", "john": ""},
    {"id": "h013", "period": "Birth and Infancy", "event": "Return to Nazareth",
     "matthew": "Matthew 2:19-23", "mark": "", "luke": "Luke 2:39", "john": ""},
    {"id": "h014", "period": "Birth and Infancy", "event": "The boy Jesus in the Temple",
     "matthew": "", "mark": "", "luke": "Luke 2:41-52", "john": ""},
    # ── Preparation for ministry ────────────────────────────────────────────────────────────
    {"id": "h015", "period": "Preparation for Ministry", "event": "John the Baptist's preaching",
     "matthew": "Matthew 3:1-12", "mark": "Mark 1:1-8", "luke": "Luke 3:1-18", "john": "John 1:19-28"},
    {"id": "h016", "period": "Preparation for Ministry", "event": "Baptism of Jesus",
     "matthew": "Matthew 3:13-17", "mark": "Mark 1:9-11", "luke": "Luke 3:21-22", "john": ""},
    {"id": "h017", "period": "Preparation for Ministry", "event": "Temptation in the wilderness",
     "matthew": "Matthew 4:1-11", "mark": "Mark 1:12-13", "luke": "Luke 4:1-13", "john": ""},
    {"id": "h018", "period": "Preparation for Ministry", "event": "First disciples follow Jesus",
     "matthew": "", "mark": "", "luke": "", "john": "John 1:35-51"},
    {"id": "h019", "period": "Preparation for Ministry", "event": "Water turned to wine at Cana",
     "matthew": "", "mark": "", "luke": "", "john": "John 2:1-11"},
    # ── Early Judean ministry ───────────────────────────────────────────────────────────────
    {"id": "h020", "period": "Early Judean Ministry", "event": "First cleansing of the Temple",
     "matthew": "", "mark": "", "luke": "", "john": "John 2:13-25"},
    {"id": "h021", "period": "Early Judean Ministry", "event": "Nicodemus visits by night",
     "matthew": "", "mark": "", "luke": "", "john": "John 3:1-21"},
    {"id": "h022", "period": "Early Judean Ministry", "event": "The woman at the well in Samaria",
     "matthew": "", "mark": "", "luke": "", "john": "John 4:1-42"},
    # ── The great Galilean ministry ─────────────────────────────────────────────────────────
    {"id": "h023", "period": "Galilean Ministry", "event": "Jesus begins preaching in Galilee",
     "matthew": "Matthew 4:12-17", "mark": "Mark 1:14-15", "luke": "Luke 4:14-15", "john": "John 4:43-45"},
    {"id": "h024", "period": "Galilean Ministry", "event": "Rejected at Nazareth",
     "matthew": "", "mark": "Mark 6:1-6", "luke": "Luke 4:16-30", "john": ""},
    {"id": "h025", "period": "Galilean Ministry", "event": "Calling of the first fishermen",
     "matthew": "Matthew 4:18-22", "mark": "Mark 1:16-20", "luke": "Luke 5:1-11", "john": ""},
    {"id": "h026", "period": "Galilean Ministry", "event": "A demon-possessed man healed at Capernaum",
     "matthew": "", "mark": "Mark 1:21-28", "luke": "Luke 4:31-37", "john": ""},
    {"id": "h027", "period": "Galilean Ministry", "event": "Peter's mother-in-law healed",
     "matthew": "Matthew 8:14-15", "mark": "Mark 1:29-31", "luke": "Luke 4:38-39", "john": ""},
    {"id": "h028", "period": "Galilean Ministry", "event": "First preaching tour of Galilee",
     "matthew": "Matthew 4:23-25", "mark": "Mark 1:35-39", "luke": "Luke 4:42-44", "john": ""},
    {"id": "h029", "period": "Galilean Ministry", "event": "A man with leprosy cleansed",
     "matthew": "Matthew 8:1-4", "mark": "Mark 1:40-45", "luke": "Luke 5:12-16", "john": ""},
    {"id": "h030", "period": "Galilean Ministry", "event": "A paralytic let down through the roof",
     "matthew": "Matthew 9:1-8", "mark": "Mark 2:1-12", "luke": "Luke 5:17-26", "john": ""},
    {"id": "h031", "period": "Galilean Ministry", "event": "The call of Matthew (Levi)",
     "matthew": "Matthew 9:9-13", "mark": "Mark 2:13-17", "luke": "Luke 5:27-32", "john": ""},
    {"id": "h032", "period": "Galilean Ministry", "event": "A question about fasting",
     "matthew": "Matthew 9:14-17", "mark": "Mark 2:18-22", "luke": "Luke 5:33-39", "john": ""},
    {"id": "h033", "period": "Galilean Ministry", "event": "Lord of the Sabbath (grain fields; withered hand)",
     "matthew": "Matthew 12:1-14", "mark": "Mark 2:23-3:6", "luke": "Luke 6:1-11", "john": ""},
    {"id": "h034", "period": "Galilean Ministry", "event": "Choosing the Twelve",
     "matthew": "Matthew 10:1-4", "mark": "Mark 3:13-19", "luke": "Luke 6:12-16", "john": ""},
    {"id": "h035", "period": "Galilean Ministry", "event": "The Sermon on the Mount / Plain",
     "matthew": "Matthew 5:1-7:29", "mark": "", "luke": "Luke 6:17-49", "john": ""},
    {"id": "h036", "period": "Galilean Ministry", "event": "A centurion's servant healed",
     "matthew": "Matthew 8:5-13", "mark": "", "luke": "Luke 7:1-10", "john": ""},
    {"id": "h037", "period": "Galilean Ministry", "event": "The widow of Nain's son raised",
     "matthew": "", "mark": "", "luke": "Luke 7:11-17", "john": ""},
    {"id": "h038", "period": "Galilean Ministry", "event": "John the Baptist's question from prison",
     "matthew": "Matthew 11:2-19", "mark": "", "luke": "Luke 7:18-35", "john": ""},
    {"id": "h039", "period": "Galilean Ministry", "event": "A sinful woman anoints Jesus' feet",
     "matthew": "", "mark": "", "luke": "Luke 7:36-50", "john": ""},
    {"id": "h040", "period": "Galilean Ministry", "event": "Parable of the Sower and the parables of the kingdom",
     "matthew": "Matthew 13:1-53", "mark": "Mark 4:1-34", "luke": "Luke 8:4-18", "john": ""},
    {"id": "h041", "period": "Galilean Ministry", "event": "Jesus calms the storm",
     "matthew": "Matthew 8:23-27", "mark": "Mark 4:35-41", "luke": "Luke 8:22-25", "john": ""},
    {"id": "h042", "period": "Galilean Ministry", "event": "The Gerasene demoniac",
     "matthew": "Matthew 8:28-34", "mark": "Mark 5:1-20", "luke": "Luke 8:26-39", "john": ""},
    {"id": "h043", "period": "Galilean Ministry", "event": "Jairus' daughter; the woman healed by touching his robe",
     "matthew": "Matthew 9:18-26", "mark": "Mark 5:21-43", "luke": "Luke 8:40-56", "john": ""},
    {"id": "h044", "period": "Galilean Ministry", "event": "Sending out the Twelve",
     "matthew": "Matthew 10:5-42", "mark": "Mark 6:7-13", "luke": "Luke 9:1-6", "john": ""},
    {"id": "h045", "period": "Galilean Ministry", "event": "Death of John the Baptist",
     "matthew": "Matthew 14:1-12", "mark": "Mark 6:14-29", "luke": "Luke 9:7-9", "john": ""},
    {"id": "h046", "period": "Galilean Ministry", "event": "Feeding of the five thousand",
     "matthew": "Matthew 14:13-21", "mark": "Mark 6:30-44", "luke": "Luke 9:10-17", "john": "John 6:1-15"},
    {"id": "h047", "period": "Galilean Ministry", "event": "Jesus walks on the water",
     "matthew": "Matthew 14:22-33", "mark": "Mark 6:45-52", "luke": "", "john": "John 6:16-21"},
    {"id": "h048", "period": "Galilean Ministry", "event": "The Bread of Life discourse",
     "matthew": "", "mark": "", "luke": "", "john": "John 6:22-59"},
    {"id": "h049", "period": "Galilean Ministry", "event": "What defiles a person (tradition of the elders)",
     "matthew": "Matthew 15:1-20", "mark": "Mark 7:1-23", "luke": "", "john": ""},
    # ── Retirement / withdrawal ministry ────────────────────────────────────────────────────
    {"id": "h050", "period": "Retirement Ministry", "event": "The Syrophoenician woman's faith",
     "matthew": "Matthew 15:21-28", "mark": "Mark 7:24-30", "luke": "", "john": ""},
    {"id": "h051", "period": "Retirement Ministry", "event": "Feeding of the four thousand",
     "matthew": "Matthew 15:29-39", "mark": "Mark 8:1-10", "luke": "", "john": ""},
    {"id": "h052", "period": "Retirement Ministry", "event": "Peter's confession at Caesarea Philippi",
     "matthew": "Matthew 16:13-20", "mark": "Mark 8:27-30", "luke": "Luke 9:18-21", "john": ""},
    {"id": "h053", "period": "Retirement Ministry", "event": "First prediction of the Passion",
     "matthew": "Matthew 16:21-28", "mark": "Mark 8:31-9:1", "luke": "Luke 9:22-27", "john": ""},
    {"id": "h054", "period": "Retirement Ministry", "event": "The Transfiguration",
     "matthew": "Matthew 17:1-13", "mark": "Mark 9:2-13", "luke": "Luke 9:28-36", "john": ""},
    {"id": "h055", "period": "Retirement Ministry", "event": "A boy with an unclean spirit healed",
     "matthew": "Matthew 17:14-21", "mark": "Mark 9:14-29", "luke": "Luke 9:37-43", "john": ""},
    {"id": "h056", "period": "Retirement Ministry", "event": "Second prediction of the Passion",
     "matthew": "Matthew 17:22-23", "mark": "Mark 9:30-32", "luke": "Luke 9:43-45", "john": ""},
    {"id": "h057", "period": "Retirement Ministry", "event": "Who is the greatest in the kingdom",
     "matthew": "Matthew 18:1-14", "mark": "Mark 9:33-50", "luke": "Luke 9:46-50", "john": ""},
    # ── Later Judean and Perean ministry ────────────────────────────────────────────────────
    {"id": "h058", "period": "Later Judean and Perean Ministry", "event": "Teaching at the Feast of Tabernacles",
     "matthew": "", "mark": "", "luke": "", "john": "John 7:1-8:59"},
    {"id": "h059", "period": "Later Judean and Perean Ministry", "event": "A man born blind healed",
     "matthew": "", "mark": "", "luke": "", "john": "John 9:1-41"},
    {"id": "h060", "period": "Later Judean and Perean Ministry", "event": "The Good Shepherd discourse",
     "matthew": "", "mark": "", "luke": "", "john": "John 10:1-21"},
    {"id": "h061", "period": "Later Judean and Perean Ministry", "event": "Sending of the seventy-two",
     "matthew": "", "mark": "", "luke": "Luke 10:1-24", "john": ""},
    {"id": "h062", "period": "Later Judean and Perean Ministry", "event": "The Good Samaritan",
     "matthew": "", "mark": "", "luke": "Luke 10:25-37", "john": ""},
    {"id": "h063", "period": "Later Judean and Perean Ministry", "event": "Mary and Martha of Bethany",
     "matthew": "", "mark": "", "luke": "Luke 10:38-42", "john": ""},
    {"id": "h064", "period": "Later Judean and Perean Ministry", "event": "The Lord's Prayer taught",
     "matthew": "Matthew 6:9-13", "mark": "", "luke": "Luke 11:1-13", "john": ""},
    {"id": "h065", "period": "Later Judean and Perean Ministry", "event": "The raising of Lazarus",
     "matthew": "", "mark": "", "luke": "", "john": "John 11:1-44"},
    {"id": "h066", "period": "Later Judean and Perean Ministry", "event": "The lost sheep, lost coin, and prodigal son",
     "matthew": "", "mark": "", "luke": "Luke 15:1-32", "john": ""},
    {"id": "h067", "period": "Later Judean and Perean Ministry", "event": "The rich man and Lazarus",
     "matthew": "", "mark": "", "luke": "Luke 16:19-31", "john": ""},
    {"id": "h068", "period": "Later Judean and Perean Ministry", "event": "The persistent widow; the Pharisee and the tax collector",
     "matthew": "", "mark": "", "luke": "Luke 18:1-14", "john": ""},
    {"id": "h069", "period": "Later Judean and Perean Ministry", "event": "Jesus blesses the little children",
     "matthew": "Matthew 19:13-15", "mark": "Mark 10:13-16", "luke": "Luke 18:15-17", "john": ""},
    {"id": "h070", "period": "Later Judean and Perean Ministry", "event": "The rich young ruler",
     "matthew": "Matthew 19:16-30", "mark": "Mark 10:17-31", "luke": "Luke 18:18-30", "john": ""},
    {"id": "h071", "period": "Later Judean and Perean Ministry", "event": "Third prediction of the Passion",
     "matthew": "Matthew 20:17-19", "mark": "Mark 10:32-34", "luke": "Luke 18:31-34", "john": ""},
    {"id": "h072", "period": "Later Judean and Perean Ministry", "event": "Blind Bartimaeus (and companion) healed",
     "matthew": "Matthew 20:29-34", "mark": "Mark 10:46-52", "luke": "Luke 18:35-43", "john": ""},
    {"id": "h073", "period": "Later Judean and Perean Ministry", "event": "Zacchaeus the tax collector",
     "matthew": "", "mark": "", "luke": "Luke 19:1-10", "john": ""},
    # ── Passion Week ────────────────────────────────────────────────────────────────────────
    {"id": "h074", "period": "Passion Week", "event": "The anointing at Bethany",
     "matthew": "Matthew 26:6-13", "mark": "Mark 14:3-9", "luke": "", "john": "John 12:1-8"},
    {"id": "h075", "period": "Passion Week", "event": "The triumphal entry into Jerusalem",
     "matthew": "Matthew 21:1-11", "mark": "Mark 11:1-11", "luke": "Luke 19:28-44", "john": "John 12:12-19"},
    {"id": "h076", "period": "Passion Week", "event": "Second cleansing of the Temple; the fig tree cursed",
     "matthew": "Matthew 21:12-22", "mark": "Mark 11:12-19", "luke": "Luke 19:45-48", "john": ""},
    {"id": "h077", "period": "Passion Week", "event": "Jesus' authority questioned; parables of judgment",
     "matthew": "Matthew 21:23-22:14", "mark": "Mark 11:27-12:12", "luke": "Luke 20:1-19", "john": ""},
    {"id": "h078", "period": "Passion Week", "event": "Taxes to Caesar, the resurrection, and the greatest commandment",
     "matthew": "Matthew 22:15-46", "mark": "Mark 12:13-37", "luke": "Luke 20:20-44", "john": ""},
    {"id": "h079", "period": "Passion Week", "event": "Woes to the scribes and Pharisees; the widow's mite",
     "matthew": "Matthew 23:1-39", "mark": "Mark 12:38-44", "luke": "Luke 20:45-21:4", "john": ""},
    {"id": "h080", "period": "Passion Week", "event": "The Olivet Discourse",
     "matthew": "Matthew 24:1-25:46", "mark": "Mark 13:1-37", "luke": "Luke 21:5-36", "john": ""},
    {"id": "h081", "period": "Passion Week", "event": "The plot against Jesus; Judas' betrayal arranged",
     "matthew": "Matthew 26:1-5,14-16", "mark": "Mark 14:1-2,10-11", "luke": "Luke 22:1-6", "john": ""},
    {"id": "h082", "period": "Passion Week", "event": "The Last Supper",
     "matthew": "Matthew 26:17-30", "mark": "Mark 14:12-26", "luke": "Luke 22:7-38", "john": "John 13:1-30"},
    {"id": "h083", "period": "Passion Week", "event": "The Upper Room Discourse and the High-Priestly Prayer",
     "matthew": "", "mark": "", "luke": "", "john": "John 14:1-17:26"},
    {"id": "h084", "period": "Passion Week", "event": "Gethsemane",
     "matthew": "Matthew 26:36-46", "mark": "Mark 14:32-42", "luke": "Luke 22:39-46", "john": "John 18:1"},
    {"id": "h085", "period": "Passion Week", "event": "Betrayal and arrest",
     "matthew": "Matthew 26:47-56", "mark": "Mark 14:43-52", "luke": "Luke 22:47-53", "john": "John 18:2-12"},
    {"id": "h086", "period": "Passion Week", "event": "Trials before Annas, Caiaphas, and the Sanhedrin",
     "matthew": "Matthew 26:57-27:2", "mark": "Mark 14:53-15:1", "luke": "Luke 22:54,63-71", "john": "John 18:13-24"},
    {"id": "h087", "period": "Passion Week", "event": "Peter denies Jesus three times",
     "matthew": "Matthew 26:58,69-75", "mark": "Mark 14:54,66-72", "luke": "Luke 22:54-62", "john": "John 18:15-18,25-27"},
    {"id": "h088", "period": "Passion Week", "event": "Trials before Pilate and Herod",
     "matthew": "Matthew 27:2,11-26", "mark": "Mark 15:1-15", "luke": "Luke 23:1-25", "john": "John 18:28-19:16"},
    {"id": "h089", "period": "Passion Week", "event": "The crucifixion",
     "matthew": "Matthew 27:27-56", "mark": "Mark 15:16-41", "luke": "Luke 23:26-49", "john": "John 19:16-37"},
    {"id": "h090", "period": "Passion Week", "event": "The burial",
     "matthew": "Matthew 27:57-66", "mark": "Mark 15:42-47", "luke": "Luke 23:50-56", "john": "John 19:38-42"},
    # ── Resurrection and appearances ────────────────────────────────────────────────────────
    {"id": "h091", "period": "Resurrection and Appearances", "event": "The empty tomb",
     "matthew": "Matthew 28:1-10", "mark": "Mark 16:1-8", "luke": "Luke 24:1-12", "john": "John 20:1-10"},
    {"id": "h092", "period": "Resurrection and Appearances", "event": "Appearance to Mary Magdalene",
     "matthew": "", "mark": "Mark 16:9-11", "luke": "", "john": "John 20:11-18"},
    {"id": "h093", "period": "Resurrection and Appearances", "event": "On the road to Emmaus",
     "matthew": "", "mark": "Mark 16:12-13", "luke": "Luke 24:13-35", "john": ""},
    {"id": "h094", "period": "Resurrection and Appearances", "event": "Appearance to the disciples (Thomas absent, then present)",
     "matthew": "", "mark": "", "luke": "Luke 24:36-43", "john": "John 20:19-29"},
    {"id": "h095", "period": "Resurrection and Appearances", "event": "Appearance by the Sea of Galilee",
     "matthew": "", "mark": "", "luke": "", "john": "John 21:1-25"},
    {"id": "h096", "period": "Resurrection and Appearances", "event": "The Great Commission",
     "matthew": "Matthew 28:16-20", "mark": "Mark 16:14-18", "luke": "", "john": ""},
    {"id": "h097", "period": "Resurrection and Appearances", "event": "The Ascension",
     "matthew": "", "mark": "Mark 16:19-20", "luke": "Luke 24:44-53", "john": ""},
]
_BY_ID = {h["id"]: h for h in _HARMONY}
_PERIOD_ORDER = list(dict.fromkeys(h["period"] for h in _HARMONY))  # first-seen order, stable


def _bible_path() -> Optional[Path]:
    env = os.environ.get("CONCORDANCE_BIBLE_EN", "").strip()
    if env:
        return Path(env)
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    p = (Path(d) if d else Path("data")) / "bible_en.jsonl"
    return p if p.exists() else None


def _parse_ref(ref: str):
    """A single 'Book ch:v-v' reference (no comma-lists, no multi-chapter ranges) -> (book, ch, v1, v2)."""
    import re
    m = re.match(r"^(\d?\s?[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?$", ref.strip())
    if not m:
        return None
    book, ch, v1, v2 = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
    return book, ch, v1, int(v2) if v2 else v1


def _passage_text(ref: str) -> str:
    """The WEB text for a single-chapter reference. Multi-chapter/comma refs (e.g. '5:1-7:29',
    '26:1-5,14-16') are display-only in the table; we don't attempt verbatim inline text for those
    here — the reference itself links out to the full passage reader."""
    if not ref:
        return ""
    parsed = _parse_ref(ref)
    if not parsed:
        return ""
    book, ch, v1, v2 = parsed
    p = _bible_path()
    if not p:
        return ""
    out: List[str] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("book") == book and r.get("chapter") == ch and v1 <= (r.get("verse") or 0) <= v2:
                out.append(r.get("text") or "")
    except OSError:
        return ""
    return " ".join(out)


def periods() -> Dict[str, Any]:
    """Every event, grouped by the phase of the ministry, in narrative order."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for h in _HARMONY:
        groups.setdefault(h["period"], []).append(
            {"id": h["id"], "event": h["event"], **{g: h[g] for g in _GOSPELS}})
    return {"total": len(_HARMONY), "note": NOTE,
            "periods": [{"period": p, "count": len(groups[p]), "events": groups[p]} for p in _PERIOD_ORDER]}


def get(event_id: str) -> Optional[Dict[str, Any]]:
    """One event: its references across all four gospels, plus the WEB text for each that has one
    (found, verbatim, never generated). Returns None for an unknown id."""
    h = _BY_ID.get((event_id or "").strip())
    if not h:
        return None
    witnesses = []
    for g in _GOSPELS:
        ref = h[g]
        if ref:
            witnesses.append({"gospel": g.capitalize(), "ref": ref, "text": _passage_text(ref)})
    return {"id": h["id"], "period": h["period"], "event": h["event"], "witnesses": witnesses,
            "witness_count": len(witnesses), "note": NOTE}


def full() -> Dict[str, Any]:
    """The whole harmony table at once, for a single-page read-through."""
    return periods()


__all__ = ["periods", "get", "full", "NOTE"]
