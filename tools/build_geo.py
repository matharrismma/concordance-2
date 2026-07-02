"""Build the offline IP→country table the traffic rollup reads (data/geo/ip2country.tsv).

Source: DB-IP IP-to-Country Lite (https://db-ip.com), CC BY 4.0 — free, attributed. We fetch the
monthly CSV, keep the IPv4 ranges, convert each to integer bounds, and write a sorted TSV
(start_int\\tend_int\\tCC) that tools/traffic_rollup.py binary-searches. Sovereign at runtime: the
rollup never touches the network; only THIS builder does, on demand.

ATTRIBUTION (required by CC BY): "IP geolocation by DB-IP (https://db-ip.com), CC BY 4.0."
Also written to data/geo/ATTRIBUTION.txt.

Run on a box with internet (e.g. the droplet):
    python -m tools.build_geo            # tries the current + recent months automatically
    python -m tools.build_geo --src /path/to/dbip-country-lite.csv[.gz]   # offline file
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import os
import time
import urllib.request

_BASE = "https://download.db-ip.com/free/dbip-country-lite-{ym}.csv.gz"
_ATTRIB = "IP geolocation by DB-IP (https://db-ip.com), CC BY 4.0."


def _ipv4_to_int(s: str):
    parts = s.split(".")
    if len(parts) != 4:
        return None
    try:
        a, b, c, d = (int(x) for x in parts)
    except ValueError:
        return None
    if not all(0 <= x <= 255 for x in (a, b, c, d)):
        return None
    return (a << 24) + (b << 16) + (c << 8) + d


def _recent_months(n=4):
    t = time.gmtime()
    y, m = t.tm_year, t.tm_mon
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12; y -= 1
    return out


def _fetch_csv_bytes(src):
    if src:
        raw = open(src, "rb").read()
        return gzip.decompress(raw) if src.endswith(".gz") else raw
    hdrs = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0 Safari/537.36",
            "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    last_err = None
    for ym in _recent_months():
        url = _BASE.format(ym=ym)
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            print(f"  fetched {url} ({len(data)} bytes)")
            return gzip.decompress(data)
        except Exception as e:  # noqa: BLE001 — try the previous month
            last_err = e
            print(f"  (no {ym}: {e})")
    raise SystemExit(f"could not fetch DB-IP lite for any recent month: {last_err}")


def build(src=None, out=None) -> int:
    body = _fetch_csv_bytes(src).decode("utf-8", errors="replace")
    rows = []
    for row in csv.reader(io.StringIO(body)):
        if len(row) < 3:
            continue
        start, end, cc = row[0].strip(), row[1].strip(), row[2].strip().upper()
        if ":" in start or ":" in end or len(cc) != 2:
            continue  # skip IPv6 + malformed
        a, b = _ipv4_to_int(start), _ipv4_to_int(end)
        if a is None or b is None or b < a:
            continue
        rows.append((a, b, cc))
    rows.sort(key=lambda r: r[0])
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    out = out or os.path.join(base, "geo", "ip2country.tsv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for a, b, cc in rows:
            f.write(f"{a}\t{b}\t{cc}\n")
    with open(os.path.join(os.path.dirname(out), "ATTRIBUTION.txt"), "w", encoding="utf-8") as f:
        f.write(_ATTRIB + "\n")
    print(f"wrote {len(rows)} IPv4 country ranges → {out}\n  {_ATTRIB}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build data/geo/ip2country.tsv from DB-IP lite (CC BY).")
    ap.add_argument("--src", default=None, help="local dbip-country-lite csv[.gz] (skip download)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    return build(src=args.src, out=args.out)


if __name__ == "__main__":
    raise SystemExit(main())
