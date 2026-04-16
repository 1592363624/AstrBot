---
name: "astrbot-ai-integration"
description: "AstrBot AI 能力集成指南，包括 LLM 调用、Tool 定义、Agent 系统、多智能体协作、对话管理等。当用户需要在插件中集成大语言模型能力或实现 AI Agent 时调用此 skill。"
---

# 调用 AI - AstrBot LLM 与 Agent 集成

基于 [AstrBot 官方文档 - AI](https://docs.astrbot.app/dev/star/guides/ai.html) 的完整指南。

## 🤖 概述

AstrBot 内置了对多种大语言模型（LLM）提供商的支持，并提供统一接口。你可以轻松地在插件中调用 LLM 服务，实现自己的智能 Agent。

> 💡 **推荐**: v4.5.7+ 版本后使用了新的调用方式，更加简洁且支持更多功能。

## 📡 第一步：获取当前会话的聊天模型 ID

```python
umo = event.unified_msg_origin
provider_id = await self.context.get_current_chat_provider_id(umo=umo)
```

**返回值**: 当前会话使用的聊天模型 Provider ID（字符串）

## 🗣️ 第二步：调用大语言模型（基础用法）

### 简单文本生成

```python
@filter.command("ask")
async def ask_ai(self, event: AstrMessageEvent, question: str):
    """向 AI 提问"""
    
    # 获取当前模型的 ID
    umo = event.unified_msg_origin
    provider_id = await self.context.get_current_chat_provider_id(umo=umo)
    
    # 调用 LLM
    llm_resp = await self.context.llm_generate(
        chat_provider_id=provider_id,
        prompt=f"请回答以下问题：{question}"
    )
    
    # 获取返回的文本
    answer = llm_resp.completion_text
    
    yield event.plain_result(answer)
```

### 使用上下文（多轮对话）

```python
from astrbot.core.agent.message import UserMessageSegment, TextPart


@filter.command("chat")
async def chat_with_context(self, event: AstrMessageEvent, message: str):
    """带上下文的对话"""
    
    provider_id = await self.context.get_current_chat_provider_id(
        event.unified_msg_origin
    )
    
    # 构建用户消息
    user_msg = UserMessageSegment(content=[TextPart(text=message)])
    
    # 调用 LLM（可以传入历史上下文）
    llm_resp = await self.context.llm_generate(
        chat_provider_id=provider_id,
        contexts=[user_msg],  # 传入上下文
        prompt="你是一个有帮助的助手。"  # 可选的系统提示
    )
    
    yield event.plain_result(llm_resp.completion_text)
```

## 🔧 第三步：定义 Tool（工具）

Tool 是让大语言模型能够调用外部能力的关键机制。

### 方式一：使用 @dataclass 定义 Tool

```python
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class BilibiliTool(FunctionTool[AstrAgentContext]):
    """
    Bilibili 视频搜索工具
    
    让 AI 能够搜索 Bilibili 上的视频
    """
    name: str = "bilibili_videos"       # 工具名称
    description: str = "搜索 Bilibili 视频"  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["keywords"]
        }
    )

    async def call(
        self, 
        context: ContextWrapper[AstrAgentContext], 
        **kwargs
    ) -> ToolExecResult:
        """执行工具调用"""
        keywords = kwargs.get("keywords", "")
        
        # 这里实现实际的搜索逻辑
        videos = self.search_bilibili(keywords)
        
        return f"找到以下视频：\n" + "\n".join(videos)
    
    def search_bilibili(self, keywords: str) -> list:
        """模拟搜索 Bilibili（实际应调用 API）"""
        return [
            f"1. 视频标题：如何使用AstrBot\n   链接：https://bilibili.com/video/xxx",
            f"2. 视频标题：AstrBot 教程\n   链接：https://bilibili.com/video/yyy"
        ]
```

### 方式二：使用装饰器注册 Tool（更简洁）

```python
@filter.llm_tool(name="get_weather")
async def get_weather(self, event: AstrMessageEvent, location: str) -> MessageEventResult:
    """
    获取天气信息
    
    Args:
        location(string): 要查询天气的城市名称
    """
    weather_data = self.fetch_weather_from_api(location)
    yield event.plain_result(f"{location} 的天气：{weather_data}")
```

**装饰器方式的优势**:
- ✅ 更简洁，无需定义类
- ✅ 自动解析函数注释作为工具描述
- ✅ 参数类型和描述直接写在 Docstring 中

**支持的参数类型**: `string`, `number`, `object`, `boolean`, `array`
> v4.5.7+ 支持 array 子类型，例如 `array[string]`

## 🤖 第四步：注册 Tool 到 AstrBot

如果希望 Tool 在用户对话时自动被 AI 调用，需在插件的 `__init__` 中注册：

```python
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 注册 Tool 到 AstrBot（v4.5.1+ 推荐方式）
        self.context.add_llm_tools(
            BilibiliTool(),
            WeatherTool(),
            SecondTool()
        )
        
        # 旧版方式（< v4.5.1）
        # tool_mgr = self.context.provider_manager.llm_tools
        # tool_mgr.func_list.append(BilibiliTool())
```

## 🧠 第五步：调用 Agent（智能体）

Agent = System Prompt + Tools + LLM，可实现复杂的智能行为。

### 基本 Agent 调用

```python
@filter.command("search_video")
async def search_video(self, event: AstrMessageEvent, query: str):
    """使用 Agent 搜索视频"""
    
    provider_id = await self.context.get_current_chat_provider_id(
        event.unified_msg_origin
    )
    
    # 调用 tool_loop_agent
    llm_resp = await self.context.tool_loop_agent(
        event=event,
        chat_provider_id=provider_id,
        prompt=f"搜索一下 bilibili 上关于 '{query}' 的相关视频。",
        tools=ToolSet([BilibiliTool()]),  # 传入工具集
        max_steps=30,                      # 最大执行步骤数
        tool_call_timeout=120,             # 工具调用超时时间（秒）
    )
    
    yield event.plain_result(llm_resp.completion_text)
```

**tool_loop_agent() 工作原理**:
1. 将 prompt 发送给 LLM
2. LLM 决定是否调用工具
3. 如果调用工具，执行工具并将结果返回给 LLM
4. 循环步骤 2-3，直到 LLM 不再调用工具或达到最大步骤数
5. 返回最终结果

## 🌐 第六步：Multi-Agent（多智能体系统）

将复杂应用分解为多个专业化智能体协同工作。

### 定义 Tools

```python
@dataclass
class AssignAgentTool(FunctionTool[AstrAgentContext]):
    """主 Agent 用于决定分配任务给哪个子 Agent"""
    
    name: str = "assign_agent"
    description: str = "根据查询内容分配给合适的子 Agent 处理"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要处理的查询内容"
                }
            },
            "required": ["query"]
        }
    )

    async def call(
        self, 
        context: ContextWrapper[AstrAgentContext], 
        **kwargs
    ) -> ToolExecResult:
        query = kwargs["query"]
        # 根据查询内容决定分配给哪个 Agent
        if "天气" in query or "weather" in query.lower():
            return "应该分配给 subagent1（天气查询 Agent）"
        else:
            return "应该分配给 subagent2（通用问答 Agent）"


@dataclass
class WeatherTool(FunctionTool[AstrAgentContext]):
    """子 Agent 1 使用的天气查询工具"""
    
    name: str = "weather"
    description: str = "获取指定城市的天气信息"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    )

    async def call(
        self, 
        context: ContextWrapper[AstrAgentContext], 
        **kwargs
    ) -> ToolExecResult:
        city = kwargs["city"]
        return f"{city} 当前天气：晴朗，温度 25°C"

@dataclass
class SubAgent1(FunctionTool[AstrAgentContext]):
    """天气查询子 Agent"""
    
    name: str = "subagent1_weather"
    description: str = "专门处理天气相关的查询"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "天气查询内容"
                }
            },
            "required": ["query"]
        }
    )

    async def call(
        self, 
        context: ContextWrapper[AstrAgentContext], 
        **kwargs
    ) -> ToolExecResult:
        ctx = context.context.context
        event = context.context.event
        
        # 子 Agent 内部也可以调用 tool_loop_agent
        llm_resp = await ctx.tool_loop_agent(
            event=event,
            chat_provider_id=await ctx.get_current_chat_provider_id(
                event.unified_msg_origin
            ),
            prompt=kwargs["query"],
            tools=ToolSet([WeatherTool()]),
            max_steps=30
        )
        
        return llm_resp.completion_text
```

### 调用 Multi-Agent

```python
@filter.command("multi_agent_test")
async def multi_agent_test(self, event: AstrMessageEvent, question: str):
    """测试多智能体系统"""
    
    umo = event.unified_msg_origin
    prov_id = await self.context.get_current_chat_provider_id(umo)
    
    llm_resp = await self.context.tool_loop_agent(
        event=event,
        chat_provider_id=prov_id,
        prompt=question,
        system_prompt=(
            "你是主协调 Agent。你的任务是根据用户查询的内容，"
            "使用 assign_agent 工具决定将任务分配给合适的子 Agent。"
        ),
        tools=ToolSet([
            SubAgent1(), 
            SubAgent2(), 
            AssignAgentTool()
        ]),
        max_steps=30
    )
    
    yield event.plain_result(llm_resp.completion_text)
```

## 💬 第七步：对话管理器

### 获取当前对话信息

```python
from astrbot.core.conversation_mgr import Conversation


# 获取对话管理器
conv_mgr = self.context.conversation_manager

# 获取当前对话 ID
curr_cid = await conv_mgr.get_curr_conversation_id(
    event.unified_msg_origin
)

# 获取完整的对话对象
conversation = await conv_mgr.get_conversation(
    event.unified_msg_origin, 
    curr_cid
)

# Conversation 对象属性
print(conversation.cid)           # 对话 ID（UUID）
print(conversation.history)       # 对话历史
print(conversation.title)         # 对话标题
print(conversation.persona_id)    # 绑定的人设 ID
print(conversation.created_at)    # 创建时间
```

### 操作对话

```python
# 新建对话
new_cid = await conv_mgr.new_conversation(
    unified_msg_origin=event.unified_msg_origin,
    title="新对话",
    persona_id="my_persona"
)

# 切换对话
await conv_mgr.switch_conversation(
    event.unified_msg_origin,
    target_conversation_id
)

# 删除对话
await conv_mgr.delete_conversation(
    event.unified_msg_origin,
    conversation_id=None  # None 表示删除当前对话
)

# 更新对话
await conv_mgr.update_conversation(
    unified_msg_origin=event.unified_msg_origin,
    conversation_id=None,  # None 表示当前对话
    history=new_history,
    title="新标题"
)

# 获取所有对话列表
conversations = await conv_mgr.get_conversations(
    unified_msg_origin=event.unified_msg_origin
)
```

### 手动添加对话记录

```python
from astrbot.core.agent.message import (
    AssistantMessageSegment,
    UserMessageSegment,
    TextPart,
)


curr_cid = await conv_mgr.get_curr_conversation_id(
    event.unified_msg_origin
)

# 构建用户消息
user_msg = UserMessageSegment(content=[TextPart(text="你好")])

# 调用 LLM
llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id,
    contexts=[user_msg]
)

# 将对话记录添加到历史
await conv_mgr.add_message_pair(
    cid=curr_cid,
    user_message=user_msg,
    assistant_message=AssistantMessageSegment(
        content=[TextPart(text=llm_resp.completion_text)]
    ),
)
```

## 🎭 第八步：人设（Persona）管理

```python
# 获取人设管理器
persona_mgr = self.context.persona_manager

# 获取指定人设
persona = persona_mgr.get_persona("my_persona_id")

# 获取所有人设
all_personas = persona_mgr.get_all_personas()

# 创建新人设
new_persona = persona_mgr.create_persona(
    persona_id="helpful_assistant",
    system_prompt="你是一个有帮助的助手。",
    begin_dialogs=["你好！", "有什么我可以帮您的吗？"],
    tools=None  # None 表示可以使用所有工具
)

# 更新人设
updated_persona = persona_mgr.update_persona(
    persona_id="helpful_assistant",
    system_prompt="你是一个专业的技术顾问。",
)

# 删除人设
persona_mgr.delete_persona("old_persona_id")

# 获取默认人设（v3 兼容格式）
default_persona = persona_mgr.get_default_persona_v3(
    umo=event.unified_msg_origin
)
```

## 📊 功能速查表

| 功能 | 方法 | 版本要求 |
|------|------|----------|
| 获取 Provider ID | `get_current_chat_provider_id()` | v4.5.7+ |
| 调用 LLM | `llm_generate()` | v4.5.7+ |
| 调用 Agent | `tool_loop_agent()` | v4.5.7+ |
| 注册 Tool | `add_llm_tools()` | v4.5.1+ |
| 装饰器 Tool | `@filter.llm_tool()` | 所有版本 |
| 对话管理 | `conversation_manager` | v4.5.7+ |
| 人设管理 | `persona_manager` | v4.x |

## 💡 最佳实践

1. **Tool 设计**: 保持 Tool 功能单一、职责清晰
2. **参数验证**: 在 Tool 的 call 方法中进行参数校验
3. **错误处理**: 捕获异常并返回友好的错误信息
4. **性能考虑**: 设置合理的 max_steps 和 timeout
5. **日志记录**: 记录 Agent 执行过程便于调试
6. **权限控制**: 敏感操作加上管理员权限检查

---

**使用场景**: 当你需要在插件中集成 AI 能力，实现智能对话、自动化任务处理、多步骤问题解决等功能时使用此 skill。
