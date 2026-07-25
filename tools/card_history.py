#!/usr/bin/env python3
"""Fill the history gap — card dated historical events from Wikidata (CC0). The card maps to the source.

Matt: "Look for the most obvious gaps." The corpus had NO history shelf. Wikidata is CC0 (public
domain dedication) and holds millions of dated events. This pulls the key event classes (battles,
wars, treaties, sieges, massacres, disasters, revolutions, historical events) with a point-in-time
date + English label + description, STORES the raw pull on the HD, and mints one stub card per event
whose link (the Wikidata entity) IS the map to the full record. Bounded per class so it does not
swamp the corpus; polite to the endpoint.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_history.py
    ... --per 3000
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_history"
_UA = "NarrowHighway/1.0 (history archive; mesh@narrowhighway.org)"
_slug = re.compile(r"[^a-z0-9]+")
# (Wikidata class QID, a human label for the kind)
_CLASSES = [
    ("Q178561", "battle"), ("Q198", "war"), ("Q131569", "treaty"), ("Q188055", "siege"),
    ("Q3199915", "massacre"), ("Q3839081", "disaster"), ("Q10931", "revolution"),
    ("Q13418847", "historical event"), ("Q7283", "terrorist attack"), ("Q3230247", "coup"),
]


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _sparql(qid: str, per: int) -> list:
    # The WITNESS gate at acquisition (Deuteronomy 19:15): only take events borne witness to by at least
    # two independent language communities (sitelinks >= 2). This both enforces the two-witness threshold
    # AND shrinks the result set so ORDER BY the attestation breadth does not blow the endpoint's timeout;
    # the best-witnessed events come first.
    q = (f'SELECT ?e ?eLabel ?date ?eDescription ?sl WHERE {{ ?e wdt:P31 wd:{qid} ; wdt:P585 ?date ; '
         f'wikibase:sitelinks ?sl . FILTER(?sl >= 2) '
         f'SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} ORDER BY DESC(?sl) LIMIT {per}')
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/sparql-results+json"})
    last = None
    for attempt in range(3):  # the endpoint 502s intermittently under load; be patient, be polite
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3.0 * (attempt + 1))
    raise last


def main() -> int:
    per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 3000
    raw: dict = {}
    for qid, kind in _CLASSES:
        try:
            rows = _sparql(qid, per)
            for b in rows:
                qurl = b.get("e", {}).get("value", "")
                q = qurl.rsplit("/", 1)[-1]
                if not q or q in raw:
                    continue
                label = b.get("eLabel", {}).get("value", "")
                if not label or label == q:            # skip unlabeled entities
                    continue
                try:
                    sl = int(float(b.get("sl", {}).get("value", "0") or 0))
                except ValueError:
                    sl = 0
                raw[q] = {"qid": q, "label": label, "date": b.get("date", {}).get("value", "")[:10],
                          "desc": b.get("eDescription", {}).get("value", ""), "kind": kind, "url": qurl, "sl": sl}
            print(f"  {kind:18s} {len(rows):>6,} rows | total {len(raw):,}")
            time.sleep(1.0)
        except Exception as e:  # noqa: BLE001 — a class that errors is skipped, the rest proceed
            print(f"  {kind:18s} ERR {type(e).__name__}: {str(e)[:60]}")
    if not raw:
        print("no events fetched"); return 1
    # store the raw pull on the HD (the source), keep the cards small
    hd = _base() / "history"
    hd.mkdir(parents=True, exist_ok=True)
    (hd / "events.json").write_text(json.dumps(list(raw.values()), ensure_ascii=False), encoding="utf-8")

    out = Path("data")
    spine = {
        "id": SPINE, "kind": "reference", "title": "History — established by the witness gate",
        "body": ("The dated events of the world — battles, wars, treaties, disasters, turning points. "
                 "History does NOT pass the deterministic gate: an event cannot be sealed like a sum. It "
                 "passes the WITNESS gate — a matter is established by two or three witnesses (Deuteronomy "
                 "19:15; Matthew 18:16; 2 Corinthians 13:1). Each event here carries its ATTESTATION (how "
                 "many independent records bear witness), and its link points to the sources so the reader "
                 "may weigh the witnesses. The LORD is Lord of history (Daniel 2:21)."),
        "source": {"label": "Wikidata (CC0)", "url": "https://www.wikidata.org", "domain": "history", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["history", "events", "witness", "attestation", "time", "spine"],
        "subject": "history",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the events of time, a spine of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    method = {
        "id": "card_history_the_witness_gate", "kind": "reference",
        "title": "The witness gate — how the events of history are established",
        "body": ("History cannot go through the same gate as mathematics and physics: you cannot SEAL that "
                 "the Battle of Hastings occurred the way you seal 2+2=4. History has two layers. Its "
                 "SKELETON — the dates and the calendar — is sealable (calendar arithmetic passes the "
                 "deterministic gate). Its BODY — that the event happened — is ATTESTED, established by the "
                 "WITNESS gate: two or three independent witnesses (Deuteronomy 19:15; Matthew 18:16; 2 "
                 "Corinthians 13:1). This is exactly the historical method — multiple independent "
                 "attestation, primary sources near the event, physical evidence, coherence — and it is the "
                 "Playbook's BROTHERS gate applied to the past. Luke names his method (Luke 1:1-4); Paul "
                 "appeals to 500 living witnesses (1 Corinthians 15:6); Peter refuses cleverly devised myths "
                 "for eyewitness testimony (2 Peter 1:16). So: we do not claim to SEAL an event; we count "
                 "its witnesses and point to the sources. One witness is not enough to establish a matter; "
                 "two or three begin to. Weigh them."),
        "source": {"label": "The witness gate — the historical method + Deuteronomy 19:15",
                   "url": "", "domain": "history", "authority_tier": "reference"},
        "shelf": "history", "box": "principle",
        "bands": ["witness", "gate", "attestation", "historical method", "deuteronomy", "evidence", "history"],
        "subject": "the witness gate",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "how history is established"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "history_spine.jsonl").write_text(
        json.dumps(spine, ensure_ascii=False) + "\n" + json.dumps(method, ensure_ascii=False) + "\n", encoding="utf-8")
    n = 0
    with (out / "history_cards.jsonl.tmp").open("w", encoding="utf-8") as f:
        for e in raw.values():
            year = (e["date"][:5].rstrip("-") or e["date"][:4]) if e["date"] else ""
            title = f"{e['label']}" + (f" ({year})" if year else "")
            sl = e.get("sl", 0)
            wclass = ("widely attested" if sl >= 10 else "well attested" if sl >= 5
                      else "attested by three or more witnesses" if sl >= 3 else "attested by two witnesses")
            body = (f"{e['label']}" + (f" — {e['desc']}" if e["desc"] else "") + f". A {e['kind']}"
                    + (f", {e['date']}" if e["date"] else "") + f". Attestation: {wclass}"
                    + (f" ({sl} independent records)." if sl else ".")
                    + f" History passes the witness gate, not the seal — weigh the witnesses at the record: {e['url']}")
            f.write(json.dumps({
                "id": f"card_src_hist_{e['qid'].lower()}", "kind": "reference", "title": title[:180], "body": body,
                "source": {"label": "Wikidata (CC0)", "url": e["url"], "domain": "history", "authority_tier": "reference"},
                "shelf": "history", "box": "source",
                "bands": _slug.sub(" ", e["label"].lower()).split()[:8] + [e["kind"], "history", "event", str(year)],
                "subject": e["label"],
                "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": f"a {e['kind']} in history"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"qid": e["qid"], "date": e["date"], "kind": e["kind"]},
            }, ensure_ascii=False) + "\n")
            n += 1
    os.replace(out / "history_cards.jsonl.tmp", out / "history_cards.jsonl")
    print(f"\ncarded {n:,} historical events -> data/history_cards.jsonl (+1 spine); source on HD at {hd/'events.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
