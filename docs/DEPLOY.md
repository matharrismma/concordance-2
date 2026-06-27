# Deploying Narrow Highway 2.0

Two faces, one engine: **narrowhighway.com** (the secular reach) and **narrowhighway.org**
(the witness) run as two services off the same code, behind Caddy (auto-TLS).

These configs are *prepared*. **Deployment is the operator's** — it is outward-facing and
touches DNS, the server, and live traffic. Nothing here deploys anything by itself.

## Prerequisites (operator)
- A server (the droplet) with Python ≥ 3.10 and Caddy installed.
- DNS **A records**: `narrowhighway.com` and `narrowhighway.org` (and `www`) → the droplet IP.
- A `nh` user with a home dir (paths below assume `/home/nh`).

## 1. Code
```bash
git clone <concordance-2 remote> /home/nh/concordance-2     # or rsync the repo up
cd /home/nh/concordance-2
python3 -m venv .venv                                        # a DEDICATED venv (don't share another app's)
.venv/bin/pip install sympy cryptography numpy scipy          # moat + signing + the heavier verifiers
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q           # sanity: 63 tests, moat 58/58
```
The systemd units (`deploy/nh-*.service`) run `/home/nh/concordance-2/.venv/bin/python`.

## 2. Data (the keeping, the WEB Bible, Strong's)
Data is **gitignored** — it lives beside the engine, not in source. Generate it on the droplet
from the frozen 1.0 sources (already present there), or rsync your local `data/` up:
```bash
# from 1.0 on the same box (adjust the source path if different):
python3 tools/migrate_cards.py    /home/nh/Lighthouse/data/cards            data/cards.jsonl
python3 tools/migrate_bible.py    /home/nh/Lighthouse/data/bible_en/verses.jsonl data/bible_en.jsonl
python3 tools/migrate_strongs.py  /home/nh/Lighthouse/lw/00_source          data/strongs
```
The engine runs without data (it just has less to retrieve); the **moat, verifiers, and signing
do not need it**. Scripture/word-study/search need it.

## 3. Services (both surfaces)
```bash
sudo cp deploy/nh-com.service deploy/nh-org.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nh-com nh-org
systemctl status nh-com nh-org          # both active
```
`.com` listens on `127.0.0.1:8000` (secular), `.org` on `127.0.0.1:8001` (witness).

## 4. Caddy (TLS + routing)
```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile     # or append its blocks to your existing one
sudo systemctl reload caddy
```

## 5. Verify (live)
```bash
curl -s https://narrowhighway.com/health          # {"ok":true,"surface":"secular",...}
curl -s https://narrowhighway.org/health          # surface":"witness"
curl -s -X POST https://narrowhighway.com/verify -H content-type:application/json \
  -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}'   # verdict HOLDS
curl -s 'https://narrowhighway.org/word_study?strongs=G26'   # agape — witness-only
curl -s 'https://narrowhighway.com/word_study?strongs=G26'   # 404 — gated off the secular reach
```

## Notes
- **Sovereign**: no external services required; runs offline. `sympy` (the moat) and
  `cryptography` (signing) are the only runtime deps worth installing; everything else is stdlib.
- **Updating**: `git pull`, `pip install -e ".[math]"` if deps changed, `sudo systemctl restart nh-com nh-org`.
- **Docker alternative**: `docker build -t narrowhighway .`, then run two containers (`--surface
  secular -p 8000` and `--surface witness -p 8001`) with `-v /path/to/data:/data`.
- The witness endpoints (`/resolve`, `/word_study`) are 404 on `.com` by design; the keeping
  (`/search`) is shared on both. The `.com` does not hide the faith — it links to `.org`.
