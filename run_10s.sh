#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

{
  echo "===== scheduled checkin $(date '+%Y-%m-%d %H:%M:%S') ====="
  python3 -u run.py --wait-until 00:00:02 --prewarm-seconds 2 --attempts 12 --interval 0.25
} >> checkin.log 2>&1
