import argparse
import datetime
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from notifier import Notifier
from vae_api import create_session, run_checkin, warmup


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = BASE_DIR / "config.json"


def load_config(path):
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = BASE_DIR / config_path
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_enabled_users(config):
    users = []
    for index, user in enumerate(config.get("users", []), start=1):
        if user.get("enabled", True) is False:
            continue
        cookie = (user.get("cookie") or "").strip()
        if not cookie:
            continue
        users.append(
            {
                "name": user.get("name") or f"账号{index}",
                "cookie": cookie,
            }
        )
    return users


def get_run_options(config, args):
    run_config = config.get("run", {})
    attempts = args.attempts if args.attempts is not None else run_config.get("attempts", 1)
    interval = args.interval if args.interval is not None else run_config.get("interval_seconds", 1)
    max_workers = run_config.get("max_workers") or len(config.get("users", [])) or 1

    return {
        "attempts": max(1, int(attempts)),
        "interval": max(0, float(interval)),
        "max_workers": max(1, int(max_workers)),
    }


def execute_user(user, attempts, interval):
    try:
        checkin_ok, status_ok, message = run_checkin(
            user["cookie"],
            attempts=attempts,
            interval=interval,
            session=user.get("session"),
        )
    except Exception as exc:
        checkin_ok = False
        status_ok = False
        message = f"【状态】\n* 签到失败：{exc}"

    return {
        "name": user["name"],
        "checkin_ok": checkin_ok,
        "status_ok": status_ok,
        "message": message,
    }


def resolve_target_time(clock_time):
    parts = clock_time.split(":")
    if len(parts) == 2:
        hour = int(parts[0])
        minute = int(parts[1])
        second = 0.0
    elif len(parts) == 3:
        hour = int(parts[0])
        minute = int(parts[1])
        second = float(parts[2])
    else:
        raise ValueError("--wait-until 必须是 HH:MM、HH:MM:SS 或 HH:MM:SS.sss")

    whole_second = int(second)
    microsecond = int(round((second - whole_second) * 1_000_000))

    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=whole_second, microsecond=microsecond)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target


def precise_wait_until(target, label):
    while True:
        remaining = (target - datetime.datetime.now()).total_seconds()
        if remaining <= 0:
            return
        if remaining > 1:
            time.sleep(remaining - 0.3)
        elif remaining > 0.05:
            time.sleep(remaining / 2)
        elif remaining > 0.003:
            time.sleep(0.001)
        else:
            pass


def warmup_users(users, max_workers):
    print("开始预热连接")

    def do_warmup(user):
        session = create_session()
        ok, message = warmup(user["cookie"], session=session)
        user["session"] = session
        return user["name"], ok, message

    workers = min(len(users), max_workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(do_warmup, user) for user in users]
        for future in as_completed(futures):
            name, ok, message = future.result()
            state = "OK" if ok else "WARN"
            print(f"预热 {state}：{name} - {message}")


def wait_until(clock_time, users=None, max_workers=1, prewarm_seconds=0):
    if not clock_time:
        return

    target = resolve_target_time(clock_time)
    wait_seconds = (target - datetime.datetime.now()).total_seconds()
    print(f"等待到 {target.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} 开始抢签，约 {wait_seconds:.1f} 秒")

    if users and prewarm_seconds > 0:
        prewarm_target = target - datetime.timedelta(seconds=prewarm_seconds)
        if prewarm_target > datetime.datetime.now():
            precise_wait_until(prewarm_target, "预热")
            warmup_users(users, max_workers)

    precise_wait_until(target, "抢签")


def main():
    parser = argparse.ArgumentParser(description="Vae+ 云服务器签到脚本")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Cookie/Webhook 配置文件路径")
    parser.add_argument("--attempts", type=int, default=None, help="每个账号最多尝试签到次数")
    parser.add_argument("--interval", type=float, default=None, help="每次尝试之间的间隔秒数")
    parser.add_argument("--wait-until", default=None, help="等到指定本地时间再开始，例如 00:00:00")
    parser.add_argument("--prewarm-seconds", type=float, default=2, help="抢签前多少秒预热连接，0 表示不预热")
    args = parser.parse_args()

    config = load_config(args.config)
    users = get_enabled_users(config)
    if not users:
        raise RuntimeError("没有可执行账号，请在 config.json 的 users 中填写 Cookie。")

    run_options = get_run_options(config, args)
    checkin_results = []
    status_results = []
    ordered_results = [None] * len(users)

    wait_until(
        args.wait_until,
        users=users,
        max_workers=run_options["max_workers"],
        prewarm_seconds=args.prewarm_seconds,
    )

    print(
        f"开始抢签：{len(users)} 个账号，每个账号最多 {run_options['attempts']} 次，"
        f"间隔 {run_options['interval']} 秒"
    )

    workers = min(len(users), run_options["max_workers"])
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(execute_user, user, run_options["attempts"], run_options["interval"]): index
            for index, user in enumerate(users)
        }
        for future in as_completed(futures):
            index = futures[future]
            ordered_results[index] = future.result()

    message_parts = []
    for result in ordered_results:
        checkin_results.append(result["checkin_ok"])
        status_results.append(result["status_ok"])
        message_parts.append(f"【{result['name']}】\n{result['message']}")

    title = "Vae+ 签到成功!" if all(checkin_results) else "Vae+ 签到失败!"
    content = f"{title}\n" + "\n".join(message_parts)

    print(content)
    Notifier(config.get("notify", {})).send(title, content)

    return 0 if all(status_results) else 1


if __name__ == "__main__":
    sys.exit(main())
