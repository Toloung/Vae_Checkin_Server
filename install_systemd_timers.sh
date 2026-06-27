#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

install -m 0755 scripts/checkin-failure-notify.py /usr/local/bin/checkin-failure-notify.py
install -m 0755 scripts/checkin-status /usr/local/bin/checkin-status
install -m 0755 scripts/vae-checkin-fallback.sh /usr/local/bin/vae-checkin-fallback.sh

install -m 0644 systemd/checkin-failure-notify@.service /etc/systemd/system/checkin-failure-notify@.service
install -m 0644 systemd/vae-checkin.service /etc/systemd/system/vae-checkin.service
install -m 0644 systemd/vae-checkin.timer /etc/systemd/system/vae-checkin.timer
install -m 0644 systemd/vae-checkin-fallback.service /etc/systemd/system/vae-checkin-fallback.service
install -m 0644 systemd/vae-checkin-fallback.timer /etc/systemd/system/vae-checkin-fallback.timer

if [[ -d /root/qqmusic-medal-checkin ]]; then
  install -m 0644 systemd/qqmusic-first-sign.service /etc/systemd/system/qqmusic-first-sign.service
  install -m 0644 systemd/qqmusic-first-sign.timer /etc/systemd/system/qqmusic-first-sign.timer
fi

tmpfile="$(mktemp)"
crontab -l 2>/dev/null | grep -v 'Vae_Checkin_Server' | grep -v 'qqmusic-medal-checkin' > "$tmpfile" || true
crontab "$tmpfile"
rm -f "$tmpfile"

python3 -m py_compile /usr/local/bin/checkin-failure-notify.py
bash -n /usr/local/bin/vae-checkin-fallback.sh

systemctl daemon-reload
systemd-analyze verify \
  /etc/systemd/system/checkin-failure-notify@.service \
  /etc/systemd/system/vae-checkin.service \
  /etc/systemd/system/vae-checkin.timer \
  /etc/systemd/system/vae-checkin-fallback.service \
  /etc/systemd/system/vae-checkin-fallback.timer

systemctl enable --now vae-checkin.timer vae-checkin-fallback.timer

if [[ -d /root/qqmusic-medal-checkin ]]; then
  systemd-analyze verify \
    /etc/systemd/system/qqmusic-first-sign.service \
    /etc/systemd/system/qqmusic-first-sign.timer
  systemctl enable --now qqmusic-first-sign.timer
fi

checkin-status
