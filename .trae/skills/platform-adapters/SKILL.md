---
name: "astrbot-platform-adapters"
description: "AstrBot 平台适配器接入指南，包括 QQ、Telegram、Discord、Slack、飞书、钉钉等主流平台的对接方法。当用户需要将 AstrBot 连接到不同的消息平台时调用此 skill。"
---

# 接入平台适配器 - AstrBot 多平台连接指南

## 🌐 概述

AstrBot 支持连接多种消息平台，每个平台通过**平台适配器（Platform Adapter）**实现。本 Skill 汇总了各平台的接入方法和注意事项。

## 📋 支持的平台列表

| 平台 | 适配器名称 | 类型 | 维护者 |
|------|-----------|------|--------|
| **QQ (OneBot v11)** | aiocqhttp | 官方 | AstrBot 团队 |
| **QQ (官方)** | qq_official | 官方 | AstrBot 团队 |
| **Telegram** | telegram | 官方 | AstrBot 团队 |
| **Discord** | discord | 官方 | AstrBot 团队 |
| **企业微信 (WeCom)** | wecom | 官方 | AstrBot 团队 |
| **飞书 (Lark)** | lark | 官方 | AstrBot 团队 |
| **钉钉 (DingTalk)** | dingtalk | 官方 | AstrBot 团队 |
| **Slack** | slack | 社区 | 社区维护 |
| **Kook (开黑啦)** | kook | 社区 | 社区维护 |
| **VoceChat** | vocechat | 社区 | HikariFroya |
| **Matrix** | matrix | 社区 | stevessr |
| **LINE** | line | 官方 | AstrBot 团队 |
| **Misskey** | misskey | 官方 | AstrBot 团队 |

---

## 🔧 一、QQ 平台

### 方式 1: OneBot v11 适配器（推荐）

适用于 QQ 个人号、NTQQ 等 OneBot 协议实现。

#### 步骤：

1. **安装 OneBot 实现**（选择其一）：
   - [NapCat](https://github.com/NapNeko/NapCatQQ) （推荐）
   - [Lagrange](https://github.com/LagrangeDev/Lagrange.Core)
   - [LLOneBot](https://github.com/LLOneBot/LLOneBot)

2. **配置 NapCat 示例**：
   ```json
   {
     "platform": [
       {
         "type": "aiocqhttp",
         "enable": true,
         "ws_reverse_host": "127.0.0.1",
         "ws_reverse_port": 8080
       }
     ]
   }
   ```

3. **NapCat 配置**：
   - 打开 NapCat WebUI
   - 网络配置 → 设置反向 WebSocket
   - URL: `ws://127.0.0.1:8080/ws`

#### Docker 部署注意：

如果 AstrBot 和 NapCat 都使用 Docker 部署：

```bash
# 创建共享网络
sudo docker network create astrbot-net

# 将两个容器加入网络
sudo docker network connect astrbot-net astrbot-container
sudo docker network connect astrbot-net napcat-container

# NapCat 的 WebUI 中修改 WS 地址为：
# ws://astrbot-container:8080/ws
```

### 方式 2: QQ 官方 API

使用腾讯官方机器人平台（有限制）。

```json
{
  "platform": [
    {
      "type": "qq_official",
      "enable": true,
      "app_id": "YOUR_APP_ID",
      "client_secret": "YOUR_SECRET"
    }
  ]
}
```

> ⚠️ **限制**: 仅支持特定场景（群机器人等），个人号无法使用。

---

## 💬 二、Telegram

### 步骤：

1. **创建 Telegram Bot**:
   - 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot`
   - 按提示设置 Bot 名称和用户名
   - 获取 **Bot Token**

2. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "telegram",
         "enable": true,
         "telegram_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
       }
     ]
   }
   ```

3. **可选配置**:
   ```json
   {
     "type": "telegram",
     "enable": true,
     "telegram_token": "YOUR_TOKEN",
     
     // 高级选项
     "proxy": "socks5://127.0.0.1:7890",  // 代理地址（如需要）
     "webhook_url": "",                    // 自定义 Webhook
     "webhook_port": 8443,                  // Webhook 端口
   }
   ```

4. **测试**: 在 Telegram 中找到你的 Bot，发送 `/start` 或任意消息

### 特殊功能：

- **预输入提示**: 可在 `platform_specific.telegram.pre_ack_emoji` 中启用
- **支持**: 图片、文件、贴纸、内联按钮等

---

## 🎮 三、Discord

### 步骤：

1. **创建 Discord Application**:
   - 访问 [Discord Developer Portal](https://discord.com/developers/applications)
   - 点击 **"New Application"**
   - 设置应用名称

2. **创建 Bot**:
   - 左侧菜单 → **Bot**
   - 点击 **"Add Bot"**
   - 复制 **Bot Token**

3. **设置权限**:
   - 左侧菜单 → **OAuth2 → URL Generator**
   - Scopes 勾选 `bot`
   - Bot Permissions 勾选：
     - ✅ Send Messages
     - ✅ Read Message History
     - ✅ Add Reactions
     - ✅ Attach Files
     - ✅ Use Slash Commands

4. **邀请 Bot 到服务器**:
   - 复制生成的 URL
   - 在浏览器打开并选择服务器授权

5. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "discord",
         "enable": true,
         "discord_bot_token": "YOUR_BOT_TOKEN_HERE"
       }
     ]
   }
   ```

6. **开启 Intent**（重要）:
   - Developer Portal → Bot → **Privileged Gateway Intents**
   - 开启以下选项：
     - ✅ PRESENCE INTENT
     - ✅ SERVER MEMBERS INTENT
     - ✅ MESSAGE CONTENT INTENT

7. **测试**: 在 Discord 服务器中 @你的Bot 发送消息

### 特殊功能：

- **预输入提示**: `platform_specific.discord.pre_ack_emoji`
- **支持**: 嵌入消息、附件、表情反应等

---

## 📱 四、企业微信 (WeCom)

### 步骤：

1. **注册企业微信**:
   - 访问 [企业微信官网](https://work.weixin.qq.com/)
   - 注册并创建企业/组织

2. **创建自建应用**:
   - 企业微信管理后台 → 应用管理 → 自建 → 创建应用
   - 记录 **AgentId** 和 **Secret**

3. **配置可信 IP**:
   - 应用详情 → 企业可信IP
   - 添加 AstrBot 服务器的 IP

4. **获取 CorpID**:
   - 我的企业 → 企业信息 → CorpID

5. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "wecom",
         "enable": true,
         "corp_id": "YOUR_CORP_ID",
         "agent_id": 1000002,
         "secret": "YOUR_APP_SECRET"
       }
     ]
   }
   ```

6. **配置回调 URL**（如需要）:
   - 需要公网可访问的 URL 或使用内网穿透工具

---

## 🚀 五、飞书 (Lark)

### 步骤：

1. **创建飞书应用**:
   - 访问 [飞书开放平台](https://open.feishu.cn/)
   - 创建企业自建应用

2. **获取凭证**:
   - 凭证与基础信息 → App ID 和 App Secret

3. **添加权限**:
   - 权限管理 → 搜索并开通：
     - `im:message` - 消息相关权限
     - `im:chat` - 群组权限

4. **发布应用版本**:
   - 版本管理与发布 → 创建版本并提交审核

5. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "lark",
         "enable": true,
         "app_id": "cli_xxxxxxxxxxxx",
         "app_secret": "YOUR_APP_SECRET"
       }
     ]
   }
   ```

6. **事件订阅配置**（如需要）:
   - 事件与回调 → 配置请求地址

### 特殊功能：

- **预输入提示**: `platform_specific.lark.pre_ack_emoji`

---

## 📌 六、钉钉 (DingTalk)

### 步骤：

1. **创建钉钉应用**:
   - 访问 [钉钉开放平台](https://open-dev.dingtalk.com/)
   - 创建企业内部应用

2. **获取凭证**:
   - 凭证与基础信息 → AppKey 和 AppSecret

3. **配置权限**:
   - 权限管理 → 添加所需权限

4. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "dingtalk",
         "enable": true,
         "app_key": "dingxxxxxxxxx",
         "app_secret": "YOUR_APP_SECRET"
       }
     ]
   }
   ```

---

## 💼 七、Slack

> ⚠️ 此适配器由社区维护，非官方维护。

### 步骤：

1. **创建 Slack App**:
   - 访问 [Slack API](https://api.slack.com/apps)
   - 点击 **Create New App → From Scratch**

2. **配置 App**:
   - **Basic Information**:
     - 复制 **Signing Secret** → 填入 `signing_secret`
   
   - **App-Level Tokens**:
     - Generate Token → 添加 `connections:write` scope → 复制 Token → 填入 `app_token`
   
   - **OAuth & Permissions**:
     - Bot Token Scopes 添加：
       ```
       channels:history, channels:read, channels:write.invites,
       chat:write, chat:write.customize, chat:write.public,
       files:read, files:write, groups:history, groups:read,
       groups:write, im:history, im:read, im:write,
       reactions:read, reactions:write, users:read
       ```
     - Install to Workspace → 复制 **Bot User OAuth Token** → 填入 `bot_token`

3. **选择连接方式**:

   **方式 A: Socket Mode（推荐，简单）**:
   - Socket Mode 页面 → Enable Socket Mode
   
   **方式 B: Webhook Mode（需公网服务器）**:
   - Event Subscriptions → Enable Events
   - Request URL: 填写你的 Webhook 地址
   - Subscribe to bot events:
     - `channel_created`, `channel_deleted`, `member_joined_channel`,
     - `member_left_channel`, `message.channels`, `message.groups`, `message.im`,
     - `reaction_added`, `reaction_removed`, `team_join`

4. **AstrBot 配置**:
   ```json
   {
     "platform": [
       {
         "type": "slack",
         "enable": true,
         "bot_token": "xoxb-xxxxx",
         "app_token": "xapp-xxxxx",
         "signing_secret": "xxxxx"
       }
     ]
   }
   ```

5. **测试**: 在 Slack 中 @你的App 发送 `/help`

---

## 🎵 八、其他社区平台

### Kook (开黑啦)

```bash
# 安装适配器插件
# 在 WebUI 插件市场搜索 astrbot_plugin_kook 并安装
```

### VoceChat

```bash
# 安装适配器插件
# 在 WebUI 插件市场搜索 astrbot_plugin_vocechat 并安装
```

详细配置请参考对应插件的 README 文档。

---

## 🔗 九、通用配置说明

### 多平台同时接入

可以同时配置多个平台：

```json
{
  "platform": [
    {
      "type": "aiocqhttp",
      "enable": true,
      // ... QQ 配置
    },
    {
      "type": "telegram",
      "enable": true,
      // ... Telegram 配置
    },
    {
      "type": "discord",
      "enable": true,
      // ... Discord 配置
    }
  ]
}
```

### 启用/禁用平台

通过 `"enable": false` 可以临时禁用某个平台而不删除配置：

```json
{
  "type": "telegram",
  "enable": false,  // 暂时禁用
  // ...
}
```

### 平台特定设置

某些平台有专属的高级配置项：

```json
{
  "platform_specific": {
    "lark": {
      "pre_ack_emoji": {
        "enable": false,
        "emojis": ["Typing"]
      }
    },
    "telegram": {
      "pre_ack_emoji": {
        "enable": true,
        "emojis": ["✍️"]
      }
    },
    "discord": {
      "pre_ack_emoji": {
        "enable": true,
        "emojis": ["🤔"]
      }
    }
  }
}
```

## 🛠️ 十、调试与排查

### 1. 检查平台连接状态

在 WebUI → Bots 页面查看各平台连接状态：
- 🟢 绿色 = 已连接
- 🔴 红色 = 断开/错误
- 🟡 黄色 = 重连中

### 2. 查看平台日志

WebUI → 日志 → 选择平台类型过滤日志

### 3. 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无法连接 | Token 错误 | 检查 Token 是否正确复制 |
| 收不到消息 | 权限不足 | 检查 Bot 权限是否完整 |
| 发送失败 | API 限制 | 检查频率限制和内容审查 |
| Docker 网络 | 容器隔离 | 使用共享网络或正确映射端口 |
| Webhook 失败 | 公网访问 | 使用 Cloudflare Tunnel 或 ngrok |

### 4. 网络问题解决

**国内访问 Telegram/Discord**:

```json
{
  "http_proxy": "http://127.0.0.1:7890",
  "no_proxy": ["localhost", "127.0.0.1"]
}
```

或为单个平台配置代理：

```json
{
  "type": "telegram",
  "proxy": "socks5://127.0.0.1:7890"
}
```

## 📊 十一、选择合适平台的建议

| 场景 | 推荐平台 | 原因 |
|------|----------|------|
| 个人娱乐/学习 | QQ (OneBot) | 功能丰富，生态成熟 |
| 国际用户/开源项目 | Telegram | 全球可用，API 友好 |
| 游戏社区 | Discord | 语音+文字，适合游戏圈 |
| 企业内部工具 | 企业微信/飞书/钉钉 | 国内企业标配 |
| 技术团队协作 | Slack | 开发者友好 |

## 💡 最佳实践

1. **先测试再上线**: 使用测试群/频道验证功能
2. **合理设置权限**: 只申请必要的最小权限
3. **处理异常情况**: 网络断线时的重连机制
4. **日志监控**: 关注错误率和延迟
5. **定期更新**: 保持适配器和依赖库最新

## 📞 获取帮助

如果在接入过程中遇到问题：

1. **查阅文档**: 各平台官方 API 文档
2. **检查 Issue**: [AstrBot GitHub Issues](https://github.com/AstrBotDevs/AstrBot/issues)
3. **加入社群**: 
   - QQ群: 975206796
   - 各平台对应的开发者社区
4. **提交 Bug**: 包含详细的复现步骤和日志

---

**使用场景**: 当你需要将 AstrBot 连接到 QQ、Telegram、Discord、企业微信等不同消息平台时参考此 skill。
