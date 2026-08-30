#!/usr/bin/env python3
"""Build data/prophecy/messianic.jsonl — the OT-prophecy → NT-fulfillment map (Matt, 2026-08-30: "run
all prophecies in the Old Testament, find how they are met in the New Testament").

CONDUIT, NOT INTERPRETER. This does NOT judge that a prophecy is fulfilled — that is interpretive, and
not ours to assert. It enumerates the NT-EXPLICIT tier: pairs where the NEW TESTAMENT ITSELF cites the
Old ("that it might be fulfilled…", or a direct quotation). The interpretive claim is carried by
Scripture's own witness, not by us; both verses are in our public-domain WEB corpus. What this tool
seals is only the MECHANICAL fact — that each reference RESOLVES against the WEB — and it OMITS, never
guesses, any pair whose refs do not resolve (the honesty gate the VISION_PLAN mandates: "unsupported
links are omitted, not guessed"). Verdict is CONCORDANT (the NT affirms the pairing), never "HOLDS".

    PYTHONPATH=src python tools/build_prophecy_fulfillments.py [--check]

Leaves the cross-cultural signposts (data/prophecy/signposts.jsonl) untouched — a different concept.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concordance.verifiers import scripture  # noqa: E402

OUT = ROOT / "data" / "prophecy" / "messianic.jsonl"

# The NT-explicit tier: (id, title, ot_ref, [nt_refs], theme, how the NT names it). Single anchor
# verses (WEB resolves verses, not ranges). Each NT verse quotes or names the OT text as fulfilled —
# the source is Scripture's own citation, which is why this tier is the least contestable place to
# start. Ordered roughly birth → ministry → passion → resurrection → the apostles' witness.
ROWS = [
    ("mp_virgin_birth", "Born of a virgin", "Isaiah 7:14", ["Matthew 1:23"], "birth",
     "Matthew 1:22-23 quotes Isaiah 7:14 as fulfilled"),
    ("mp_bethlehem", "Born in Bethlehem", "Micah 5:2", ["Matthew 2:6"], "birth",
     "Matthew 2:5-6 cites Micah 5:2"),
    ("mp_out_of_egypt", "Called out of Egypt", "Hosea 11:1", ["Matthew 2:15"], "birth",
     "Matthew 2:15 cites Hosea 11:1 as fulfilled"),
    ("mp_rachel_weeping", "Weeping in Ramah", "Jeremiah 31:15", ["Matthew 2:18"], "birth",
     "Matthew 2:17-18 cites Jeremiah 31:15 as fulfilled"),
    ("mp_voice_wilderness", "A voice in the wilderness", "Isaiah 40:3", ["Matthew 3:3"], "ministry",
     "Matthew 3:3 cites Isaiah 40:3"),
    ("mp_galilee_light", "A light in Galilee", "Isaiah 9:2", ["Matthew 4:16"], "ministry",
     "Matthew 4:14-16 cites Isaiah 9:1-2 as fulfilled"),
    ("mp_messenger_before", "A messenger before him", "Malachi 3:1", ["Matthew 11:10"], "ministry",
     "Matthew 11:10 cites Malachi 3:1"),
    ("mp_bore_infirmities", "He bore our infirmities", "Isaiah 53:4", ["Matthew 8:17"], "ministry",
     "Matthew 8:17 cites Isaiah 53:4 as fulfilled"),
    ("mp_chosen_servant", "The chosen servant", "Isaiah 42:1", ["Matthew 12:18"], "ministry",
     "Matthew 12:17-18 cites Isaiah 42:1-4 as fulfilled"),
    ("mp_parables", "He spoke in parables", "Psalm 78:2", ["Matthew 13:35"], "ministry",
     "Matthew 13:35 cites Psalm 78:2 as fulfilled"),
    ("mp_hardened_hearts", "Hearing they do not understand", "Isaiah 6:10",
     ["Matthew 13:15", "John 12:40"], "ministry", "Matthew 13:14-15 and John 12:39-40 cite Isaiah 6:9-10"),
    ("mp_spirit_upon", "The Spirit of the Lord upon him", "Isaiah 61:1", ["Luke 4:18"], "ministry",
     "Luke 4:18-21 reads Isaiah 61:1-2 as fulfilled"),
    ("mp_zeal_house", "Zeal for your house", "Psalm 69:9", ["John 2:17"], "ministry",
     "John 2:17 cites Psalm 69:9"),
    ("mp_babes_praise", "Praise from the mouths of babes", "Psalm 8:2", ["Matthew 21:16"], "ministry",
     "Matthew 21:16 cites Psalm 8:2"),
    ("mp_triumphal_entry", "Riding on a donkey", "Zechariah 9:9", ["Matthew 21:5"], "passion",
     "Matthew 21:4-5 cites Zechariah 9:9 as fulfilled"),
    ("mp_he_who_comes", "Blessed is he who comes", "Psalm 118:26", ["Matthew 21:9"], "passion",
     "Matthew 21:9 quotes Psalm 118:26"),
    ("mp_cornerstone", "The rejected cornerstone", "Psalm 118:22",
     ["Matthew 21:42", "Acts 4:11"], "passion", "Matthew 21:42 and Acts 4:11 cite Psalm 118:22"),
    ("mp_betrayed_friend", "Betrayed by a friend", "Psalm 41:9", ["John 13:18"], "passion",
     "John 13:18 cites Psalm 41:9 as fulfilled"),
    ("mp_thirty_pieces", "Thirty pieces of silver", "Zechariah 11:13", ["Matthew 27:9"], "passion",
     "Matthew 27:9-10 cites the prophecy (Zechariah 11:12-13)"),
    ("mp_shepherd_struck", "Strike the shepherd", "Zechariah 13:7", ["Matthew 26:31"], "passion",
     "Matthew 26:31 cites Zechariah 13:7 as fulfilled"),
    ("mp_with_transgressors", "Numbered with transgressors", "Isaiah 53:12", ["Luke 22:37"], "passion",
     "Luke 22:37 cites Isaiah 53:12 as fulfilled"),
    ("mp_forsaken", "My God, why have you forsaken me", "Psalm 22:1", ["Matthew 27:46"], "passion",
     "Matthew 27:46 quotes Psalm 22:1"),
    ("mp_cast_lots", "They cast lots for my garments", "Psalm 22:18", ["John 19:24"], "passion",
     "John 19:24 cites Psalm 22:18 as fulfilled"),
    ("mp_gall_vinegar", "Gall and vinegar", "Psalm 69:21", ["John 19:28"], "passion",
     "John 19:28-29 fulfills Psalm 69:21"),
    ("mp_no_bone_broken", "Not a bone broken", "Psalm 34:20", ["John 19:36"], "passion",
     "John 19:36 cites the Scripture (Psalm 34:20; Exodus 12:46) as fulfilled"),
    ("mp_pierced", "They will look on him whom they pierced", "Zechariah 12:10", ["John 19:37"],
     "passion", "John 19:37 cites Zechariah 12:10 as fulfilled"),
    ("mp_silent_lamb", "Led as a lamb, silent", "Isaiah 53:7", ["Acts 8:32"], "passion",
     "Acts 8:32-33 quotes Isaiah 53:7-8"),
    ("mp_not_corruption", "You will not let your Holy One see decay", "Psalm 16:10", ["Acts 2:27"],
     "resurrection", "Acts 2:25-31 cites Psalm 16:10 as fulfilled in the resurrection"),
    ("mp_right_hand", "Sit at my right hand", "Psalm 110:1", ["Matthew 22:44", "Acts 2:34"],
     "resurrection", "Matthew 22:44 and Acts 2:34-35 cite Psalm 110:1"),
    ("mp_begotten", "You are my Son", "Psalm 2:7", ["Acts 13:33"], "resurrection",
     "Acts 13:33 cites Psalm 2:7 (also Hebrews 1:5)"),
    ("mp_prophet_like_moses", "A prophet like Moses", "Deuteronomy 18:15", ["Acts 3:22"], "apostles",
     "Acts 3:22 cites Deuteronomy 18:15"),
    ("mp_spirit_poured", "I will pour out my Spirit", "Joel 2:28", ["Acts 2:17"], "apostles",
     "Acts 2:16-17 cites Joel 2:28 as fulfilled at Pentecost"),
    ("mp_call_on_name", "Whoever calls on the name of the Lord", "Joel 2:32", ["Acts 2:21"], "apostles",
     "Acts 2:21 quotes Joel 2:32 (also Romans 10:13)"),
    ("mp_tabernacle_david", "The tabernacle of David rebuilt", "Amos 9:11", ["Acts 15:16"], "apostles",
     "Acts 15:16-17 cites Amos 9:11-12"),
    ("mp_sure_mercies", "The sure mercies of David", "Isaiah 55:3", ["Acts 13:34"], "apostles",
     "Acts 13:34 cites Isaiah 55:3"),
    ("mp_light_gentiles", "A light to the Gentiles", "Isaiah 49:6", ["Acts 13:47"], "apostles",
     "Acts 13:47 cites Isaiah 49:6"),
    ("mp_seed_nations", "In your seed all nations blessed", "Genesis 22:18", ["Acts 3:25"], "apostles",
     "Acts 3:25 cites Genesis 22:18 (also Galatians 3:16)"),
    ("mp_nations_rage", "The nations rage", "Psalm 2:1", ["Acts 4:25"], "apostles",
     "Acts 4:25-26 cites Psalm 2:1-2"),
    ("mp_body_prepared", "A body you prepared for me", "Psalm 40:6", ["Hebrews 10:5"], "epistles",
     "Hebrews 10:5-7 cites Psalm 40:6-8"),
    ("mp_throne_god", "Your throne, O God, is forever", "Psalm 45:6", ["Hebrews 1:8"], "epistles",
     "Hebrews 1:8-9 cites Psalm 45:6-7"),
    ("mp_foundation_earth", "You laid the foundation of the earth", "Psalm 102:25", ["Hebrews 1:10"],
     "epistles", "Hebrews 1:10-12 cites Psalm 102:25-27"),
    ("mp_declare_name", "I will declare your name to my brothers", "Psalm 22:22", ["Hebrews 2:12"],
     "epistles", "Hebrews 2:12 cites Psalm 22:22"),
    ("mp_new_covenant", "A new covenant", "Jeremiah 31:31", ["Hebrews 8:8"], "epistles",
     "Hebrews 8:8-12 cites Jeremiah 31:31-34"),
    ("mp_cornerstone_zion", "A cornerstone laid in Zion", "Isaiah 28:16", ["1 Peter 2:6"], "epistles",
     "1 Peter 2:6 and Romans 9:33 cite Isaiah 28:16"),
    ("mp_who_believed", "Who has believed our report", "Isaiah 53:1", ["John 12:38"], "epistles",
     "John 12:38 and Romans 10:16 cite Isaiah 53:1"),
    ("mp_every_knee", "Every knee shall bow", "Isaiah 45:23", ["Romans 14:11"], "epistles",
     "Romans 14:11 and Philippians 2:10-11 cite Isaiah 45:23"),
    ("mp_root_jesse", "The root of Jesse", "Isaiah 11:10", ["Romans 15:12"], "epistles",
     "Romans 15:12 cites Isaiah 11:10"),
    ("mp_live_by_faith", "The righteous shall live by faith", "Habakkuk 2:4", ["Romans 1:17"], "epistles",
     "Romans 1:17, Galatians 3:11, Hebrews 10:38 cite Habakkuk 2:4"),
    ("mp_abraham_believed", "Abraham believed God", "Genesis 15:6", ["Romans 4:3"], "epistles",
     "Romans 4:3 and Galatians 3:6 cite Genesis 15:6"),
    ("mp_deliverer_zion", "The deliverer from Zion", "Isaiah 59:20", ["Romans 11:26"], "epistles",
     "Romans 11:26-27 cites Isaiah 59:20-21"),
]


def _verse(ref):
    r = scripture.resolve_ref(ref)
    return (r.get("text") or "").strip() if r.get("status") == "ok" else None


def build():
    kept, dropped = [], []
    for rid, title, ot, nts, theme, source in ROWS:
        ot_text = _verse(ot)
        if ot_text is None:
            dropped.append((rid, "OT ref did not resolve: " + ot))
            continue
        nt_ok = []
        for nt in nts:
            t = _verse(nt)
            if t is not None:
                nt_ok.append({"ref": nt, "text": t})
        if not nt_ok:
            dropped.append((rid, "no NT fulfillment ref resolved: " + ", ".join(nts)))
            continue
        kept.append({
            "id": rid, "title": title, "category": "messianic", "theme": theme,
            "fulfillment_kind": "nt_explicit",
            "ot": {"ref": ot, "text": ot_text},
            "nt_fulfillments": nt_ok,
            "source": source,                      # Scripture's OWN citation carries the interpretive link
            "verdict": "CONCORDANT",               # the NT affirms it — a signpost, NEVER "HOLDS"
            "note": "The New Testament itself names this fulfillment; the pairing is Scripture's "
                    "witness, not ours. We seal only that every reference resolves against the WEB.",
        })
    return kept, dropped


def main():
    kept, dropped = build()
    for rid, why in dropped:
        print("OMITTED  %-22s  (%s)" % (rid, why))
    print("\n%d verified / %d omitted (of %d curated NT-explicit pairs)" % (len(kept), len(dropped), len(ROWS)))
    if "--check" in sys.argv[1:]:
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        for row in kept:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
