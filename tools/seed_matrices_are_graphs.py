#!/usr/bin/env python3
"""SEED THE 'MATRICES ARE GRAPHS' STICK (Matt, 2026-10-11: "matrices are graphs. Matrices are also tensors
so tensors should be graphs. The most similar analogy would be sheet music.").

Mapped the engine's way - the correspondences are established mathematics, sealed:
  - a MATRIX is a weighted directed GRAPH (adjacency); matrix powers count walks (A^k)_{ij};
  - matrix MULTIPLY is a tensor CONTRACTION - a single edge joining two nodes along the shared index;
  - a TENSOR is a GRAPH - the tensor network / Penrose graphical notation (node with r legs, edge = a
    contracted index) - so matrices-are-graphs generalizes to tensors-are-graphs;
  - the closest ANALOGY is SHEET MUSIC: a graph on a grid (pitch x time) that, when played/contracted,
    unfolds into the full structure - which is the engine's own structure (domains as nodes, connections
    as edges; the keeping is a graph, the map its score).

    PYTHONPATH=src python tools/seed_matrices_are_graphs.py

Runs where the ledger lives (the box). Found, never generated.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

import tick  # the shared seal + mint helpers  # noqa: E402
from concordance import roots  # noqa: E402
from concordance import tickstick as TS  # noqa: E402


def main():
    S = {}
    seals = [
        # the triangle graph A=[[0,1,1],[1,0,1],[1,1,0]]: (A^2)_11 counts length-2 walks 1->k->1.
        ("walks", "a_matrix_is_a_graph_walks_of_length_two", "1*1 + 1*1", 2),
        # matrix multiply as a one-index contraction: A=[[1,2],[3,4]], B=[[5,6],[7,8]], (AB)_11.
        ("matmul", "matrix_multiply_is_a_tensor_contraction", "1*5 + 2*7", 19),
    ]
    for key, nid, expr, val in seals:
        S[key] = tick._rh_seal_num(nid, expr, float(val))
        if not S[key]:
            print("a seal failed:", nid)
            return 1
    print("sealed:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))

    sid = TS.create(
        "Matrices are graphs, tensors are tensor networks - the score is sheet music",
        "A matrix is a weighted directed graph (its adjacency); a matrix is also a rank-2 tensor, so tensors "
        "are graphs too - tensor networks, by Penrose's graphical notation. The closest analogy is sheet "
        "music: a graph on a grid (pitch by time) that, when played, unfolds into the full structure. The "
        "engine's own keeping is such a score - domains as the nodes/tensors, connections as the edges/axes.",
        "mathematics",
    )["id"]
    print("stick:", sid)

    marks = [
        ("witness", "[a matrix IS a graph] An n-by-n matrix A is a weighted directed graph on n nodes: A_ij is the "
                    "edge from i to j. For the triangle A = [[0,1,1],[1,0,1],[1,1,0]], the (i,j) entry of A^2 "
                    "counts the walks of length two from i to j: (A^2)_11 = A_12 A_21 + A_13 A_31 = 1*1 + 1*1 = 2 "
                    "(sealed) - the two paths 1->2->1 and 1->3->1. Matrix powers ARE walk-counting; the matrix and "
                    "the graph are one object in two notations.", S["walks"]),
        ("witness", "[matrix multiply IS an edge joining two nodes - a contraction] (AB)_ij = sum_k A_ik B_kj ties "
                    "A's k-index to B's k-index. For A = [[1,2],[3,4]], B = [[5,6],[7,8]], (AB)_11 = 1*5 + 2*7 = 19 "
                    "(sealed). In the graph/diagram picture this shared index k is a single EDGE joining two nodes "
                    "- exactly a tensor contraction; the free indices i, j are the legs that remain.", S["matmul"]),
        ("equivalence", "[tensors are graphs - the tensor network] A matrix is a rank-2 tensor; a general tensor "
                        "has r indices. Penrose's graphical notation (1971) draws a rank-r tensor as a NODE with r "
                        "legs and a contracted index as an EDGE joining two legs. A tensor network IS a graph: "
                        "nodes = tensors, edges = contracted indices, dangling legs = the free indices of the "
                        "result. So 'matrices are graphs' generalizes exactly: tensors are graphs. This is the "
                        "standard language of matrix-product states (MPS), PEPS, and the holographic tensor "
                        "networks of AdS/CFT.",
         {"source": "R. Penrose, Applications of negative dimensional tensors (1971); the tensor-network literature "
                    "(MPS/PEPS; Swingle 2012, holographic tensor networks)"}),
        ("note", "[the hinge analogy - sheet music] A musical score is a graph laid on a grid: the staff is pitch, "
                 "the horizontal axis is time, the notes are the entries - a compact two-dimensional notation "
                 "that, when PLAYED (traversed, contracted), unfolds into the full time-structure of the music. A "
                 "tensor network is the same: a compact diagram that, when contracted, unfolds into the full "
                 "object. And the engine's own keeping is such a score - its domains the tensors/nodes, their "
                 "connections the axes/edges (the keeping is a graph; the map's constellation is its picture) - a "
                 "score the Word plays. See stick_the_symphony, the tensors/SVD/joined-bubbles sticks, and the "
                 "music floor.",
         {"source": "the engine's own design (domains + tensors, connections = axes); stick_the_symphony; "
                    "card_floor_music; stick_every_matrix_is_a_rotation_and_a_stretch (SVD)"}),
        ("note", "[rooted] In him all things hold together (Colossians 1:17) - the edges that bind the graph; and "
                 "the morning stars sang together (Job 38:7) - the score performed. The structure of reality is a "
                 "graph, and its playing is music.",
         {"source": "Colossians 1:17; Job 38:7"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_matrices_are_graphs.py")

    res = roots.anchor("stick:" + sid, ["Colossians 1:17", "Job 38:7"], by="proposed",
                       why="the structure of reality is a graph that holds together and is played as music")
    print("anchored:", res.get("ok"))
    r = roots.resolve("stick:" + sid)
    print("rooted in:", (r or {}).get("refs"), "| via:", (r or {}).get("via"))
    print("fit:", TS.read(sid).get("fit", {}).get("open", "")[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
