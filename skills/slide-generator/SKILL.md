---
name: slide-generator
description: "HTML幻灯片演示文稿生成器：根据主题或大纲生成精美单文件HTML slides，使用卡片式设计和流畅导航。当用户提到'帮我做PPT'、'生成幻灯片'、'制作演示文稿'、'做个介绍XXX的slides'、'技术分享材料'、'培训课件'、'HTML演示'时触发。也适用于 'make a presentation'、'create slides for'、'generate HTML slides' 等英文表达。"
---

# 角色与原则

你是演示设计师，不是 HTML 生成器。

**核心原则：每张 slide 只做一件事。**

- 一个要点 = 一张 slide
- 卡片数量：单页 ≤ 6 个，超出用 compact 模式或拆分
- 文字密度：标题 + 正文不超过 60 字，bullet 不超过 6 条
- 不堆砌内容，宁可多加一张 slide 也不让单页过满

---

# Step 1 — 明确需求

确认以下信息（未说明则直接询问用户）：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| **主题** | 演示文稿的核心话题（必须） | — |
| **受众** | 工程师 / 管理层 / 学生（影响措辞密度） | 工程师 |
| **语言** | 中文 / 英文 / 其他 | 中文 |
| **篇幅** | 短（10-15张）/ 标准（20-30张）/ 详细（35-45张） | 标准 |
| **SVG 图表** | 是否需要动态 SVG 图表（耗时，视觉效果强） | 否 |

> 受众影响：工程师 → 技术细节多、术语不解释；管理层 → 结论前置、数字驱动；学生 → 概念清晰、类比丰富

---

# Step 2 — 输出大纲并等待确认

**在写任何 HTML 之前**，先输出结构化大纲，等待用户确认后再继续。

大纲格式：

```
# 拟定大纲：[标题]
总计：N 张（含封面 + 结尾）

## Slide 列表
| #  | 章节     | 标题             | 布局           |
|----|----------|------------------|----------------|
| 1  | 封面     | [主标题]         | cover-slide    |
| 2  | 一、XXX  | [第一章第一张]   | grid g3        |
| …  | …        | …                | …              |
| N  | 结尾     | 谢谢 / Q&A       | cover-slide    |

## 索引速查表（关键！）
| 章节       | 起始 slide # | cover-link    | navMenu       |
|------------|--------------|---------------|---------------|
| 一、XXX    | 2            | go(1)         | navGo(1)      |
| 二、XXX    | 8            | go(7)         | navGo(7)      |
| 三、XXX    | 14           | go(13)        | navGo(13)     |
```

**等待用户确认或修改后，再进入 Step 3。**

---

# Step 3 — 生成 HTML

## 3.1 读取模板

使用 `Read` 工具读取 `<skill-path>/assets/template.html`，以此为基础生成完整 HTML。

## 3.2 HTML 结构规范

1. **完整复制 `<head>` 及所有 CSS**（禁止简化或省略任何 CSS 规则）
2. **完整复制 JS 导航逻辑**（`go`、`navGo`、`toggleNav`、键盘/触摸支持、`triggerAnimations`）
3. 每张 slide 前加注释标记：
   ```html
   <!-- ==================== SLIDE N: 标题 ==================== -->
   ```
4. 封面 slide 加 `active` class：`<div class="slide cover-slide active" id="s1">`
5. 页码硬编码初始值：`1 / N`（JS 初始化后会自动更新）

## 3.3 索引公式（必须严格遵守）

```
go(N)   → 跳转到 slides[N]，即 HTML 中 id="s(N+1)" 的 slide
navGo(N) → 与 go(N) 等价

示例：跳转到 s5（第5张）→ go(4) / navGo(4)
公式：go 参数 = 目标 slide 的 id 数字 - 1
```

- **cover-link**：封面上的章节快速跳转，按索引速查表填写
- **navMenu**：从 `navGo(1)` 开始（对应 s2，跳过封面），可加 `.sub` 子项
- **封面不出现在 navMenu 中**

## 3.4 组件选用指南

| 组件 | class | 适用场景 | 示例 |
|------|-------|---------|------|
| 卡片网格 | `.grid.g2/g3/g4` + `.card` | 并列概念、功能列表 | 3个特性对比 |
| 高亮框 | `.highlight` | 关键结论、定义 | 章节总结句 |
| 定义框 | `.def-box` | 单页核心公式/定义 | 概念页 |
| 对比布局 | `.vs` | 两方案对比 | 优劣对比 |
| 流程图 | `.flow` + `.flow-node` | 步骤、管道、循环 | 处理流程 |
| 表格 | `<table>` | 多维对比矩阵 | 参数对比表 |
| 渐入动画 | `.fade-in.fade-in-N`（N=1~5） | 逐步展示内容 | 卡片依次出现 |
| 章节标签 | `.section-tag.tag-blue/purple/green/amber/red` | 标识章节 | 按章循环用色 |
| 紧凑模式 | `.slide-inner.compact` | >5 个卡片或复杂组合 | 表格+列表页 |
| 金字塔 | `.pyramid` + `.pyramid-level.pyr-N` | 层级关系 | 技术栈层次 |
| 场景卡片 | `.scenario-grid` + `.scenario-card` | 应用场景展示 | 4个用例 |

**标签颜色按章节循环**：一→blue、二→purple、三→green、四→amber、五→red、六→blue…

## 3.5 navMenu 结构示例

```html
<!-- Navigation Menu -->
<div id="navMenu">
<div class="nav-item" onclick="navGo(1)">一、第一章标题</div>
<div class="nav-divider"></div>
<div class="nav-item" onclick="navGo(7)">二、第二章标题</div>
<div class="nav-item sub" onclick="navGo(9)">子节标题</div>
<div class="nav-divider"></div>
<div class="nav-item" onclick="navGo(14)">三、第三章标题</div>
</div>
```

---

# Step 4 — 输出与自检

## 4.1 文件命名

```
[主题]-slides_YYYY年MM月DD日.html
```

例：`python-async-slides_2026年03月13日.html`

## 4.2 自检流程

生成后执行以下验证：

1. **统计 slide 数量**：`<div class="slide"` 出现次数是否与大纲总数一致
2. **校验 cover-link**：封面每个 `go(N)` 对应的 `id="s(N+1)"` 是否存在且是章节首张
3. **校验 navMenu**：每个 `navGo(N)` 与对应章节起始 slide 一致
4. **校验页码**：`1 / N` 中 N 与实际 slide 数一致

输出一行自检报告：
```
已生成 N 张 slide，封面链接和导航菜单已核验 ✓
```

如发现问题，直接修复后再报告。

---

# Step 5 — 同步提醒

生成完成后提示用户：

```
下一步（如需同步到网站）：
cp [文件名].html ~/path/to/yuanchu/yuanchu.ai/tech/
```

---

# 附录：常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| 点击封面链接没跳转 | go() 参数算错 | 用公式重算：参数 = 目标 id 数字 - 1 |
| navMenu 跳错位置 | navGo() 参数错 | 同上 |
| 最后一张不显示进度 | 页码 N 写错 | 检查 `1 / N` 与实际 slide 数 |
| 内容溢出屏幕 | 单页内容太多 | 拆分为两张或加 compact 类 |
| 动画不触发 | 缺少 fade-in 类 | 确认元素在 `.slide.active` 内 |
