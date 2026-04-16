---
name: "astrbot-misc"
description: "AstrBot 插件开发杂项功能汇总，包括定时任务、权限管理、日志系统、其他实用工具等。当用户需要了解插件开发中的辅助功能和工具类API时调用此 skill。"
---

# 杂项 - AstrBot 插件开发辅助功能

## 📌 概述

本 Skill 汇总 AstrBot 插件开发中不归类于上述主要功能的**辅助工具和实用功能**。

## 🔐 一、权限管理

### 管理员指令过滤

```python
from astrbot.api.event import filter, AstrMessageEvent


class AdminPlugin(Star):
    """管理员专属功能"""
    
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("admin_only")
    async def admin_command(self, event: AstrMessageEvent):
        """仅管理员可用的指令"""
        yield event.plain_result("🔑 这是管理员专属指令！")
    
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("shutdown")
    async def shutdown_bot(self, event: AstrMessageEvent):
        """关闭机器人（仅管理员）"""
        # 执行关闭逻辑
        yield event.plain_result("⚠️ 正在关闭机器人...")
```

### 自定义权限检查（手动实现）

```python
class PermissionPlugin(Star):
    """自定义权限管理"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 从配置加载白名单用户 ID
        self.allowed_users = set()
    
    def check_permission(self, event: AstrMessageEvent) -> bool:
        """检查用户是否有权限"""
        user_id = event.get_sender_id()
        
        # 管理员始终有权限
        if self.is_admin(user_id):
            return True
        
        # 检查白名单
        return user_id in self.allowed_users
    
    def is_admin(self, user_id: str) -> bool:
        """检查是否为管理员"""
        admins = self.context.get_config("admins_id", [])
        return user_id in admins
    
    @filter.command("protected")
    async def protected_action(self, event: AstrMessageEvent):
        """受保护的操作"""
        
        if not self.check_permission(event):
            yield event.plain_result("❌ 权限不足！")
            event.stop_event()  # 阻止后续处理
            return
        
        # 执行受保护的操作
        yield event.plain_result("✅ 操作成功！")
```

## ⏰ 二、定时任务

### 使用 asyncio 实现简单定时任务

```python
import asyncio


class SchedulerPlugin(Star):
    """定时任务示例"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self._tasks = []
    
    async def start_periodic_task(self, interval: int, callback):
        """
        启动周期性任务
        
        Args:
            interval: 间隔时间（秒）
            callback: 异步回调函数
        """
        task = asyncio.create_task(self._periodic_loop(interval, callback))
        self._tasks.append(task)
    
    async def _periodic_loop(self, interval: int, callback):
        """周期性执行循环"""
        while True:
            try:
                await callback()
            except Exception as e:
                logger.error(f"定时任务出错: {e}")
            
            await asyncio.sleep(interval)
    
    async def terminate(self):
        """插件卸载时清理任务"""
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

### 定时消息推送示例

```python
class ReminderPlugin(Star):
    """提醒插件"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 启动每小时检查一次的任务
        asyncio.create_task(self.hourly_check())
    
    async def hourly_check(self):
        """每小时执行的检查任务"""
        while True:
            try:
                # 获取当前时间
                from datetime import datetime
                now = datetime.now()
                
                # 在整点时发送提醒
                if now.minute == 0:
                    await self.send_hourly_reminder()
                
            except Exception as e:
                logger.error(f"提醒任务出错: {e}")
            
            # 每60秒检查一次
            await asyncio.sleep(60)
    
    async def send_hourly_reminder(self):
        """发送整点提醒"""
        from astrbot.api.event import MessageChain
        
        # 构造消息
        chain = MessageChain().message(
            f"⏰ 整点报时 - {datetime.now().strftime('%H:%M')}"
        )
        
        # 发送给所有在线会话（需要自行管理会话列表）
        # 这里仅作示例，实际需要维护会话列表
        pass
```

## 📊 三、数据统计与监控

### 插件使用统计

```python
from collections import defaultdict
import time


class StatsPlugin(Star):
    """使用统计插件"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        self.stats = defaultdict(lambda: {
            "count": 0,
            "last_used": None,
            "users": set()
        })
    
    @filter.command("stats")
    async def show_stats(self, event: AstrMessageEvent):
        """显示插件使用统计"""
        
        report = "📊 插件使用统计\n" + "="*30 + "\n\n"
        
        for cmd, data in sorted(
            self.stats.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        ):
            report += (
                f"📌 /{cmd}\n"
                f"   使用次数: {data['count']}\n"
                f"   使用人数: {len(data['users'])}\n"
                f"   最后使用: {data['last_used'] or '从未'}\n\n"
            )
        
        yield event.plain_result(report)
    
    # 使用装饰器自动记录统计
    def track_usage(self, func):
        """装饰器：记录命令使用情况"""
        async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
            cmd_name = func.__name__
            
            # 更新统计
            self.stats[cmd_name]["count"] += 1
            self.stats[cmd_name]["last_used"] = time.strftime("%Y-%m-%d %H:%M")
            self.stats[cmd_name]["users"].add(event.get_sender_id())
            
            # 调用原函数
            result = await func(self, event, *args, **kwargs)
            return result
        
        return wrapper
```

## 🛠️ 四、实用工具函数

### 字符串处理工具

```python
class StringUtils:
    """字符串处理工具集"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """截断文本并添加省略号"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """转义 Markdown 特殊字符"""
        special_chars = ['*', '_', '`', '~', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def format_list(items: list, separator: str = "\n") -> str:
        """格式化列表为字符串"""
        return separator.join(f"- {item}" for item in items)
```

### 数据验证工具

```python
from typing import Optional


class Validator:
    """数据验证工具"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证 URL 格式"""
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(pattern.match(url))
    
    @staticmethod
    def validate_integer(value: str, min_val: int = None, max_val: int = None) -> Optional[int]:
        """验证整数范围"""
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return None
            if max_val is not None and num > max_val:
                return None
            return num
        except ValueError:
            return None
```

### 消息构建助手

```python
import astrbot.api.message_components as Comp


class MessageBuilder:
    """消息构建助手"""
    
    @staticmethod
    def create_info_card(title: str, items: dict) -> list:
        """
        创建信息卡片
        
        Args:
            title: 标题
            items: 键值对字典
        
        Returns:
            消息链组件列表
        """
        components = [
            Comp.Plain(f"{'='*20}\n"),
            Comp.Plain(f"📋 {title}\n"),
            Comp.Plain(f"{'='*20}\n")
        ]
        
        for key, value in items.items():
            components.append(Comp.Plain(f"{key}: {value}\n"))
        
        return components
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 20) -> str:
        """
        创建进度条
        
        Args:
            current: 当前进度
            total: 总量
            length: 进度条长度（字符数）
        
        Returns:
            进度条字符串
        """
        percent = current / total if total > 0 else 0
        filled = int(length * percent)
        bar = '█' * filled + '░' * (length - filled)
        return f"[{bar}] {percent:.1%}"
```

## 🎨 五、响应式 UI 构建

### 分页显示长内容

```python
class PaginationHelper:
    """分页助手"""
    
    def __init__(self, items: list, items_per_page: int = 5):
        self.items = items
        self.per_page = items_per_page
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    def get_page(self, page_num: int) -> tuple:
        """
        获取指定页的内容
        
        Returns:
            (page_content, current_page, total_pages)
        """
        page_num = max(1, min(page_num, self.total_pages))
        start = (page_num - 1) * self.per_page
        end = start + self.per_page
        
        return self.items[start:end], page_num, self.total_pages
    
    def format_page(self, page_content: list, current_page: int, title: str = "") -> str:
        """格式化页面内容"""
        lines = [f"📄 {title}" if title else "📄 列表"]
        lines.append("-" * 25)
        
        for i, item in enumerate(page_content, 1):
            global_index = (current_page - 1) * self.per_page + i
            lines.append(f"{global_index}. {item}")
        
        lines.append("-" * 25)
        lines.append(f"第 {current_page}/{self.total_pages} 页 | 共 {len(self.items)} 项")
        lines.append("回复 '上一页'/'下一页' 或页码翻页")
        
        return "\n".join(lines)


# 使用示例
@filter.command("list_items")
async def list_items(self, event: AstrMessageEvent):
    """分页显示项目列表"""
    
    items = [f"项目 {i}" for i in range(1, 51)]  # 假设有50个项目
    pagination = PaginationHelper(items, items_per_page=8)
    
    content, page, total = pagination.get_page(1)
    message = pagination.format_page(content, page, "项目列表")
    
    yield event.plain_result(message)
```

## 🔧 六、错误处理最佳实践

### 统一错误处理器

```python
class ErrorHandler:
    """统一错误处理"""
    
    @staticmethod
    def handle_error(error: Exception, notify_user: bool = True) -> str:
        """
        处理错误并返回友好的错误信息
        
        Args:
            error: 异常对象
            notify_user: 是否通知用户
        
        Returns:
            用户友好的错误信息
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # 记录详细日志
        logger.error(f"[{error_type}] {error_msg}", exc_info=True)
        
        # 返回用户友好信息
        if notify_user:
            return f"❌ 操作失败: {error_type}\n请联系管理员查看详细日志"
        return ""
    
    @staticmethod
    async def safe_execute(func, *args, **kwargs):
        """
        安全执行异步函数
        
        Returns:
            (success: bool, result_or_error)
        """
        try:
            result = await func(*args, **kwargs)
            return True, result
        except Exception as e:
            return False, e
```

### 使用装饰器简化错误处理

```python
def error_handler(func):
    """错误处理装饰器"""
    async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
        try:
            return await func(self, event, *args, **kwargs)
        except ValueError as e:
            yield event.plain_result(f"⚠️ 参数错误: {e}")
        except PermissionError:
            yield event.plain_result("❌ 权限不足")
        except ConnectionError:
            yield event.plain_result("🌐 网络连接失败")
        except Exception as e:
            logger.error(f"未预期的错误: {e}", exc_info=True)
            yield event.plain_result("😵 发生未知错误，请稍后重试")
    return wrapper


# 使用
@error_handler
@filter.command("risky_operation")
async def risky_op(self, event: AstrMessageEvent, param: str):
    """可能出错的操作"""
    if not param:
        raise ValueError("参数不能为空")
    
    # ... 业务逻辑
    yield event.plain_result("✅ 操作成功")
```

## 📝 七、日志规范

### 推荐的日志使用方式

```python
from astrbot.api import logger


class LoggingExample(Star):
    """日志使用示例"""
    
    @filter.command("demo_log")
    async def demo_logging(self, event: AstrMessageEvent):
        """演示不同级别的日志"""
        
        user_id = event.get_sender_id()
        
        # DEBUG: 详细调试信息（开发阶段）
        logger.debug(f"用户 {user_id} 触发了 demo_log 指令")
        
        # INFO: 一般性信息（推荐用于正常流程）
        logger.info(f"正在处理用户请求...")
        
        # WARNING: 警告信息（可恢复的问题）
        some_condition = False
        if not some_condition:
            logger.warning(f"条件未满足，使用默认值")
        
        # ERROR: 错误信息（需要关注的问题）
        try:
            result = self.risky_operation()
        except Exception as e:
            logger.error(f"操作失败: {e}")
            yield event.plain_result("操作失败")
            return
        
        yield event.plain_result("✅ 完成")
    
    def risky_operation(self):
        """模拟可能失败的操作"""
        pass
```

### 日志级别说明

| 级别 | 用途 | 示例 |
|------|------|------|
| `DEBUG` | 详细调试信息 | 变量值、函数参数 |
| `INFO` | 正常流程信息 | 用户操作、状态变更 |
| `WARNING` | 可恢复问题 | 使用默认值、降级处理 |
| `ERROR` | 错误但可继续 | 单次请求失败 |
| `CRITICAL` | 严重错误 | 服务不可用 |

## 💡 最佳实践总结

1. **防御性编程**: 假设所有外部输入都可能是无效的
2. **优雅降级**: 功能部分失效时应提供替代方案
3. **详细日志**: 关键节点记录足够的信息便于排查
4. **用户友好**: 错误信息要清晰但不暴露技术细节
5. **资源清理**: 及时释放文件句柄、网络连接等资源
6. **性能考虑**: 避免在热路径上进行重量级操作

---

**使用场景**: 当你需要实现权限控制、定时任务、数据统计、工具函数、错误处理等辅助功能时参考此 skill。
