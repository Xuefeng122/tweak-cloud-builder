# TweakCloudBuilder

手机上填参数，云端编译，直接下载 deb 包。

## 原理

1. 手机 App / 网页填参数（Bundle ID、弹窗文案等）
2. 上传到服务器
3. 服务器自动生成代码 + 调用 Theos 编译
4. 返回编译好的 deb 文件

## 部署

### 服务器要求

- Linux / macOS
- 装好 Theos 工具链
- Python 3.10+

### 一键部署

```bash
git clone https://github.com/Xuefeng122/tweak-cloud-builder.git
cd tweak-cloud-builder
pip install -r requirements.txt
python server.py
```

服务跑在 `http://your-server:8000`。

## API

### POST /build

**请求体：**
```json
{
  "bundle_id": "com.yourcompany.yourapp",
  "process_name": "YourAppName",
  "tweak_name": "UpdateAlertTweak",
  "alert_title": "更新提示",
  "alert_message_update": "已从 v{old} 更新到 v{new}",
  "alert_message_first": "欢迎使用 v{new}"
}
```

**返回：**
```json
{
  "success": true,
  "download_url": "/download/UpdateAlertTweak.deb"
}
```

### GET /download/:filename

下载编译好的 deb 文件。

## 手机端怎么用

1. 打开任意浏览器
2. 访问 `http://your-server:8000`
3. 填参数，点生成
4. 下载 deb 装到手机上

## 安全提醒

这个服务没有鉴权，任何人都能调。别暴露在公网，或者自己加个 token 验证。

## 安装方法

把下面这句话发给你的 AI 助手：

```
请将公开仓库 https://github.com/Xuefeng122/tweak-cloud-builder 下载并安装为本地 Skill。
```
