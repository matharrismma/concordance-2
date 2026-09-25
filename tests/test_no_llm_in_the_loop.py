"""No model in the loop — the guarantee, made load-bearing (2026-09-25).

The frozen identity is "a model of reality, not an LLM": the engine FINDS and VERIFIES; it never asks
a language model to generate an answer, and — the subtler seam — it never asks one to STRUCTURE a
plain claim into checkable form either. A plain-language claim is reduced to a checkable {domain, spec}
by deterministic extractors (`audit.extract`, surfaced through `discern`), so nothing in the serving
engine needs a model or an API key. The plain-claim door `POST /verify` proves it live: prose in →
extractors find the computable claims → the moat verifies → a re-checkable receipt out, with a
deterministic FIND fallback to sourced cards when nothing is computable. No key, no model, ever.

That has always been true by construction — there is no model-client import anywhere in the runtime —
but a guarantee that lives only in prose can be broken by one convenient import in a hurry (the exact
seam an external `check` wrapper filled with an LLM, which 401'd and reminded us the dependency is not
ours and not needed). This test makes the guarantee enforced: the whole serving engine (every module
under src/concordance — core AND every door) is parsed, and if any module imports a hosted-or-local
model client, or calls a model's generate endpoint, CI goes red.

Scope is the RUNTIME loop (src/concordance). Build-time seeders under tools/ are not the loop and are
not guarded here. AST-based on purpose: the codebase says "no LLM", "conduit, not oracle", "no model"
all over its prose and docstrings — those must never trip the guard, and only real imports/calls do.
"""
from __future__ import annotations

import ast
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "src" / "concordance"

# Single-token import roots that put a model in the loop — hosted LLM clients, local runners, and the
# ML frameworks a neural model would ride in on. None are present; the guard keeps it that way.
FORBIDDEN_IMPORT_ROOTS = {
    "anthropic", "openai", "cohere", "replicate", "together", "mistralai", "groq", "ollama",
    "llama_cpp", "ctransformers", "vertexai", "vllm", "transformers", "sentence_transformers",
    "huggingface_hub", "torch", "tensorflow", "keras", "onnxruntime",
}
# Dotted module prefixes (a bare root like "google" is legitimate; only these sub-packages are not).
FORBIDDEN_IMPORT_PREFIXES = ("google.generativeai", "google.genai")

# Call signatures that mean "generate with a model", whatever the client was named.
FORBIDDEN_CALL_SUFFIXES = ("messages.create", "chat.completions.create", "completions.create",
                           "generate_content", "chat.complete")


def _py_files():
    return sorted(ENGINE.rglob("*.py"))


def _forbidden_module(name: str) -> bool:
    if not name:
        return False
    if name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
        return True
    return any(name == p or name.startswith(p + ".") for p in FORBIDDEN_IMPORT_PREFIXES)


def _attr_chain(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    parts.reverse()
    return ".".join(parts)


def test_no_model_client_imports():
    """No module in the runtime imports an LLM client or an ML framework a model would ride in on."""
    offenders = []
    for f in _py_files():
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if _forbidden_module(a.name):
                        offenders.append(f"{f.name}: import {a.name}")
            elif isinstance(node, ast.ImportFrom):
                if not node.level and _forbidden_module(node.module or ""):
                    offenders.append(f"{f.name}: from {node.module} import ...")
    assert not offenders, (
        "a model was wired into the runtime loop — the engine FINDS and VERIFIES, it never "
        "generates and never asks a model to structure a claim:\n  " + "\n  ".join(offenders))


def test_no_model_generation_calls():
    """No module calls a model's generate endpoint, however the client was named or imported."""
    offenders = []
    for f in _py_files():
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                chain = _attr_chain(node.func)
                if any(chain == s or chain.endswith("." + s) for s in FORBIDDEN_CALL_SUFFIXES):
                    offenders.append(f"{f.name}: {chain}(...)")
    assert not offenders, (
        "a model-generation call is present in the runtime loop:\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    import pytest
    raise SystemExit(int(pytest.main([__file__, "-q"])))
