import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
EXAMPLE_FILE = BASE_DIR / "config.example.json"


def input_text(prompt, default=""):
    suffix = f"（直接回车使用当前值）" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    if EXAMPLE_FILE.exists():
        with EXAMPLE_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)
    else:
        config = {"users": [], "notify": {}}

    save_config(config)
    return config


def save_config(config):
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)
        file.write("\n")


def mask_secret(value):
    if not value:
        return "未填写"
    if len(value) <= 12:
        return value[:2] + "***"
    return value[:8] + "***" + value[-4:]


def install_dependencies():
    print("\n开始安装依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])
    print("依赖安装完成。")


def configure_first_user():
    config = load_config()
    users = config.setdefault("users", [])
    if not users:
        users.append({"name": "账号1", "cookie": "", "enabled": True})

    user = users[0]
    print("\n配置第一个账号")
    user["name"] = input_text("账号名称", user.get("name", "账号1"))
    user["cookie"] = input_text("粘贴 Cookie", user.get("cookie", ""))
    user["enabled"] = True

    notify = config.setdefault("notify", {})
    print("\n配置企业微信机器人 Webhook")
    notify["wecom_webhook"] = input_text("粘贴 Webhook", notify.get("wecom_webhook", ""))

    save_config(config)
    print("\n已保存到 config.json。")


def add_user():
    config = load_config()
    users = config.setdefault("users", [])
    number = len(users) + 1
    print(f"\n添加账号{number}")
    name = input_text("账号名称", f"账号{number}")
    cookie = input_text("粘贴 Cookie")
    if not cookie:
        print("Cookie 为空，已取消添加。")
        return

    users.append({"name": name, "cookie": cookie, "enabled": True})
    save_config(config)
    print(f"已添加：{name}")


def list_users():
    config = load_config()
    users = config.get("users", [])
    notify = config.get("notify", {})

    print("\n当前账号：")
    if not users:
        print("- 暂无账号")
    for index, user in enumerate(users, start=1):
        enabled = "启用" if user.get("enabled", True) else "停用"
        print(f"- {index}. {user.get('name', f'账号{index}')} [{enabled}] Cookie={mask_secret(user.get('cookie', ''))}")

    print("\n通知配置：")
    print(f"- 企业微信 Webhook：{mask_secret(notify.get('wecom_webhook', ''))}")
    print(f"- Pushplus：{mask_secret(notify.get('pushplus_token', ''))}")
    print(f"- Server酱：{mask_secret(notify.get('serverchan_sendkey', ''))}")
    print(f"- Bark：{mask_secret(notify.get('bark_device_key', ''))}")
    print(f"- Wxpusher：{mask_secret(notify.get('wxpusher_app_token', ''))}")


def run_checkin():
    print("\n开始执行签到...")
    subprocess.call([sys.executable, str(BASE_DIR / "run.py")])


def print_cron_help():
    path = BASE_DIR.as_posix()
    print("\n复制下面这一行到 crontab，就会每天 00:00 自动执行：\n")
    print(f"0 0 * * * cd {path} && python3 run.py >> checkin.log 2>&1")
    print("\n打开 crontab 的命令：crontab -e")


def configure_more_notify():
    config = load_config()
    notify = config.setdefault("notify", {})
    print("\n可选推送配置，不用的直接回车跳过。")
    notify["pushplus_token"] = input_text("Pushplus Token", notify.get("pushplus_token", ""))
    notify["serverchan_sendkey"] = input_text("Server酱 SendKey", notify.get("serverchan_sendkey", ""))
    notify["bark_device_key"] = input_text("Bark DeviceKey", notify.get("bark_device_key", ""))
    notify["wxpusher_app_token"] = input_text("Wxpusher AppToken", notify.get("wxpusher_app_token", ""))
    wxpusher_uids = input_text("Wxpusher UID，多个用英文逗号分隔", ",".join(notify.get("wxpusher_uids", [])))
    notify["wxpusher_uids"] = [item.strip() for item in wxpusher_uids.split(",") if item.strip()]
    save_config(config)
    print("推送配置已保存。")


def show_menu():
    print(
        """
==============================
 Vae+ 云服务器签到助手
==============================
1. 安装依赖
2. 配置第一个账号和企业微信
3. 添加更多账号
4. 查看当前配置
5. 立即测试签到
6. 查看定时任务命令
7. 配置其他推送渠道
0. 退出
"""
    )


def main():
    actions = {
        "1": install_dependencies,
        "2": configure_first_user,
        "3": add_user,
        "4": list_users,
        "5": run_checkin,
        "6": print_cron_help,
        "7": configure_more_notify,
    }

    while True:
        show_menu()
        choice = input("请选择数字: ").strip()
        if choice == "0":
            print("已退出。")
            return
        action = actions.get(choice)
        if not action:
            print("无效选择，请重新输入。")
            continue
        try:
            action()
        except Exception as exc:
            print(f"操作失败：{exc}")


if __name__ == "__main__":
    main()
