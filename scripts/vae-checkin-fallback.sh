#!/usr/bin/env bash
set -euo pipefail

cd /root/Vae_Checkin_Server
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

today="$(date '+%Y-%m-%d')"
if python3 - <<'PY'
from pathlib import Path
import datetime
import sys

today = datetime.datetime.now().strftime("%Y-%m-%d")
text = Path("checkin.log").read_text(encoding="utf-8", errors="ignore")
marker = "\u7b7e\u5230\u72b6\u6001\uff1a\u5df2\u7b7e\u5230"
index = text.rfind(today)
sys.exit(0 if index >= 0 and marker in text[index:] else 1)
PY
then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] fallback skipped: today's Vae check-in log already exists" >> checkin.log
  exit 0
fi

if ! flock -n /run/vae-checkin.lock true; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] fallback skipped: primary Vae check-in is still running" >> checkin.log
  exit 0
fi

{
  echo "===== fallback checkin $(date '+%Y-%m-%d %H:%M:%S') ====="
  flock /run/vae-checkin.lock python3 -u run.py --attempts 12 --interval 0.25
} >> checkin.log 2>&1
