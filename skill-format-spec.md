# Agent Skill 格式规格对比：Claude Code / OpenClaw / Codex

本文档详细描述三个主流 AI Agent 平台的 Skill 定义格式，便于开发者编写跨平台兼容的 Skill。

---

## 一、总览

三个平台都采用 **SKILL.md**（YAML frontmatter + Markdown 正文）作为 Skill 的核心定义文件，但在扩展配置、依赖管理和目录结构上各有不同。

| 特性 | Claude Code | OpenClaw (龙虾) | Codex (OpenAI) |
|------|------------|-----------------|----------------|
| 核心文件 | `SKILL.md` | `SKILL.md` | `SKILL.md` |
| Frontmatter 字段 | `name` + `description` | `name` + `description` + `metadata` | `name` + `description` |
| 扩展配置 | 无 | frontmatter 内 `metadata` | 单独 `agents/openai.yaml` |
| 依赖声明 | 无 | `metadata.openclaw.requires` | `openai.yaml → dependencies` |
| UI 定制 | 无 | `metadata.openclaw.emoji` | `openai.yaml → interface` |
| 安装指引 | 无 | `metadata.openclaw.install` | 无 |
| Skill 目录 | `~/.claude/skills/` | npm 全局包 `skills/` + `extensions/` | `.agents/skills/`（多级扫描） |

---

## 二、Claude Code

### 2.1 目录结构

```
my-skill/
├── SKILL.md          # 必需
└── assets/           # 可选，模板等资源
```

Skill 安装位置：

```
~/.claude/skills/<skill-name>/SKILL.md
```

### 2.2 SKILL.md 格式

Frontmatter 只需 `name` 和 `description` 两个字段，正文为 Markdown 格式的指令。

```yaml
---
name: skill-name
description: "Skill 的用途描述，用于判断何时触发该 Skill。"
---

# Skill 标题

这里是 Skill 的具体指令内容，使用 Markdown 格式编写。
Agent 会按照这里的指令执行任务。
```

### 2.3 完整示例

```yaml
---
name: stock-analysis
description: "股票投资分析助手：综合多方面因素分析股票走势，生成精简的HTML投资分析报告。"
---

# 股票投资分析助手

你是一位专业的股票投资分析师，任务是综合多方面因素分析股票走势。

## 分析框架

### 一、操作建议（第一时间给出）
- ✅ **买入** - 强烈推荐
- ➡️ **持有/观望** - 继续持有
- ❌ **卖出** - 建议卖出

### 二、基本面
- 营收/利润增长情况
- PE估值（历史分位）

### 三、技术面
- MACD：金叉/死叉/零轴位置
- KDJ：超买/超卖
```

### 2.4 特点

- **最简洁**：无依赖管理、无 UI 配置、无安装指引
- Skill 的触发完全依赖 `description` 字段的语义匹配
- 支持 `assets/` 目录存放 HTML 模板等资源文件

---

## 三、OpenClaw (龙虾)

### 3.1 目录结构

```
my-skill/
├── SKILL.md          # 必需
├── scripts/          # 可选，可执行脚本
├── references/       # 可选，参考文档
└── assets/           # 可选，模板和资源
```

Skill 安装位置（npm 全局包内）：

```
<npm-global>/openclaw/skills/<skill-name>/SKILL.md        # 内置 Skill
<npm-global>/openclaw/extensions/<ext-name>/skills/        # 扩展 Skill
```

### 3.2 SKILL.md 格式

在 `name` 和 `description` 基础上，增加了 `metadata` 字段（可选 `homepage` 字段）。

```yaml
---
name: skill-name
description: "Skill 用途描述，明确说明何时使用、何时不使用。"
homepage: https://example.com          # 可选
metadata:
  openclaw:
    emoji: "🔧"                        # UI 展示图标
    requires:                           # 依赖声明
      bins: ["curl"]                    # 需要的命令行工具
      config: ["channels.slack"]        # 需要的配置项
    install:                            # 安装指引
      - id: "brew"
        kind: "brew"
        formula: "curl"
        bins: ["curl"]
        label: "Install curl (brew)"
      - id: "apt"
        kind: "apt"
        package: "curl"
        bins: ["curl"]
        label: "Install curl (apt)"
---

# Skill 标题

Skill 的具体指令内容。
```

### 3.3 metadata 字段详解

| 字段 | 类型 | 说明 |
|------|------|------|
| `openclaw.emoji` | string | Skill 在 UI 中显示的 emoji 图标 |
| `openclaw.requires.bins` | string[] | 依赖的命令行工具列表 |
| `openclaw.requires.config` | string[] | 依赖的配置项列表 |
| `openclaw.install` | object[] | 安装方式声明（支持 brew/apt 等） |
| `openclaw.install[].id` | string | 安装方式标识 |
| `openclaw.install[].kind` | string | 安装方式类型（`brew` / `apt`） |
| `openclaw.install[].formula` / `package` | string | 包名 |
| `openclaw.install[].bins` | string[] | 安装后提供的可执行文件 |
| `openclaw.install[].label` | string | UI 展示的安装按钮文字 |

### 3.4 完整示例

```yaml
---
name: github
description: "GitHub operations via gh CLI: issues, PRs, CI runs, code review, API queries."
metadata:
  openclaw:
    emoji: "🐙"
    requires:
      bins: ["gh"]
    install:
      - id: "brew"
        kind: "brew"
        formula: "gh"
        bins: ["gh"]
        label: "Install GitHub CLI (brew)"
      - id: "apt"
        kind: "apt"
        package: "gh"
        bins: ["gh"]
        label: "Install GitHub CLI (apt)"
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub repositories, issues, PRs, and CI.

## When to Use

✅ **USE this skill when:**
- Checking PR status, reviews, or merge readiness
- Viewing CI/workflow run status and logs
- Creating, closing, or commenting on issues

## When NOT to Use

❌ **DON'T use this skill when:**
- Local git operations → use `git` directly
- Non-GitHub repos → different CLIs

## Common Commands

### Pull Requests

```bash
gh pr list --repo owner/repo
gh pr checks 55 --repo owner/repo
gh pr create --title "feat: add feature" --body "Description"
```
```

### 3.5 特点

- **依赖管理最完善**：可声明 bins/config 依赖，并提供多平台安装指引
- `metadata` 嵌套在 frontmatter 内，无需额外文件
- 支持 `scripts/`、`references/`、`assets/` 子目录

---

## 四、Codex (OpenAI)

### 4.1 目录结构

```
my-skill/
├── SKILL.md              # 必需
├── scripts/              # 可选，确定性操作脚本
├── references/           # 可选，长文档参考
├── assets/               # 可选，模板和资源
└── agents/
    └── openai.yaml       # 可选，UI 和行为配置
```

Skill 扫描路径（按优先级）：

```
$CWD/.agents/skills/              # 当前工作目录
$REPO_ROOT/.agents/skills/        # 仓库根目录（向上逐级扫描）
$HOME/.agents/skills/             # 用户级
/etc/codex/skills/                # 系统级
内置系统 skills                    # Codex 自带
```

### 4.2 SKILL.md 格式

Frontmatter 与 Claude Code 相同，只需 `name` 和 `description`。

```yaml
---
name: skill-name
description: "Skill 用途描述，决定隐式触发的时机。"
---

# Skill 标题

Skill 的具体指令内容。
```

### 4.3 agents/openai.yaml 配置

扩展配置通过单独的 YAML 文件管理，分为三个部分：

```yaml
# UI 展示配置
interface:
  display_name: "用户可见名称"
  short_description: "简短描述"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "可选的默认提示词"

# 行为策略
policy:
  allow_implicit_invocation: true    # 是否允许根据用户输入自动触发（默认 true）

# 工具依赖
dependencies:
  tools:
    - type: "mcp"
      value: "toolIdentifier"
      description: "工具描述"
      transport: "streamable_http"
      url: "https://example.com"
```

### 4.4 openai.yaml 字段详解

#### interface（UI 展示）

| 字段 | 类型 | 说明 |
|------|------|------|
| `display_name` | string | 用户可见的 Skill 名称 |
| `short_description` | string | 简短描述 |
| `icon_small` | string | 小图标路径（SVG） |
| `icon_large` | string | 大图标路径（PNG） |
| `brand_color` | string | 品牌色（HEX） |
| `default_prompt` | string | 默认提示词上下文 |

#### policy（行为策略）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `allow_implicit_invocation` | boolean | `true` | 是否允许根据语义自动触发 |

#### dependencies（工具依赖）

| 字段 | 类型 | 说明 |
|------|------|------|
| `tools[].type` | string | 工具类型（如 `mcp`） |
| `tools[].value` | string | 工具标识符 |
| `tools[].description` | string | 工具描述 |
| `tools[].transport` | string | 传输协议（如 `streamable_http`） |
| `tools[].url` | string | 工具服务地址 |

### 4.5 完整示例

**SKILL.md:**

```yaml
---
name: deploy-helper
description: "Assist with deployment tasks: checking CI status, triggering deploys, and rollbacks. Use when user mentions deploy, release, or rollback."
---

# Deploy Helper

Help users manage deployments safely.

## Capabilities

- Check CI pipeline status before deploy
- Trigger deployment to staging/production
- Monitor deployment progress
- Execute rollback if needed

## Workflow

1. Verify all CI checks pass
2. Confirm target environment with user
3. Trigger deployment
4. Monitor and report status
```

**agents/openai.yaml:**

```yaml
interface:
  display_name: "Deploy Helper"
  short_description: "Manage deployments and rollbacks"
  icon_small: "./assets/deploy-icon.svg"
  brand_color: "#10B981"

policy:
  allow_implicit_invocation: true

dependencies:
  tools:
    - type: "mcp"
      value: "ci-status"
      description: "Check CI pipeline status"
      transport: "streamable_http"
      url: "https://ci.example.com/mcp"
```

### 4.6 Skill 调用方式

- **显式调用**：输入 `$skill-name` 或在 CLI 中输入 `/skills` 选择
- **隐式调用**：Codex 根据用户输入语义自动匹配（可通过 `allow_implicit_invocation: false` 关闭）

### 4.7 特点

- **配置分离**：SKILL.md 专注指令，openai.yaml 管理元数据
- **多级扫描**：从当前目录到系统级，灵活的 Skill 发现机制
- **UI 定制最丰富**：支持图标、品牌色等视觉配置
- **MCP 工具依赖**：可声明对 MCP 工具服务的依赖

---

## 五、跨平台兼容建议

如果希望编写一个兼容三个平台的 Skill，建议：

1. **SKILL.md 只使用 `name` + `description`**：这是三个平台的公共子集
2. **正文使用标准 Markdown**：三个平台都支持
3. **平台特定配置单独管理**：
   - OpenClaw：在 frontmatter 中添加 `metadata`
   - Codex：添加 `agents/openai.yaml`
   - Claude Code：无需额外配置
4. **推荐的兼容目录结构**：

```
my-skill/
├── SKILL.md              # 三平台通用（仅 name + description frontmatter）
├── assets/               # 三平台通用
├── scripts/              # OpenClaw + Codex 支持
├── references/           # OpenClaw + Codex 支持
└── agents/
    └── openai.yaml       # Codex 专用配置
```

5. **最小兼容模板**：

```yaml
---
name: my-skill
description: "清晰描述 Skill 的用途、触发条件和不适用场景。"
---

# My Skill

## 概述

简要说明 Skill 的功能。

## 使用场景

- 场景 1
- 场景 2

## 指令

具体的执行指令和步骤。
```
