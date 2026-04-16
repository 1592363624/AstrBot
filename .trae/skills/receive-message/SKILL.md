---
name: "astrbot-receive-message"
description: "AstrBot 消息事件处理详解，包括指令注册、指令组、事件过滤、事件钩子等功能。当用户需要处理各种类型的消息事件或实现复杂的交互逻辑时调用此 skill。"
---

# 接收消息事件 - AstrBot 事件监听与处理

基于 [AstrBot 官方文档 - 处理消息事件](https://docs.astrbot.app/dev/star/guides/listen-message-event.html) 的完整指南。

## 📥 导入必要模块

```python
from astrbot.api.event import filter, AstrMessageEvent
```

⚠️ **重要**: 务必从 `astrbot.api.event.filter` 导入，否则会和 Python 内置的 `filter` 高阶函数冲突！

## 🎯 核心概念

### 消息事件 (AstrMessageEvent)

AstrBot 接收消息平台下发的消息，封装为 `AstrMessageEvent` 对象传递给插件：

```python
class AstrMessageEvent:
    """AstrBot 消息事件对象"""
    
    # 主要属性
    message_obj: AstrBotMessage     # 完整消息对象
    message_str: str                # 纯文本内容
    unified_msg_origin: str         # 统一消息来源标识
    
    # 常用方法
    get_sender_name() -> str        # 获取发送者昵称
    get_sender_id() -> str          # 获取发送者 ID
    get_group_id() -> str           # 获取群组 ID（私聊为空）
```

### 消息对象 (AstrBotMessage)

通过 `event.message_obj` 获取：

```python
class AstrBotMessage:
    type: MessageType                           # 消息类型
    self_id: str                                # 机器人 ID
    session_id: str                             # 会话 ID
    message_id: str                             # 消息 ID
    group_id: str                               # 群组 ID（私聊为空字符串）
    sender: MessageMember                       # 发送者信息
    message: List[BaseMessageComponent]         # 消息链
    message_str: str                            # 纯文本消息
    raw_message: object                         # 平台原始消息对象
    timestamp: int                              # 时间戳
```

## 🔧 一、指令系统

### 1. 基础指令注册

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star


class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld")  # 注册 /helloworld 指令
    async def helloworld(self, event: AstrMessageEvent):
        """这是 hello world 指令"""
        user_name = event.get_sender_name()
        message_str = event.message_str
        yield event.plain_result(f"Hello, {user_name}!")
```

**规则**:
- ⚠️ 指令名**不能包含空格**，否则会被解析为第二个参数
- 用户输入 `/helloworld` 即可触发

### 2. 带参数指令

AstrBot 自动解析命令参数：

```python
@filter.command("add")
def add(self, event: AstrMessageEvent, a: int, b: int):
    """加法计算器
    
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    # 用户输入: /add 1 2
    result = a + b
    yield event.plain_result(f"结果是: {result}")
```

**支持的参数类型**: `int`, `float`, `str`, `bool` 等

### 3. 指令组（Command Groups）

帮助组织相关指令：

```python
@filter.command_group("math")
def math(self):
    """数学计算指令组"""
    pass  # 指令组函数不需要实现逻辑

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    """加法 - /math add 1 2"""
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    """减法 - /math sub 1 2"""
    yield event.plain_result(f"结果是: {a - b}")

@math.command("help")
def math_help(self, event: AstrMessageEvent):
    """显示帮助信息"""
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

**特点**:
- 子指令使用 `指令组名.command()` 注册
- 用户不输入子指令时，显示树形结构
- 支持无限嵌套！

### 4. 嵌套指令组示例

```python
'''
math
├── calc
│   ├── add (a(int),b(int),)
│   ├── sub (a(int),b(int),)
│   └── help (无参数指令)
'''

@filter.command_group("math")
def math():
    pass

@math.group("calc")  # 注意：这里是 group，不是 command_group
def calc():
    pass

@calc.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@calc.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")

@calc.command("help")
def calc_help(self, event: AstrMessageEvent):
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

### 5. 指令别名（v3.4.28+）

```python
@filter.command("help", alias={'帮助', 'helpme'})
def help(self, event: AstrMessageEvent):
    """帮助指令 - 支持 /help, /帮助, /helpme"""
    yield event.plain_result("这是帮助信息...")
```

## 🎭 二、事件类型过滤

### 1. 接收所有消息

```python
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    """接收所有消息事件"""
    yield event.plain_result("收到了一条消息。")
```

### 2. 私聊/群聊过滤

```python
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    """仅接收私聊消息"""
    message_str = event.message_str
    yield event.plain_result("收到了一条私聊消息。")

@filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
async def on_group_message(self, event: AstrMessageEvent):
    """仅接收群聊消息"""
    yield event.plain_result("收到了一条群聊消息。")
```

**EventType 枚举值**:
- `PRIVATE_MESSAGE`: 私聊消息
- `GROUP_MESSAGE`: 群聊消息
- `ALL`: 所有消息

### 3. 平台过滤

```python
@filter.platform_adapter_type(
    filter.PlatformAdapterType.AIOCQHTTP | 
    filter.PlatformAdapterType.QQOFFICIAL
)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    """仅接收 AIOCQHTTP 和 QQOFFICIAL 平台的消息"""
    yield event.plain_result("收到了特定平台的消息。")
```

**PlatformAdapterType 枚举值**:
- `AIOCQHTTP`
- `QQOFFICIAL`
- `GEWECHAT`
- `ALL`

### 4. 权限过滤（管理员指令）

```python
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("admin_test")
async def admin_test(self, event: AstrMessageEvent):
    """仅管理员可用"""
    yield event.plain_result("这是管理员专属指令！")
```

### 5. 组合多个过滤器

使用 AND 逻辑（所有条件都满足才执行）：

```python
@filter.command("hello")
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def private_hello(self, event: AstrMessageEvent):
    """仅在私聊中触发的 hello 指令"""
    yield event.plain_result("你好！（私聊模式）")
```

## 🪝 三、事件钩子（Event Hooks）

> ⚠️ 事件钩子**不支持**与 `@filter.command` 等装饰器一起使用

### 1. Bot 初始化完成钩子（v3.4.34+）

```python
@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    """AstrBot 初始化完成时触发"""
    print("AstrBot 已初始化完成！")
    # 可以在这里执行初始化任务
```

### 2. 等待 LLM 请求钩子

在准备调用 LLM 但还未获取锁时触发：

```python
@filter.on_waiting_llm_request()
async def on_waiting_llm(self, event: AstrMessageEvent):
    """LLM 请求等待中"""
    await event.send("🤔 正在思考中...")
    # 注意：这里不能用 yield，要用 event.send()
```

### 3. LLM 请求钩子

在调用 LLM 前触发，可以修改请求：

```python
from astrbot.api.provider import ProviderRequest

@filter.on_llm_request()
async def my_custom_hook(self, event: AstrMessageEvent, req: ProviderRequest):
    """拦截并修改 LLM 请求"""
    print(req.prompt)  # 查看请求文本
    req.system_prompt += "\n请用中文回答。"  # 自定义 system prompt
```

### 4. LLM 响应钩子

LLM 请求完成后触发：

```python
from astrbot.api.provider import LLMResponse

@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse):
    """处理 LLM 响应"""
    print(resp.completion_text)  # 获取模型返回文本
```

### 5. 消息装饰钩子

发送消息前触发，可用于消息装饰：

```python
import astrbot.api.message_components as Comp

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    """装饰即将发送的消息"""
    result = event.get_result()
    chain = result.chain
    chain.append(Comp.Plain("!"))  # 在末尾添加感叹号
```

### 6. 消息发送后钩子

```python
@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    """消息发送完成后触发"""
    logger.info("消息已发送")
```

## ⚡ 四、高级功能

### 1. 设置优先级

让某些处理器优先执行：

```python
@filter.command("check", priority=10)
async def check_first(self, event: AstrMessageEvent):
    """高优先级指令，先于其他指令执行"""
    # 默认 priority 为 0
    yield event.plain_result("优先检查！")
```

### 2. 控制事件传播

停止后续所有处理：

```python
@filter.command("check_ok")
async def check_ok(self, event: AstrMessageEvent):
    """检查是否允许继续"""
    ok = self.check_permission()
    
    if not ok:
        yield event.plain_result("❌ 权限不足")
        event.stop_event()  # 停止事件传播！
        return
    
    # 后续逻辑...
```

**效果**: 调用 `stop_event()` 后，其他插件的 handler、LLM 请求等都不会执行。

## 📋 过滤器速查表

| 过滤器 | 用途 | 示例 |
|--------|------|------|
| `@filter.command()` | 注册命令 | `@filter.command("cmd")` |
| `@filter.command_group()` | 注册命令组 | `@filter.command_group("group")` |
| `@filter.event_message_type()` | 过滤消息类型 | 私聊/群聊/全部 |
| `@filter.platform_adapter_type()` | 过滤平台 | QQ/Telegram/Discord |
| `@filter.permission_type()` | 权限过滤 | 管理员专用 |
| `@filter.on_astrbot_loaded()` | Bot初始化钩子 | 初始化时触发 |
| `@filter.on_waiting_llm_request()` | LLM等待钩子 | 显示等待提示 |
| `@filter.on_llm_request()` | LLM请求钩子 | 修改请求 |
| `@filter.on_llm_response()` | LLM响应钩子 | 处理响应 |
| `@filter.on_decorating_result()` | 消息装饰钩子 | 装饰消息 |
| `@filter.after_message_sent()` | 发送后钩子 | 日志记录 |

## 💡 最佳实践

1. **合理使用指令组**: 相关功能组织在一起
2. **Docstring 要写好**: 会显示在 WebUI 中
3. **组合过滤器**: 精确控制触发条件
4. **事件钩子慎用**: 不要阻塞主流程
5. **权限控制**: 敏感操作加上管理员权限

---

**使用场景**: 当你需要实现复杂的消息处理逻辑、多级指令系统、或者需要对消息流进行精细控制时使用此 skill。
