---
name: "astrbot-publish-plugin"
description: "AstrBot 插件发布到市场的完整流程指南。当用户完成插件开发并准备分享给其他用户或发布到 AstrBot 插件市场时调用此 skill。"
---

# 发布插件 - AstrBot 插件市场发布指南

基于 [AstrBot 官方文档 - 发布插件](https://docs.astrbot.app/en/dev/star/plugin-publish.html) 的完整指南。

## 🎯 概述

完成插件开发后，你可以选择将其发布到 **AstrBot 插件市场**，让更多用户受益于你的工作！

## 📋 发布前检查清单

在提交之前，请确保你的插件符合以下要求：

### ✅ 必须项

- [ ] 插件代码已推送到 GitHub 仓库
- [ ] `metadata.yaml` 文件完整且正确
- [ ] `main.py` 文件存在且结构正确
- [ ] 插件可以在本地正常运行
- [ ] 无明显的 bug 或安全漏洞
- [ ] 使用 `ruff` 格式化过代码

### ✅ 推荐项

- [ ] 包含详细的 README.md 说明文档
- [ ] 主要功能都有代码注释
- [ ] 提供 `requirements.txt`（如有依赖）
- [ ] 设置了合适的 Logo（logo.png）
- [ ] 测试了主要功能流程
- [ ] 处理了异常情况和边界条件

## 🚀 第一步：准备 GitHub 仓库

AstrBot 使用 **GitHub** 来托管插件代码。

### 1. 确保代码已推送

```bash
# 检查远程仓库
git remote -v

# 如果没有远程仓库，添加一个
git remote add origin https://github.com/your-username/your-plugin-repo.git

# 推送代码
git push -u origin main
```

### 2. 打版本 Tag（推荐）

```bash
# 创建版本标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0
```

> 💡 **提示**: 使用语义化版本号（Semantic Versioning）：`主版本.次版本.修订号`

## 📝 第二步：完善元数据信息

确保 `metadata.yaml` 包含完整的元数据：

```yaml
name: astrbot_plugin_example          # 插件名
author: YourName                      # 作者名称
description: "插件的功能描述"          # 清晰的功能描述
version: "1.0.0"                      # 版本号
repo: https://github.com/xxx/xxx      # 仓库地址（重要！）

# 可选但有帮助的字段
display_name: "Example Plugin"         # 显示名（更友好）
logo: logo.png                        # Logo 文件名
support_platforms:                    # 支持的平台
  - aiocqhttp
  - telegram
astrbot_version: ">=4.16,<5"         # 版本兼容性
```

**关键字段说明**:

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | ✅ | 插件标识符（唯一） |
| `author` | ✅ | 作者名称/ID |
| `description` | ✅ | 功能描述（会显示在市场中） |
| `version` | ✅ | 当前版本号 |
| `repo` | ⚠️ 强烈推荐 | GitHub 仓库地址 |

## 🎨 第三步：编写 README.md（强烈建议）

虽然不是必须的，但好的 README 能显著提高插件的下载率：

```markdown
# AstrBot Plugin Example

简短描述你的插件是做什么的。

## ✨ 功能特性

- 特性 1
- 特性 2
- 特性 3

## 📦 安装

通过 AstrBot WebUI 的插件市场搜索安装，或：

```bash
# 手动安装方式
cd data/plugins
git clone https://github.com/your-repo/plugin-name.git
```

## ⚙️ 配置

在 WebUI 中配置以下选项：

- **选项 1**: 说明
- **选项 2**: 说明

## 📖 使用方法

### 指令 1

```
/command1 参数
```

效果描述...

### 指令 2

```
/command2 参数
```

效果描述...

## 🔧 开发

如果你想要修改或扩展此插件：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢 AstrBot 团队提供优秀的框架
- 感谢所有贡献者

## 📞 支持

如果你遇到问题或有建议：

- 提交 [Issue](https://github.com/your-repo/issues)
- 加入 QQ群: 975206796
```

## 🌐 第四步：访问 AstrBot 插件市场

### 方法一：通过网站提交

1. 打开 **AstrBot 插件市场网站**
   - URL: （请查阅官方最新地址）

2. 点击右下角的 **"+"** 按钮

3. 填写表单：
   - **基本信息**:
     - 插件名称
     - 作者信息
     - 功能简介
   
   - **仓库信息**:
     - GitHub 仓库 URL（必填）
     - 分支名称（通常是 main 或 master）
   
   - **分类和标签**:
     - 选择合适的功能分类
     - 添加关键词标签
   
   - **截图和演示**（可选）:
     - 上传使用截图
     - 提供 GIF 演示

4. 点击 **"Submit to GITHUB"** 按钮

5. 你将被重定向到 AstrBot 仓库的 Issue 提交页面

6. **验证所有信息正确**，然后点击 **"Create"** 按钮

7. 等待审核（通常 1-3 个工作日）

### 方法二：直接提交 GitHub Issue

如果网站无法访问，也可以直接提交 Issue：

1. 访问 [AstrBot GitHub Issues](https://github.com/AstrBotDevs/AstrBot/issues)

2. 点击 **"New Issue"**

3. 选择 **"Plugin Submission"** 模板（如果有）

4. 按照模板填写信息：

```markdown
## 插件信息

- **插件名称**: your-plugin-name
- **作者**: Your Name
- **GitHub 仓库**: https://github.com/xxx/xxx
- **当前版本**: 1.0.0
- **AstrBot 版本要求**: >=4.16,<5

## 功能描述

简要描述插件的主要功能和用途。

## 安装和使用

说明如何安装和使用插件。

## 截图（可选）

上传一些截图展示插件效果。
```

5. 提交 Issue 并等待审核

## ✅ 第五步：审核与发布

### 审核标准

AstrBot 团队会审核你提交的插件，主要检查：

#### ✅ 通过审核的情况

- 代码质量良好，无明显 bug
- 功能描述准确
- 不包含恶意代码
- 符合 AstrBot 插件开发规范
- metadata.yaml 信息完整

#### ❌ 可能被拒绝的原因

- 代码无法运行或存在严重 bug
- 功能描述与实际不符
- 包含不安全代码（如硬编码密钥、后门等）
- 侵犯他人版权
- 与已有插件功能高度重复且无创新

### 审核流程

1. **提交** → 2. **初步审查** → 3. **测试验证** → 4. **审核结果通知**

通常在 **1-3 个工作日** 内完成审核。

### 审核通过后

✨ **恭喜！你的插件已上线！**

用户现在可以：
- 在 AstrBot WebUI 插件市场中搜索并安装
- 通过一键安装快速部署
- 给你的插件评分和反馈

## 🔄 第六步：维护和更新

### 发布新版本

当你修复 bug 或添加新功能后：

```bash
# 1. 更新 version
# 编辑 metadata.yaml，将 version 改为 1.1.0

# 2. 提交更改
git add .
git commit -m "feat: 新增功能 X"

# 3. 打新版本 tag
git tag v1.1.0

# 4. 推送
git push origin main
git push origin v1.1.0
```

### 更新插件市场信息

如果需要更新插件描述或其他信息：

1. 回到你提交的 Issue 页面
2. 添加评论说明更新内容
3. 或者联系 AstrBot 团队协助更新

### 处理用户反馈

定期检查：
- GitHub Issues（bug 报告、功能请求）
- 插件市场的评分和评论
- QQ 群的用户反馈

及时回应用户问题和建议。

## 📈 第七步：推广你的插件

### 优化曝光率

1. **关键词优化**:
   - 在 description 中包含常用搜索词
   - 选择准确的分类和标签

2. **视觉吸引力**:
   - 提供清晰的 Logo（256x256）
   - 上传高质量的使用截图
   - 制作 GIF 动图展示核心功能

3. **完善的文档**:
   - 编写详细的 README
   - 提供快速开始指南
   - 列出常见问题 FAQ

### 分享渠道

- **AstrBot 官方 QQ群**: 975206796
- **社交媒体**: 微博、Twitter 等
- **技术社区**: V2EX、掘金、知乎等
- **个人博客/公众号**: 写一篇介绍文章

## ⚠️ 注意事项

### 版权和许可

- 确保你有权发布此插件的所有代码
- 选择合适的开源许可证（推荐 MIT、Apache 2.0）
- 如果使用了第三方库，确保其许可证兼容

### 安全性

- 不要在代码中硬编码敏感信息（API 密钥、密码等）
- 用户输入要进行验证和清理
- 外部 API 调用要有超时设置
- 避免使用 `eval()`、`exec()` 等危险函数

### 兼容性

- 明确标注支持的 AstrBot 版本范围
- 测试在不同平台适配器下的表现
- 处理依赖缺失的 gracefully

## 🎉 发布后的持续改进

### 收集使用数据（可选）

```python
class AnalyticsPlugin(Star):
    """带基本分析的插件"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.usage_count = 0
    
    @filter.command("feature")
    async def feature(self, event: AstrMessageEvent):
        """某个功能"""
        self.usage_count += 1
        
        # 每 100 次使用记录一次日志（避免刷屏）
        if self.usage_count % 100 == 0:
            logger.info(f"功能已使用 {self.usage_count} 次")
        
        # 正常逻辑...
```

### 版本策略建议

- **Patch 版本** (x.x.Z): Bug 修复、小改动
- **Minor 版本** (x.Y.z): 新功能、向后兼容
- **Major 版本** (X.y.z): 重大改动、可能不兼容

## 📚 相关资源

- [AstrBot 官方文档](https://docs.astrbot.app/)
- [AstrBot GitHub 仓库](https://github.com/AstrBotDevs/AstrBot)
- [开发者 QQ群](https://jq.qq.com/?_wv=1027&k=QYV7mX3l) (975206796)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

**使用场景**: 当你完成了插件的开发和测试，准备将插件分享给社区或发布到 AstrBot 插件市场时使用此 skill。
