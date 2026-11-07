# Changelog

## 2026-11-06

- An Integer or Rational power past the bound (`_MAX_POW_BITS`, 2**20 bits) is refused where it is
  computed, and so is a root that would multiply out past it or leave more than 2**14 bits unfactored.
  A claim that reaches one reads as not checkable, never as an answer.
- Arithmetic holds the same bound: `compute` measures every power and product before computing it,
  and declines a text past 500 characters.

This is a floor at those two powers, not at every long read. Other long reads stay open to run
2026-11-06-engine-cells, which holds the list.
