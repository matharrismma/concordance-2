#!/usr/bin/env python3
"""Sorting algorithms — measured witnesses for the sorting_algorithms stick (pure python, no dependencies).

The stick (data/sticks/sorting_algorithms.json; run `tick.py sorting_algorithms`) SEALS the arithmetic of the
bounds; this demo MEASURES the same numbers by running the algorithms and counting:

  * insertion sort on 1000 reversed items   -> 499,500 comparisons   (n(n-1)/2, the worst case)
  * merge sort over all 8! = 40,320 orders  -> worst 17 comparisons  (n lg n - 2^lg n + 1 = 24 - 8 + 1)
  * Batcher's odd-even merge network, n = 8 -> 19 comparators, depth 6, sorts all 2^8 zero-one inputs
  * the bitonic sorter, n = 8               -> 24 comparators, depth 6, sorts all 2^8 zero-one inputs
  * timsort's minrun for n = 1000           -> 63  (CPython listsort.txt: top six bits of n, +1 if the rest are set)
  * the comparison lower bound for n = 8    -> 16  (ceil(log2 8!) — and Ford-Johnson reaches it)

Knuth's zero-one principle (TAOCP vol. 3, 5.3.4): a comparator network sorts every input iff it sorts every
sequence of zeros and ones — so 256 inputs prove the 8-wire networks. Nothing here is generated: the counts are
the algorithms' own, and the asserts pin them to the sealed values.

    python tools/sorting_demo.py
"""
from __future__ import annotations

import math
from itertools import permutations, product
from typing import Iterator, List, Sequence, Tuple

Comparator = Tuple[int, int]


# --- comparison counting -------------------------------------------------------------------------------------------

def insertion_sort_comparisons(a: Sequence[int]) -> int:
    xs = list(a)
    n = 0
    for i in range(1, len(xs)):
        key = xs[i]
        j = i - 1
        while j >= 0:
            n += 1
            if xs[j] > key:
                xs[j + 1] = xs[j]
                j -= 1
            else:
                break
        xs[j + 1] = key
    return n


def merge_sort_comparisons(a: Sequence[int]) -> int:
    count = 0

    def rec(xs: List[int]) -> List[int]:
        nonlocal count
        if len(xs) <= 1:
            return xs
        mid = len(xs) // 2
        left, right = rec(xs[:mid]), rec(xs[mid:])
        out: List[int] = []
        i = j = 0
        while i < len(left) and j < len(right):
            count += 1
            if left[i] <= right[j]:
                out.append(left[i]); i += 1
            else:
                out.append(right[j]); j += 1
        out.extend(left[i:]); out.extend(right[j:])
        return out

    rec(list(a))
    return count


# --- sorting networks ------------------------------------------------------------------------------------------------

def batcher_odd_even_merge_sort(n: int) -> List[Comparator]:
    """Batcher 1968, odd-even merge sort on n = 2^k wires; comparators as (low, high) pairs."""
    def merge(lo: int, hi: int, r: int) -> Iterator[Comparator]:
        step = r * 2
        if step < hi - lo:
            yield from merge(lo, hi, step)
            yield from merge(lo + r, hi, step)
            for i in range(lo + r, hi - r, step):
                yield (i, i + r)
        else:
            yield (lo, lo + r)

    def sort(lo: int, hi: int) -> Iterator[Comparator]:
        if hi - lo >= 1:
            mid = lo + (hi - lo) // 2
            yield from sort(lo, mid)
            yield from sort(mid + 1, hi)
            yield from merge(lo, hi, 1)

    return list(sort(0, n - 1))


def bitonic_sorter(n: int) -> List[Comparator]:
    """Batcher 1968, the bitonic sorter on n = 2^k wires (ascending); comparators as (low, high)."""
    out: List[Comparator] = []
    k = 2
    while k <= n:
        j = k // 2
        while j >= 1:
            for i in range(n):
                partner = i ^ j
                if partner > i:
                    out.append((i, partner) if (i & k) == 0 else (partner, i))
            j //= 2
        k *= 2
    return out


def network_depth(comparators: Sequence[Comparator]) -> int:
    """Layers: a comparator sits one layer after the latest of its two wires."""
    at = {}
    depth = 0
    for a, b in comparators:
        layer = max(at.get(a, 0), at.get(b, 0)) + 1
        at[a] = at[b] = layer
        depth = max(depth, layer)
    return depth


def sorts_all_zero_one(comparators: Sequence[Comparator], n: int) -> bool:
    for bits in product((0, 1), repeat=n):
        w = list(bits)
        for a, b in comparators:
            if w[a] > w[b]:
                w[a], w[b] = w[b], w[a]
        if any(w[i] > w[i + 1] for i in range(n - 1)):
            return False
    return True


# --- timsort's minrun (CPython Objects/listsort.txt) ------------------------------------------------------------

def minrun(n: int) -> int:
    r = 0
    while n >= 64:
        r |= n & 1
        n >>= 1
    return n + r


def comparison_lower_bound(n: int) -> int:
    return math.ceil(math.log2(math.factorial(n)))


def run() -> dict:
    ins = insertion_sort_comparisons(range(1000, 0, -1))
    merge_worst8 = max(merge_sort_comparisons(p) for p in permutations(range(8)))
    b8 = batcher_odd_even_merge_sort(8)
    bt8 = bitonic_sorter(8)
    return {
        "insertion_reversed_1000": ins,
        "merge_sort_worst_8": merge_worst8,
        "batcher8_comparators": len(b8), "batcher8_depth": network_depth(b8), "batcher8_sorts": sorts_all_zero_one(b8, 8),
        "bitonic8_comparators": len(bt8), "bitonic8_depth": network_depth(bt8), "bitonic8_sorts": sorts_all_zero_one(bt8, 8),
        "minrun_1000": minrun(1000),
        "lower_bound_8": comparison_lower_bound(8),
        "lower_bound_1000": comparison_lower_bound(1000),
    }


def main() -> int:
    r = run()
    for k, v in r.items():
        print(f"  {k:26s} {v}")
    assert r["insertion_reversed_1000"] == 499500, r
    assert r["merge_sort_worst_8"] == 17, r
    assert (r["batcher8_comparators"], r["batcher8_depth"], r["batcher8_sorts"]) == (19, 6, True), r
    assert (r["bitonic8_comparators"], r["bitonic8_depth"], r["bitonic8_sorts"]) == (24, 6, True), r
    assert r["minrun_1000"] == 63, r
    assert r["lower_bound_8"] == 16 and r["lower_bound_1000"] == 8530, r
    print("OK - every measured count matches the sealed arithmetic on the sorting_algorithms stick")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
