---
name: "astrbot-text-to-image"
description: "AstrBot 文字转图片功能详解，包括基础文转图和自定义 HTML 模板渲染。当用户需要将文本内容渲染为图片或创建美观的消息卡片时调用此 skill。"
---

# 文转图 - AstrBot 文本渲染为图片

基于 [AstrBot 官方文档 - 文转图](https://docs.astrbot.app/dev/star/guides/html-to-pic.html) 的完整指南。

## 🖼️ 概述

AstrBot 支持将文字渲染成图片，提供两种方式：
1. **基础文转图** - 简单的纯文本转图片
2. **自定义 HTML 模板** - 使用 HTML + Jinja2 渲染精美图片

## ✨ 一、基础文转图

### 最简单的用法

```python
@filter.command("image")
async def text_to_image(self, event: AstrMessageEvent, text: str):
    """将文本转换为图片"""
    
    # 将文本渲染为图片，返回 URL
    url = await self.text_to_image(text)
    
    # 发送图片
    yield event.image_result(url)
```

### 保存到本地

```python
@filter.command("image_local")
async def text_to_image_local(self, event: AstrMessageEvent, text: str):
    """将文本转换为图片并保存到本地"""
    
    # 返回本地文件路径而非 URL
    path = await self.text_to_image(
        text, 
        return_url=False  # 设置为 False 返回路径
    )
    
    yield event.image_result(path)
```

### 实际示例：代码展示

```python
@filter.command("show_code")
async def show_code(self, event: AstrMessageEvent, language: str):
    """显示指定语言的示例代码"""
    
    code_examples = {
        "python": '''
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_word()''',
        
        "javascript": '''
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

helloWorld();''',
        
        "java": '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}'''
    }
    
    code = code_examples.get(language, "# 代码未找到")
    
    url = await self.text_to_image(code)
    yield event.image_result(url)
```

## 🎨 二、自定义 HTML 模板（高级）

使用 HTML + Jinja2 可以创建更美观、更复杂的图片。

### 基础模板示例

```python
TMPL = '''
<div style="font-family: 'Microsoft YaHei', sans-serif; padding: 20px;">
    <h1 style="color: #333; border-bottom: 2px solid #4a90e2; padding-bottom: 10px;">
        📋 Todo List
    </h1>
    
    <ul style="list-style: none; padding: 0;">
        {% for item in items %}
        <li style="
            background: #f5f5f5;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4a90e2;
        ">
            {{ item }}
        </li>
        {% endfor %}
    </ul>
</div>
'''

@filter.command("todo")
async def custom_todo(self, event: AstrMessageEvent):
    """渲染 Todo 列表为图片"""
    
    options = {}  # 渲染选项（可选）
    
    url = await self.html_render(
        TMPL,                                    # HTML 模板
        {"items": ["吃饭", "睡觉", "玩原神"]},   # Jinja2 数据
        options=options                           # 渲染选项
    )
    
    yield event.image_result(url)
```

### 复杂模板示例：个人信息卡片

```python
PROFILE_TMPL = '''
<div style="
    font-family: 'Microsoft YaHei', sans-serif;
    max-width: 400px;
    margin: 0 auto;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
">
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="
            width: 80px;
            height: 80px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
        ">
            {{ avatar }}
        </div>
        <h2 style="margin: 0; font-size: 24px;">{{ name }}</h2>
        <p style="margin: 5px 0 0; opacity: 0.8;">{{ title }}</p>
    </div>
    
    <div style="
        background: rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
    >
        {% for stat in stats %}
        <div style="
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        ">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
        </div>
        {% endfor %}
    </div>
</div>
'''

@filter.command("profile")
async def profile_card(self, event: AstrMessageEvent):
    """生成个人资料卡片"""
    
    user_name = event.get_sender_name()
    
    data = {
        "avatar": "👤",
        "name": user_name,
        "title": "AstrBot 用户",
        "stats": [
            {"label": "等级", "value": "Lv.42"},
            {"label": "经验值", "value": "12,580"},
            {"label": "注册时间", "value": "2024-01-01"},
            {"label": "活跃度", "value": "⭐⭐⭐⭐⭐"}
        ]
    }
    
    url = await self.html_render(PROFILE_TMPL, data)
    yield event.image_result(url)
```

### 数据可视化示例：进度条

```python
PROGRESS_TMPL = '''
<div style="
    font-family: 'Microsoft YaHei', sans-serif;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 12px;
">
    <h3 style="margin: 0 0 20px; color: #333;">{{ title }}</h3>
    
    {% for item in items %}
    <div style="margin-bottom: 15px;">
        <div style="
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 14px;
        >
            <span>{{ item.name }}</span>
            <span style="color: {{ item.color }};">{{ item.value }}%</span>
        </div>
        <div style="
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        ">
            <div style="
                height: 100%;
                width: {{ item.value }}%;
                background: linear-gradient(90deg, {{ item.color }}, {{ item.color }}dd);
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    {% endfor %}
</div>
'''

@filter.command("progress")
async def progress_chart(self, event: AstrMessageEvent):
    """生成技能进度图表"""
    
    data = {
        "title": "📊 技能熟练度",
        "items": [
            {"name": "Python", "value": 90, "color": "#4a90e2"},
            {"name": "JavaScript", "value": 75, "color": "#f39c12"},
            {"name": "Docker", "value": 60, "color": "#27ae60"},
            {"name": "SQL", "value": 85, "color": "#e74c3c"}
        ]
    }
    
    url = await self.html_render(PROGRESS_TMPL, data)
    yield event.image_result(url)
```

## ⚙️ 三、渲染选项（Options）

`html_render()` 方法支持 Playwright 的截图选项：

```python
options = {
    # 截图超时时间（秒）
    "timeout": 30,
    
    # 图片格式: "jpeg" 或 "png"
    "type": "png",
    
    # 图片质量（仅 JPEG 有效，0-100）
    "quality": 90,
    
    # 是否透明背景（仅 PNG 有效）
    "omit_background": False,
    
    # 是否截取整个页面
    "full_page": True,
    
    # 裁切区域
    "clip": {"x": 0, "y": 0, "width": 800, "height": 600},
    
    # CSS 动画: "allow" 或 "disabled"
    "animations": "disabled",
    
    # 文本光标: "hide" 或 "initial"
    "caret": "hide",
    
    # 页面缩放: "css" 或 "device"
    "scale": "css"
}

url = await self.html_render(template, data, options=options)
```

### 常用选项组合

#### 高质量 PNG（推荐用于复杂设计）

```python
options = {
    "type": "png",
    "quality": 100,
    "omit_background": False,
    "full_page": True
}
```

#### 压缩 JPEG（适合快速分享）

```python
options = {
    "type": "jpeg",
    "quality": 85,
    "full_page": False
}
```

#### 透明背景 PNG（适合贴图）

```python
options = {
    "type": "png",
    "omit_background": True,
    "full_page": False
}
```

## 🎯 四、Jinja2 模板语法

### 变量输出

```html
<!-- 输出变量 -->
<p>{{ variable }}</p>

<!-- 带默认值 -->
<p>{{ variable or "默认值" }}</p>
```

### 条件判断

```html
{% if score >= 90 %}
    <p style="color: green">优秀！</p>
{% elif score >= 60 %}
    <p style="color: orange">及格</p>
{% else -->
    <p style="color: red">需要努力</p>
{% endif %}
```

### 循环

```html
<ul>
{% for item in items %}
    <li>{{ loop.index }}. {{ item.name }}</li>
{% endfor %}
</ul>

<!-- 带索引 -->
{% for i in range(10) %}
    <span>{{ i }}</span>
{% endfor %}
```

### 过滤器

```html
<!-- 字符串处理 -->
<p>{{ text | upper }}</p>           <!-- 转大写 -->
<p>{{ text | lower }}</p>           <!-- 转小写 -->
<p>{{ text | truncate(50) }}</p>    <!-- 截断 -->

<!-- 列表处理 -->
<p>{{ items | length }}</p>         <!-- 长度 -->
<p>{{ items | join(", ") }}</p>    <!-- 连接 -->

<!-- 日期格式化 -->
<p>{{ date | strftime("%Y-%m-%d") }}</p>
```

## 🛠️ 五、实际应用案例

### 案例 1：每日报告

```python
DAILY_REPORT_TMPL = '''
<div style="
    font-family: 'Microsoft YaHei', sans-serif;
    max-width: 500px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
">
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        text-align: center;
    ">
        <h1 style="margin: 0; font-size: 28px;">📊 每日报告</h1>
        <p style="margin: 10px 0 0; opacity: 0.9;">{{ date }}</p>
    </div>
    
    <div style="padding: 24px;">
        {% for section in sections %}
        <div style="margin-bottom: 20px;">
            <h3 style="
                margin: 0 0 12px;
                color: {{ section.color }};
                font-size: 18px;
                border-left: 4px solid {{ section.color }};
                padding-left: 12px;
            ">
                {{ section.title }}
            </h3>
            <p style="
                margin: 0;
                line-height: 1.6;
                color: #555;
            ">
                {{ section.content }}
            </p>
        </div>
        {% endfor %}
    </div>
</div>
'''

@filter.command("daily_report")
async def daily_report(self, event: AstrMessageEvent):
    """生成每日报告"""
    
    from datetime import datetime
    
    report_data = {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "sections": [
            {
                "title": "✅ 完成任务",
                "color": "#27ae60",
                "content": "• 完成了插件开发文档\n• 修复了 3 个 bug\n• 优化了性能"
            },
            {
                "title": "📝 进行中",
                "color": "#f39c12",
                "content": "• 新功能开发（完成度 70%）\n• 代码审查\n• 单元测试编写"
            },
            {
                "title": "⏳ 待办事项",
                "color": "#e74c3c",
                "content": "• 部署到生产环境\n• 编写用户手册\n• 性能测试"
            }
        ]
    }
    
    url = await self.html_render(DAILY_REPORT_TMPL, report_data)
    yield event.image_result(url)
```

### 案例 2：排行榜

```python
RANKING_TMPL = '''
<div style="
    font-family: 'Microsoft YaHei', sans-serif;
    max-width: 450px;
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
">
    <h2 style="
        text-align: center;
        margin: 0 0 24px;
        font-size: 26px;
        background: linear-gradient(90deg, #f093fb, #f5576c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    ">
        🏆 {{ title }}
    </h2>
    
    {% for entry in rankings %}
    <div style="
        display: flex;
        align-items: center;
        background: rgba(255,255,255,0.05);
        margin-bottom: 12px;
        padding: 16px;
        border-radius: 12px;
        {% if loop.index <= 3 %}
        border-left: 4px solid 
            {% if loop.index == 1 %}#ffd700
            {% elif loop.index == 2 %}#c0c0c0
            {% else %}#cd7f32{% endif %};
        {% endif %}
    ">
        <div style="
            width: 40px;
            height: 40px;
            background: 
                {% if loop.index == 1 %}linear-gradient(135deg, #ffd700, #ffed4e)
                {% elif loop.index == 2 %}linear-gradient(135deg, #c0c0c0, #ffffff)
                {% elif loop.index == 3 %}linear-gradient(135deg, #cd7f32, #ff9a44)
                {% else %}rgba(255,255,255,0.1){% endif %};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            margin-right: 16px;
        ">
            {{ loop.index }}
        </div>
        
        <div style="flex: 1;">
            <div style="font-weight: bold; font-size: 16px;">
                {{ entry.name }}
            </div>
            <div style="opacity: 0.7; font-size: 13px; margin-top: 4px;">
                {{ entry.desc }}
            </div>
        </div>
        
        <div style="
            font-size: 22px;
            font-weight: bold;
            color: 
                {% if loop.index == 1 %}#ffd700
                {% elif loop.index == 2 %}#c0c0c0
                {% elif loop.index == 3 %}#cd7f32
                {% else %}white{% endif %};
        ">
            {{ entry.score }}
        </div>
    </div>
    {% endfor %}
</div>
'''

@filter.command("ranking")
async def ranking(self, event: AstrMessageEvent):
    """生成排行榜图片"""
    
    data = {
        "title": "活跃用户排行",
        "rankings": [
            {"name": "用户A", "desc": "连续登录 30 天", "score": "9999"},
            {"name": "用户B", "desc": "连续登录 28 天", "score": "8888"},
            {"name": "用户C", "desc": "连续登录 25 天", "score": "7777"},
            {"name": "用户D", "desc": "连续登录 20 天", "score": "6666"},
            {"name": "用户E", "desc": "连续登录 15 天", "score": "5555"}
        ]
    }
    
    url = await self.html_render(RANKING_TMPL, data)
    yield event.image_result(url)
```

## 💡 最佳实践

1. **响应式设计**: 使用相对单位和 Flexbox/Grid
2. **颜色搭配**: 保持视觉一致性，使用渐变增加美感
3. **字体选择**: 使用系统字体保证兼容性
4. **性能优化**: 避免过于复杂的 CSS 动画
5. **测试预览**: 使用 AstrBot Text2Image Playground 在线调试
6. **移动端适配**: 注意在手机上的显示效果

## 🌐 相关资源

- **在线调试工具**: AstrBot Text2Image Playground（可在 WebUI 中找到）
- **Jinja2 文档**: https://jinja.palletsprojects.com/
- **Playwright 文档**: https://playwright.dev/python/docs/api/page-screenshot

---

**使用场景**: 当你需要将文本、数据报告、排行榜、个人信息等内容以美观的图片形式发送给用户时使用此 skill。
