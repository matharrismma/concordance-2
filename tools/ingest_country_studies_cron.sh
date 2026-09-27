#!/bin/sh
# Off-peak, resumable ingest of the LoC FRD Country Studies ON THE BOX (its IP is not rate-limited,
# unlike a dev machine that hammered loc.gov). Installed in the box crontab at 09:00 UTC daily.
# Self-guarding: no-op once complete; skips if an ingest is already running; reloads only on new cards.
#
#   crontab: 0 9 * * * /home/nh/concordance-2/tools/ingest_country_studies_cron.sh
cd /home/nh/concordance-2 || exit 0
DATA=data/country_studies_cards.jsonl
if [ -f "$DATA" ] && [ "$(wc -l < "$DATA" 2>/dev/null)" -ge 72 ]; then exit 0; fi   # complete (73 land; ~5 skip thin OCR)
if pgrep -f card_country_studies.py >/dev/null 2>&1; then exit 0; fi                # already running
before=0; [ -f "$DATA" ] && before=$(wc -l < "$DATA" 2>/dev/null)
python3 tools/card_country_studies.py --all --resume >> data/cs_ingest_cron.log 2>&1
after=0; [ -f "$DATA" ] && after=$(wc -l < "$DATA" 2>/dev/null)
if [ "$after" -gt "$before" ]; then
  echo "$(date -u) reload: $before -> $after cards" >> data/cs_ingest_cron.log
  sudo systemctl restart nh-org nh-com-2 >> data/cs_ingest_cron.log 2>&1
fi
