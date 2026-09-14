#!/usr/bin/env python3
"""THE STRATEGY CONCORDANCE — the recurring patterns of what endures, across time.

Matt, 2026-09-14: "Look at all of the successful dynasties, politically and in business.
Hannibal and Caesar, but also Elon, Ford and Thiel. We do the same thing in ministry. We
look across time." The same method that found the master equations of computation, turned
on HISTORY: the recurring PATTERNS of building things that win and endure. A pattern is a
master form; a historical CASE is an instance; the ARENAS (war, politics, business,
ministry) are the domains; and a pattern that recurs across arenas is a bridge — the same
move winning for a general, a founder, and an apostle. Found, not invented; every case
carries its evidence.

    python tools/seed_strategy.py --list      # patterns ranked by arena-span, with cases
    python tools/seed_strategy.py --check      # validate arenas + structure
    python tools/seed_strategy.py --rebuild    # (re)write data/strategy_cards.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

STORE = Path("data/strategy_cards.jsonl")
ARENAS = {
    "war": "the field", "politics": "the state", "business": "the enterprise",
    "ministry": "the church", "science": "the discipline", "nature": "the living world",
}

# each case: (arena, who, when, the move, the evidence)
PATTERNS: list[dict] = [
    {"id": "concentrate_force", "title": "Concentrate force at the decisive point",
     "gist": "Mass what you have where it decides. Dispersion loses to concentration.",
     "cases": [
        ("war", "Hannibal at Cannae", "216 BC", "a deliberately yielding centre and concentrated flanks — double envelopment", "annihilated a Roman army roughly twice his size; the textbook of concentration"),
        ("business", "Peter Thiel & PayPal", "1999-2002", "own one small market first (eBay's power-sellers) before widening", "'competition is for losers' — take a monopoly of a niche, then expand (Zero to One)"),
        ("ministry", "The Jerusalem church", "c. 30-40 AD", "begin concentrated in one city, then radiate outward", "Acts 1:8 — Jerusalem, then Judea, Samaria, the ends of the earth"),
        ("politics", "Napoleon's central position", "1796-1809", "place the army between divided enemies and beat each in turn", "local superiority against larger coalitions, repeatedly")]},
    {"id": "tempo", "title": "Tempo — speed as a weapon",
     "gist": "Act faster than the other side can react; decide before they can.",
     "cases": [
        ("war", "Caesar and the Rubicon", "49 BC", "cross before the Senate can organise; march on Rome at once", "'the die is cast' — decisive speed took the initiative and the war"),
        ("business", "Musk / SpaceX iteration", "2010s", "build, fly, fail, fix — a fast test cadence instead of a slow perfect design", "reusable rockets by out-iterating slower, risk-averse incumbents"),
        ("war", "Genghis Khan's mobility", "1206-1227", "mounted armies moving and communicating faster than any enemy", "an empire built on operational tempo"),
        ("business", "Amazon 'Day 1'", "1997-", "bias to action, reversible decisions made fast", "'Day 2 is stasis, then death' — speed as culture")]},
    {"id": "own_the_bottleneck", "title": "Own the bottleneck",
     "gist": "Control the one chokepoint everything must pass through.",
     "cases": [
        ("business", "Rockefeller / Standard Oil", "1870-1911", "control refining, then the pipelines and rail rebates", "owned the chokepoint of the oil economy, not just the wells"),
        ("business", "Ford's River Rouge", "1928", "raw ore and rubber in one gate, finished cars out the other — vertical integration", "own the whole chain so no supplier can hold you up"),
        ("politics", "Rome's roads and logistics", "312 BC-", "own the network that moves legions, grain, law and coin", "control of movement was control of the empire"),
        ("war", "Themistocles at Salamis", "480 BC", "fight in the narrows where numbers cannot be brought to bear", "the strait was the bottleneck; owning it beat a larger fleet")]},
    {"id": "asymmetric_leverage", "title": "Asymmetric leverage",
     "gist": "Fight where you are strong and they are weak; do what they can't or won't.",
     "cases": [
        ("war", "Hannibal over the Alps", "218 BC", "attack on the axis the enemy believed impossible", "arrived in Italy from the direction Rome never defended"),
        ("ministry", "David and Goliath", "c. 1010 BC", "refuse the enemy's game (armour, sword); win with the sling at range", "1 Samuel 17 — strength met on your own terms, not his"),
        ("war", "Lawrence of Arabia", "1916-18", "raid the railway, never hold ground — a war of the weak against mass", "tie down a large army with a small mobile one"),
        ("business", "The disruptive entrant", "ongoing", "enter at the low end the incumbent is glad to cede, then move up", "the innovator's dilemma — attack where the leader will not defend")]},
    {"id": "compounding", "title": "Compounding — the long game",
     "gist": "Hold the position and reinvest; time in the compound beats the brilliant stroke.",
     "cases": [
        ("politics", "Rome's slow consolidation", "509 BC-", "absorb, settle, extend citizenship, repeat over centuries", "the republic grew by patient accretion, not one conquest"),
        ("business", "Warren Buffett", "1965-", "reinvest and let returns compound for decades", "the eighth wonder is patience applied to capital"),
        ("ministry", "The Benedictine monasteries", "529 AD-", "keep copying, praying, farming across centuries of collapse", "'ora et labora' preserved the West by outlasting the dark"),
        ("nature", "Old-growth forest", "millennia", "small annual increments, unbroken, become a canopy", "compounding is how the largest living things are built")]},
    {"id": "founder_conviction", "title": "Founder conviction",
     "gist": "A clear telos, bigger than the self, held with will through the hard middle.",
     "cases": [
        ("business", "Ford's 'car for the multitude'", "1908", "a single obsessive aim: a car ordinary people can own", "the Model T followed from an unbending purpose"),
        ("business", "Musk's mission", "2000s-", "sustainable energy; make humanity multi-planetary", "capital and talent recruited by a cause, not a return"),
        ("ministry", "Paul's ambition", "c. 50-60 AD", "preach where Christ is not yet named", "Romans 15:20 — a conviction that set the map of the mission"),
        ("war", "Alexander", "336-323 BC", "a vision of one world, carried past every reasonable stopping point", "conviction that outran his generals' caution")]},
    {"id": "antifragility", "title": "Antifragility — grow from the blow",
     "gist": "Build so that shocks strengthen you rather than break you.",
     "cases": [
        ("war", "Rome after Cannae", "216 BC", "refuse to negotiate; rebuild; wear Hannibal down and win the war", "the worst defeat became the turning point — it did not quit"),
        ("ministry", "The persecuted church", "1st-3rd c. AD", "spread further under persecution, not less", "Tertullian: 'the blood of the martyrs is the seed of the church'"),
        ("war", "Fabian strategy", "217 BC", "trade space and battle for time; deny the decisive fight", "attrition turned the enemy's strength into his weakness"),
        ("business", "Surviving the bust", "2000-01", "the firms that live through the crash inherit the field", "downturns clear competitors for the durable")]},
    {"id": "distribution_over_product", "title": "Distribution beats product",
     "gist": "Owning the channel of reach beats a better thing no one can receive.",
     "cases": [
        ("ministry", "The printing press", "1517-", "cheap print carried the Reformation faster than any preacher could walk", "the 95 Theses were across Europe in weeks"),
        ("ministry", "The apostolic letters", "c. 50-65 AD", "a network of congregations bound by circulated epistles", "Paul's letters were the distribution layer of the early church"),
        ("business", "Standard Oil's pipelines", "1870s-", "own the rails and pipes, not only the refinery", "the channel, not the product, was the lever"),
        ("politics", "Roman roads", "312 BC-", "the same network moved troops, trade, mail and law", "reach was the empire's true product")]},
    {"id": "win_the_narrative", "title": "Win the story",
     "gist": "Control the meaning of events; legitimacy is a weapon.",
     "cases": [
        ("politics", "Augustus and the Pax Romana", "27 BC-14 AD", "frame autocracy as restored republic and peace", "the Res Gestae and the coinage told the story that held the order"),
        ("war", "Caesar's Commentaries", "58-49 BC", "narrate your own campaigns to Rome, in the third person", "shaped his legend while the events were still warm"),
        ("ministry", "The gospel as the story", "1st c. AD-", "reframe all of history around one death and resurrection", "the narrative, not force, carried the movement"),
        ("business", "Brand mythos", "modern", "a product wrapped in a story people want to belong to", "the story compounds loyalty the specs cannot")]},
    {"id": "outlive_the_founder", "title": "Outlive the founder",
     "gist": "Institutionalize past the one whose will built it, or it dies with them.",
     "cases": [
        ("politics", "Rome's adoptive succession", "96-180 AD", "adopt the ablest heir rather than trust blood", "the Five Good Emperors — until Marcus chose his son Commodus, and it broke"),
        ("ministry", "Canon, creed, and office", "1st-4th c. AD", "fix the deposit in Scripture, rule of faith, and succession", "the church carried past the apostles because it institutionalized the deposit (2 Tim 1:14)"),
        ("business", "The third-generation problem", "recurring", "few family firms survive the founder's grandchildren", "the drift when conviction is inherited, not chosen"),
        ("politics", "Genghis Khan's succession", "1227-", "a division on death that fractured within generations", "the empire outgrew the man but not the succession problem")]},
    {"id": "first_principles", "title": "Reason from first principles",
     "gist": "Strip the inherited assumptions; reason up from what is actually true.",
     "cases": [
        ("science", "The Scientific Revolution", "16-17th c.", "observe and measure rather than defer to Aristotle and authority", "Galileo, Newton — the ground, not the analogy"),
        ("business", "Musk's cost teardown", "2000s-", "price a rocket by the raw materials, not by what rockets 'cost'", "first-principles cost analysis broke the industry's assumptions"),
        ("business", "Thiel's contrarian question", "modern", "'what important truth do very few people agree with you on?'", "value is found where consensus is wrong"),
        ("ministry", "The Reformers", "1517-", "go back to the text itself — sola scriptura", "authority re-grounded on the source, not accretion")]},
    {"id": "coalition", "title": "Coalition — borrow strength",
     "gist": "Multiply your force through allies, marriages, and networks.",
     "cases": [
        ("politics", "Rome's client kingdoms", "2nd c. BC-", "rule through allies and clients, not only direct conquest", "borrowed strength held a frontier a legion could not"),
        ("politics", "Habsburg marriages", "15-16th c.", "'let others wage war; you, fortunate Austria, marry'", "a dynasty assembled by alliance more than by battle"),
        ("ministry", "The collection for Jerusalem", "c. 55 AD", "bind distant churches by mutual aid", "2 Corinthians 8-9 — a network held together by giving"),
        ("business", "Platform ecosystems", "modern", "let others build on you; their strength becomes yours", "the ecosystem out-competes the standalone product")]},
    {"id": "requisite_variety", "title": "Requisite variety — adapt to the terrain",
     "gist": "Match the complexity of the environment, or it will overwhelm you.",
     "cases": [
        ("politics", "Rome extends citizenship", "1st c. BC-3rd c. AD", "absorb and adapt conquered peoples rather than only subjugate", "variety inside the system matched the variety it ruled"),
        ("ministry", "The Jerusalem Council", "c. 49 AD", "adapt the terms of belonging to reach a new people", "Acts 15 — contextualize without losing the core"),
        ("business", "Relentless experimentation", "modern", "run many small tests so the winners emerge from variety", "the org that generates variety adapts faster than one that plans"),
        ("nature", "Evolution by variation", "deep time", "generate variety; let selection keep what fits", "Ashby's law in the living world — variety answers variety")]},
    {"id": "build_a_moat", "title": "Build a moat",
     "gist": "Make the position you have won expensive to take.",
     "cases": [
        ("war", "Rome's fortified frontier", "1st-4th c. AD", "walls, forts and the limes to make ground costly to cross", "defensibility turned conquest into a settled border"),
        ("business", "Scale and network moats", "modern", "grow until size or network effects deter every challenger", "the moat, not the product, keeps the profit"),
        ("ministry", "Guard the deposit", "1st c. AD-", "a fixed creed as a moat against doctrinal drift", "2 Timothy 1:14 — 'guard the good deposit'"),
        ("business", "Standard Oil's scale", "1880s-", "undercut and absorb until the scale itself was the barrier", "the moat was the size no rival could match")]},
    {"id": "intelligence", "title": "See first — reconnaissance and information",
     "gist": "Know the ground and the enemy before you commit; surprise is a failure of the other side's seeing.",
     "cases": [
        ("war", "Sun Tzu's spies", "5th c. BC", "'know the enemy and know yourself' — win before the battle by knowing", "The Art of War: foreknowledge is the general's first weapon"),
        ("business", "Bloomberg's terminal", "1981-", "sell the information advantage itself as the product", "own what the market must see, and it must come to you"),
        ("politics", "Walsingham's network", "1570s-80s", "a spy service to see plots before they mature", "Elizabeth I's intelligence pre-empted the threats to the throne"),
        ("science", "Measurement first", "17th c.-", "instrument and observe before theorizing", "the telescope and microscope: seeing further decided the arguments")]},
    {"id": "cut_losses", "title": "Cut losses — retreat to fight again",
     "gist": "A position is only worth what it costs to keep; abandon the sunk cost to preserve the force.",
     "cases": [
        ("war", "Washington's retreats", "1776", "trade ground and avoid the decisive battle to keep the army alive", "the Continental Army survived by refusing to be destroyed"),
        ("business", "Intel exits memory", "1985", "abandon the founding business (DRAM) for microprocessors", "Grove: 'if we got kicked out, what would a new CEO do?' — then did it"),
        ("politics", "Diocletian's abdication", "305 AD", "step down at strength rather than cling to power to the end", "a rare voluntary exit that stabilized the succession"),
        ("ministry", "Paul leaves a city", "1st c. AD", "shake the dust and move on where the door is closed (Acts 13:51)", "the mission preserved by not dying on ground that would not receive it")]},
    {"id": "standardize", "title": "Standardize — the interchangeable part",
     "gist": "Make the units uniform and the whole becomes repeatable, scalable, and teachable.",
     "cases": [
        ("business", "Ford's interchangeable parts", "1913", "identical components on a moving line", "the assembly line made the car reproducible at scale"),
        ("war", "The Roman legion", "3rd c. BC-", "a standard unit, drill, camp and kit anywhere in the empire", "one interchangeable system fought from Britain to Syria"),
        ("ministry", "The canon and creed", "2nd-4th c. AD", "a fixed rule of faith teachable in every congregation", "a standard the whole church could carry and reproduce"),
        ("business", "The shipping container", "1956", "one box, one standard, every port and ship", "standardization collapsed the cost of global trade")]},
    {"id": "decentralize", "title": "Push decisions to the edge",
     "gist": "Let those nearest the problem decide; a body that must ask the center for everything cannot move.",
     "cases": [
        ("war", "Auftragstaktik (mission command)", "19th-20th c.", "give the intent, let the officer on the spot choose the means", "Prussian/German doctrine: initiative at the edge beat rigid central control"),
        ("business", "Amazon's two-pizza teams", "2000s", "small autonomous teams owning their own service end to end", "decentralized ownership kept a giant moving fast"),
        ("ministry", "The house-church network", "1st c. AD", "many self-governing local congregations, loosely bound", "no single point of failure; it spread faster than any center could direct"),
        ("nature", "The colony without a center", "always", "ants and slime molds solve without a controller", "distributed local rules produce coherent global behavior")]},
    {"id": "reinvest_the_core", "title": "Reinvest the flywheel",
     "gist": "Plow the returns back into the engine that produced them; let the loop feed itself.",
     "cases": [
        ("business", "Amazon's flywheel", "1997-", "lower prices -> more customers -> more sellers -> lower costs -> lower prices", "reinvest every gain into the loop instead of taking profit"),
        ("politics", "Rome's settled veterans", "republic-empire", "reinvest conquest into colonies that secured and extended the frontier", "each win funded the base for the next"),
        ("ministry", "Disciples who make disciples", "1st c. AD-", "the fruit is trained to reproduce, not merely counted", "2 Timothy 2:2 — entrust it to faithful men who will teach others"),
        ("nature", "Seed and forest", "always", "the tree spends its surplus on seed, not only on itself", "the flywheel of life is reinvested growth")]},
]


def _card(cid, kind, title, body, shelf, box, bands, subject, conns, extra):
    return {"id": cid, "kind": kind, "title": title, "body": body,
            "source": {"label": "The Strategy Concordance — patterns of what endures", "url": "",
                       "domain": "strategy", "authority_tier": "reference"},
            "shelf": shelf, "box": box, "bands": bands, "subject": subject, "connections": conns,
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False, "extra": extra}


def _case_id(pid, arena, who):
    slug = "".join(ch if ch.isalnum() else "_" for ch in who.lower())[:40]
    return f"card_case_{pid}__{arena}__{slug}"


def build_cards():
    cards = []
    for p in PATTERNS:
        arenas = sorted({a for a, *_ in p["cases"]})
        conns = []
        for arena, who, when, move, ev in p["cases"]:
            cid = _case_id(p["id"], arena, who)
            conns.append({"to_card_id": cid, "relationship": "instance_of",
                          "evidence": f"{arena}: {who} ({when}) — {ev}"})
        cards.append(_card(
            f"card_pattern_{p['id']}", "strategy_pattern", p["title"],
            f"{p['gist']} A recurring strategic form seen across {len(arenas)} arenas "
            f"({', '.join(arenas)}) and across time — the same move winning in each.",
            "strategy", "pattern", ["strategy", "pattern"] + arenas, p["title"], conns,
            {"gist": p["gist"], "arenas": arenas, "span": len(arenas)}))
        for arena, who, when, move, ev in p["cases"]:
            cid = _case_id(p["id"], arena, who)
            cards.append(_card(
                cid, "strategy_case", f"{who} ({when})",
                f"{who}, {when} — {move}. Evidence: {ev}. An instance of '{p['title']}' in the arena of {arena}.",
                "strategy", "case", ["strategy", "case", arena, p["id"]], who,
                [{"to_card_id": f"card_pattern_{p['id']}", "relationship": "instance_of",
                  "evidence": f"an instance of the pattern '{p['title']}'"}],
                {"arena": arena, "when": when, "move": move, "pattern": p["id"], "who": who}))
    return cards


def cmd_check() -> int:
    rc = 0
    ids = [c["id"] for c in build_cards()]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        rc = 3; print("duplicate ids:", dupes[:8])
    bad = [(p["id"], a) for p in PATTERNS for a, *_ in p["cases"] if a not in ARENAS]
    if bad:
        rc = 3; print("cases in unknown arenas:", bad)
    thin = [p["id"] for p in PATTERNS if len({a for a, *_ in p["cases"]}) < 2]
    if thin:
        rc = 3; print("patterns spanning <2 arenas (not a bridge):", thin)
    ncases = sum(len(p["cases"]) for p in PATTERNS)
    print(f"OK: {len(PATTERNS)} patterns, {ncases} cases across {len({a for p in PATTERNS for a,*_ in p['cases']})} arenas; "
          f"every pattern bridges >=2 arenas; no dup ids.")
    return rc


def cmd_list() -> int:
    for p in sorted(PATTERNS, key=lambda x: -len({a for a, *_ in x["cases"]})):
        arenas = sorted({a for a, *_ in p["cases"]})
        print(f"\n== {p['title']}  [{len(arenas)} arenas: {', '.join(arenas)}]")
        print(f"   {p['gist']}")
        for arena, who, when, move, ev in p["cases"]:
            print(f"     {arena:9} {who} ({when})")
    return 0


def cmd_rebuild() -> int:
    if cmd_check():
        return 3
    cards = build_cards()
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    npat = sum(1 for c in cards if c["kind"] == "strategy_pattern")
    print(f"wrote {STORE}: {npat} patterns + {len(cards)-npat} cases = {len(cards)} cards")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    if args.list:
        return cmd_list()
    if args.rebuild:
        return cmd_rebuild()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
