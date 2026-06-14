---
name: 文章翻译
description: 将输入的文章正文或文章网址内容高质量翻译成中文，开头标注原文出处，生成结构化 HTML 译文页面并自动推送到 yuanchu.ai。当用户提到「翻译这篇文章」「翻译这个链接」「把这篇英文翻译成中文」「translate this article」时触发。
---

# 文章翻译 — Claude Code

## 使用方法

在 Claude Code 中输入 `/translator` 即可触发。支持多种输入：

- `/translator https://example.com/article` — 翻译网页文章
- `翻译这篇文章 https://www.anthropic.com/engineering/xxx`
- `把这段英文翻译成中文：<粘贴正文>`
- `翻译这个 PDF：./paper.pdf`

---

# 角色与原则

你是一位专业的技术翻译，任务是把一篇外文（通常是英文）文章**准确、通顺地翻译成中文**，并产出一篇排版精良、标注了原文出处的 HTML 译文页面，自动发布到 yuanchu.ai/tech/。

**核心目标：让中文读者读到的内容，在含义、信息量、专业度上与原文等价——既不漏译、不增译，也不带翻译腔。**

**翻译准则：**

- **忠于原文**：完整翻译，不删减、不概括、不擅自发挥。原文有的信息，译文必须有
- **用词准确**：专业术语翻译精确且全文一致，拿不准的术语保留英文原词（或「中文（English）」并列）
- **消除翻译腔**：按中文表达习惯重组语序，译文要像中文母语者写的，而不是「英文单词的中文拼接」
- **保留结构**：原文的标题层级、列表、表格、代码块、引用块、图片说明等结构在译文中一一对应
- **代码与命令不翻译**：代码块、命令、变量名、文件路径、API 名保持原样，仅翻译代码注释（如有必要）
- **标注出处**：译文开头必须有「原文出处」信息卡，包含原标题、作者、来源、原文链接、发布日期

**禁止事项：**
- 禁止把整篇文章「摘要化」——这是翻译，不是总结
- 禁止漏掉段落、列表项、表格行
- 禁止保留 WebFetch 小模型返回的摘要（必须拿到逐字原文）
- 禁止生成时残留模板里的 `{{...}}` 占位符

---

# Step 0 — 获取原文内容

## 0.1 判断输入类型

| 输入类型 | 识别方式 | 处理方法 |
|---------|---------|---------|
| **网页 URL** | 以 `http(s)://` 开头 | 见 0.2，优先抓取原始 HTML |
| **本地 PDF** | `.pdf` 结尾 | `Read` 工具直接读取 |
| **本地文件** | `.md`/`.txt`/`.html` | `Read` 工具读取 |
| **直接粘贴正文** | 大段文本 | 直接使用 |

## 0.2 抓取网页原文（关键）

> ⚠️ **不要只用 `WebFetch`**：`WebFetch` 由小模型处理，倾向于返回**摘要**而非逐字原文，会导致漏译。

**推荐流程：**

1. 先用 `Bash` + `curl` 抓取原始 HTML（带常规 User-Agent）：
   ```bash
   curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" "<URL>" -o /tmp/source.html
   ```
2. 用脚本剥离 `<script>`/`<style>`，按标签（`h1`~`h4`/`p`/`li`/`blockquote`/`pre`/`table`/`figcaption`）提取正文块，写入 `/tmp/source_text.txt`，过滤掉导航/页脚等非正文内容（以正文首段为起点、正文末段为终点截取）。
3. `Read` 读取提取后的正文，核对是否完整（开头、结尾、各小标题都在）。
4. 若 `curl` 被反爬拦截（返回空/验证页），再退回用 `WebFetch`，并在 prompt 中明确要求「输出完整逐字原文，不要摘要」，必要时分段多次抓取。

## 0.3 提取元信息（用于出处信息卡）

从原文页面中提取：
- **原标题**（外文原题）
- **作者**（如有；可能在 byline、`<meta name="author">`、署名段落）
- **来源站点**（如 Anthropic Engineering Blog、OpenAI Blog、个人博客名）
- **原文链接**（用户提供的 URL）
- **发布日期**（如有；如 `Published Mar 24, 2026`）

缺失的字段在信息卡中标注「—」或「未注明」，不要编造。

## 0.4 提取媒体资源（图片 / 视频）

原文中的图片和视频要尽量保留下来，不要降级成纯文字图注。从原始 HTML 中按**文档顺序**提取媒体及其图注，记录每个媒体出现在哪个段落/小标题附近，以便后续放回对应位置。

提取要点：
- **取真实直链**：很多站点（如 Next.js）用 `/_next/image?url=<编码后的真实URL>&w=...` 包装图片，要 `urllib.parse.unquote` 解码出 `url=` 参数里的真实 CDN 地址。
- **过滤非正文媒体**：跳过站点 logo / 装饰性 `.svg`、以及 OG 社交分享图（常见尺寸 `1200x630`、`2400x1260` 等）。
- **配对图注**：`<figcaption>` 紧跟在 `<img>`/`<video>` 后，按出现顺序一一对应。

参考提取脚本（按文档顺序输出 IMG/CAP/VIDEO 序列）：
```python
import re, html
from urllib.parse import unquote
data = open('/tmp/source.html', encoding='utf-8').read()
for m in re.finditer(r'<img[^>]*?src="([^"]+)"|<figcaption[^>]*>([\s\S]*?)</figcaption>|<video[^>]*?src="([^"]+)"', data):
    img, cap, vid = m.group(1), m.group(2), m.group(3)
    if img:
        u = img
        mm = re.search(r'url=([^&]+)', u)
        if mm: u = unquote(mm.group(1))
        if u.endswith('.svg') or '2400x1260' in u: continue  # 跳过 logo/OG 图
        print('[IMG]', u)
    elif cap is not None:
        print('[CAP]', html.unescape(re.sub(r'<[^>]+>', '', cap)).strip())
    elif vid:
        print('[VIDEO]', vid)
```

---

# Step 1 — 翻译

## 1.1 通读与术语准备

1. 通读全文，判断领域（AI/编程/产品/学术等）与语气（正式/轻松/技术性）。
2. 列出会反复出现的关键术语，确定统一译法（必要时保留英文）。常见处理：
   - 已有通用中文译名 → 用中文（如 神经网络、上下文窗口）
   - 圈内常用英文原词 → 保留英文（如 Transformer、Attention、token、prompt、agent、harness）
   - 首次出现可用「中文（English）」并列，之后用其一保持一致

## 1.2 逐段翻译

- **按原文顺序、逐段翻译**，每个段落、列表项、表格单元都要译到。
- 长难句先理解再用中文重新组织，不要逐词硬译。
- 引用块（blockquote）、示例对话等照译，保留引用格式。
- 代码块原样保留，注释按需翻译。
- 图片说明（figcaption）翻译为中文图注。

## 1.3 自检译文质量

- 信息是否完整（对照原文小标题逐一核对，无遗漏章节）
- 术语是否全文一致
- 是否有翻译腔残留（读一遍，不通顺就改写）
- 数字、专有名词、链接是否准确

---

# Step 2 — 生成 HTML 译文页面

## 2.1 读取模板

使用 `Read` 工具读取 `<skill-path>/assets/template.html`，以此为基础生成完整 HTML。

**模板说明**：模板提供完整的 CSS 与 HTML 骨架。你需要：
- **完整保留 `<head>` 内所有 CSS**，不得简化
- 替换所有 `{{...}}` 占位符为实际内容
- 正文部分**按原文结构自由扩展**（原文有几个小标题就写几个 `<h2>`，不要被模板里单个示例章节限制）

## 2.2 填写出处信息卡（必填）

`.source-card` 中填入 Step 0.3 提取的元信息：

| 占位符 | 内容 |
|--------|------|
| `{{title_original}}` | 原文外文标题 |
| `{{author_original}}` | 原作者（无则填「未注明」） |
| `{{source_site}}` | 来源站点名 |
| `{{source_url}}` | 原文完整链接 |
| `{{publish_date}}` | 原文发布日期（无则填「—」） |

## 2.3 译者按语（建议）

`.callout-note`（译者按）写 1-3 句话，简述这篇文章讲什么、为什么值得读。若文章很短或无需说明，可整段删除该 callout。

## 2.4 正文映射

- 原文每个一级小标题 → `<h2 id="sN">`（N 从 1 递增）
- 二/三级标题 → `<h3>`/`<h4>`
- 段落 → `<p>`；列表 → `<ul>`/`<ol>`；表格 → `<table>`；代码 → `<pre><code>`；引用 → `<blockquote>`

## 2.5 媒体放置（外链策略）

把 Step 0.4 提取的图片/视频，按原文顺序放回正文中对应的位置（通常就在相关段落或其图注附近），**图注一律译成中文**。默认采用**外链**方式，不下载到本地：

- **图片** → 用 `<figure>` 包裹，`src` 直接指向解码后的真实 CDN 直链，`alt` 写中文描述，加 `loading="lazy"`：
  ```html
  <figure>
    <img src="https://cdn.example.com/xxx.png" alt="中文描述" loading="lazy">
    <figcaption>译成中文的图注</figcaption>
  </figure>
  ```
- **视频** → 用 `<video controls>` 外链原 mp4，可在页面内直接播放，加 `playsinline muted preload="metadata"`（避免自动下载整段）：
  ```html
  <figure>
    <video src="https://cdn.example.com/xxx.mp4" controls playsinline muted preload="metadata"></video>
    <figcaption>译成中文的视频说明</figcaption>
  </figure>
  ```

放置原则：
- **位置忠实**：媒体放在原文出现的相对位置，不要全堆到文末。
- **图注必译**：原文有 `figcaption` 就译成中文；原文无图注则用 `alt` 给出简短中文描述、可省略 `figcaption`。
- **顺序去重**：原文连续多张同主题图按顺序逐一放置，不合并、不漏放。
- **外链失效兜底**：若某条媒体直链取不到（反爬/需鉴权），退化为中文图注 + 「（见原文配图/视频）」并链接原文。

> 备注：当前默认外链原站 CDN（零存储、最省事）。若原站启用防盗链或删除资源，外链会失效；届时可改为下载到 `tech/assets/<slug>/` 本地托管（更稳但仓库变大、需注意转载版权）。

## 2.6 元信息填写

| 占位符 | 内容 |
|--------|------|
| `{{title_zh}}` | 中文译题（准确传达原题含义，可适度意译使其通顺） |
| `{{tag1}}`/`{{tag2}}` | 2 个领域标签（如 `AI 工程`、`Agent`） |
| `{{translator}}` | 默认 `Jackie Zhan` |
| `{{date}}` | 当前日期 `YYYY-MM-DD` |

---

# Step 3 — 输出与自检

## 3.1 文件命名

```
translation-[slug-title].html
```

`slug-title` 为原标题的英文小写连字符形式，3-5 个关键词。例如：
`translation-harness-design-long-running-apps.html`

## 3.2 输出目录

先写入当前工作目录。

## 3.3 自检清单

| # | 检查项 | 不通过的后果 |
|---|--------|------------|
| 1 | 出处信息卡完整（原标题/作者/来源/链接/日期） | 无法溯源 |
| 2 | 译文覆盖原文全部章节，无遗漏、无摘要化 | 内容缺失 |
| 3 | 无 `{{...}}` 占位符残留 | 页面显示占位符 |
| 4 | CSS 完整保留 | 排版错乱 |
| 5 | 术语全文一致 | 阅读混乱 |
| 6 | 代码块原样保留 | 代码失真 |
| 7 | 无明显翻译腔 | 阅读体验差 |
| 8 | 中文译题准确 | 标题误导 |
| 9 | 原文图片/视频已按位置嵌入（外链），图注译成中文 | 丢失关键视觉信息 |

---

# Step 4 — 同步到网站

## 4.1 复制文件

```bash
cp [文件名].html ~/github/yuanchu/yuanchu.ai/tech/
```

## 4.2 更新文章索引

读取 `~/github/yuanchu/yuanchu.ai/tech/index.html`，在 `.article-list` 的**最前面**插入新条目（标题前加「【译】」便于区分）：

```html
<a href="[文件名].html" class="article-item">
    <div class="article-title">【译】[中文译题]</div>
    <div class="article-meta">
        <span>译者：[译者]</span>
        <span>[日期]</span>
    </div>
</a>
```

## 4.3 完成提示

```
译文已生成并同步到 yuanchu.ai/tech/：
- 文件：tech/[文件名].html
- 索引：tech/index.html 已更新
- 原文：[原文链接]
- 预览：在浏览器打开文件即可查看
```
