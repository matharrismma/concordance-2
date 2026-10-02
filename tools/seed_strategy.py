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
FLOOR = "card_k_floor_of_discovery"
SPINE_ID = "card_spine_strategy"        # The Strategy Concordance — roots the patterns to the Floor
ARENAS = {
    "war": "the field", "politics": "the state", "business": "the enterprise",
    "ministry": "the church", "science": "the discipline", "nature": "the living world",
}

# each case: (arena, who, when, the move, the evidence)
PATTERNS: list[dict] = [
    {"id": "concentrate_force", "title": "Concentrate force at the decisive point",
     "gist": "Mass what you have where it decides. Dispersion loses to concentration.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', "Lee at Gettysburg — Pickett's Charge", '3 July 1863', 'massed ~12,500 men on the Union centre at Cemetery Ridge after a bombardment', 'concentration against a PREPARED decisive point: ~50% of the assaulting force lost in under an hour; the mass was the target, not the lever'),
        ('business', 'Quibi', '2020', '$1.75 billion concentrated on one product — mobile-only short-form video', 'the single point was the wrong one: shut down six months after launch; concentration cannot rescue a bet the market did not want'),
     ],
     "cases": [
        ("war", "Hannibal at Cannae", "216 BC", "a deliberately yielding centre and concentrated flanks — double envelopment", "annihilated a Roman army roughly twice his size; the textbook of concentration"),
        ("business", "Peter Thiel & PayPal", "1999-2002", "own one small market first (eBay's power-sellers) before widening", "'competition is for losers' — take a monopoly of a niche, then expand (Zero to One)"),
        ("ministry", "The Jerusalem church", "c. 30-40 AD", "begin concentrated in one city, then radiate outward", "Acts 1:8 — Jerusalem, then Judea, Samaria, the ends of the earth"),
        ("politics", "Napoleon's central position", "1796-1809", "place the army between divided enemies and beat each in turn", "local superiority against larger coalitions, repeatedly")]},
    {"id": "tempo", "title": "Tempo — speed as a weapon",
     "gist": "Act faster than the other side can react; decide before they can.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'Napoleon in Russia', '1812', 'a lightning advance to Moscow to force a decision before winter', 'tempo outran supply: ~600,000 crossed the Niemen, under 100,000 returned; speed without the line of supply is a march into the void'),
        ('business', 'Webvan', '1999–2001', 'built warehouses and fleets in 26 cities at once, ahead of demand', '$800M+ spent before the market existed; bankrupt July 2001 — speed is a weapon only when it outruns the ENEMY, not the customer'),
     ],
     "cases": [
        ("war", "Caesar and the Rubicon", "49 BC", "cross before the Senate can organise; march on Rome at once", "'the die is cast' — decisive speed took the initiative and the war"),
        ("business", "Musk / SpaceX iteration", "2010s", "build, fly, fail, fix — a fast test cadence instead of a slow perfect design", "reusable rockets by out-iterating slower, risk-averse incumbents"),
        ("war", "Genghis Khan's mobility", "1206-1227", "mounted armies moving and communicating faster than any enemy", "an empire built on operational tempo"),
        ("business", "Amazon 'Day 1'", "1997-", "bias to action, reversible decisions made fast", "'Day 2 is stasis, then death' — speed as culture")]},
    {"id": "own_the_bottleneck", "title": "Own the bottleneck",
     "gist": "Control the one chokepoint everything must pass through.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Standard Oil', '1870–1911', 'owned refining, pipelines and rail rebates — the bottleneck of the whole trade', 'the choke invited the state: Standard Oil v. United States (1911) broke it into 34 companies — a bottleneck too total provokes its own breaking'),
        ('politics', 'Britain and France at Suez', '1956', 'seized the Canal Zone to keep the bottleneck in their hands', 'the United States and the USSR forced withdrawal within weeks; a bottleneck held without the strength of the greater powers is a hostage, not an asset'),
     ],
     "cases": [
        ("business", "Rockefeller / Standard Oil", "1870-1911", "control refining, then the pipelines and rail rebates", "owned the chokepoint of the oil economy, not just the wells"),
        ("business", "Ford's River Rouge", "1928", "raw ore and rubber in one gate, finished cars out the other — vertical integration", "own the whole chain so no supplier can hold you up"),
        ("politics", "Rome's roads and logistics", "312 BC-", "own the network that moves legions, grain, law and coin", "control of movement was control of the empire"),
        ("war", "Themistocles at Salamis", "480 BC", "fight in the narrows where numbers cannot be brought to bear", "the strait was the bottleneck; owning it beat a larger fleet")]},
    {"id": "asymmetric_leverage", "title": "Asymmetric leverage",
     "gist": "Fight where you are strong and they are weak; do what they can't or won't.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'Operation Market Garden', 'September 1944', 'a narrow airborne thrust to seize the Rhine bridges and shorten the war', "the surprise was lost (German armour at Arnhem was reported and discounted); 1st Airborne destroyed — 'a bridge too far'"),
        ('politics', 'The Bay of Pigs', 'April 1961', '1,400 exiles to spark an uprising with deniable backing', 'no surprise (the plan was known), no uprising, no air cover: crushed in three days — leverage assumes a reaction that never came'),
     ],
     "cases": [
        ("war", "Hannibal over the Alps", "218 BC", "attack on the axis the enemy believed impossible", "arrived in Italy from the direction Rome never defended"),
        ("ministry", "David and Goliath", "c. 1010 BC", "refuse the enemy's game (armour, sword); win with the sling at range", "1 Samuel 17 — strength met on your own terms, not his"),
        ("war", "Lawrence of Arabia", "1916-18", "raid the railway, never hold ground — a war of the weak against mass", "tie down a large army with a small mobile one"),
        ("business", "The disruptive entrant", "ongoing", "enter at the low end the incumbent is glad to cede, then move up", "the innovator's dilemma — attack where the leader will not defend")]},
    {"id": "compounding", "title": "Compounding — the long game",
     "gist": "Hold the position and reinvest; time in the compound beats the brilliant stroke.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Long-Term Capital Management', '1994–1998', 'compounded small spreads with 25:1+ leverage', 'the Russian default (1998) reversed the spreads; a $3.6B rescue — compounding on leverage compounds the loss as fast as the gain'),
        ('business', 'Sears', '1886–2018', 'a century of compounded retail dominance (catalogue, stores, credit)', 'the core eroded under discount and online rivals; bankruptcy 2018 — compounding stops the day the thing being compounded stops being wanted'),
     ],
     "cases": [
        ("politics", "Rome's slow consolidation", "509 BC-", "absorb, settle, extend citizenship, repeat over centuries", "the republic grew by patient accretion, not one conquest"),
        ("business", "Warren Buffett", "1965-", "reinvest and let returns compound for decades", "the eighth wonder is patience applied to capital"),
        ("ministry", "The Benedictine monasteries", "529 AD-", "keep copying, praying, farming across centuries of collapse", "'ora et labora' preserved the West by outlasting the dark"),
        ("nature", "Old-growth forest", "millennia", "small annual increments, unbroken, become a canopy", "compounding is how the largest living things are built")]},
    {"id": "founder_conviction", "title": "Founder conviction",
     "gist": "A clear telos, bigger than the self, held with will through the hard middle.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Theranos', '2003–2018', 'unshakable conviction in a device that could run hundreds of tests on a finger-prick', 'the device never worked; investors and patients deceived; the founder convicted of fraud (2022) — conviction without a working thing is a lie with a long fuse'),
        ('war', 'Custer at the Little Bighorn', '25 June 1876', 'attacked at once, dividing his regiment, certain the village would scatter', 'the village was the largest ever gathered on the plains; five companies annihilated — conviction overrode reconnaissance'),
     ],
     "cases": [
        ("business", "Ford's 'car for the multitude'", "1908", "a single obsessive aim: a car ordinary people can own", "the Model T followed from an unbending purpose"),
        ("business", "Musk's mission", "2000s-", "sustainable energy; make humanity multi-planetary", "capital and talent recruited by a cause, not a return"),
        ("ministry", "Paul's ambition", "c. 50-60 AD", "preach where Christ is not yet named", "Romans 15:20 — a conviction that set the map of the mission"),
        ("war", "Alexander", "336-323 BC", "a vision of one world, carried past every reasonable stopping point", "conviction that outran his generals' caution")]},
    {"id": "antifragility", "title": "Antifragility — grow from the blow",
     "gist": "Build so that shocks strengthen you rather than break you.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Nokia', '2007–2013', 'met the iPhone blow with the existing platform and process', 'the blow did not strengthen: from ~50% smartphone share to the sale of the handset business to Microsoft (2013) — a shock only builds what was already able to change'),
        ('war', 'Carthage after Zama', '202–146 BC', 'absorbed defeat and rebuilt trade and wealth', 'the recovery provoked the third war; Carthage was razed (146 BC) — a rival that cannot be allowed to grow back is not antifragile, it is marked'),
     ],
     "cases": [
        ("war", "Rome after Cannae", "216 BC", "refuse to negotiate; rebuild; wear Hannibal down and win the war", "the worst defeat became the turning point — it did not quit"),
        ("ministry", "The persecuted church", "1st-3rd c. AD", "spread further under persecution, not less", "Tertullian: 'the blood of the martyrs is the seed of the church'"),
        ("war", "Fabian strategy", "217 BC", "trade space and battle for time; deny the decisive fight", "attrition turned the enemy's strength into his weakness"),
        ("business", "Surviving the bust", "2000-01", "the firms that live through the crash inherit the field", "downturns clear competitors for the durable")]},
    {"id": "distribution_over_product", "title": "Distribution beats product",
     "gist": "Owning the channel of reach beats a better thing no one can receive.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Blockbuster', '2000–2010', 'the largest rental distribution network in the world; declined to buy Netflix for $50M (2000)', 'distribution of the wrong form: the stores became the cost; bankrupt 2010 while the mail-and-stream rival it refused grew'),
        ('business', 'Kodak', '1975–2012', 'unmatched film distribution and retail; shelved its own digital camera (1975)', 'distribution bound to a product that was ending; Chapter 11 in 2012 — a channel cannot save what it is built to carry'),
     ],
     "cases": [
        ("ministry", "The printing press", "1517-", "cheap print carried the Reformation faster than any preacher could walk", "the 95 Theses were across Europe in weeks"),
        ("ministry", "The apostolic letters", "c. 50-65 AD", "a network of congregations bound by circulated epistles", "Paul's letters were the distribution layer of the early church"),
        ("business", "Standard Oil's pipelines", "1870s-", "own the rails and pipes, not only the refinery", "the channel, not the product, was the lever"),
        ("politics", "Roman roads", "312 BC-", "the same network moved troops, trade, mail and law", "reach was the empire's true product")]},
    {"id": "win_the_narrative", "title": "Win the story",
     "gist": "Control the meaning of events; legitimacy is a weapon.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'The United States in Vietnam', '1965–1973', 'won nearly every set-piece battle and reported progress', 'lost the story: the Tet Offensive (1968) was a military defeat for the North and a narrative defeat for Washington; the war was lost at home'),
        ('business', 'New Coke', '1985', "re-told the brand as 'new' on the strength of blind taste tests", "the public's story of the old Coke beat the test data; reversed in 79 days — a narrative cannot be won against the one people already hold"),
     ],
     "cases": [
        ("politics", "Augustus and the Pax Romana", "27 BC-14 AD", "frame autocracy as restored republic and peace", "the Res Gestae and the coinage told the story that held the order"),
        ("war", "Caesar's Commentaries", "58-49 BC", "narrate your own campaigns to Rome, in the third person", "shaped his legend while the events were still warm"),
        ("ministry", "The gospel as the story", "1st c. AD-", "reframe all of history around one death and resurrection", "the narrative, not force, carried the movement"),
        ("business", "Brand mythos", "modern", "a product wrapped in a story people want to belong to", "the story compounds loyalty the specs cannot")]},
    {"id": "outlive_the_founder", "title": "Outlive the founder",
     "gist": "Institutionalize past the one whose will built it, or it dies with them.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', "Alexander's empire", '323 BC', "no named heir — 'to the strongest'", 'the Diadochi tore the empire into warring kingdoms within a generation — the greatest conquest in history outlived its founder by nothing'),
        ('politics', 'Yugoslavia after Tito', '1980–1991', "a federation held together by one man's authority", 'the institution was the man; a decade after his death the state dissolved in war'),
     ],
     "cases": [
        ("politics", "Rome's adoptive succession", "96-180 AD", "adopt the ablest heir rather than trust blood", "the Five Good Emperors — until Marcus chose his son Commodus, and it broke"),
        ("ministry", "Canon, creed, and office", "1st-4th c. AD", "fix the deposit in Scripture, rule of faith, and succession", "the church carried past the apostles because it institutionalized the deposit (2 Tim 1:14)"),
        ("business", "The third-generation problem", "recurring", "few family firms survive the founder's grandchildren", "the drift when conviction is inherited, not chosen"),
        ("politics", "Genghis Khan's succession", "1227-", "a division on death that fractured within generations", "the empire outgrew the man but not the succession problem")]},
    {"id": "first_principles", "title": "Reason from first principles",
     "gist": "Strip the inherited assumptions; reason up from what is actually true.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('science', 'Lysenkoism', '1930s–1960s', "'reasoned' agriculture from ideology, rejecting Mendelian genetics", 'crop failures, the ruin of Soviet biology, geneticists imprisoned — first principles that are false reason straight to disaster'),
        ('business', 'Juicero', '2016–2017', 'engineered a $400 press from first principles for proprietary juice bags', 'the bags could be squeezed by hand (Bloomberg, 2017); shut down within the year — reasoning from the wrong first question'),
     ],
     "cases": [
        ("science", "The Scientific Revolution", "16-17th c.", "observe and measure rather than defer to Aristotle and authority", "Galileo, Newton — the ground, not the analogy"),
        ("business", "Musk's cost teardown", "2000s-", "price a rocket by the raw materials, not by what rockets 'cost'", "first-principles cost analysis broke the industry's assumptions"),
        ("business", "Thiel's contrarian question", "modern", "'what important truth do very few people agree with you on?'", "value is found where consensus is wrong"),
        ("ministry", "The Reformers", "1517-", "go back to the text itself — sola scriptura", "authority re-grounded on the source, not accretion")]},
    {"id": "coalition", "title": "Coalition — borrow strength",
     "gist": "Multiply your force through allies, marriages, and networks.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'The Third Coalition at Austerlitz', '2 December 1805', 'Austria and Russia united their armies against Napoleon', 'divided command and a plan each ally read differently; routed in a day — a coalition without one will is two armies'),
        ('politics', 'The Delian League', '478–404 BC', "Athens' alliance of Aegean cities against Persia", "became an empire; the allies' revolts and the Peloponnesian War ended Athenian power (404 BC) — borrowed strength taken rather than kept is lost"),
     ],
     "cases": [
        ("politics", "Rome's client kingdoms", "2nd c. BC-", "rule through allies and clients, not only direct conquest", "borrowed strength held a frontier a legion could not"),
        ("politics", "Habsburg marriages", "15-16th c.", "'let others wage war; you, fortunate Austria, marry'", "a dynasty assembled by alliance more than by battle"),
        ("ministry", "The collection for Jerusalem", "c. 55 AD", "bind distant churches by mutual aid", "2 Corinthians 8-9 — a network held together by giving"),
        ("business", "Platform ecosystems", "modern", "let others build on you; their strength becomes yours", "the ecosystem out-competes the standalone product")]},
    {"id": "requisite_variety", "title": "Requisite variety — adapt to the terrain",
     "gist": "Match the complexity of the environment, or it will overwhelm you.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'Singapore', 'February 1942', 'fortress guns and plans pointed to the sea', 'the Japanese came down the Malay peninsula through the jungle; 80,000 surrendered — a defence with one answer meets the question it did not ask'),
        ('business', 'BlackBerry', '2007–2013', 'held to the physical keyboard and the enterprise niche as touchscreens took the market', 'from ~50% US share to under 1%; variety the market demanded was refused'),
     ],
     "cases": [
        ("politics", "Rome extends citizenship", "1st c. BC-3rd c. AD", "absorb and adapt conquered peoples rather than only subjugate", "variety inside the system matched the variety it ruled"),
        ("ministry", "The Jerusalem Council", "c. 49 AD", "adapt the terms of belonging to reach a new people", "Acts 15 — contextualize without losing the core"),
        ("business", "Relentless experimentation", "modern", "run many small tests so the winners emerge from variety", "the org that generates variety adapts faster than one that plans"),
        ("nature", "Evolution by variation", "deep time", "generate variety; let selection keep what fits", "Ashby's law in the living world — variety answers variety")]},
    {"id": "build_a_moat", "title": "Build a moat",
     "gist": "Make the position you have won expensive to take.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'The Maginot Line', 'May 1940', 'the strongest fortified line ever built, along the German border', 'walked around through the Ardennes; France fell in six weeks — a moat defends only the ground it covers'),
        ('business', 'Encyclopædia Britannica', '1768–2012', 'two centuries of authority and a door-to-door sales moat', 'Encarta then Wikipedia made the moat irrelevant; print edition ended 2012 — a moat around a form the world stops using is a monument'),
     ],
     "cases": [
        ("war", "Rome's fortified frontier", "1st-4th c. AD", "walls, forts and the limes to make ground costly to cross", "defensibility turned conquest into a settled border"),
        ("business", "Scale and network moats", "modern", "grow until size or network effects deter every challenger", "the moat, not the product, keeps the profit"),
        ("ministry", "Guard the deposit", "1st c. AD-", "a fixed creed as a moat against doctrinal drift", "2 Timothy 1:14 — 'guard the good deposit'"),
        ("business", "Standard Oil's scale", "1880s-", "undercut and absorb until the scale itself was the barrier", "the moat was the size no rival could match")]},
    {"id": "intelligence", "title": "See first — reconnaissance and information",
     "gist": "Know the ground and the enemy before you commit; surprise is a failure of the other side's seeing.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('war', 'Stalin before Barbarossa', 'June 1941', 'held multiple warnings of the invasion date (Sorge, British intelligence, deserters)', 'disbelieved them all; the Red Army was caught deployed forward and unready — intelligence held but not believed is none'),
        ('business', 'Decca rejects the Beatles', '1 January 1962', 'an audition heard and judged', "'guitar groups are on the way out' — the information was in the room and misread; the group signed with EMI within months"),
     ],
     "cases": [
        ("war", "Sun Tzu's spies", "5th c. BC", "'know the enemy and know yourself' — win before the battle by knowing", "The Art of War: foreknowledge is the general's first weapon"),
        ("business", "Bloomberg's terminal", "1981-", "sell the information advantage itself as the product", "own what the market must see, and it must come to you"),
        ("politics", "Walsingham's network", "1570s-80s", "a spy service to see plots before they mature", "Elizabeth I's intelligence pre-empted the threats to the throne"),
        ("science", "Measurement first", "17th c.-", "instrument and observe before theorizing", "the telescope and microscope: seeing further decided the arguments")]},
    {"id": "cut_losses", "title": "Cut losses — retreat to fight again",
     "gist": "A position is only worth what it costs to keep; abandon the sunk cost to preserve the force.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Concorde', '1962–2003', 'kept funding a programme whose economics were known to be broken', "never recovered its cost; the 'Concorde fallacy' is named for it — sunk cost kept the losses running for forty years"),
        ('war', 'Verdun', '1916', 'neither side would yield the ground once blood was spent on it', '~700,000 casualties for a front that barely moved — the refusal to cut losses became the loss'),
     ],
     "cases": [
        ("war", "Washington's retreats", "1776", "trade ground and avoid the decisive battle to keep the army alive", "the Continental Army survived by refusing to be destroyed"),
        ("business", "Intel exits memory", "1985", "abandon the founding business (DRAM) for microprocessors", "Grove: 'if we got kicked out, what would a new CEO do?' — then did it"),
        ("politics", "Diocletian's abdication", "305 AD", "step down at strength rather than cling to power to the end", "a rare voluntary exit that stabilized the succession"),
        ("ministry", "Paul leaves a city", "1st c. AD", "shake the dust and move on where the door is closed (Acts 13:51)", "the mission preserved by not dying on ground that would not receive it")]},
    {"id": "standardize", "title": "Standardize — the interchangeable part",
     "gist": "Make the units uniform and the whole becomes repeatable, scalable, and teachable.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', "Ford's Model T", '1908–1927', "'any colour so long as it is black' — one standard car, held for nineteen years", "GM's annual models and choice took the market; Ford shut the line for six months in 1927 to retool — a standard held past its day is a cage"),
        ('war', 'Braddock on the Monongahela', '9 July 1755', 'European linear drill and standard formation in the American forest', 'ambushed by French and Native irregulars; ~900 of 1,300 casualties — the standard answered a battlefield that was not there'),
     ],
     "cases": [
        ("business", "Ford's interchangeable parts", "1913", "identical components on a moving line", "the assembly line made the car reproducible at scale"),
        ("war", "The Roman legion", "3rd c. BC-", "a standard unit, drill, camp and kit anywhere in the empire", "one interchangeable system fought from Britain to Syria"),
        ("ministry", "The canon and creed", "2nd-4th c. AD", "a fixed rule of faith teachable in every congregation", "a standard the whole church could carry and reproduce"),
        ("business", "The shipping container", "1956", "one box, one standard, every port and ship", "standardization collapsed the cost of global trade")]},
    {"id": "decentralize", "title": "Push decisions to the edge",
     "gist": "Let those nearest the problem decide; a body that must ask the center for everything cannot move.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Enron', '1990s–2001', 'autonomous units, mark-to-market freedom, incentives at the edge', 'no centre to check the books; collapse and prosecutions (2001) — decisions at the edge with no intent from the centre is abandonment, not delegation'),
        ('war', 'Ewell at Gettysburg', '1 July 1863', "Lee's discretionary order to take Cemetery Hill 'if practicable'", 'the hill was not taken; the Union held the high ground for two more days — delegation without clear intent delegates the defeat'),
     ],
     "cases": [
        ("war", "Auftragstaktik (mission command)", "19th-20th c.", "give the intent, let the officer on the spot choose the means", "Prussian/German doctrine: initiative at the edge beat rigid central control"),
        ("business", "Amazon's two-pizza teams", "2000s", "small autonomous teams owning their own service end to end", "decentralized ownership kept a giant moving fast"),
        ("ministry", "The house-church network", "1st c. AD", "many self-governing local congregations, loosely bound", "no single point of failure; it spread faster than any center could direct"),
        ("nature", "The colony without a center", "always", "ants and slime molds solve without a controller", "distributed local rules produce coherent global behavior")]},
    {"id": "reinvest_the_core", "title": "Reinvest the flywheel",
     "gist": "Plow the returns back into the engine that produced them; let the loop feed itself.",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ('business', 'Xerox PARC', '1970s', 'reinvested heavily in research — the GUI, Ethernet, the laser printer, the mouse', "Apple and Microsoft harvested the inventions; Xerox did not — reinvestment that never returns to the flywheel feeds someone else's"),
        ('politics', 'Soviet heavy-industry reinvestment', '1950s–1980s', 'poured surplus into steel, arms and heavy plant year after year', 'consumer goods and agriculture starved; stagnation and collapse (1991) — reinvesting in a core the people did not want'),
     ],
     "cases": [
        ("business", "Amazon's flywheel", "1997-", "lower prices -> more customers -> more sellers -> lower costs -> lower prices", "reinvest every gain into the loop instead of taking profit"),
        ("politics", "Rome's settled veterans", "republic-empire", "reinvest conquest into colonies that secured and extended the frontier", "each win funded the base for the next"),
        ("ministry", "Disciples who make disciples", "1st c. AD-", "the fruit is trained to reproduce, not merely counted", "2 Timothy 2:2 — entrust it to faithful men who will teach others"),
        ("nature", "Seed and forest", "always", "the tree spends its surplus on seed, not only on itself", "the flywheel of life is reinvested growth")]},
    # Matt, 2026-10-02: "The Prisoner's dilemma." The game is sealed on the engine (defect dominates;
    # mutual defection is the only equilibrium; yet cooperation pays 3 against the equilibrium's 1; and
    # with a shadow of the future w > max((T-R)/(R-S), (T-R)/(T-P)) = 2/3 a reciprocator cannot be invaded —
    # Axelrod 1984). The PATTERN is what wins the iterated game: nice, retaliatory, forgiving, clear.
    {"id": "reciprocity", "title": "Reciprocity — cooperate first, answer in kind, forgive, be clear",
     "gist": "In a repeated game the winning move is tit-for-tat: open with cooperation, return what you receive, forgive a single defection, and be predictable — so the other side's best reply is to cooperate too. The Gospel asks more than reciprocity (Matt 5:44), never less (Matt 7:12).",
     "counters": [  # where the SAME move FAILED — the boundary of the pattern, with evidence
        ("politics", "The July Crisis", "1914", "each power answered the last mobilisation in kind — Austria, Russia, Germany, France — with no forgiveness and no clear signal of limits", "tit-for-tat without forgiveness or clarity is an escalation ladder: five weeks from a murder to a continental war"),
        ("war", "The Hatfield–McCoy feud", "1863–1891", "every killing answered by a killing, for a generation", "reciprocity with no end in sight and no forgiveness consumed both families — a dozen dead for a hog and a grudge; the pattern needs the shadow of a SHARED future, not merely a next move"),
        ("business", "The last round — Enron's counterparties", "2001", "trading partners who had cooperated for years defected the week the future vanished", "when the game is known to end, backward induction unravels cooperation from the last round to the first; reciprocity holds only while tomorrow is worth something"),
     ],
     "cases": [
        ("war", "Live-and-let-live in the trenches", "1914–1917", "front-line units on both sides tacitly refrained from lethal fire at mealtimes and routines, answering restraint with restraint and a breach with a sharp but bounded reply", "documented by Ashworth (1980) and analysed by Axelrod (1984) — the iterated dilemma played with real lives, and cooperation emerged without any treaty"),
        ("science", "Axelrod's tournaments", "1979–1980", "the simplest entry, TIT FOR TAT (cooperate, then copy the other's last move), won both open computer tournaments against more cunning strategies", "Axelrod, The Evolution of Cooperation (1984): the winners were nice, retaliatory, forgiving and clear — the properties, not the cleverness, won"),
        ("politics", "'Trust, but verify' — the INF Treaty", "1987", "reciprocal elimination of a whole missile class with on-site verification, each side's step answered by the other's", "2,692 missiles destroyed by 1991 — cooperation sustained between adversaries by reciprocity made verifiable"),
        ("business", "Reputation among strangers — eBay feedback", "1996–", "a public running score turned one-shot trades between strangers into a repeated game", "sellers with a record of cooperation commanded a price premium (Resnick et al., 2006 — ~8% for a strong reputation); the shadow of the future, engineered"),
        ("nature", "Vampire bats", "always", "a bat that fed shares blood with a roost-mate that did not — preferentially with those that shared with it before", "Wilkinson (1984): reciprocal altruism in the field; cheats are remembered and refused"),
        ("ministry", "The collection for Jerusalem", "c. 55 AD", "the Gentile churches gave to the famine-struck Judean church that had first given them the gospel", "2 Corinthians 8:14 — 'that your abundance may be a supply for their want, that their abundance also may be a supply for your want: that there may be equality'"),
     ]},
]


def _card(cid, kind, title, body, shelf, box, bands, subject, conns, extra):
    return {"id": cid, "kind": kind, "title": title, "body": body,
            "source": {"label": "The Strategy Concordance — patterns of what endures", "url": "",
                       "domain": "strategy", "authority_tier": "reference"},
            "shelf": shelf, "box": box, "bands": bands, "subject": subject, "connections": conns,
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False, "extra": extra}


def _counter_id(pid, arena, who):
    slug = "".join(ch if ch.isalnum() else "_" for ch in who.lower())[:40]
    return f"card_counter_{pid}__{arena}__{slug}"


def _case_id(pid, arena, who):
    slug = "".join(ch if ch.isalnum() else "_" for ch in who.lower())[:40]
    return f"card_case_{pid}__{arena}__{slug}"


def _spine_card() -> dict:
    """The Strategy Concordance spine, rooted in the Floor. Every pattern is a member of it, so the
    whole strategy island (patterns and their cases) reaches the Floor (§5.3 reachability)."""
    return _card(
        SPINE_ID, "reference", "The Strategy Concordance",
        ("Patterns of what endures — the same strategic move winning across war, politics, business, "
         "ministry, science and nature, and across time. The method turned on history: not who was "
         "clever once, but the form that recurs because it is true to how the world is made."),
        "spine", "spine", ["strategy", "patterns", "concordance", "spine"], "the strategy concordance",
        [{"to_card_id": FLOOR, "relationship": "part_of",
          "evidence": "the strategy concordance, a shelf of the Floor of Discovery"}],
        {"span": "history"})


def build_cards():
    cards = [_spine_card()]        # the Floor-rooted spine the patterns hang from
    for p in PATTERNS:
        arenas = sorted({a for a, *_ in p["cases"]})
        # the pattern is a member of the spine (roots it to the Floor), then names its cases
        conns = [{"to_card_id": SPINE_ID, "relationship": "member_of",
                  "evidence": "a recurring strategic pattern of the Strategy Concordance"}]
        for arena, who, when, move, ev in p["cases"]:
            cid = _case_id(p["id"], arena, who)
            conns.append({"to_card_id": cid, "relationship": "instance_of",
                          "evidence": f"{arena}: {who} ({when}) — {ev}"})
        for arena, who, when, move, ev in p.get("counters", []):
            cid = _counter_id(p["id"], arena, who)
            conns.append({"to_card_id": cid, "relationship": "counterexample_of",
                          "evidence": f"{arena}: {who} ({when}) — FAILED: {ev}"})
        cards.append(_card(
            f"card_pattern_{p['id']}", "strategy_pattern", p["title"],
            f"{p['gist']} A recurring strategic form seen across {len(arenas)} arenas "
            f"({', '.join(arenas)}) and across time — the same move winning in each.",
            "strategy", "pattern", ["strategy", "pattern"] + arenas, p["title"], conns,
            {"gist": p["gist"], "arenas": arenas, "span": len(arenas),
             "record": {"won": len(p["cases"]), "failed": len(p.get("counters", []))}}))
        for arena, who, when, move, ev in p.get("counters", []):
            cid = _counter_id(p["id"], arena, who)
            cards.append(_card(
                cid, "strategy_counter", f"{who} ({when}) — where it failed",
                f"{who}, {when} — {move}. What failed, and why: {ev}. A counterexample to '{p['title']}' "
                f"in the arena of {arena}: the boundary of the pattern, kept beside its wins.",
                "strategy", "counter", ["strategy", "counter", "failure", arena, p["id"]], who,
                [{"to_card_id": f"card_pattern_{p['id']}", "relationship": "counterexample_of",
                  "evidence": f"where the move '{p['title']}' failed"}],
                {"arena": arena, "when": when, "move": move, "pattern": p["id"], "who": who, "failed": ev}))
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
    unbounded = [p["id"] for p in PATTERNS if not p.get("counters")]
    if unbounded:
        rc = 3; print("patterns with no counter-case (a pattern with no known failure is a slogan):", unbounded)
    thin = [p["id"] for p in PATTERNS if len({a for a, *_ in p["cases"]}) < 2]
    if thin:
        rc = 3; print("patterns spanning <2 arenas (not a bridge):", thin)
    ncases = sum(len(p["cases"]) for p in PATTERNS)
    ncounter = sum(len(p.get("counters", [])) for p in PATTERNS)
    print(f"      {ncounter} counter-cases (where the move failed) — every pattern bounded")
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
        for arena, who, when, move, ev in p.get("counters", []):
            print(f"     {arena:9} FAILED: {who} ({when})")
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
