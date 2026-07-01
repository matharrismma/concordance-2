"""Traffic rollup — where visitors come FROM and where they GO, split into humans / bots / agents.

Reads the Caddy JSON access logs (the complete record of every request: ip, uri, user-agent,
referer, status) and writes an aggregated, privacy-respecting summary to data/traffic.json, which
the keep dashboard reads (the same pattern as tools/integrity_check.py → integrity_status.json).

Privacy: humans are aggregated only (top referrers, source networks /24, countries when a geo
dataset is present) — NEVER individual human IPs in the output. Bots and agents self-identify by
user-agent, so they are named. No secrets, no full personal IPs persisted. Advisory ops data, not
part of the integrity chain. Sovereign: stdlib only.

Run (needs read access to /var/log/caddy — run as root or via the nh-traffic.service timer):
    python -m tools.traffic_rollup [--days 7] [--out data/traffic.json] LOG...
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from collections import Counter, defaultdict
from typing import Any, Dict, Optional, Tuple

# AI agents / LLM crawlers (order matters: first match wins). name → the operator they act for.
_AGENTS: Tuple[Tuple[str, str], ...] = (
    ("gptbot", "OpenAI · GPTBot"), ("oai-searchbot", "OpenAI · SearchBot"), ("chatgpt-user", "OpenAI · ChatGPT"),
    ("claudebot", "Anthropic · ClaudeBot"), ("claude-web", "Anthropic · Claude"), ("claude-user", "Anthropic · Claude"),
    ("anthropic-ai", "Anthropic"), ("perplexitybot", "Perplexity · bot"), ("perplexity-user", "Perplexity · user"),
    ("google-extended", "Google · AI"), ("applebot-extended", "Apple · AI"), ("bytespider", "ByteDance · Bytespider"),
    ("ccbot", "Common Crawl"), ("meta-externalagent", "Meta · AI"), ("cohere-ai", "Cohere"),
    ("youbot", "You.com"), ("amazonbot", "Amazon"), ("diffbot", "Diffbot"), ("timpibot", "Timpi"),
    ("imagesiftbot", "ImageSift"), ("omgili", "Webz.io"), ("gemini", "Google · Gemini"),
)
# Ordinary bots: search engines, social unfurlers, monitors, generic http clients.
_BOTS: Tuple[Tuple[str, str], ...] = (
    ("googlebot", "Google · Search"), ("bingbot", "Bing"), ("duckduckbot", "DuckDuckGo"), ("yandex", "Yandex"),
    ("baiduspider", "Baidu"), ("slurp", "Yahoo"), ("sogou", "Sogou"), ("exabot", "Exalead"),
    ("facebookexternalhit", "Facebook"), ("facebookbot", "Facebook"), ("twitterbot", "Twitter/X"),
    ("linkedinbot", "LinkedIn"), ("slackbot", "Slack"), ("telegrambot", "Telegram"), ("discordbot", "Discord"),
    ("whatsapp", "WhatsApp"), ("pinterest", "Pinterest"), ("redditbot", "Reddit"), ("embedly", "Embedly"),
    ("uptimerobot", "UptimeRobot"), ("pingdom", "Pingdom"), ("statuscake", "StatusCake"), ("censys", "Censys"),
    ("ahrefsbot", "Ahrefs"), ("semrushbot", "SEMrush"), ("mj12bot", "Majestic"), ("dotbot", "Moz"),
    ("petalbot", "Petal"), ("dataforseo", "DataForSEO"), ("bot", "other bot"), ("crawl", "other crawler"),
    ("spider", "other spider"), ("curl", "curl"), ("wget", "wget"), ("python-requests", "python-requests"),
    ("python-urllib", "python-urllib"), ("go-http-client", "Go client"), ("java/", "Java client"),
    ("okhttp", "OkHttp"), ("scrapy", "Scrapy"), ("headlesschrome", "headless Chrome"), ("axios", "axios"),
    ("node-fetch", "node-fetch"), ("libwww", "libwww"), ("httpclient", "http client"),
)


def classify(user_agent: str, uri: str) -> Tuple[str, str]:
    """(class, who) — class in {agent, bot, human}; who names the agent/bot (humans → 'human')."""
    ua = (user_agent or "").lower()
    if (uri or "").split("?")[0].rstrip("/") == "/mcp":
        return "agent", "MCP client (uses our tools)"
    for pat, name in _AGENTS:
        if pat in ua:
            return "agent", name
    for pat, name in _BOTS:
        if pat in ua:
            return "bot", name
    if not ua:
        return "bot", "unknown (no user-agent)"
    return "human", "human"


def _country(ip: str) -> Optional[str]:
    """Best-effort IP → country. Returns None unless an offline geo dataset is present at
    data/geo/ip2country.tsv (sorted 'start_int\\tend_int\\tCC' rows, CC-BY DB-IP lite or similar).
    Kept sovereign + optional so the rollup never needs the network."""
    db = _geo_db()
    if not db or "." not in (ip or ""):
        return None
    try:
        parts = [int(x) for x in ip.split(".")]
        if len(parts) != 4:
            return None
        n = (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]
    except (ValueError, IndexError):
        return None
    import bisect
    i = bisect.bisect_right(db[0], n) - 1
    if 0 <= i < len(db[0]) and db[1][i] >= n:
        return db[2][i]
    return None


_GEO_CACHE: Any = "unset"


def _geo_db():
    """Lazy-load the optional geo table into (starts[], ends[], ccs[]). None if absent."""
    global _GEO_CACHE
    if _GEO_CACHE != "unset":
        return _GEO_CACHE
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    path = os.path.join(base, "geo", "ip2country.tsv")
    starts, ends, ccs = [], [], []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                a, b, cc = line.rstrip("\n").split("\t")[:3]
                starts.append(int(a)); ends.append(int(b)); ccs.append(cc)
        _GEO_CACHE = (starts, ends, ccs) if starts else None
    except (OSError, ValueError):
        _GEO_CACHE = None
    return _GEO_CACHE


def _ref_host(referer: str, our_hosts: set) -> Optional[str]:
    """The external site a visit came from — None for direct or self-referrals."""
    r = (referer or "").strip()
    if not r or r == "-":
        return None
    r = r.split("://", 1)[-1].split("/", 1)[0].split(":")[0].lower()
    if not r or any(r == h or r.endswith("." + h) for h in our_hosts):
        return None
    return r


def _net24(ip: str) -> str:
    if "." in (ip or ""):
        return ".".join(ip.split(".")[:3]) + ".0/24"
    if ":" in (ip or ""):
        return ":".join(ip.split(":")[:3]) + "::/48"
    return "?"


def _uri_path(uri: str) -> str:
    p = (uri or "/").split("?")[0]
    return p if len(p) <= 80 else p[:80] + "…"


def rollup(log_paths, days: int = 7, now: Optional[int] = None,
           our_hosts=("narrowhighway.com", "narrowhighway.org", "narrowhighway.tv",
                      "api.narrowhighway.com", "www.narrowhighway.com")) -> Dict[str, Any]:
    now = int(now if now is not None else time.time())
    cutoff = now - days * 86400
    our = set(our_hosts)

    tot = Counter()
    uniq = defaultdict(set)          # class → set of ips (for unique counts; not persisted raw)
    ref = defaultdict(Counter)       # class → referrer host → count
    nets = defaultdict(Counter)      # class → /24 → count
    ctry = defaultdict(Counter)      # class → country → count
    paths = defaultdict(Counter)     # class → path → count
    who = defaultdict(Counter)       # class → agent/bot name → count

    for path in log_paths:
        try:
            f = open(path, "r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with f:
            for line in f:
                line = line.strip()
                if not line or line[0] != "{":
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("ts") and d["ts"] < cutoff:
                    continue
                req = d.get("request") or {}
                uri = req.get("uri") or "/"
                headers = req.get("headers") or {}
                ua = (headers.get("User-Agent") or [""])[0] if isinstance(headers.get("User-Agent"), list) else (headers.get("User-Agent") or "")
                referer = (headers.get("Referer") or [""])[0] if isinstance(headers.get("Referer"), list) else (headers.get("Referer") or "")
                ip = req.get("client_ip") or req.get("remote_ip") or ""
                cls, name = classify(ua, uri)
                tot[cls] += 1; tot["requests"] += 1
                if ip:
                    uniq[cls].add(ip)
                paths[cls][_uri_path(uri)] += 1
                if cls == "human":
                    rh = _ref_host(referer, our)
                    ref["human"][rh or "(direct / none)"] += 1
                    nets["human"][_net24(ip)] += 1
                    c = _country(ip)
                    if c:
                        ctry["human"][c] += 1
                else:
                    who[cls][name] += 1
                    rh = _ref_host(referer, our)
                    if rh:
                        ref[cls][rh] += 1

    def top(counter, n=12):
        return counter.most_common(n)

    out: Dict[str, Any] = {
        "generated_at": now, "window_days": days,
        "totals": {"requests": tot["requests"], "human": tot["human"], "bot": tot["bot"],
                   "agent": tot["agent"], "unique_ips": sum(len(v) for v in uniq.values())},
        "geo_available": _geo_db() is not None,
        "classes": {},
    }
    for cls in ("human", "bot", "agent"):
        block: Dict[str, Any] = {
            "requests": tot[cls], "unique_ips": len(uniq[cls]),
            "going": {"paths": top(paths[cls])},
            "from": {"referrers": top(ref[cls])},
        }
        if cls == "human":
            block["from"]["networks"] = top(nets["human"])
            block["from"]["countries"] = top(ctry["human"])
        else:
            block["from"]["who"] = top(who[cls])
        out["classes"][cls] = block
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Roll up Caddy access logs into data/traffic.json")
    ap.add_argument("logs", nargs="*", default=[], help="Caddy JSON access log paths (glob ok)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    logs = []
    for pat in (args.logs or ["/var/log/caddy/*.access.log"]):
        logs.extend(sorted(glob.glob(pat)) or [pat])
    data = rollup(logs, days=args.days)
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    out = args.out or os.path.join(base, "traffic.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    t = data["totals"]
    print(f"traffic rollup → {out}: {t['requests']} reqs · {t['human']} human · {t['bot']} bot · {t['agent']} agent "
          f"({data['window_days']}d, geo={'on' if data['geo_available'] else 'off'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
