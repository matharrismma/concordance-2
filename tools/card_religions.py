#!/usr/bin/env python3
"""Card the nations' faiths as FORESHADOW — the seeds of the Word, fulfilled in Christ, held in love.

Matt: "Same with the religions of the world that came before Christianity, at least where they
contributed positively. My belief is these were given to foreshadow Christ, but we don't hide from
the fulfillment of the foreshadow for the light. Also that anything that came after is anti-christ."

This is the Areopagus charter (Acts 17): God scattered seeds and shadows among the nations to prepare
them — the logos spermatikos of Justin Martyr, the shadow whose substance is Christ (Colossians
2:16-17), the true Light that enlightens everyone (John 1:9). So each pre-Christian faith is credited
MAGNANIMOUSLY where it contributed positively — the seed it kept, the ache it named, the shadow it
cast — and then the fulfillment is named plainly, for we do not hide the light for fear of the dark.

The calibration principle for what came AFTER is Matt's, carried faithfully and anchored on Scripture:
the objective test of the spirits (1 John 4:2-3; 2:22; 2 John 7) — whether a teaching confesses or
DENIES Jesus Christ, the Son, come in the flesh. This tests SPIRITS and TEACHINGS, never persons or
peoples; it is held with deep love, and the door to the fulfillment always stands open. "We don't
lie, but we love you." Conduit: gathered + attributed, generated=False. Nested under a foreshadow
spine -> the Word. Git-tracked (small).

    PYTHONPATH=src python tools/card_religions.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

WORD = "card_k_spine_the_word"
SPINE = "card_spine_foreshadows"


def _card(sid, title, body, box, bands, extra, subject=None):
    return {
        "id": f"card_foreshadow_{sid}", "kind": "reference", "title": title[:180], "body": body,
        "source": {"label": "The nations' foreshadows — gathered in love, calibrated to the Word (Acts 17)",
                   "url": "", "domain": "religion", "authority_tier": "reference"},
        "shelf": "foreshadows", "box": box,
        "bands": ["foreshadow", "religion", "calibration", "praeparatio", "acts17"] + list(bands),
        "subject": subject or title,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a shadow among the nations, whose substance is Christ"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": extra,
    }


def _fore(sid, name, era, seed, shortfall, fulfillment, bands):
    body = (f"{name} ({era}). The seed it kept: {seed}. Where the shadow fell short: {shortfall}. The "
            f"fulfillment (named, not hidden — we do not fear the light): {fulfillment}. (Credited in "
            f"love as a foreshadow — praeparatio evangelica, Acts 17:23; the shadow whose substance is "
            f"Christ, Colossians 2:17.)")
    return _card(sid, name, body, "foreshadow", ["pre-christian"] + list(bands),
                 {"era": era, "seed": seed, "shortfall": shortfall, "fulfillment": fulfillment}, subject=name)


PRINCIPLES = [
    _card("praeparatio_evangelica",
          "Praeparatio evangelica — the foreshadow and the fulfillment",
          ("The principle beneath this whole shelf: God did not leave the nations without witness (Acts "
           "14:17). He wrote his law on every heart (Romans 2:14-15), showed his power in what is made "
           "(Romans 1:19-20), and set the times and places of the nations 'that they should seek God, and "
           "perhaps feel their way toward him' (Acts 17:26-27). So among the peoples he scattered SEEDS of "
           "the Word (Justin Martyr's logos spermatikos) and SHADOWS of the thing to come (Colossians "
           "2:16-17) — the true Light that enlightens everyone (John 1:9) breaking in refracted. We honor "
           "the seed and the shadow generously; and because a shadow exists only where a body casts it, we "
           "name the Body plainly. We do not hide the fulfillment for fear of the light — that would be to "
           "love the shadow more than the One who cast it."),
          "principle", ["praeparatio", "logos spermatikos", "shadow", "fulfillment", "acts17", "justin martyr"],
          {"anchor": "Acts 17:23-28; Colossians 2:16-17; John 1:9; Romans 1:19-2:15"}),
    _card("the_test_of_the_spirits",
          "The test of the spirits — 1 John 4:2-3 (held in love)",
          ("The calibration for what came AFTER Christ, carried as Matt's framing and anchored on the text: "
           "'By this you know the Spirit of God: every spirit that confesses that Jesus Christ has come in "
           "the flesh is from God, and every spirit that does not confess Jesus is not from God. This is the "
           "spirit of the antichrist' (1 John 4:2-3; cf. 2:22, 'the liar is the one who denies that Jesus is "
           "the Christ'; 2 John 7). The foreshadows PREPARED for the Son; a teaching that arises after him and "
           "DENIES the Son — his incarnation, his death, his deity — is, by this test, of the antichrist "
           "spirit. Three guardrails, kept strictly: (1) the test is of SPIRITS and TEACHINGS, never of "
           "persons or peoples — we love every soul and condemn none; (2) it is stated with grief, not "
           "triumph — 'we don't lie, but we love you'; (3) the door stands open — the invitation is always "
           "toward the Son the shadow was pointing at all along."),
          "principle", ["test of the spirits", "antichrist", "1 john", "denial of the son", "in love"],
          {"anchor": "1 John 4:2-3; 1 John 2:22; 2 John 7"}),
    _card("the_root_israel",
          "Israel and the Hebrew Scriptures — not a shadow but the root and the promise",
          ("Set apart from the foreshadows in kind, and honored above them: the covenant with Abraham, the "
           "Law and the Prophets are not a distant shadow among the nations but the very ROOT and PROMISE — "
           "the cultivated olive tree onto which the nations were grafted (Romans 11:17-24). To Israel belong "
           "'the adoption, the glory, the covenants, the giving of the law, the worship, and the promises' "
           "(Romans 9:4-5); they were entrusted with the very oracles of God (Romans 3:2). Every foreshadow "
           "elsewhere is dim; here the light is direct — 'beginning with Moses and all the Prophets, he "
           "interpreted... the things concerning himself' (Luke 24:27). We hold this people and this "
           "Scripture with the deepest honor, and the fulfillment we name is not a rival but the homecoming "
           "the Prophets themselves foretold — Messiah, the consolation of Israel (Luke 2:25-32)."),
          "root", ["israel", "hebrew scriptures", "covenant", "olive tree", "romans 11", "honor"],
          {"anchor": "Romans 11:17-24; Romans 9:4-5; Luke 24:27"}),
]


FORESHADOWS = [
    _fore("greek_philosophy", "Greek philosophy (Platonism & the unmoved mover)", "c. 6th–4th c. BC",
          "the intuition of a transcendent Good, the eternal Forms behind appearances, a divine Reason "
          "(logos) ordering all things, and an 'unknown god' beyond the idols (Acts 17:23)",
          "its God was impersonal and its Logos a principle, never a Person; it reasoned toward the divine "
          "but could not be reconciled to it",
          "'In the beginning was the Logos, and the Logos was with God, and the Logos was God... and the "
          "Logos became flesh' (John 1:1,14) — the principle the philosophers glimpsed is a Person who came",
          ["plato", "logos", "forms", "unknown god"]),
    _fore("stoicism", "Stoicism", "c. 3rd c. BC onward",
          "conscience and natural law, a providence governing all, the divine logos indwelling the world, "
          "and the brotherhood of all humanity — Paul quotes their poets: 'in him we live and move and have "
          "our being... for we are indeed his offspring' (Acts 17:28)",
          "it made the logos pantheistic and impersonal, and sought salvation in self-sufficiency and "
          "detachment rather than in grace and love",
          "the law written on the heart (Romans 2:15) is fulfilled by the Spirit given, not the will "
          "steeled; the offspring the Stoics named can become sons by adoption (Galatians 4:5)",
          ["stoic", "natural law", "conscience", "providence"]),
    _fore("zoroastrianism", "Zoroastrianism", "c. 1200–600 BC",
          "one wise Lord (Ahura Mazda), a real moral struggle of good against evil, a coming Savior "
          "(Saoshyant), the resurrection of the body and a final judgment — and the Magi who read the "
          "heavens and came to worship the newborn King (Matthew 2:1-11)",
          "it framed the struggle as a dualism of two near-coequal principles, rather than one sovereign "
          "God over a defeated evil",
          "the awaited Savior came, the resurrection it hoped for was accomplished first-fruits in Christ "
          "(1 Corinthians 15:20-23), and its own wise men were led to the manger",
          ["zoroaster", "magi", "resurrection", "saoshyant", "judgment"]),
    _fore("egyptian", "Ancient Egyptian religion (Ma'at)", "c. 3000–30 BC",
          "Ma'at — truth, justice and cosmic order as the will of heaven — and a vivid expectation of "
          "judgment after death, the heart weighed against the feather of truth",
          "it scattered the one order among many gods and trusted in spells and magic to pass the judgment",
          "there is a judgment, and a heart no spell can make light — but 'there is now no condemnation for "
          "those who are in Christ Jesus' (Romans 8:1), whose righteousness is credited, not weighed and "
          "found wanting",
          ["egypt", "maat", "judgment", "order"]),
    _fore("mesopotamian", "Mesopotamian religion (Sumer, Babylon)", "c. 3000–500 BC",
          "the earliest written law codes binding a people to justice, a keen sense of cosmic order, and a "
          "preserved memory of the great Flood carried in its epics",
          "its gods were capricious and quarreling, and its Flood was remembered as myth, its true shape "
          "distorted",
          "the Law finds its ground not in a king's stele but in the God who gives it (Exodus 20), and the "
          "Flood it half-remembered is told true in Genesis 6-9 — with a covenant and a bow of mercy in the "
          "cloud",
          ["sumer", "babylon", "law code", "flood", "gilgamesh"]),
    _fore("vedic_hindu", "Vedic religion and early Hinduism", "c. 1500 BC onward",
          "rita, the cosmic moral order; sacrifice placed at the very center of worship; and a deep, "
          "unquenched hunger for union with the divine and the unseen",
          "it dissolved the personal Creator into an impersonal Absolute and set the soul on endless cycles "
          "of rebirth to be escaped, not a body to be raised",
          "the sacrifice the altars reached toward is offered once for all in Christ (Hebrews 10:10), and the "
          "hunger for the divine is met not by absorption but by adoption — 'that they may be one, as we are "
          "one' (John 17:22)",
          ["hinduism", "vedic", "rita", "sacrifice"]),
    _fore("buddhism", "Buddhism", "c. 5th c. BC",
          "an unflinching diagnosis of the human condition — that life as we grasp it is shot through with "
          "suffering (dukkha) — profound compassion, and a refusal to rest in the emptiness of created idols",
          "it found no personal God to cry to and no Redeemer to send, and set the goal as the extinction of "
          "the self (nirvana) rather than communion with the Living One",
          "the suffering it named so honestly is real (Romans 8:20-22), but the answer is not to be blown out "
          "like a candle — it is a Man of Sorrows who bore it (Isaiah 53:3-4) and a self not annihilated but "
          "raised",
          ["buddhism", "dukkha", "suffering", "compassion", "nirvana"]),
    _fore("chinese", "Chinese traditions — Confucianism & Daoism", "c. 6th–5th c. BC",
          "the moral order and the cultivation of virtue, filial reverence, the rectification of names — and, "
          "in Daoism, 'the Way' (the Dao): an ineffable Source from which all things flow, and the wisdom of "
          "yielding (wu wei)",
          "the moral order had no covenant-keeping Person behind it, and the Way was a principle, nameless "
          "and impersonal, never a Someone who could be known or followed home",
          "'I am the Way' (John 14:6) — the Dao the sages reached toward has a face and a name; the order "
          "written on the heart is kept by the One who wrote it and now indwells",
          ["confucius", "daoism", "the way", "dao", "virtue"]),
    _fore("mystery_dying_rising", "The dying-and-rising motif in the mysteries", "antiquity",
          "the deep, near-universal human intuition — carried in Osiris, Dionysus, Tammuz and others — that "
          "life is somehow won through death, and that a god might die and live again",
          "these were myths without a date, a place, or a witness — seasonal dreams, not events; they longed "
          "for what they could not make true",
          "the pattern every culture dreamed became FACT in one place at one hour — 'the true myth' (C.S. "
          "Lewis): crucified under Pontius Pilate, raised the third day, seen by five hundred at once (1 "
          "Corinthians 15:4-6). The shadows dreamed it; Christ did it",
          ["mystery religions", "osiris", "dionysus", "true myth", "dying and rising"]),
    _fore("primal_witness", "Primal religion and the 'unknown god'", "all ages",
          "the near-universal witness of conscience, the awe before creation, and the reaching-after of every "
          "people 'in the hope that they might feel their way toward him and find him' (Acts 17:27) — the "
          "altar to the unknown god on every hill",
          "left to itself it slid toward idols, exchanging the glory of the immortal God for images (Romans "
          "1:23), feeling after a God it could not name",
          "'What therefore you worship as unknown, this I proclaim to you' (Acts 17:23) — the God felt-after "
          "in the dark has drawn near and made himself known in his Son",
          ["primal", "unknown god", "conscience", "areopagus"]),
]


AFTER = [
    _card("islam_under_the_test",
          "Islam under the test of the spirits (Matt's framing, anchored, in love)",
          ("Credited where it contributes positively: a strict and serious monotheism, a deep reverence "
           "before God, moral earnestness, the honoring of many prophets, and a call to prayer and mercy. "
           "And then, held to the one test in love: arising in the 7th century AD, after Christ, it "
           "explicitly denies the crucifixion ('they did not kill him... but it was made to appear so to "
           "them', Qur'an 4:157) and denies the Sonship and deity of Christ (Surah 112; 5:72-75) — which is "
           "precisely the confession that 1 John 4:2-3 and 1 John 2:22 make the dividing line. So by Matt's "
           "framing, carried faithfully, a teaching that denies the Son come in the flesh bears the "
           "antichrist spirit named in that test. This is said of the DOCTRINE'S denial, never of any Muslim "
           "soul — every one of whom is loved, and for whom the door to the fulfillment stands wide open. "
           "'We don't lie, but we love you': the cross the Qur'an calls an appearance is the very place the "
           "love of God was proven (Romans 5:8)."),
          "under_the_test", ["islam", "test of the spirits", "denial of the crucifixion", "in love", "1 john"],
          {"anchor": "1 John 4:2-3; 1 John 2:22; John 3:16; Romans 5:8", "framing": "Matt's, anchored"}),
    _card("post_christ_pattern",
          "The pattern for movements arising after Christ (the test, in love)",
          ("Beyond any single case, the calibration is a pattern, applied gently: a religion or movement that "
           "arises AFTER Christ and redefines, demotes, or denies the Son — his full deity, his incarnation, "
           "his atoning death and resurrection — falls under the test of 1 John 4:2-3, whatever real goods it "
           "also carries (community, discipline, moral seriousness). We name the denial honestly and credit "
           "the goods generously; we never pronounce on the standing of any person before God, which is his "
           "alone to judge (Romans 14:4). The foreshadows before Christ ache toward him; a teaching after "
           "him is measured by whether it confesses him. In both directions the compass points to one place, "
           "and the invitation is the same: come to the Son."),
          "under_the_test", ["post-christ", "pattern", "test of the spirits", "in love", "1 john"],
          {"anchor": "1 John 4:2-3; Romans 14:4"}),
]


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The nations' foreshadows — seeds of the Word, fulfilled in Christ",
        "body": ("Every faith of the nations that came before Christ, credited MAGNANIMOUSLY where it "
                 "contributed positively and read as a foreshadow — the seeds of the Word scattered among the "
                 "peoples (Acts 17), the shadow whose substance is Christ (Colossians 2:17), the true Light "
                 "refracted (John 1:9). We honor the seed and name the fulfillment plainly, for we do not hide "
                 "the light. What arose after Christ is measured by the test of the spirits — whether it "
                 "confesses or denies the Son come in the flesh (1 John 4:2-3) — carried as Matt's framing, "
                 "anchored on the text, and held always in love: the door to the fulfillment stands open to "
                 "all. 'We don't lie, but we love you.'"),
        "source": {"label": "The nations' foreshadows, calibrated to the Word (Acts 17)", "url": "",
                   "domain": "religion", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["foreshadows", "religions", "praeparatio", "acts17", "test of the spirits", "fulfillment", "spine"],
        "subject": "the nations' foreshadows",
        "connections": [{"to_card_id": WORD, "relationship": "part_of",
                         "evidence": "the seeds and shadows among the nations, rooted in and fulfilled by the Word"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    cards = [spine] + PRINCIPLES + FORESHADOWS + AFTER
    out = Path("data") / "religions_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(PRINCIPLES)} principles + {len(FORESHADOWS)} foreshadows + {len(AFTER)} under-the-test "
          f"(+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
