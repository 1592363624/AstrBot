---
name: "astrbot-storage"
description: "AstrBot 插件数据持久化方案，包括 KV 存储、大文件存储规范等。当用户需要在插件中保存配置信息、临时数据或大文件时调用此 skill。"
---

# 存储 - AstrBot 插件数据持久化

基于 [AstrBot 官方文档 - 插件存储](https://docs.astrbot.app/dev/star/guides/storage.html) 的完整指南。

## 📦 概述

AstrBot 为插件提供多种数据持久化方案：
1. **简单 KV 存储** (v4.9.2+) - 适合轻量级数据
2. **大文件存储规范** - 适合文件、图片等大数据
3. **插件配置系统** - 适合用户可配置项（见 [插件配置 Skill](../plugin-config/SKILL.md)）

## 🔑 一、简单 KV 存储（推荐）

> ⚠️ **要求**: AstrBot 版本 >= 4.9.2

### 特点
- ✅ 基于插件维度隔离（每个插件独立空间）
- ✅ 简单易用的 Key-Value 接口
- ✅ 自动持久化，无需手动管理文件
- ✅ 适合存储配置、状态、缓存等轻量数据

### API 方法

```python
class Main(Star):
    
    @filter.command("storage_demo")
    async def storage_demo(self, event: AstrMessageEvent):
        """演示 KV 存储用法"""
        
        # 1. 写入数据
        await self.put_kv_data("greeted", True)
        await self.put_kv_data("user_name", "Alice")
        await self.put_kv_data("count", 42)
        
        # 2. 读取数据（带默认值）
        greeted = await self.get_kv_data("greeted", False)
        name = await self.get_kv_data("user_name", "陌生人")
        count = await self.get_kv_data("count", 0)
        
        # 3. 删除数据
        await self.delete_kv_data("temporary_data")
        
        yield event.plain_result(
            f"已问候: {greeted}\n"
            f"用户名: {name}\n"
            f"计数: {count}"
        )
```

### 支持的数据类型

KV 存储支持 Python 基本数据类型：

```python
# 字符串
await self.put_kv_data("token", "abc123")

# 整数/浮点数
await self.put_kv_data("score", 95.5)
await self.put_kv_data("level", 10)

# 布尔值
await self.put_kv_data("enabled", True)

# 列表
await self.put_kv_data("history", ["msg1", "msg2", "msg3"])

# 字典
await self.put_kv_data("config", {
    "theme": "dark",
    "language": "zh-CN"
})

# None（删除时使用）
```

### 实际应用示例：用户计数器

```python
class CounterPlugin(Star):
    """用户访问计数器"""
    
    @filter.command("visit")
    async def visit(self, event: AstrMessageEvent):
        """记录并显示访问次数"""
        
        user_id = event.get_sender_id()
        
        # 获取当前计数
        count = await self.get_kv_data(f"visit_count_{user_id}", 0)
        
        # 计数 +1
        count += 1
        await self.put_kv_data(f"visit_count_{user_id}", count)
        
        yield event.plain_result(
            f"🎉 欢迎回来！\n"
            f"这是你的第 {count} 次访问。"
        )
    
    @filter.command("reset_visit")
    async def reset_visit(self, event: AstrMessageEvent):
        """重置访问计数"""
        
        user_id = event.get_sender_id()
        await self.delete_kv_data(f"visit_count_{user_id}")
        
        yield event.plain_result("✅ 计数器已重置！")
```

### 实际应用示例：简单缓存

```python
class CachePlugin(Star):
    """API 结果缓存"""
    
    async def get_with_cache(self, key: str, fetch_func, ttl: int = 3600):
        """
        带缓存的获取数据
        
        Args:
            key: 缓存键
            fetch_func: 数据获取函数（异步）
            ttl: 缓存有效期（秒）
        """
        import time
        
        # 尝试从缓存读取
        cached = await self.get_kv_data(key, None)
        
        if cached:
            data, timestamp = cached
            
            # 检查是否过期
            if time.time() - timestamp < ttl:
                return data
        
        # 缓存未命中或已过期，重新获取
        data = await fetch_func()
        
        # 写入缓存
        await self.put_kv_data(key, (data, time.time()))
        
        return data
    
    @filter.command("weather")
    async def weather(self, event: AstrMessageEvent, city: str):
        """查询天气（带缓存）"""
        
        async def fetch_weather():
            # 实际应调用天气 API
            return f"{city}: 晴朗, 25°C"
        
        weather_info = await self.get_with_cache(
            f"weather_{city}",
            fetch_weather,
            ttl=1800  # 缓存30分钟
        )
        
        yield event.plain_result(weather_info)
```

## 📁 二、大文件存储规范

当需要存储大文件（图片、视频、数据库文件等）时，请遵循以下规范：

### 存储位置

```
data/plugin_data/{plugin_name}/
```

### 获取插件数据目录

```python
from pathlib import Path
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class FilePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 获取插件专属数据目录
        self.data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
```

**注意**: `self.name` 在 v4.9.2+ 可用，低版本需手动指定插件名称。

### 文件操作示例

```python
import json
import aiofiles
from pathlib import Path


class DataPlugin(Star):
    """大文件存储示例"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        self.data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @filter.command("save_file")
    async def save_file(self, event: AstrMessageEvent):
        """保存文件到插件数据目录"""
        
        file_path = self.data_dir / "data.json"
        
        data = {
            "timestamp": "2024-01-01",
            "items": ["item1", "item2"]
        }
        
        # 异步写入文件
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        
        yield event.plain_result(f"✅ 文件已保存到: {file_path}")
    
    @filter.command("load_file")
    async def load_file(self, event: AstrMessageEvent):
        """从插件数据目录读取文件"""
        
        file_path = self.data_dir / "data.json"
        
        if not file_path.exists():
            yield event.plain_result("❌ 文件不存在")
            return
        
        # 异步读取文件
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
        
        yield event.plain_result(f"📄 文件内容:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    
    @filter.command("save_image")
    async def save_image(self, event: AstrMessageEvent, url: str):
        """下载并保存图片"""
        
        import aiohttp
        
        image_path = self.data_dir / f"image_{int(time.time())}.jpg"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    
                    async with aiofiles.open(image_path, 'wb') as f:
                        await f.write(data)
                    
                    yield event.image_result(str(image_path))
                else:
                    yield event.plain_result("❌ 下载失败")
```

## 📊 三、存储方案选择指南

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 用户偏好设置 | **KV 存储** + 插件配置 | 小量结构化数据 |
| 临时状态/缓存 | **KV 存储** | 简单键值对 |
| 访问计数/统计 | **KV 存储** | 数字累加 |
| 日志记录 | **大文件** | 文本追加写入 |
| 图片/媒体 | **大文件** | 二进制数据 |
| 数据库文件 | **大文件** | SQLite 等 |
| 用户上传文件 | **大文件** | 文件上传场景 |

## ⚠️ 重要注意事项

### 1. 数据目录权限

确保 `data/plugin_data/{plugin_name}/` 目录有读写权限。

### 2. 文件清理

定期清理不再需要的文件，避免占用过多磁盘空间：

```python
@filter.command("cleanup")
async def cleanup(self, event: AstrMessageEvent):
    """清理过期文件"""
    import time
    
    max_age = 7 * 24 * 3600  # 7天
    
    for file_path in self.data_dir.iterdir():
        if file_path.is_file():
            age = time.time() - file_path.stat().st_mtime
            if age > max_age:
                file_path.unlink()
    
    yield event.plain_result("✅ 已清理过期文件")
```

### 3. 并发安全

对于高并发场景，注意文件操作的原子性：

```python
import asyncio

async def safe_write(self, path: Path, data: str):
    """安全的文件写入（先写临时文件再重命名）"""
    temp_path = path.with_suffix('.tmp')
    
    async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
        await f.write(data)
    
    # 原子重命名
    temp_path.rename(path)
```

### 4. 备份重要数据

对于关键数据，建议定期备份：

```python
@filter.command("backup")
async def backup(self, event: AstrMessageEvent):
    """备份插件数据"""
    
    import shutil
    from datetime import datetime
    
    backup_dir = self.data_dir.parent / f"{self.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    shutil.copytree(self.data_dir, backup_dir)
    
    yield event.plain_result(f"✅ 已备份到: {backup_dir}")
```

## 💡 最佳实践

1. **优先使用 KV 存储**: 对于简单数据，KV 存储更方便
2. **合理组织目录**: 大文件按类型分子目录（images/, logs/, db/）
3. **及时清理**: 避免无限增长占用磁盘
4. **错误处理**: 处理文件不存在、权限不足等情况
5. **使用异步 IO**: 使用 aiofiles 等异步库避免阻塞

---

**使用场景**: 当你需要在插件中持久化保存数据（如用户配置、缓存、统计信息、文件等），或者需要管理插件的大文件存储时使用此 skill。
