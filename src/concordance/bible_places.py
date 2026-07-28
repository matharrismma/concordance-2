"""The places of the Bible — real coordinates, honest uncertainty.

Contract §6 item 9: "Maps/Atlas — real biblical place coordinates." The same invariants as the
Harmony, the Timeline and the study tables:

  * every place carries refs a reader can open;
  * coordinates are given ONLY where the identification is secure — a place whose location is
    genuinely disputed (Mount Sinai, Emmaus, Bethsaida, Golgotha) says so and names the candidates
    rather than planting one flag; a place nobody can locate (Eden, Ophir, Tarshish) is listed
    WITHOUT coordinates, because an honest blank beats a confident guess;
  * the curated coordinates are cross-checked against the geonames gazetteer at test time where a
    modern city continues the ancient one (Jerusalem, Damascus, Athens, Rome …) — the table is
    verified against an independent source, not merely asserted.

Witness-gated like the other study surfaces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# status: "located" (secure identification, coordinates given) · "disputed" (candidates named,
# traditional coordinates given only when one candidate has long-standing precedence) ·
# "unlocated" (no coordinates — honest blank).
PLACES: List[Dict[str, Any]] = [
    # ── The land: cities of Israel and Judah ──────────────────────────────────────────────
    {"name": "Jerusalem", "status": "located", "lat": 31.7683, "lon": 35.2137, "modern": "Jerusalem",
     "period": "all", "refs": ["2 Samuel 5:6-7", "Psalm 122:6", "Luke 24:47"]},
    {"name": "Bethlehem", "status": "located", "lat": 31.7054, "lon": 35.2024, "modern": "Bethlehem (Beit Lahm)",
     "period": "all", "refs": ["Micah 5:2", "Ruth 1:19", "Matthew 2:1"]},
    {"name": "Nazareth", "status": "located", "lat": 32.7021, "lon": 35.2978, "modern": "Nazareth",
     "period": "NT", "refs": ["Luke 1:26-27", "Matthew 2:23", "John 1:46"]},
    {"name": "Capernaum", "status": "located", "lat": 32.8811, "lon": 35.5751, "modern": "Kfar Nahum (ruins)",
     "period": "NT", "refs": ["Matthew 4:13", "Mark 2:1", "Luke 7:1"]},
    {"name": "Jericho", "status": "located", "lat": 31.8611, "lon": 35.4444, "modern": "Jericho (Tell es-Sultan)",
     "period": "all", "refs": ["Joshua 6:20", "Luke 19:1-5"]},
    {"name": "Hebron", "status": "located", "lat": 31.5326, "lon": 35.0998, "modern": "Hebron (Al-Khalil)",
     "period": "OT", "refs": ["Genesis 23:2", "2 Samuel 2:11"]},
    {"name": "Beersheba", "status": "located", "lat": 31.2518, "lon": 34.7913, "modern": "Be'er Sheva",
     "period": "OT", "refs": ["Genesis 21:31", "Judges 20:1"]},
    {"name": "Dan", "status": "located", "lat": 33.2486, "lon": 35.6523, "modern": "Tel Dan",
     "period": "OT", "refs": ["Judges 18:29", "1 Kings 12:29"]},
    {"name": "Shechem", "status": "located", "lat": 32.2137, "lon": 35.2817, "modern": "Tell Balata, near Nablus",
     "period": "OT", "refs": ["Genesis 12:6", "Joshua 24:1", "John 4:5-6"]},
    {"name": "Shiloh", "status": "located", "lat": 32.0556, "lon": 35.2897, "modern": "Khirbet Seilun",
     "period": "OT", "refs": ["Joshua 18:1", "1 Samuel 3:21"]},
    {"name": "Bethel", "status": "located", "lat": 31.9308, "lon": 35.2394, "modern": "Beitin",
     "period": "OT", "refs": ["Genesis 28:19", "1 Kings 12:29"]},
    {"name": "Samaria", "status": "located", "lat": 32.2761, "lon": 35.1897, "modern": "Sebastia",
     "period": "all", "refs": ["1 Kings 16:24", "John 4:4"]},
    {"name": "Megiddo", "status": "located", "lat": 32.5850, "lon": 35.1833, "modern": "Tel Megiddo",
     "period": "OT", "refs": ["Judges 5:19", "2 Kings 23:29", "Revelation 16:16"]},
    {"name": "Joppa", "status": "located", "lat": 32.0500, "lon": 34.7500, "modern": "Jaffa (Tel Aviv-Yafo)",
     "period": "all", "refs": ["Jonah 1:3", "Acts 9:36"]},
    {"name": "Caesarea", "status": "located", "lat": 32.5000, "lon": 34.8917, "modern": "Caesarea Maritima",
     "period": "NT", "refs": ["Acts 10:1", "Acts 23:23-24"]},
    {"name": "Caesarea Philippi", "status": "located", "lat": 33.2486, "lon": 35.6944, "modern": "Banias",
     "period": "NT", "refs": ["Matthew 16:13-16", "Mark 8:27"]},
    {"name": "Gaza", "status": "located", "lat": 31.5000, "lon": 34.4667, "modern": "Gaza",
     "period": "OT", "refs": ["Judges 16:21", "Acts 8:26"]},
    {"name": "Ashkelon", "status": "located", "lat": 31.6658, "lon": 34.5664, "modern": "Ashkelon",
     "period": "OT", "refs": ["Judges 14:19", "1 Samuel 6:17"]},
    {"name": "Bethany", "status": "located", "lat": 31.7714, "lon": 35.2586, "modern": "Al-Eizariya",
     "period": "NT", "refs": ["John 11:1", "Mark 11:11"]},
    {"name": "Gethsemane", "status": "located", "lat": 31.7794, "lon": 35.2397, "modern": "foot of the Mount of Olives",
     "period": "NT", "refs": ["Matthew 26:36", "Mark 14:32"]},
    {"name": "Mount of Olives", "status": "located", "lat": 31.7780, "lon": 35.2454, "modern": "Jerusalem, east ridge",
     "period": "all", "refs": ["Zechariah 14:4", "Luke 22:39", "Acts 1:12"]},
    {"name": "Bethany beyond the Jordan", "status": "located", "lat": 31.8371, "lon": 35.5547,
     "modern": "Al-Maghtas (traditional baptism site)", "period": "NT", "refs": ["John 1:28", "Matthew 3:13"]},
    # ── Mountains and waters ──────────────────────────────────────────────────────────────
    {"name": "Mount Carmel", "status": "located", "lat": 32.7333, "lon": 35.0500, "modern": "Mount Carmel",
     "period": "OT", "refs": ["1 Kings 18:19-20", "1 Kings 18:42"]},
    {"name": "Mount Tabor", "status": "located", "lat": 32.6870, "lon": 35.3903, "modern": "Har Tavor",
     "period": "OT", "refs": ["Judges 4:6", "Psalm 89:12"]},
    {"name": "Mount Hermon", "status": "located", "lat": 33.4160, "lon": 35.8570, "modern": "Jabal ash-Shaykh",
     "period": "all", "refs": ["Deuteronomy 3:8", "Psalm 133:3"]},
    {"name": "Mount Nebo", "status": "located", "lat": 31.7683, "lon": 35.7253, "modern": "Jabal Nibu, Jordan",
     "period": "OT", "refs": ["Deuteronomy 34:1", "Deuteronomy 34:4-5"]},
    {"name": "Mount Gerizim", "status": "located", "lat": 32.2000, "lon": 35.2731, "modern": "Jabal Jarizim",
     "period": "all", "refs": ["Deuteronomy 11:29", "John 4:20"]},
    {"name": "Sea of Galilee", "status": "located", "lat": 32.8000, "lon": 35.5900, "modern": "Lake Kinneret",
     "period": "NT", "refs": ["Matthew 4:18", "Mark 4:39", "John 21:1"]},
    {"name": "Dead Sea (Salt Sea)", "status": "located", "lat": 31.5000, "lon": 35.5000, "modern": "Dead Sea",
     "period": "OT", "refs": ["Genesis 14:3", "Ezekiel 47:8"]},
    {"name": "Jordan River", "status": "located", "lat": 32.3000, "lon": 35.5600, "modern": "Nahr al-Urdun",
     "period": "all", "refs": ["Joshua 3:15-17", "2 Kings 5:14", "Matthew 3:13"],
     "note": "A river, not a point — the marker sits mid-course; the crossing near Jericho and the baptism site are separate entries."},
    # ── The wider Old Testament world ─────────────────────────────────────────────────────
    {"name": "Babylon", "status": "located", "lat": 32.5364, "lon": 44.4208, "modern": "Hillah, Iraq (ruins)",
     "period": "OT", "refs": ["2 Kings 25:11", "Daniel 1:1", "Jeremiah 29:10"]},
    {"name": "Nineveh", "status": "located", "lat": 36.3600, "lon": 43.1520, "modern": "Mosul, Iraq (ruins)",
     "period": "OT", "refs": ["Jonah 3:3", "Nahum 1:1"]},
    {"name": "Ur of the Chaldees", "status": "disputed", "lat": 30.9626, "lon": 46.1030,
     "modern": "Tell el-Muqayyar, Iraq (the standard identification)",
     "candidates": ["Tell el-Muqayyar in southern Iraq (the standard view)",
                    "a northern Ur near Harran (Urfa tradition)"],
     "period": "OT", "refs": ["Genesis 11:31", "Genesis 15:7"]},
    {"name": "Haran", "status": "located", "lat": 36.8646, "lon": 39.0261, "modern": "Harran, Türkiye",
     "period": "OT", "refs": ["Genesis 11:31", "Genesis 28:10"]},
    {"name": "Mount Ararat", "status": "disputed", "lat": 39.7020, "lon": 44.2988,
     "modern": "Ağrı Dağı, Türkiye (the traditional peak)",
     "candidates": ["Genesis names the MOUNTAINS of Ararat (Urartu) — a region, not one summit",
                    "Ağrı Dağı is the traditional peak within it"],
     "period": "OT", "refs": ["Genesis 8:4"]},
    {"name": "Memphis (Noph)", "status": "located", "lat": 29.8444, "lon": 31.2506, "modern": "Mit Rahina, Egypt",
     "period": "OT", "refs": ["Jeremiah 46:19", "Hosea 9:6"]},
    {"name": "Goshen", "status": "disputed", "lat": 30.5500, "lon": 31.8000,
     "modern": "eastern Nile delta (approximate centre)",
     "candidates": ["the Wadi Tumilat and eastern delta — a REGION; the marker is an area centre, not a town"],
     "period": "OT", "refs": ["Genesis 47:6", "Exodus 8:22"]},
    {"name": "Mount Sinai (Horeb)", "status": "disputed", "lat": 28.5394, "lon": 33.9751,
     "modern": "Jebel Musa, Egypt (the traditional site since at least the 4th century)",
     "candidates": ["Jebel Musa in the south Sinai (traditional)",
                    "other Sinai peaks (Jebel Serbal, Jebel Sin Bishar)",
                    "sites in northwest Arabia (Jebel al-Lawz) argued from Galatians 4:25"],
     "period": "OT", "refs": ["Exodus 19:20", "Exodus 3:1", "1 Kings 19:8"]},
    {"name": "Kadesh-barnea", "status": "disputed", "lat": 30.6870, "lon": 34.4260,
     "modern": "Ein el-Qudeirat (the common identification)",
     "candidates": ["Ein el-Qudeirat (most common)", "Ein Qadis nearby"],
     "period": "OT", "refs": ["Numbers 13:26", "Deuteronomy 1:19"]},
    {"name": "Susa (Shushan)", "status": "located", "lat": 32.1892, "lon": 48.2436, "modern": "Shush, Iran",
     "period": "OT", "refs": ["Esther 1:2", "Nehemiah 1:1", "Daniel 8:2"]},
    {"name": "Tyre", "status": "located", "lat": 33.2708, "lon": 35.2033, "modern": "Sur, Lebanon",
     "period": "all", "refs": ["Ezekiel 26:3-4", "Mark 7:24"]},
    {"name": "Sidon", "status": "located", "lat": 33.5606, "lon": 35.3758, "modern": "Saida, Lebanon",
     "period": "all", "refs": ["Genesis 10:19", "Acts 27:3"]},
    {"name": "Damascus", "status": "located", "lat": 33.5131, "lon": 36.2919, "modern": "Damascus, Syria",
     "period": "all", "refs": ["Genesis 14:15", "2 Kings 5:12", "Acts 9:3"]},
    {"name": "Sela (Petra)", "status": "disputed", "lat": 30.3285, "lon": 35.4444,
     "modern": "Petra, Jordan (commonly identified)",
     "candidates": ["Umm el-Biyara at Petra (common)", "es-Sela near Buseirah"],
     "period": "OT", "refs": ["2 Kings 14:7", "Isaiah 16:1"]},
    # ── The gospel geography that is genuinely argued ─────────────────────────────────────
    {"name": "Cana of Galilee", "status": "disputed", "lat": 32.7469, "lon": 35.3397,
     "modern": "Kafr Kanna (traditional)",
     "candidates": ["Kafr Kanna (traditional pilgrim site)", "Khirbet Qana (favoured by many archaeologists)"],
     "period": "NT", "refs": ["John 2:1-2", "John 4:46"]},
    {"name": "Bethsaida", "status": "disputed", "lat": 32.9100, "lon": 35.6310,
     "modern": "north of the Sea of Galilee",
     "candidates": ["et-Tell (the long-standing identification)", "el-Araj (an active excavation argument)"],
     "period": "NT", "refs": ["Mark 8:22", "Luke 9:10", "John 1:44"]},
    {"name": "Emmaus", "status": "unlocated",
     "candidates": ["Emmaus-Nicopolis (Imwas)", "Abu Ghosh", "el-Qubeibeh", "Motza"],
     "period": "NT", "refs": ["Luke 24:13"],
     "note": "Luke gives a distance (sixty stadia), and four sites have serious claims — no flag is planted."},
    {"name": "Golgotha (Calvary)", "status": "disputed", "lat": 31.7785, "lon": 35.2298,
     "modern": "within the Church of the Holy Sepulchre (the majority identification)",
     "candidates": ["the Holy Sepulchre site (majority, attested from the 4th century)",
                    "the Garden Tomb / Skull Hill north of the Damascus Gate (19th-century proposal)"],
     "period": "NT", "refs": ["John 19:17-18", "Matthew 27:33"]},
    # ── The apostolic roads ───────────────────────────────────────────────────────────────
    {"name": "Antioch (Syrian)", "status": "located", "lat": 36.2000, "lon": 36.1667, "modern": "Antakya, Türkiye",
     "period": "NT", "refs": ["Acts 11:26", "Acts 13:1-3"]},
    {"name": "Tarsus", "status": "located", "lat": 36.9177, "lon": 34.8949, "modern": "Tarsus, Türkiye",
     "period": "NT", "refs": ["Acts 9:11", "Acts 22:3"]},
    {"name": "Ephesus", "status": "located", "lat": 37.9411, "lon": 27.3419, "modern": "Selçuk, Türkiye (ruins)",
     "period": "NT", "refs": ["Acts 19:1", "Ephesians 1:1", "Revelation 2:1"]},
    {"name": "Smyrna", "status": "located", "lat": 38.4237, "lon": 27.1428, "modern": "İzmir, Türkiye",
     "period": "NT", "refs": ["Revelation 2:8"]},
    {"name": "Pergamum", "status": "located", "lat": 39.1319, "lon": 27.1844, "modern": "Bergama, Türkiye",
     "period": "NT", "refs": ["Revelation 2:12"]},
    {"name": "Thyatira", "status": "located", "lat": 38.9184, "lon": 27.8388, "modern": "Akhisar, Türkiye",
     "period": "NT", "refs": ["Revelation 2:18", "Acts 16:14"]},
    {"name": "Sardis", "status": "located", "lat": 38.4883, "lon": 28.0399, "modern": "Sart, Türkiye",
     "period": "NT", "refs": ["Revelation 3:1"]},
    {"name": "Philadelphia", "status": "located", "lat": 38.3500, "lon": 28.5167, "modern": "Alaşehir, Türkiye",
     "period": "NT", "refs": ["Revelation 3:7"]},
    {"name": "Laodicea", "status": "located", "lat": 37.8358, "lon": 29.1075, "modern": "near Denizli, Türkiye",
     "period": "NT", "refs": ["Revelation 3:14", "Colossians 4:16"]},
    {"name": "Colossae", "status": "located", "lat": 37.7859, "lon": 29.2607, "modern": "near Honaz, Türkiye (unexcavated tell)",
     "period": "NT", "refs": ["Colossians 1:2"]},
    {"name": "Patmos", "status": "located", "lat": 37.3090, "lon": 26.5470, "modern": "Patmos, Greece",
     "period": "NT", "refs": ["Revelation 1:9"]},
    {"name": "Philippi", "status": "located", "lat": 41.0136, "lon": 24.2862, "modern": "Filippoi, Greece (ruins)",
     "period": "NT", "refs": ["Acts 16:12", "Philippians 1:1"]},
    {"name": "Thessalonica", "status": "located", "lat": 40.6401, "lon": 22.9444, "modern": "Thessaloniki, Greece",
     "period": "NT", "refs": ["Acts 17:1", "1 Thessalonians 1:1"]},
    {"name": "Berea", "status": "located", "lat": 40.5236, "lon": 22.2028, "modern": "Veria, Greece",
     "period": "NT", "refs": ["Acts 17:10-11"]},
    {"name": "Athens", "status": "located", "lat": 37.9838, "lon": 23.7275, "modern": "Athens, Greece",
     "period": "NT", "refs": ["Acts 17:22-23", "Acts 17:34"]},
    {"name": "Corinth", "status": "located", "lat": 37.9058, "lon": 22.8797, "modern": "Archaia Korinthos, Greece",
     "period": "NT", "refs": ["Acts 18:1", "1 Corinthians 1:2"]},
    {"name": "Salamis (Cyprus)", "status": "located", "lat": 35.1833, "lon": 33.9000, "modern": "near Famagusta, Cyprus",
     "period": "NT", "refs": ["Acts 13:5"]},
    {"name": "Paphos", "status": "located", "lat": 34.7754, "lon": 32.4218, "modern": "Paphos, Cyprus",
     "period": "NT", "refs": ["Acts 13:6-12"]},
    {"name": "Malta (Melita)", "status": "located", "lat": 35.9375, "lon": 14.3754, "modern": "Malta",
     "period": "NT", "refs": ["Acts 28:1"]},
    {"name": "Rome", "status": "located", "lat": 41.8925, "lon": 12.4853, "modern": "Rome, Italy",
     "period": "NT", "refs": ["Acts 28:16", "Romans 1:7"]},
    # ── The honest blanks ─────────────────────────────────────────────────────────────────
    {"name": "Eden", "status": "unlocated", "period": "OT", "refs": ["Genesis 2:8", "Genesis 2:10-14"],
     "note": "Genesis names the Tigris and Euphrates among its four rivers; no identification is possible, and none is offered."},
    {"name": "Sodom and Gomorrah", "status": "unlocated", "period": "OT",
     "candidates": ["sites near the southern Dead Sea (Bab edh-Dhra among them)", "Tall el-Hammam northeast of the Dead Sea"],
     "refs": ["Genesis 19:24-25", "Deuteronomy 29:23"],
     "note": "Candidates are argued; none is established. Listed without a flag."},
    {"name": "Tarshish", "status": "unlocated", "period": "OT",
     "candidates": ["Tartessos in Spain", "Sardinia", "Tarsus in Cilicia"],
     "refs": ["Jonah 1:3", "1 Kings 10:22"]},
    {"name": "Ophir", "status": "unlocated", "period": "OT",
     "candidates": ["southwest Arabia", "the Horn of Africa", "India"],
     "refs": ["1 Kings 9:28", "Job 28:16"]},
]

NOTE = ("Real coordinates only where the identification is secure. A disputed place names its "
        "candidates instead of planting one flag; an unlocatable place is an honest blank. The "
        "curated coordinates are cross-checked against an independent gazetteer in the test suite "
        "— the map is verified, not asserted.")


def places() -> Dict[str, Any]:
    counts = {"located": 0, "disputed": 0, "unlocated": 0}
    for p in PLACES:
        counts[p["status"]] += 1
    return {"places": PLACES, "count": len(PLACES), "by_status": counts,
            "means": {"located": "secure identification — coordinates given",
                      "disputed": "real candidates named; coordinates only where one site has "
                                  "long-standing precedence, and marked as such",
                      "unlocated": "no coordinates — an honest blank beats a confident guess"},
            "note": NOTE}


def get(name: str) -> Optional[Dict[str, Any]]:
    key = (name or "").strip().lower()
    for p in PLACES:
        if p["name"].lower() == key:
            return p
    return None


__all__ = ["places", "get", "PLACES", "NOTE"]
