# Vae_Checkin_Server

Vae+ 云服务器自动签到工具，支持多账号、企业微信等多渠道推送、菜单化配置，以及用于抢每日首签的定时预启动模式。

## 功能

- 多账号签到，可单独启用、停用、改名、更新 Cookie。
- 每天 23:59 预启动，等到 00:00:00 开始抢签，减少 Python 启动延迟。
- 默认最多尝试 12 次，每次间隔 0.25 秒，覆盖约 3 秒。
- 成功、今日已签到、账号/Cookie 异常、网络异常会被区分处理。
- 签到成功、今日已签到或账号异常时会立即停止，不会继续高频请求。
- 最终只发送 1 条汇总通知。
- 支持企业微信、Pushplus、Server酱、Bark、Wxpusher。

## 文件说明

- `menu.py`：菜单助手，推荐日常使用。
- `run.py`：签到主入口。
- `run_10s.sh`：定时任务入口，实际参数为 12 次、0.25 秒间隔。
- `vae_api.py`：Vae+ 接口请求、重试和结果判断。
- `notifier.py`：推送通知。
- `config.example.json`：配置模板。
- `config.json`：真实 Cookie/Webhook 配置，只放在服务器本地，不要上传到公开仓库。
- `crontab.example`：定时任务示例。

## 安装

进入项目目录：

```bash
cd /home/ubuntu/Vae_Checkin_Server
```

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

也可以使用菜单：

```bash
python3 menu.py
```

然后选择：

```text
1. 安装依赖
```

## 配置

启动菜单：

```bash
cd /home/ubuntu/Vae_Checkin_Server
python3 menu.py
```

常用菜单：

```text
2. 配置第一个账号和企业微信
3. 添加账号
4. 查看当前配置
5. 立即测试签到
7. 账号管理
9. 测试推送
10. 安装/更新定时任务
```

账号管理里可以：

```text
1. 查看账号
2. 修改账号名称
3. 更新账号 Cookie
4. 启用/停用账号
5. 删除账号
6. 添加账号
```

配置文件示例：

```json
{
  "users": [
    {
      "name": "账号1",
      "cookie": "JSESSID=xxxxxxxx",
      "enabled": true
    }
  ],
  "notify": {
    "wecom_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx",
    "pushplus_token": "",
    "serverchan_sendkey": "",
    "bark_device_key": "",
    "wxpusher_app_token": "",
    "wxpusher_uids": []
  },
  "run": {
    "attempts": 12,
    "interval_seconds": 0.25
  }
}
```

## 定时抢签

推荐使用菜单安装：

```bash
python3 menu.py
```

选择：

```text
10. 安装/更新定时任务
```

当前推荐定时任务：

```cron
59 23 * * * /home/ubuntu/Vae_Checkin_Server/run_10s.sh
```

它会每天 23:59 预启动程序，然后程序内部等待到 00:00:00 开始签到。

`run_10s.sh` 默认内容：

```bash
python3 run.py --wait-until 00:00:00 --attempts 12 --interval 0.25 >> checkin.log 2>&1
```

如果要调整抢签参数，编辑：

```bash
nano /home/ubuntu/Vae_Checkin_Server/run_10s.sh
```

可改参数：

```text
--wait-until 00:00:00   开始抢签时间
--attempts 12           最多尝试次数
--interval 0.25         每次尝试间隔秒数
```

## 手动测试

测试推送：

```bash
python3 menu.py
```

选择：

```text
9. 测试推送
```

测试签到：

```bash
python3 run.py --attempts 1 --interval 1
```

注意：测试签到会真实请求 Vae+ 接口。当天已经签到时，接口可能返回“今日已签到”或“一天只能签到一次”。

## 日志

定时任务日志默认写入：

```bash
/home/ubuntu/Vae_Checkin_Server/checkin.log
```

查看最近日志：

```bash
tail -80 /home/ubuntu/Vae_Checkin_Server/checkin.log
```

## 安全注意

- 不要把 `config.json` 上传到公开仓库。
- 不要在 README、Issue、截图里暴露 Cookie、Webhook、Push Token。
- 如果接口返回“账号在某设备上登录”或提示修改密码，优先确认账号安全和 Cookie 是否有效。
- 抢签间隔不建议过小；当前 `12 次 / 0.25 秒` 是相对克制的折中配置。

## 常见问题

### 怎么进入服务器菜单？

```bash
ssh -i ~/.ssh/your_key ubuntu@your_server_ip
cd /home/ubuntu/Vae_Checkin_Server
python3 menu.py
```

如果你在 Windows PowerShell：

```powershell
ssh -i $env:USERPROFILE\.ssh\your_key ubuntu@your_server_ip
```

### 为什么定时任务不是 00:00？

因为 `23:59` 是预启动时间。真正开始签到的时间由 `run.py --wait-until 00:00:00` 控制，这样能减少程序启动带来的延迟。

### 会不会连续推送很多条？

不会。程序会汇总所有尝试，最后只发送一条通知。
