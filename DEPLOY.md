# TweakCloudBuilder · 服务器部署教程

在 Linux 服务器上部署编译服务，手机浏览器打开网页就能生成 deb。

---

## 一、你需要什么

| 东西 | 说明 |
|---|---|
| Linux 服务器 | Ubuntu 20.04+，有 root 权限 |
| 公网 IP | 手机能访问到 |
| 域名（可选） | 有更好，没有直接用 IP |

---

## 二、安装系统依赖

```bash
sudo apt update
sudo apt install -y git make clang lld ldid dpkg python3-pip
```

验证一下：
```bash
clang --version
ldid
```

能出版本号就 OK。

---

## 三、安装 Theos

```bash
sudo git clone --recursive https://github.com/theos/theos.git /opt/theos
echo "export THEOS=/opt/theos" >> ~/.bashrc
source ~/.bashrc
```

下载 iOS SDK：
```bash
cd /opt/theos/sdks
sudo curl -LO https://github.com/theos/sdks/archive/refs/heads/master.zip
sudo unzip master.zip
sudo mv sdks-master/*.sdk .
```

验证：
```bash
ls $THEOS/sdks/
# 应该看到 iPhoneOS12.4.sdk 之类的
```

---

## 四、部署编译服务

### 1. 下载代码

```bash
cd ~
git clone https://github.com/Xuefeng122/tweak-cloud-builder.git
cd tweak-cloud-builder
```

### 2. 装 Python 依赖

```bash
pip3 install -r requirements.txt
# 如果没有 requirements.txt，直接装：
pip3 install fastapi uvicorn
```

### 3. 测试运行

```bash
python3 server.py
```

看到这个就说明跑起来了：
```
Uvicorn running on http://0.0.0.0:8000
```

### 4. 后台常驻

用 systemd 管理：

```bash
sudo nano /etc/systemd/system/tweak-builder.service
```

写入：
```ini
[Unit]
Description=Tweak Cloud Builder
After=network.target

[Service]
User=root
WorkingDirectory=/root/tweak-cloud-builder
ExecStart=/usr/bin/python3 /root/tweak-cloud-builder/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启用：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tweak-builder
sudo systemctl start tweak-builder
```

查看状态：
```bash
sudo systemctl status tweak-builder
```

---

## 五、手机端怎么用

### 1. 打开浏览器

手机 Safari 或 Chrome 打开：
```
http://你的服务器IP:8000
```

应该能看到：
```json
{"name":"Tweak Cloud Builder","status":"running"}
```

### 2. 发请求编译

用网页或者 curl 测试：

```bash
curl -X POST http://你的服务器IP:8000/build \
  -H "Content-Type: application/json" \
  -d '{
    "bundle_id": "com.yourcompany.yourapp",
    "process_name": "YourApp",
    "tweak_name": "UpdateAlertTweak",
    "alert_title": "更新提示",
    "alert_message_update": "已从 v%@ 更新到 v%@",
    "alert_message_first": "欢迎使用 v%@"
  }'
```

返回：
```json
{
  "success": true,
  "download_url": "/download/UpdateAlertTweak.deb"
}
```

### 3. 下载 deb

浏览器打开：
```
http://你的服务器IP:8000/download/UpdateAlertTweak.deb
```

下载下来，用 Filza 装到越狱手机上。

---

## 六、加个简单网页界面（可选）

现在只有 API，没有网页。想在手机上点点点就能用的话，加个 HTML 页面：

```bash
nano /var/www/index.html
```

写一个简单表单，填参数提交到 `/build`，然后显示下载链接。

---

## 七、安全提醒

- 这个服务没有密码，谁都能调
- 别暴露在公网裸奔，至少加个 token 验证
- 或者只在内网用，手机连同一个 WiFi

---

## 八、故障排查

| 问题 | 解决 |
|---|---|
| 编译失败 | 看服务器日志：`journalctl -u tweak-builder -f` |
| 找不到 SDK | 检查 `$THEOS/sdks/` 里有没有 .sdk 文件 |
| 端口被占 | 改 server.py 里的 port |
| 下载 404 | deb 文件名不对，先调 /build 看返回的 download_url |

---

## 安装方法

把下面这句话发给你的 AI 助手：

```
请将公开仓库 https://github.com/Xuefeng122/tweak-cloud-builder 下载并安装为本地 Skill。
```
