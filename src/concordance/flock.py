"""FLOCK — the starling's rule (BOIDS, measured). A bird does not track every neighbor in its range; it
tracks a FIXED number of nearest neighbors — about six or seven — no matter how dense the flock (Ballerini
/ Cavagna / Giardina, STARFLAG, PNAS 2008/2010). This TOPOLOGICAL interaction (fixed count, not fixed
distance) is exactly why a murmuration stays coherent and scale-free: a turn crosses fifty thousand birds
as fast as five hundred, because each bird only ever answers to its handful.

Our mesh is the flock. A hub may hold hundreds of links (up to _MAX_LINKS), but coherence does not come from
answering to all of them — it comes from a small, well-woven interaction set. This picks each node's
topological neighborhood: its most tightly-woven handful (most shared neighbors, then most-connected, then
a stable id tie-break — deterministic, offline-reproducible). It reorders/annotates nothing on its own; the
map foregrounds the flock only when the lever is on.

GATED OFF by default (CONCORDANCE_FLOCK): `neighborhood` still computes (it is a pure helper), but the map
does not surface a flock until a node opts in, so the network view is byte-for-byte unchanged. Held for
review. The lever, once on, keeps the map coherent as the mesh grows — you see the handful you actually
move with, not a hairball. No signal travels here and no identity is read; this is topology only.
"""
from __future__ import annotations

import os
from typing import Dict, List, Sequence

_K = 7                         # the measured interaction set — a starling answers to ~6-7 neighbors


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_FLOCK", "").strip().lower() in ("1", "true", "yes", "on")


def neighborhood(center_links: Sequence[str], neighbor_links: Dict[str, Sequence[str]],
                 k: int = _K) -> List[str]:
    """The center's topological neighborhood: its k most tightly-woven direct links.

    `center_links` are the node's direct links; `neighbor_links` maps each of those to ITS own links.
    A neighbor is ranked by how many neighbors it SHARES with the center (the woven cluster — birds
    align with those they are most interconnected with), then by its own degree (a well-connected
    neighbor carries the turn farther), then by id so the result is stable and reproducible offline.
    Pure and side-effect-free; returns at most k ids, or all of them when there are fewer than k."""
    mine = {x for x in (center_links or []) if x}
    if not mine:
        return []
    ranked = []
    for nb in mine:
        nb_links = set(neighbor_links.get(nb) or ())
        shared = len(mine & nb_links)            # tightness of the weave with the center
        degree = len(nb_links)                   # how far this neighbor can carry a turn
        ranked.append((-shared, -degree, nb))
    ranked.sort()
    kk = max(1, int(k or _K))
    return [nb for _, _, nb in ranked[:kk]]
