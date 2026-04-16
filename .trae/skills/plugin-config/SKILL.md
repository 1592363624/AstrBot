---
name: "astrbot-plugin-config"
description: "AstrBot 插件配置系统详解，包括 Schema 定义、可视化配置界面、配置读取与保存等。当用户需要为插件添加可配置选项或在 WebUI 中提供配置界面时调用此 skill。"
---

# 插件配置 - AstrBot 配置管理系统

基于 [AstrBot 官方文档 - 插件配置](https://docs.astrbot.app/dev/star/guides/plugin-config.html) 的完整指南。

## 📋 概述

AstrBot 提供"强大"的配置解析和可视化功能，让用户可以在**管理面板（WebUI）**上直接配置插件，而无需修改代码。

## 🔧 第一步：定义配置 Schema

在插件目录下创建 `_conf_schema.json` 文件：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string"
  },
  "enable_feature": {
    "description": "启用高级功能",
    "type": "bool",
    "default": false
  },
  "max_retries": {
    "description": "最大重试次数",
    "type": "int",
    "default": 3,
    "hint": "建议设置为 1-10 之间"
  },
  "sub_config": {
    "description": "嵌套配置测试",
    "type": "object",
    "hint": "这是嵌套配置的提示",
    "items": {
      "name": {
        "description": "名称",
        "type": "string",
        "hint": "请输入名称"
      },
      "timeout": {
        "description": "超时时间（秒）",
        "type": "int",
        "default": 30
      }
    }
  }
}
```

## 📝 Schema 字段详解

### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 配置项类型（见下方支持的类型） |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 配置描述（建议一句话） |
| `hint` | string | 提示信息（显示在问号按钮悬浮窗） |
| `obvious_hint` | bool | 是否醒目显示 hint |
| `default` | any | 默认值 |
| `items` | object | 当 type 为 object 时，定义子 Schema |
| `invisible` | bool | 是否隐藏（默认 false） |
| `options` | list | 下拉列表选项 |
| `editor_mode` | bool | 启用代码编辑器模式（v3.5.10+） |
| `editor_language` | string | 代码编辑器语言（默认 json） |
| `editor_theme` | string | 编辑器主题（vs-light / vs-dark） |
| `_special` | string | 特殊功能选择器（v4.0.0+） |

## 🎨 支持的配置类型

### 1. 基础类型

```json
{
  "string_field": {
    "description": "字符串字段",
    "type": "string",
    "default": ""
  },
  
  "text_field": {
    "description": "多行文本",
    "type": "text",
    "hint": "适合长文本输入"
  },
  
  "int_field": {
    "description": "整数",
    "type": "int",
    "default": 0
  },
  
  "float_field": {
    "description": "浮点数",
    "type": "float",
    "default": 0.0
  },
  
  "bool_field": {
    "description": "布尔值",
    "type": "bool",
    "default": false
  }
}
```

### 2. 选择类型（下拉列表）

```json
{
  "mode": {
    "description": "运行模式",
    "type": "string",
    "options": ["chat", "agent", "workflow"],
    "default": "chat"
  }
}
```

### 3. 对象类型（嵌套配置）

```json
{
  "database": {
    "description": "数据库配置",
    "type": "object",
    "items": {
      "host": {
        "description": "主机地址",
        "type": "string",
        "default": "localhost"
      },
      "port": {
        "description": "端口",
        "type": "int",
        "default": 3306
      },
      "credentials": {
        "description": "认证信息",
        "type": "object",
        "items": {
          "username": {
            "description": "用户名",
            "type": "string"
          },
          "password": {
            "description": "密码",
            "type": "string",
            "invisible": true
          }
        }
      }
    }
  }
}
```

### 4. 列表类型

```json
{
  "keywords": {
    "description": "关键词列表",
    "type": "list",
    "default": []
  }
}
```

### 5. 字典类型（v4.13.0+）

用于可视化编辑 Python dict：

```json
{
  "custom_extra_body": {
    "description": "自定义请求体参数",
    "type": "dict",
    "hint": "用于添加额外参数如 temperature, top_p 等",
    "template_schema": {
      "temperature": {
        "name": "Temperature",
        "description": "温度参数",
        "type": "float",
        "default": 0.6,
        "slider": { "min": 0, "max": 2, "step": 0.1 }
      },
      "top_p": {
        "name": "Top-p",
        "type": "float",
        "default": 1.0,
        "slider": { "min": 0, "max": 1, "step": 0.01 }
      },
      "max_tokens": {
        "name": "Max Tokens",
        "type": "int",
        "default": 8192
      }
    }
  }
}
```

### 6. 文件上传类型（v4.13.0+）

允许用户通过 WebUI 上传文件：

```json
{
  "uploaded_files": {
    "type": "file",
    "description": "上传的文件",
    "default": [],
    "file_types": ["pdf", "docx", "txt"]
  }
}
```

### 7. 模板列表类型（v4.10.4+）

```json
{
  "templates": {
    "type": "template_list",
    "description": "模板列表",
    "templates": {
      "template_1": {
        "name": "模板一",
        "hint": "第一个模板",
        "items": {
          "attr_a": {
            "description": "属性 A",
            "type": "int",
            "default": 10
          },
          "attr_b": {
            "description": "属性 B",
            "type": "bool",
            "default": true
          }
        }
      },
      "template_2": {
        "name": "模板二",
        "items": {
          "attr_c": {
            "description": "属性 C",
            "type": "int",
            "default": 20
          }
        }
      }
    }
  }
}
```

保存后的数据结构：
```json
[
  { "__template_key": "template_1", "attr_a": 10, "attr_b": true },
  { "__template_key": "template_2", "attr_c": 20 }
]
```

## 🎯 _special 特殊选择器（v4.0.0+）

用于快速选择已在 WebUI 配置的数据：

```json
{
  "provider_select": {
    "description": "选择模型提供商",
    "type": "string",
    "_special": "select_provider"
  },
  
  "persona_select": {
    "description": "选择人设",
    "type": "string",
    "_special": "select_persona"
  },
  
  "knowledge_base": {
    "description": "选择知识库",
    "type": "list",
    "default": [],
    "_special": "select_knowledgebase"
  }
}
```

**常用 _special 值**:

| 值 | 返回类型 | 说明 |
|----|----------|------|
| `select_provider` | string | 模型提供商 |
| `select_provider_tts` | string | TTS 提供商 |
| `select_provider_stt` | string | STT 提供商 |
| `select_persona` | string | 人设 |
| `select_knowledgebase` | list | 知识库（支持多选） |

> ⚠️ **注意**: 其他 `_special` 值（如 select_providers, provider_pool 等）属于内部实现，请勿在插件中使用。

## 💻 第二步：在插件中使用配置

AstrBot 会自动解析 `_conf_schema.json` 并传入插件的 `__init__` 方法：

```python
from astrbot.api import AstrBotConfig


class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        """
        插件初始化
        
        Args:
            context: AstrBot 上下文
            config: 插件配置对象（继承自 Dict）
        """
        super().__init__(context)
        self.config = config
        
        # 读取配置
        token = self.config.get("token", "")
        max_retries = self.config.get("max_retries", 3)
        
        print(f"Token: {token}")
        print(f"Max Retries: {max_retries}")

    @filter.command("show_config")
    async def show_config(self, event: AstrMessageEvent):
        """显示当前配置"""
        yield event.plain_result(f"当前配置:\n{dict(self.config)}")
```

**AstrBotConfig 特性**:
- 继承自 `Dict`，拥有字典的所有方法
- 支持 `.get()`, `.keys()`, `.values()` 等
- 可直接像字典一样访问

### 保存配置

```python
# 直接修改并保存
self.config["new_key"] = "new_value"
self.config.save_config()  # 保存到 data/config/<plugin_name>_config.json
```

## 🔄 第三步：配置版本更新管理

当你发布新版本的插件并更新 Schema 时，AstrBot 会**自动处理**配置迁移：

- ✅ 自动为新增的配置项添加默认值
- ✅ 自动移除已删除的配置项
- ✅ 递归检查所有嵌套层级

**无需手动编写迁移代码！**

## 📊 完整示例

### _conf_schema.json

```json
{
  "api_token": {
    "description": "API Token",
    "type": "string",
    "obvious_hint": true,
    "hint": "从服务提供商获取的 API 密钥"
  },
  "mode": {
    "description": "运行模式",
    "type": "string",
    "options": ["simple", "advanced", "expert"],
    "default": "simple"
  },
  "settings": {
    "description": "详细设置",
    "type": "object",
    "items": {
      "timeout": {
        "description": "请求超时（秒）",
        "type": "int",
        "default": 30,
        "hint": "建议 10-60 秒"
      },
      "retry_count": {
        "description": "重试次数",
        "type": "int",
        "default": 3
      },
      "enable_cache": {
        "description": "启用缓存",
        "type": "bool",
        "default": true
      }
    }
  },
  "provider": {
    "description": "AI 模型提供商",
    "type": "string",
    "_special": "select_provider"
  }
}
```

### main.py

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api import AstrBotConfig


class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        self.token = config.get("api_token", "")
        self.mode = config.get("mode", "simple")
        
        settings = config.get("settings", {})
        self.timeout = settings.get("timeout", 30)
        self.retry_count = settings.get("retry_count", 3)
        
        logger.info(f"插件初始化完成 - Mode: {self.mode}")

    @filter.command("config_info")
    async def show_config_info(self, event: AstrMessageEvent):
        """显示当前配置信息"""
        info = f"""📋 当前配置：
        
🔑 Token: {'*' * len(self.token) if self.token else '未设置'}
⚙️ 模式: {self.mode}
⏱️ 超时: {self.timeout}s
🔄 重试: {self.retry_count}次
        
完整配置:
{dict(self.config)}
"""
        yield event.plain_result(info)

    @filter.command("update_timeout")
    async def update_timeout(self, event: AstrMessageEvent, timeout: int):
        """动态更新超时设置"""
        if timeout < 1 or timeout > 300:
            yield event.plain_result("❌ 超时时间应在 1-300 秒之间")
            return
        
        self.config["settings"]["timeout"] = timeout
        self.config.save_config()
        
        self.timeout = timeout
        yield event.plain_result(f"✅ 已更新超时时间为 {timeout} 秒")
```

## 💡 最佳实践

1. **合理组织配置**: 使用嵌套对象对相关配置分组
2. **提供默认值**: 让开箱即用体验更好
3. **编写清晰的 description 和 hint**: 帮助用户理解每个配置项
4. **使用 options 限制输入**: 对于有限选项使用下拉列表
5. **敏感信息标记 invisible**: 如密码、Token 等
6. **利用 _special**: 减少用户手动输入，提高易用性
7. **测试配置迁移**: 发布新版时验证旧配置兼容性

---

**使用场景**: 当你的插件需要让用户自定义行为参数、连接外部 API、或者需要在 WebUI 中提供友好的配置界面时使用此 skill。
