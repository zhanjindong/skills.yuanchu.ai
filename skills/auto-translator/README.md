# 自动选译

自动选译工具会主动扫描一线大厂博客、行业分析、论文预印本、技术社区等高质量 AI 信息源，发现近期最值得翻译的技术文章，自动评分选出一篇，然后**调用 `translator` skill** 完成翻译并自动推送到 yuanchu.ai/tech/。

它专注做好一件事——「自动选题」，翻译与发布完全交给 `translator`。你不用自己找文章、不用贴链接，一句 `/auto-translator` 就能从信息源里淘出一篇好文并发布。因为翻译就是 translator 在干活，**译文的排版、出处信息卡、媒体外链、文件命名、发布流程与直接使用 translator 完全一致**。

## 使用场景

- 不知道翻什么时，让它从权威信息源自动挑一篇近期好文翻译
- 想定期给技术站点补充优质译文（可配合定时任务每天/每周自动跑）
- 限定方向（如「找篇 Agent 的」）或限定信息源（如「只看大厂博客」）后再自动选题

## 信息源

- **一线大厂博客**：OpenAI、Anthropic Engineering、Google DeepMind、Meta AI、Mistral AI
- **行业分析**：Sequoia AI、a16z AI、Artificial Analysis、Scale AI
- **论文 / 预印本**：arXiv（cs.AI/cs.CL/cs.LG）、Papers with Code、Hugging Face Blog
- **技术社区**：LangChain Blog、OpenAI Cookbook、AWS AI Blog

抓取时 RSS/Atom 优先，无 feed 则抓首页 HTML，失败再用 WebSearch 兜底。

## 特点

- **主动发现**：自动扫描多源近期条目，形成候选池，无需提供链接
- **自动选题**：按时效、影响力、技术深度、差异化、站点适配五维打分，自动锁定最高分
- **自动去重**：对照站点已有文章排除重复主题，避免重复翻译
- **全自动到底**：选题→调用 translator 翻译→发布一条龙，适合做成定时任务
- **翻译质量一致**：选定后调用 translator skill，逐字抓取、忠于原文、无翻译腔、结构保真、媒体外链，输出格式与直接用 translator 完全相同

## 输出格式

每次运行先输出一张候选榜（Top 3-5 + 五维分），再自动选定第 1 篇翻译，最终生成单文件 HTML 译文页面：

- 顶部「译文」标签与中文译题
- **原文出处信息卡**（原标题、作者、来源站点、原文链接、发布日期）
- 译者按语（可选）
- 与原文结构一一对应的中文正文（含外链的图片/视频）
- 底部版权声明

文件命名：`translation-[slug-title].html`，发布后同步到 `~/github/yuanchu/yuanchu.ai/tech/`，并在 `tech/index.html` 文章列表顶部插入带「【译】」前缀的条目。

## 与 translator 的区别

| | translator | auto-translator |
|---|-----------|-----------------|
| 输入 | 你提供链接/正文/PDF | 无需输入，自动从信息源发现 |
| 选题 | 你已经选好了 | 自动扫描 + 评分 + 选定 |
| 适合 | 已有明确想翻的文章 | 不知道翻什么、想定期补稿 |

已有明确链接时直接用 `/translator <URL>` 更快。
