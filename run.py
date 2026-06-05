import argparse
import json
import sys
from pathlib import Path

from notifier import Notifier
from vae_api import run_checkin


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


def main():
    parser = argparse.ArgumentParser(description="Vae+ 云服务器签到脚本")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Cookie/Webhook 配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)
    users = get_enabled_users(config)
    if not users:
        raise RuntimeError("没有可执行账号，请在 config.json 的 users 中填写 Cookie。")

    checkin_results = []
    status_results = []
    message_parts = []

    for user in users:
        print(f"【{user['name']}】开始签到")
        try:
            checkin_ok, status_ok, message = run_checkin(user["cookie"])
        except Exception as exc:
            checkin_ok = False
            status_ok = False
            message = f"【状态】\n* 签到失败：{exc}"

        checkin_results.append(checkin_ok)
        status_results.append(status_ok)
        message_parts.append(f"【{user['name']}】\n{message}")

    title = "Vae+ 签到成功!" if all(checkin_results) else "Vae+ 签到失败!"
    content = f"{title}\n" + "\n".join(message_parts)

    print(content)
    Notifier(config.get("notify", {})).send(title, content)

    return 0 if all(status_results) else 1


if __name__ == "__main__":
    sys.exit(main())
