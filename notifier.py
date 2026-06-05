import json

import requests


DEFAULT_TIMEOUT = 15


class Notifier:
    def __init__(self, config):
        self.config = config or {}

    def send(self, title, content):
        self._send_wecom(title, content)
        self._send_pushplus(title, content)
        self._send_serverchan(title, content)
        self._send_bark(title, content)
        self._send_wxpusher(title, content)

    def _send_wecom(self, title, content):
        webhook = self.config.get("wecom_webhook")
        if not webhook:
            return
        response = requests.post(
            webhook,
            json={"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        print("【企业微信】推送成功")

    def _send_pushplus(self, title, content):
        token = self.config.get("pushplus_token")
        if not token:
            return
        response = requests.post(
            "http://www.pushplus.plus/send",
            data={
                "token": token,
                "title": title,
                "content": content.replace("\n", "\n\n"),
                "channel": "wechat",
                "template": "markdown",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        self._print_result("Pushplus", response)

    def _send_serverchan(self, title, content):
        sendkey = self.config.get("serverchan_sendkey")
        if not sendkey:
            return
        response = requests.post(
            f"https://sctapi.ftqq.com/{sendkey}.send",
            data={"title": title, "desp": content.replace("\n", "\n\n")},
            timeout=DEFAULT_TIMEOUT,
        )
        self._print_result("Server酱", response)

    def _send_bark(self, title, content):
        device_key = self.config.get("bark_device_key")
        if not device_key:
            return
        response = requests.post(
            "https://api.day.app/push",
            headers={"content-type": "application/json", "charset": "utf-8"},
            data=json.dumps({"title": title, "body": content, "device_key": device_key}),
            timeout=DEFAULT_TIMEOUT,
        )
        self._print_result("Bark", response)

    def _send_wxpusher(self, title, content):
        app_token = self.config.get("wxpusher_app_token")
        uids = self.config.get("wxpusher_uids") or []
        if not app_token or not uids:
            return

        for uid in uids:
            response = requests.post(
                "https://wxpusher.zjiecode.com/api/send/message",
                headers={"Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "appToken": app_token,
                        "content": content.replace("\n", "\n\n"),
                        "contentType": 3,
                        "uids": [uid],
                    }
                ),
                timeout=DEFAULT_TIMEOUT,
            )
            self._print_result("Wxpusher", response)

    @staticmethod
    def _print_result(name, response):
        try:
            response.raise_for_status()
            print(f"【{name}】推送返回：{response.text}")
        except Exception as exc:
            print(f"【{name}】推送失败：{exc}")
