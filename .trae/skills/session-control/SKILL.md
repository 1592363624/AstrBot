---
name: "astrbot-session-control"
description: "AstrBot 会话控制器详解，实现多轮对话、超时管理、历史记录等功能。当用户需要实现成语接龙、多步骤表单填写、交互式游戏等多轮对话场景时调用此 skill。"
---

# 会话控制器 - AstrBot 多轮对话管理

基于 [AstrBot 官方文档 - 会话控制](https://docs.astrbot.app/dev/star/guides/session-control.html) 的完整指南。

## 🎯 为什么需要会话控制器？

考虑一个**成语接龙**插件的场景：

```
用户: /成语接龙
机器人: 请发送一个成语
用户: 一马当先
机器人: 先见之明
用户: 明察秋毫
...
```

这种需要与机器人进行**多次交互**的场景，就需要会话控制器来维持对话状态。

## 🚀 快速开始

### 导入必要模块

```python
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
```

### 基础示例：成语接龙

```python
from astrbot.api.event import filter, AstrMessageEvent


class IdiomPlugin(Star):
    """成语接龙插件"""
    
    @filter.command("成语接龙")
    async def idiom_chain(self, event: AstrMessageEvent):
        """启动成语接龙游戏"""
        
        try:
            # 发送初始提示
            yield event.plain_result("🎮 成语接龙开始！\n请输入一个四字成语（输入 '退出' 结束游戏）")
            
            # 注册会话控制器
            @session_waiter(timeout=60, record_history_chains=False)
            async def idiom_waiter(controller: SessionController, event: AstrMessageEvent):
                """成语接龙的会话处理器"""
                
                idiom = event.message_str.strip()
                
                # 检查是否退出
                if idiom == "退出":
                    await event.send(event.plain_result("👋 游戏结束，下次再来！"))
                    controller.stop()  # 停止会话
                    return
                
                # 验证成语格式
                if len(idiom) != 4:
                    await event.send(event.plain_result("❌ 必须是四个字的成语哦！"))
                    return  # 不停止会话，等待下一次输入
                
                # 业务逻辑：检查成语接龙规则
                next_idiom = self.get_next_idiom(idiom)
                
                if next_idiom:
                    message_result = event.make_result()
                    message_result.chain = [Comp.Plain(f"✨ {next_idiom}")]
                    await event.send(message_result)
                    
                    # 继续会话，重置超时时间
                    controller.keep(timeout=60, reset_timeout=True)
                else:
                    await event.send(event.plain_result("😅 我想不到合适的成语了，你赢了！"))
                    controller.stop()
            
            # 启动会话等待
            await idiom_waiter(event)
            
        except TimeoutError:
            # 超时处理
            yield event.plain_result("⏰ 时间到了！游戏结束。")
            
        except Exception as e:
            # 错误处理
            logger.error(f"成语接龙出错: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}")
            
        finally:
            # 清理：停止事件传播
            event.stop_event()
    
    def get_next_idiom(self, idiom: str) -> str:
        """根据上一个成语返回下一个（简化版）"""
        # 实际应查询成语数据库
        last_char = idiom[-1]
        idioms_db = {
            "一": "一马当先",
            "先": "先见之明",
            "明": "明察秋毫",
            "秋": "秋高气爽"
        }
        return idioms_db.get(last_char)
```

## 🎛️ SessionController 详解

`SessionController` 是会话控制的核心对象，用于控制会话生命周期：

### 方法列表

```python
class SessionController:
    """会话控制器"""
    
    def keep(self, timeout: float, reset_timeout: bool = False):
        """
        保持会话继续
        
        Args:
            timeout: 必填，新的超时时间（秒）
            reset_timeout: 
                - True: 重置超时时间（timeout 必须 > 0）
                - False: 继续原来的超时时间（新时间 = 剩余时间 + timeout）
        """
        pass
    
    def stop(self):
        """立即结束此会话"""
        pass
    
    def get_history_chains(self) -> list:
        """
        获取历史消息链
        
        Returns:
            List[List[Comp.BaseMessageComponent]]: 历史消息链列表
        """
        pass
```

### keep() 的两种模式

#### 模式 1: 重置超时（reset_timeout=True）

```python
controller.keep(timeout=60, reset_timeout=True)
```
- 每次调用都重新计时 60 秒
- 适合需要固定等待时间的场景

#### 模式 2: 累加超时（reset_timeout=False）

```python
controller.keep(timeout=30, reset_timeout=False)
```
- 在剩余时间基础上增加 30 秒
- 适合灵活延长时间的场景

## 📝 完整示例：问卷调查

```python
class SurveyPlugin(Star):
    """问卷调查插件"""
    
    @filter.command("survey")
    async def start_survey(self, event: AstrMessageEvent):
        """开始问卷调查"""
        
        try:
            yield event.plain_result(
                "📋 欢迎参与问卷调查！\n"
                "我们将问您几个问题，请依次回答。\n"
                "（输入 '跳过' 可跳过当前问题，输入 '退出' 结束调查）"
            )
            
            questions = [
                "1. 您的年龄范围是？\n   A. 18岁以下  B. 18-25岁  C. 25-35岁  D. 35岁以上",
                "2. 您使用我们产品的频率？\n   A. 每天  B. 每周几次  C. 偶尔  D. 很少",
                "3. 您对我们的服务满意吗？（1-5分）",
                "4. 有什么建议或意见吗？"
            ]
            
            answers = []
            current_q = 0
            
            @session_waiter(timeout=120, record_history_chains=True)
            async def survey_waiter(controller: SessionController, event: AstrMessageEvent):
                nonlocal current_q, answers
                
                response = event.message_str.strip()
                
                if response == "退出":
                    await event.send(event.plain_result("感谢您的参与！"))
                    controller.stop()
                    return
                
                if response == "跳过":
                    answers.append("[已跳过]")
                else:
                    answers.append(response)
                
                current_q += 1
                
                if current_q < len(questions):
                    await event.send(event.plain_result(questions[current_q]))
                    controller.keep(timeout=120, reset_timeout=True)
                else:
                    # 问卷结束，汇总结果
                    summary = "📊 调查结果汇总\n" + "="*30 + "\n"
                    for i, (q, a) in enumerate(zip(questions, answers)):
                        summary += f"\n{q.split(chr(10))[0]}\n回答: {a}\n"
                    
                    await event.send(event.plain_result(summary))
                    controller.stop()
            
            # 发送第一个问题
            await event.send(event.plain_result(questions[0]))
            
            # 启动会话
            await survey_waiter(event)
            
        except TimeoutError:
            yield event.plain_result("⏰ 问卷超时，已自动提交已有答案。")
            
        except Exception as e:
            logger.error(f"问卷出错: {e}")
            yield event.plain_result("❌ 发生错误")
            
        finally:
            event.stop_event()
```

## 👥 自定义会话 ID（群组会话）

默认情况下，会话控制器基于 `sender_id`（发送人 ID）识别不同会话。

如果想让**整个群**作为一个会话（例如群内多人协作），需要自定义会话 ID：

```python
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionFilter,
    SessionController,
)


class GroupQuizPlugin(Star):
    """群组答题游戏"""
    
    @filter.command("群答题")
    async def group_quiz(self, event: AstrMessageEvent):
        """启动群组答题游戏"""
        
        try:
            yield event.plain_result(
                "🎯 群答题开始！\n"
                "我会出题，群内任何人都可以回答！\n"
                "（输入 '结束' 停止游戏）"
            )
            
            questions = [
                ("中国的首都是哪里？", "北京"),
                ("1+1=?", "2"),
                ("Python 是解释型语言吗？", "是"),
            ]
            current_q = 0
            score = {}
            
            class GroupSessionFilter(SessionFilter):
                """自定义过滤器：基于群 ID 识别会话"""
                
                def filter(self, event: AstrMessageEvent) -> str:
                    # 如果有群 ID 则使用群 ID，否则使用原始标识
                    return event.get_group_id() or event.unified_msg_origin
            
            @session_waiter(timeout=90, record_history_chains=False)
            async def quiz_waiter(controller: SessionController, event: AstrMessageEvent):
                nonlocal current_q, score
                
                answer = event.message_str.strip()
                user = event.get_sender_name()
                
                if answer == "结束":
                    # 显示最终得分
                    result = "🏆 最终得分\n" + "="*20 + "\n"
                    sorted_scores = sorted(score.items(), key=lambda x: x[1], reverse=True)
                    for i, (name, s) in enumerate(sorted_scores, 1):
                        result += f"{i}. {name}: {s} 分\n"
                    
                    await event.send(event.plain_result(result))
                    controller.stop()
                    return
                
                if current_q < len(questions):
                    question, correct_answer = questions[current_q]
                    
                    if answer.lower() == correct_answer.lower():
                        score[user] = score.get(user, 0) + 10
                        await event.send(
                            event.plain_result(f"✅ {user} 回答正确！+10分")
                        )
                    else:
                        await event.send(
                            event.plain_result(f"❌ {user} 回答错误！正确答案是: {correct_answer}")
                        )
                    
                    current_q += 1
                    
                    if current_q < len(questions):
                        next_question, _ = questions[current_q]
                        await event.send(event.plain_result(f"\n下一题: {next_question}"))
                        controller.keep(timeout=90, reset_timeout=True)
                    else:
                        await event.send(event.plain_result("🎉 所有题目已完成！"))
                        controller.stop()
            
            # 发送第一题
            first_question, _ = questions[0]
            await event.send(event.plain_result(f"第一题: {first_question}"))
            
            # 启动会话（传入自定义过滤器）
            await quiz_waiter(event, session_filter=GroupSessionFilter())
            
        except TimeoutError:
            yield event.plain_result("⏰ 答题超时，游戏结束！")
            
        except Exception as e:
            logger.error(f"群答题出错: {e}")
            yield event.plain_result("❌ 发生错误")
            
        finally:
            event.stop_event()
```

## 🔄 历史消息链（record_history_chains）

当设置 `record_history_chains=True` 时，可以获取用户的所有历史输入：

```python
@session_waiter(timeout=60, record_history_chains=True)
async def chat_waiter(controller: SessionController, event: AstrMessageEvent):
    # 获取历史消息链
    history = controller.get_history_chains()
    
    # history 格式: List[List[BaseMessageComponent]]
    # 每个元素是一轮用户输入的消息链
    
    for i, chain in enumerate(history, 1):
        # 从消息链中提取文本
        texts = [comp.text for comp in chain if hasattr(comp, 'text')]
        print(f"第{i}轮输入: {' '.join(texts)}")
    
    # ... 其他逻辑
```

**适用场景**:
- 需要回顾之前的对话内容
- 实现上下文理解
- 对话摘要和分析

## ⚠️ 重要注意事项

### 1. 必须在 finally 中停止事件

```python
try:
    # ... 会话逻辑
finally:
    event.stop_event()  # 必须调用！
```

这可以防止用户的后续消息触发其他处理器。

### 2. 会话中的消息发送

在会话处理器内部，**不能使用 `yield`**，必须使用 `await event.send()`:

```python
# ❌ 错误
yield event.plain_result("消息")

# ✅ 正确
await event.send(event.plain_result("消息"))
```

### 3. 超时处理

必须捕获 `TimeoutError`:

```python
try:
    await my_waiter(event)
except TimeoutError:
    yield event.plain_result("超时了！")
```

### 4. 嵌套限制

虽然理论上可以嵌套，但不建议过深的嵌套，以免造成混乱。

## 📋 应用场景总结

| 场景 | 示例 | 特点 |
|------|------|------|
| 游戏 | 成语接龙、猜数字 | 多轮交互 |
| 表单收集 | 问卷调查、报名 | 步骤引导 |
| 协作任务 | 群答题、投票 | 多人参与 |
| 向导式操作 | 设置向导、教程 | 引导流程 |
| 状态机 | 订单状态跟踪 | 状态转换 |

## 💡 最佳实践

1. **明确退出机制**: 提供"退出"、"取消"等命令
2. **合理的超时时间**: 根据任务复杂度设置（30-300秒）
3. **友好的错误提示**: 引导用户正确输入
4. **进度反馈**: 让用户知道当前进行到哪一步
5. **日志记录**: 记录关键节点便于调试
6. **资源清理**: 在 stop() 时释放资源

---

**使用场景**: 当你需要实现需要多次用户交互的功能（如游戏、表单填写、向导式操作、多人协作等）时使用此 skill。
