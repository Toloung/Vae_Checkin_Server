# encoding=utf-8
import datetime

import requests


DEFAULT_TIMEOUT = 15
CHECKIN_URL = "http://api1-xusong.91q.com/USER_HOME/addRecord"
STATUS_URL = "http://api1-xusong.91q.com/USER_HOME/getRecord"


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
        "message": data.get("errMsg", "查询状态失败"),
        "server_time": data.get("serverTime", 0),
    }


def format_rank(rank):
    if rank > 100 or rank == 0:
        return "未进入排行榜"
    return f"第{rank}名"


def run_checkin(cookie):
    checkin_ok, checkin_message = checkin(cookie)
    current_status = status(cookie)

    if current_status["ok"]:
        sign_today_text = "已签到" if current_status["sign_today"] else "未签到"
        message = (
            "【状态】\n"
            f"* 签到：{checkin_message}\n"
            f"* 日期：{format_server_time(current_status['server_time'])}\n"
            f"* 签到状态：{sign_today_text}\n"
            f"* 连续签到：{current_status['continuity']}天\n"
            f"* 总签到数：{current_status['total_count']}天\n"
            f"* 今日排名：{format_rank(current_status['rank'])}"
        )
        return checkin_ok, True, message

    message = (
        "【状态】\n"
        f"* 日期：{format_server_time(current_status['server_time'])}\n"
        "* 状态：失败\n"
        f"* 日志：{current_status['message']}"
    )
    return checkin_ok, False, message
