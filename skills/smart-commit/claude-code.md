# Smart Commit — Claude Code Slash Command

## 使用方法

在 Claude Code 中输入 `/smart-commit` 即可触发。

---

分析当前 git 暂存区（staged）的代码变更，生成符合 Angular Commit Convention 的 commit message。

## 步骤

1. 运行 `git diff --cached` 获取暂存区变更。如果暂存区为空，运行 `git diff` 获取工作区变更并提示用户先 stage。
2. 分析变更内容，确定：
   - **type**: 根据变更性质选择（feat/fix/refactor/docs/style/test/chore/perf/ci/build）
   - **scope**: 根据文件路径和变更模块确定影响范围，用简短词语表达
   - **description**: 用一句简洁的话描述变更的目的（不是过程）
3. 如果变更涉及多个不相关的改动，建议用户拆分提交，并为每个部分分别生成 message。
4. 生成格式：

```
type(scope): description

- bullet point details if needed
```

## 规则

- description 首字母小写，结尾不加句号
- 优先使用英文，除非用户明确要求中文
- 描述聚焦"为什么改"而非"改了什么文件"
- scope 应反映业务模块（如 auth, user, order），而非技术层级（如 controller, service）
- 单行 description 不超过 72 个字符
