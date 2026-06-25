#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/Vae_Checkin_Server
export PYTHONIOENCODING=utf-8

python3 run.py --wait-until 00:00:00 --attempts 12 --interval 0.25 >> checkin.log 2>&1
