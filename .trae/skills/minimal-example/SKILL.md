---
name: "astrbot-minimal-example"
description: "AstrBot 最小插件实例详解，提供完整的代码示例和逐行解释。当用户需要快速理解插件基本结构或创建第一个简单插件时调用此 skill。"
---

# 最小实例 - AstrBot 插件基础结构

基于 [AstrBot 官方文档 - 最小实例](https://docs.astrbot.app/dev/star/guides/simple.html) 的完整代码解析。

## 📝 完整最小实例代码

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger  # 使用 astrbot 提供的 logger 接口


class MyPlugin(Star):
    """我的第一个 AstrBot 插件"""

    def __init__(self, context: Context):
        """
        插件初始化方法
        
        Args:
            context: AstrBot 上下文对象，用于与 AstrBot Core 交互
        """
        super().__init__(context)

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """
        这是一个 hello world 指令
        
        这是 handler 的描述，将会被解析方便用户了解插件内容。
        非常建议填写此描述。
        
        Args:
            event: 消息事件对象，包含发送者、消息内容等信息
        """
        user_name = event.get_sender_name()  # 获取发送者名称
        message_str = event.message_str      # 获取消息的纯文本内容
        
        logger.info("触发hello world指令!")  # 记录日志
        
        yield event.plain_result(f"Hello, {user_name}!")  # 发送纯文本回复

    async def terminate(self):
        """
        插件终止时的清理方法（可选实现）
        
        当插件被卸载/停用时会自动调用此方法
        可以在这里进行资源释放、连接关闭等清理工作
        """
        pass
```

## 🔍 代码逐行解析

### 1. 导入必要的模块

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
```

**关键点**:
- `filter`: 事件过滤器装饰器，用于注册命令和监听器
- `AstrMessageEvent`: 消息事件对象类
- `Context`: AstrBot 上下文类，提供核心 API 访问
- `Star`: 插件基类，所有插件必须继承此类
- `logger`: AstrBot 日志接口（**禁止使用 Python 内置的 logging 模块**）

### 2. 定义插件类

```python
class MyPlugin(Star):
    """插件类必须继承 Star 基类"""
    
    def __init__(self, context: Context):
        super().__init__(context)
```

**重要规则**:
- ✅ 类名可自定义，但**必须继承 Star 类**
- ✅ `__init__` 方法必须接受 `context: Context` 参数
- ✅ 必须调用 `super().__init__(context)` 初始化父类
- ✅ 插件文件必须命名为 `main.py`

### 3. 注册命令处理器

```python
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    '''handler 描述'''
    # 处理逻辑
    yield event.plain_result("回复内容")
```

**Handler 规范**:
- ✅ Handler 必须定义在插件类内部
- ✅ 前两个参数必须是 `self` 和 `event`
- ✅ 使用 `@filter.command()` 装饰器注册命令
- ✅ 命令名不能包含空格
- ✅ 建议填写 Docstring 描述（会显示在 WebUI 中）
- ✅ 如果文件过长，可将服务逻辑写在外部，在 Handler 中调用

### 4. 发送消息响应

```python
yield event.plain_result(f"Hello, {user_name}!")
```

**返回方式**:
- 使用 `yield` 返回结果（被动回复）
- `event.plain_result()`: 发送纯文本消息
- 其他返回方式见 [发送消息 Skill](../send-message/SKILL.md)

### 5. 可选的终止方法

```python
async def terminate(self):
    """插件卸载/停用时调用"""
    pass
```

**用途**:
- 释放资源（数据库连接、文件句柄等）
- 保存状态
- 清理临时文件
- 此方法是可选的，不是必须实现

## 🎯 核心概念说明

### AstrMessageEvent（消息事件对象）

```python
event.get_sender_name()    # 获取发送者昵称
event.get_sender_id()      # 获取发送者 ID
event.message_str          # 纯文本消息内容
event.message_obj          # 完整的消息对象（AstrBotMessage 类型）
event.unified_msg_origin   # 统一消息来源标识
event.get_group_id()       # 群组 ID（私聊时为空）
```

### AstrBotMessage（消息对象）

通过 `event.message_obj` 获取：

```python
class AstrBotMessage:
    type: MessageType                    # 消息类型
    self_id: str                         # 机器人 ID
    session_id: str                      # 会话 ID
    message_id: str                      # 消息 ID
    group_id: str                        # 群组 ID
    sender: MessageMember               # 发送者信息
    message: List[BaseMessageComponent] # 消息链
    message_str: str                     # 纯文本内容
    raw_message: object                  # 原始消息对象
    timestamp: int                       # 时间戳
```

### 消息链（Message Chain）

消息链是一个有序列表，每个元素是消息段：

```python
import astrbot.api.message_components as Comp

# 示例：构建包含文本、@提及、图片的消息链
chain = [
    Comp.Plain(text="Hello"),
    Comp.At(qq=123456),
    Comp.Image(file="https://example.com/image.jpg")
]
```

**常见消息段类型**:
- `Plain`: 文本消息段
- `At`: @提及消息段
- `Image`: 图片消息段
- `Record`: 语音消息段
- `Video`: 视频消息段
- `File`: 文件消息段

## 📂 项目结构示例

```
astrbot_plugin_example/
├── main.py              # 主入口文件（必须）
├── metadata.yaml        # 元数据配置（必须）
├── requirements.txt     # 依赖列表（如需要）
├── logo.png            # 插件 Logo（可选）
└── data/               # 持久化数据目录
```

## ⚠️ 常见错误及解决方案

### 错误 1: 导入冲突

```python
# ❌ 错误：使用 Python 内置 filter
from filter import command

# ✅ 正确：从 astrbot 导入
from astrbot.api.event import filter
```

### 错误 2: 日志使用不当

```python
# ❌ 错误：使用 Python logging
import logging
logging.info("message")

# ✅ 正确：使用 AstrBot logger
from astrbot.api import logger
logger.info("message")
```

### 错误 3: Handler 参数错误

```python
# ❌ 错误：缺少必要参数
async def my_handler(event):
    pass

# ✅ 正确：包含 self 和 event
async def my_handler(self, event: AstrMessageEvent):
    pass
```

## 🚀 下一步学习

掌握最小实例后，建议继续学习：

1. **[接收消息事件](../receive-message/SKILL.md)** - 学习更多事件监听器和过滤器
2. **[发送消息](../send-message/SKILL.md)** - 了解各种消息发送方式
3. **[插件配置](../plugin-config/SKILL.md)** - 添加用户可配置选项
4. **[调用 AI](../ai/SKILL.md)** - 集成大语言模型能力

---

**使用场景**: 当你第一次接触 AstrBot 插件开发，需要理解最基础的插件结构和代码组织方式时使用此 skill。
