#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/Vae_Checkin_Server
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

{
  echo "===== scheduled checkin $(date '+%Y-%m-%d %H:%M:%S') ====="
  python3 -u run.py --wait-until 00:00:00 --prewarm-seconds 2 --attempts 12 --interval 0.25
} >> checkin.log 2>&1
