"""Traffic rollup — classification (human/bot/agent) + where-from/where-going aggregation.

Hermetic: synthetic Caddy-shaped JSON log lines, no real logs, no network. Proves humans are
aggregated (never listed by raw IP), bots/agents are named, referrers/paths roll up. Runs under
pytest OR directly.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `tools` imports

from tools.traffic_rollup import classify, rollup  # noqa: E402


def test_classify_the_three_kinds():
    assert classify("Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36", "/bible.html")[0] == "human"
    assert classify("GPTBot/1.2 (+https://openai.com/gptbot)", "/card.html?id=x")[0] == "agent"
    assert classify("Mozilla/5.0 (compatible; ClaudeBot/1.0)", "/")[0] == "agent"
    assert classify("Mozilla/5.0 (compatible; Googlebot/2.1)", "/")[0] == "bot"
    assert classify("some-random-client", "/mcp")[0] == "agent"          # our MCP callers = agents
    assert classify("", "/")[0] == "bot"                                  # no UA → not a human
    assert classify("curl/8.4.0", "/search")[0] == "bot"


def _line(ip, uri, ua, ref="", ts=10_000):
    return json.dumps({"ts": ts, "status": 200, "request": {
        "client_ip": ip, "uri": uri, "headers": {"User-Agent": [ua], "Referer": [ref] if ref else []}}})


def test_rollup_from_and_going():
    lines = [
        _line("1.2.3.4", "/bible.html", "Mozilla/5.0 Chrome/120 Safari", "https://www.google.com/search?q=bible"),
        _line("1.2.3.5", "/ask.html", "Mozilla/5.0 Firefox/121", "https://narrowhighway.org/"),   # self-ref → direct
        _line("9.9.9.9", "/card.html?id=a", "GPTBot/1.1", ""),
        _line("9.9.9.9", "/card.html?id=b", "GPTBot/1.1", ""),
        _line("66.66.66.66", "/", "Googlebot/2.1", ""),
    ]
    p = Path(tempfile.mkdtemp(prefix="nh-traffic-")) / "site.access.log"
    p.write_text("\n".join(lines), encoding="utf-8")

    out = rollup([str(p)], days=3650, now=20_000)
    t = out["totals"]
    assert t["requests"] == 5 and t["human"] == 2 and t["agent"] == 2 and t["bot"] == 1

    human = out["classes"]["human"]
    refs = dict(human["from"]["referrers"])
    assert refs.get("www.google.com") == 1                 # external referrer captured
    assert refs.get("(direct / none)") == 1                # self-referral folded into direct
    going = dict(human["going"]["paths"])
    assert going.get("/bible.html") == 1 and going.get("/ask.html") == 1
    # privacy: humans aggregated by /24 network, never raw individual IPs in the output blob
    blob = json.dumps(out)
    assert "1.2.3.4" not in blob and "1.2.3.5" not in blob
    assert dict(human["from"]["networks"]).get("1.2.3.0/24") == 2

    agent = out["classes"]["agent"]
    assert dict(agent["from"]["who"]).get("OpenAI · GPTBot") == 2
    assert dict(agent["going"]["paths"]).get("/card.html") == 2   # query stripped, grouped


def test_monitor_reclassification():
    # one browser-UA IP hammering an ops endpoint far past the threshold → monitor, not human
    ua = "Mozilla/5.0 Chrome/120 Safari"
    lines = [_line("50.0.0.1", "/health", ua) for _ in range(600)]
    lines += [_line("7.7.7.7", "/bible.html", ua, "https://www.google.com/")]   # a real person
    p = Path(tempfile.mkdtemp(prefix="nh-traffic-")) / "s.log"
    p.write_text("\n".join(lines), encoding="utf-8")
    out = rollup([str(p)], days=3650, now=20_000, monitor_threshold=500)
    t = out["totals"]
    assert t["monitor"] == 600 and t["human"] == 1          # the poller split out of humans
    assert out["classes"]["monitor"]["unique_ips"] == 1
    assert dict(out["classes"]["monitor"]["going"]["paths"]).get("/health") == 600
    assert dict(out["classes"]["human"]["going"]["paths"]).get("/bible.html") == 1


def test_window_excludes_old():
    p = Path(tempfile.mkdtemp(prefix="nh-traffic-")) / "a.log"
    p.write_text(_line("5.5.5.5", "/", "Chrome/120 Safari Mozilla", ts=1000), encoding="utf-8")
    out = rollup([str(p)], days=1, now=1_000_000)   # the one line is far older than the window
    assert out["totals"]["requests"] == 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} traffic tests passed — humans aggregated, bots/agents named, from+going roll up.")
