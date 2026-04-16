---
name: "astrbot-plugin-start"
description: "AstrBot 插件开发入门指南，涵盖环境准备、项目初始化、模板获取、元数据配置等基础流程。当用户首次开发插件或需要了解插件开发整体流程时调用此 skill。"
---

# 从这里开始 - AstrBot 插件开发入门

基于 [AstrBot 官方插件开发指南](https://docs.astrbot.app/dev/star/plugin-new.html) 的完整入门教程。

## 📋 前置要求

- 具备 Python 编程经验
- 了解 Git 和 GitHub 的基本使用
- 开发者 QQ 群: 975206796（可选加入）

## 🚀 第一步: 获取插件模板

1. 打开 AstrBot 插件模板仓库: [helloworld](https://github.com/AstrBotDevs/helloworld)
2. 点击右上角 **"Use this template"**
3. 点击 **"Create new repository"**
4. 在 **Repository name** 处填写插件名：
   - ✅ 推荐格式: `astrbot_plugin_xxx`
   - ❌ 不能包含空格
   - ✅ 保持全部字母小写
   - ✅ 尽量简短
5. 点击右下角 **"Create repository"**

## 📥 第二步: 克隆项目到本地

```bash
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone <你的插件仓库地址>
```

使用 VSCode 打开 AstrBot 项目，定位到 `data/plugins/<你的插件名字>` 目录。

## ⚙️ 第三步: 配置元数据文件

⚠️ **重要**: 必须修改 `metadata.yaml` 文件，AstrBot 依赖此文件识别插件元数据。

### metadata.yaml 完整配置示例

```yaml
name: astrbot_plugin_example          # 插件名（必须）
author: your_name                     # 作者（必须）
description: "插件描述"                # 功能描述（必须）
version: "1.0.0"                      # 版本号（必须）

# 可选配置项
display_name: "Example Plugin"        # 插件展示名（用于市场等场景）
logo: logo.png                        # Logo 文件名（需放在插件根目录）

# 支持平台声明（可选）
support_platforms:
  - aiocqhttp
  - qq_official
  - telegram
  - wecom
  - lark
  - dingtalk
  - discord
  - slack
  - kook
  - vocechat
  - weixin_official_accounts
  - atori
  - misskey
  - line

# AstrBot 版本兼容性（可选，遵循 PEP 440 规范）
astrbot_version: ">=4.16,<5"
```

### 版本号格式说明

```yaml
# 仅最低版本要求
astrbot_version: ">=4.17.0"

# 范围约束（推荐）
astrbot_version: ">=4.16,<5"

# 兼容版本
astrbot_version: "~=4.17"
```

### 可选功能配置

#### 设置插件 Logo（可选）

在插件目录下添加 `logo.png`:
- 长宽比: **1:1**
- 推荐尺寸: **256x256**

#### 声明支持平台（Optional）

在 metadata.yaml 中添加 `support_platforms` 字段，WebUI 插件页会展示该字段。

支持的值：
- aiocqhttp, qq_official, telegram, wecom, lark, dingtalk
- discord, slack, kook, vocechat, weixin_official_accounts
- atori, misskey, line

## 🔧 第四步: 调试与开发环境

### 调试方法

AstrBot 采用运行时注入机制：

1. 启动 AstrBot 主程序
2. 进入 WebUI → **插件管理**
3. 找到你的插件，点击右上角 **...**
4. 选择 **"重载插件"**

如果插件加载失败：
- 查看错误提示
- 点击 **"尝试一键重载修复"**

### 依赖管理

在插件目录下创建 `requirements.txt`:

```
aiohttp>=3.8.0
httpx>=0.23.0
```

⚠️ **重要**: 必须声明所有第三方依赖，防止用户安装时出现 Module Not Found 错误。

## 📝 开发原则（必读）

### ✅ 必须遵守的原则

1. **功能测试**: 所有功能必须经过测试
2. **代码注释规范**:
   - 文件顶部注释说明用途
   - 类/函数前添加 Docstring
   - 关键逻辑添加行内注释解释"为什么"
3. **数据存储位置**: 持久化数据存放在 `data/` 目录，而非插件自身目录
4. **错误处理**: 良好的异常处理机制，避免因单个错误导致崩溃
5. **代码格式化**: 提交前使用 `ruff` 工具格式化代码

### ❌ 禁止事项

1. **禁止使用 `requests` 库**进行网络请求
2. 推荐使用异步库: `aiohttp`, `httpx` 等
3. 功能扩展优先提交 PR 给原插件作者（除非原作者已停止维护）

## 🛠️ 常用命令

```bash
# 代码格式化
ruff format .
ruff check .

# 重载插件（通过 WebUI 操作）
```

## 💡 最佳实践建议

1. **模块化设计**: 将不同功能拆分为独立模块
2. **日志记录**: 使用 AstrBot 提供的日志接口 (`from astrbot.api import logger`)
3. **配置管理**: 使用 YAML 或 JSON 管理可配置项
4. **版本控制**: 及时打 tag 标记重要版本
5. **文档完善**: 为复杂逻辑编写详细注释

## 🐛 常见问题排查

| 问题 | 解决方案 |
|------|----------|
| 插件未加载 | 检查 `metadata.yaml` 格式是否正确 |
| 依赖缺失 | 确认 `requirements.txt` 已创建且格式正确 |
| 版本不兼容 | 检查 `astrbot_version` 字段设置 |
| 网络请求报错 | 将 `requests` 替换为 `aiohttp` 或 `httpx` |
| 数据丢失 | 确保持久化数据存储在 `data/` 目录 |

## 📚 相关资源

- [AstrBot 官方文档](https://docs.astrbot.app/)
- [插件模板仓库](https://github.com/AstrBotDevs/helloworld)
- [开发者 QQ群](https://jq.qq.com/?_wv=1027&k=QYV7mX3l) (975206796)

---

**使用场景**: 当你需要开始一个新的 AstrBot 插件项目时，按照此 skill 的步骤操作即可完成标准化的项目初始化和配置。
