# Vae_Checkin_Server

使用ChatGPT制作，未经测试 
云服务器傻瓜版 Vae+ 自动签到。

## 最简单用法

把整个 `Vae_Checkin_Server` 文件夹上传到服务器，然后运行：

```bash
cd /home/ubuntu/Vae_Checkin_Server
python3 menu.py
```

进入菜单后按数字操作：

1. 先选 `1` 安装依赖。
2. 再选 `2` 配置第一个账号和企业微信 Webhook。
3. 需要多个账号就选 `3` 添加更多账号。
4. 选 `5` 立即测试签到。
5. 选 `6` 显示定时任务命令。

如果服务器支持 shell 脚本，也可以运行：

```bash
chmod +x start.sh run_once.sh
./start.sh
```

## 文件说明

- `menu.py`：菜单助手，推荐直接用这个。
- `run.py`：真正执行签到的入口。
- `config.json`：真实 Cookie/Webhook，只放服务器本地。
- `config.example.json`：配置模板。
- `vae_api.py`：签到接口。
- `notifier.py`：推送通知。
- `crontab.example`：定时任务示例。

## 多账号

不用改代码，直接运行：

```bash
python3 menu.py
```

然后选择 `3. 添加更多账号`。

## 定时执行

运行菜单后选择 `6`，复制它显示的那一行到 `crontab -e` 里即可。

注意：不要把 `config.json` 上传到公开仓库。
