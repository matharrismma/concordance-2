"""BUILT DATA: how the engine reads what the box built (tools/box_build.py, run 2026-11-11-box-build).

A build lands at data/builds/<name>/<content hash>/, and nothing reads it until a gated deploy ships a pin naming that
hash here, in src/concordance/build_pins.json, together with the reader that uses it. `built_dir(name)` is the one way
in: the pinned hash's directory when it is there, and None (not built, a miss) when it is not, never another hash's
directory. tests/test_box_build.py holds the pins equal to the hashes tools/box_builds.txt lists.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Union

PINS = Path(__file__).resolve().with_name("build_pins.json")
_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
_HASH = re.compile(r"[0-9a-f]{64}")


def pins() -> Dict[str, str]:
    """Every pinned build, name to content hash, as this checkout ships them. A malformed pin is no pin."""
    with open(PINS, encoding="utf-8") as fh:
        held = json.load(fh)
    return {name: digest for name, digest in held.items()
            if isinstance(digest, str) and _NAME.fullmatch(name) and _HASH.fullmatch(digest)}


def pinned_hash(name: str) -> Optional[str]:
    """The content hash pinned for `name`, or None when nothing is pinned for it."""
    return pins().get(name) if isinstance(name, str) else None


def _data_dir(data_dir: Union[str, Path, None]) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    env = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return Path(env) if env else Path("data")


def built_dir(name: str, data_dir: Union[str, Path, None] = None) -> Optional[Path]:
    """data/builds/<name>/<pinned hash>/ when that build is on this machine; None when it is not built."""
    digest = pinned_hash(name)
    if digest is None:
        return None
    found = _data_dir(data_dir) / "builds" / name / digest
    return found if found.is_dir() and not found.is_symlink() else None
