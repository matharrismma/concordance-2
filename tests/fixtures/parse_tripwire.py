"""A runtime tripwire on sympy's string parser, for the tests that prove no text reaches it.

It wraps parse_expr at sympy.parsing.sympy_parser, the attribute sympify looks up on every call, so it sees sympify,
S, Rational, simplify and every other sympy entry that parses a string, by what they do and not by their names. A
wrapper on sympy.sympify would see none of them: each holds its own reference. It never wraps a builtin.

Arm it only after sympy and its units are imported, because importing the units parses literal names, and only
around the parser side of a test, because a test's own sympify oracle parses text on purpose. The real parse still
runs, so an input that would have done something still does it and the test can see that. The Meijer G table is built
before arming for the same reason: sympy builds it on first use and it parses a literal of sympy's own, which a stick's
integral in this repo reaches. That text is sympy's, never a request's, and building it first keeps every str that
arrives while armed a failure.

It sees only the branches the tests exercise, and proves nothing about an input no test sends. The default-deny walk
in tests/test_no_other_route.py is the static half.
"""
from __future__ import annotations

import contextlib
from typing import Iterator, List

_built = False


def _build_sympys_own_tables() -> None:
    global _built
    if not _built:
        import sympy
        x = sympy.Symbol("x")
        sympy.integrate(sympy.exp(-x ** 2), (x, 0, sympy.oo), meijerg=True)
        _built = True


@contextlib.contextmanager
def tripwire() -> Iterator[List[str]]:
    """Yields the list of every str that reached parse_expr while armed: empty is the only pass."""
    import sympy.parsing.sympy_parser as parser
    import sympy.physics.units  # noqa: F401  importing the units parses literal names: never count those

    _build_sympys_own_tables()
    real = parser.parse_expr
    hits: List[str] = []

    def wrapped(s, *args, **kwargs):
        if isinstance(s, str):
            hits.append(s)
        return real(s, *args, **kwargs)

    parser.parse_expr = wrapped
    try:
        yield hits
    finally:
        parser.parse_expr = real
