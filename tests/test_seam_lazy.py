"""The secular reach must not LOAD witness code.

The witness verifier `scripture` is surface-gated, but the web/mcp layers used to import it
at module top — so the .com process loaded witness code it must never surface. These tests
run a fresh interpreter, exercise the SECULAR path, and assert concordance.verifiers.scripture
was never imported (and, as a positive control, that the WITNESS path does load it).
Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parent.parent / "src")


def _run(code: str) -> str:
    env = {**os.environ, "PYTHONPATH": SRC}
    return subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()


def test_secular_web_path_does_not_load_scripture():
    code = (
        "import sys\n"
        "from concordance.web.api import dispatch\n"
        "from concordance.config import EngineConfig\n"
        "dispatch('POST','/verify',{'seal':'0'},"
        "{'mode':'equality','params':{'expr_a':'2+2','expr_b':'4','variables':{}}}, EngineConfig('secular'))\n"
        "dispatch('GET','/search',{'q':'grace'}, None, EngineConfig('secular'))\n"
        "print('LOADED' if 'concordance.verifiers.scripture' in sys.modules else 'CLEAN')\n"
    )
    assert _run(code) == "CLEAN"


def test_secular_mcp_path_does_not_load_scripture():
    code = (
        "import sys\n"
        "from concordance.mcp.server import handle\n"
        "from concordance.config import EngineConfig\n"
        "handle({'jsonrpc':'2.0','id':1,'method':'tools/list'}, EngineConfig('secular'))\n"
        "print('LOADED' if 'concordance.verifiers.scripture' in sys.modules else 'CLEAN')\n"
    )
    assert _run(code) == "CLEAN"


def test_witness_path_does_load_scripture():
    # positive control: the witness surface genuinely uses scripture
    code = (
        "import sys\n"
        "from concordance.web.api import dispatch\n"
        "from concordance.config import EngineConfig\n"
        "dispatch('GET','/resolve',{'ref':'John 1:1'}, None, EngineConfig('witness'))\n"
        "print('LOADED' if 'concordance.verifiers.scripture' in sys.modules else 'CLEAN')\n"
    )
    assert _run(code) == "LOADED"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} seam tests passed — secular never loads witness code; witness does.")
