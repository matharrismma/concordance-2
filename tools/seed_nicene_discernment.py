#!/usr/bin/env python3
"""The Nicene confession on the one map: the line of historic Christian faith, and where groups depart.

Matt, 2026-10-11: the "Church Denominations History" tree marks some bodies (LDS, Jehovah's Witnesses,
Christian Science, Oneness Pentecostalism) outside historic Christianity. We render that HONESTLY, as
the engine must: never a stamp, never a verdict on any person's standing before God (that is the
Lord's alone). We state a SPECIFIC, SOURCED departure from the Nicene confession - the historic
plumb-line of the Church - citing the creed's own clause and the group's OWN published doctrine, and
we mark it PROPOSED (calibrate, not judge; expose but do not humiliate - we love you).

Nothing here is sealed. A creedal confession is CITED, never a sealed theorem - the engine seals math
and structure, never a theological verdict (theology_doctrine.py itself: "NOT an attestation that the
doctrine is TRUE ... the truth is in the Word and in Christ, not in this tool"). The engine's
theology_doctrine verifier (witness surface) can STRUCTURALLY confirm two of these departures (the
Holy Spirit named as a person; a bodily resurrection) and is cited as the signpost; the essence-level
departures (one substance; three persons vs. modes) it cannot decide and so are cited to the creed.

All marks are CITED (exclusion / note). Rooted to the test of the spirits (1 John 4:1-3) and the faith
once delivered (Jude 3). Placed on the Church-history floor. Idempotent (TS.create slug + _mint_marks
dedup).

    PYTHONPATH=src python tools/seed_nicene_discernment.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_church_history"

QUESTION = "The Nicene confession - the line of historic Christian faith, and where groups depart from it"
STATEMENT = ("The historic Church confesses the Nicene faith: one God in three co-equal, co-eternal persons; "
             "the Son true God of true God, of one substance (homoousios) with the Father; the Holy Spirit the "
             "Lord and giver of life. A body that denies this confession, by its own doctrine, departs from the "
             "historic Christian line - named here from its own words, as a proposed discernment, never a verdict "
             "on any person.")

CREED = ("the Nicene Creed (325/381); Matthew 28:19; John 1:1-14; 2 Corinthians 13:14; "
         "src/concordance/verifiers/theology_doctrine.py")

MARKS = [
    ("note",
     "[the plumb-line, cited] The Nicene Creed (381) is the historic confession of the whole Church: one God the "
     "Father Almighty, maker of heaven and earth; one Lord Jesus Christ, the only-begotten Son, God of God, Light "
     "of Light, true God of true God, begotten not made, of ONE SUBSTANCE (homoousios) with the Father; and the "
     "Holy Spirit, the Lord and giver of life, who with the Father and the Son together is worshipped and "
     "glorified. Three co-equal, co-eternal persons, one God. This is the line every tradition on "
     "card_floor_church_history confesses in common (Ephesians 4:4-6).",
     {"source": CREED}),
    ("note",
     "[the method, cited - how we discern] Test the spirits (1 John 4:1-3): the confession of Jesus Christ come in "
     "the flesh. Contend for the faith once for all delivered (Jude 3). A confession is within the historic line "
     "when it confesses the Nicene faith; a departure is named by the group's OWN published doctrine against the "
     "creed's own clause. The engine PROPOSES (authority 'proposed'), it does not judge; it names a departure from "
     "a CONFESSION, never a person's standing before God. Expose, but do not humiliate.",
     {"source": "1 John 4:1-3; Jude 3; src/concordance/discern.py (authority is always 'proposed')"}),
    ("exclusion",
     "[Jehovah's Witnesses - departs, cited] By their own doctrine the Holy Spirit is God's impersonal active "
     "force (not a third divine person), and the Son is the first created being (an Arian Christology). This names "
     "fewer than three co-equal persons and denies the Son's being true God of true God - a departure from the "
     "Nicene 'one substance, three persons.' The engine's theology_doctrine.trinitarian_formula structurally "
     "confirms that a confession naming only the Father and the Son is not the complete Nicene formula (the "
     "signpost); the attribution is cited to their own publications.",
     {"source": "Watch Tower Bible and Tract Society doctrinal publications (Let God Be True; Should You Believe "
                "in the Trinity?); the Nicene Creed (325/381); John 1:1; theology_doctrine.trinitarian_formula"}),
    ("exclusion",
     "[The Church of Jesus Christ of Latter-day Saints - departs, cited] By their own doctrine (the Articles of "
     "Faith; Doctrine and Covenants 130:22) the Father, the Son and the Holy Ghost are three separate beings, the "
     "Father has a body of flesh and bones, and exalted humans may become gods - with additional scripture (the "
     "Book of Mormon, D&C, Pearl of Great Price) received. This denies the Nicene 'one substance' (homoousios) and "
     "the historic confession of one God. The persons are NAMED, so the structural naming test alone cannot decide "
     "this; the departure is cited to the creed's 'one substance' clause and the group's own doctrine.",
     {"source": "The Articles of Faith; Doctrine and Covenants 130:22; the Nicene Creed (325/381) - homoousios"}),
    ("exclusion",
     "[Christian Science - departs, cited] By its own doctrine (M. B. Eddy, Science and Health with Key to the "
     "Scriptures) matter, sin, sickness and death are unreal, and the resurrection of Christ was a spiritual "
     "demonstration, not the raising of a body. This departs from the bodily resurrection the historic faith "
     "confesses - 'a spirit hath not flesh and bones, as ye see me have' (Luke 24:39; John 20:27). The engine's "
     "theology_doctrine.bodily_resurrection structurally confirms that a non-bodily resurrection is not the "
     "confessed bodily one (the signpost); cited to Eddy's own text.",
     {"source": "M. B. Eddy, Science and Health with Key to the Scriptures (1875, public domain); Luke 24:39; "
                "John 20:27; theology_doctrine.bodily_resurrection"}),
    ("exclusion",
     "[Oneness Pentecostalism - departs, cited] By its own doctrine (the 'Oneness' or 'Jesus Only' teaching) God "
     "is one person who manifests in three modes or offices (Father, Son, Spirit) successively - modalism - rather "
     "than three co-eternal persons. This denies the Nicene three-person confession. As with naming, the modes are "
     "labelled, so the structural test alone cannot decide it; the departure is cited to the creed's three-person "
     "clause and the group's own teaching.",
     {"source": "United Pentecostal Church International, Fundamental Doctrine (the Oneness of God); the Nicene "
                "Creed (325/381) - three persons; Matthew 28:19; 2 Corinthians 13:14"}),
    ("note",
     "[the charity and the limit, cited] This names departures from a CONFESSION, in each group's own published "
     "words, measured against the historic creed - not a judgment of any person, which belongs to the Lord. The "
     "engine seals none of it: a creedal confession is cited, never a sealed theorem. The structural checks it can "
     "make (the Spirit named as a person; a bodily resurrection) are a signpost on the witness surface, not the "
     "verdict; the truth is in the Word and in Christ, not in this tool. We expose but do not humiliate: we don't "
     "lie, but we love you.",
     {"source": "src/concordance/verifiers/theology_doctrine.py; tools/card_churches.py (calibrate, not judge)"}),
]


def main() -> int:
    import tick
    from concordance import roots, tickstick as TS

    sid = TS.create(QUESTION, STATEMENT, "theology")["id"]
    print("stick id:", sid)
    tick._mint_marks(sid, MARKS, by="tools/seed_nicene_discernment.py")

    # anchor the range AND its opening verse (the Console weaves one verse at a time)
    a = roots.anchor("stick:" + sid, ["1 John 4:1-3", "1 John 4:1", "Jude 1:3"], by="proposed",
                     why="test the spirits; the faith once for all delivered", data_dir=DATA)
    print("  roots.anchor ->", a)
    p = roots.place("stick:" + sid, FLOOR, by="proposed",
                    why="the Nicene line and its departures, on the Church-history floor", data_dir=DATA)
    print("  roots.place  ->", p)
    # read the marks back (the capstone lesson: confirm what was minted)
    rec = TS.read(sid) if hasattr(TS, "read") else None
    if isinstance(rec, dict):
        print("  marks kept:", len(rec.get("marks", [])), "| fit:", (rec.get("fit") or {}).get("inferred", "")[:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
