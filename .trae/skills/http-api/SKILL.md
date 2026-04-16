---
name: "astrbot-http-api"
description: "AstrBot HTTP API 完整指南，包括 API Key 管理、对话接口、消息发送、文件上传等。当用户需要通过 HTTP API 与 AstrBot 交互或集成到外部系统时调用此 skill。"
---

# AstrBot HTTP API - 外部接口集成指南

基于 [AstrBot 官方文档 - HTTP API](https://docs.astrbot.app/dev/openapi.html) 的完整指南。

## 🌐 概述

从 **v4.18.0** 开始，AstrBot 提供基于 **API Key** 的 HTTP API，开发者可以通过标准的 HTTP 请求访问 AstrBot 的核心能力。

## 🔑 第一步：创建 API Key

### 在 WebUI 中创建

1. 打开 AstrBot WebUI（默认 `http://localhost:6185`）
2. 进入 **设置** 页面
3. 找到 **API Key** 管理区域
4. 点击 **创建新的 API Key**
5. 设置 Key 名称和权限范围（Scopes）
6. 复制生成的 Key（格式：`abk_xxxxxx`）

> ⚠️ **重要**: 请妥善保管 API Key，它相当于你的访问凭证！

## 📡 第二步：认证方式

### 请求头携带 API Key

支持两种方式：

```bash
# 方式一：Authorization 头（推荐）
curl -H "Authorization: Bearer abk_xxx" ...

# 方式二：X-API-Key 头
curl -H "X-API-Key: abk_xxx" ...
```

### Python 示例

```python
import aiohttp

API_KEY = "abk_your_key_here"
BASE_URL = "http://localhost:6185"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async with aiohttp.ClientSession() as session:
    async with session.post(
        f"{BASE_URL}/api/v1/chat",
        headers=headers,
        json={"message": "Hello", "username": "test"}
    ) as resp:
        result = await resp.json()
```

## 🔐 第三步：Scope 权限说明

创建 API Key 时可配置 Scopes，每个 Scope 控制可访问的接口范围：

| Scope | 作用 | 可访问接口 |
|-------|------|-----------|
| `chat` | 对话能力 | POST /api/v1/chat, GET /api/v1/chat/sessions |
| `config` | 配置文件 | GET /api/v1/configs |
| `file` | 文件上传 | POST /api/v1/file |
| `im` | IM 消息 | POST /api/v1/im/message, GET /api/v1/im/bots |

**权限不足返回**: `403 Insufficient API key scope`

## 💬 第四步：对话类接口

### POST /api/v1/chat - 发送对话消息

**特点**: SSE 流式返回，适合实时获取 AI 回复

#### 请求格式

```json
{
  "message": "Hello",
  "username": "alice",
  "session_id": "my_session_001",
  "enable_streaming": true
}
```

**必填字段**:
- `message`: 消息内容
- `username`: 用户标识

**可选字段**:
- `session_id`: 会话 ID（不传则自动生成 UUID）
- `enable_streaming`: 是否启用流式输出（默认 false）

#### cURL 示例

```bash
# 基础对话
curl -N 'http://localhost:6185/api/v1/chat' \
  -H 'Authorization: Bearer abk_xxx' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello","username":"alice"}'

# 流式输出（SSE）
curl -N 'http://localhost:6185/api/v1/chat' \
  -H 'Authorization: Bearer abk_xxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "message":"介绍一下 Python",
    "username":"alice",
    "enable_streaming": true
  }'
```

#### Python 示例（流式）

```python
import aiohttp
import json

async def chat_streaming(message: str, username: str):
    """流式对话示例"""
    
    url = "http://localhost:6185/api/v1/chat"
    headers = {
        "Authorization": "Bearer abk_xxx",
        "Content-Type": "application/json"
    }
    payload = {
        "message": message,
        "username": username,
        "enable_streaming": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            # SSE 流式读取
            async for line in resp.content:
                if line:
                    print(line.decode('utf-8'), end='')
```

### GET /api/v1/chat/sessions - 查询会话列表

#### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `username` | ✅ | 用户标识 |
| `page` | 否 | 页码（默认 1） |
| `page_size` | 否 | 每页数量（默认 20） |

#### cURL 示例

```bash
curl 'http://localhost:6185/api/v1/chat/sessions?username=alice&page=1&page_size=10' \
  -H 'Authorization: Bearer abk_xxx'
```

## 📁 第五步：文件上传接口

### POST /api/v1/file - 上传附件

上传文件并获取 `attachment_id`，用于在消息中引用。

#### cURL 示例

```bash
curl -X POST 'http://localhost:6185/api/v1/file' \
  -H 'Authorization: Bearer abk_xxx' \
  -F 'file=@/path/to/document.pdf'
```

#### 响应格式

```json
{
  "attachment_id": "9a2f8c72-e7af-4c0e-b352-111111111111",
  "filename": "document.pdf",
  "size": 1234567
}
```

#### Python 示例

```python
async def upload_file(file_path: str) -> str:
    """上传文件并返回 attachment_id"""
    
    url = "http://localhost:6185/api/v1/file"
    headers = {
        "Authorization": "Bearer abk_xxx"
    }
    
    data = aiohttp.FormData()
    data.add_field('file', open(file_path, 'rb'))
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as resp:
            result = await resp.json()
            return result["attachment_id"]
```

## 📨 第六步：IM 消息发送接口

### POST /api/v1/im/message - 主动发送 IM 消息

通过 UMO（Unified Message Origin）主动向指定会话发送消息。

#### 请求格式

```json
{
  "umo": "webchat:FriendMessage:openapi_probe",
  "message": [
    {
      "type": "plain",
      "text": "这是一条主动消息"
    },
    {
      "type": "image",
      "attachment_id": "9a2f8c72-e7af-4c0e-b352-222222222222"
    }
  ]
}
```

**必填字段**:
- `umo`: 目标会话标识
- `message`: 消息内容

#### cURL 示例

```bash
curl -X POST 'http://localhost:6185/api/v1/im/message' \
  -H 'Authorization: Bearer abk_xxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "umo": "aiocqhttp:GroupMessage:123456",
    "message": "大家好！"
  }'
```

### GET /api/v1/im/bots - 获取 Bot 列表

查询已连接的平台适配器和 Bot 信息：

```bash
curl 'http://localhost:6185/api/v1/im/bots' \
  -H 'Authorization: Bearer abk_xxx'
```

## 📝 第七步：Message 字段格式详解

POST `/api/v1/chat` 和 POST `/api/v1/im/message` 的 `message` 字段支持两种格式：

### 格式 1: 纯文本字符串

```json
{
  "message": "Hello World"
}
```

### 格式 2: 消息段数组（Message Chain）

```json
{
  "message": [
    {"type": "plain", "text": "请看这个文件"},
    {"type": "file", "attachment_id": "xxx"}
  ]
}
```

#### 支持的消息段类型

| type | 必填字段 | 可选字段 | 说明 |
|------|----------|----------|------|
| `plain` | - | `text` | 文本段 |
| `reply` | `message_id` | `selected_text` | 引用回复（仅 /api/v1/chat） |
| `image` | `attachment_id` | - | 图片段 |
| `record` | `attachment_id` | - | 音频段 |
| `file` | `attachment_id` | - | 文件段 |
| `video` | `attachment_id` | - | 视频段 |

#### 完整示例：复杂消息

```json
{
  "message": [
    {
      "type": "plain",
      "text": "这是我的报告摘要："
    },
    {
      "type": "reply",
      "message_id": "msg_12345",
      "selected_text": "原始消息"
    },
    {
      "type": "image",
      "attachment_id": "img_uuid_here"
    },
    {
      "type": "file",
      "attachment_id": "file_uuid_here"
    },
    {
      "type": "plain",
      "text": "\n详情请查看附件"
    }
  ]
}
```

> ⚠️ **注意**: 
> - `reply` 不能单独作为唯一内容，至少需要一个有实际内容的段
> - `reply` 目前仅适用于 `/api/v1/chat`
> - `attachment_id` 来自 `POST /api/v1/file` 的上传结果

## 🛠️ 第八步：完整集成示例

### 示例 1: 外部客服系统集成

```python
import aiohttp
import json

class AstrBotClient:
    """AstrBot HTTP API 客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat(self, message: str, username: str, session_id: str = None) -> str:
        """发送对话消息并获取完整回复"""
        
        payload = {
            "message": message,
            "username": username
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat",
                headers=self.headers,
                json=payload
            ) as resp:
                
                # 收集流式响应
                full_response = ""
                async for line in resp.content:
                    if line:
                        full_response += line.decode('utf-8')
                
                return full_response
    
    async def send_message_to_group(self, umo: str, message: str):
        """向群组发送消息"""
        
        payload = {
            "umo": umo,
            "message": message
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/im/message",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()
    
    async def upload_and_send_image(self, umo: str, image_path: str, caption: str):
        """上传图片并发送"""
        
        # 1. 上传文件
        attachment_id = await self.upload_file(image_path)
        
        # 2. 构造消息
        message = [
            {"type": "plain", "text": caption},
            {"type": "image", "attachment_id": attachment_id}
        ]
        
        # 3. 发送
        payload = {"umo": umo, "message": message}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/im/message",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()
    
    async def upload_file(self, file_path: str) -> str:
        """上传文件"""
        
        data = aiohttp.FormData()
        data.add_field('file', open(file_path, 'rb'))
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/file",
                headers={"Authorization": self.headers["Authorization"]},
                data=data
            ) as resp:
                result = await resp.json()
                return result["attachment_id"]


# 使用示例
async def main():
    client = AstrBotClient(
        base_url="http://localhost:6185",
        api_key="abk_your_key"
    )
    
    # 对话
    response = await client.chat(
        message="你好",
        username="customer_001"
    )
    print(response)
    
    # 发送图片到群
    await client.upload_and_send_image(
        umo="aiocqhttp:GroupMessage:123456",
        image_path="/path/to/image.jpg",
        caption="看看这张图片"
    )
```

### 示例 2: Webhook 自动回复

```python
from fastapi import FastAPI, Request
import aiohttp

app = FastAPI()

ASTROBOT_URL = "http://localhost:6185"
API_KEY = "abk_xxx"

@app.post("/webhook")
async def webhook_handler(request: Request):
    """接收外部系统的消息并转发给 AstrBot"""
    
    body = await request.json()
    user_message = body.get("message", "")
    user_id = body.get("user_id", "unknown")
    
    # 转发给 AstrBot
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ASTROBOT_URL}/api/v1/chat",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "message": user_message,
                "username": user_id
            }
        ) as resp:
            result = ""
            async for line in resp.content:
                if line:
                    result += line.decode('utf-8')
            
            return {"reply": result}
```

## 📚 第九步：交互式 API 文档

AstrBot 提供了完整的交互式 API 文档（基于 OpenAPI/Swagger）：

**访问地址**: `https://docs.astrbot.app/scalar.html` 或本地部署的 `{your-host}/scalar.html`

在这里你可以：
- 查看所有 API 接口的详细定义
- 在线测试 API（填入 API Key 即可）
- 查看请求/响应的数据模型
- 复制 cURL/Python/JavaScript 代码示例

## ⚠️ 重要注意事项

### 安全性

1. **不要泄露 API Key**: 特别是在公开的代码仓库中
2. **使用 HTTPS**: 生产环境务必启用 HTTPS
3. **限制 IP 白名单**: 如果可能，限制 API 访问来源 IP
4. **定期轮换 Key**: 定期更换 API Key

### 性能考虑

1. **合理使用流式**: 对于长回复启用 streaming 减少延迟感知
2. **复用连接**: 使用连接池（如 aiohttp.ClientSession）
3. **设置超时**: 避免请求无限等待
4. **批量操作**: 尽量减少不必要的 API 调用

### 错误处理

常见 HTTP 状态码：

| 状态码 | 含义 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式 |
| 401 | 未认证 | 检查 API Key 是否正确 |
| 403 | 权限不足 | 检查 Scope 是否包含所需权限 |
| 404 | 接口不存在 | 检查 URL 和 AstrBot 版本 |
| 500 | 服务器错误 | 查看 AstrBot 日志 |

## 💡 最佳实践

1. **封装客户端库**: 将 API 调用封装为易用的类
2. **实现重试机制**: 对于网络不稳定的环境添加重试
3. **日志记录**: 记录 API 调用便于排查问题
4. **缓存策略**: 对频繁查询的结果适当缓存
5. **速率限制**: 避免过度调用导致被限流

---

**使用场景**: 当你需要从外部系统（Web 应用、移动端、其他服务）与 AstrBot 进行交互，或者需要集成 AstrBot 到现有系统中时使用此 skill。
