#!/usr/bin/env python3
"""Card the builders of the Floor — historians, scientists, mathematicians, credited with love.

Matt: "We also make sure we give credit to historians, and the scientists and mathematicians that
got a lot of things partially right or contributed. We will identify where their ideas fell short,
but again with love. We want to be magnanimous."

So each card is MAGNANIMOUS: it names the real gift generously (what they got right, what they
built, what they contributed to the Floor of Discovery), names honestly and specifically where the
idea fell short — never hidden, for we do not fear the light — and holds the whole person with love.
"Expose but do not humiliate; we don't lie, but we love you." Many of these builders were themselves
worshippers who understood their work as thinking God's thoughts after Him; that witness is part of
the credit. Calibrated against the one plumb-line, not judged. Conduit: gathered + attributed,
generated=False. Nested under a builders spine -> the Floor of Discovery. Git-tracked (small).

    PYTHONPATH=src python tools/card_contributors.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_builders"
_slug = re.compile(r"[^a-z0-9]+")


def _sk(s):
    return _slug.sub("_", s.lower()).strip("_")


def _c(name, field, era, gift, shortfall, love, bands):
    body = (f"{name} ({era}) — {field}. The gift: {gift}. Where it fell short: {shortfall}. Held with "
            f"love: {love}. (Credited magnanimously and measured against the one plumb-line — not judged; "
            f"a builder of the Floor of Discovery, honored for the truth kept and told the truth in love.)")
    return {
        "id": f"card_builder_{_sk(name)}", "kind": "reference", "title": name[:180], "body": body,
        "source": {"label": "The builders of the Floor — credited with love, calibrated to the plumb-line",
                   "url": "", "domain": "history of ideas", "authority_tier": "reference"},
        "shelf": "builders", "box": field,
        "bands": ["builder", "contributor", "calibration", "magnanimous", field.lower()] + list(bands),
        "subject": name,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a builder of the Floor, credited with love"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"field": field, "era": era, "gift": gift, "shortfall": shortfall, "love": love},
    }


BUILDERS = [
    # — Historians —
    _c("Herodotus", "history", "c. 484–425 BC",
       "he founded the discipline itself — the first to gather testimony systematically and ask WHY events happened, not merely that they did",
       "he was often credulous with his sources and wove in marvels and hearsay he could not check",
       "he asked the founding question and preserved a world that would otherwise be lost; the Father of History earned the title",
       ["herodotus", "greek", "father of history"]),
    _c("Thucydides", "history", "c. 460–400 BC",
       "the critical method — evidence weighed, speeches reconstructed, cause distinguished from pretext; the first rigorously secular history",
       "his lens of power-as-the-only-mover is real but partial; it cannot see providence, mercy, or the God who topples the strong",
       "his honesty about human nature is a gift to every historian who came after; he told the plague as he saw it",
       ["thucydides", "greek", "critical method"]),
    _c("Eusebius of Caesarea", "history", "c. 260–340 AD",
       "the first church history — he preserved documents, letters and martyr-accounts that would otherwise have perished",
       "his closeness to imperial power sometimes tipped his account toward the triumphal and the hagiographic",
       "without his labor much of the early Church's memory would be gone; he kept the record",
       ["eusebius", "church history", "patristic"]),
    _c("Ibn Khaldun", "history", "1332–1406 AD",
       "the Muqaddimah founded the philosophy of history and proto-sociology — asabiyyah (social cohesion) as the engine of the rise and fall of dynasties",
       "his cyclical determinism can flatten the singular and the providential into mere pattern",
       "a mind centuries ahead of its time, seeking the lawful order beneath the chaos of events",
       ["ibn khaldun", "muqaddimah", "sociology"]),
    _c("Edward Gibbon", "history", "1737–1794 AD",
       "the monumental Decline and Fall — narrative history at its most magisterial, built on wide and careful sources",
       "his Enlightenment hostility colored his thesis, blaming Christianity for Rome's fall where the evidence is far more tangled",
       "a craftsman of the historian's art whose prose and diligence still instruct; we take the gold and leave the bias",
       ["gibbon", "decline and fall", "rome"]),
    # — Scientists / natural philosophers —
    _c("Aristotle", "science", "384–322 BC",
       "he founded systematic inquiry across biology, logic, physics and ethics — the very framework of ordered knowledge, and a taxonomy of life unmatched for two millennia",
       "his physics reasoned from principles without experiment, so it was largely wrong (falling bodies, the geocentric spheres); the error froze science where his authority reigned",
       "the scaffolding of nearly all later learning is his; the Schoolmen were right to call him simply 'the Philosopher'",
       ["aristotle", "logic", "biology", "natural philosophy"]),
    _c("Claudius Ptolemy", "science", "c. 100–170 AD",
       "predictive mathematical astronomy — the Almagest 'saved the appearances' and forecast the heavens accurately for 1400 years",
       "he put the earth at the center; the math was ingenious but modeled the wrong frame, needing ever more epicycles to hold",
       "right mathematics around a wrong center is still a monument of disciplined observation; he gave the world its first working sky-model",
       ["ptolemy", "almagest", "astronomy", "geocentric"]),
    _c("Johannes Kepler", "science", "1571–1630 AD",
       "the three laws of planetary motion — he broke the 2000-year spell of the circle and found the ellipse, uniting physics and astronomy",
       "he clung long to a mysticism of nested Platonic solids and astrology before the data pried him loose",
       "he called science 'thinking God's thoughts after Him' and worshipped as he calculated; his awe is a model, not an embarrassment",
       ["kepler", "planetary motion", "ellipse", "astronomy"]),
    _c("Isaac Newton", "science", "1643–1727 AD",
       "universal gravitation, the calculus, the laws of motion, foundational optics — arguably the widest single leap in the history of science",
       "privately he held an anti-Trinitarian (Arian) theology and poured years into alchemy that bore no fruit; his gift did not extend to every claim he made",
       "he wrote more on Scripture than on physics and knew himself 'a boy playing on the seashore' before the great ocean of truth; humility crowned the genius",
       ["newton", "gravitation", "calculus", "optics"]),
    _c("Michael Faraday", "science", "1791–1867 AD",
       "electromagnetic induction and the field concept — the foundation of every motor, generator and the electrical age itself, all from a self-taught bookbinder",
       "little fell short in his science; his refusal of honors and wealth even cost him worldly standing",
       "a devout, humble believer who saw the study of nature as reading the second book of God; his character matched his gift",
       ["faraday", "induction", "fields", "electromagnetism"]),
    _c("James Clerk Maxwell", "science", "1831–1879 AD",
       "the unification of electricity, magnetism and light into four equations — the template for every later unification in physics",
       "little fell short; even his statistical mechanics opened doors he did not live to walk through",
       "a devout Christian who prayed over his work and kept a childlike faith beside a towering intellect; Einstein said he stood on Maxwell's shoulders",
       ["maxwell", "electromagnetism", "equations", "light"]),
    _c("Charles Darwin", "science", "1809–1882 AD",
       "patient, honest observation of variation and natural selection — a real mechanism, carefully evidenced, that reshaped biology",
       "he extrapolated far past his evidence to a universal story that excluded design, and he himself confessed the eye gave him 'a cold shudder'",
       "an honest naturalist wracked by the very questions he raised; we credit the observation and calibrate the overreach, in love",
       ["darwin", "natural selection", "biology", "variation"]),
    _c("Louis Pasteur", "science", "1822–1895 AD",
       "germ theory, vaccination, pasteurization, the fall of spontaneous generation — he saved untold millions of lives",
       "little fell short in his science; his disputes with rivals could be sharp",
       "'the more I study nature, the more I stand amazed at the work of the Creator'; his faith and his rigor grew together",
       ["pasteur", "germ theory", "vaccination", "microbiology"]),
    _c("Albert Einstein", "science", "1879–1955 AD",
       "special and general relativity — a re-founding of space, time and gravity, and one of the deepest unifications ever achieved",
       "he resisted quantum indeterminacy to the end ('God does not play dice') and confessed only an impersonal, Spinozist God, not the living One",
       "his awe before 'the comprehensibility of the universe' was genuine reverence; he stood at the door of worship even where he did not enter",
       ["einstein", "relativity", "spacetime", "gravity"]),
    # — Mathematicians —
    _c("Pythagoras", "mathematics", "c. 570–495 BC",
       "the insight that number and ratio structure reality — music, geometry and the cosmos bound by proportion",
       "his school hardened into a secretive cult, and legend says the discovery of irrational numbers was suppressed as a scandal",
       "the intuition that the world is written in number is profoundly true and points beyond itself to a Mind that ordered it",
       ["pythagoras", "number", "ratio", "geometry"]),
    _c("Euclid", "mathematics", "c. 300 BC",
       "the axiomatic method — the Elements built all of geometry from a handful of postulates by proof, the model of rigor for 2000 years",
       "he assumed the parallel postulate as self-evident; twenty-two centuries later that single gap opened the whole world of non-Euclidean geometry",
       "the discipline of 'from few clear truths, by valid steps, to certain conclusions' is one of humanity's greatest instruments; it is the shape of the moat itself",
       ["euclid", "elements", "axioms", "geometry"]),
    _c("Archimedes", "mathematics", "c. 287–212 BC",
       "the method of exhaustion (proto-calculus), hydrostatics, the lever, and pi bounded by rigor — genius that would not be equaled for eighteen centuries",
       "his work was so far ahead that much of it was lost or unread for a millennium; the age could not carry it forward",
       "he pursued truth for its own beauty ('do not disturb my circles'); the palimpsest recovering his lost method is a small resurrection",
       ["archimedes", "exhaustion", "hydrostatics", "pi"]),
    _c("Al-Khwarizmi", "mathematics", "c. 780–850 AD",
       "algebra as a discipline and the very word 'algorithm' (from his name) — the systematic solving of equations that underlies all computation",
       "the work was procedural and rhetorical, without the symbolic notation that later made it soar",
       "he gathered and advanced Greek and Indian mathematics and handed the world a tool it has never set down",
       ["al-khwarizmi", "algebra", "algorithm"]),
    _c("Blaise Pascal", "mathematics", "1623–1662 AD",
       "probability theory (with Fermat), the mechanical calculator, projective geometry, and foundational work on pressure and the vacuum",
       "some find his famous Wager a thin ground for faith, reasoning toward God as a bet rather than a Person",
       "after a night of fire he sewed the 'Memorial' into his coat — 'the God of Abraham, not of the philosophers'; his heart knew what his proofs could only point at",
       ["pascal", "probability", "pensees", "wager"]),
    _c("Gottfried Wilhelm Leibniz", "mathematics", "1646–1716 AD",
       "the calculus (independently, with the notation we still use), binary arithmetic, and the dream of a universal calculus of reasoning",
       "his 'best of all possible worlds' was caricatured as naive optimism, and his metaphysics of monads few could follow",
       "he sought a 'characteristica universalis' to make truth computable to the glory of God — a vision the digital age partly fulfilled",
       ["leibniz", "calculus", "binary", "logic"]),
    _c("Leonhard Euler", "mathematics", "1707–1783 AD",
       "the most prolific mathematician in history — analysis, number theory, graph theory, notation (e, i, f(x), and the identity that binds them)",
       "his boundless productivity sometimes outran full rigor, later generations tightening what his intuition leapt past",
       "a devout Lutheran who worked and worshipped to the last, blind and still dictating theorems; faith and fruitfulness in one life",
       ["euler", "analysis", "number theory", "notation"]),
    _c("Georg Cantor", "mathematics", "1845–1918 AD",
       "set theory and the transfinite — he made the infinite an object of rigorous mathematics, with orders of infinity beyond counting",
       "his work met fierce rejection, and he suffered breakdowns under the strain and the opposition",
       "he saw the transfinite as a finite reflection of the Absolute Infinite, which he identified with God; his mathematics was, to him, worship",
       ["cantor", "set theory", "infinity", "transfinite"]),
    _c("Kurt Gödel", "mathematics", "1906–1978 AD",
       "the incompleteness theorems — the proof that any sufficient formal system holds truths it cannot itself prove: no system can be its own complete ground",
       "his later years were shadowed by paranoia that ended in tragedy; the mind that mapped the limits of systems could not always order his own life",
       "he believed in God, drafted a formal ontological argument, and gave the world the keystone: every system must point beyond itself — the humility theorem",
       ["godel", "incompleteness", "logic", "keystone"]),
    _c("Alan Turing", "mathematics", "1912–1954 AD",
       "the theory of computation — the Turing machine defined what an algorithm is and founded computer science; his codebreaking helped end a war",
       "his reductive 'imitation game' framing of the mind sells short what a person is; a machine's mimicry is not a soul",
       "a brilliant, wounded man whom his own nation treated with cruelty; we hold his memory with grief and honor, and take the gift he gave",
       ["turing", "computation", "algorithm", "machine"]),
]


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The builders of the Floor — credited with love",
        "body": ("The historians, scientists and mathematicians who mapped the Floor of Discovery, each "
                 "credited MAGNANIMOUSLY: the real gift honored generously, the shortfall named honestly "
                 "and never hidden, the whole person held with love. Many were worshippers who understood "
                 "their work as thinking God's thoughts after Him; that is part of the credit. We calibrate "
                 "against the one plumb-line, we do not judge — 'we don't lie, but we love you' (Ephesians "
                 "4:15: speaking the truth in love). Every good and perfect gift is from above (James 1:17), "
                 "and the truth any of them told is the Lord's, wherever it was found."),
        "source": {"label": "The builders of the Floor, credited with love", "url": "",
                   "domain": "history of ideas", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["builders", "contributors", "historians", "scientists", "mathematicians", "magnanimous", "spine"],
        "subject": "the builders of the Floor",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "those who mapped the Floor of Discovery, credited with love"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    cards = [spine] + BUILDERS
    out = Path("data") / "contributors_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} builders (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
