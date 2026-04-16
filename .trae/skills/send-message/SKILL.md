---
name: "astrbot-send-message"
description: "AstrBot 消息发送完整指南，包括被动回复、主动推送、富媒体消息（图片/音频/视频/文件）等。当用户需要发送各种类型的消息或实现主动消息推送时调用此 skill。"
---

# 发送消息 - AstrBot 消息发送指南

基于 [AstrBot 官方文档 - 发送消息](https://docs.astrbot.app/dev/star/guides/send-message.html) 的完整指南。

## 📤 一、被动消息（回复）

被动消息是机器人对用户消息的响应式回复。

### 1. 纯文本消息

```python
@filter.command("hello")
async def hello(self, event: AstrMessageEvent):
    """发送纯文本消息"""
    yield event.plain_result("Hello!")
    yield event.plain_result("你好！")  # 可以发送多条
```

### 2. 图片消息

```python
@filter.command("image")
async def send_image(self, event: AstrMessageEvent):
    """发送图片"""
    
    # 从本地文件系统发送
    yield event.image_result("path/to/image.jpg")
    
    # 从 URL 发送（必须以 http 或 https 开头）
    yield event.image_result("https://example.com/image.jpg")
```

### 3. 消息链（富媒体消息）

使用 `MessageChain` 构建包含多种元素的消息：

```python
import astrbot.api.message_components as Comp

@filter.command("rich")
async def send_rich_message(self, event: AstrMessageEvent):
    """发送富媒体消息链"""
    
    chain = [
        Comp.At(qq=event.get_sender_id()),           # @提及发送者
        Comp.Plain("请看这张图片："),                  # 文本
        Comp.Image.fromURL("https://example.com/img"), # URL 图片
        Comp.Image.fromFileSystem("path/to/img.jpg"),   # 本地图片
        Comp.Plain("这是图片说明。")                     # 文本
    ]
    
    yield event.chain_result(chain)
```

## 🚀 二、主动消息（推送）

主动消息是机器人主动推送给用户的消息，不依赖用户触发。

### 基本用法

```python
from astrbot.api.event import MessageChain

@filter.command("schedule")
async def schedule_message(self, event: AstrMessageEvent):
    """设置定时任务或延迟发送"""
    
    # 获取当前会话标识（用于后续发送）
    umo = event.unified_msg_origin
    
    # 构建消息链
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    
    # 在需要的时候主动发送
    await self.context.send_message(umo, message_chain)
```

**应用场景**:
- 定时任务通知
- 异步处理完成后通知
- 后台监控告警
- 订阅信息推送

### 关于 unified_msg_origin

`unified_msg_origin` 是一个字符串，记录了会话的唯一标识：
- 格式：`platform_name:message_type:session_id`
- AstrBot 用它来识别属于哪个平台和哪个会话
- 使用 `send_message()` 时必须提供此参数以确保消息发送到正确的位置

## 🎨 三、消息组件详解

### 文本消息段 (Plain)

```python
Comp.Plain(text="Hello World")
```

> ⚠️ **注意**: 在 aiocqhttp 平台中，`Plain` 类型消息在发送时会自动 `strip()` 去除空格和换行。
> 
> **解决方案**: 在消息前后添加零宽空格 `\u200b` 来保留格式。

### @提及消息段 (At)

```python
Comp.At(qq=123456)                    # @指定 QQ 用户
Comp.At(qq=event.get_sender_id())     # @消息发送者
```

### 图片消息段 (Image)

```python
# 从 URL 加载
Comp.Image.fromURL(url="https://example.com/image.jpg")

# 从本地文件系统加载
Comp.Image.fromFileSystem(path="path/to/image.jpg")
```

### 文件消息段 (File)

```python
Comp.File(file="path/to/file.txt", name="file.txt")
```

> ⚠️ 部分平台可能不支持此消息类型。

### 语音消息段 (Record)

```python
path = "path/to/record.wav"  # 目前仅支持 wav 格式
Comp.Record(file=path, url=path)
```

> 💡 需要自行将其他音频格式转换为 wav。

### 视频消息段 (Video)

```python
from astrbot.api.message_components import Video

# 从本地文件系统加载（需要客户端和机器人同系统）
Video.fromFileSystem(path="test.mp4")

# 更通用的方式（从 URL）
Video.fromURL(url="https://example.com/video.mp4")
```

#### 发送视频消息示例

```python
@filter.command("video")
async def send_video(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Video
    
    video = Video.fromURL(url="https://example.com/video.mp4")
    yield event.chain_result([video])
```

## 📦 四、群转发消息（OneBot v11）

目前仅 OneBot v11 平台支持此功能：

```python
from astrbot.api.message_components import Node, Plain, Image

@filter.command("forward")
async def send_forward(self, event: AstrMessageEvent):
    """发送群转发消息"""
    
    node = Node(
        uin=905617992,              # 发送者 QQ 号
        name="Soulter",             # 显示名称
        content=[
            Plain("hi"),            # 转发内容
            Image.fromFileSystem("test.jpg")
        ]
    )
    
    yield event.chain_result([node])
```

## 🔧 五、MessageChain 高级用法

### 链式构建

```python
from astrbot.api.event import MessageChain

chain = (
    MessageChain()
    .message("第一段文本")
    .at(qq=123456)
    .image_from_url("https://example.com/img")
    .message("第二段文本")
)
```

### 组合使用示例

```python
@filter.command("complex")
async def complex_message(self, event: AstrMessageEvent):
    """复杂消息组合示例"""
    
    import astrbot.api.message_components as Comp
    
    # 构建包含多种元素的消息
    components = [
        Comp.At(qq=event.get_sender_id()),
        Comp.Plain("\n📊 数据报告\n"),
        Comp.Plain("-" * 20 + "\n"),
        Comp.Plain("✅ 任务完成度: 85%\n"),
        Comp.Plain("⏰ 更新时间: 刚刚\n"),
        Comp.Image.fromURL("https://example.com/chart.png"),
        Comp.Plain("\n详情请查看附件 👇"),
        Comp.File(file="report.pdf", name="月度报告.pdf")
    ]
    
    yield event.chain_result(components)
```

## ⚡ 六、异步发送注意事项

在某些场景下（如事件钩子中），需要使用 `event.send()` 而不是 `yield`：

```python
@filter.on_waiting_llm_request()
async def on_waiting(self, event: AstrMessageEvent):
    """LLM 请求等待中的提示（不能使用 yield）"""
    await event.send(event.plain_result("🤔 正在思考中..."))
```

**何时用 `yield`，何时用 `event.send()`**:
- ✅ Handler 中：使用 `yield`
- ✅ 事件钩子中：使用 `await event.send()`
- ✅ 主动推送：使用 `await self.context.send_message()`

## 📋 消息类型速查表

| 方法 | 用途 | 示例 |
|------|------|------|
| `event.plain_result()` | 纯文本 | `yield event.plain_result("Hi")` |
| `event.image_result()` | 图片 | `yield event.image_result("url")` |
| `event.chain_result()` | 消息链 | `yield event.chain_result([comp1, comp2])` |
| `event.send()` | 异步发送 | `await event.send(result)` |
| `self.context.send_message()` | 主动推送 | `await self.context.send_message(umo, chain)` |

## 💡 最佳实践

1. **优先使用消息链**: 支持更丰富的内容展示
2. **注意平台兼容性**: 不是所有平台都支持所有消息类型
3. **合理使用主动消息**: 避免频繁打扰用户
4. **错误处理**: 处理文件不存在、URL 无效等情况
5. **性能考虑**: 大文件建议先上传再发送链接

---

**使用场景**: 当你需要向用户发送各种类型的消息（文本、图片、视频、文件等），或者需要实现主动消息推送功能时使用此 skill。
