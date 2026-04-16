---
name: "astrbot-config-file"
description: "AstrBot 主配置文件详解，包括所有配置项说明、平台设置、Provider 配置、Dashboard 设置等。当用户需要理解或修改 AstrBot 核心配置文件 cmd_config.json 时调用此 skill。"
---

# AstrBot 配置文件 - 完整配置指南

基于 [AstrBot 官方文档 - 配置文件](https://docs.astrbot.app/dev/astrbot-config.html) 的完整指南。

## 📍 配置文件位置

**主配置文件**: `data/cmd_config.json`

> 从 AstrBot v4.0.0 起，引入了多配置文件概念：
> - `data/cmd_config.json`: 默认配置（主配置）
> - `data/config/abconf_*.json`: 其他配置文件（通过 WebUI 创建）

## 📋 完整配置模板

```jsonc
{
  "config_version": 2,
  
  // ===== 平台通用设置 =====
  "platform_settings": {
    "unique_session": false,
    "rate_limit": {
      "time": 60,
      "count": 30,
      "strategy": "stall"  // stall | discard
    },
    "reply_prefix": "",
    "forward_threshold": 1500,
    "enable_id_white_list": true,
    "id_whitelist": [],
    "id_whitelist_log": true,
    "wl_ignore_admin_on_group": true,
    "wl_ignore_admin_on_friend": true,
    "reply_with_mention": false,
    "reply_with_quote": false,
    "path_mapping": [],
    "segmented_reply": {
      "enable": false,
      "only_llm_result": true,
      "interval_method": "random",
      "interval": "1.5,3.5",
      "log_base": 2.6,
      "words_count_threshold": 150,
      "regex": ".*?[。？！~…]+|.+$",
      "content_cleanup_rule": "",
    },
    "no_permission_reply": true,
    "empty_mention_waiting": true,
    "empty_mention_waiting_need_reply": true,
    "friend_message_needs_wake_prefix": false,
    "ignore_bot_self_message": false,
    "ignore_at_all": false,
  },

  // ===== LLM Provider 配置 =====
  "provider": [],

  // ===== Provider 高级设置 =====
  "provider_settings": {
    "enable": true,
    "default_provider_id": "",
    "default_image_caption_provider_id": "",
    "image_caption_prompt": "Please describe the image using Chinese.",
    "provider_pool": ["*"],
    "wake_prefix": "",
    "web_search": false,
    "websearch_provider": "tavily",
    "websearch_tavily_key": [],
    "websearch_bocha_key": [],
    "websearch_brave_key": [],
    "web_search_link": false,
    "display_reasoning_text": false,
    "identifier": false,
    "group_name_display": false,
    "datetime_system_prompt": true,
    "default_personality": "default",
    "persona_pool": ["*"],
    "prompt_prefix": "{{prompt}}",
    "max_context_length": -1,
    "dequeue_context_length": 1,
    "streaming_response": false,
    "show_tool_use_status": false,
    "streaming_segmented": false,
    "max_agent_step": 30,
    "tool_call_timeout": 120,
  },

  // ===== STT（语音转文字）设置 =====
  "provider_stt_settings": {
    "enable": false,
    "provider_id": "",
  },

  // ===== TTS（文字转语音）设置 =====
  "provider_tts_settings": {
    "enable": false,
    "provider_id": "",
    "dual_output": false,
    "use_file_service": false,
  },

  // ===== LTM（长期记忆）设置 =====
  "provider_ltm_settings": {
    "group_icl_enable": false,
    "group_message_max_cnt": 300,
    "image_caption": false,
    "active_reply": {
      "enable": false,
      "method": "possibility_reply",
      "possibility_reply": 0.1,
      "whitelist": [],
    },
  },

  // ===== 内容安全 =====
  "content_safety": {
    "also_use_in_response": false,
    "internal_keywords": {
      "enable": true,
      "extra_keywords": []
    },
    "baidu_aip": {
      "enable": false,
      "app_id": "",
      "api_key": "",
      "secret_key": "",
    },
  },

  // ===== 管理员设置 =====
  "admins_id": ["astrbot"],

  // ===== 文转图设置 =====
  "t2i": false,
  "t2i_word_threshold": 150,
  "t2i_strategy": "remote",
  "t2i_endpoint": "",
  "t2i_use_file_service": false,
  "t2i_active_template": "base",

  // ===== 网络设置 =====
  "http_proxy": "",
  "no_proxy": ["localhost", "127.0.0.1", "::1"],

  // ===== Dashboard（WebUI）设置 =====
  "dashboard": {
    "enable": true,
    "username": "astrbot",
    "password": "77b90590a8945a7d36c963981a307dc9",
    "jwt_secret": "",
    "host": "0.0.0.0",
    "port": 6185,
  },

  // ===== 平台适配器配置 =====
  "platform": [],

  // ===== 平台特定设置 =====
  "platform_specific": {
    "lark": {
      "pre_ack_emoji": {
        "enable": false,
        "emojis": ["Typing"]
      },
    },
    "telegram": {
      "pre_ack_emoji": {
        "enable": false,
        "emojis": ["✍️"]
      },
    },
    "discord": {
      "pre_ack_emoji": {
        "enable": false,
        "emojis": ["🤔"]
      },
    },
  },

  // ===== 基础设置 =====
  "wake_prefix": ["/"],
  "log_level": "INFO",
  "trace_enable": false,
  "pip_install_arg": "",
  "pypi_index_url": "https://mirrors.aliyun.com/pypi/simple/",
  "persona": [],  // 已废弃
  "timezone": "Asia/Shanghai",
  "callback_api_base": "",
  "default_kb_collection": "",
  "plugin_set": ["*"],
}
```

## 🔧 核心配置项详解

### 1. platform_settings（平台通用设置）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `unique_session` | bool | false | 是否启用会话隔离（每人独立会话） |
| `rate_limit.time` | int | 60 | 限流时间窗口（秒） |
| `rate_limit.count` | int | 30 | 时间窗口内最大消息数 |
| `rate_limit.strategy` | string | "stall" | 限流策略：stall（排队）/ discard（丢弃） |
| `forward_threshold` | int | 1500 | 消息超过此字数时转为转发 |
| `enable_id_white_list` | bool | true | 是否启用白名单 |
| `reply_with_mention` | bool | false | 回复时是否 @发送者 |
| `segmented_reply.enable` | bool | false | 是否分段发送长消息 |

### 2. provider_settings（LLM Provider 设置）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_provider_id` | string | "" | 默认使用的 Provider ID |
| `wake_prefix` | string | "" | 触发 AI 对话的前缀 |
| `web_search` | bool | false | 是否启用联网搜索 |
| `streaming_response` | bool | false | 是否启用流式输出 |
| `max_agent_step` | int | 30 | Agent 最大执行步骤 |
| `tool_call_timeout` | int | 120 | 工具调用超时（秒） |
| `max_context_length` | int | -1 | 最大上下文长度（-1 为无限制） |

### 3. dashboard（WebUI 设置）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable` | bool | true | 是否启用 WebUI |
| `host` | string | "0.0.0.0" | 监听地址 |
| `port` | int | 6185 | 监听端口 |
| `username` | string | "astrbot" | 用户名 |
| `password` | string | (MD5加密) | 密码（MD5 加密存储） |

**修改密码方法**:
1. 在线 MD5 加密工具生成新密码的 MD5
2. 修改 `cmd_config.json` 中的 password 字段
3. 重启 AstrBot

### 4. t2i（文转图设置）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `t2i` | bool | false | 是否启用文转图 |
| `t2i_word_threshold` | int | 150 | 超过此字数的消息转为图片 |
| `t2i_strategy` | string | "remote" | 渲染策略：remote（远程）/ local（本地） |
| `t2i_endpoint` | string | "" | 自定义文转图服务地址 |

## 🌐 Platform 配置示例

### OneBot v11 (QQ)

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

### Telegram

```json
{
  "platform": [
    {
      "type": "telegram",
      "enable": true,
      "telegram_token": "YOUR_BOT_TOKEN"
    }
  ]
}
```

### Discord

```json
{
  "platform": [
    {
      "type": "discord",
      "enable": true,
      "discord_bot_token": "YOUR_BOT_TOKEN"
    }
  ]
}
```

## 🤖 Provider 配置示例

### OpenAI 兼容接口

```json
{
  "provider": [
    {
      "name": "openai_compatible",
      "type": "openai_chat",
      "enable": true,
      "api_key": "sk-xxxxxxxx",
      "api_base": "https://api.openai.com/v1",
      "model": "gpt-4o",
      "max_tokens": 4096
    }
  ]
}
```

### 国内大模型（如通义千问、文心一言等）

```json
{
  "provider": [
    {
      "name": "qwen",
      "type": "openai_chat",
      "enable": true,
      "api_key": "sk-xxxxxxxx",
      "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-max",
      "max_tokens": 2048
    }
  ]
}
```

## ⚠️ 配置修改注意事项

### 1. JSON 格式要求

- 确保有效的 JSON 格式（注意逗号、引号）
- 注释使用 `//` 或 `/* */`（JSONC 格式）
- 字符串必须使用双引号

### 2. 修改后生效

大部分配置修改后需要**重启 AstrBot** 才能生效：

```bash
# Linux/Mac
sudo systemctl restart astrbot

# Windows
# 直接关闭重新启动程序

# Docker
docker restart astrbot-container
```

### 3. 备份配置

修改前务必备份：

```bash
cp data/cmd_config.json data/cmd_config.json.backup.$(date +%Y%m%d_%H%M%S)
```

### 4. 通过 WebUI 修改（推荐）

对于大多数配置，建议通过 WebUI 的可视化界面修改：
- 进入 **配置** 页面
- 修改需要的选项
- 点击右下角 **保存** 按钮

## 🔍 常见配置问题

### 问题 1: WebUI 无法访问

**检查项**:
- `dashboard.enable` 是否为 `true`
- `dashboard.port` 是否被占用
- 防火墙是否放行端口
- Docker 映射是否正确

**解决方案**:
```json
{
  "dashboard": {
    "enable": true,
    "host": "0.0.0.0",
    "port": 6185
  }
}
```

### 问题 2: AI 不回复

**检查项**:
- `provider` 数组是否配置了 Provider
- `provider_settings.default_provider_id` 是否正确
- API Key 是否有效
- 网络是否能访问 API

### 问题 3: 消息触发不了 AI

**检查项**:
- `wake_prefix` 设置（默认为 `"/"`）
- `unique_session` 影响
- 白名单设置是否限制了用户

### 问题 4: 文转图不生效

**检查项**:
- `t2i` 是否设为 `true`
- `t2i_endpoint` 是否可访问
- 网络连接（如果是 remote 模式）

## 📊 性能调优建议

### 1. 减少延迟

```json
{
  "provider_settings": {
    "streaming_response": true,  // 启用流式输出
    "max_context_length": 8000,  // 合理控制上下文长度
  }
}
```

### 2. 控制成本

```json
{
  "provider_settings": {
    "max_agent_step": 10,       // 减少 Agent 步骤
    "tool_call_timeout": 60,    // 缩短超时时间
  },
  "platform_settings": {
    "rate_limit": {
      "time": 60,
      "count": 20              // 降低频率限制
    }
  }
}
```

### 3. 提升稳定性

```json
{
  "platform_settings": {
    "segmented_reply": {
      "enable": true,           // 分段发送避免消息过长
      "words_count_threshold": 100
    }
  }
}
```

## 💡 最佳实践

1. **使用 WebUI 修改**: 避免手动编辑 JSON 导致格式错误
2. **修改前备份**: 防止配置损坏导致无法启动
3. **逐步调整**: 一次只改一项，测试后再改下一项
4. **查看日志**: 出问题时先查看平台日志定位原因
5. **参考文档**: 不确定的配置项查阅官方文档

## 📚 相关资源

- [AstrBot 官方文档](https://docs.astrbot.app/)
- [配置文件完整说明](https://docs.astrbot.app/dev/astrbot-config.html)
- [WebUI 使用指南](https://docs.astrbot.app/use/webui.html)
- [FAQ 常见问题](https://docs.astrbot.app/faq.html)

---

**使用场景**: 当你需要理解 AstrBot 的核心配置、优化性能、解决配置相关问题，或者需要进行高级定制时使用此 skill。
