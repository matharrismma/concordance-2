"""Unit-pin the genetics verifier (A2: verifier test-depth, 2026-10-06).

Standard molecular-biology operations, hand-checked:
  complement ATCG -> TAGC; reverse-complement ATCG -> CGAT; GC content of ATCG = 0.5;
  standard-code translation ATGGCC -> MA (Met-Ala). A wrong claim is caught; a missing field is
  NOT_APPLICABLE (never a false pass).
"""
from __future__ import annotations

from concordance.verifiers import genetics as G


def test_complementarity():
    assert G.verify_complementarity({"sequence": "ATCG", "claimed_complement": "TAGC"}).status == "CONFIRMED"
    assert G.verify_complementarity({"sequence": "ATCG", "claimed_complement": "CGAT"}).status == "MISMATCH"
    assert G.verify_complementarity({}).status == "NOT_APPLICABLE"


def test_reverse_complement():
    assert G.verify_reverse_complement({"sequence": "ATCG",
                                        "claimed_reverse_complement": "CGAT"}).status == "CONFIRMED"
    assert G.verify_reverse_complement({"sequence": "ATCG",
                                        "claimed_reverse_complement": "TAGC"}).status == "MISMATCH"


def test_gc_content():
    assert G.verify_gc_content({"sequence": "ATCG", "claimed_gc_fraction": 0.5}).status == "CONFIRMED"
    assert G.verify_gc_content({"sequence": "ATCG", "claimed_gc_fraction": 0.9}).status == "MISMATCH"


def test_codon_translation():
    assert G.verify_codon_translation({"sequence": "ATGGCC", "claimed_protein": "MA"}).status == "CONFIRMED"
    assert G.verify_codon_translation({"sequence": "ATGGCC", "claimed_protein": "MG"}).status == "MISMATCH"
