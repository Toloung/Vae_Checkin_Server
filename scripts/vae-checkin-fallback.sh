#!/usr/bin/env bash
set -euo pipefail

cd /root/Vae_Checkin_Server
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

today="$(date '+%Y-%m-%d')"
if grep -q "$today" checkin.log 2>/dev/null; then
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
