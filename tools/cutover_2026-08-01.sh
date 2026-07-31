#!/bin/sh
# THE MIDNIGHT CUTOVER — 2026-08-01, the start date.
#
# Matt, 2026-07-31: "We deploy at Midnight. We 8/1/2026 start date."
#
# Written the evening before, while every step was still fresh, so the cutover is ONE command
# rather than a memory exercise at midnight. Three units, gated together at 1,045 tests:
#
#   1. the receipt is also a card   — a seal outlives the machine that minted it
#   2. llms.txt                      — what agents read to learn what we are, made true again
#   3. /canon.html                   — the last shim that dropped its ?ref=
#
# ORDER MATTERS and is not cosmetic. The app change must land BEFORE the Caddy line is removed:
# Caddy answers /canon.html today, so removing its redirect first would 404 the path for as long
# as the deploy takes. App first, then Caddy, then verify.
#
#   sh tools/cutover_2026-08-01.sh            # deploy + Caddy + verify
#   sh tools/cutover_2026-08-01.sh --verify   # verification only (safe to re-run any time)
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOX="nh@5.78.186.55"
KEY="$HOME/.ssh/id_ed25519_nh"
COM="https://narrowhighway.com"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok=0; bad=0
check() {  # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then ok=$((ok+1)); printf '   ok    %-52s %s\n' "$1" "$3"
  else bad=$((bad+1));     printf '   FAIL  %-52s got %s, want %s\n' "$1" "$3" "$2"; fi
}

if [ "${1:-}" != "--verify" ]; then
  say "1/3  the gate — nothing goes out unproven"
  ( cd "$ROOT" && PYTHONPATH=src python tools/check.py | tail -3 )

  say "2/3  deploy the staged set"
  ( cd "$ROOT" && sh tools/deploy.sh \
      src/concordance/cas.py \
      src/concordance/corpus.py \
      src/concordance/web/api.py \
      site/llms.txt \
      tests/test_receipt_is_also_a_card.py \
      tests/MANIFEST.txt )

  say "3/3  the Caddy line comes out — AFTER the app can answer /canon.html"
  ssh -i "$KEY" -o ConnectTimeout=20 "$BOX" '
    sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-2026-08-01
    sudo sed -i "/redir \/canon.html \/bible.html 301/d" /etc/caddy/Caddyfile
    sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null \
      && sudo systemctl reload caddy && echo "   caddy reloaded (backup: Caddyfile.before-2026-08-01)"
  '
fi

say "VERIFY LIVE — not HTTP 200, the thing itself"

# the reference survives the hop it used to die on
loc=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 25 "$COM/canon.html?ref=Revelation%205")
case "$loc" in *"bible.html?ref=Revelation"*) check "/canon.html carries its ?ref=" "yes" "yes";;
                *) check "/canon.html carries its ?ref=" "yes" "no ($loc)";; esac

# a receipt minted now resolves from its card even with no CAS object
h=$(curl -s --max-time 30 -X POST "$COM/verify" -H 'content-type: application/json' \
    -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}' \
    | python -c 'import sys,json;d=json.load(sys.stdin);print((d.get("seal") or {}).get("content_hash") or d.get("content_hash") or "")')
if [ -n "$h" ]; then
  check "a fresh seal resolves at /s/<hash>" "200" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$COM/s/$h")"
  check "and its card is in the keeping" "200" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$COM/card?id=card_seal_$h")"
else
  bad=$((bad+1)); printf '   FAIL  %-52s no hash came back from /verify\n' "a fresh seal"
fi

# what agents read
check "llms.txt names the Corpus" "yes" \
  "$(curl -s --max-time 25 "$COM/llms.txt" | grep -qi 'corpus.html' && echo yes || echo no)"
check "llms.txt no longer claims a witness-only section" "yes" \
  "$(curl -s --max-time 25 "$COM/llms.txt" | grep -q 'Witness surface only' && echo no || echo yes)"

# the doors still agree, and knowledge is still open
check "an agent on .com sees the full tool list" "79" \
  "$(curl -s --max-time 30 -X POST "$COM/mcp" -H 'content-type: application/json' \
     -H 'accept: application/json, text/event-stream' \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
     | python -c 'import sys,json,re;m=re.search(r"\{.*\}",sys.stdin.read(),re.S);print(len(json.loads(m.group(0))["result"]["tools"]) if m else 0)')"
for p in /passage?ref=John%203:16 /characters?search=Aaron /commentary?ref=John%203:16; do
  check "open on .com: ${p%%\?*}" "open" \
    "$(curl -s --max-time 25 "$COM$p" | python -c 'import sys,json;print("REFUSED" if json.load(sys.stdin).get("gate")=="closed" else "open")' 2>/dev/null || echo unreadable)"
done

printf '\n   %d ok, %d failed\n' "$ok" "$bad"
[ "$bad" -eq 0 ] || { printf '\n   THE CUTOVER IS NOT DONE. Read the failures above before anything else.\n'; exit 1; }
printf '\n   Start date 2026-08-01. Still to do by hand: walk the reader path in a browser.\n'
