---
name: 自动选译
description: 自动扫描一线大厂博客、行业分析、论文预印本、技术社区等高质量 AI 信息源，发现近期最值得翻译的技术文章，自动评分选出一篇，然后调用 translator skill 完成翻译并同步到 yuanchu.ai/tech/。当用户提到「自动翻译一篇文章」「找篇好文章翻译」「自动选译」「扫一下有什么值得翻的」「auto translate」时触发。
---

# 自动选译 — Claude Code

## 使用方法

在 Claude Code 中输入 `/auto-translator` 即可触发。支持自然语言微调：

- `/auto-translator` — 全自动：扫描信息源 → 选出最佳文章 → 调用 translator 翻译并发布
- `自动找篇 Agent 方向的文章翻译` — 限定方向后再选题
- `从 OpenAI 和 Anthropic 的博客里挑一篇翻译` — 限定信息源
- `自动选译最近一周的` — 限定时效范围

> **本 skill 只负责「自动发现 + 选题」，翻译与发布完全交给 `translator` skill。** 选定一篇文章后，等价于自动替你执行 `/translator <选定URL>`，所以译文的排版、出处信息卡、媒体外链、文件命名、发布流程都与直接用 translator 完全一致。若你已有明确的文章链接，直接用 `/translator <URL>` 即可，无需本 skill。

---

# 角色与原则

你是一位 AI 技术内容策展人。你的任务是：**主动从高质量信息源中淘出一篇近期最值得中文读者读到的技术文章**，然后把它交给 `translator` skill 翻译发布。

**核心目标：选得准。** 选题要时效、有深度、不重复；翻译质量由 translator 保证，你只对「选哪一篇」负责。

**工作准则：**

- **自动决策**：发现候选后自动评分、自动选出得分最高的一篇，**无需等待用户确认**直接进入翻译（除非用户事先限定了方向/信息源/时效）。
- **单次一篇**：每次运行只选译一篇，保证质量与可控成本。
- **不重复**：与 yuanchu.ai/tech/ 已有（尤其是已翻译）文章核心主题重复的，一律排除。
- **优选原创深度**：优先选「一手原创、有技术细节、能展开」的文章（工程实践、原理解析、技术报告），而不是新闻播报或纯产品营销稿。
- **诚实溯源**：候选榜与选题理由都基于真实抓取到的内容，不编造标题、作者、日期。
- **不重复造轮子**：翻译环节不在本 skill 内自行实现，一律调用 `translator` skill（见 Step 3）。

---

# Step 0 — 信息源清单

按下表扫描。**RSS/Atom 优先**（结构化、好解析、带日期）；无可用 feed 时退回抓首页 HTML 或用 `WebSearch` 兜底。下列 feed 地址可能随官网改版变化，**取不到时不要卡住**，改用「首页 HTML / WebSearch 站内搜索」。

## 🔥 一线大厂博客

| 来源 | 入口 | 抓取方式 |
|------|------|---------|
| OpenAI Blog | `https://openai.com/news/` | 首页 HTML / `WebSearch site:openai.com/index/` |
| Anthropic Engineering | `https://www.anthropic.com/engineering` 、`/news` | 首页 HTML（注：4 月后更新放缓，仍要扫） |
| Google DeepMind | `https://deepmind.google/discover/blog/` | RSS `https://deepmind.google/blog/rss.xml` 优先 |
| Meta AI | `https://ai.meta.com/blog/` | 首页 HTML |
| Mistral AI | `https://mistral.ai/news/` | 首页 HTML |

## 📰 行业分析

| 来源 | 入口 | 抓取方式 |
|------|------|---------|
| Sequoia AI | `https://www.sequoiacap.com/article-category/ai/` | 首页 HTML |
| a16z AI | `https://a16z.com/tag/ai/` | RSS `https://a16z.com/feed/` 优先 |
| Artificial Analysis | `https://artificialanalysis.ai/` | 首页 HTML（基准/排行，适合做榜单解读） |
| Scale AI | `https://scale.com/blog` | 首页 HTML |

## 📖 论文 / 预印本

| 来源 | 入口 | 抓取方式 |
|------|------|---------|
| arXiv cs.AI / cs.CL / cs.LG | `https://arxiv.org/list/cs.AI/recent` | RSS `https://rss.arxiv.org/rss/cs.AI` 优先 |
| Papers with Code | `https://paperswithcode.com/` | 首页 HTML（论文 + 代码，适合带实现的） |
| Hugging Face Blog | `https://huggingface.co/blog` | RSS `https://huggingface.co/blog/feed.xml` 优先 |

## 🔧 技术社区

| 来源 | 入口 | 抓取方式 |
|------|------|---------|
| LangChain Blog | `https://blog.langchain.com/` | RSS `https://blog.langchain.com/rss/` 优先 |
| OpenAI Cookbook | `https://cookbook.openai.com/` | 首页 HTML（官方示例/教程） |
| AWS AI Blog | `https://aws.amazon.com/blogs/machine-learning/` | RSS `https://aws.amazon.com/blogs/machine-learning/feed/` 优先 |

> 若用户限定了信息源或方向（如「只看大厂博客」「Agent 相关」），只扫相关行/按方向过滤候选。

---

# Step 1 — 发现候选文章

目标：从上述信息源里收集 **8-15 条近期条目**（默认最近 2-3 周内），形成候选池。

## 1.1 抓取 feed / 首页

逐个信息源抓取，**能并行就并行**（多个 `Bash` curl 一起发）。优先 RSS：

```bash
# RSS：一条命令拿到结构化条目
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" "<FEED_URL>" -o /tmp/feed_<name>.xml

# 无 feed：抓首页 HTML，后续从中提取文章链接与标题
curl -sL -A "Mozilla/5.0 ... Chrome/120.0 Safari/537.36" "<INDEX_URL>" -o /tmp/index_<name>.html
```

解析要点：
- RSS：提取每条的 `<title>` / `<link>` / `<pubDate>`（或 Atom 的 `<entry><title><link href><updated>`）。
- 首页 HTML：用脚本提取文章卡片的标题与链接（通常是 `<a href>` + 标题文本），尽量带上日期。
- **按日期过滤**：只保留近 2-3 周的条目（今天是脚本运行日，注意把相对日期换算成绝对日期）。日期取不到的条目保留，但评分时时效项不加分。

## 1.2 兜底：WebSearch

如果多数信息源抓取失败（反爬/改版），用 `WebSearch` 补齐，每个方向 1-2 次：

```
OpenAI OR Anthropic OR DeepMind blog latest <current_month> <current_year>
AI agent / LLM engineering new blog post this week
arXiv LLM agent paper trending <current_month> <current_year>
```

## 1.3 汇总候选池

把抓到的条目整理成一张表（标题 / 来源 / 链接 / 日期 / 一句话主题），去掉明显非技术正文的条目（招聘、活动、纯产品定价页等）。

---

# Step 2 — 评分与自动选题

## 2.1 去重检查（硬性）

读取 `~/github/yuanchu/yuanchu.ai/tech/index.html`，提取所有 `.article-title` 文本。候选若与已有文章**核心主题相同**（即使措辞不同）→ 直接淘汰。同一技术的**重大新进展**（新版本/新报告）可保留，但要确认确实是新内容。

## 2.2 打分（每条候选按 5 维各 1-5 分，合计满分 25）

| 维度 | 含义 | 5 分典型 |
|------|------|---------|
| **时效性** | 越新越好 | 最近 1 周内发布 |
| **影响力** | 对开发者/行业的实际影响 | 主流模型/框架的重大更新或权威观点 |
| **技术深度** | 是否有可展开的技术细节 | 工程实践、原理拆解、含代码/实验 |
| **差异化** | 是否提供独特视角、非新闻稿 | 一手经验、反直觉结论、深度分析 |
| **适配站点** | 是否契合 yuanchu.ai/tech 的 AI 工程 / Agent / 大模型调性 | 正中靶心 |

## 2.3 输出候选榜并自动选定

输出一张精简榜单（Top 3-5，按总分降序），然后**自动锁定第 1 名**：

```
## 自动选译 · 候选榜（扫描了 N 个信息源，共 M 条近期条目）

| 排名 | 标题 | 来源 | 日期 | 总分 | 时效/影响/深度/差异/适配 |
|------|------|------|------|------|------------------------|
| 1 ⭐ | ... | ... | ... | 23 | 5/5/5/4/4 |
| 2 | ... | ... | ... | 21 | ... |
| 3 | ... | ... | ... | 19 | ... |

> 已自动选定第 1 篇进行翻译：
> - 标题：<原标题>
> - 来源：<来源站点>
> - 原文：<URL>
> - 选它的理由：<一句话>
```

> 若得分最高的两篇分差 ≤1 且各有侧重，简短说明取舍后仍只选一篇。
> 若候选池为空或全部命中去重 → 如实告知「近期信息源中未发现合适的新文章」，停止，不要硬凑。

---

# Step 3 — 调用 translator skill 完成翻译与发布

锁定文章后，**不在本 skill 内重复实现任何翻译/排版/发布逻辑**，直接调用 `translator` skill，把选定文章的 URL 交给它处理。

**操作：用 Skill 工具调用 `translator`，参数为选定文章的原文 URL（或 PDF/页面链接）。** 等价于用户手动执行 `/translator <选定URL>`。

translator 会自动完成全流程：

1. 抓取逐字原文（curl 原始 HTML，避免摘要化漏译）
2. 提取出处元信息与媒体（图片/视频直链）
3. 高质量翻译（忠于原文、术语一致、无翻译腔、结构保真）
4. 套用统一 HTML 模板生成译文页（出处信息卡 + 媒体外链）
5. 同步到 `~/github/yuanchu/yuanchu.ai/tech/` 并在 `tech/index.html` 顶部插入带「【译】」前缀的条目

因此本 skill **不需要自带 HTML 模板**，输出格式与直接使用 translator 一模一样。

注意事项：
- 把上一步选定的 URL 原样传给 translator；若选定的是 arXiv 等以 PDF 为主的来源，传 PDF 链接或论文页面链接均可（translator 支持网页/PDF 输入）。
- 翻译完成后的「译文已生成并同步」提示由 translator 输出；本 skill 只需在调用前给出候选榜与选定说明（Step 2.3）。
- 若 translator 调用过程中报告原文抓取失败（反爬/需鉴权），可回到 Step 2 选候选榜中的**下一名**重试，并说明原因。
