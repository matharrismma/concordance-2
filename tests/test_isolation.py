"""Moat-guard isolation test — the new side-modules can NEVER perturb the moat.

The moat is the deterministic SEALED math: 58/58 domains, 0 false-positives. That guarantee
lives entirely in `concordance.verifiers.*` (the 71 domain verifiers + their registry) and the
`concordance.derivation` engine that drives them. If a *side*-module (identity, coach, badges —
portable identity, the reading coach, shared-study badges) could reach into that machinery, then
merely adding one of these features could shift a verdict or open a false-positive. It must be
impossible by construction.

This test proves the isolation two ways for each side-module:

  1. SOURCE (direct): the module's own source imports NOTHING from `concordance.verifiers` or
     `concordance.derivation`. A grep-with-a-parser: we walk the AST so a commented-out or
     string-literal mention never trips it, and a real `import` always does.

  2. RUNTIME (transitive): importing the module in a *fresh* interpreter must not pull the
     moat LOGIC into `sys.modules` — i.e. the `concordance.derivation` engine or any DOMAIN
     verifier module (`concordance.verifiers.mathematics`, `.medicine`, ...). Those are what
     compute and seal a verdict; if importing a side-module loaded one, adding that feature
     could move a verdict. Two inert leaves under `concordance.verifiers` are allowed, because
     the sanctioned floor already pulls them transitively and neither runs any verification:
       - `concordance.verifiers` — the package `__init__`: just the alias->module-path string
         table (imports are LAZY; no domain verifier is loaded when the registry is imported).
       - `concordance.verifiers.base` — the stdlib-only `VerifierResult` dataclass (the shape of
         a receipt). `concordance.receipts` / `signing` use it, exactly as `steward` already does.
     This is not a loophole: the already-shipped `steward` side-module pulls those same two leaves
     and no more. `derivation` and every domain verifier stay unloaded — that is the moat, sealed.

TOLERANT BY DESIGN: identity/coach/badges do not all exist yet. A module that isn't present is
SKIPPED, so this test passes today and stays a live guard the moment each module lands.

Sovereign: stdlib only. Runnable with pytest OR `python tests/test_isolation.py`.
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))

# The side-modules under guard. Adding any of these must never touch the moat.
SIDE_MODULES = ["concordance.identity", "concordance.coach", "concordance.badges", "concordance.groups"]

# The moat machinery no side-module may reach.
FORBIDDEN_ROOTS = ("concordance.verifiers", "concordance.derivation")

# The inert leaves under a forbidden root that the SANCTIONED floor already pulls transitively,
# neither of which runs any verification (the already-shipped `steward` side-module pulls exactly
# these two and no more):
#   - concordance.verifiers       : the registry __init__ — an alias->module-path string table;
#                                   its imports are LAZY, so no domain verifier loads with it.
#   - concordance.verifiers.base  : the stdlib-only VerifierResult dataclass (the receipt shape);
#                                   `receipts`/`signing` depend on it to seal.
# Everything ELSE under concordance.verifiers.* (the 71 DOMAIN verifiers) — and all of
# concordance.derivation (the engine) — is the moat, and stays forbidden.
ALLOWED_LEAVES = {"concordance.verifiers", "concordance.verifiers.base"}


def _module_file(dotted: str) -> Path | None:
    """The source file for a dotted module name, or None if it isn't installed yet."""
    parts = dotted.split(".")[1:]  # drop the top-level 'concordance'
    p = _SRC / "concordance"
    for part in parts[:-1]:
        p = p / part
    leaf = parts[-1]
    cand = p / f"{leaf}.py"
    if cand.exists():
        return cand
    pkg = p / leaf / "__init__.py"
    if pkg.exists():
        return pkg
    return None


def _present_modules() -> list[str]:
    return [m for m in SIDE_MODULES if _module_file(m) is not None]


def _is_forbidden(name: str) -> bool:
    if name in ALLOWED_LEAVES:
        return False
    return any(name == r or name.startswith(r + ".") for r in FORBIDDEN_ROOTS)


def _imported_names(source: str) -> set[str]:
    """Every fully-qualified module a source file imports, resolved from the AST.

    Handles `import a.b`, `from a.b import c`, and package-relative `from . import x` /
    `from .x import y` (level>0), which resolve against the concordance package.
    """
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import inside the concordance package. A side-module lives at
                # concordance.<name>, so level-1 relative resolves against `concordance`.
                base = "concordance"
                mod = f"{base}.{node.module}" if node.module else base
                found.add(mod)
                for alias in node.names:
                    found.add(f"{mod}.{alias.name}")
            elif node.module:
                found.add(node.module)
                for alias in node.names:
                    found.add(f"{node.module}.{alias.name}")
    return found


# --------------------------------------------------------------------------- #
# 1. SOURCE (direct) — the module's own imports.
# --------------------------------------------------------------------------- #

def test_side_modules_do_not_import_the_moat_in_source():
    present = _present_modules()
    if not present:
        # None have landed yet — nothing to guard, but the guard is armed.
        return
    offenders: dict[str, list[str]] = {}
    for dotted in present:
        src = _module_file(dotted).read_text(encoding="utf-8")
        bad = sorted(n for n in _imported_names(src) if _is_forbidden(n))
        if bad:
            offenders[dotted] = bad
    assert not offenders, (
        "side-module imports the moat directly (this could perturb 58/58 / 0-FP): "
        f"{offenders}"
    )


# --------------------------------------------------------------------------- #
# 2. RUNTIME (transitive) — import in a clean interpreter, inspect sys.modules.
# --------------------------------------------------------------------------- #

_CHILD = textwrap.dedent(
    """
    import sys
    sys.path.insert(0, {src!r})
    __import__({mod!r})
    forbidden_roots = {roots!r}
    allowed = {allowed!r}
    leaked = sorted(
        m for m in sys.modules
        if any(m == r or m.startswith(r + ".") for r in forbidden_roots)
        and m not in allowed
    )
    print("\\n".join(leaked))
    """
)


def _runtime_leak(dotted: str) -> list[str]:
    code = _CHILD.format(
        src=str(_SRC),
        mod=dotted,
        roots=FORBIDDEN_ROOTS,
        allowed=sorted(ALLOWED_LEAVES),
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"clean-interpreter import of {dotted} failed:\n{proc.stderr}"
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def test_importing_side_modules_does_not_load_the_moat_at_runtime():
    present = _present_modules()
    if not present:
        return
    leaks: dict[str, list[str]] = {}
    for dotted in present:
        leaked = _runtime_leak(dotted)
        if leaked:
            leaks[dotted] = leaked
    assert not leaks, (
        "importing a side-module pulled the moat machinery into sys.modules "
        f"(only {sorted(ALLOWED_LEAVES)} is allowed): {leaks}"
    )


# --------------------------------------------------------------------------- #
# Meta: the guard is well-formed even before any side-module exists.
# --------------------------------------------------------------------------- #

def test_guard_is_meaningful_and_self_consistent():
    # Every allowed leaf must itself sit under (or equal) a forbidden root — else the exception
    # is pointless. (The registry package IS a root; the base dataclass sits under one.)
    for leaf in ALLOWED_LEAVES:
        assert any(leaf == r or leaf.startswith(r + ".") for r in FORBIDDEN_ROOTS), (
            f"allowed leaf {leaf!r} is not under a forbidden root — exception is meaningless"
        )
    # The classifier does what it says: the MOAT (domain verifiers + the engine) is forbidden;
    # the two inert registry leaves are allowed.
    assert _is_forbidden("concordance.verifiers.mathematics")   # a domain verifier — the moat
    assert _is_forbidden("concordance.verifiers.medicine")      # another domain verifier
    assert _is_forbidden("concordance.derivation")              # the engine that runs the moat
    assert not _is_forbidden("concordance.verifiers")           # inert alias table
    assert not _is_forbidden("concordance.verifiers.base")      # inert receipt dataclass
    assert not _is_forbidden("concordance.receipts")            # a sanctioned public helper
    # The AST parser resolves absolute and relative imports to fully-qualified names.
    names = _imported_names(
        "import concordance.derivation\n"
        "from concordance.verifiers import mathematics\n"
        "from . import receipts\n"
        "from .verifiers import base\n"
    )
    assert "concordance.derivation" in names
    assert "concordance.verifiers.mathematics" in names
    assert "concordance.receipts" in names
    assert "concordance.verifiers.base" in names


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    present = _present_modules()
    if present:
        print(f"\nMoat-guard: {len(present)} side-module(s) verified isolated from the moat: "
              + ", ".join(present))
    else:
        print("\nMoat-guard armed: identity/coach/badges not present yet — "
              "the instant any lands, it is held to import nothing from the moat.")
