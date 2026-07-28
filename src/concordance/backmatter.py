"""Back-matter reference tables — the study helps at the back of a good Bible, served whole.

Contract §6 item 9: topical index, weights & measures, parables and miracles lists, book
introductions, names of God. Same invariants as the Harmony and the Timeline:

  * every entry carries REFS a reader can open and check — the table points at Scripture, it never
    replaces it;
  * where scholarship genuinely disagrees (the length of a cubit, the weight of a talent, the date
    of Revelation, the author of Hebrews) BOTH positions are carried, never one flattened verdict —
    "we live in the nuance";
  * names of God carry their Strong's numbers, so every name opens into the real lexicon entry and
    its occurrences — the plumb-line, not our paraphrase;
  * nothing generated at answer time: these are curated tables of long-established reference facts,
    the kind printed in the back of study Bibles for a century, with the disputes restored.

Witness-gated like /harmony and /timeline: this is Bible study material and lives behind the same
door on the secular surface.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── Weights & measures ──────────────────────────────────────────────────────────────────────────
# Modern equivalents are approximations; where the systems genuinely differ (common vs royal cubit,
# light vs heavy talent) both are given. Money entries note that ancient values were weights of
# metal, not coins with a fixed exchange rate — a modern currency figure would be a false precision.
WEIGHTS_MEASURES: List[Dict[str, Any]] = [
    {"name": "Cubit", "category": "length", "hebrew": "אַמָּה (ammah)", "strongs": "H520",
     "equivalent": "common cubit ≈ 17.5 in / 44.5 cm; royal (long) cubit ≈ 20.6 in / 52.3 cm",
     "disputed": "Two systems attested; Ezekiel 40:5 names a cubit 'of a cubit and a handbreadth' — the long cubit.",
     "refs": ["Genesis 6:15", "Ezekiel 40:5", "2 Chronicles 3:3"]},
    {"name": "Span", "category": "length", "hebrew": "זֶרֶת (zeret)", "strongs": "H2239",
     "equivalent": "≈ half a cubit; ≈ 9 in / 23 cm", "refs": ["Exodus 28:16", "1 Samuel 17:4"]},
    {"name": "Handbreadth", "category": "length", "hebrew": "טֶפַח (tephach)", "strongs": "H2947",
     "equivalent": "≈ 3 in / 7.4 cm", "refs": ["Exodus 25:25", "Psalm 39:5"]},
    {"name": "Fathom", "category": "length", "greek": "ὀργυιά (orguia)", "strongs": "G3712",
     "equivalent": "≈ 6 ft / 1.8 m", "refs": ["Acts 27:28"]},
    {"name": "Furlong (stadion)", "category": "length", "greek": "στάδιον (stadion)", "strongs": "G4712",
     "equivalent": "≈ 607 ft / 185 m", "refs": ["Luke 24:13", "Revelation 21:16", "John 6:19"]},
    {"name": "Mile", "category": "length", "greek": "μίλιον (milion)", "strongs": "G3400",
     "equivalent": "Roman mile ≈ 4,854 ft / 1,479 m", "refs": ["Matthew 5:41"]},
    {"name": "Sabbath day's journey", "category": "length",
     "equivalent": "≈ 2,000 cubits ≈ 0.57 mi / 0.9 km (rabbinic limit, not a biblical statute)",
     "refs": ["Acts 1:12"]},
    {"name": "Reed", "category": "length", "hebrew": "קָנֶה (qaneh)", "strongs": "H7070",
     "equivalent": "6 long cubits ≈ 10.3 ft / 3.1 m", "refs": ["Ezekiel 40:5", "Revelation 21:15"]},
    {"name": "Talent", "category": "weight", "hebrew": "כִּכָּר (kikkar)", "strongs": "H3603",
     "equivalent": "≈ 75 lb / 34 kg (common); a 'heavy' or double standard ≈ 150 lb / 68 kg is also attested",
     "disputed": "Weight standards varied by era and region; both light and heavy talents appear in the ancient Near East.",
     "refs": ["Exodus 38:27", "2 Samuel 12:30", "Matthew 25:15"]},
    {"name": "Mina (maneh)", "category": "weight", "hebrew": "מָנֶה (maneh)", "strongs": "H4488",
     "equivalent": "50 shekels ≈ 1.25 lb / 0.57 kg (Ezekiel 45:12 defines it as 60 shekels — the standards differ)",
     "disputed": "50-shekel and 60-shekel minas are both attested; Ezekiel's is explicit.",
     "refs": ["Ezekiel 45:12", "1 Kings 10:17", "Luke 19:13"]},
    {"name": "Shekel", "category": "weight", "hebrew": "שֶׁקֶל (sheqel)", "strongs": "H8255",
     "equivalent": "≈ 0.4 oz / 11.4 g; also the everyday unit of silver money by weight",
     "refs": ["Genesis 23:15", "Exodus 30:13", "2 Samuel 14:26"]},
    {"name": "Gerah", "category": "weight", "hebrew": "גֵּרָה (gerah)", "strongs": "H1626",
     "equivalent": "1/20 shekel ≈ 0.57 g", "refs": ["Exodus 30:13", "Leviticus 27:25"]},
    {"name": "Beka", "category": "weight", "hebrew": "בֶּקַע (beqa)", "strongs": "H1235",
     "equivalent": "half a shekel ≈ 5.7 g", "refs": ["Exodus 38:26", "Genesis 24:22"]},
    {"name": "Ephah", "category": "dry measure", "hebrew": "אֵיפָה (ephah)", "strongs": "H374",
     "equivalent": "≈ 22 L / 3/5 bushel (estimates range ≈ 20–24 L)",
     "refs": ["Exodus 16:36", "Ruth 2:17", "Amos 8:5"]},
    {"name": "Omer", "category": "dry measure", "hebrew": "עֹמֶר (omer)", "strongs": "H6016",
     "equivalent": "1/10 ephah ≈ 2.2 L", "refs": ["Exodus 16:16", "Exodus 16:36"]},
    {"name": "Seah", "category": "dry measure", "hebrew": "סְאָה (seah)", "strongs": "H5429",
     "equivalent": "1/3 ephah ≈ 7.3 L", "refs": ["Genesis 18:6", "1 Samuel 25:18"]},
    {"name": "Homer / Cor", "category": "dry measure", "hebrew": "חֹמֶר (chomer) / כֹּר (kor)", "strongs": "H2563",
     "equivalent": "10 ephahs ≈ 220 L", "refs": ["Leviticus 27:16", "Ezekiel 45:14", "Hosea 3:2"]},
    {"name": "Cab", "category": "dry measure", "hebrew": "קַב (qab)", "strongs": "H6894",
     "equivalent": "≈ 1.2 L", "refs": ["2 Kings 6:25"]},
    {"name": "Lethech", "category": "dry measure", "hebrew": "לֶתֶךְ (lethek)", "strongs": "H3963",
     "equivalent": "half a homer ≈ 110 L", "refs": ["Hosea 3:2"]},
    {"name": "Bath", "category": "liquid measure", "hebrew": "בַּת (bath)", "strongs": "H1324",
     "equivalent": "≈ 22 L / 5.8 US gal — the liquid equal of the ephah",
     "refs": ["1 Kings 7:26", "Ezekiel 45:11", "Isaiah 5:10"]},
    {"name": "Hin", "category": "liquid measure", "hebrew": "הִין (hin)", "strongs": "H1969",
     "equivalent": "1/6 bath ≈ 3.7 L", "refs": ["Exodus 29:40", "Numbers 15:4"]},
    {"name": "Log", "category": "liquid measure", "hebrew": "לֹג (log)", "strongs": "H3849",
     "equivalent": "1/12 hin ≈ 0.3 L", "refs": ["Leviticus 14:10"]},
    {"name": "Firkin (metretes)", "category": "liquid measure", "greek": "μετρητής (metretes)", "strongs": "G3355",
     "equivalent": "≈ 39 L / 10 US gal", "refs": ["John 2:6"]},
    {"name": "Denarius", "category": "money", "greek": "δηνάριον (denarion)", "strongs": "G1220",
     "equivalent": "a day's wage for a labourer (Matthew 20:2) — the honest anchor; no fixed modern price",
     "refs": ["Matthew 20:2", "Matthew 22:19", "Luke 10:35"]},
    {"name": "Drachma", "category": "money", "greek": "δραχμή (drachme)", "strongs": "G1406",
     "equivalent": "Greek silver coin ≈ a denarius", "refs": ["Luke 15:8"]},
    {"name": "Didrachma (temple tax)", "category": "money", "greek": "δίδραχμον (didrachmon)", "strongs": "G1323",
     "equivalent": "two drachmas — the half-shekel temple tax", "refs": ["Matthew 17:24", "Exodus 30:13"]},
    {"name": "Stater", "category": "money", "greek": "στατήρ (stater)", "strongs": "G4715",
     "equivalent": "four drachmas — exactly the temple tax for two", "refs": ["Matthew 17:27"]},
    {"name": "Mite (lepton)", "category": "money", "greek": "λεπτόν (lepton)", "strongs": "G3016",
     "equivalent": "the smallest coin in circulation; 1/128 of a denarius",
     "refs": ["Mark 12:42", "Luke 21:2"]},
    {"name": "Quadrans (farthing)", "category": "money", "greek": "κοδράντης (kodrantes)", "strongs": "G2835",
     "equivalent": "two lepta; 1/64 of a denarius", "refs": ["Mark 12:42", "Matthew 5:26"]},
    {"name": "Piece of silver (30 pieces)", "category": "money", "hebrew": "כֶּסֶף (keseph)", "strongs": "H3701",
     "equivalent": "30 shekels of silver — the compensation price of a slave (Exodus 21:32)",
     "refs": ["Zechariah 11:12", "Matthew 26:15", "Exodus 21:32"]},
    {"name": "Watch (of the night)", "category": "time",
     "equivalent": "OT: three watches; NT (Roman): four watches (evening, midnight, cockcrow, morning — Mark 13:35)",
     "refs": ["Judges 7:19", "Mark 13:35", "Matthew 14:25"]},
    {"name": "Hour", "category": "time", "greek": "ὥρα (hora)", "strongs": "G5610",
     "equivalent": "1/12 of daylight — its length varied with the season; the 'third hour' ≈ mid-morning",
     "refs": ["Matthew 20:3", "John 11:9", "Acts 2:15"]},
]

# ── Names of God ────────────────────────────────────────────────────────────────────────────────
# Each name carries its Strong's number where one exists, so the entry opens into the real lexicon
# and every occurrence — the reader checks us, not the other way round.
NAMES_OF_GOD: List[Dict[str, Any]] = [
    {"name": "Elohim", "meaning": "God — the Mighty One (plural of majesty)", "strongs": "H430",
     "first_ref": "Genesis 1:1", "refs": ["Genesis 1:1", "Psalm 19:1", "Deuteronomy 10:17"]},
    {"name": "YHWH (the LORD)", "meaning": "the covenant Name — HE IS; rendered LORD in small capitals", "strongs": "H3068",
     "first_ref": "Genesis 2:4", "refs": ["Exodus 3:15", "Exodus 34:6", "Psalm 23:1"],
     "note": "Pronunciation not preserved; 'Yahweh' is the common scholarly reconstruction, 'Jehovah' the older hybrid form. Both traditions are carried, neither settled."},
    {"name": "Adonai", "meaning": "Lord, Master", "strongs": "H136",
     "first_ref": "Genesis 15:2", "refs": ["Genesis 15:2", "Psalm 110:1", "Isaiah 6:1"]},
    {"name": "El Shaddai", "meaning": "God Almighty", "strongs": "H7706",
     "first_ref": "Genesis 17:1", "refs": ["Genesis 17:1", "Genesis 49:25", "Job 5:17"]},
    {"name": "El Elyon", "meaning": "God Most High", "strongs": "H5945",
     "first_ref": "Genesis 14:18", "refs": ["Genesis 14:18-20", "Psalm 78:35", "Daniel 4:34"]},
    {"name": "El Olam", "meaning": "the Everlasting God", "strongs": "H5769",
     "first_ref": "Genesis 21:33", "refs": ["Genesis 21:33", "Isaiah 40:28"]},
    {"name": "El Roi", "meaning": "the God who sees me", "strongs": "H7210",
     "first_ref": "Genesis 16:13", "refs": ["Genesis 16:13"]},
    {"name": "I AM (Ehyeh)", "meaning": "I AM WHO I AM — the Name declared to Moses", "strongs": "H1961",
     "first_ref": "Exodus 3:14", "refs": ["Exodus 3:14", "John 8:58"]},
    {"name": "YHWH-Jireh", "meaning": "the LORD will provide", "strongs": "H3070",
     "first_ref": "Genesis 22:14", "refs": ["Genesis 22:14"]},
    {"name": "YHWH-Rapha", "meaning": "the LORD who heals you", "strongs": "H7495",
     "first_ref": "Exodus 15:26", "refs": ["Exodus 15:26"]},
    {"name": "YHWH-Nissi", "meaning": "the LORD is my banner", "strongs": "H3071",
     "first_ref": "Exodus 17:15", "refs": ["Exodus 17:15"]},
    {"name": "YHWH-Mekaddishkem", "meaning": "the LORD who sanctifies you", "strongs": "H6942",
     "first_ref": "Exodus 31:13", "refs": ["Exodus 31:13", "Leviticus 20:8"]},
    {"name": "YHWH-Shalom", "meaning": "the LORD is peace", "strongs": "H3073",
     "first_ref": "Judges 6:24", "refs": ["Judges 6:24"]},
    {"name": "YHWH-Sabaoth", "meaning": "the LORD of hosts (armies)", "strongs": "H6635",
     "first_ref": "1 Samuel 1:3", "refs": ["1 Samuel 1:3", "Psalm 46:7", "Isaiah 6:3"]},
    {"name": "YHWH-Tsidkenu", "meaning": "the LORD our righteousness", "strongs": "H3072",
     "first_ref": "Jeremiah 23:6", "refs": ["Jeremiah 23:6", "Jeremiah 33:16"]},
    {"name": "YHWH-Shammah", "meaning": "the LORD is there", "strongs": "H3074",
     "first_ref": "Ezekiel 48:35", "refs": ["Ezekiel 48:35"]},
    {"name": "YHWH-Rohi", "meaning": "the LORD is my shepherd", "strongs": "H7462",
     "first_ref": "Psalm 23:1", "refs": ["Psalm 23:1", "Ezekiel 34:11-12"]},
    {"name": "Ancient of Days", "meaning": "the eternal Judge enthroned", "strongs": "H6268",
     "first_ref": "Daniel 7:9", "refs": ["Daniel 7:9", "Daniel 7:13", "Daniel 7:22"]},
    {"name": "Immanuel", "meaning": "God with us", "strongs": "H6005",
     "first_ref": "Isaiah 7:14", "refs": ["Isaiah 7:14", "Matthew 1:23"]},
    {"name": "Father", "meaning": "the Father of Israel and, in Christ, of believers", "strongs": "G3962",
     "first_ref": "Deuteronomy 32:6", "refs": ["Deuteronomy 32:6", "Isaiah 64:8", "Matthew 6:9"]},
    {"name": "Theos", "meaning": "God (Greek)", "strongs": "G2316",
     "first_ref": "Matthew 1:23", "refs": ["John 1:1", "John 3:16", "Romans 8:31"]},
    {"name": "Kyrios", "meaning": "Lord (Greek) — the Septuagint's rendering of YHWH, confessed of Jesus", "strongs": "G2962",
     "first_ref": "Matthew 1:20", "refs": ["Romans 10:9", "Philippians 2:11", "Acts 2:36"]},
    {"name": "Logos", "meaning": "the Word — who was with God and was God, and became flesh", "strongs": "G3056",
     "first_ref": "John 1:1", "refs": ["John 1:1", "John 1:14", "Revelation 19:13"]},
    {"name": "Alpha and Omega", "meaning": "the first and the last, the beginning and the end", "strongs": "G1",
     "first_ref": "Revelation 1:8", "refs": ["Revelation 1:8", "Revelation 21:6", "Revelation 22:13"]},
    {"name": "Messiah / Christ", "meaning": "the Anointed One", "strongs": "G5547",
     "first_ref": "Daniel 9:25", "refs": ["Daniel 9:25", "John 1:41", "Matthew 16:16"],
     "note": "Hebrew mashiach (H4899) and Greek Christos (G5547) are one title — both lexicon entries apply."},
    {"name": "Son of Man", "meaning": "Daniel's figure given everlasting dominion; Jesus' chosen self-title", "strongs": "G5207",
     "first_ref": "Daniel 7:13", "refs": ["Daniel 7:13-14", "Mark 10:45", "Matthew 26:64"]},
    {"name": "Lamb of God", "meaning": "the sacrifice who takes away the sin of the world", "strongs": "G286",
     "first_ref": "John 1:29", "refs": ["John 1:29", "Revelation 5:6", "Isaiah 53:7"]},
    {"name": "Good Shepherd", "meaning": "the shepherd who lays down his life for the sheep", "strongs": "G4166",
     "first_ref": "John 10:11", "refs": ["John 10:11", "Psalm 23:1", "1 Peter 5:4"]},
    {"name": "King of Kings and Lord of Lords", "meaning": "sovereign over every throne", "strongs": "G935",
     "first_ref": "1 Timothy 6:15", "refs": ["1 Timothy 6:15", "Revelation 19:16", "Revelation 17:14"]},
    {"name": "Almighty (Pantokrator)", "meaning": "the All-Ruler", "strongs": "G3841",
     "first_ref": "2 Corinthians 6:18", "refs": ["Revelation 1:8", "Revelation 4:8"]},
]

# ── The parables of Jesus ───────────────────────────────────────────────────────────────────────
# Synoptic parallels side by side, like the Harmony: one parable, every gospel that carries it.
# John's gospel has figures (the Shepherd, the Vine) rather than narrative parables — listed at the
# end under their own flag rather than silently mixed in or silently dropped.
PARABLES: List[Dict[str, Any]] = [
    {"name": "The sower", "matthew": "Matthew 13:3-9", "mark": "Mark 4:3-9", "luke": "Luke 8:5-8", "theme": "hearing the word"},
    {"name": "The lamp under a basket", "matthew": "Matthew 5:14-16", "mark": "Mark 4:21-22", "luke": "Luke 8:16-17", "theme": "witness"},
    {"name": "The wheat and the tares", "matthew": "Matthew 13:24-30", "theme": "patience until the harvest"},
    {"name": "The mustard seed", "matthew": "Matthew 13:31-32", "mark": "Mark 4:30-32", "luke": "Luke 13:18-19", "theme": "the kingdom's growth"},
    {"name": "The leaven", "matthew": "Matthew 13:33", "luke": "Luke 13:20-21", "theme": "the kingdom's working"},
    {"name": "The hidden treasure", "matthew": "Matthew 13:44", "theme": "the kingdom's worth"},
    {"name": "The pearl of great price", "matthew": "Matthew 13:45-46", "theme": "the kingdom's worth"},
    {"name": "The net", "matthew": "Matthew 13:47-50", "theme": "the final sorting"},
    {"name": "The seed growing secretly", "mark": "Mark 4:26-29", "theme": "God gives the growth"},
    {"name": "The unmerciful servant", "matthew": "Matthew 18:23-35", "theme": "forgiveness"},
    {"name": "The good Samaritan", "luke": "Luke 10:30-37", "theme": "who is my neighbour"},
    {"name": "The friend at midnight", "luke": "Luke 11:5-8", "theme": "persistence in prayer"},
    {"name": "The rich fool", "luke": "Luke 12:16-21", "theme": "treasure toward God"},
    {"name": "The watchful servants", "mark": "Mark 13:34-37", "luke": "Luke 12:35-40", "theme": "readiness"},
    {"name": "The faithful and wise steward", "matthew": "Matthew 24:45-51", "luke": "Luke 12:42-48", "theme": "stewardship"},
    {"name": "The barren fig tree", "luke": "Luke 13:6-9", "theme": "repentance while there is time"},
    {"name": "The great banquet", "luke": "Luke 14:16-24", "theme": "the invitation refused and widened"},
    {"name": "The wedding feast", "matthew": "Matthew 22:2-14", "theme": "the invitation and the garment"},
    {"name": "Counting the cost (tower and war)", "luke": "Luke 14:28-33", "theme": "discipleship"},
    {"name": "The lost sheep", "matthew": "Matthew 18:12-14", "luke": "Luke 15:4-7", "theme": "the seeking God"},
    {"name": "The lost coin", "luke": "Luke 15:8-10", "theme": "the seeking God"},
    {"name": "The prodigal son", "luke": "Luke 15:11-32", "theme": "the father's welcome"},
    {"name": "The shrewd manager", "luke": "Luke 16:1-9", "theme": "faithfulness with wealth"},
    {"name": "The rich man and Lazarus", "luke": "Luke 16:19-31", "theme": "the great reversal"},
    {"name": "Unprofitable servants", "luke": "Luke 17:7-10", "theme": "duty and grace"},
    {"name": "The persistent widow", "luke": "Luke 18:1-8", "theme": "always pray, never give up"},
    {"name": "The Pharisee and the tax collector", "luke": "Luke 18:9-14", "theme": "justified humility"},
    {"name": "The labourers in the vineyard", "matthew": "Matthew 20:1-16", "theme": "the generosity of the master"},
    {"name": "The minas", "luke": "Luke 19:12-27", "theme": "occupy till he comes"},
    {"name": "The talents", "matthew": "Matthew 25:14-30", "theme": "entrusted much"},
    {"name": "The two sons", "matthew": "Matthew 21:28-32", "theme": "doing the father's will"},
    {"name": "The wicked tenants", "matthew": "Matthew 21:33-44", "mark": "Mark 12:1-11", "luke": "Luke 20:9-18", "theme": "the rejected son"},
    {"name": "The budding fig tree", "matthew": "Matthew 24:32-35", "mark": "Mark 13:28-31", "luke": "Luke 21:29-33", "theme": "reading the season"},
    {"name": "The ten virgins", "matthew": "Matthew 25:1-13", "theme": "watchfulness"},
    {"name": "The sheep and the goats", "matthew": "Matthew 25:31-46", "theme": "the least of these"},
    {"name": "The two builders", "matthew": "Matthew 7:24-27", "luke": "Luke 6:47-49", "theme": "hearing and doing"},
    {"name": "The two debtors", "luke": "Luke 7:41-43", "theme": "loving much, forgiven much"},
    {"name": "New cloth, new wineskins", "matthew": "Matthew 9:16-17", "mark": "Mark 2:21-22", "luke": "Luke 5:36-39", "theme": "the new covenant"},
    {"name": "The good shepherd (figure)", "john": "John 10:1-18", "theme": "the shepherd who lays down his life", "figure": True},
    {"name": "The vine and the branches (figure)", "john": "John 15:1-8", "theme": "abiding", "figure": True},
]

# ── The miracles of Jesus ───────────────────────────────────────────────────────────────────────
MIRACLES: List[Dict[str, Any]] = [
    {"name": "Water into wine", "john": "John 2:1-11", "category": "nature"},
    {"name": "The official's son healed", "john": "John 4:46-54", "category": "healing"},
    {"name": "The miraculous catch of fish", "luke": "Luke 5:1-11", "category": "nature"},
    {"name": "The demoniac in the synagogue", "mark": "Mark 1:23-26", "luke": "Luke 4:33-35", "category": "deliverance"},
    {"name": "Peter's mother-in-law healed", "matthew": "Matthew 8:14-15", "mark": "Mark 1:30-31", "luke": "Luke 4:38-39", "category": "healing"},
    {"name": "The leper cleansed", "matthew": "Matthew 8:2-4", "mark": "Mark 1:40-42", "luke": "Luke 5:12-13", "category": "healing"},
    {"name": "The paralytic through the roof", "matthew": "Matthew 9:2-7", "mark": "Mark 2:3-12", "luke": "Luke 5:18-25", "category": "healing"},
    {"name": "The invalid at Bethesda", "john": "John 5:1-9", "category": "healing"},
    {"name": "The withered hand", "matthew": "Matthew 12:10-13", "mark": "Mark 3:1-5", "luke": "Luke 6:6-10", "category": "healing"},
    {"name": "The centurion's servant", "matthew": "Matthew 8:5-13", "luke": "Luke 7:1-10", "category": "healing"},
    {"name": "The widow of Nain's son raised", "luke": "Luke 7:11-15", "category": "raising the dead"},
    {"name": "The storm stilled", "matthew": "Matthew 8:23-27", "mark": "Mark 4:37-41", "luke": "Luke 8:22-25", "category": "nature"},
    {"name": "The Gadarene demoniacs", "matthew": "Matthew 8:28-34", "mark": "Mark 5:1-15", "luke": "Luke 8:27-35", "category": "deliverance"},
    {"name": "Jairus's daughter raised", "matthew": "Matthew 9:18-26", "mark": "Mark 5:22-43", "luke": "Luke 8:41-56", "category": "raising the dead"},
    {"name": "The woman with the issue of blood", "matthew": "Matthew 9:20-22", "mark": "Mark 5:25-34", "luke": "Luke 8:43-48", "category": "healing"},
    {"name": "Two blind men healed", "matthew": "Matthew 9:27-31", "category": "healing"},
    {"name": "The mute demoniac", "matthew": "Matthew 9:32-33", "category": "deliverance"},
    {"name": "Five thousand fed", "matthew": "Matthew 14:15-21", "mark": "Mark 6:35-44", "luke": "Luke 9:12-17", "john": "John 6:5-13", "category": "nature",
     "note": "The only miracle before the resurrection carried by all four gospels."},
    {"name": "Walking on the sea", "matthew": "Matthew 14:25-33", "mark": "Mark 6:48-51", "john": "John 6:19-21", "category": "nature"},
    {"name": "The Syrophoenician woman's daughter", "matthew": "Matthew 15:21-28", "mark": "Mark 7:24-30", "category": "deliverance"},
    {"name": "The deaf and mute man", "mark": "Mark 7:31-37", "category": "healing"},
    {"name": "Four thousand fed", "matthew": "Matthew 15:32-38", "mark": "Mark 8:1-9", "category": "nature"},
    {"name": "The blind man at Bethsaida", "mark": "Mark 8:22-26", "category": "healing"},
    {"name": "The man born blind", "john": "John 9:1-7", "category": "healing"},
    {"name": "The boy with a demon", "matthew": "Matthew 17:14-18", "mark": "Mark 9:17-27", "luke": "Luke 9:38-42", "category": "deliverance"},
    {"name": "The coin in the fish's mouth", "matthew": "Matthew 17:24-27", "category": "nature"},
    {"name": "The bent-over woman", "luke": "Luke 13:11-13", "category": "healing"},
    {"name": "The man with dropsy", "luke": "Luke 14:1-4", "category": "healing"},
    {"name": "Ten lepers cleansed", "luke": "Luke 17:11-19", "category": "healing"},
    {"name": "Lazarus raised", "john": "John 11:38-44", "category": "raising the dead"},
    {"name": "Blind Bartimaeus (and companion)", "matthew": "Matthew 20:29-34", "mark": "Mark 10:46-52", "luke": "Luke 18:35-43", "category": "healing",
     "note": "Matthew records two blind men; Mark and Luke name one, Bartimaeus. Both accounts carried."},
    {"name": "The fig tree withered", "matthew": "Matthew 21:18-22", "mark": "Mark 11:12-24", "category": "nature"},
    {"name": "Malchus's ear healed", "luke": "Luke 22:50-51", "category": "healing"},
    {"name": "The second catch of fish", "john": "John 21:1-11", "category": "nature"},
]

# ── Book introductions ──────────────────────────────────────────────────────────────────────────
# One line of orientation per book: traditional authorship WITH the honest dispute flag where real
# scholarship genuinely divides, a working date range (never one flattened year where systems
# disagree), the theme, and one key verse to open first.
BOOK_INTROS: List[Dict[str, Any]] = [
    {"book": "Genesis", "author": "traditionally Moses; sources and composition debated in modern scholarship", "date": "events from creation; composition traditionally 15th-13th c. BC", "theme": "beginnings — creation, fall, flood, covenant with Abraham", "key_verse": "Genesis 1:1"},
    {"book": "Exodus", "author": "traditionally Moses", "date": "exodus dated c. 1446 BC (early) or c. 1270 BC (late) — both systems carried", "theme": "redemption out of Egypt; the covenant and the dwelling of God", "key_verse": "Exodus 3:14"},
    {"book": "Leviticus", "author": "traditionally Moses", "date": "wilderness period", "theme": "holiness — atonement, priesthood, clean and unclean", "key_verse": "Leviticus 19:2"},
    {"book": "Numbers", "author": "traditionally Moses", "date": "wilderness period", "theme": "the wilderness generation — unbelief and God's faithfulness", "key_verse": "Numbers 6:24-26"},
    {"book": "Deuteronomy", "author": "traditionally Moses (his death recorded by another hand)", "date": "plains of Moab, end of the wilderness years", "theme": "covenant renewed — hear, love, obey", "key_verse": "Deuteronomy 6:4-5"},
    {"book": "Joshua", "author": "traditionally Joshua; final form later", "date": "conquest period", "theme": "the land received — not one promise failed", "key_verse": "Joshua 1:9"},
    {"book": "Judges", "author": "unknown; tradition names Samuel", "date": "conquest to the rise of the monarchy", "theme": "everyone did what was right in his own eyes", "key_verse": "Judges 21:25"},
    {"book": "Ruth", "author": "unknown", "date": "days of the judges; written later", "theme": "the kinsman-redeemer — loyal love in dark days", "key_verse": "Ruth 1:16"},
    {"book": "1 Samuel", "author": "unknown; Samuel-Nathan-Gad tradition (1 Chronicles 29:29)", "date": "c. 1050-1010 BC events", "theme": "the kingdom asked for — Saul rises and falls, David anointed", "key_verse": "1 Samuel 16:7"},
    {"book": "2 Samuel", "author": "unknown; same tradition as 1 Samuel", "date": "c. 1010-970 BC events", "theme": "David's reign — covenant, sin, and consequence", "key_verse": "2 Samuel 7:16"},
    {"book": "1 Kings", "author": "unknown; tradition names Jeremiah", "date": "Solomon to the divided kingdom", "theme": "the kingdom divided — prophets against idolatry", "key_verse": "1 Kings 18:21"},
    {"book": "2 Kings", "author": "unknown; continuous with 1 Kings", "date": "to the falls of Samaria (722 BC) and Jerusalem (586 BC)", "theme": "the long descent into exile", "key_verse": "2 Kings 17:13-14"},
    {"book": "1 Chronicles", "author": "traditionally Ezra ('the Chronicler')", "date": "after the exile", "theme": "Israel's story retold for the returned community — David and worship", "key_verse": "1 Chronicles 29:11"},
    {"book": "2 Chronicles", "author": "the Chronicler", "date": "after the exile", "theme": "the temple, the kings of Judah, and the hope of restoration", "key_verse": "2 Chronicles 7:14"},
    {"book": "Ezra", "author": "traditionally Ezra", "date": "c. 458-440 BC", "theme": "return and rebuilding — the word restored", "key_verse": "Ezra 7:10"},
    {"book": "Nehemiah", "author": "Nehemiah's memoirs, compiled with Ezra tradition", "date": "c. 445-420 BC", "theme": "the wall rebuilt, the people re-covenanted", "key_verse": "Nehemiah 8:10"},
    {"book": "Esther", "author": "unknown", "date": "Persian period, c. 480-470 BC events", "theme": "providence unnamed — for such a time as this", "key_verse": "Esther 4:14"},
    {"book": "Job", "author": "unknown", "date": "setting patriarchal; composition date widely debated", "theme": "suffering and the God who answers out of the whirlwind", "key_verse": "Job 19:25"},
    {"book": "Psalms", "author": "David and many others (Asaph, Korah's sons, Moses, Solomon, anonymous)", "date": "collected over centuries", "theme": "the prayer book of the Bible — every register of the soul before God", "key_verse": "Psalm 23:1"},
    {"book": "Proverbs", "author": "chiefly Solomon; also Agur, Lemuel, 'the wise'", "date": "united monarchy onward; compiled later (Proverbs 25:1)", "theme": "wisdom — the fear of the LORD is the beginning", "key_verse": "Proverbs 9:10"},
    {"book": "Ecclesiastes", "author": "'Qoheleth, son of David' — traditionally Solomon; authorship debated", "date": "debated (monarchy to post-exilic)", "theme": "vanity under the sun; fear God and keep his commandments", "key_verse": "Ecclesiastes 12:13"},
    {"book": "Song of Solomon", "author": "attributed to Solomon", "date": "united monarchy (traditional)", "theme": "covenant love delighted in", "key_verse": "Song of Solomon 8:7"},
    {"book": "Isaiah", "author": "Isaiah son of Amoz; the book's unity vs. multiple-author composition is a genuine scholarly divide — both positions carried", "date": "ministry c. 740-681 BC", "theme": "the Holy One of Israel — judgment, comfort, and the Servant", "key_verse": "Isaiah 53:5"},
    {"book": "Jeremiah", "author": "Jeremiah, with Baruch the scribe", "date": "c. 627-580 BC", "theme": "the weeping prophet — exile and the new covenant", "key_verse": "Jeremiah 31:33"},
    {"book": "Lamentations", "author": "traditionally Jeremiah", "date": "after 586 BC", "theme": "grief over Jerusalem; mercies new every morning", "key_verse": "Lamentations 3:22-23"},
    {"book": "Ezekiel", "author": "Ezekiel the priest", "date": "exile, c. 593-571 BC", "theme": "the glory departs and returns — a new heart, a new spirit", "key_verse": "Ezekiel 36:26"},
    {"book": "Daniel", "author": "Daniel; traditional 6th-c. dating and critical 2nd-c. dating are both long-standing positions, carried side by side", "date": "exile setting, c. 605-536 BC", "theme": "God rules the kingdoms of men", "key_verse": "Daniel 2:44"},
    {"book": "Hosea", "author": "Hosea", "date": "c. 755-715 BC", "theme": "faithless Israel, faithful Husband", "key_verse": "Hosea 6:6"},
    {"book": "Joel", "author": "Joel", "date": "widely debated — pre-exilic to post-exilic proposals", "theme": "the day of the LORD; the Spirit poured out", "key_verse": "Joel 2:28"},
    {"book": "Amos", "author": "Amos, herdsman of Tekoa", "date": "c. 760 BC", "theme": "let justice roll down like waters", "key_verse": "Amos 5:24"},
    {"book": "Obadiah", "author": "Obadiah", "date": "likely after 586 BC (debated)", "theme": "Edom judged; the kingdom is the LORD's", "key_verse": "Obadiah 1:15"},
    {"book": "Jonah", "author": "unnamed; about Jonah son of Amittai (2 Kings 14:25)", "date": "8th-c. setting", "theme": "mercy wider than the prophet wanted", "key_verse": "Jonah 4:11"},
    {"book": "Micah", "author": "Micah of Moresheth", "date": "c. 735-700 BC", "theme": "do justice, love mercy, walk humbly; Bethlehem's ruler foretold", "key_verse": "Micah 6:8"},
    {"book": "Nahum", "author": "Nahum", "date": "c. 663-612 BC", "theme": "Nineveh's fall — the LORD slow to anger, great in power", "key_verse": "Nahum 1:7"},
    {"book": "Habakkuk", "author": "Habakkuk", "date": "c. 609-598 BC", "theme": "the just shall live by his faith", "key_verse": "Habakkuk 2:4"},
    {"book": "Zephaniah", "author": "Zephaniah", "date": "c. 640-621 BC", "theme": "the day of the LORD; he rejoices over you with singing", "key_verse": "Zephaniah 3:17"},
    {"book": "Haggai", "author": "Haggai", "date": "520 BC (precisely dated)", "theme": "build the house — consider your ways", "key_verse": "Haggai 2:9"},
    {"book": "Zechariah", "author": "Zechariah", "date": "520-518 BC (chs. 1-8); chs. 9-14 undated", "theme": "visions of restoration; the King on a donkey, the pierced One", "key_verse": "Zechariah 9:9"},
    {"book": "Malachi", "author": "Malachi ('my messenger')", "date": "c. 430 BC", "theme": "the last word before the silence — the messenger to come", "key_verse": "Malachi 3:1"},
    {"book": "Matthew", "author": "traditionally Matthew (Levi) the apostle", "date": "c. AD 50-70 (debated)", "theme": "Jesus the Messiah, son of David — the kingdom of heaven", "key_verse": "Matthew 28:19-20"},
    {"book": "Mark", "author": "traditionally John Mark, from Peter's preaching", "date": "c. AD 50-70", "theme": "the Son of Man came to serve and to give his life", "key_verse": "Mark 10:45"},
    {"book": "Luke", "author": "Luke the physician, companion of Paul", "date": "c. AD 60-85 (debated)", "theme": "an orderly account — the Saviour of the lost", "key_verse": "Luke 19:10"},
    {"book": "John", "author": "traditionally John the apostle ('the disciple whom Jesus loved'); authorship discussed since antiquity", "date": "c. AD 85-95 (an earlier date is also argued)", "theme": "that you may believe — the Word made flesh", "key_verse": "John 20:31"},
    {"book": "Acts", "author": "Luke, volume two", "date": "c. AD 62-85 (debated)", "theme": "the gospel from Jerusalem to Rome by the Spirit", "key_verse": "Acts 1:8"},
    {"book": "Romans", "author": "Paul", "date": "c. AD 57", "theme": "the righteousness of God by faith", "key_verse": "Romans 1:16-17"},
    {"book": "1 Corinthians", "author": "Paul", "date": "c. AD 55", "theme": "the cross against division — love, gifts, resurrection", "key_verse": "1 Corinthians 13:13"},
    {"book": "2 Corinthians", "author": "Paul", "date": "c. AD 56", "theme": "strength in weakness — the ministry of reconciliation", "key_verse": "2 Corinthians 12:9"},
    {"book": "Galatians", "author": "Paul", "date": "c. AD 48-55 (early/late debated)", "theme": "justified by faith, not works of the law — stand in freedom", "key_verse": "Galatians 2:20"},
    {"book": "Ephesians", "author": "Paul (authorship affirmed traditionally; questioned by some moderns)", "date": "c. AD 60-62", "theme": "the church, Christ's body — grace, unity, armor", "key_verse": "Ephesians 2:8-9"},
    {"book": "Philippians", "author": "Paul", "date": "c. AD 61-62", "theme": "joy in Christ from a prison cell", "key_verse": "Philippians 4:13"},
    {"book": "Colossians", "author": "Paul (with the same modern discussion as Ephesians)", "date": "c. AD 60-62", "theme": "Christ preeminent — in him all things hold together", "key_verse": "Colossians 1:17"},
    {"book": "1 Thessalonians", "author": "Paul", "date": "c. AD 50-51 — among the earliest NT documents", "theme": "holy living and the hope of his coming", "key_verse": "1 Thessalonians 4:16-17"},
    {"book": "2 Thessalonians", "author": "Paul (questioned by some moderns)", "date": "c. AD 51-52", "theme": "stand firm — the day of the Lord not yet", "key_verse": "2 Thessalonians 3:3"},
    {"book": "1 Timothy", "author": "Paul (the Pastorals' authorship is a real modern debate; the tradition is unbroken)", "date": "c. AD 62-66", "theme": "order and godliness in God's household", "key_verse": "1 Timothy 1:15"},
    {"book": "2 Timothy", "author": "Paul — his last letter by tradition", "date": "c. AD 66-67", "theme": "guard the deposit; finish the course", "key_verse": "2 Timothy 3:16-17"},
    {"book": "Titus", "author": "Paul", "date": "c. AD 62-66", "theme": "sound doctrine adorned by good works", "key_verse": "Titus 3:5"},
    {"book": "Philemon", "author": "Paul", "date": "c. AD 60-62", "theme": "a slave received as a brother", "key_verse": "Philemon 1:16"},
    {"book": "Hebrews", "author": "unknown — 'God alone knows' (Origen); Paul, Apollos, Barnabas and others proposed, none settled", "date": "before AD 70 (the temple stands in its argument)", "theme": "Christ better than all — the once-for-all sacrifice", "key_verse": "Hebrews 4:15-16"},
    {"book": "James", "author": "James, the Lord's brother (traditional)", "date": "c. AD 45-62 — possibly the earliest NT book", "theme": "faith that works", "key_verse": "James 1:22"},
    {"book": "1 Peter", "author": "Peter, through Silvanus", "date": "c. AD 62-64", "theme": "hope for exiles under fire", "key_verse": "1 Peter 5:7"},
    {"book": "2 Peter", "author": "Peter (the most-questioned NT attribution since antiquity; carried with its dispute)", "date": "c. AD 64-68 (traditional)", "theme": "remember — grow in grace; the day will come", "key_verse": "2 Peter 3:9"},
    {"book": "1 John", "author": "traditionally John the apostle", "date": "c. AD 85-95", "theme": "God is light, God is love — that you may know", "key_verse": "1 John 1:9"},
    {"book": "2 John", "author": "'the elder' — traditionally John", "date": "c. AD 85-95", "theme": "walk in truth and love; test the teachers", "key_verse": "2 John 1:6"},
    {"book": "3 John", "author": "'the elder' — traditionally John", "date": "c. AD 85-95", "theme": "hospitality to the truth's workers", "key_verse": "3 John 1:4"},
    {"book": "Jude", "author": "Jude, brother of James (traditional)", "date": "c. AD 65-80", "theme": "contend for the faith once delivered", "key_verse": "Jude 1:24-25"},
    {"book": "Revelation", "author": "John, on Patmos — apostle by tradition; 'John the elder' also argued since antiquity", "date": "c. AD 95 (Domitian) or c. AD 65-68 (Nero) — both datings are long-standing and carried side by side", "theme": "the Lamb wins — every tear wiped away", "key_verse": "Revelation 21:4"},
]

# ── Topical index ───────────────────────────────────────────────────────────────────────────────
# Where to start reading on a subject — a door into Scripture, not a substitute for it. Refs are
# starting points, deliberately few; /search and /cross_refs carry the reader deeper.
TOPICAL_INDEX: List[Dict[str, Any]] = [
    {"topic": "Faith", "refs": ["Hebrews 11:1", "Romans 10:17", "Habakkuk 2:4", "Ephesians 2:8-9", "James 2:17"], "related": ["Faith and works", "Hope"]},
    {"topic": "Hope", "refs": ["Romans 15:13", "Hebrews 6:19", "Lamentations 3:21-23", "1 Peter 1:3", "Romans 8:24-25"], "related": ["Faith", "Perseverance"]},
    {"topic": "Love", "refs": ["1 Corinthians 13:4-7", "John 3:16", "1 John 4:7-8", "Deuteronomy 6:5", "John 13:34-35"], "related": ["Mercy", "Forgiveness"]},
    {"topic": "Prayer", "refs": ["Matthew 6:9-13", "Philippians 4:6-7", "1 Thessalonians 5:17", "James 5:16", "Luke 18:1"], "related": ["Thanksgiving", "Worship"]},
    {"topic": "Forgiveness", "refs": ["Matthew 6:14-15", "Ephesians 4:32", "Psalm 103:12", "1 John 1:9", "Matthew 18:21-22"], "related": ["Mercy", "Repentance"]},
    {"topic": "Salvation", "refs": ["John 3:16-17", "Romans 10:9-10", "Ephesians 2:8-9", "Acts 4:12", "Titus 3:5"], "related": ["Grace", "Repentance"]},
    {"topic": "Grace", "refs": ["Ephesians 2:8-9", "2 Corinthians 12:9", "Romans 5:20", "Titus 2:11", "John 1:16-17"], "related": ["Salvation", "Mercy"]},
    {"topic": "Sin", "refs": ["Romans 3:23", "Romans 6:23", "1 John 1:8-9", "Genesis 4:7", "Psalm 51:1-4"], "related": ["Repentance", "Forgiveness"]},
    {"topic": "Repentance", "refs": ["Acts 3:19", "Luke 15:7", "2 Chronicles 7:14", "Psalm 51:17", "2 Peter 3:9"], "related": ["Sin", "Salvation"]},
    {"topic": "The Holy Spirit", "refs": ["John 14:26", "Acts 1:8", "Romans 8:26", "Galatians 5:22-23", "1 Corinthians 6:19"], "related": ["Fruit of the Spirit", "Spiritual gifts"]},
    {"topic": "Wisdom", "refs": ["Proverbs 9:10", "James 1:5", "Proverbs 3:5-6", "1 Corinthians 1:25", "Colossians 2:2-3"], "related": ["Fear of the LORD", "Guidance"]},
    {"topic": "Fear of the LORD", "refs": ["Proverbs 1:7", "Proverbs 9:10", "Psalm 111:10", "Ecclesiastes 12:13", "Deuteronomy 10:12"], "related": ["Wisdom"]},
    {"topic": "Anxiety and worry", "refs": ["Philippians 4:6-7", "Matthew 6:25-34", "1 Peter 5:7", "Psalm 55:22", "Isaiah 41:10"], "related": ["Peace"]},
    {"topic": "Comfort", "refs": ["2 Corinthians 1:3-4", "Psalm 23:4", "Matthew 5:4", "Isaiah 40:1", "John 14:1-3"], "related": ["Suffering", "Peace"]},
    {"topic": "Suffering", "refs": ["Romans 8:18", "1 Peter 4:12-13", "James 1:2-4", "2 Corinthians 4:17", "Psalm 34:18"], "related": ["Comfort", "Perseverance"]},
    {"topic": "Joy", "refs": ["Nehemiah 8:10", "Philippians 4:4", "Psalm 16:11", "John 15:11", "Galatians 5:22"], "related": ["Peace", "Thanksgiving"]},
    {"topic": "Peace", "refs": ["John 14:27", "Philippians 4:7", "Isaiah 26:3", "Romans 5:1", "Matthew 5:9"], "related": ["Joy", "Anxiety and worry"]},
    {"topic": "Patience", "refs": ["James 5:7-8", "Romans 12:12", "Psalm 27:14", "Galatians 6:9", "Ecclesiastes 7:8"], "related": ["Perseverance", "Hope"]},
    {"topic": "Humility", "refs": ["Philippians 2:3-8", "Micah 6:8", "James 4:6", "Proverbs 11:2", "1 Peter 5:5-6"], "related": ["Pride", "Servanthood"]},
    {"topic": "Pride", "refs": ["Proverbs 16:18", "James 4:6", "Proverbs 8:13", "1 John 2:16", "Daniel 4:37"], "related": ["Humility"]},
    {"topic": "Anger", "refs": ["Ephesians 4:26-27", "James 1:19-20", "Proverbs 15:1", "Psalm 37:8", "Colossians 3:8"], "related": ["Patience", "Forgiveness"]},
    {"topic": "Money and giving", "refs": ["1 Timothy 6:10", "2 Corinthians 9:6-7", "Malachi 3:10", "Matthew 6:19-21", "Proverbs 3:9-10"], "related": ["Work", "The poor"]},
    {"topic": "Work", "refs": ["Colossians 3:23-24", "Proverbs 14:23", "2 Thessalonians 3:10", "Ecclesiastes 9:10", "Genesis 2:15"], "related": ["Money and giving", "Rest and Sabbath"]},
    {"topic": "Marriage", "refs": ["Genesis 2:24", "Ephesians 5:25-33", "1 Corinthians 13:4-7", "Ecclesiastes 4:9-12", "Song of Solomon 8:7"], "related": ["Love", "Family"]},
    {"topic": "Family", "refs": ["Deuteronomy 6:6-7", "Ephesians 6:1-4", "Proverbs 22:6", "Psalm 127:3", "Joshua 24:15"], "related": ["Marriage", "Children"]},
    {"topic": "Children", "refs": ["Psalm 127:3", "Proverbs 22:6", "Matthew 19:14", "Ephesians 6:4", "3 John 1:4"], "related": ["Family"]},
    {"topic": "Friendship", "refs": ["Proverbs 17:17", "Proverbs 27:17", "John 15:13", "Ecclesiastes 4:9-10", "1 Samuel 18:1"], "related": ["Love", "Unity"]},
    {"topic": "Justice", "refs": ["Micah 6:8", "Amos 5:24", "Isaiah 1:17", "Proverbs 31:8-9", "Psalm 89:14"], "related": ["Mercy", "The poor"]},
    {"topic": "Mercy", "refs": ["Micah 6:8", "Matthew 5:7", "Lamentations 3:22-23", "Luke 6:36", "Titus 3:5"], "related": ["Grace", "Justice"]},
    {"topic": "Truth", "refs": ["John 14:6", "John 8:32", "Psalm 25:5", "Ephesians 4:15", "John 17:17"], "related": ["Lying", "The Word"]},
    {"topic": "Lying", "refs": ["Proverbs 12:22", "Exodus 20:16", "Colossians 3:9", "Proverbs 19:9", "John 8:44"], "related": ["Truth"]},
    {"topic": "Temptation", "refs": ["1 Corinthians 10:13", "James 1:13-14", "Matthew 26:41", "Hebrews 4:15", "Matthew 4:1-11"], "related": ["Sin", "Perseverance"]},
    {"topic": "Perseverance", "refs": ["James 1:12", "Galatians 6:9", "Hebrews 12:1-2", "Romans 5:3-4", "2 Timothy 4:7"], "related": ["Patience", "Hope"]},
    {"topic": "Heaven", "refs": ["John 14:2-3", "Revelation 21:1-4", "Philippians 3:20", "2 Corinthians 5:1", "Matthew 6:20"], "related": ["Resurrection", "The second coming"]},
    {"topic": "Resurrection", "refs": ["1 Corinthians 15:20-22", "John 11:25-26", "Romans 6:4-5", "1 Thessalonians 4:16", "Matthew 28:5-6"], "related": ["Heaven", "The second coming"]},
    {"topic": "The second coming", "refs": ["Acts 1:11", "1 Thessalonians 4:16-17", "Matthew 24:36", "Revelation 22:12", "Titus 2:13"], "related": ["Heaven", "Resurrection"]},
    {"topic": "Creation", "refs": ["Genesis 1:1", "Psalm 19:1", "John 1:3", "Colossians 1:16", "Romans 1:20"], "related": ["The Word"]},
    {"topic": "Covenant", "refs": ["Genesis 12:2-3", "Exodus 19:5", "Jeremiah 31:31-33", "Luke 22:20", "Hebrews 8:6"], "related": ["Law and gospel"]},
    {"topic": "Rest and Sabbath", "refs": ["Genesis 2:2-3", "Exodus 20:8-11", "Matthew 11:28-30", "Hebrews 4:9-10", "Psalm 46:10"], "related": ["Work", "Peace"]},
    {"topic": "Worship", "refs": ["John 4:23-24", "Psalm 95:6", "Romans 12:1", "Psalm 100:1-5", "Revelation 4:11"], "related": ["Praise", "Prayer"]},
    {"topic": "Praise", "refs": ["Psalm 150:1-6", "Psalm 34:1", "Hebrews 13:15", "Psalm 103:1-2", "Ephesians 1:6"], "related": ["Worship", "Thanksgiving"]},
    {"topic": "Thanksgiving", "refs": ["1 Thessalonians 5:18", "Psalm 100:4", "Philippians 4:6", "Colossians 3:17", "Psalm 107:1"], "related": ["Praise", "Joy"]},
    {"topic": "Servanthood", "refs": ["Mark 10:43-45", "John 13:14-15", "Philippians 2:5-7", "Galatians 5:13", "Matthew 25:40"], "related": ["Humility", "Leadership"]},
    {"topic": "Leadership", "refs": ["Mark 10:42-45", "1 Timothy 3:1-7", "Proverbs 11:14", "Exodus 18:21", "1 Peter 5:2-3"], "related": ["Servanthood", "Wisdom"]},
    {"topic": "Unity", "refs": ["Psalm 133:1", "John 17:20-21", "Ephesians 4:3-6", "1 Corinthians 1:10", "Colossians 3:14"], "related": ["The church", "Love"]},
    {"topic": "The church", "refs": ["Matthew 16:18", "Acts 2:42-47", "1 Corinthians 12:12-27", "Ephesians 2:19-22", "Hebrews 10:24-25"], "related": ["Unity", "Spiritual gifts"]},
    {"topic": "The Great Commission", "refs": ["Matthew 28:18-20", "Acts 1:8", "Mark 16:15", "Romans 10:14-15", "2 Corinthians 5:20"], "related": ["The church"]},
    {"topic": "The armor of God", "refs": ["Ephesians 6:10-18", "2 Corinthians 10:4", "1 Thessalonians 5:8", "Psalm 18:39"], "related": ["Temptation", "Perseverance"]},
    {"topic": "Fruit of the Spirit", "refs": ["Galatians 5:22-23", "John 15:4-5", "Matthew 7:16-20", "Colossians 3:12-14"], "related": ["The Holy Spirit", "Love"]},
    {"topic": "Spiritual gifts", "refs": ["1 Corinthians 12:4-11", "Romans 12:6-8", "1 Peter 4:10-11", "Ephesians 4:11-13"], "related": ["The Holy Spirit", "The church"]},
    {"topic": "The Shepherd", "refs": ["Psalm 23:1-6", "John 10:11-15", "Ezekiel 34:11-16", "Isaiah 40:11", "1 Peter 5:4"], "related": ["Comfort", "Guidance"]},
    {"topic": "Light", "refs": ["John 8:12", "Psalm 119:105", "Matthew 5:14-16", "1 John 1:5-7", "Isaiah 9:2"], "related": ["Truth", "The Word"]},
    {"topic": "The Word", "refs": ["John 1:1-5", "2 Timothy 3:16-17", "Psalm 119:11", "Hebrews 4:12", "Isaiah 55:11"], "related": ["Truth", "Creation"]},
    {"topic": "Law and gospel", "refs": ["Romans 3:20-24", "Galatians 3:24", "Matthew 5:17", "Romans 8:3-4", "John 1:17"], "related": ["Covenant", "Grace"]},
    {"topic": "Faith and works", "refs": ["James 2:14-26", "Ephesians 2:8-10", "Titus 3:8", "Galatians 5:6"], "related": ["Faith", "Fruit of the Spirit"]},
    {"topic": "Strength", "refs": ["Isaiah 40:29-31", "Philippians 4:13", "Psalm 46:1", "Nehemiah 8:10", "2 Corinthians 12:9-10"], "related": ["Perseverance", "Comfort"]},
    {"topic": "Guidance", "refs": ["Proverbs 3:5-6", "Psalm 32:8", "James 1:5", "Psalm 119:105", "Isaiah 30:21"], "related": ["Wisdom", "The Shepherd"]},
    {"topic": "Healing", "refs": ["Psalm 147:3", "James 5:14-15", "Exodus 15:26", "Isaiah 53:5", "Jeremiah 17:14"], "related": ["Comfort", "Prayer"]},
    {"topic": "The poor", "refs": ["Proverbs 19:17", "Matthew 25:35-40", "Isaiah 58:6-7", "James 2:5", "Deuteronomy 15:11"], "related": ["Justice", "Mercy", "Money and giving"]},
    {"topic": "Widows and orphans", "refs": ["James 1:27", "Psalm 68:5", "Exodus 22:22", "Isaiah 1:17", "Deuteronomy 10:18"], "related": ["The poor", "Justice"]},
]

# ── API ─────────────────────────────────────────────────────────────────────────────────────────

NOTE = ("Curated reference tables with the disputes restored — where scholarship genuinely "
        "disagrees (a cubit's length, a book's date) both positions are carried, never one "
        "flattened verdict. Every entry points into Scripture; the table is the index, never "
        "the text. Names carry Strong's numbers that open into the real lexicon.")

_TABLES: Dict[str, Dict[str, Any]] = {
    "weights_measures": {"title": "Weights & measures", "entries": WEIGHTS_MEASURES,
                         "means": "biblical units with modern approximations; disputed standards carry both values"},
    "names_of_god": {"title": "Names of God", "entries": NAMES_OF_GOD,
                     "means": "the names and titles of God with Strong's numbers — each opens into the lexicon and every occurrence"},
    "parables": {"title": "The parables of Jesus", "entries": PARABLES,
                 "means": "one parable, every gospel that carries it, side by side; John's figures flagged as figures"},
    "miracles": {"title": "The miracles of Jesus", "entries": MIRACLES,
                 "means": "one miracle, every gospel witness; differing details (Bartimaeus and companion) carried, not harmonised away"},
    "book_intros": {"title": "Book introductions", "entries": BOOK_INTROS,
                    "means": "orientation per book: traditional authorship with real disputes flagged, working dates as ranges, theme, key verse"},
    "topical_index": {"title": "Topical index", "entries": TOPICAL_INDEX,
                      "means": "starting-point references per subject — a door into Scripture, deliberately few; /search goes deeper"},
}


def tables() -> Dict[str, Any]:
    """The index: every table with its count and what the count means."""
    return {"tables": [{"key": k, "title": t["title"], "count": len(t["entries"]), "means": t["means"]}
                       for k, t in _TABLES.items()],
            "note": NOTE}


def get_table(key: str) -> Optional[Dict[str, Any]]:
    t = _TABLES.get((key or "").strip().lower())
    if t is None:
        return None
    return {"key": (key or "").strip().lower(), "title": t["title"], "count": len(t["entries"]),
            "means": t["means"], "entries": t["entries"], "note": NOTE}


def all_refs() -> List[str]:
    """Every scripture reference in every table — the test walks these against the corpus."""
    out: List[str] = []
    for t in _TABLES.values():
        for e in t["entries"]:
            out.extend(e.get("refs") or [])
            for k in ("first_ref", "key_verse", "matthew", "mark", "luke", "john"):
                if e.get(k):
                    out.append(e[k])
    return out


__all__ = ["tables", "get_table", "all_refs", "NOTE",
           "WEIGHTS_MEASURES", "NAMES_OF_GOD", "PARABLES", "MIRACLES", "BOOK_INTROS", "TOPICAL_INDEX"]
