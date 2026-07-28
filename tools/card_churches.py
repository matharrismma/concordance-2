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
    _c("Seventh-day Adventist", "the 28 Fundamental Beliefs; the ancient creeds' core affirmed",
       "the seventh-day Sabbath; the soon return of Christ; whole-person health and stewardship",
       "the blessed hope kept vivid — a people who live expecting Him, and who care for the body as a temple",
       "Exodus 20:8-11; Titus 2:13; Revelation 14:12", ["adventist", "sabbath", "second coming", "health"]),
    _c("Restoration Movement (Churches of Christ / Disciples)", "the Declaration and Address (1809) — 'no creed but Christ, no book but the Bible'",
       "the restoration of New Testament Christianity; believer's baptism; weekly communion; the unity of all Christians",
       "the longing to be simply Christian — Scripture alone as the pattern, and unity as the goal",
       "John 17:20-21; Acts 2:42; 1 Corinthians 1:10", ["restoration", "churches of christ", "disciples", "unity"]),
    _c("Evangelical / Interdenominational", "the Lausanne Covenant (1974); the ancient creeds' core",
       "the new birth; the authority of Scripture; the urgency of world evangelization across every denomination",
       "the gospel carried across every church boundary — cooperation in the one message",
       "John 3:3; Romans 1:16; Matthew 24:14", ["evangelical", "lausanne", "evangelism", "interdenominational"]),
]


# ── The voices — one per tradition, chosen by THEIR reckoning ───────────────────────────────────
# Matt, 2026-07-27/28: "We identify a major voice for each denomination and church philosophy. We
# use them as a frame but always point to Christ. We are honest on both ends." And: "Think of us as
# a knowledge logistical system. One system meant to unify the church. all of the church."
#
# A broker never manufactures the goods. Each voice is chosen by the TRADITION'S own reckoning (who
# they themselves hold up), carried with its waybill: the gift the whole church receives, the
# HONEST note (what is contested, or what the voice got wrong — stated plainly and charitably,
# never hidden and never used to humiliate), and the voice's own Christ-ward resolution. Every card
# ends at the same Person. Quotable text only where public domain; living-memory figures carry
# facts and a pointer, never reproduced text.

def _v(name, dates, tradition, reckoning, gift, honest, resolves, ref, pd_status, bands):
    body = (f"{name} ({dates}) — the voice of the {tradition} tradition, by its own reckoning: "
            f"{reckoning}. The gift the whole church receives: {gift}. Honest on both ends: "
            f"{honest}. And the voice itself resolves to Christ: {resolves} ({ref}). "
            f"[{pd_status}]")
    return {
        "id": f"card_voice_{_sk(name)}", "kind": "reference", "title": f"{name} — {tradition}",
        "body": body,
        "source": {"label": "The voices of the traditions — chosen by their own reckoning", "url": "",
                   "domain": "theology", "authority_tier": "reference"},
        "shelf": "churches", "box": "voice",
        "bands": ["voice", "church", tradition.lower().split()[0], "witness"] + list(bands),
        "subject": name,
        "connections": [
            {"to_card_id": SPINE, "relationship": "member_of",
             "evidence": "a voice of the one Church, carried with its waybill"},
            {"to_card_id": f"card_church_{_sk(tradition)}", "relationship": "figure_of",
             "evidence": f"the voice this tradition itself holds up"},
        ],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"dates": dates, "tradition": tradition, "reckoning": reckoning, "gift": gift,
                  "honest_note": honest, "resolves_to_christ": resolves, "ref": ref,
                  "pd_status": pd_status},
    }


VOICES = [
    _v("Athanasius of Alexandria", "c. 296-373", "The ecumenical creeds — the shared ground",
       "the defender of Nicene faith when nearly the whole world wavered — 'Athanasius contra mundum'",
       "that the Son is true God of true God — the confession every tradition below still shares",
       "his fierceness in controversy was real; exiles were mutual and the era's polemics were harsh on all sides",
       "'He became what we are, that He might make us what He is' — the whole point is Christ",
       "John 1:14", "public domain (On the Incarnation and the festal letters are freely available)",
       ["athanasius", "nicaea", "incarnation"]),
    _v("John Chrysostom", "c. 347-407", "Eastern Orthodoxy",
       "the 'Golden-mouthed' preacher whose Divine Liturgy the Orthodox pray to this day",
       "preaching that weds Scripture to the poor — 'if you cannot find Christ in the beggar at the church door, you will not find Him in the chalice'",
       "his sermons against the Jews of Antioch are a real and grievous stain, named honestly by historians of every tradition",
       "his last words: 'Glory be to God for all things' — a life preached toward Christ",
       "Matthew 25:40", "public domain (homilies widely available)",
       ["chrysostom", "liturgy", "preaching", "the poor"]),
    _v("Thomas Aquinas", "1225-1274", "Roman Catholicism",
       "the Angelic Doctor — the tradition's own summa of faith seeking understanding",
       "the confidence that faith and reason are one gift from one God — grace perfects nature",
       "his system is held authoritative by Rome in a way the wider church does not bind itself to; he himself called it 'straw' beside what he saw of Christ",
       "at the end he left the Summa unfinished: 'I can write no more; all I have written seems like straw' — beside the Person he had met",
       "Philippians 3:8", "public domain (the Summa is freely available)",
       ["aquinas", "summa", "faith and reason"]),
    _v("Martin Luther", "1483-1546", "Lutheran",
       "the reformer the tradition bears the name of — the recovery of justification by faith",
       "that the gospel is a gift received, not a wage earned — grace alone, through faith alone",
       "his late writings against the Jews are indefensible and are repudiated by Lutheran bodies themselves — honesty requires saying so plainly",
       "'the cross alone is our theology' — everything he recovered points at Christ crucified",
       "Romans 1:17", "public domain (the catechisms, commentaries and hymns are freely available)",
       ["luther", "justification", "grace", "reformation"]),
    _v("John Calvin", "1509-1564", "Reformed / Presbyterian",
       "the Institutes' author — the tradition's systematic voice of God's sovereignty",
       "a God-centered vision of the whole of life, and rigorous submission of every claim to Scripture",
       "the execution of Servetus in Geneva happened with his concurrence; Reformed historians name it without excuse",
       "'we are not our own; we are God's' — the sovereignty he preached was Christ's claim on the whole person",
       "1 Corinthians 6:19-20", "public domain (the Institutes and commentaries are freely available)",
       ["calvin", "institutes", "sovereignty"]),
    _v("Thomas Cranmer", "1489-1556", "Anglican",
       "the Prayer Book's author — the cadences Anglicans have prayed for five centuries",
       "common prayer that catechizes a whole people — worship as formation",
       "he recanted under threat and then recanted his recantation at the stake, thrusting the offending hand into the fire first — a flawed man whose end was honest",
       "his collects gather every prayer 'through Jesus Christ our Lord' — the Book's constant resolution",
       "Colossians 3:16", "public domain (the Book of Common Prayer 1549/1552/1662)",
       ["cranmer", "prayer book", "collects"]),
    _v("Charles Spurgeon", "1834-1892", "Baptist",
       "the 'Prince of Preachers' — the voice Baptists themselves hold highest",
       "plain gospel preaching to ordinary people, and a pastor's heart for the poor and the orphan",
       "he broke fellowship in the Downgrade Controversy — some judge the break prophetic, others needlessly sharp; both readings are carried",
       "'I take my text and make a beeline to the cross' — his own stated method",
       "1 Corinthians 2:2", "public domain (thousands of sermons freely available — some already in this keeping)",
       ["spurgeon", "sermons", "gospel"]),
    _v("John Wesley", "1703-1791", "Methodist / Wesleyan",
       "the founder whose Standard Sermons the tradition made its doctrinal standard",
       "grace offered to every person, and holiness pursued as the real shape of salvation — faith working by love",
       "his marriage was unhappy and his organizational splits from Anglicanism were contested in his own lifetime — the tradition tells it honestly",
       "'the best of all is, God is with us' — his dying words, the whole method's resolution",
       "Hebrews 12:14", "public domain (sermons and journals freely available)",
       ["wesley", "holiness", "grace"]),
    _v("William J. Seymour", "1870-1922", "Pentecostal / Charismatic",
       "the Azusa Street revival's pastor — the fountainhead the tradition itself names",
       "the expectation that the Spirit still falls on all flesh — and a revival that crossed the color line when almost nothing else did",
       "the movement he birthed fractured along the very racial lines Azusa had crossed; the tradition's own historians grieve it",
       "he preached that the gifts exist to exalt Jesus, not the gifted — 'the baptism is to give you power to witness to Christ'",
       "Acts 1:8", "public domain (The Apostolic Faith papers, 1906-1908)",
       ["seymour", "azusa", "spirit", "revival"]),
    _v("Menno Simons", "1496-1561", "Anabaptist",
       "the shepherd the Mennonites bear the name of — discipleship under persecution",
       "that following Jesus is the substance of faith — peace, community, and a church that cannot coerce",
       "his strict church discipline (the ban) divided families and is debated within the tradition itself",
       "his motto, kept on every title page: 'No other foundation can any one lay than that which is laid, which is Jesus Christ'",
       "1 Corinthians 3:11", "public domain (the Foundation Book is freely available)",
       ["menno", "discipleship", "peace"]),
    _v("Jonathan Edwards", "1703-1758", "Congregational / Free Church",
       "America's theologian — the congregational tradition's towering mind and revival preacher",
       "the beauty and weight of God — religious affections tested by their fruit, not their heat",
       "he owned slaves; the tradition that honors his theology says so plainly and does not look away",
       "'The redeemed have all their inherent good in Christ' — his sermons return there relentlessly",
       "John 1:16", "public domain (the works are freely available)",
       ["edwards", "affections", "revival"]),
    _v("Ellen G. White", "1827-1915", "Seventh-day Adventist",
       "the messenger the tradition itself names — her counsels shaped its mission, schools and hospitals",
       "steadfastness on the Sabbath as gift, the soon return of Christ, and whole-person care for health",
       "Adventists hold her writings as an inspired lesser light; the wider church does not — both positions are stated, neither is flattened. Her own rule is kept: the Bible is the greater light by which the lesser is tested",
       "'lift up Jesus, the Man of Calvary, higher and still higher' — her constant charge",
       "John 12:32", "public domain (Steps to Christ, The Desire of Ages and more are freely available)",
       ["white", "adventist", "sabbath", "health"]),
    _v("Alexander Campbell", "1788-1866", "Restoration Movement (Churches of Christ / Disciples)",
       "the Restoration's chief editor and debater — 'where the Scriptures speak, we speak'",
       "the plea to be simply Christian — Scripture as the pattern and the unity of all believers as the aim",
       "the movement devoted to unity itself divided over instruments and societies; its own historians name the irony",
       "his plea's whole ground: the church rests on the one confession — 'Thou art the Christ, the Son of the living God'",
       "Matthew 16:16", "public domain (The Christian System is freely available)",
       ["campbell", "restoration", "unity"]),
    _v("Billy Graham", "1918-2018", "Evangelical / Interdenominational",
       "the evangelist the whole movement names first — crusades that preached to more people than any voice before him",
       "one simple message carried across every denominational line, with financial and personal integrity kept deliberately (the Modesto Manifesto)",
       "he later regretted political entanglements and said so himself; his recordings and books remain under copyright, so this card carries facts and a pointer, never his text",
       "his one sermon, by his own account: 'the Bible says' — and the invitation to come to Christ",
       "John 14:6", "NOT public domain (d. 2018) — no text reproduced; see the Billy Graham Evangelistic Association archives",
       ["graham", "evangelism", "crusades"]),
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
    cards = [spine] + TRADITIONS + VOICES
    # every voice's figure_of target must be a tradition card that exists — no dangling grafts
    ids = {c["id"] for c in cards}
    for v in VOICES:
        for l in v["connections"]:
            assert l["to_card_id"] in ids, f"{v['id']} points at missing {l['to_card_id']}"
    out = Path("data") / "church_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(TRADITIONS)} traditions + {len(VOICES)} voices (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
