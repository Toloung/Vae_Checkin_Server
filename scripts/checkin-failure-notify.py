#!/usr/bin/env python3
import datetime
import json
import socket
import subprocess
import sys
import urllib.request


def main():
    unit = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    config_path = "/root/Vae_Checkin_Server/config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except Exception:
        config = {}

    webhook = (config.get("notify") or {}).get("wecom_webhook")
    if not webhook:
        return 0

    try:
        logs = subprocess.run(
            ["journalctl", "-u", unit, "-n", "80", "--no-pager"],
            text=True,
            capture_output=True,
            timeout=10,
        ).stdout
    except Exception as exc:
        logs = f"failed to read journal: {exc}"

    if len(logs) > 3000:
        logs = logs[-3000:]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    host = socket.gethostname()
    content = (
        "Check-in timer failed\n\n"
        f"Unit: {unit}\n"
        f"Host: {host}\n"
        f"Time: {now}\n\n"
        f"Recent logs:\n{logs}"
    )
    body = json.dumps(
        {"msgtype": "text", "text": {"content": content}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
    )

    try:
        urllib.request.urlopen(request, timeout=15).read()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
