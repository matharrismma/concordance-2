"""EXPAND ON THE CALL — one mechanism, two planes, and the want list only when there is no way out.

Matt, 2026-08-01, two sentences that settled the design:

    "It should be the same just different planes."
    "The want list is for when we don't have internet. Otherwise, we just execute then and allow
     the user to assist."

So a miss is not a dead end and not a queue ticket. It is a slower answer. The library goes and
gets it, cards it, hands it over, and is permanently larger — and the person may assist (choose
among what came back, refine the ask) rather than wait on anyone.

WHY THIS MODULE EXISTS AT ALL. The behaviour was already built and already good — `/ask` has run
the tortoise for months, and a live probe proved it: `/search?q=Rigveda` returned 0, two `/ask`
calls later it returned 3 public-domain sources that the tortoise had found and carded on the
call. But `/search` and the MCP `search` tool never invoked it. Same question, same engine, two
doors, two different answers — and the door AGENTS use (about 35% of traffic) was the deaf one. An
agent got `count: 0` and reasonably concluded the library was empty on the Rigveda, while the
other door was busy acquiring it.

That is this project's recurring failure in its purest form: correct in one place, absent where
the reader actually stands. So the capability moves here, where every door can call the same thing.

THE TWO PLANES — the act is identical, and BOTH now wait for review (Matt, 2026-08-06):

    human   the person pulls and USES it in the moment (it is returned to them, and the card is
            kept so the next asking finds it). But the "human plane" is the anonymous /ask conduit
            — any visitor reaches it — so a pull cannot enter everyone else's PUBLIC library on an
            anonymous say-so. It enters `public_review`, held until a copyright/PD check clears it.
    agent   same: cards enter `public_review`.

    `corpus.is_public()` withholds `public_review` from every public read path. Carding is not
    infringement (a card is metadata + a re-readable span pointer, not a republished body); PUBLIC
    RELEASE is what waits for the check. This supersedes the earlier "human -> public" rule: the
    two planes now differ only in `acquired_by_plane` (who pulled it), never in what the public sees.

THE WANT LIST IS THE OFFLINE QUEUE, nothing more. If the network is reachable we execute now; a
want is opened only when we could not reach out at all, so the miss survives until a connection
does. Opening a want for something we could have simply fetched turns a slower answer into a
chore for a person, which is exactly backwards.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

PLANES = ("human", "agent")


def offline() -> bool:
    """True when no outward path exists — the one condition that justifies queueing a want."""
    from . import find
    return not find.enabled()


def expand(query: str, config, plane: str = "human",
           note: str = "") -> Dict[str, Any]:
    """Try to answer a miss NOW. Returns what happened, in words a caller can act on.

    {"status": "acquired", cards, documents, source_note}   found and carded (slower lane)
    {"status": "nothing_found"}                             we looked, the archives had nothing
    {"status": "queued", want_id}                           no network — the want waits for one
    """
    plane = plane if plane in PLANES else "human"
    q = str(query or "").strip()
    if not q:
        return {"status": "nothing_found", "reason": "an empty query asks nothing"}

    if offline():
        # THE ONLY CASE THAT BECOMES A WANT. Offline is not a failure of the library, it is a
        # postponement — the miss is kept so the miners can work it when a connection returns.
        from . import wants
        r = wants.open_want(kind="missing", query=q, plane=plane,
                            note=note or "no network at the time of asking")
        return {"status": "queued", "want_id": r.get("id"), "ok": r.get("ok", False),
                "message": "There is no connection right now, so this is written down and will be "
                           "fetched when there is one."}

    from . import find
    try:
        found = find.find_and_check(q, config, plane=plane)
    except Exception:  # noqa: BLE001 — the slow lane must never break the fast one
        found = None

    docs: List[Dict[str, Any]] = list((found or {}).get("documents") or [])
    if not found or not (found.get("answer") or docs):
        # WE LOOKED AND THE ARCHIVES HAD NOTHING. That is not a want either: queueing it would ask
        # a person to do what the miners just failed to do. Say so plainly instead.
        return {"status": "nothing_found",
                "message": "I went to the public-domain archives for this and they had nothing I "
                           "could stand behind. I won't invent one."}

    return {"status": "acquired", "plane": plane, "documents": docs,
            "answer": found.get("answer"), "framed": found.get("framed", ""),
            "checks": found.get("checks_verdict"), "source_note": found.get("source_note") or "",
            "held_for_review": True,
            "message": ("Not in the keeping, so I went and found it — public-domain sources, "
                        "kept for next time. Carded and waiting for a copyright check before it "
                        "joins the shared public library.")}


_PD_YEAR_CEILING = 1928          # unambiguously public domain in the US as of 2026


def _pd_ok(doc: Dict[str, Any]) -> bool:
    """A PD CHECK at the moment of the pull (Matt, 2026-08-12: "do a PD check and find an available
    source to add to the corpus"). A confirmed primary PUBLIC-DOMAIN source may go STRAIGHT into the
    shared library — that is why these providers were chosen — so the next asking finds it at once.
    Project Gutenberg is curated public domain. An Internet Archive item is released only when its own
    date puts it before 1929. Anything else waits in the human review lane, unchanged. Conservative by
    design: uncertain -> held, never the reverse."""
    import re as _re
    src = str(doc.get("source") or "")
    if "Gutenberg" in src:
        return True
    if "Internet Archive" in src:
        m = _re.search(r"\b(1[5-9]\d\d|20\d\d)\b", str(doc.get("year") or ""))
        return bool(m and int(m.group(1)) <= _PD_YEAR_CEILING)
    return False


def pull_and_card(query: str, subject: str, config=None, plane: str = "human",
                  providers=None, fetch=None, craft_fn=None) -> Dict[str, Any]:
    """The WHOLE pull — find a source, open it, cut the cards, keep them. One call.

    Matt, 2026-08-02: *"Right now it only pulls the card. It needs to be able to pull the
    requested information and then make the card for the future, so we only search once per
    question. Right now, it just didn't have what it needed on Nazarene, so that was it. I asked
    it to find the information, and it couldn't do that."*

    He is describing the exact seam this closes. The tortoise found catalogue entries and minted
    CITATIONS — a pointer to a book, never a page of it. The craft chain (fetch → ark → spans,
    each span re-readable at its offsets) existed and was proven, but only a person at a terminal
    ever drove it. So a miss produced "here is a book that exists", which is not the information
    that was asked for. This function is the citation path and the craft path joined: the same
    slower answer, now carrying the source's own words — and because the cards are KEPT, the next
    asking finds them in the keeping and never goes out at all. Search once per question.

    Bounded for use inside a request: at most three candidate documents are tried, the first that
    yields real cards wins, and every network step carries the fetch layer's own timeout and size
    ceiling. On a device that anchors no sources (no ark), it says so and the citation behaviour
    stands — degraded honestly, never silently.

    `providers` / `fetch` / `craft_fn` are injectable for tests; production defaults are the real
    tortoise, the real ark, the real craft.
    """
    from . import craft as _craft
    from . import find as _find
    from . import sources as _sources
    from . import unchecked as _unchecked

    q = str(query or "").strip()
    subj = str(subject or q).strip()
    if not q and not subj:
        return {"status": "nothing_found", "reason": "an empty query asks nothing"}
    if offline():
        return {"status": "offline"}
    if _sources.sources_dir() is None:
        # No ark on this device — the citation path still works upstream; say what is missing.
        return {"status": "no_ark",
                "message": "this device anchors no source bodies, so the text cannot be kept here"}

    fetch = fetch or _sources.fetch
    craft_fn = craft_fn or _craft.craft
    # A pull only ever answers a practical/how-to gap, so the tortoise reads the Foxfire era and the
    # cards it keeps belong on the practical shelf. The intent lives in `q` ("how do I start a fire")
    # even after `subj` was stripped to the bare "start fire", so read practicality from `q`.
    practical = _find.is_practical(q)
    default_providers = providers is None
    if default_providers:
        # PROJECT GUTENBERG FIRST FOR A PRACTICAL PULL. Its plain-text is curated public domain
        # (released to the shared library at once, so the next asking is instant) and holds the
        # Foxfire-era manuals whole — Nessmuk's "Woodcraft and Camping" and its kin. The loop keeps
        # the FIRST source that yields enough verifying cards, so whichever provider leads decides
        # the source: with the Internet Archive first, a tangential story book with a few 'fire'
        # mentions won the race over the real manual (measured live 2026-08-15). For a non-practical
        # miss the Archive's far broader catalogue still leads — it is likelier to hold an obscure
        # subject at all.
        providers = ((_find.project_gutenberg, _find.internet_archive) if practical
                     else (_find.internet_archive, _find.project_gutenberg))

    docs: List[Dict[str, Any]] = []
    for p in providers:
        try:
            # The real archives must be searched on the PERIOD term (find._terms) — a bare "start
            # fire" returns sermons, "woodcraft" returns the manual. An INJECTED test provider is
            # called plainly, so its signature is never assumed to carry `practical`.
            docs.extend((p(subj if subj else q, limit=3, practical=True) if default_providers
                         else p(subj if subj else q, limit=3)) or [])
        except Exception:  # noqa: BLE001 — one deaf provider must not silence the others
            continue

    tried = 0
    for doc in docs:
        if tried >= 3:
            break
        text_url = _sources.resolve_text_url(doc.get("url") or "")
        if not text_url:
            continue
        tried += 1
        wb = fetch(text_url, label=str(doc.get("title") or "")[:200],
                   license_note=str(doc.get("license") or "public domain source"),
                   chosen_by=f"pull_and_card: a miss on {subj!r} answered on the call")
        if wb.get("status") not in ("held", "already"):
            continue
        sha = wb["sha256"]
        parent_id = "card_src_" + sha[:12]
        r = craft_fn(sha, subj or q, parent_id=parent_id, plane=plane)
        cards = list(r.get("cards") or [])
        if len(cards) < 3:
            continue          # a book that barely speaks to the subject is the wrong book
        sv = _craft.verify_spans(cards)
        if sv["false"] or sv["true"] != len(cards):
            continue          # never keep a card that does not verify — try the next source
        # THE PD CHECK AT THE PULL (Matt, 2026-08-12): a confirmed primary PUBLIC-DOMAIN source is
        # added to the shared corpus at once (lifecycle 'public'), so the NEXT asking finds it and
        # never goes out — the tortoise's whole point, "search once per question". Anything the PD
        # check cannot confirm keeps the earlier, conservative behaviour: marked for the human review
        # lane at 'public_review'. (This deliberately loosens the 2026-08-06 "both planes wait" rule,
        # but ONLY for a verified-PD primary source — uncertain still waits.)
        pd = _pd_ok(doc)
        # A practical pull is Foxfire knowledge: keep it on the PRACTICAL shelf, which the how-to
        # ranker leads with and which the next asking recognises — a generic "sources" card is
        # demoted below a tangential field card, so the tortoise would go out all over again and
        # "search once, keep it" would never hold. And tag every kept card `tortoise: True`, so a
        # later ask can tell the tortoise's OWN passages (cut FOR this subject) from the millions of
        # bulk source excerpts and short-circuit straight to them, instantly, without re-fetching.
        shelf = "practical" if practical else "sources"
        spine_id = "card_spine_practical" if practical else "card_spine_sources"
        parent_card = {
            "id": parent_id, "kind": "practical" if practical else "reference",
            "title": str(doc.get("title") or subj)[:140],
            "body": (f"A source fetched on the call for {subj!r}: "
                     f"{str(doc.get('title') or '')[:160]} (license as reported by the source: "
                     f"{str(doc.get('license') or 'unstated')[:60]}; "
                     + ("verified public domain — released to the shared library."
                        if pd else "not yet verified — held for review.")
                     + " Kept whole in the ark; the passages carded beneath this one are cut "
                     "from it, and each names the exact place it came from."),
            "source": {"label": str(doc.get("title") or "")[:200],
                       "url": str(doc.get("url") or ""), "domain": "",
                       "authority_tier": "primary_pd"},
            "shelf": shelf, "box": "foxfire" if practical else "source", "subject": subj,
            "bands": sorted({w for w in subj.lower().split() if len(w) > 2})[:10]
                     + (["practical", "foxfire"] if practical else ["source"]),
            "connections": [{"to_card_id": spine_id, "relationship": "member_of",
                             "evidence": "a primary source the tortoise went and found"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public",
            "lifecycle_stage": "public" if pd else "public_review",
            "volatility": "permanent", "surface": "secular", "generated": False,
            "extra": {"source_sha256": sha, "crafted_from": str(doc.get("url") or ""),
                      "license": str(doc.get("license") or "")[:120], "pd_released": pd,
                      "tortoise": True},
        }
        # a released PD source needs no review queue; an uncertain one is marked for the operator.
        parent = parent_card if pd else _unchecked.mark(parent_card)
        for c in cards:                       # the span cards ride at the parent's stage AND shelf
            c["lifecycle_stage"] = "public" if pd else "public_review"
            c["shelf"] = shelf
            ex = dict(c.get("extra") or {})
            ex["tortoise"] = True
            c["extra"] = ex
        # The spine must exist before the members that hang off it, or the graft dangles (the same
        # no-orphan rule find._mint_doc keeps). _keep is idempotent, so re-asserting it costs nothing.
        spine = _find._spine_card(shelf)
        kept = _keep(([spine] if spine else []) + [parent] + cards)
        return {"status": "carded", "source_card": parent, "cards": cards,
                "kept": kept, "sha256": sha, "plane": plane,
                "held_for_review": (not pd), "released_public": pd,
                "message": (f"Not in the keeping, so it was fetched and cut on the call — "
                            f"{len(cards)} passage(s) from {str(doc.get('title') or '')[:80]!r}, "
                            "kept so the next asking finds them at once."
                            + (" A verified public-domain source — added to the shared library."
                               if pd else " Held for a copyright check before it joins the "
                               "shared public library."))}

    return {"status": "nothing_found",
            "message": "the archives were searched and no openable text spoke to this subject"}


def _keep(cards: List[Dict[str, Any]]) -> int:
    """Write through the mint's own store — the same file and the same live-corpus add that
    find._mint_doc uses, so pulled cards and minted citations live in one place. Idempotent."""
    import json as _json
    import os as _os
    from pathlib import Path

    base = _os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    p = Path(base) / "web_cache.jsonl"
    existing = set()
    if p.is_file():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    existing.add(_json.loads(ln).get("id"))
                except ValueError:
                    pass
    wrote = 0
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            for c in cards:
                if c.get("id") in existing:
                    continue
                fh.write(_json.dumps(c, ensure_ascii=False) + "\n")
                existing.add(c.get("id"))
                wrote += 1
                try:
                    from . import corpus as _c
                    _c.add_to_default(c)
                except Exception:  # noqa: BLE001 — visible next restart rather than lost
                    pass
    except OSError:
        return wrote
    return wrote


__all__ = ["expand", "pull_and_card", "offline", "PLANES"]
