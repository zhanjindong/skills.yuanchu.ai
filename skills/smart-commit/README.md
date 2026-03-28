# 智能提交

智能提交是一个智能 Git 提交消息生成工具。它会分析你的代码变更（git diff），理解修改的意图和范围，然后自动生成符合 Angular Commit Convention 规范的 commit message。

## 使用场景

- 日常开发中快速生成规范的提交消息，省去手动组织语言的时间
- 团队协作时保持提交消息风格统一，便于代码审查和变更追踪
- 在大型项目中自动识别变更涉及的模块，准确填写 scope 字段

## 特点

- **规范驱动**: 严格遵循 `type(scope): description` 格式，支持 feat/fix/refactor/docs/test/chore 等类型
- **上下文感知**: 不仅分析 diff 内容，还会参考文件路径、函数名等上下文信息，生成更准确的描述
- **多语言支持**: 可根据配置生成中文或英文的提交消息
- **批量变更处理**: 当一次提交涉及多个文件时，能够归纳出统一的变更主题，而非简单罗列文件名

## 输出格式

```
type(scope): concise description

- detail 1
- detail 2
```

支持的 type: feat, fix, docs, style, refactor, test, chore, perf, ci, build
