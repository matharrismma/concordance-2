"""Timeline — Old Testament, New Testament (Acts onward), and Church History, one spine.

The companion to the Harmony of the Gospels: where harmony.py lays the four gospels side by side
for Christ's earthly life, this module lays the rest of the story end to end — creation through the
apostles through the church age to today. Every Scripture reference is fetched verbatim from the
corpus (found, never generated); every date is either well-attested (an external synchronism — an
inscription, an eclipse, a foreign king's records), traditional (later church testimony, honestly
labeled as such), or genuinely disputed among careful scholars, in which case BOTH positions are
given and neither is declared the winner.

We live in the nuance. This is a study aid for seeing where the story sits in time, not a claim to
have settled the early/late Exodus debate, the date of Revelation, or which year Jerusalem fell —
questions serious scholarship still holds open. Where a plain date is given with no dispute noted, it
reflects the ordinary consensus this project could find no live scholarly argument against.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("Old Testament, New Testament (Acts onward), and Church History — one spine, creation to "
        "today. Every reference is found, verbatim World English Bible text, never generated. Where "
        "careful scholarship genuinely disagrees on a date, both positions are given side by side — "
        "we live in the nuance, and no position here is declared the winner.")

_ERA_ORDER = ("Old Testament", "New Testament", "Church History")

# (id, era, period, event, refs, date, disputed, positions, note)
_TIMELINE: List[Dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════════════════════
    # OLD TESTAMENT
    # ══════════════════════════════════════════════════════════════════════════════════════
    # ── Creation and the Patriarchs ─────────────────────────────────────────────────────────
    {"id": "t001", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "Creation of the world", "refs": ["Genesis 1:1-2:3"], "date": "no fixed year (disputed)",
     "disputed": True, "positions": [
         {"view": "Traditional genealogical reckoning (Ussher-style)", "date": "c. 4004 BC"},
         {"view": "Old-earth / framework readings", "date": "no date claimed; the days are not read as a strict recent chronology"}],
     "note": "Genesis fixes no external synchronism for creation itself; every date offered for it comes "
             "from adding up genealogies (and how those genealogies are read) or from reading the days a "
             "different way. Both are real positions within Christian scholarship."},
    {"id": "t002", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "The Fall", "refs": ["Genesis 3:1-24"], "date": "no fixed year",
     "disputed": False, "positions": [],
     "note": "Follows creation narratively; its date depends entirely on whichever creation-dating "
             "framework is held."},
    {"id": "t003", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "The Flood", "refs": ["Genesis 6:1-8:22"], "date": "c. 2300-2500 BC (traditional reckonings)",
     "disputed": True, "positions": [
         {"view": "Ussher's chronology", "date": "c. 2348 BC"},
         {"view": "Other genealogical reckonings (depending on whether Genesis 11's genealogy allows gaps)",
          "date": "c. 2500-2300 BC"}],
     "note": "Every date rests on how the Genesis 11 genealogy is read — as a strict count of years or "
             "as a selective record with gaps, a question the text itself does not settle."},
    {"id": "t004", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "The Tower of Babel", "refs": ["Genesis 11:1-9"], "date": "no fixed year",
     "disputed": False, "positions": [],
     "note": "Placed after the Flood narratively; Genesis gives no year."},
    {"id": "t005", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "The call of Abraham", "refs": ["Genesis 12:1-9"], "date": "c. 2091 BC (traditional) or c. 2166-1900 BC (range)",
     "disputed": True, "positions": [
         {"view": "Ussher's chronology", "date": "c. 2091 BC"},
         {"view": "Conservative range depending on the reckoning of the sojourn in Egypt (Exodus 12:40; Galatians 3:17)",
          "date": "c. 2166-1900 BC"}],
     "note": "The whole patriarchal chronology hinges on how the 430-year sojourn of Exodus 12:40 and "
             "Galatians 3:17 is counted — from Abraham's call, or from Jacob's entry into Egypt."},
    {"id": "t006", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "God's covenant with Abraham", "refs": ["Genesis 15:1-21", "Genesis 17:1-27"],
     "date": "no fixed year", "disputed": False, "positions": [], "note": ""},
    {"id": "t007", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "Birth of Isaac", "refs": ["Genesis 21:1-7"], "date": "no fixed year",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t008", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "Jacob and Esau; Jacob's years with Laban", "refs": ["Genesis 25:19-34", "Genesis 29:1-30"],
     "date": "no fixed year", "disputed": False, "positions": [], "note": ""},
    {"id": "t009", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "Joseph sold into Egypt", "refs": ["Genesis 37:1-36"], "date": "no fixed year",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t010", "era": "Old Testament", "period": "Creation and the Patriarchs",
     "event": "Jacob's family settles in Egypt", "refs": ["Genesis 46:1-47:12"], "date": "c. 1876 BC (traditional)",
     "disputed": False, "positions": [],
     "note": "Ussher's traditional date; depends on the same sojourn-length question as Abraham's call."},
    # ── Exodus and Wilderness ───────────────────────────────────────────────────────────────
    {"id": "t011", "era": "Old Testament", "period": "Exodus and Wilderness",
     "event": "The Exodus from Egypt", "refs": ["Exodus 12:29-42"], "date": "1446 BC or c. 1250-1260 BC (disputed)",
     "disputed": True, "positions": [
         {"view": "Early date — from 1 Kings 6:1's 480 years before Solomon's 4th regnal year", "date": "1446 BC"},
         {"view": "Late date — from the store cities of Pithom and Rameses (Exodus 1:11) and the Merneptah "
                  "Stele's c. 1208 BC mention of Israel in Canaan", "date": "c. 1250-1260 BC"}],
     "note": "One of the most live, unresolved debates in biblical chronology, argued seriously on both "
             "sides by evangelical and mainstream scholars alike. This project takes no side."},
    {"id": "t012", "era": "Old Testament", "period": "Exodus and Wilderness",
     "event": "The Law given at Sinai", "refs": ["Exodus 19:1-20:21"], "date": "shortly after the Exodus",
     "disputed": False, "positions": [], "note": "Dated relative to the Exodus, under either dating above."},
    {"id": "t013", "era": "Old Testament", "period": "Exodus and Wilderness",
     "event": "The twelve spies; forty years of wandering begin", "refs": ["Numbers 13:1-14:45"],
     "date": "shortly after the Exodus", "disputed": False, "positions": [], "note": ""},
    {"id": "t014", "era": "Old Testament", "period": "Exodus and Wilderness",
     "event": "Death of Moses", "refs": ["Deuteronomy 34:1-12"], "date": "40 years after the Exodus",
     "disputed": False, "positions": [], "note": "Dated relative to the Exodus, under either dating above."},
    # ── Conquest and the Judges ─────────────────────────────────────────────────────────────
    {"id": "t015", "era": "Old Testament", "period": "Conquest and the Judges",
     "event": "Conquest of Canaan under Joshua", "refs": ["Joshua 1:1-11:23"],
     "date": "c. 1406 BC or c. 1230-1200 BC (disputed)", "disputed": True, "positions": [
         {"view": "Early date", "date": "c. 1406 BC"}, {"view": "Late date", "date": "c. 1230-1200 BC"}],
     "note": "Follows directly from whichever Exodus date is held."},
    {"id": "t016", "era": "Old Testament", "period": "Conquest and the Judges",
     "event": "The period of the judges", "refs": ["Judges 2:6-16:31"],
     "date": "roughly 350 years (early date) or considerably compressed (late date)",
     "disputed": True, "positions": [
         {"view": "Early-date framework", "date": "the summed judge- and oppression-years run to roughly 350 years"},
         {"view": "Late-date framework", "date": "the same years are read as substantially overlapping regionally"}],
     "note": "Most chronologists on both sides now accept that at least some judgeships were regional and "
             "overlapping, rather than a single strict national sequence — the text itself never claims "
             "otherwise."},
    {"id": "t017", "era": "Old Testament", "period": "Conquest and the Judges",
     "event": "Ruth's story, “in the days when the judges ruled”", "refs": ["Ruth 1:1-4:22"],
     "date": "sometime within the judges period", "disputed": False, "positions": [], "note": ""},
    # ── The United Kingdom ──────────────────────────────────────────────────────────────────
    {"id": "t018", "era": "Old Testament", "period": "The United Kingdom",
     "event": "Saul anointed Israel's first king", "refs": ["1 Samuel 10:1-27"], "date": "c. 1050 BC",
     "disputed": False, "positions": [], "note": "Commonly cited across most chronological systems."},
    {"id": "t019", "era": "Old Testament", "period": "The United Kingdom",
     "event": "David anointed king over all Israel", "refs": ["2 Samuel 5:1-5"], "date": "c. 1010 BC",
     "disputed": False, "positions": [], "note": "Commonly cited across most chronological systems."},
    {"id": "t020", "era": "Old Testament", "period": "The United Kingdom",
     "event": "Solomon's reign begins; Temple construction started", "refs": ["1 Kings 6:1-38"],
     "date": "c. 966 BC", "disputed": False, "positions": [],
     "note": "1 Kings 6:1 dates the Temple's start to 480 years after the Exodus, in Solomon's 4th regnal "
             "year — the single verse at the center of the whole early/late Exodus debate above. Once "
             "Solomon's reign is fixed by later Assyrian synchronisms, this date is comparatively "
             "well-anchored even though the Exodus date it points back to is not."},
    {"id": "t021", "era": "Old Testament", "period": "The United Kingdom",
     "event": "Division of the kingdom after Solomon's death", "refs": ["1 Kings 12:1-24"],
     "date": "931/930 BC", "disputed": False, "positions": [],
     "note": "Edwin Thiele's reconciliation of Israel's and Judah's regnal years (The Mysterious Numbers of "
             "the Hebrew Kings) is the most widely used modern reference chronology for this date."},
    # ── The Divided Kingdom and Exile ───────────────────────────────────────────────────────
    {"id": "t022", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Fall of Samaria (the northern kingdom) to Assyria", "refs": ["2 Kings 17:1-23"],
     "date": "722 BC", "disputed": False, "positions": [],
     "note": "Well-attested; corroborated by Assyrian royal records of Sargon II."},
    {"id": "t023", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Fall of Jerusalem to Babylon; the Temple destroyed", "refs": ["2 Kings 25:1-21"],
     "date": "586 or 587 BC (disputed by one year)", "disputed": True, "positions": [
         {"view": "586 BC (majority; Thiele)", "date": "586 BC"},
         {"view": "587 BC (a real minority position; Rodger Young and others, from Babylonian vs. Judean "
                  "calendar reckoning of Nebuchadnezzar's 19th year)", "date": "587 BC"}],
     "note": "A genuine, still-argued one-year split among careful conservative chronologists, not a "
             "rounding matter."},
    {"id": "t024", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "The Babylonian captivity", "refs": ["Daniel 1:1-7", "Psalms 137:1-9"], "date": "586-539 BC",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t025", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Return under Cyrus's decree", "refs": ["Ezra 1:1-11"], "date": "538 BC",
     "disputed": False, "positions": [], "note": "Corroborated by the Cyrus Cylinder."},
    {"id": "t026", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Rebuilding of the Temple completed", "refs": ["Ezra 6:13-22"], "date": "516 BC",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t027", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Ezra's return to Jerusalem", "refs": ["Ezra 7:1-10"], "date": "c. 458 BC",
     "disputed": False, "positions": [], "note": "Commonly cited; depends on which Persian king's 7th year is meant."},
    {"id": "t028", "era": "Old Testament", "period": "The Divided Kingdom and Exile",
     "event": "Nehemiah rebuilds Jerusalem's walls", "refs": ["Nehemiah 2:1-6:19"], "date": "445 BC",
     "disputed": False, "positions": [], "note": ""},
    # ── Intertestamental Period ─────────────────────────────────────────────────────────────
    {"id": "t029", "era": "Old Testament", "period": "Intertestamental Period",
     "event": "Malachi, the last Old Testament prophet", "refs": ["Malachi 1:1-4:6"], "date": "c. 430s BC",
     "disputed": False, "positions": [], "note": "Closes the Old Testament's own internal witness."},
    {"id": "t030", "era": "Old Testament", "period": "Intertestamental Period",
     "event": "The “four hundred silent years”", "refs": [], "date": "c. 430 BC - 5 BC",
     "disputed": False, "positions": [],
     "note": "No canonical Scripture from this span. The secular-historical bridge into the New Testament "
             "world: Alexander's conquest of the Levant (332 BC), the Ptolemaic and Seleucid periods, the "
             "Maccabean revolt (167-160 BC) and Hasmonean independence, and Rome's conquest of Judea under "
             "Pompey (63 BC)."},

    # ══════════════════════════════════════════════════════════════════════════════════════
    # NEW TESTAMENT (Acts onward — the Gospels are the Harmony's own table)
    # ══════════════════════════════════════════════════════════════════════════════════════
    # ── Pentecost and the Jerusalem Church ──────────────────────────────────────────────────
    {"id": "t031", "era": "New Testament", "period": "Pentecost and the Jerusalem Church",
     "event": "Pentecost; the church begins", "refs": ["Acts 2:1-47"], "date": "AD 30 or AD 33 (disputed)",
     "disputed": True, "positions": [{"view": "AD 30", "date": "AD 30"}, {"view": "AD 33", "date": "AD 33"}],
     "note": "Tied directly to the disputed year of the crucifixion itself, which turns on reconstructing "
             "the Passover/lunar calendar of the relevant years."},
    {"id": "t032", "era": "New Testament", "period": "Pentecost and the Jerusalem Church",
     "event": "Healing at the Beautiful Gate; Peter and John before the Sanhedrin",
     "refs": ["Acts 3:1-4:31"], "date": "shortly after Pentecost", "disputed": False, "positions": [], "note": ""},
    {"id": "t033", "era": "New Testament", "period": "Pentecost and the Jerusalem Church",
     "event": "Ananias and Sapphira", "refs": ["Acts 5:1-11"], "date": "shortly after Pentecost",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t034", "era": "New Testament", "period": "Pentecost and the Jerusalem Church",
     "event": "Stephen's martyrdom, the first Christian martyr", "refs": ["Acts 6:8-7:60"],
     "date": "c. AD 34-36", "disputed": False, "positions": [], "note": "Commonly placed in this range."},
    {"id": "t035", "era": "New Testament", "period": "Pentecost and the Jerusalem Church",
     "event": "Saul's conversion on the road to Damascus", "refs": ["Acts 9:1-19"], "date": "c. AD 33-36",
     "disputed": False, "positions": [],
     "note": "An approximate range; Paul's own later reckoning in Galatians 1:15-2:1 is the chief internal "
             "tool for working backward from later, better-anchored dates."},
    # ── The Church Spreads; Paul's Early Ministry ───────────────────────────────────────────
    {"id": "t036", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "Peter and Cornelius; the gospel opens to the Gentiles", "refs": ["Acts 10:1-48"],
     "date": "c. AD 40s", "disputed": False, "positions": [], "note": ""},
    {"id": "t037", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "The church at Antioch; believers first called Christians", "refs": ["Acts 11:19-26"],
     "date": "c. AD 40s", "disputed": False, "positions": [], "note": ""},
    {"id": "t038", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "Herod Agrippa I's persecution and death", "refs": ["Acts 12:1-23"], "date": "AD 44",
     "disputed": False, "positions": [],
     "note": "Well-attested; corroborated independently by the Jewish historian Josephus (Antiquities "
             "19.343-352) — a strong external anchor for all of Acts' chronology."},
    {"id": "t039", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "Barnabas and Saul's relief visit to Jerusalem", "refs": ["Acts 11:27-30"],
     "date": "c. AD 46", "disputed": False, "positions": [], "note": ""},
    {"id": "t040", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "Paul's first missionary journey", "refs": ["Acts 13:1-14:28"], "date": "c. AD 46-48",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t041", "era": "New Testament", "period": "The Church Spreads; Paul's Early Ministry",
     "event": "The Jerusalem Council", "refs": ["Acts 15:1-35"], "date": "c. AD 48-50",
     "disputed": False, "positions": [],
     "note": "Its exact correlation with the private meeting Paul describes in Galatians 2:1-10 is itself "
             "debated among scholars, though the council's approximate date is not seriously disputed."},
    # ── Paul's Later Missionary Journeys ────────────────────────────────────────────────────
    {"id": "t042", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's second missionary journey", "refs": ["Acts 15:36-18:22"], "date": "c. AD 49-52",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t043", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul before Gallio at Corinth", "refs": ["Acts 18:12-17"], "date": "AD 51-52",
     "disputed": False, "positions": [],
     "note": "The Gallio inscription found at Delphi dates Gallio's proconsulship of Achaia to this year — "
             "one of the strongest external anchors in all of New Testament chronology, from which much "
             "of the rest of Paul's timeline is worked backward and forward."},
    {"id": "t044", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's third missionary journey", "refs": ["Acts 18:23-21:16"], "date": "c. AD 52-57",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t045", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's arrest in Jerusalem", "refs": ["Acts 21:27-36"], "date": "c. AD 57",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t046", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's imprisonment at Caesarea", "refs": ["Acts 24:1-26:32"], "date": "c. AD 57-59",
     "disputed": False, "positions": [], "note": "Under the Roman governors Felix, then Festus."},
    {"id": "t047", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's voyage to Rome and shipwreck", "refs": ["Acts 27:1-28:10"], "date": "c. AD 59-60",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t048", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's first Roman imprisonment", "refs": ["Acts 28:16-31"], "date": "c. AD 60-62",
     "disputed": False, "positions": [],
     "note": "Traditionally the setting for Ephesians, Philippians, Colossians, and Philemon (the “Prison "
             "Epistles”), though some scholars argue an earlier Ephesian imprisonment for some of these "
             "letters instead."},
    {"id": "t049", "era": "New Testament", "period": "Paul's Later Missionary Journeys",
     "event": "Paul's release and further ministry", "refs": [], "date": "c. AD 62-64",
     "disputed": False, "positions": [],
     "note": "Not narrated in Acts, which ends at the first imprisonment. The traditional reconstruction, "
             "built from the Pastoral Epistles' travel notices, holds that Paul was released, ministered "
             "further (Crete, Macedonia, Nicopolis), then was arrested again. This reconstruction depends "
             "on Pauline authorship of the Pastorals, which is itself contested in critical scholarship."},
    # ── The Apostolic Church Under Persecution ──────────────────────────────────────────────
    {"id": "t050", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "Paul's martyrdom in Rome", "refs": [], "date": "c. AD 64-67",
     "disputed": False, "positions": [],
     "note": "Church tradition (Eusebius, building on earlier sources including 1 Clement), under Nero; not "
             "itself narrated in Scripture."},
    {"id": "t051", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "Peter's martyrdom in Rome", "refs": [], "date": "c. AD 64-68",
     "disputed": False, "positions": [],
     "note": "Church tradition, under Nero, by crucifixion — read by the church as the fulfillment of John "
             "21:18-19. The “upside down” detail comes from later tradition (Origen, via Eusebius), not "
             "an earlier source."},
    {"id": "t052", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "The Neronic persecution and the burning of Rome", "refs": [], "date": "AD 64",
     "disputed": False, "positions": [],
     "note": "Attested by the Roman historian Tacitus (Annals 15.44), an external, non-Christian witness to "
             "the persecution's scale."},
    {"id": "t053", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "Destruction of Jerusalem and the Temple", "refs": ["Matthew 24:1-2", "Luke 21:20-24"],
     "date": "AD 70", "disputed": False, "positions": [],
     "note": "Extensively attested by the Jewish historian Josephus, an eyewitness; the church has long "
             "read this as the near-term fulfillment Jesus described in the Olivet Discourse."},
    {"id": "t054", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "John's exile on Patmos; the writing of Revelation", "refs": ["Revelation 1:9-11"],
     "date": "c. AD 95-96 or c. AD 65-69 (disputed)", "disputed": True, "positions": [
         {"view": "Late date (majority; Irenaeus, Against Heresies 5.30.3, writing c. AD 180, places it "
                  "“toward the end of Domitian's reign”)", "date": "c. AD 95-96"},
         {"view": "Early date (a minority position, argued chiefly from internal evidence rather than an "
                  "ancient named source)", "date": "c. AD 65-69"}],
     "note": "The late date is the majority scholarly view by a wide margin, but the early date has serious "
             "advocates. This project takes no side."},
    {"id": "t055", "era": "New Testament", "period": "The Apostolic Church Under Persecution",
     "event": "Death of the apostle John", "refs": [], "date": "c. AD 98-100",
     "disputed": False, "positions": [], "note": "Church tradition — at Ephesus, the last surviving apostle."},

    # ══════════════════════════════════════════════════════════════════════════════════════
    # CHURCH HISTORY (post-apostolic to today)
    # ══════════════════════════════════════════════════════════════════════════════════════
    # ── The Ante-Nicene Church ──────────────────────────────────────────────────────────────
    {"id": "t056", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Martyrdom of Ignatius of Antioch", "refs": [], "date": "c. AD 107-110 (traditional; disputed)",
     "disputed": True, "positions": [
         {"view": "Traditional (Trajanic; Eusebius)", "date": "c. AD 107-110"},
         {"view": "A minority of scholars (e.g. Pervo, Barnes) argue later", "date": "AD 130s-140s"}],
     "note": "Rests on later church tradition rather than a contemporary synchronism, which is why a real "
             "minority view exists for a later date."},
    {"id": "t057", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Martyrdom of Polycarp of Smyrna", "refs": [], "date": "c. AD 155-156 or c. AD 167-168 (disputed)",
     "disputed": True, "positions": [
         {"view": "Earlier date (from internal details in the Martyrdom of Polycarp text)", "date": "c. AD 155-156"},
         {"view": "Later date (Eusebius, placing it under Marcus Aurelius)", "date": "c. AD 167-168"}],
     "note": "A disciple of the apostle John by tradition (Irenaeus). Modern scholarship leans toward the "
             "earlier date but this is not settled."},
    {"id": "t058", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Justin Martyr's apologetic writings and martyrdom", "refs": [], "date": "c. AD 150-165",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t059", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Irenaeus writes Against Heresies", "refs": [], "date": "c. AD 180",
     "disputed": False, "positions": [], "note": "Defends apostolic tradition against Gnosticism."},
    {"id": "t060", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Tertullian's writings; Latin Christian theology takes shape", "refs": [], "date": "c. AD 197-220",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t061", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Origen's scholarly work in Alexandria", "refs": [], "date": "c. AD 230s",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t062", "era": "Church History", "period": "The Ante-Nicene Church",
     "event": "Waves of persecution under Decius and then Diocletian", "refs": [],
     "date": "AD 250 and AD 303-311", "disputed": False, "positions": [],
     "note": "The Decian persecution (AD 250) and the “Great Persecution” under Diocletian (AD 303-311) "
             "were the most severe and empire-wide."},
    # ── Constantine, Nicaea, and the Imperial Church ────────────────────────────────────────
    {"id": "t063", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "The Edict of Milan grants religious toleration", "refs": [], "date": "AD 313",
     "disputed": False, "positions": [],
     "note": "Under Constantine and Licinius, ending the era of empire-wide persecution."},
    {"id": "t064", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "The Council of Nicaea", "refs": [], "date": "AD 325", "disputed": False, "positions": [],
     "note": "Called by Constantine; condemns Arianism and affirms the Son's full deity in the Creed's "
             "first form."},
    {"id": "t065", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "The Council of Constantinople completes the Nicene Creed", "refs": [], "date": "AD 381",
     "disputed": False, "positions": [], "note": "Affirms the deity of the Holy Spirit."},
    {"id": "t066", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "Jerome completes the Latin Vulgate", "refs": [], "date": "c. AD 405",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t067", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "Augustine of Hippo's major works", "refs": [], "date": "c. AD 397-426",
     "disputed": False, "positions": [], "note": "Confessions, then City of God."},
    {"id": "t068", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "The Council of Ephesus condemns Nestorianism", "refs": [], "date": "AD 431",
     "disputed": False, "positions": [],
     "note": "Affirms Mary as “Theotokos” (God-bearer) as a way of safeguarding the unity of Christ's person."},
    {"id": "t069", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "The Council of Chalcedon defines Christ's two natures", "refs": [], "date": "AD 451",
     "disputed": False, "positions": [],
     "note": "Accepted by the Catholic, Eastern Orthodox, and most Protestant traditions, but rejected by "
             "the Oriental Orthodox churches (Coptic, Armenian, Syriac, Ethiopian), who hold a different "
             "Christological formula — a real, still-unhealed division worth naming plainly."},
    {"id": "t070", "era": "Church History", "period": "Constantine, Nicaea, and the Imperial Church",
     "event": "Fall of the Western Roman Empire", "refs": [], "date": "AD 476",
     "disputed": False, "positions": [], "note": "Traditionally marks the start of the medieval period in Western historiography."},
    # ── The Medieval Church ─────────────────────────────────────────────────────────────────
    {"id": "t071", "era": "Church History", "period": "The Medieval Church",
     "event": "Gregory the Great sends missionaries to England", "refs": [], "date": "c. AD 596-604",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t072", "era": "Church History", "period": "The Medieval Church",
     "event": "The rise of Islam and the Muslim conquests reach historically Christian lands", "refs": [],
     "date": "AD 630s-710s", "disputed": False, "positions": [],
     "note": "Across the Levant, North Africa, and Spain — one of the most significant shifts in "
             "Christianity's geography in its history."},
    {"id": "t073", "era": "Church History", "period": "The Medieval Church",
     "event": "The Filioque controversy develops between East and West", "refs": [],
     "date": "6th-11th centuries", "disputed": False, "positions": [],
     "note": "The Western church's addition of “and the Son” to the Creed's wording on the Spirit's "
             "procession, formally settled in Rome by the 11th century — a real and still-unresolved point "
             "of difference between Eastern Orthodox and Western (Catholic and most Protestant) theology."},
    {"id": "t074", "era": "Church History", "period": "The Medieval Church",
     "event": "The East-West Schism (“The Great Schism”)", "refs": [], "date": "AD 1054",
     "disputed": False, "positions": [],
     "note": "Mutual excommunications between Rome and Constantinople. The Orthodox and Catholic traditions "
             "today still describe its causes somewhat differently (papal authority claims, the Filioque, "
             "and liturgical/cultural differences) — a real division this project does not adjudicate."},
    {"id": "t075", "era": "Church History", "period": "The Medieval Church",
     "event": "The First Crusade is called", "refs": [], "date": "AD 1095",
     "disputed": False, "positions": [],
     "note": "By Pope Urban II. The Crusades remain a complex and still-debated chapter of Christian "
             "history, named here as a historical fact without adjudicating the wider moral debate."},
    {"id": "t076", "era": "Church History", "period": "The Medieval Church",
     "event": "Peter Waldo and the Waldensians", "refs": [], "date": "c. AD 1170s",
     "disputed": False, "positions": [],
     "note": "An early pre-Reformation movement emphasizing vernacular Scripture and apostolic simplicity."},
    {"id": "t077", "era": "Church History", "period": "The Medieval Church",
     "event": "John Wycliffe translates the Bible into English", "refs": [], "date": "c. AD 1382",
     "disputed": False, "positions": [], "note": "Later called the “Morning Star of the Reformation.”"},
    {"id": "t078", "era": "Church History", "period": "The Medieval Church",
     "event": "Jan Hus is burned at the Council of Constance", "refs": [], "date": "AD 1415",
     "disputed": False, "positions": [], "note": "A Bohemian reformer influenced by Wycliffe."},
    {"id": "t079", "era": "Church History", "period": "The Medieval Church",
     "event": "Johannes Gutenberg's printing press; the Gutenberg Bible", "refs": [], "date": "c. AD 1454-1455",
     "disputed": False, "positions": [],
     "note": "Printed at Mainz — a technological turning point that later made the Reformation's spread of "
             "vernacular Scripture possible at unprecedented scale."},
    {"id": "t080", "era": "Church History", "period": "The Medieval Church",
     "event": "The fall of Constantinople to the Ottomans", "refs": [], "date": "AD 1453",
     "disputed": False, "positions": [], "note": "Ends the Byzantine Empire."},
    # ── The Reformation ──────────────────────────────────────────────────────────────────────
    {"id": "t081", "era": "Church History", "period": "The Reformation",
     "event": "Martin Luther's Ninety-Five Theses", "refs": [], "date": "October 31, 1517",
     "disputed": False, "positions": [],
     "note": "The theses' existence and this date are not disputed, but the specific detail of Luther "
             "physically nailing them to the Wittenberg Castle Church door is contested: no contemporary "
             "account, including Luther's own writings, records it, and the earliest report comes from "
             "Melanchthon, writing after Luther's death and not himself an eyewitness."},
    {"id": "t082", "era": "Church History", "period": "The Reformation",
     "event": "The Diet of Worms; Luther's stand", "refs": [], "date": "AD 1521",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t083", "era": "Church History", "period": "The Reformation",
     "event": "Huldrych Zwingli's reforms in Zurich", "refs": [], "date": "beginning c. AD 1519",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t084", "era": "Church History", "period": "The Reformation",
     "event": "The Anabaptist movement begins", "refs": [], "date": "c. AD 1525",
     "disputed": False, "positions": [],
     "note": "In Zurich, emphasizing believer's baptism; historically persecuted by both Catholic and "
             "mainline Protestant civil authorities of the era."},
    {"id": "t085", "era": "Church History", "period": "The Reformation",
     "event": "John Calvin publishes the Institutes; reforms Geneva", "refs": [],
     "date": "AD 1536 (first edition)", "disputed": False, "positions": [],
     "note": "Reforms in Geneva developed further through the 1540s-1550s."},
    {"id": "t086", "era": "Church History", "period": "The Reformation",
     "event": "The English Reformation; Henry VIII's break with Rome", "refs": [], "date": "AD 1534",
     "disputed": False, "positions": [],
     "note": "The Act of Supremacy — a reformation with distinct political as well as theological dimensions."},
    {"id": "t087", "era": "Church History", "period": "The Reformation",
     "event": "The Council of Trent", "refs": [], "date": "AD 1545-1563", "disputed": False, "positions": [],
     "note": "The Catholic Church's own clarification and response to the Reformation."},
    {"id": "t088", "era": "Church History", "period": "The Reformation",
     "event": "The King James Version of the Bible published", "refs": [], "date": "AD 1611",
     "disputed": False, "positions": [], "note": ""},
    # ── Post-Reformation to the Great Awakenings ────────────────────────────────────────────
    {"id": "t089", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "The Pilgrims and Puritans settle New England", "refs": [], "date": "beginning AD 1620",
     "disputed": False, "positions": [], "note": "Seeking freedom to worship and reform the church."},
    {"id": "t090", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "The Westminster Assembly and Confession", "refs": [], "date": "AD 1643-1646",
     "disputed": False, "positions": [], "note": ""},
    {"id": "t091", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "The First Great Awakening", "refs": [], "date": "c. AD 1730s-1740s",
     "disputed": False, "positions": [],
     "note": "Associated chiefly with Jonathan Edwards and George Whitefield, spanning Britain and colonial "
             "America."},
    {"id": "t092", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "John Wesley and the birth of Methodism", "refs": [], "date": "AD 1738",
     "disputed": False, "positions": [], "note": "Wesley's Aldersgate experience and the movement that followed."},
    {"id": "t093", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "William Carey and the modern Protestant missions movement", "refs": [],
     "date": "AD 1792-1793", "disputed": False, "positions": [],
     "note": "Carey's “Enquiry” (1792) and his sailing for India (1793)."},
    {"id": "t094", "era": "Church History", "period": "Post-Reformation to the Great Awakenings",
     "event": "The Second Great Awakening", "refs": [], "date": "c. AD 1790s-1840s",
     "disputed": False, "positions": [], "note": "American frontier revivals and camp meetings."},
    # ── The Modern and Global Church ────────────────────────────────────────────────────────
    {"id": "t095", "era": "Church History", "period": "The Modern and Global Church",
     "event": "The fundamentalist-modernist controversy", "refs": [], "date": "late 19th-early 20th century",
     "disputed": False, "positions": [],
     "note": "A significant division within Protestantism over biblical higher criticism and the authority "
             "of Scripture, named here evenhandedly rather than adjudicated."},
    {"id": "t096", "era": "Church History", "period": "The Modern and Global Church",
     "event": "The Azusa Street Revival", "refs": [], "date": "beginning AD 1906",
     "disputed": False, "positions": [],
     "note": "In Los Angeles, under William J. Seymour — the event most historians point to as the birth of "
             "the modern Pentecostal movement."},
    {"id": "t097", "era": "Church History", "period": "The Modern and Global Church",
     "event": "The World Missionary Conference at Edinburgh", "refs": [], "date": "AD 1910",
     "disputed": False, "positions": [], "note": "A landmark of the modern missions and ecumenical movements."},
    {"id": "t098", "era": "Church History", "period": "The Modern and Global Church",
     "event": "The Second Vatican Council", "refs": [], "date": "AD 1962-1965", "disputed": False, "positions": [],
     "note": "A major council of the Catholic Church addressing its relationship to the modern world."},
    {"id": "t099", "era": "Church History", "period": "The Modern and Global Church",
     "event": "Billy Graham's crusades and 20th-century American evangelicalism", "refs": [],
     "date": "beginning c. AD 1949", "disputed": False, "positions": [], "note": ""},
    {"id": "t100", "era": "Church History", "period": "The Modern and Global Church",
     "event": "The growth of Christianity in the Global South", "refs": [], "date": "20th-21st centuries",
     "disputed": False, "positions": [],
     "note": "Across this span, the demographic center of the world's Christian population has shifted "
             "decisively toward Africa, Asia, and Latin America — bringing this history to today."},
]
_BY_ID = {t["id"]: t for t in _TIMELINE}


def _bible_path() -> Optional[Path]:
    env = os.environ.get("CONCORDANCE_BIBLE_EN", "").strip()
    if env:
        return Path(env)
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    p = (Path(d) if d else Path("data")) / "bible_en.jsonl"
    return p if p.exists() else None


def _parse_ref(ref: str):
    """A single 'Book ch:v-v' reference (no comma-lists, no multi-chapter ranges) -> (book, ch, v1, v2)."""
    m = re.match(r"^(\d?\s?[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?$", ref.strip())
    if not m:
        return None
    book, ch, v1, v2 = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
    return book, ch, v1, int(v2) if v2 else v1


def _passage_text(ref: str) -> str:
    """The WEB text for a single-chapter reference. Multi-chapter/whole-book refs are display-only in
    the table; we don't attempt verbatim inline text for those — the reference links out to the full
    passage reader instead."""
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


def eras() -> Dict[str, Any]:
    """Every event, grouped era -> period, in the order the story unfolds."""
    era_groups: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    era_period_order: Dict[str, List[str]] = {}
    for t in _TIMELINE:
        e, p = t["era"], t["period"]
        era_groups.setdefault(e, {})
        era_period_order.setdefault(e, [])
        if p not in era_groups[e]:
            era_groups[e][p] = []
            era_period_order[e].append(p)
        era_groups[e][p].append({
            "id": t["id"], "event": t["event"], "date": t["date"], "disputed": t["disputed"]})
    out = []
    for e in _ERA_ORDER:
        periods = [{"period": p, "count": len(era_groups[e][p]), "events": era_groups[e][p]}
                   for p in era_period_order.get(e, [])]
        out.append({"era": e, "count": sum(x["count"] for x in periods), "periods": periods})
    return {"total": len(_TIMELINE), "note": NOTE, "eras": out}


def get(event_id: str) -> Optional[Dict[str, Any]]:
    """One event: its scripture references with fetched WEB text where available (found, verbatim,
    never generated), its dating (with both positions if disputed), and its note. None for an unknown id."""
    t = _BY_ID.get((event_id or "").strip())
    if not t:
        return None
    refs = [{"ref": r, "text": _passage_text(r)} for r in t["refs"]]
    return {"id": t["id"], "era": t["era"], "period": t["period"], "event": t["event"], "refs": refs,
            "date": t["date"], "disputed": t["disputed"], "positions": t["positions"], "note": t["note"]}


def full() -> Dict[str, Any]:
    """The whole timeline at once, for a single-page read-through."""
    return eras()


__all__ = ["eras", "get", "full", "NOTE"]
