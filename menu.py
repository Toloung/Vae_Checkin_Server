import json
import subprocess
import sys
from pathlib import Path

from notifier import Notifier


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
EXAMPLE_FILE = BASE_DIR / "config.example.json"
CRON_LINE = f"59 23 * * * {BASE_DIR / 'run_10s.sh'}"


def input_text(prompt, default=""):
    suffix = "（直接回车保留当前值）" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def input_number(prompt, minimum=1, maximum=None):
    value = input(f"{prompt}: ").strip()
    if not value.isdigit():
        return None
    number = int(value)
    if number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    if EXAMPLE_FILE.exists():
        with EXAMPLE_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)
    else:
        config = {"users": [], "notify": {}, "run": {"attempts": 12, "interval_seconds": 0.25}}

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
    print(f"\n添加账号 {number}")
    name = input_text("账号名称", f"账号{number}")
    cookie = input_text("粘贴 Cookie")
    if not cookie:
        print("Cookie 为空，已取消添加。")
        return

    users.append({"name": name, "cookie": cookie, "enabled": True})
    save_config(config)
    print(f"已添加：{name}")


def print_users(users):
    if not users:
        print("- 暂无账号")
        return
    for index, user in enumerate(users, start=1):
        enabled = "启用" if user.get("enabled", True) else "停用"
        name = user.get("name") or f"账号{index}"
        print(f"- {index}. {name} [{enabled}] Cookie={mask_secret(user.get('cookie', ''))}")


def list_config():
    config = load_config()
    users = config.get("users", [])
    notify = config.get("notify", {})
    run_config = config.get("run", {})

    print("\n当前账号：")
    print_users(users)

    print("\n通知配置：")
    print(f"- 企业微信 Webhook：{mask_secret(notify.get('wecom_webhook', ''))}")
    print(f"- Pushplus：{mask_secret(notify.get('pushplus_token', ''))}")
    print(f"- Server酱：{mask_secret(notify.get('serverchan_sendkey', ''))}")
    print(f"- Bark：{mask_secret(notify.get('bark_device_key', ''))}")
    print(f"- Wxpusher：{mask_secret(notify.get('wxpusher_app_token', ''))}")

    print("\n抢签配置：")
    print(f"- 尝试次数：{run_config.get('attempts', 12)}")
    print(f"- 间隔秒数：{run_config.get('interval_seconds', 0.25)}")


def run_checkin():
    print("\n开始执行一次测试签到...")
    subprocess.call([sys.executable, str(BASE_DIR / "run.py"), "--attempts", "1", "--interval", "1"])


def print_cron_help():
    print("\n当前推荐定时任务：\n")
    print(CRON_LINE)
    print("\n它会 23:59 预启动，并在 00:00:00 自动抢签约 3 秒。")


def read_crontab():
    result = subprocess.run(["crontab", "-l"], text=True, capture_output=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def install_cron():
    current = read_crontab()
    lines = []
    for line in current.splitlines():
        if "Vae_Checkin" in line or "Vae_Checkin_Server" in line:
            continue
        lines.append(line)
    lines.append(CRON_LINE)
    new_cron = "\n".join(lines).rstrip() + "\n"
    subprocess.run(["crontab", "-"], input=new_cron, text=True, check=True)
    print("\n已安装/更新定时任务：")
    print(CRON_LINE)


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


def test_notify():
    config = load_config()
    title = "Vae+ 推送测试"
    content = "如果你收到这条消息，说明推送链路正常。"
    Notifier(config.get("notify", {})).send(title, content)
    print("测试推送已发送。")


def choose_user(config):
    users = config.get("users", [])
    print("\n账号列表：")
    print_users(users)
    if not users:
        return None
    index = input_number("请选择账号序号", 1, len(users))
    if index is None:
        print("无效序号。")
        return None
    return index - 1


def rename_user():
    config = load_config()
    index = choose_user(config)
    if index is None:
        return
    user = config["users"][index]
    user["name"] = input_text("新的账号名称", user.get("name") or f"账号{index + 1}")
    save_config(config)
    print("账号名称已更新。")


def update_user_cookie():
    config = load_config()
    index = choose_user(config)
    if index is None:
        return
    user = config["users"][index]
    user["cookie"] = input_text("新的 Cookie", user.get("cookie", ""))
    save_config(config)
    print("Cookie 已更新。")


def toggle_user():
    config = load_config()
    index = choose_user(config)
    if index is None:
        return
    user = config["users"][index]
    user["enabled"] = not user.get("enabled", True)
    save_config(config)
    state = "启用" if user["enabled"] else "停用"
    print(f"账号已{state}。")


def delete_user():
    config = load_config()
    index = choose_user(config)
    if index is None:
        return
    user = config["users"][index]
    confirm = input_text(f"确认删除 {user.get('name', f'账号{index + 1}')}？输入 YES 确认")
    if confirm != "YES":
        print("已取消删除。")
        return
    config["users"].pop(index)
    save_config(config)
    print("账号已删除。")


def account_menu():
    actions = {
        "1": list_config,
        "2": rename_user,
        "3": update_user_cookie,
        "4": toggle_user,
        "5": delete_user,
        "6": add_user,
    }

    while True:
        print(
            """
==============================
 账号管理
==============================
1. 查看账号
2. 修改账号名称
3. 更新账号 Cookie
4. 启用/停用账号
5. 删除账号
6. 添加账号
0. 返回主菜单
"""
        )
        choice = input("请选择数字: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if not action:
            print("无效选择，请重新输入。")
            continue
        action()


def show_menu():
    print(
        """
==============================
 Vae+ 云服务器签到助手
==============================
1. 安装依赖
2. 配置第一个账号和企业微信
3. 添加账号
4. 查看当前配置
5. 立即测试签到
6. 查看定时任务命令
7. 账号管理
8. 配置其他推送渠道
9. 测试推送
10. 安装/更新定时任务
0. 退出
"""
    )


def main():
    actions = {
        "1": install_dependencies,
        "2": configure_first_user,
        "3": add_user,
        "4": list_config,
        "5": run_checkin,
        "6": print_cron_help,
        "7": account_menu,
        "8": configure_more_notify,
        "9": test_notify,
        "10": install_cron,
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
