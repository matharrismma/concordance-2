#!/usr/bin/env python3
"""We are the connection to the legal free tools — books, textbooks, media, knowledge.

Matt, 2026-07-25: "There are many outstanding free tools that have stood up in court — sharing
textbooks and other media. We are the connection to those. We don't do anything that could be
remotely on the line, but we use everything up to it." So this cards a curated catalogue of
LEGALLY-SOLID free-access tools — public-library lending, open textbooks, open-access research,
find-a-copy, public-domain full texts, and the ones that WON in court (HathiTrust's fair-use ruling).

THE BOUNDARY (load-bearing): everything up to the line, nothing on it. Only lawful free access —
public-library lending, open licenses (CC/OER), public domain, and fair use validated in court. NO
piracy: Sci-Hub, Library Genesis and their kind are deliberately EXCLUDED (they lost in court). We
are the concierge that connects a person to the free, legal way — we host nothing, we take nothing.

Conduit: real, named services with their legal basis, attributed, generated=False. Authored/curated
(git-tracked). Rooted in the Floor. A gift-economy build — get the poor the most knowledge, free.

    PYTHONPATH=src python tools/card_access_tools.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_access_tools"
_slug = re.compile(r"[^a-z0-9]+")

# (name, url, category, legal_basis, what_you_get)
TOOLS = [
    # ── Public libraries — free with a library card ──
    ("Libby / OverDrive", "https://libbyapp.com", "library", "public-library lending (licensed)",
     "Borrow ebooks and audiobooks FREE from your public library, on your phone. The single best free reading app."),
    ("Hoopla", "https://www.hoopladigital.com", "library", "public-library lending (licensed)",
     "Ebooks, audiobooks, movies, music, and comics — free, instantly, with a library card; usually no waitlist."),
    ("Kanopy", "https://www.kanopy.com", "library", "public-library lending (licensed)",
     "Films and documentaries — Criterion, PBS, indie — streamed free through your library or university."),
    ("Get a library card online", "https://www.overdrive.com/libraries", "library", "public institution",
     "Many US public libraries issue a card online in minutes; some (e.g. large city systems) enroll non-residents. The master key to everything above."),
    # ── Open textbooks — openly licensed, free forever ──
    ("OpenStax", "https://openstax.org", "textbooks", "CC-BY open license (Rice University)",
     "Free, peer-reviewed college textbooks — biology, physics, calculus, economics, history — openly licensed, keep them forever."),
    ("MIT OpenCourseWare", "https://ocw.mit.edu", "textbooks", "open courseware (CC)",
     "The actual materials of thousands of MIT courses — lectures, notes, problem sets, exams — free and open."),
    ("LibreTexts", "https://libretexts.org", "textbooks", "open education (CC)",
     "A vast free library of open textbooks across the sciences, humanities and more — remixable and legal."),
    ("Open Textbook Library", "https://open.umn.edu/opentextbooks", "textbooks", "open license (U. Minnesota)",
     "Peer-reviewed open textbooks you can read, download and print free."),
    ("OER Commons", "https://oercommons.org", "textbooks", "open educational resources (CC)",
     "A search engine for openly-licensed teaching and learning materials at every level."),
    ("Khan Academy", "https://www.khanacademy.org", "textbooks", "free nonprofit",
     "Free lessons and practice from arithmetic to calculus, grammar to history — for any learner, any age."),
    ("Saylor Academy", "https://www.saylor.org", "textbooks", "free nonprofit (CC)",
     "Free, self-paced college-level courses, with free certificates and credit pathways."),
    # ── Open-access research — legal free papers ──
    ("Unpaywall", "https://unpaywall.org", "research", "open access (legal author/publisher copies)",
     "A free browser button that finds the LEGAL open-access version of a paywalled paper — the author's or publisher's own free copy."),
    ("arXiv", "https://arxiv.org", "research", "author-posted preprints (open)",
     "Free preprints in physics, mathematics, computer science, biology and more — posted by the authors themselves."),
    ("PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc", "research", "open access (NIH, public)",
     "Millions of free full-text biomedical and life-sciences articles from the US National Institutes of Health."),
    ("DOAJ", "https://doaj.org", "research", "open-access journals (peer-reviewed)",
     "The Directory of Open Access Journals — vetted, free, peer-reviewed scholarship across every field."),
    ("CORE", "https://core.ac.uk", "research", "open-access aggregator",
     "The world's largest collection of open-access research papers, searchable and free to read."),
    ("Google Scholar", "https://scholar.google.com", "research", "index (links to legal free copies)",
     "Search scholarly literature; the 'All versions' link often surfaces a free, legal PDF."),
    ("OpenAlex", "https://openalex.org", "research", "open catalog (CC0)",
     "A free, open index of the world's scholarship — papers, authors, institutions — with links to open copies."),
    # ── Find or borrow any book — legal routes ──
    ("WorldCat", "https://search.worldcat.org", "find", "library catalog",
     "Find which library near you holds any book, then borrow it free. The map to every library's shelves."),
    ("Interlibrary Loan (ILL)", "https://www.worldcat.org", "find", "library cooperation",
     "Ask your library to borrow a book or article from another library for you — usually free. Almost anything can be gotten this way."),
    ("Internet Archive", "https://archive.org", "find", "public domain + fair use archive",
     "Millions of PUBLIC-DOMAIN books, films, audio and software, free to download; plus a scan-and-borrow library. A vast lawful commons."),
    ("HathiTrust", "https://www.hathitrust.org", "find", "fair use — WON in court (Authors Guild v. HathiTrust)",
     "Full text of public-domain works, and full-text SEARCH across millions more — a use the courts ruled lawful fair use."),
    # ── Public-domain full texts — free and clear ──
    ("Project Gutenberg", "https://www.gutenberg.org", "public_domain", "public domain",
     "~77,000 public-domain books, full text, free — the classics of the world, no strings."),
    ("Standard Ebooks", "https://standardebooks.org", "public_domain", "public domain (CC0 formatting)",
     "The great public-domain books, lovingly re-typeset into beautiful, free, modern ebook files."),
    ("Wikisource", "https://wikisource.org", "public_domain", "public domain / CC-BY-SA",
     "A free library of source texts — documents, public-domain books, translations — transcribed and proofread."),
    ("Library of Congress — Digital", "https://www.loc.gov/collections", "public_domain", "US government / public domain",
     "Free digitized books, maps, photographs, recordings and manuscripts from the world's largest library."),
    ("Google Books", "https://books.google.com", "public_domain", "public-domain full view + fair-use preview",
     "Read public-domain books in full, and preview and search inside most others — free and lawful."),
    # ── Borrow from people — the oldest free tool, and the fellowship ──
    ("Borrow from your people", "", "borrow", "personal lending (first-sale doctrine)",
     "The oldest free tool: ask a friend, your church, or a neighbor to lend you their copy — lending a "
     "book or disc you own is entirely lawful. Among believers, say what you need and someone near you "
     "may already have it on their shelf."),
    # ── Media — legal free ──
    ("Musopen", "https://musopen.org", "media", "public domain / CC music",
     "Free public-domain sheet music and recordings of classical music — legal to use for anything."),
    ("Free Music Archive", "https://freemusicarchive.org", "media", "Creative Commons music",
     "Free, legal music under Creative Commons licenses — for listening and for making."),
    ("LibriVox", "https://librivox.org", "media", "public domain (volunteer recordings)",
     "Free public-domain audiobooks, read by volunteers — thousands of classics to listen to, free."),
    # ── Homeschool & families — free curriculum and learning ──
    ("Easy Peasy All-in-One Homeschool", "https://allinonehomeschool.com", "homeschool", "free Christian curriculum",
     "A complete, free, Christian homeschool curriculum, preschool through high school — daily lessons, all subjects."),
    ("Ambleside Online", "https://www.amblesideonline.org", "homeschool", "free (Charlotte Mason)",
     "A free, complete Charlotte Mason curriculum built on living books — used by homeschool families worldwide."),
    ("CK-12", "https://www.ck12.org", "homeschool", "free nonprofit (CC-BY-NC)",
     "Free K-12 textbooks, practice, and adaptive lessons in math and science — for teachers, parents, and students."),
    ("CommonLit", "https://www.commonlit.org", "homeschool", "free nonprofit",
     "Free reading passages and literacy lessons, grades 3-12 — build a strong reader at home."),
    ("Blue Letter Bible", "https://www.blueletterbible.org", "faith", "free Bible study",
     "Free in-depth Bible study — original Hebrew/Greek, concordances, commentaries, many translations side by side."),
    ("Duolingo", "https://www.duolingo.com", "homeschool", "free tier",
     "Learn a language free — a gentle daily habit for the whole family, including Biblical-language starters."),
    # ── Offline knowledge — carry it where there is no signal (prep · homeschool · radio) ──
    ("Kiwix", "https://kiwix.org", "offline", "free/open (offline copies of open content)",
     "Put all of Wikipedia, Wiktionary, medical guides, and more on a phone or drive to read with NO internet. "
     "Essential for off-grid, rural, or prepared homes."),
    ("Organic Maps", "https://organicmaps.app", "offline", "free/open (OpenStreetMap)",
     "Free, private, fully OFFLINE maps and turn-by-turn navigation from OpenStreetMap — no tracking, no signal needed."),
    ("Internet-in-a-Box", "https://internet-in-a-box.org", "offline", "free/open",
     "A pocket server that serves a whole library (Wikipedia, books, courses, maps) over local Wi-Fi where there is no internet."),
    # ── Communication & privacy — free, sovereign, off-grid-friendly (radio · prep · the flock) ──
    ("Signal", "https://signal.org", "comms", "free/open (nonprofit)",
     "Free, private, end-to-end-encrypted messaging and calls — the standard for keeping family and fellowship private."),
    ("Meshtastic", "https://meshtastic.org", "comms", "free/open (LoRa mesh)",
     "Free off-grid text messaging over long-range radio — no cell towers, no internet. The backbone for a prepared community."),
    ("Proton (Mail · Calendar · Drive)", "https://proton.me", "everyday", "free tier (encrypted, Swiss)",
     "Free, private, encrypted email, calendar, and file storage — a privacy-respecting alternative to Big Tech for daily life."),
    # ── Everyday tools — plan the day, write, keep files (recommend, never rebuild) ──
    ("Google Calendar", "https://calendar.google.com", "everyday", "free",
     "Free shared calendars for the family — plan days, set reminders, coordinate a household or a co-op."),
    ("LibreOffice", "https://www.libreoffice.org", "everyday", "free/open",
     "A free, offline, sovereign office suite — documents, spreadsheets, presentations — no subscription, yours forever."),
    ("Nextcloud", "https://nextcloud.com", "everyday", "free/open (self-host)",
     "Your own private cloud — files, calendar, contacts — that YOU host and control. Sovereignty for a family's data."),
    # ── Help in hard times — free aid for those who need it most ──
    ("211 (dial 2-1-1)", "https://www.211.org", "help", "free public referral (United Way)",
     "Call or text 211, free, 24/7 — connects you to local help: food, housing, utilities, health, crisis. The first door when you're stuck."),
    ("FindHelp", "https://www.findhelp.org", "help", "free (nonprofit)",
     "Enter your ZIP to find free and reduced-cost local help — food, shelter, medical, work, care — near you."),
    ("Feeding America — Food Bank Finder", "https://www.feedingamerica.org/find-your-local-foodbank", "help", "free (nonprofit)",
     "Find your nearest food bank and pantry — free groceries for a family that's short this week."),
    ("MedlinePlus", "https://medlineplus.gov", "health", "free (US National Library of Medicine)",
     "Free, trustworthy health information from the NIH — conditions, medicines, tests — in plain language."),
    ("LawHelp", "https://www.lawhelp.org", "help", "free legal aid directory",
     "Find free legal aid and self-help for civil problems — housing, family, benefits — for those who can't afford a lawyer."),
    ("Benefits.gov", "https://www.benefits.gov", "help", "free (US government)",
     "A free finder for government assistance you may qualify for — food, healthcare, housing, family support."),
    # ── Make, fix, and build — repair instead of replace (makers · families · stewardship) ──
    ("iFixit", "https://www.ifixit.com", "maker", "free repair guides (CC)",
     "Free, step-by-step guides to FIX what you own — phones, appliances, cars — instead of buying new. Stewardship in practice."),
    ("Instructables", "https://www.instructables.com", "maker", "free (community DIY)",
     "Free how-to projects for making almost anything — from woodworking to electronics to food."),
    ("KiCad", "https://www.kicad.org", "maker", "free/open (electronics CAD)",
     "Free, professional circuit-board design — schematic to PCB. For the maker and the hardware builder."),
    ("FreeCAD", "https://www.freecad.org", "maker", "free/open (3D CAD)",
     "Free, open 3D modeling and parametric CAD — design real parts to print or build."),
    ("Ready.gov", "https://www.ready.gov", "prep", "free (US government)",
     "Free, sober guidance to prepare a household for emergencies — water, food, plan, kit. Prudence, not fear (Prov 22:3)."),
]

BOUNDARY = (
    "THE LINE — what we will and will not connect you to. We point ONLY to lawful free access: "
    "public-library lending, open licenses (Creative Commons / OER), the public domain, and fair use "
    "that has been upheld in court (as HathiTrust's was). We use everything UP TO that line and nothing "
    "on it. We do NOT point to Sci-Hub, Library Genesis, or any piracy — they lost in court, and we keep "
    "our hands clean (Romans 13:1; Matthew 22:21). The gift is real precisely because it is legal.")


def _sk(name):
    return _slug.sub("_", name.lower()).strip("_")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference", "title": "The free tools — the connection to lawful free access",
        "body": ("Outstanding free tools, legally solid, for books, textbooks, research and media. We are "
                 "the CONNECTION to them — we host nothing and take nothing; we get you the most, free, "
                 "through every lawful channel. Everything up to the line, nothing on it."),
        "source": {"label": "The free-access catalogue (curated, lawful)", "url": "", "domain": "access", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["free", "tools", "access", "library", "open", "public domain", "spine"],
        "subject": "the free tools",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "lawful free access, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the connection to free tools)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }
    cards = [spine]
    for name, url, cat, legal, what in TOOLS:
        cards.append({
            "id": f"card_tool_{_sk(name)}", "kind": "reference",
            "title": f"{name} — free {cat.replace('_',' ')}"[:180],
            "body": f"{name}: {what}  How it's free & legal: {legal}.  Go: {url}",
            "source": {"label": name, "url": url, "domain": "access", "authority_tier": "reference"},
            "shelf": "access", "box": "tool",
            "bands": [_sk(name).replace("_", " "), cat, "free", "tool", "access", "legal"] + what.lower().split()[:6],
            "subject": name,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"a lawful free-access tool ({cat})"}],
            "author": "Matt Harris (the connection to free tools)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": cat, "url": url, "legal_basis": legal, "cost": "free"},
        })
    cards.append({
        "id": "card_tool_the_line", "kind": "reference", "title": "The line — lawful free access only",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "access", "authority_tier": "reference"},
        "shelf": "access", "box": "principle",
        "bands": ["boundary", "legal", "lawful", "piracy", "fair use", "line", "integrity"],
        "subject": "the line",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the catalogue"}],
        "author": "Matt Harris (the connection to free tools)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "access_tools_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards)-1} free-access tools (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
