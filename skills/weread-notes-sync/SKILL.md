---
name: 读书笔记同步
description: 从微信读书拉取阅读统计、全部书的划线与想法，生成书架列表页和每本书的笔记详情页（静态 HTML，风格对齐 yuanchu.ai），每条笔记可深链跳回微信读书 App 对应位置。当用户提到「更新读书笔记」「同步微信读书」「刷新读书页」「重新生成读书笔记」时触发，也适用于「sync weread notes」「update reading notes」等英文表达。
---

# 读书笔记同步 — 微信读书 → 静态站

把微信读书里「我」的阅读数据（阅读统计、划线、想法）拉下来，生成一组静态 HTML 页面：一个书架列表页 + 每本书一个笔记详情页，每条划线/想法都带深链可跳回微信读书 App 的精确位置。

## 前置条件

1. **API Key（必需，通过环境变量读取）**：微信读书 Agent API Gateway 的密钥，格式 `wrk-xxxx`。
   - 运行前必须设置：`export WEREAD_API_KEY=wrk-你的密钥`
   - 脚本只从环境变量 `WEREAD_API_KEY` 读取，**不接受**在命令行明文传入，**不得**写入任何文件或提交到仓库。
2. **Python 3**（标准库即可，无需第三方依赖）。
3. **输出目录**：目标网站的 `reading/` 目录（默认 `yuanchu.ai` 仓库下的 `reading/`）。

## 执行步骤

1. **检查密钥**：确认 `WEREAD_API_KEY` 已设置。若未设置，提示用户先 `export WEREAD_API_KEY=wrk-...`，不要继续。
2. **拉取数据**：在临时目录运行抓取脚本，生成中间数据 `weread_data.json`：
   ```bash
   python3 scripts/fetch_weread.py /tmp/weread_data.json
   ```
   脚本会拉取：阅读统计（`/readdata/detail`）、笔记本概览（`/user/notebooks`，自动翻页）、以及每本书的划线（`/book/bookmarklist`）和我的想法（`/review/list/mine`）。
3. **生成页面**：把数据渲染成静态站到目标 `reading/` 目录：
   ```bash
   python3 scripts/gen_site.py /path/to/yuanchu.ai/reading /tmp/weread_data.json
   ```
   产出：`reading/index.html`（书架封面网格 + 阅读统计）+ `reading/book-<bookId>.html`（每本书全部想法与划线）。
4. **自动提交并推送**（默认行为）：生成完成后，自动把 `reading/` 改动提交并推送到网站仓库，使其上线。
   ```bash
   cd /path/to/yuanchu.ai
   # 安全闸：确认没有把密钥混入将提交的文件，命中则中止
   grep -rl "wrk-" reading && echo "检测到密钥，已中止提交" && exit 1
   git add reading
   git diff --cached --quiet && echo "无变化，跳过提交" || git commit -m "读书笔记：自动同步微信读书内容"
   git pull --rebase && git push
   ```
   - 提交前**必须**先跑密钥检查（`grep -rl "wrk-" reading`），命中则中止、不提交。
   - 若 `reading/` 无变化（数据没更新），跳过提交，不产生空 commit。
   - 若用户明确说"先别提交 / 只生成不推送"，则跳过本步，仅停在本地改动。
5. **汇报结果**：告诉用户更新了多少本书、多少条划线/想法，以及是否已提交推送（含 commit 短哈希）。

## 关键实现细节

- **网络**：网关域名 `i.weread.qq.com`。脚本已内置「绕过系统代理 + 跳过 SSL 校验」，应对常见网络/证书环境。
- **请求格式**：`POST /api/agent/gateway`，body 里 `api_name` + 业务参数**平铺**（不要包在 `params` 内），每次必须带 `skill_version`。
- **深链**：每条划线/想法用官方精确定位格式
  `weread://bestbookmark?bookId=&chapterUid=&rangeStart=&rangeEnd=&userVid=`
  （`range` 形如 `"900-2004"`，按 `-` 拆成 start/end）。无 `range` 时自动降级到章节级 `weread://reading?bId=&chapterUid=`，再不行降到书级别。`userVid` 取自想法返回字段。
- **只读**：微信读书网关只提供读接口，本 skill 不会修改你的微信读书账号内容。
- **深链仅移动端生效**：`weread://` 是 App 私有协议，只在装了微信读书 App 的手机/iPad 上点击才会跳转，电脑浏览器点击无反应（属正常）。

## 自动化（可选）

可配 GitHub Action / cron 定时执行步骤 2–3 并自动提交，实现「读书笔记每日自动刷新」。密钥以仓库 Secret（`WEREAD_API_KEY`）注入，切勿明文写进工作流文件。
