#!/usr/bin/env python3
"""THE SHEPHERD'S ROUNDS — little knowledge miners, sent down on purpose and watched.

    PYTHONPATH=src python tools/shepherd_rounds.py                    # dry-run: what WOULD be dug
    PYTHONPATH=src python tools/shepherd_rounds.py --apply            # dig, and file the options
    PYTHONPATH=src python tools/shepherd_rounds.py --choose want_x 1 --by "Matt Harris"

Matt, 2026-08-01, the design in his words, each one now a mechanism:

  "little knowledge miners. Coal mining is probably the best metaphor."
      Each miner is DUMB and crafted for its task. This tool never wanders: it digs only where
      the want ledger points (THE MAP), and only when a person asked.

  "You need maps, and sanitation/filtration."
      The map is the ledger. Filtration is layered: the Tortoise's own provider whitelist
      (public-domain / open-access sources only), the queen's option shape (label + url +
      snippet, attributed, capped), and the scrub before anything is stored.

  "canaries to shut them down if they aren't conditions for life"
      Every miner carries a canary: consecutive failures drop it for the whole run, said out
      loud. WEB_FIND_DISABLED is the master canary — no network work at all when it is set.

  "branches that can be cut off, so you don't have to completely rebuild"
      Every option is stamped with its miner and run id (the shaft-tags). A source later found
      poisoned is excised by a query over those tags — a branch cut, not a rebuild.

  "Self healing. Always from source to source."
      A minted card records the URL and label it came FROM. Healing re-mines from that origin —
      never patches a copy from a copy. (The assay's `refill_from_source` repair is the same law
      applied to the whole keeping.)

The choosing stays human: `--choose` requires a name, mints ONE card from ONE option, roots it
(nothing isolated), closes the want with an edge to what it produced, and says plainly that a
restart is needed before the new card serves.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import corpus, sources, wants  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

CANARY_LIMIT = 3          # consecutive failures before a miner is shut down for the run


def _run_id() -> str:
    return time.strftime("run_%Y%m%d_%H%M%S", time.gmtime())


def _miner_catalogue(want: dict) -> list:
    """The first miner never leaves the mine: it re-checks OUR OWN catalogue, because a want may
    have been filled since it was opened. Retrieve-first, even on the rounds."""
    hits = corpus.search(want.get("query") or "", limit=3)
    return [{"label": f"already in the keeping: {h.get('title', h.get('id'))}",
             "url": f"/card/{h.get('id')}", "snippet": (h.get("snippet") or "")[:300],
             "domain": "the-keeping", "miner": "catalogue"} for h in (hits or [])]


def _miner_tortoise(want: dict, config) -> list:
    """The slow, sure path — find.py's whitelisted public-domain / open-access providers. The
    miner itself adds no judgement: whatever filtration lives in the Tortoise is the filtration."""
    from concordance import find
    if not find.enabled():
        return []                              # the master canary: no network work when disabled
    result = find.find_and_check(want.get("query") or "", config)
    if not result:
        return []

    # READ THE SHAPE THE FINDER ACTUALLY RETURNS. This miner used to read `source`, `title` and
    # `body` off the top level — keys `find_and_check` has never produced. It returns
    # {answer, checks_verdict, documents, framed, source_note}. So EVERY option this miner ever
    # filed was `label="found source", url="", snippet=""`: unactionable, unanchorable, and
    # indistinguishable from a real find in the ledger.
    #
    # Nothing caught it because the option was structurally VALID — strings, within their caps —
    # just empty, and no one had ever run `--choose` all the way to a body. A well-formed lie
    # passes every check that only looks at form. Found 2026-08-01 the first time the loop was
    # driven end to end against the Rigveda.
    out = []
    for d in (result.get("documents") or [])[:5]:      # several, so a person can CHOOSE
        url = str(d.get("url") or "").strip()
        if not url:
            continue                                   # an option nobody can act on is not an option
        out.append({
            "label": str(d.get("title") or url)[:200],
            "url": url[:500],
            "snippet": (f"{d.get('source') or 'source'} · {d.get('format') or 'document'} · "
                        f"{d.get('tier') or 'tier?'} · {d.get('license') or 'license unstated'}")[:600],
            "domain": str(d.get("source") or "")[:60],
            "miner": "tortoise",
        })
    return out


MINERS = (("catalogue", _miner_catalogue), )
NET_MINERS = (("tortoise", _miner_tortoise), )


def rounds(apply: bool, limit: int) -> int:
    run = _run_id()
    ledger = wants.fold()
    open_wants = [w for w in ledger.values() if w["state"] == "open"][:limit]
    if not open_wants:
        print("the want list has no open wants — the library is not missing anything it knows of")
        return 0

    config = EngineConfig("secular")
    canaries: dict = {}
    dug = skipped = 0
    print(f"{'DRY-RUN — nothing filed' if not apply else 'THE ROUNDS'} · {run} · "
          f"{len(open_wants)} open want(s)\n")
    for w in open_wants:
        print(f"  {w['id']}  ({w['asks']} ask{'s' if w['asks'] != 1 else ''})  "
              f"{(w.get('query') or w.get('card_id'))[:60]}")
        for name, miner in MINERS + NET_MINERS:
            if canaries.get(name, 0) >= CANARY_LIMIT:
                continue                       # this miner's canary died; it stays shut down
            try:
                found = miner(w, config) if miner is _miner_tortoise else miner(w)
                canaries[name] = 0
            except Exception as exc:  # noqa: BLE001 — a miner that dies is counted, never fatal
                canaries[name] = canaries.get(name, 0) + 1
                if canaries[name] >= CANARY_LIMIT:
                    print(f"     CANARY: miner {name!r} shut down for this run "
                          f"({CANARY_LIMIT} consecutive failures; last: {exc})")
                continue
            for src in found:
                src["run"] = run               # the shaft-tag: which run dug this
                if apply:
                    r = wants.add_option(w["id"], src)
                    ok = r.get("ok")
                else:
                    ok = True
                print(f"     {'filed' if (apply and ok) else 'would file'}  "
                      f"[{src['miner']}] {src['label'][:64]}")
                dug += 1 if ok else 0
                if apply and not ok:
                    skipped += 1
                    print(f"        refused by the queen: {r.get('error')}")
    print(f"\n{dug} option(s) {'filed' if apply else 'proposed'}"
          + (f", {skipped} refused" if skipped else ""))
    if not apply:
        print("Nothing was written. Re-run with --apply to file the options.")
    return 0


def choose(want_id: str, n: int, by: str) -> int:
    """The human act: one option becomes one card. Roots it, closes the want, says what remains."""
    if not by.strip():
        print("--choose carries a name: no anonymous minting")
        return 2
    w = wants.fold().get(want_id)
    if not w:
        print(f"no such want: {want_id}")
        return 2
    opts = w.get("options") or []
    if not (1 <= n <= len(opts)):
        print(f"want {want_id} has {len(opts)} option(s); pick 1..{len(opts)}")
        return 2
    o = opts[n - 1]

    # ANCHOR THE BODY, THEN MINT. Until now this minted a card whose body was the miner's
    # 600-character snippet with the origin in source.url — a POINTER, not a holding. Nothing
    # landed on a drive, nothing could be read offline, and "heal from what you hold" had nothing
    # to heal from. The loop ran miss -> want -> forage -> choose and stopped one step short of
    # an asset.
    #
    # The fetch is allowed to fail, and the card is minted either way — it simply says which.
    # A card that claims to hold what it does not is worse than a card that admits a gap.
    ark = sources.fetch(o.get("url") or "", want_id=want_id, chosen_by=by.strip(),
                        label=o.get("label") or "")
    anchored = ark.get("status") in (sources.HELD, sources.ALREADY)

    card = {
        "id": f"card_acq_{want_id.removeprefix('want_')}_{n}",
        "kind": "reference",
        "shelf": "acquisitions",
        "surface": "secular",
        "title": o["label"][:180],
        "body": (o.get("snippet") or o["label"])
                + f"\n\n[Acquired by request — want {want_id}, chosen by {by.strip()}. "
                  f"Source to source: heal by re-mining the origin below, never a copy.]"
                + (f"\n\nBody anchored: sha256 {ark['sha256'][:16]}… "
                   f"({ark['bytes']:,} bytes, {ark.get('media_type')}). Any holder of the drive can "
                   f"re-verify this against its own hash, offline, without trusting us."
                   if anchored else
                   f"\n\nBody NOT anchored — {ark.get('reason')}. The reference stands; the full "
                   f"text is not on this device."),
        "source": {"label": o["label"], "url": o.get("url") or "",
                   "ref": (w.get("query") or w.get("card_id") or "")[:120],
                   "authority_tier": "external_aligned",
                   # THE WAYBILL travels with the card: origin + hash, so a reader who holds the
                   # drive can find the body, and one who does not can still fetch and check it.
                   "ark": ({"sha256": ark["sha256"], "bytes": ark["bytes"],
                            "media_type": ark.get("media_type"),
                            "fetched_at": ark.get("fetched_at")} if anchored else None)},
        "extra": {"want_id": want_id, "miner": o.get("miner") or "", "run": o.get("run") or "",
                  "ark_status": ark.get("status"), "ark_reason": ark.get("reason", "")},
        "connections": [{"to_card_id": "card_k_floor_of_discovery", "relationship": "part_of",
                         "evidence": f"acquired on request (want {want_id}) — rooted, never an orphan"}],
    }
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    path = Path(base) / "acquired_cards.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    corpus.add_to_default(card)      # live insert IF a corpus is already built (a server); a CLI
    r = wants.close_want(want_id, card["id"], by)     # run relies on the file + restart instead
    if anchored:
        print(f"  body anchored: {ark['bytes']:,} bytes -> {ark['path']}")
        print(f"  sha256 {ark['sha256']}  ({ark['status']})")
    else:
        print(f"  body NOT anchored — {ark.get('reason')}  (the card says so, and stands)")
    print(f"minted {card['id']} on the acquisitions shelf"
          + ("" if r.get("ok") else f" (want close refused: {r.get('error')})"))
    print("filed to acquired_cards.jsonl — restart the services so every door serves it")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="file the dug options (default: dry-run)")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--choose", nargs=2, metavar=("WANT_ID", "N"), help="mint option N of a want")
    ap.add_argument("--drop", nargs=2, metavar=("WANT_ID", "REASON"),
                    help="a steward refuses a want — recorded with a reason, never erased")
    ap.add_argument("--by", default="", help="who is choosing — required with --choose")
    a = ap.parse_args()
    if a.drop:
        r = wants.drop_want(a.drop[0], a.drop[1], a.by)
        print(f"dropped {a.drop[0]}: {a.drop[1]}" if r.get("ok") else f"refused: {r.get('error')}")
        return 0 if r.get("ok") else 2
    if a.choose:
        return choose(a.choose[0], int(a.choose[1]), a.by)
    return rounds(a.apply, a.limit)


if __name__ == "__main__":
    sys.exit(main())
