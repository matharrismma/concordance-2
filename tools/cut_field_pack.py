#!/usr/bin/env python3
"""Cut a RUNNABLE Narrow Highway FIELD PACK — the Lighthouse Node + a corpus slice, drop-in.

The field-library image (`tools/cut_field_image.py`, lever 4) gives a family the library to READ. This
is the next tier: a pack a person RUNS. Drop it on a Pi/old phone/solar mini-PC beside a Meshtastic
radio and the whole mesh gets a signed Daily Word and verified answers — sovereign, offline, no account.

What it assembles (self-contained, nothing fetched at runtime):

    code/concordance/     the Lighthouse Node's MINIMAL import closure (6 modules) + a stub __init__,
                          so `import concordance.lighthouse_node` is light on a Pi (no engine/corpus DB).
    data/cards.jsonl      the SLICE: the practical field shelves (first aid, water, power, navigation,
                          food, survival, comms, field kit) + the WHOLE Bible (WEB), public cards only.
    field_search.py       a small deterministic offline finder over the slice (stdlib only).
    crisis.py             the crisis test, FROZEN from the engine's ask.py at cut time (one test, no
                          hand-copied drift) — a cry for help is always answered with real help.
    run.py                the field launcher: --ask / --daily / --serve / (default) a no-radio self-test.
    LIGHTHOUSE_NODE.md    the operator quickstart (copied from docs/).
    README.md             what it is, how to run, how to verify, honest status, reference-not-advice.
    MANIFEST.json         every file's bytes + sha256 — the pack's own seal.
    verify_pack.py        stdlib re-hasher: anyone can confirm the copy is unaltered.

Runtime is decoupled from the full engine: run.py injects field_search + crisis into the node, so the
heavy corpus/engine modules are never imported. The pack still carries none of our servers — your node,
your slice, your key.

    python tools/cut_field_pack.py            # cut + self-verify into the releases dir
    python tools/cut_field_pack.py --check    # counts only, cut nothing
    python tools/cut_field_pack.py --out DIR  # cut into DIR (used by the test)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "concordance"
RELEASES = Path(os.environ.get("CONCORDANCE_RELEASES", "").strip() or "D:/NarrowHighway-Releases")

# The Lighthouse Node's minimal top-level import closure — exactly the modules it needs, no engine.
CLOSURE = ["lighthouse_node", "meshtastic_bridge", "mesh", "signing", "identity", "validate"]
# The practical field shelves that ride in every pack (each an in-repo per-shelf jsonl).
FIELD_FILES = ["firstaid", "water", "power", "navigation", "food", "survival", "comms", "fieldkit"]
BIBLE_FILE = "bible_en.jsonl"


# ── selecting the slice ────────────────────────────────────────────────────────────────────────────
def _is_public(card: Dict[str, Any]) -> bool:
    # FAIL-CLOSED. A card that a stranger will redistribute must EXPLICITLY declare itself public and
    # released; a MISSING visibility/lifecycle must never default to shippable. (Every in-repo field
    # card already carries visibility:"public" + lifecycle_stage:"public", so this excludes nothing
    # legitimate — only an accidental quarantined/public_review/unset card, which must never ride out.)
    return card.get("visibility") == "public" and \
           card.get("lifecycle_stage") in ("public", "featured")


def _norm_field(card: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": card.get("id"), "title": (card.get("title") or "").strip(),
            "body": (card.get("body") or "").strip(), "shelf": card.get("shelf") or "field",
            "source": card.get("source") or {}}


def _norm_verse(row: Dict[str, Any]) -> Dict[str, Any]:
    book, ch, vs = row.get("book", ""), str(row.get("chapter", "")), str(row.get("verse", ""))
    abbr = (row.get("book_abbr") or book[:3]).upper()
    return {"id": f"web-{abbr}-{ch}-{vs}", "title": f"{book} {ch}:{vs}".strip(),
            "body": (row.get("text") or "").strip(), "shelf": "bible",
            "source": {"label": "World English Bible (public domain)", "ref": f"{book} {ch}:{vs}"}}


def select_cards(data_dir: Path) -> List[Dict[str, Any]]:
    """The pack's slice: the public field cards + the whole Bible, normalized to what the node needs."""
    out: List[Dict[str, Any]] = []
    seen = set()
    for name in FIELD_FILES:
        p = data_dir / f"{name}_cards.jsonl"
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if not _is_public(c):
                continue
            nc = _norm_field(c)
            if nc["id"] and nc["title"] and nc["body"] and nc["id"] not in seen:
                seen.add(nc["id"])
                out.append(nc)
    bible = data_dir / BIBLE_FILE
    if bible.is_file():
        for line in bible.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            nv = _norm_verse(row)
            if nv["body"] and nv["id"] not in seen:
                seen.add(nv["id"])
                out.append(nv)
    return out


def _counts(cards: List[Dict[str, Any]]) -> Dict[str, int]:
    field = sum(1 for c in cards if c["shelf"] != "bible")
    return {"field_cards": field, "bible_verses": len(cards) - field, "total": len(cards)}


# ── generated pack files ───────────────────────────────────────────────────────────────────────────
_STUB_INIT = '"""Narrow Highway field pack — minimal package stub (the full engine is not shipped).\n' \
             '\nOnly the Lighthouse Node closure lives here; run.py injects the slice finder + crisis\n' \
             'test, so no corpus/engine module is imported. See LIGHTHOUSE_NODE.md."""\n'

_FIELD_SEARCH = '''#!/usr/bin/env python3
"""The field pack\\'s offline finder over its slice (data/cards.jsonl). Stdlib only, deterministic.

Token-overlap ranking with stopwords removed; the Lighthouse Node\\'s relevance floor does the rest. This
is a small, honest finder over a curated field slice — not the full engine\\'s ranker over the whole
corpus. It returns cards best-first; the node decides crisis/answer/miss."""
import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_CARDS_PATH = os.path.join(_HERE, "data", "cards.jsonl")
_STOP = {"the", "a", "an", "to", "of", "and", "or", "how", "do", "does", "did", "i", "is", "it", "its",
         "my", "me", "in", "on", "for", "with", "what", "why", "when", "who", "can", "could", "should",
         "would", "you", "your", "not", "no", "without", "am", "are", "be", "get", "got", "this", "that"}
# The Daily Word rotates among these anchor verses (encouragement, not a random narrative line),
# deterministic by the day\\'s seed. Falls back to any verse, then any card, if the slice lacks them.
_ANCHORS = ["web-PSA-23-1", "web-JOH-3-16", "web-PHI-4-13", "web-ISA-41-10", "web-JER-29-11",
            "web-ROM-8-28", "web-MAT-11-28", "web-PRO-3-5", "web-JOS-1-9", "web-PSA-46-1",
            "web-JOH-14-27", "web-2CO-12-9", "web-PHI-4-6", "web-PSA-121-1", "web-ISA-40-31",
            "web-MAT-6-34"]
_CARDS = None


def _cards():
    global _CARDS
    if _CARDS is None:
        rows = []
        with open(_CARDS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        _CARDS = rows
    return _CARDS


def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def search(query, limit=3):
    qt = _tokens(query)
    if not qt:
        return []
    scored = []
    for i, c in enumerate(_cards()):
        ct = _tokens((c.get("title") or "") + " " + (c.get("body") or ""))
        overlap = len(qt & ct)
        if overlap:
            title_hits = len(qt & _tokens(c.get("title") or ""))
            scored.append((title_hits, overlap, -i, c))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    return [t[3] for t in scored[:max(1, int(limit))]]


def daily(seed):
    cards = _cards()
    by_id = {c.get("id"): c for c in cards}
    pool = [by_id[i] for i in _ANCHORS if i in by_id] \\
        or [c for c in cards if c.get("shelf") == "bible"] or cards
    if not pool:
        return None
    idx = int(hashlib.sha256((seed or "").encode("utf-8")).hexdigest(), 16) % len(pool)
    return pool[idx]
'''

_REQUIREMENTS = """# Narrow Highway Field Pack — Python dependencies
# Python 3.8+ and one library are all the pack needs to run and to sign/verify:
cryptography>=41
# meshtastic       # ONLY needed for `--serve` (answering a real LoRa radio); uncomment to install
"""

_CRISIS_FUNCS = '''

def normalize(text):
    t = (str(text) if text else "").lower().translate(_SMART).replace("'", "")
    return re.sub(r"\\s+", " ", t).strip()


def is_crisis(text):
    """True if the message reads as a cry of self-harm. The one test, frozen from ask.py at cut time."""
    t = normalize(text)
    return t in _CRISIS_EXACT or any(w in t for w in _CRISIS_WORDS)
'''

_RUN = '''#!/usr/bin/env python3
"""Narrow Highway Field Pack — run the Lighthouse Node on this pack\\'s slice. No internet, no account.

    python run.py                              # a no-radio self-test (proves the pack)
    python run.py --ask "how do i stop bad bleeding"
    python run.py --daily                      # the signed card of the day
    python run.py --serve --dev /dev/ttyUSB0   # answer a Meshtastic mesh (needs: pip install meshtastic)

The engine lives BEHIND the radio. This pack carries none of our servers — your node, your slice, your
key. Verify the pack is unaltered any time with: python verify_pack.py
"""
import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "code"))
sys.path.insert(0, _HERE)
import crisis  # noqa: E402
import field_search  # noqa: E402
from concordance import lighthouse_node as ln  # noqa: E402


def _reply(q):
    return ln.compose_reply(q, search_fn=field_search.search, is_crisis_fn=crisis.is_crisis)


def _station_key():
    """The node\\'s identity, kept on disk (0600) so the mesh PINS YOU ONCE and verifies your
    broadcasts forever. Created on the first --serve; never leaves this device. Do NOT share
    station_key.json — it is your private key. Delete it only to become a new station."""
    import json
    import stat
    path = os.path.join(_HERE, "station_key.json")
    if os.path.exists(path):
        d = json.load(open(path, encoding="utf-8"))
        return d["priv"], d["pub"]
    priv, pub = ln.new_station()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"priv": priv, "pub": pub}, fh)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    return priv, pub


def main():
    p = argparse.ArgumentParser(prog="run.py", description="Narrow Highway Field Pack — the Lighthouse "
                                "Node on its slice, sovereign and offline.")
    p.add_argument("--ask", metavar="QUESTION")
    p.add_argument("--daily", nargs="?", const="today", metavar="SEED")
    p.add_argument("--serve", action="store_true")
    p.add_argument("--dev", default=None)
    a = p.parse_args()

    if a.serve:
        priv, pub = _station_key()          # persisted on disk: the mesh pins you ONCE, not per launch
        print("station public key (pin this on the mesh):", pub)
        ctl = ln.serve(priv, pub, dev_path=a.dev, search_fn=field_search.search,
                       is_crisis_fn=crisis.is_crisis,
                       on_answer=lambda q, r, n: print("  answered", repr(q), "->", n,
                                                       "packets [%s]" % r["kind"]))
        if not ctl.get("ok"):
            print("not started:", ctl.get("error"))
            return 1
        print(ctl.get("note"))
        print("Listening. Ctrl-C to stop.")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            ctl.get("close", lambda: None)()
            print()
        return 0

    if a.ask is not None:
        r = _reply(a.ask)
        print("[%s] verified=%s" % (r.get("kind"), r.get("verified")))
        print(r.get("text"))
        return 0

    if a.daily is not None:
        r = ln.daily_word(a.daily, daily_fn=field_search.daily)
        print("[daily] " + r["text"] if r.get("ok") else "no daily: " + str(r.get("error")))
        return 0

    # default: the self-test — proves the whole chain with no radio
    demo = ln.simulate_answer("how do i stop bad bleeding", search_fn=field_search.search,
                              is_crisis_fn=crisis.is_crisis)
    v = demo["verify"]
    ok = demo["reassembled"] and v["authentic"]
    print("Field pack OK." if ok else "Field pack FAILED.")
    print("  answer :", demo["reply"]["text"])
    print("  packets=%d max=%dB authentic=%s" % (demo["packets"], demo["max_packet_bytes"], v["authentic"]))
    cr = _reply("i want to end it all")
    print("  crisis routes to real help:", "988" in cr["text"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
'''

_VERIFY = '''#!/usr/bin/env python3
"""Verify this field pack against its MANIFEST — standard library only.
    python verify_pack.py           # from inside the pack directory
"""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
man = json.load(open(root / "MANIFEST.json", encoding="utf-8"))
bad = 0
for f in man["files"]:
    p = root / f["path"]
    if not p.is_file():
        print("MISSING   " + f["path"])
        bad += 1
        continue
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != f["sha256"]:
        print("ALTERED   " + f["path"])
        bad += 1
print("VERIFIED: every file matches its seal" if not bad else "FAILED: %d file(s) differ" % bad)
sys.exit(1 if bad else 0)
'''

_RUN_SH = '''#!/bin/sh
# Narrow Highway Field Pack — ONE COMMAND. Creates a private virtual environment, installs the single
# dependency (OFFLINE from ./wheelhouse if present, else from the internet), and runs the node on this
# pack\\'s slice. Nothing here depends on our servers.
#
#   ./run.sh                                  prove the pack works (a no-radio self-test)
#   ./run.sh --ask "how do i stop bad bleeding"
#   ./run.sh --daily
#   ./run.sh --serve --dev /dev/ttyUSB0       answer a Meshtastic mesh (needs a radio)
#
# Verify the pack is unaltered any time:  python3 verify_pack.py
set -eu
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "Python 3 is required. Install python3 and run ./run.sh again."; exit 1; }
if [ ! -d .venv ]; then
  echo "First run: setting up (once)…"
  "$PY" -m venv .venv || { echo "could not create a virtual environment"; exit 1; }
  if [ -d wheelhouse ]; then
    .venv/bin/pip install --quiet --no-index --find-links wheelhouse -r requirements.txt \\
      || { echo "offline install failed — see wheelhouse/README"; exit 1; }
  else
    .venv/bin/pip install --quiet -r requirements.txt \\
      || { echo "install needs the internet once (no ./wheelhouse present)"; exit 1; }
  fi
fi
exec .venv/bin/python run.py "$@"
'''

_RUN_CMD = '''@echo off
REM Narrow Highway Field Pack — ONE COMMAND (Windows). Creates a private virtual environment, installs
REM the single dependency (offline from wheelhouse\\ if present, else from the internet), runs the node.
REM   run.cmd                                  self-test
REM   run.cmd --ask "how do i stop bad bleeding"
REM   run.cmd --serve --dev COM3               answer a Meshtastic mesh
setlocal
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3 is required. Install it from python.org and run run.cmd again. & exit /b 1)
if not exist .venv (
  echo First run: setting up ^(once^)...
  python -m venv .venv || (echo could not create a virtual environment & exit /b 1)
  if exist wheelhouse (
    .venv\\Scripts\\pip install --quiet --no-index --find-links wheelhouse -r requirements.txt || (echo offline install failed & exit /b 1)
  ) else (
    .venv\\Scripts\\pip install --quiet -r requirements.txt || (echo install needs the internet once & exit /b 1)
  )
)
.venv\\Scripts\\python run.py %*
'''

_README = """# Narrow Highway — Field Pack

**The engine, behind a radio.** Drop this on an offline computer (a Raspberry Pi, an old phone, a solar
mini-PC) beside a [Meshtastic](https://meshtastic.org) radio and the whole LoRa mesh gets, free and
offline, with no account:

- **The Daily Word** — a signed verse / card of the day, broadcast to every node in range.
- **Answers** — a question typed into the mesh comes back as a *verified* card: crisis-first, budgeted
  to the ~200-byte LoRa payload, carrying a `/c/<id>` pull-ref to open later when there is signal.

## Run it — one command

You need **Python 3.8+**. Nothing else to figure out.

- Linux / Mac / Raspberry Pi:  `./run.sh`
- Windows:  `run.cmd`

The first run sets up a private environment and installs the one dependency (`cryptography`, for
signing) — offline from the bundled `wheelhouse/` if this pack includes it, otherwise from the internet
once — then proves itself with a no-radio self-test. After that:

```
./run.sh --ask "how do i stop bad bleeding"
./run.sh --daily
./run.sh --serve --dev /dev/ttyUSB0      # answer a Meshtastic mesh (plug in a radio first)
```

The first `--serve` creates and saves `station_key.json` — your node's identity, kept `0600` on this
device only. Publish the **station public key** it prints **once**, so the mesh can *pin* your
lighthouse and verify its broadcasts offline forever — the same key on every restart. Do not share
`station_key.json`; it is your private key.

(Prefer to drive it yourself? `pip install -r requirements.txt` then `python run.py …` works too.
`meshtastic` is only needed for `--serve`.)

## What's inside

- `data/cards.jsonl` — {field:,} practical field cards (first aid, water, power, navigation, food,
  survival, comms, field kit) + the whole Bible ({verses:,} verses, World English Bible). All public
  domain / freely redistributable.
- `code/concordance/` — the Lighthouse Node (minimal, sovereign, stdlib-first).
- `field_search.py` — a small offline finder over the slice. `crisis.py` — the crisis test.

## Verify it

```
python verify_pack.py
```

Re-hashes every file against `MANIFEST.json` (standard library only). The pack depends on none of our
servers.

## Honest notes

- The composer never fabricates: a checkable question is answered from a card that carries its own
  re-checkable reference, and if nothing in the slice is genuinely relevant it says so — **a gap stays a
  gap**. A cry for help is always answered with real-person help (988, findahelpline.com), immediately.
- **Reference, not advice.** The field cards are public-domain reference material. In a real emergency,
  get to real medical or professional help. This pack is a keeping, not a substitute for a person.
- The `--serve` radio transport is written to the Meshtastic API and is **field-test-pending** — proven
  in memory (`python run.py`), not yet run on real hardware where this was built. If you field-test it on
  your board, that is the last mile.

Cut {date}. The whole library, searchable and served: https://narrowhighway.com — Psalm 119:105.
"""


# ── writing the pack ───────────────────────────────────────────────────────────────────────────────
def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# The dependency (`cryptography`) wheels bundled for a truly OFFLINE install, across the arches a field
# node actually runs on — x86 Linux, Raspberry Pi (aarch64/armv7), Windows, Apple silicon.
_WHEEL_TARGETS = [("manylinux2014_x86_64", "39"), ("manylinux2014_aarch64", "39"),
                  ("manylinux2014_armv7l", "39"), ("win_amd64", "39"), ("macosx_11_0_arm64", "39")]


def _populate_wheelhouse(dest: Path) -> int:
    """Download `cryptography`'s wheels for the common field arches into dest/wheelhouse, so ./run.sh
    can install with NO internet. Needs network at CUT time only; best-effort per platform (a platform
    with no matching wheel is skipped, not fatal). Sealed with the rest of the pack."""
    import subprocess
    wh = dest / "wheelhouse"
    wh.mkdir(exist_ok=True)
    got = 0
    for plat, pyver in _WHEEL_TARGETS:
        try:
            subprocess.run([sys.executable, "-m", "pip", "download", "cryptography",
                            "--only-binary", ":all:", "--platform", plat, "--python-version", pyver,
                            "--implementation", "cp", "-d", str(wh)],
                           check=True, capture_output=True)
            got += 1
        except Exception:  # noqa: BLE001
            continue
    (wh / "README.txt").write_text(
        "Offline-install wheels for `cryptography`, one set per field arch. ./run.sh (and run.cmd) use\n"
        "these with pip --no-index when no internet is present. To add an arch, drop its wheel here.\n",
        encoding="utf-8")
    return got


def _archive(dest: Path) -> Path:
    """Bundle the whole pack into ONE .tar.gz + a .sha256 sidecar — one file to carry on a USB/SD stick,
    with a published hash so a stranger can prove the copy is unaltered before trusting it."""
    import tarfile
    tgz = dest.parent / (dest.name + ".tar.gz")
    with tarfile.open(tgz, "w:gz") as tar:
        tar.add(dest, arcname=dest.name)
    (tgz.parent / (tgz.name + ".sha256")).write_text(_sha(tgz) + "  " + tgz.name + "\n", encoding="utf-8")
    return tgz


def _crisis_module() -> str:
    """Freeze the engine's crisis test into a standalone module — the canonical word list + normalizer
    captured at cut time, so it can never drift from a hand copy."""
    sys.path.insert(0, str(REPO / "src"))
    from concordance import ask  # noqa
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    header = ('#!/usr/bin/env python3\n'
              '"""The crisis test, FROZEN from the engine\'s ask.py at pack-cut time (%s).\n\n'
              'One test, no drift: the word list and the normalization are the canonical ones, captured\n'
              'at the cut — not a hand copy that could fall out of step. A cry for help is always met\n'
              'with real-person help before any lookup."""\n' % stamp)
    body = ("import re\n\n"
            "_SMART = %r\n"
            "_CRISIS_WORDS = %r\n"
            "_CRISIS_EXACT = %r\n" % (dict(ask._SMART_QUOTES), tuple(ask._CRISIS_WORDS),
                                      set(ask._CRISIS_EXACT)))
    return header + body + _CRISIS_FUNCS


def cut(dest: Path, data_dir: Path, offline: bool = False) -> Dict[str, Any]:
    """Assemble a full field pack at `dest` from the card files in `data_dir`. Returns a summary.
    `offline=True` bundles the dependency wheels (needs network at cut time) so the pack installs with
    no internet on the field arches."""
    cards = select_cards(data_dir)
    counts = _counts(cards)
    if counts["field_cards"] == 0:
        raise SystemExit("REFUSING: no field cards found in %s — a pack with no field content is a hole"
                         % data_dir)
    dest.mkdir(parents=True, exist_ok=False)

    # the slice
    (dest / "data").mkdir()
    with open(dest / "data" / "cards.jsonl", "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # the minimal code closure + a stub package init
    code_pkg = dest / "code" / "concordance"
    code_pkg.mkdir(parents=True)
    (code_pkg / "__init__.py").write_text(_STUB_INIT, encoding="utf-8")
    for mod in CLOSURE:
        shutil.copy2(SRC / f"{mod}.py", code_pkg / f"{mod}.py")

    # generated + copied top-level files
    (dest / "field_search.py").write_text(_FIELD_SEARCH, encoding="utf-8")
    (dest / "crisis.py").write_text(_crisis_module(), encoding="utf-8")
    (dest / "run.py").write_text(_RUN, encoding="utf-8")
    (dest / "run.sh").write_text(_RUN_SH, encoding="utf-8", newline="\n")   # LF: it is a shell script
    try:
        os.chmod(dest / "run.sh", 0o755)
    except Exception:  # noqa: BLE001 — a filesystem without exec bits (e.g. some Windows mounts) is fine
        pass
    (dest / "run.cmd").write_text(_RUN_CMD, encoding="utf-8", newline="\r\n")  # CRLF for cmd.exe
    (dest / "verify_pack.py").write_text(_VERIFY, encoding="utf-8")
    (dest / "requirements.txt").write_text(_REQUIREMENTS, encoding="utf-8")
    date = time.strftime("%Y-%m-%d", time.gmtime())
    (dest / "README.md").write_text(
        _README.format(field=counts["field_cards"], verses=counts["bible_verses"], date=date),
        encoding="utf-8")
    lh = REPO / "docs" / "LIGHTHOUSE_NODE.md"
    if lh.is_file():
        shutil.copy2(lh, dest / "LIGHTHOUSE_NODE.md")

    if offline:
        _populate_wheelhouse(dest)          # bundle the dependency wheels so ./run.sh needs no internet

    # the seal: every file's bytes + sha256 (MANIFEST last, over everything else)
    files = []
    for p in sorted(dest.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files.append({"path": p.relative_to(dest).as_posix(),
                          "bytes": p.stat().st_size, "sha256": _sha(p)})
    manifest = {"pack": "narrow-highway-field-pack", "version": "v1",
                "stamp": time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime()),
                "counts": counts, "files": files,
                "note": "run.py injects field_search + crisis; the corpus/engine is not shipped"}
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    # self-verify: re-hash from the copy before claiming success
    bad = [f["path"] for f in files if _sha(dest / f["path"]) != f["sha256"]]
    if bad:
        raise SystemExit("CUT FAILED VERIFICATION: %s" % bad)
    return {"dest": str(dest), "counts": counts, "files": len(files) + 1}


def main() -> int:
    if sys.platform == "win32":  # non-ASCII titles must not die on a redirected cp1252 stdout
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    args = sys.argv[1:]
    data_dir = Path(os.environ.get("CONCORDANCE_FIELD_DATA", "").strip() or (REPO / "data"))
    if "--check" in args:
        cards = select_cards(data_dir)
        c = _counts(cards)
        print("field pack would carry: %(field_cards)s field cards + %(bible_verses)s Bible verses "
              "(%(total)s total)" % c)
        return 0
    offline = "--offline" in args           # bundle dependency wheels for a no-internet install
    if "--out" in args:
        dest = Path(args[args.index("--out") + 1])
    else:
        stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
        dest = RELEASES / "field-pack" / f"field-pack-v1-{stamp}"
    summary = cut(dest, data_dir, offline=offline)
    print("CUT + VERIFIED: %s" % summary["dest"])
    print("  %(field_cards)s field cards + %(bible_verses)s Bible verses" % summary["counts"])
    print("  %s files, sealed in MANIFEST.json" % summary["files"])
    print("  run it:  cd %s && ./run.sh        (Windows: run.cmd)" % summary["dest"])
    if "--out" not in args:                  # ship one sealed tarball a stranger can carry + verify
        tgz = _archive(dest)
        print("  bundle:  %s  (+ .sha256)" % tgz)
    return 0


if __name__ == "__main__":
    sys.exit(main())
