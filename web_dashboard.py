import argparse
import base64
import html
import os
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "checkin.log"


def read_log():
    if not LOG_FILE.exists():
        return ""
    return LOG_FILE.read_text(encoding="utf-8", errors="replace")


def split_runs(text):
    markers = list(re.finditer(r"^===== .*? =====$", text, re.MULTILINE))
    if not markers:
        return [text.strip()] if text.strip() else []

    runs = []
    for index, marker in enumerate(markers):
        start = marker.start()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            runs.append(chunk)
    return runs


def split_checkin_runs(text):
    starts = list(re.finditer(r"^开始抢签：", text, re.MULTILINE))
    if not starts:
        return []

    runs = []
    for index, start_match in enumerate(starts):
        start = start_match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        marker = text.rfind("=====", 0, start)
        if marker >= 0:
            previous_newline = text.rfind("\n", 0, start)
            if marker > previous_newline - 120:
                start = marker
        chunk = text[start:end].strip()
        if chunk:
            runs.append(chunk)
    return runs


def extract_value(pattern, text, default="--"):
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else default


def parse_latest():
    text = read_log()
    runs = split_runs(text)
    structured_runs = split_checkin_runs(text)
    latest = structured_runs[-1] if structured_runs else (runs[-1] if runs else "")

    data = {
        "raw": latest or "暂无日志",
        "title": extract_value(r"^(Vae\+ .+)$", latest),
        "account": extract_value(r"^【(.+?)】$", latest),
        "conclusion": extract_value(r"^\* 结论：(.+)$", latest),
        "checkin": extract_value(r"^\* 签到：(.+)$", latest),
        "attempts": extract_value(r"^\* 尝试：(.+)$", latest),
        "date": extract_value(r"^\* 日期：(.+)$", latest),
        "status": extract_value(r"^\* 签到状态：(.+)$", latest),
        "streak": extract_value(r"^\* 连续签到：(.+)$", latest),
        "total": extract_value(r"^\* 总签到数：(.+)$", latest),
        "rank": extract_value(r"^\* 今日排名：(.+)$", latest),
        "warmup": extract_value(r"^预热 .+?：.+? - (.+)$", latest),
        "request_ms": extract_value(r"^\d+\. \[.+?\].+?（(\d+ms)）$", latest),
        "push": "成功" if "【企业微信】推送成功" in latest else "--",
        "run_count": len(runs),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return data


def badge_class(value):
    if value in ("成功", "已签到") or "成功" in value:
        return "ok"
    if value == "--":
        return ""
    if "失败" in value or "异常" in value:
        return "bad"
    return "warn"


def render_page():
    data = parse_latest()
    cards = [
        ("结论", data["conclusion"], badge_class(data["conclusion"])),
        ("签到返回", data["checkin"], badge_class(data["checkin"])),
        ("今日排名", data["rank"], "ok" if data["rank"] == "第1名" else "warn"),
        ("签到状态", data["status"], badge_class(data["status"])),
        ("请求耗时", data["request_ms"], ""),
        ("尝试情况", data["attempts"], ""),
        ("预热", data["warmup"], ""),
        ("推送", data["push"], badge_class(data["push"])),
        ("连续签到", data["streak"], ""),
        ("总签到数", data["total"], ""),
        ("日志日期", data["date"], ""),
        ("账号", data["account"], ""),
    ]

    card_html = "\n".join(
        f"""
        <section class="card {klass}">
          <div class="label">{html.escape(label)}</div>
          <div class="value">{html.escape(value)}</div>
        </section>
        """
        for label, value, klass in cards
    )

    raw = html.escape(data["raw"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <title>Vae+ 签到看板</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #e5e7eb;
      --ok: #0f8a4b;
      --ok-bg: #eaf8f0;
      --warn: #a35c00;
      --warn-bg: #fff5df;
      --bad: #b42318;
      --bad-bg: #fff0ee;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      padding: 24px clamp(16px, 4vw, 48px) 12px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(24px, 4vw, 36px); }}
    .sub {{ color: var(--muted); font-size: 14px; }}
    main {{ padding: 20px clamp(16px, 4vw, 48px) 36px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .card {{
      min-height: 96px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 14px 16px;
    }}
    .card.ok {{ background: var(--ok-bg); border-color: #b7ebc9; }}
    .card.warn {{ background: var(--warn-bg); border-color: #ffe0a3; }}
    .card.bad {{ background: var(--bad-bg); border-color: #ffc7c2; }}
    .label {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .value {{ font-size: 20px; font-weight: 700; line-height: 1.25; overflow-wrap: anywhere; }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
    }}
    .panel-title {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      font-weight: 700;
    }}
    pre {{
      margin: 0;
      padding: 16px;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.55;
      color: #111827;
    }}
    footer {{ margin-top: 14px; color: var(--muted); font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>Vae+ 签到看板</h1>
    <div class="sub">最近一次签到结果，页面每 30 秒自动刷新。当前服务器时间：{html.escape(data["updated_at"])}</div>
  </header>
  <main>
    <div class="grid">{card_html}</div>
    <section class="panel">
      <div class="panel-title">原始日志片段</div>
      <pre>{raw}</pre>
    </section>
    <footer>已读取日志批次：{data["run_count"]}</footer>
  </main>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def is_authorized(self):
        password = os.environ.get("DASHBOARD_PASSWORD", "")
        if not password:
            return True

        username = os.environ.get("DASHBOARD_USER", "admin")
        header = self.headers.get("Authorization", "")
        prefix = "Basic "
        if not header.startswith(prefix):
            return False
        try:
            decoded = base64.b64decode(header[len(prefix):]).decode("utf-8")
        except Exception:
            return False
        return decoded == f"{username}:{password}"

    def require_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Vae Check-in Dashboard"')
        self.end_headers()

    def do_GET(self):
        if not self.is_authorized():
            self.require_auth()
            return

        if self.path not in ("/", "/index.html"):
            self.send_response(404)
            self.end_headers()
            return
        body = render_page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Vae+ 签到网页看板")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
