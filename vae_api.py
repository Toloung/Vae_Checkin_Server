# encoding=utf-8
import datetime
import time

import requests


DEFAULT_TIMEOUT = 15
CHECKIN_URL = "http://api1-xusong.91q.com/USER_HOME/addRecord"
STATUS_URL = "http://api1-xusong.91q.com/USER_HOME/getRecord"

ACCOUNT_ISSUE_KEYWORDS = (
    "登录",
    "密码",
    "cookie",
    "Cookie",
    "失效",
    "过期",
    "无效",
    "设备",
)
ALREADY_SIGNED_KEYWORDS = ("一天只能签到一次", "已经签到", "已签到")
RETRYABLE_KEYWORDS = (
    "请求失败",
    "超时",
    "timeout",
    "timed out",
    "Connection",
    "连接",
    "频繁",
    "稍后",
    "502",
    "503",
    "504",
)


def format_server_time(timestamp):
    if not timestamp:
        return "未知"
    china_timezone = datetime.timezone(datetime.timedelta(hours=8))
    dt = datetime.datetime.fromtimestamp(timestamp, china_timezone)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def post_api(url, cookie):
    response = requests.post(url, headers={"Cookie": cookie}, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def checkin(cookie):
    data = post_api(CHECKIN_URL, cookie)
    if data.get("state"):
        message = data.get("animation", {}).get("medal", {}).get("title", "签到成功")
        return True, message
    return False, data.get("errMsg", "签到失败")


def status(cookie):
    data = post_api(STATUS_URL, cookie)
    if data.get("state"):
        record = data.get("result", {}).get("signRecord", {})
        return {
            "ok": True,
            "continuity": record.get("continuity", 0),
            "total_count": record.get("totalCount", 0),
            "sign_today": record.get("signToday", False),
            "rank": record.get("rank", 0),
            "server_time": data.get("serverTime", 0),
        }

    return {
        "ok": False,
        "message": data.get("errMsg", "查询签到状态失败"),
        "server_time": data.get("serverTime", 0),
    }


def format_rank(rank):
    if rank > 100 or rank == 0:
        return "未进入排行榜"
    return f"第{rank}名"


def contains_any(message, keywords):
    return any(keyword in message for keyword in keywords)


def classify_checkin_result(ok, message):
    if ok:
        return "success", "签到成功", False
    if contains_any(message, ALREADY_SIGNED_KEYWORDS):
        return "already_signed", "今日已签到", False
    if contains_any(message, ACCOUNT_ISSUE_KEYWORDS):
        return "account_issue", "账号或 Cookie 异常", False
    if contains_any(message, RETRYABLE_KEYWORDS):
        return "retryable", "可重试异常", True
    return "unknown", "未知返回，继续尝试", True


def run_checkin(cookie, attempts=1, interval=1):
    attempts = max(1, int(attempts))
    interval = max(0, float(interval))

    attempt_logs = []
    checkin_ok = False
    checkin_message = "未执行"
    result_code = "not_run"
    result_label = "未执行"
    started_at = time.monotonic()

    for attempt in range(1, attempts + 1):
        request_started_at = time.monotonic()
        try:
            checkin_ok, checkin_message = checkin(cookie)
        except Exception as exc:
            checkin_ok = False
            checkin_message = f"请求失败：{exc}"

        elapsed_ms = int((time.monotonic() - request_started_at) * 1000)
        result_code, result_label, should_retry = classify_checkin_result(checkin_ok, checkin_message)
        attempt_logs.append(f"{attempt}. [{result_label}] {checkin_message}（{elapsed_ms}ms）")

        if not should_retry:
            break

        if attempt < attempts:
            time.sleep(interval)

    try:
        current_status = status(cookie)
    except Exception as exc:
        current_status = {
            "ok": False,
            "message": f"查询签到状态失败：{exc}",
            "server_time": 0,
        }

    total_elapsed = time.monotonic() - started_at
    attempt_summary = "\n".join(attempt_logs)

    if current_status["ok"]:
        sign_today_text = "已签到" if current_status["sign_today"] else "未签到"
        success_today = checkin_ok or result_code == "already_signed" or bool(current_status["sign_today"])
        final_label = "成功" if success_today else result_label
        message = (
            "【状态】\n"
            f"* 结论：{final_label}\n"
            f"* 签到：{checkin_message}\n"
            f"* 尝试：{len(attempt_logs)}/{attempts} 次，用时 {total_elapsed:.2f} 秒\n"
            f"* 记录：\n{attempt_summary}\n"
            f"* 日期：{format_server_time(current_status['server_time'])}\n"
            f"* 签到状态：{sign_today_text}\n"
            f"* 连续签到：{current_status['continuity']}天\n"
            f"* 总签到数：{current_status['total_count']}天\n"
            f"* 今日排名：{format_rank(current_status['rank'])}"
        )
        return success_today, True, message

    message = (
        "【状态】\n"
        f"* 结论：{result_label}\n"
        f"* 签到：{checkin_message}\n"
        f"* 尝试：{len(attempt_logs)}/{attempts} 次，用时 {total_elapsed:.2f} 秒\n"
        f"* 记录：\n{attempt_summary}\n"
        f"* 日期：{format_server_time(current_status['server_time'])}\n"
        "* 状态：失败\n"
        f"* 日志：{current_status['message']}"
    )
    return checkin_ok or result_code == "already_signed", False, message
