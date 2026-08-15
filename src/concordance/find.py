"""The tortoise — when the keeping does not hold it, go find it, surely.

Matt: "If we don't have an answer, we go search like a traditional tool… but we run it through our
tools prior to sharing. It may be slower, but our results meet a standard. We search for primary and
high quality — Library of Congress, and others. We don't claim to be the fastest. We are the surest.
We are the tortoise."

So this is not a web-scraper that hands back whatever a search engine says. It is a slow, sure path:

  1. Ask only PRIMARY, openly-licensed sources — NEVER Wikipedia or the current (everyone else
     leans on that; we don't). We'd rather be slower and find a real source. Today: the Library of
     Congress, the Internet Archive (public-domain texts, the tried-and-true 1850–1964 window), and
     Project Gutenberg. Never arbitrary copyrighted pages (that would break the moat: [[strict
     PD-only]]). The provider list is meant to grow — always openly licensed, always attributed.
  2. Our own science answers what it can, UPSTREAM of here — the keeping + the verifiers construct
     and verify (we already have the science; we don't need to always rely on the outside). This
     runs only for what we don't yet hold, and it POINTS to primary sources rather than manufacturing
     an answer from a summary.
  3. Keep what we find. A public-domain source is minted as a `practical`/`source` card (tier
     `primary_pd`, never masquerading as the verified keeping) so the library grows and can be
     carried OFFLINE — the tool fills its own gaps, and works when the internet is not there.

Sovereign and offline-first: this only runs when the keeping had no answer AND the network is
reachable; every failure degrades to the honest "I don't have that". Server-side (the query leaves
from the droplet, not the person's browser), bounded by a timeout, never stored beyond the card.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

_UA = "NarrowHighway/1.0 (+https://narrowhighway.com; sovereign verification)"
_TIMEOUT = 7          # per source; the practical path calls several, so keep each bounded
_WORD = re.compile(r"[a-z]{3,}")
_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "do", "does", "did", "how",
    "what", "why", "who", "when", "where", "which", "that", "this", "it", "for", "and", "or", "on",
    "at", "by", "with", "about", "i", "you", "my", "me", "we", "can", "tell", "explain", "mean",
    "means", "old", "new", "so", "if", "be", "from", "into", "there", "here"))


def enabled() -> bool:
    return os.environ.get("WEB_FIND_DISABLED", "").strip().lower() not in ("1", "true", "yes")


def _tokens(s: str) -> set:
    return {w for w in _WORD.findall((s or "").lower()) if w not in _STOP}


_FILLER = re.compile(
    r"^\s*(how\s+(to|do\s+i|do\s+you|does\s+one|can\s+i)|what\s+(is|are|was)|when\s+(did|was)|"
    r"who\s+(was|is|invented)|why\s+(is|do|did)|where\s+(is|was)|tell\s+me\s+about|"
    r"the\s+best\s+way\s+to|ways?\s+to|show\s+me)\b", re.I)


def _topic(query: str) -> str:
    """Strip the question/how-to filler down to the searchable topic — 'how do you make lye soap'
    -> 'make lye soap' — so the archives get keywords, not a sentence."""
    t = _FILLER.sub("", query or "").strip(" ?.")
    return t or (query or "")


# Strip only GENERIC leading verbs ('make lye soap' -> 'lye soap') and bare articles. A SPECIFIC
# craft verb IS the subject and must stay: 'tan a deer hide' searched as 'deer hide' returned deer
# newspapers, not a tanning manual — the whole craft ('tan') had been thrown away (measured 2026-08-12).
_GENERIC_VERB = re.compile(
    r"^\s*(make|making|build|building|do|does|get|getting|use|using|create|creating|find|finding|"
    r"start|starting|the|a|an)\s+", re.I)
_ARTICLE = re.compile(r"\b(a|an|the)\b", re.I)


def _search_terms(query: str) -> str:
    """The searchable subject the archives index on — keep the CRAFT ('tan', 'forge', 'ferment'),
    drop only generic filler verbs and articles, so the real topic is not buried."""
    t = _GENERIC_VERB.sub("", _topic(query)).strip()
    t = re.sub(r"\s+", " ", _ARTICLE.sub(" ", t)).strip()
    return t or _topic(query)


def _relevant(query: str, *texts: str) -> bool:
    """A finding is kept only if it actually shares a content word with what was asked — so the
    Library of Congress's tangential artifacts (a photo merely titled 'Speed of Light') are not
    passed off as an answer."""
    q = _tokens(query)
    if not q:
        return False
    hay = set()
    for t in texts:
        hay |= _tokens(t)
    return bool(q & hay)


def _get(url: str) -> Optional[str]:
    """Defensive GET — text or None. Never raises into the caller."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:   # noqa: S310 (trusted hosts only)
            return r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None


# ── providers: openly-licensed, primary / high-quality only ─────────────────────────────────
def library_of_congress(query: str, limit: int = 3,
                        practical: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Primary documents from the Library of Congress — largely public domain. Not an 'answer';
    the original sources to go deeper, attributed and linked."""
    terms = _terms(query, practical)          # relevance is judged against what we searched (see IA note)
    q = urllib.parse.quote(terms)
    raw = _get(f"https://www.loc.gov/search/?q={q}&fo=json&c={max(1, limit)}&at=results")
    if not raw:
        return []
    try:
        results = json.loads(raw).get("results") or []
    except ValueError:
        return []
    out = []
    for x in results[:limit]:
        title = (x.get("title") or "").strip()
        url = x.get("id") or x.get("url") or ""
        if not title or not url or not _relevant(terms, title, " ".join(x.get("subject") or [])):
            continue
        fmt = x.get("original_format") or x.get("type") or []
        out.append({"title": title[:140], "url": url,
                    "format": (fmt[0] if isinstance(fmt, list) and fmt else str(fmt)),
                    "source": "Library of Congress", "license": "Public domain (mostly) — verify per item",
                    "tier": "primary"})
    return out


# A practical / how-to question. For these we carry the torch of Foxfire: look back before the
# modern inputs, to the tried-and-true (1920s–1950s), public-domain and proven — NOT the latest,
# which is what everyone else leans on. Practical knowledge is the heart of this work.
_PRACTICAL = re.compile(
    r"\b(how\s+(to|do\s+i|does\s+one)|make|making|build|preserv\w*|can(ning)?|ferment\w*|pickl\w*|"
    r"garden\w*|plant\w*|grow\w*|harvest\w*|repair\w*|mend|sew\w*|knit\w*|weav\w*|soap|candle|"
    r"tan\w*|forge|blacksmith\w*|butcher\w*|forag\w*|cure|smok\w*|dry\w*|store|raise|render|churn|"
    r"brew\w*|distill\w*|whittl\w*|carpentry|masonry|homestead\w*|self.?suffic\w*|survival|"
    r"recipe|cook\w*|bak\w*|remedy|remedies|first\s+aid|compost\w*|root\s+cellar|smokehouse)\b",
    re.I)


def is_practical(query: str) -> bool:
    return bool(_PRACTICAL.search(query or ""))


# THE ARCHIVES INDEX THE CRAFT UNDER ITS PERIOD NAME, not the modern phrasing. A survival how-to
# asked in today's words does not match how the tried-and-true (1850–1964) shelved the same
# knowledge: "start a fire" stripped to "fire" returns SERMONS and a novel titled FIRE, not a
# firecraft manual; "keep warm without power" and "make soap from wood ash" return NOTHING at all,
# because no 1900s book is titled that. So a practical miss was carding a novel or falling through
# to the web tortoise while the real Foxfire-era manual sat one search term away. Map the modern
# intent to the PERIOD vocabulary the archives actually index it under — each pairing verified
# against the live archives (2026-08-15) to return an openable public-domain manual (Nessmuk's
# "Woodcraft and Camping", the "Soap-Making Manual", "Camp Cookery"). Only ever consulted for a
# PRACTICAL query, so a theology ask ("the lake of fire", "living water") is never bent to woodcraft.
_PRACTICAL_TERMS = (
    # fire, warmth, shelter — the woodcraft cluster. A SINGLE strong term ('woodcraft') puts Nessmuk's
    # "Woodcraft and Camping" first; the two-word "woodcraft camping" surfaced a story anthology
    # ("Outdoor Life and Indian Stories") ahead of the real manual (measured live 2026-08-15).
    (re.compile(r"\b(fire|firecraft|tinder|kindl|flint|ember|spark|campfire)\b", re.I), "woodcraft"),
    (re.compile(r"\b(warm|warmth|cold|heat|heating|hypotherm|freez|shelter|tent|lean|bivouac|cabin)\b",
                re.I), "woodcraft"),
    (re.compile(r"\bsoap\b", re.I), "soap making"),
    (re.compile(r"\b(water|filter|purif|potable|drinking)\b", re.I), "water purification"),
    (re.compile(r"\b(cook|bake|baking|ration|camp\s*food|camp\s*cook)\b", re.I), "camp cookery"),
)


def _terms(query: str, practical: Optional[bool] = None) -> str:
    """The subject the archives are searched on. For a practical/how-to gap, translate the modern
    phrasing to the period term the tried-and-true archives shelve the craft under (see
    `_PRACTICAL_TERMS`); otherwise, and for any unmapped practical query, the plain subject stands.
    `practical` is passed explicitly by callers that already stripped the query to a bare subject
    (`pull_and_card` hands us 'start fire', on which `is_practical` would wrongly read False)."""
    if practical is None:
        practical = is_practical(query)
    if practical:
        for rx, term in _PRACTICAL_TERMS:
            if rx.search(query or ""):
                return term
    return _search_terms(query)


def internet_archive(query: str, limit: int = 3,
                     practical: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Public-domain texts from the Internet Archive, biased to the TRIED-AND-TRUE era — older
    first. The Foxfire well: farming, food preservation, home crafts, self-reliance."""
    # look back BEFORE the modern inputs — restrict to the tried-and-true, public-domain era
    # (through 1964; the heart is the 1920s–1950s). We don't lean on the latest; everyone else does.
    # rank by the archive's own RELEVANCE (no popularity sort — that surfaces high-traffic
    # off-topic scans); the year window already keeps it in the tried-and-true, public-domain era.
    # Judge relevance against the TERM WE ACTUALLY SEARCHED, not the modern phrasing: a practical
    # how-to is searched under its period name ('start a fire' -> 'woodcraft'), and the manual that
    # comes back — "Woodcraft and Camping" — shares no word with "start fire", so checking against
    # the original query would reject every real result. The craft stage is the true subject gate.
    terms = _terms(query, practical)
    url = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(terms)
           + "+AND+mediatype%3A(texts)+AND+year%3A%5B1850+TO+1964%5D"
             "&fl[]=title&fl[]=year&fl[]=identifier&fl[]=creator"
             "&rows=" + str(max(1, limit) * 4) + "&output=json")
    raw = _get(url)
    if not raw:
        return []
    try:
        docs = (json.loads(raw).get("response") or {}).get("docs") or []
    except ValueError:
        return []
    out = []
    for x in docs:
        title = (x.get("title") if isinstance(x.get("title"), str) else "").strip()
        ident = x.get("identifier") or ""
        if not title or not ident or not _relevant(terms, title):
            continue
        yr = str(x.get("year") or "").strip()[:4]
        out.append({"title": title[:120], "url": "https://archive.org/details/" + ident,
                    "year": yr, "source": "Internet Archive",
                    "license": "Public domain (verify per item)", "tier": "primary"})
        if len(out) >= limit:
            break
    return out


def project_gutenberg(query: str, limit: int = 3,
                      practical: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Public-domain books from Project Gutenberg (PD by definition) — full text, freely carried."""
    terms = _terms(query, practical)          # relevance is judged against what we searched (see IA note)
    raw = _get("https://gutendex.com/books/?search=" + urllib.parse.quote(terms))
    if not raw:
        return []
    try:
        results = json.loads(raw).get("results") or []
    except ValueError:
        return []
    out = []
    for x in results[:limit]:
        title = (x.get("title") or "").strip()
        if not title or not _relevant(terms, title):
            continue
        who = ", ".join((a.get("name") or "") for a in (x.get("authors") or []))[:70]
        out.append({"title": title[:120], "url": "https://www.gutenberg.org/ebooks/" + str(x.get("id")),
                    "year": "", "creator": who, "source": "Project Gutenberg",
                    "license": "Public domain", "tier": "primary"})
    return out


# ── the tortoise: find, check, keep ─────────────────────────────────────────────────────────
def _store_path():
    from pathlib import Path
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "web_cache.jsonl"


FLOOR = "card_k_floor_of_discovery"

# What the tortoise brings back must be NESTED like everything else. Every other card in the
# keeping is `member_of` its shelf spine; these two shelves had no spine, so `_mint_doc` was
# writing `"connections": []` and every card it kept was born an orphan — not a one-off backlog
# but an ongoing leak, one more each time the tortoise ran. The spines are defined HERE, in code,
# rather than in a data file, because web_cache.jsonl is data-only and untracked: on a fresh box
# a data-file spine would simply be absent and the leak would return.
_SPINES = {
    "practical": ("card_spine_practical", "The practical library — knowledge that has been used",
                  "Public-domain practical sources the tortoise went and found: how things are "
                  "actually done, kept so they can be carried offline. Carry the torch of Foxfire.",
                  ["practical", "foxfire", "public domain", "spine"]),
    "sources": ("card_spine_sources", "The primary sources — go to the original",
                "Public-domain primary sources the tortoise went and found, kept whole rather than "
                "summarised. Go to the original, not to someone's account of it.",
                ["source", "primary", "public domain", "spine"]),
}


def _spine_card(shelf: str) -> Optional[Dict[str, Any]]:
    spec = _SPINES.get(shelf)
    if not spec:
        return None
    cid, title, body, bands = spec
    return {"id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": "The keeping — a spine of what the tortoise brought back",
                       "url": "", "domain": "", "authority_tier": "reference"},
            "shelf": "spine", "box": "spine", "bands": bands, "subject": title,
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": "a spine of the keeping, rooted in the Floor of Discovery"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False}


def _member_of(shelf: str) -> list:
    """The nesting for a card on this shelf — a FOUND relation ("this card is on this shelf"),
    never an authored judgement, so it cannot be a weak edge."""
    spec = _SPINES.get(shelf)
    if not spec:
        return []
    return [{"to_card_id": spec[0], "relationship": "member_of",
             "evidence": "a member of the " + shelf + " shelf in the keeping"}]


def _set_stage(store, cid: str, stage: str, only_from: str = "public_review") -> bool:
    """Move ONE card from `only_from` to `stage`. Returns True if it actually changed.

    Refuses to touch a card in any other stage: a steward's quarantine or retraction must never be
    undone by an automatic path. Rewrites atomically and refreshes the live corpus so the change is
    visible on this request rather than after a restart.
    """
    try:
        lines = store.read_text(encoding="utf-8").splitlines() if store.exists() else []
    except OSError:
        return False
    out, changed, card = [], False, None
    for ln in lines:
        if not ln.strip():
            continue
        try:
            c = json.loads(ln)
        except ValueError:
            out.append(ln)
            continue
        if c.get("id") == cid and c.get("lifecycle_stage") == only_from:
            c["lifecycle_stage"] = stage
            c["updated_at"] = time.time()
            changed, card = True, c
        out.append(json.dumps(c, ensure_ascii=False))
    if not changed:
        return False
    tmp = store.with_suffix(".tmp")
    tmp.write_text(chr(10).join(out) + chr(10), encoding="utf-8")
    os.replace(tmp, store)
    try:
        from . import corpus as _c
        _c.add_to_default(card)
    except Exception:  # noqa: BLE001
        pass
    return True


def _promote_to_public(store, cid: str) -> bool:
    """Release a held card into the shared keeping. Returns True if it actually changed.

    The named case of `_set_stage` — one implementation, so the release path and the steward's
    refusal cannot drift apart. Only ever moves `public_review` -> `public`; a retracted or
    quarantined card stays exactly where a steward put it.
    """
    return _set_stage(store, cid, "public", only_from="public_review")


def _mint_doc(query: str, doc: Dict[str, Any], practical: bool = True,
              plane: str = "human") -> Optional[Dict[str, Any]]:
    """Keep a tried-and-true public-domain practical source in the keeping — a higher tier than the
    open web (primary + PD), so the practical library grows and can be carried offline.

    ONE MECHANISM, TWO PLANES (Matt, 2026-08-01: *"It should be the same just different planes."*).
    The act is identical whoever asks: a miss goes to the tortoise, a public-domain source is found
    and carded, and the keeping is permanently larger. What differs is who authorised it.

      human plane   the person's own ask IS the authorisation — the card enters `public`.
      agent plane   the card enters `public_review`, which `corpus.is_public()` withholds from
                    every public read path, and waits for the next human to look at it.

    This closes a real breach rather than adding ceremony: `lifecycle_stage` was hardcoded
    `"public"`, so an agent calling the `ask` tool minted straight into the shared keeping with no
    human ever seeing it — against the covenant's "ask before writes" and against Matt's own rule
    that the agent plane "stays separate and must be approved by a human. We ask the next human
    that looks at it."

    Nothing is lost by waiting: the agent still receives the answer it asked for. Only the card's
    entry into everyone else's library is what waits.
    """
    try:
        url = doc.get("url") or ""
        cid = "card_pd_" + hashlib.sha256((doc.get("source", "") + "|" + url).encode()).hexdigest()[:12]
        yr = (" (" + doc["year"] + ")") if doc.get("year") else ""
        who = (" — " + doc["creator"]) if doc.get("creator") else ""
        tag = ("Carry the torch of Foxfire — practical knowledge that has stood the test of time."
               if practical else "A primary source — go to the original, not a summary.")
        body = (doc.get("title", "") + yr + who + "\n\nA public-domain source: " + doc.get("source", "")
                + " — " + url + ". " + tag + " Public domain (" + doc.get("license", "")
                + "), so it can be kept and used offline.")
        card = {"id": cid, "kind": "practical" if practical else "source",
                "title": doc.get("title", "")[:100], "body": body,
                "source": {"label": doc.get("source", "") + (yr or ""), "url": url,
                           "license": doc.get("license", ""), "authority_tier": "primary_pd"},
                "shelf": "practical" if practical else "sources",
                "box": "foxfire" if practical else "primary",
                "bands": (["practical", "foxfire"] if practical else ["source", "primary"])
                + ["public domain", doc.get("source", "").lower()]
                + ([doc["year"]] if doc.get("year") else []) + sorted(_tokens(query))[:6],
                "connections": _member_of("practical" if practical else "sources"),
                "author": "archive", "created_at": time.time(),
                "updated_at": time.time(), "visibility": "public",
                # BOTH planes wait for review (Matt, 2026-08-06). The "human plane" is the anonymous
                # /ask conduit, so a fetched document cannot enter the public library on an anonymous
                # say-so; it waits in `public_review`, which corpus.is_public() withholds from every
                # public read path until a copyright/PD check clears it. `acquired_by_plane` still
                # records who pulled it — the plane is a provenance mark now, not a fast public lane.
                "lifecycle_stage": "public_review",
                "acquired_by_plane": plane,
                "volatility": "durable", "surface": "secular", "generated": False, "verified": False}
        # THE GATE KERNEL — stamp the nine-field record on the acquisition (Matt, 2026-07-25).
        # The tortoise FOUND this (a real retrieval), but finding is not verifying: a fetched
        # public-domain source enters `public_review`, which corpus.is_public() withholds from
        # every public read path until a human looks. The kernel is given no verification evidence
        # and no witness, so it types the held card as community and lands it QUARANTINE with
        # authority 'quarantined' — exactly the held state this path already writes. The card's id
        # is content-addressed over source|url (not the whole card), so this ADDITIVE field cannot
        # perturb dedup; `acquired_by_plane` still records who pulled it — the plane buys no authority.
        from . import kernel as _kernel
        grec = _kernel.gate(card, entered_as=cid, authority_in="quarantined", author="archive",
                            in_kind_checked=True,
                            assumptions=("the tortoise fetched a public-domain source for a miss "
                                         "— found, not verified; held for human review",))
        card["gate_record"] = grec.to_dict()
        p = _store_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    try:
                        existing.add(json.loads(ln).get("id"))
                    except ValueError:
                        pass
        # The spine must exist before the card that hangs off it, or the graft dangles.
        spine = _spine_card(card["shelf"])
        if spine and spine["id"] not in existing:
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(spine, ensure_ascii=False) + "\n")
            existing.add(spine["id"])
            try:
                from . import corpus as _c
                _c.add_to_default(spine)
            except Exception:  # noqa: BLE001
                pass
        if cid not in existing:
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(card, ensure_ascii=False) + "\n")
            try:
                from . import corpus as _c
                _c.add_to_default(card)
            except Exception:  # noqa: BLE001
                pass
        elif plane == "human":
            # A HUMAN ASKING **IS** THE NEXT HUMAN THAT LOOKS AT IT.
            #
            # Without this the plane boundary becomes a trap: an agent acquires the source, the
            # card is held in `public_review`, and every later human ask finds the id ALREADY
            # PRESENT — so the mint is skipped, the stage never changes, and the material is
            # invisible to everyone for good. Caught on the live wire 2026-08-01: an agent-plane
            # `Samkhya` acquisition left a following human /search at count 0 with the cards
            # sitting right there.
            #
            # Withholding is meant to be a WAIT, not a grave. A person asking for exactly this
            # thing is the review the agent plane was waiting on, so their ask releases it — the
            # same seconding rule the want desk already uses, applied to acquisitions.
            _promote_to_public(p, cid)
        return card
    except Exception:  # noqa: BLE001
        return None


def find_and_check(query: str, config, plane: str = "human") -> Optional[Dict[str, Any]]:
    """The slow, sure path. Returns a framed answer (or None if nothing high-quality was found or
    the network was unreachable). Never raises."""
    if not enabled():
        return None
    try:
        practical = is_practical(query)
        # PRIMARY, public-domain sources only — never Wikipedia, never the latest. We'd rather be
        # slower and send you to a real source than lean on a summary. Our own science answers what
        # it can, upstream of here (the keeping + verifiers — we construct and verify); this points
        # to primary sources for what we don't yet hold.
        docs = (internet_archive(query, practical=practical)
                + project_gutenberg(query, practical=practical)
                + library_of_congress(query, practical=practical))
        if not docs:
            return None
        for d in docs[:3]:
            _mint_doc(query, d, practical=practical, plane=plane)
        if practical:
            note = ("The keeping doesn't hold this yet. For practical knowledge we carry the torch of "
                    "Foxfire — we look back before the modern inputs, to the tried-and-true (the "
                    "1920s–1950s), public-domain and proven. Not the latest; everyone else does that. "
                    "Slower, surer. We are the tortoise.")
        else:
            note = ("The keeping doesn't hold a verified answer for that yet. We construct and verify "
                    "from our own science where we can; the rest we won't fetch from a summary — we'd "
                    "rather be slower and send you to primary, public-domain sources. We are the "
                    "tortoise.")
        return {"source_note": note, "answer": None, "framed": "", "checks_verdict": None,
                "documents": docs}
    except Exception:  # noqa: BLE001
        return None
