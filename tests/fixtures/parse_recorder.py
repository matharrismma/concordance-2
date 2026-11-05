"""Records what this repo's runtime sources hand the parser, for tests/test_parse_differential.py.

A static read cannot see these texts: tools/tick.py builds its numeric claims with f-strings, and src/concordance/audit.py
builds each form from a sentence. So this runs each source for real and records every text as the parser receives it,
under the tripwire. It runs each source as its own test or tool does, on the shipped data, never on a test's two-line
fixture: the front door over data/frontdoor_claims.json, recall over data/recall_phrasings.json, and every stick in the
catalog through tools/tick_golden.py's fresh temp keeping.

It is a process of its own because tools/tick.py and tools/tick_golden.py set environment variables when imported, and
the cold seal path keeps caches in the process. None of that may reach the rest of the suite. Everything it writes goes
to a temp keeping, and it writes its answer to the file it is given.

    python tests/fixtures/parse_recorder.py OUT.json
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FRONT_DOOR, RECALL = "tests/test_frontdoor.py", "tests/test_recall.py"
PROBES, AUDIT, TICK = "eval/live_probes.jsonl", "src/concordance/audit.py", "tools/tick.py"


class Recorder:
    """Stands in for parse_expression and calls it. A read is (source, kind, text, names), as the caller made it."""

    def __init__(self, parse, unit_table):
        self.parse, self.unit_table = parse, unit_table
        self.source = ""
        self.reads: set = set()
        self.calls: Counter = Counter()

    def __call__(self, text, names=None, rational=False, evaluate=True, word_mod=False):
        kind = "math" if word_mod else "unit" if names is self.unit_table else "equation"
        held = () if kind == "unit" else tuple(sorted(set(names or ()) - ({"oo", "inf"} if kind == "math" else set())))
        self.reads.add((self.source, kind, str(text), held))
        self.calls[self.source] += 1
        return self.parse(text, names, rational, evaluate, word_mod)


def inline_sentences(path: Path) -> List[str]:
    """The sentences a test file writes out itself: every "text" value in a dict literal."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [value.value for node in ast.walk(tree) if isinstance(node, ast.Dict)
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant) and key.value == "text"
            and isinstance(value, ast.Constant) and isinstance(value.value, str)]


def probe_parts(value: Any) -> Iterator[Tuple[str, Any]]:
    """Every spec and every plain sentence a probe's body holds, however deep."""
    if isinstance(value, dict):
        if isinstance(value.get("spec"), dict):
            yield "spec", value["spec"]
        if "mode" in value and "params" in value:
            yield "spec", value
        for key, item in value.items():
            if key in ("claim", "text", "situation") and isinstance(item, str):
                yield "sentence", item
            else:
                yield from probe_parts(item)
    elif isinstance(value, list):
        for item in value:
            yield from probe_parts(item)


def main(out: str) -> int:
    keeping = Path(tempfile.mkdtemp(prefix="nh_parse_recorder_"))
    os.environ["CONCORDANCE_DATA_DIR"] = str(keeping)
    os.environ.pop("CONCORDANCE_CAS_DIR", None)        # the cold seal path keeps its CAS beside each entry's keeping
    os.environ["WEB_FIND_DISABLED"] = "1"
    os.environ["CONCORDANCE_VERIFY_TIMEOUT_S"] = "1800"    # as tools/tick.py sets it, before derivation is imported
    os.environ["CONCORDANCE_ARK_MILLENNIUM"] = str(keeping / "no_ark")     # the box's tables, held by no clean clone
    sys.path[:0] = [str(HERE), str(ROOT / "src"), str(ROOT / "tools")]

    from concordance import audit
    from concordance.config import EngineConfig
    from concordance.verifiers import mathematics as M
    from concordance.verifiers import physics as P
    from parse_tripwire import tripwire

    M._ensure_sympy()
    P._ensure_sympy()
    import frontdoor
    import recall
    import tick
    import tick_golden

    recorder = Recorder(M.parse_expression, P._UNIT_TABLE)
    M.parse_expression = P.parse_expression = recorder
    config = EngineConfig("secular")
    claims = json.loads((ROOT / "data" / "frontdoor_claims.json").read_text(encoding="utf-8"))["claims"]
    families = json.loads((ROOT / "data" / "recall_phrasings.json").read_text(encoding="utf-8"))["families"]
    phrasings = [row["text"] for rows in families.values() for row in rows]
    parts = [part for line in (ROOT / "eval" / "live_probes.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip().startswith("{") for part in probe_parts(json.loads(line).get("body"))]
    probe_sentences = [item for kind, item in parts if kind == "sentence"]
    written = inline_sentences(ROOT / "tests" / "test_frontdoor.py")
    inline = {FRONT_DOOR: written, RECALL: inline_sentences(ROOT / "tests" / "test_recall.py")}
    sentences: Dict[str, int] = {FRONT_DOOR: len(claims) + len(written), RECALL: len(phrasings) + len(inline[RECALL]),
                                 PROBES: len(probe_sentences)}
    forms: Dict[str, list] = {PROBES: [item for kind, item in parts if kind == "spec"], AUDIT: []}
    entries: Dict[str, list] = {}

    with tripwire() as hits:
        recorder.source = FRONT_DOOR
        frontdoor.run(dry_run=True, data_dir=keeping, claims_path=ROOT / "data" / "frontdoor_claims.json")
        recorder.source = RECALL
        recall.run(dry_run=True, data_dir=keeping, phrasings_path=ROOT / "data" / "recall_phrasings.json")
        for source, texts in inline.items():
            recorder.source = source
            for text in texts:
                audit.audit(text, config, seal=False, index=False, card=False)
        recorder.source = PROBES
        for text in probe_sentences:
            audit.audit(text, config, seal=False, index=False, card=False)
        for text in [c["text"] for c in claims] + phrasings + written + probe_sentences:
            forms[AUDIT].extend(step["spec"] for step in audit.extract(text))
        recorder.source = TICK
        for name, run in tick.catalog_entries():
            before = recorder.calls[TICK]
            result = tick_golden.run_entry(name, lambda: run(*tick_golden.GOLDEN_ARGS.get(name, ())))
            entries[name] = [result["rc"], recorder.calls[TICK] - before]

    Path(out).write_text(json.dumps({
        "reads": sorted(recorder.reads), "calls": dict(recorder.calls), "sentences": sentences, "forms": forms,
        "entries": entries, "hits": hits}, ensure_ascii=False), encoding="utf-8")
    shutil.rmtree(keeping, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
