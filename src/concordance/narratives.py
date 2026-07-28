"""The storyboards — the common narratives, charted in the Bible first.

Matt, 2026-07-28: "We develop story boards or the common narratives. We begin charting in the
Bible. Once that is complete we can isolate the components and mix and match. The same with the
Archetypes. You may be many of these characters at times of your life. They are just a reference
point. We are not saying you are that person, but the characteristics have been displayed."

So the order of operations here is the design itself:

  1. CHART IN THE BIBLE. Each narrative is a recurring story Scripture itself tells repeatedly —
     exile and return, the barren woman bears, the younger chosen, the testing in the wilderness.
     Each is charted as INSTANCES: real people, real places, verified references. The Bible is the
     ground corpus; nothing is imported from outside it and nothing is invented.
  2. ISOLATE THE COMPONENTS. Every narrative is a sequence drawn from ONE shared MOVEMENT
     vocabulary (call, descent, testing, deliverance, return …). Because the vocabulary is shared,
     the components can be mixed and matched — a reader tracing "testing" walks it through every
     storyboard it appears in. Recombination of attributed pieces, never generation.
  3. REFERENCE POINTS, NOT IDENTITIES. A person may recognise themselves in many of these
     storyboards at different times of their life. That recognition is the point — and its limit.
     We are not saying you are that person; the characteristics have been displayed, and the same
     faithful God met them there.

Witness-gated like the rest of the study family. Found and charted, never generated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

FRAMING = ("A reference point, not an identity. You may recognise yourself in many of these "
           "storyboards at different times of your life — that recognition is the point, and its "
           "limit. We are not saying you are that person; the characteristics have been displayed, "
           "and the same faithful God met them there.")

# ── The shared movement vocabulary — the components that mix and match ──────────────────────────
MOVEMENTS: Dict[str, str] = {
    "call":         "God addresses a person — a summons that interrupts ordinary life",
    "reluctance":   "the called one hesitates, argues, or runs",
    "descent":      "down into the pit, the prison, the storm, the far country",
    "exile":        "cast out or carried off — away from home, from the land, from Eden",
    "testing":      "the wilderness stretch where faith is proved, usually longer than wanted",
    "silence":      "the span where God seems absent and the promise seems dead",
    "provision":    "unearned sustenance in the barren place — manna, ravens, a jar that does not empty",
    "deliverance":  "God acts — the sea opens, the lions' mouths shut, the stone rolls away",
    "reversal":     "the great turn — the pit becomes the throne, the gallows take their builder",
    "return":       "the road home — to the land, to the father, to the city",
    "restoration":  "what was lost is given back, often doubled; what was broken is rebuilt",
    "promise":      "God binds Himself with a word before any evidence exists",
    "delay":        "the long gap between the promise and its keeping",
    "fulfillment":  "the promise kept — late by every human clock, exactly on time by God's",
    "sacrifice":    "a costly offering stands in the breach — a life laid down",
    "vindication":  "the rejected one is proven right and raised in honour",
    "commissioning": "the delivered one is sent — the story ends by beginning someone else's",
}

# ── The storyboards, charted in the Bible ───────────────────────────────────────────────────────
# Each instance charts one biblical telling: who, and the beats — movement → the reference where
# that movement happens in THEIR story. Not every telling has every beat; a storyboard is a family
# resemblance, not a mold. Refs are verified against the corpus by the test suite.
NARRATIVES: List[Dict[str, Any]] = [
    {"id": "exile_and_return", "name": "Exile and return",
     "meaning": "driven from home by sin or catastrophe; kept, turned, and brought back",
     "movements": ["exile", "silence", "testing", "return", "restoration"],
     "instances": [
        {"who": "Adam and Eve — out of Eden", "beats": {"exile": ["Genesis 3:23-24"], "promise": ["Genesis 3:15"]}},
        {"who": "Jacob — flight and homecoming", "beats": {"exile": ["Genesis 28:10"], "testing": ["Genesis 31:41"], "return": ["Genesis 33:4"], "restoration": ["Genesis 33:9-11"]}},
        {"who": "Israel — Babylon and back", "beats": {"exile": ["2 Kings 25:11"], "silence": ["Psalm 137:1-4"], "promise": ["Jeremiah 29:10-11"], "return": ["Ezra 1:3"], "restoration": ["Nehemiah 6:15-16"]}},
        {"who": "The prodigal son", "beats": {"exile": ["Luke 15:13"], "descent": ["Luke 15:14-16"], "return": ["Luke 15:20"], "restoration": ["Luke 15:22-24"]}}]},
    {"id": "barren_woman_bears", "name": "The barren woman bears",
     "meaning": "the impossible child, given late, so the gift is unmistakably God's",
     "movements": ["promise", "delay", "silence", "fulfillment"],
     "instances": [
        {"who": "Sarah — Isaac", "beats": {"promise": ["Genesis 17:19"], "delay": ["Genesis 18:11"], "fulfillment": ["Genesis 21:1-2"]}},
        {"who": "Rebekah — Jacob and Esau", "beats": {"delay": ["Genesis 25:21"], "fulfillment": ["Genesis 25:24-26"]}},
        {"who": "Rachel — Joseph", "beats": {"silence": ["Genesis 30:1"], "fulfillment": ["Genesis 30:22-24"]}},
        {"who": "Hannah — Samuel", "beats": {"silence": ["1 Samuel 1:10-11"], "fulfillment": ["1 Samuel 1:20"], "commissioning": ["1 Samuel 1:27-28"]}},
        {"who": "Elizabeth — John", "beats": {"delay": ["Luke 1:7"], "promise": ["Luke 1:13"], "fulfillment": ["Luke 1:57"]}}]},
    {"id": "younger_chosen", "name": "The younger chosen",
     "meaning": "the expected line is passed over; grace does not follow birth order",
     "movements": ["promise", "reversal", "vindication"],
     "instances": [
        {"who": "Isaac over Ishmael", "beats": {"promise": ["Genesis 17:19-21"]}},
        {"who": "Jacob over Esau", "beats": {"promise": ["Genesis 25:23"], "reversal": ["Genesis 27:28-29"]}},
        {"who": "Joseph over his brothers", "beats": {"promise": ["Genesis 37:5-8"], "vindication": ["Genesis 45:4-8"]}},
        {"who": "David over his brothers", "beats": {"reversal": ["1 Samuel 16:11-13"], "vindication": ["1 Samuel 17:50"]}}]},
    {"id": "wilderness_testing", "name": "Testing in the wilderness",
     "meaning": "the barren stretch between deliverance and inheritance, where trust is formed",
     "movements": ["deliverance", "testing", "provision", "fulfillment"],
     "instances": [
        {"who": "Israel — forty years", "beats": {"deliverance": ["Exodus 14:21-22"], "testing": ["Deuteronomy 8:2"], "provision": ["Exodus 16:14-15"], "fulfillment": ["Joshua 21:43-45"]}},
        {"who": "Elijah — to Horeb", "beats": {"descent": ["1 Kings 19:3-4"], "provision": ["1 Kings 19:5-8"], "call": ["1 Kings 19:11-13"]}},
        {"who": "Jesus — forty days", "beats": {"testing": ["Matthew 4:1-4"], "vindication": ["Matthew 4:10-11"]}}]},
    {"id": "call_and_reluctance", "name": "The call and the reluctant one",
     "meaning": "God calls; the called one argues; God does not withdraw the call",
     "movements": ["call", "reluctance", "commissioning"],
     "instances": [
        {"who": "Moses — the bush", "beats": {"call": ["Exodus 3:4"], "reluctance": ["Exodus 4:10-13"], "commissioning": ["Exodus 4:12"]}},
        {"who": "Gideon — the winepress", "beats": {"call": ["Judges 6:12"], "reluctance": ["Judges 6:15"], "commissioning": ["Judges 6:16"]}},
        {"who": "Jeremiah — too young", "beats": {"call": ["Jeremiah 1:4-5"], "reluctance": ["Jeremiah 1:6"], "commissioning": ["Jeremiah 1:7-9"]}},
        {"who": "Jonah — the other direction", "beats": {"call": ["Jonah 1:1-2"], "reluctance": ["Jonah 1:3"], "descent": ["Jonah 1:15-17"], "commissioning": ["Jonah 3:1-3"]}}]},
    {"id": "descent_and_raising", "name": "Down to the pit, raised to life",
     "meaning": "the death-shaped descent God turns into resurrection — the deepest storyboard",
     "movements": ["descent", "silence", "deliverance", "vindication"],
     "instances": [
        {"who": "Joseph — pit and prison to the throne", "beats": {"descent": ["Genesis 37:23-24", "Genesis 39:20"], "silence": ["Genesis 40:23"], "reversal": ["Genesis 41:39-41"], "vindication": ["Genesis 50:20"]}},
        {"who": "Jonah — three days in the deep", "beats": {"descent": ["Jonah 2:3-6"], "deliverance": ["Jonah 2:10"]}},
        {"who": "Daniel — the lions' den", "beats": {"descent": ["Daniel 6:16"], "deliverance": ["Daniel 6:22"], "vindication": ["Daniel 6:25-27"]}},
        {"who": "Christ — the cross and the third day", "beats": {"descent": ["Matthew 27:59-60"], "silence": ["Matthew 27:62-66"], "deliverance": ["Matthew 28:5-6"], "vindication": ["Philippians 2:8-11"]},
         "note": "The storyboard every other telling was sketching — Jesus names Jonah's descent as His own sign (Matthew 12:40)."}]},
    {"id": "great_reversal", "name": "The great reversal",
     "meaning": "the proud brought down, the lowly lifted — the gallows take their builder",
     "movements": ["descent", "reversal", "vindication"],
     "instances": [
        {"who": "Esther and Haman", "beats": {"descent": ["Esther 3:5-6"], "reversal": ["Esther 7:9-10"], "vindication": ["Esther 8:1-2"]}},
        {"who": "Job — double at the end", "beats": {"descent": ["Job 1:20-21"], "silence": ["Job 23:8-9"], "restoration": ["Job 42:10"]}},
        {"who": "Mary's song — the pattern named", "beats": {"reversal": ["Luke 1:51-53"]}},
        {"who": "The rich man and Lazarus", "beats": {"reversal": ["Luke 16:25"]}}]},
    {"id": "covenant_cycle", "name": "Covenant made, broken, renewed",
     "meaning": "God binds Himself; the people break it; God renews it deeper than before",
     "movements": ["promise", "testing", "silence", "fulfillment"],
     "instances": [
        {"who": "Sinai — the tablets broken and rewritten", "beats": {"promise": ["Exodus 19:5-6"], "testing": ["Exodus 32:1-4"], "fulfillment": ["Exodus 34:1"]}},
        {"who": "The judges — the cycle turned and turned", "beats": {"testing": ["Judges 2:11-12"], "deliverance": ["Judges 2:16"], "silence": ["Judges 21:25"]}},
        {"who": "The new covenant promised", "beats": {"promise": ["Jeremiah 31:31-33"], "fulfillment": ["Luke 22:20"]}}]},
    {"id": "shepherd_king", "name": "The shepherd made king",
     "meaning": "the one who tends sheep is the one fit to tend people",
     "movements": ["call", "testing", "commissioning", "fulfillment"],
     "instances": [
        {"who": "Moses — from Jethro's flock", "beats": {"call": ["Exodus 3:1-4"], "commissioning": ["Exodus 3:10"]}},
        {"who": "David — from his father's sheep", "beats": {"call": ["1 Samuel 16:11-13"], "testing": ["1 Samuel 17:34-36"], "fulfillment": ["2 Samuel 5:2-3"]}},
        {"who": "The Good Shepherd", "beats": {"fulfillment": ["John 10:11"], "sacrifice": ["John 10:15"], "commissioning": ["John 21:15-17"]},
         "note": "And the commissioning hands the crook onward: 'feed my sheep.'"}]},
    {"id": "water_crossing", "name": "Through the waters",
     "meaning": "the waters that should drown become the doorway — a birth each time",
     "movements": ["descent", "deliverance", "commissioning"],
     "instances": [
        {"who": "Noah — through the flood", "beats": {"descent": ["Genesis 7:17-18"], "deliverance": ["Genesis 8:15-18"], "promise": ["Genesis 9:12-15"]}},
        {"who": "Israel — the Red Sea", "beats": {"descent": ["Exodus 14:10"], "deliverance": ["Exodus 14:29"], "commissioning": ["Exodus 19:4-6"]}},
        {"who": "Israel — the Jordan", "beats": {"deliverance": ["Joshua 3:15-17"], "commissioning": ["Joshua 4:21-24"]}},
        {"who": "Jesus — the Jordan, and every baptism since", "beats": {"deliverance": ["Matthew 3:16-17"], "commissioning": ["Romans 6:3-4"]}}]},
    {"id": "remnant_kept", "name": "The remnant kept",
     "meaning": "when everything seems lost, God has kept a seed — always",
     "movements": ["testing", "silence", "provision", "restoration"],
     "instances": [
        {"who": "Noah's household", "beats": {"provision": ["Genesis 7:1"], "restoration": ["Genesis 9:1"]}},
        {"who": "Elijah's seven thousand", "beats": {"silence": ["1 Kings 19:10"], "provision": ["1 Kings 19:18"]}},
        {"who": "The exiles who returned", "beats": {"testing": ["Ezra 3:12-13"], "restoration": ["Haggai 2:9"]}},
        {"who": "The remnant by grace", "beats": {"fulfillment": ["Romans 11:4-5"]}}]},
    {"id": "suffering_servant", "name": "The suffering servant vindicated",
     "meaning": "the faithful one suffers not despite faithfulness but through it — and is raised",
     "movements": ["sacrifice", "silence", "vindication"],
     "instances": [
        {"who": "Joseph — sold, and a saviour of nations", "beats": {"sacrifice": ["Genesis 37:28"], "vindication": ["Genesis 45:7"]}},
        {"who": "The Servant of Isaiah", "beats": {"sacrifice": ["Isaiah 53:5-6"], "silence": ["Isaiah 53:7"], "vindication": ["Isaiah 53:11-12"]}},
        {"who": "Stephen — the first witness", "beats": {"sacrifice": ["Acts 7:59-60"], "vindication": ["Acts 7:55-56"]}},
        {"who": "Christ — the Servant Himself", "beats": {"sacrifice": ["1 Peter 2:24"], "vindication": ["Acts 2:32-36"]}}]},
]

_BY_ID = {n["id"]: n for n in NARRATIVES}

NOTE = ("The common narratives, charted in the Bible first: every instance is real people and "
        "verified references — found and charted, never generated. The movements are one shared "
        "vocabulary, so the components can be traced across storyboards and recombined without "
        "ever inventing a story Scripture does not tell. " + FRAMING)


def storyboards() -> Dict[str, Any]:
    """The index: every narrative with its movement sequence and instance count."""
    return {"narratives": [{"id": n["id"], "name": n["name"], "meaning": n["meaning"],
                            "movements": n["movements"], "instances": len(n["instances"])}
                           for n in NARRATIVES],
            "movements": MOVEMENTS, "count": len(NARRATIVES), "framing": FRAMING, "note": NOTE}


def get(narrative_id: str) -> Optional[Dict[str, Any]]:
    n = _BY_ID.get((narrative_id or "").strip().lower())
    if n is None:
        return None
    return {**n, "framing": FRAMING}


def by_movement(movement: str) -> Optional[Dict[str, Any]]:
    """Isolate ONE component and walk it across every storyboard that carries it — the mix-and-
    match view. 'Testing' traced through Israel, Elijah, and Jesus is a study in itself."""
    m = (movement or "").strip().lower()
    if m not in MOVEMENTS:
        return None
    hits = []
    for n in NARRATIVES:
        for inst in n["instances"]:
            refs = (inst.get("beats") or {}).get(m)
            if refs:
                hits.append({"narrative": n["name"], "narrative_id": n["id"],
                             "who": inst["who"], "refs": refs})
    return {"movement": m, "means": MOVEMENTS[m], "appearances": hits,
            "count": len(hits), "framing": FRAMING}


def all_refs() -> List[str]:
    """Every reference in every storyboard — the test suite walks these against the corpus."""
    out: List[str] = []
    for n in NARRATIVES:
        for inst in n["instances"]:
            for refs in (inst.get("beats") or {}).values():
                out.extend(refs)
    return out


__all__ = ["storyboards", "get", "by_movement", "all_refs",
           "NARRATIVES", "MOVEMENTS", "FRAMING", "NOTE"]
