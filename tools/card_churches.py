#!/usr/bin/env python3
"""Card the churches — calibrating, not judging. Each tradition's own confession + its Scripture.

Matt: "Review all theories and do the same for churches. We are CALIBRATING not judging. There are
seeds of wisdom across time and space of our realm. We are GATHERING, then providing optimal
conditions for others to produce FRUIT." And: the highest knowledge of every denomination, "where
they are successful," held charitably — measured against the plumb-line (Scripture / the original
tongues / the ecumenical creeds), gathered from each tradition's OWN public-domain confession.

So each card GATHERS a tradition's self-understanding: its confession(s), its central emphasis (the
seed it has kept well), and the Scripture it anchors on — presented charitably, never a verdict on the
tradition or the believer. The shared core (the ecumenical creeds) is carded as the ground they hold
in common. "Expose but do not humiliate; we don't lie, but we love you." Conduit: gathered +
attributed, generated=False. Nested under a churches spine → the Word (the plumb-line). Git-tracked.

    PYTHONPATH=src python tools/card_churches.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

WORD = "card_k_spine_the_word"
SPINE = "card_spine_churches"
_slug = re.compile(r"[^a-z0-9]+")


def _sk(s):
    return _slug.sub("_", s.lower()).strip("_")


def _c(name, confession, emphasis, gift, scripture, bands):
    body = (f"{name}. Confession: {confession}. Central emphasis: {emphasis}. The seed it has kept: "
            f"{gift}. Anchored on: {scripture}. (Calibrated against the one plumb-line — Scripture in the "
            f"original tongues and the ecumenical creeds — not judged; a tradition's gift, gathered.)")
    return {
        "id": f"card_church_{_sk(name)}", "kind": "reference", "title": name[:180], "body": body,
        "source": {"label": "The churches — calibrated from each tradition's own confession", "url": "",
                   "domain": "theology", "authority_tier": "reference"},
        "shelf": "churches", "box": "tradition",
        "bands": ["church", "tradition", "denomination", "confession", "calibration"] + list(bands),
        "subject": name,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a tradition of the one Church, measured against the plumb-line"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"confession": confession, "emphasis": emphasis, "gift": gift, "scripture": scripture},
    }


TRADITIONS = [
    _c("The ecumenical creeds — the shared ground", "Apostles' Creed; Nicene Creed (325/381); Chalcedon (451)",
       "the Trinity, the incarnation, the death and resurrection of Christ, the one holy catholic Church",
       "the core every tradition below confesses together — the center that holds",
       "Matthew 28:19; 1 Corinthians 15:3-4; John 1:1-14", ["creed", "nicene", "apostles", "chalcedon", "shared"]),
    _c("Eastern Orthodoxy", "the Nicene Creed (without the filioque); the Seven Ecumenical Councils",
       "the unbroken worship and doctrine of the ancient Church; theosis — union with God; the mystery of the liturgy",
       "continuity with the undivided Church and a deep reverence before the mystery of God",
       "John 17:21-23; 2 Peter 1:4; Psalm 46:10", ["orthodox", "eastern", "theosis", "councils", "liturgy"]),
    _c("Roman Catholicism", "the Nicene Creed; the Council of Trent; the Catechism of the Catholic Church",
       "the visible unity of the Church, the sacraments, the communion of saints across time",
       "a global, historic body holding the faith through the centuries with sacramental seriousness",
       "Matthew 16:18; 1 Corinthians 11:23-26; 1 Timothy 3:15", ["catholic", "roman", "trent", "sacraments"]),
    _c("Lutheran", "the Augsburg Confession (1530); the Book of Concord; Luther's Catechisms",
       "justification by grace alone through faith alone; law and gospel rightly divided; the Word and the sacraments",
       "the recovery of grace — that we are saved by Christ's work received, not our own achieved",
       "Romans 3:28; Ephesians 2:8-9; Galatians 2:16", ["lutheran", "augsburg", "grace", "justification"]),
    _c("Reformed / Presbyterian", "the Westminster Confession (1646); the Heidelberg Catechism; the Belgic Confession",
       "the sovereignty of God over all; covenant; Scripture as supreme authority; the whole life to God's glory",
       "a God-centered vision of all things, and Scripture as the plumb-line over every claim",
       "Romans 11:36; Ephesians 1:4-11; 2 Timothy 3:16-17", ["reformed", "presbyterian", "westminster", "sovereignty"]),
    _c("Anglican", "the Thirty-Nine Articles (1571); the Book of Common Prayer",
       "the via media — Scripture, tradition and reason; common prayer that forms a people",
       "worship that catechizes, and a breadth that holds the reformed and the ancient together",
       "Acts 2:42; Colossians 3:16; 1 Corinthians 14:40", ["anglican", "39 articles", "prayer book", "via media"]),
    _c("Baptist", "the Second London Baptist Confession (1689); the New Hampshire Confession",
       "believer's baptism by immersion; the gathered church of the regenerate; the authority of Scripture; religious liberty",
       "a personal, confessed, deliberate faith — and freedom of conscience before God",
       "Acts 2:38-41; Romans 6:3-4; Matthew 28:19-20", ["baptist", "1689", "believers baptism", "liberty"]),
    _c("Methodist / Wesleyan", "the Articles of Religion (Wesley); the Standard Sermons",
       "grace freely offered to all; the new birth; sanctification — real holiness of heart and life",
       "the pursuit of holiness and the reach of grace to every person, including the poor",
       "Titus 2:11-12; Hebrews 12:14; 1 Thessalonians 5:23", ["methodist", "wesleyan", "holiness", "sanctification"]),
    _c("Pentecostal / Charismatic", "the Statement of Fundamental Truths; the ancient creeds",
       "the present work of the Holy Spirit; the gifts; expectant prayer and worship",
       "a living expectation that the Spirit still moves, heals and empowers today",
       "Acts 2:1-4; 1 Corinthians 12:4-11; Joel 2:28", ["pentecostal", "charismatic", "spirit", "gifts"]),
    _c("Anabaptist", "the Schleitheim Confession (1527); the Dordrecht Confession",
       "discipleship as the shape of faith; the peace of Christ; a community set apart from the world's coercion",
       "the seriousness of following Jesus in daily life, and the ethic of peace and community",
       "Matthew 5:1-12; John 13:34-35; Romans 12:1-2", ["anabaptist", "mennonite", "discipleship", "peace"]),
    _c("Congregational / Free Church", "the Savoy Declaration (1658); the Cambridge Platform",
       "the local congregation gathered under Christ's headship; the priesthood of all believers",
       "the dignity and responsibility of the local body, ruled by Christ through his people",
       "Matthew 18:20; 1 Peter 2:9; Acts 14:23", ["congregational", "free church", "priesthood", "local"]),
]


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The churches — one Lord, many traditions, calibrated",
        "body": ("Every major tradition of the Church, gathered from its own confession and measured "
                 "against the one plumb-line: Scripture in the original tongues and the ecumenical creeds. "
                 "We calibrate, we do not judge — each tradition has kept a seed well; we name the gift and "
                 "the ground held in common (Ephesians 4:4-6: one body, one Spirit, one Lord, one faith)."),
        "source": {"label": "The churches, calibrated", "url": "", "domain": "theology", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["churches", "denominations", "traditions", "calibration", "ecumenical", "spine"],
        "subject": "the churches",
        "connections": [{"to_card_id": WORD, "relationship": "part_of",
                         "evidence": "the traditions of the one Church, rooted in the Word"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    cards = [spine] + TRADITIONS
    out = Path("data") / "church_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} traditions (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
