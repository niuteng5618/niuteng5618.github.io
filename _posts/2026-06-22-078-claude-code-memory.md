---
layout: post
title: "Claude Code Memory 存储机制"
display_title: "Claude Code Memory 存储机制"
display_filename: "ClaudeCodeMemory存储机制.md"
date: 2026-06-22
primary_category: "智能体应用开发"
secondary_category: "AI 编程工具"
series: "Claude Code / Codex"
primary_category_order: 5
secondary_category_order: 3
series_order: 1
post_order: 78
categories:
  - 智能体应用开发
  - AI 编程工具
  - Claude Code / Codex
tags:
  - Claude Code / Codex
  - Claude Code
  - Memory
  - CLAUDE.md
  - Auto Memory
toc: true
comments: false
author: niuteng5618
---
# Claude Code Memory 存储机制

Claude Code 的 **Memory（记忆）** 有两条线：一条是你手写的 `CLAUDE.md` 指令文件，另一条是 Claude Code 自己维护的 **Auto Memory（自动记忆）**。这里重点讲真实 Claude Code 的 Auto Memory：它会把 Claude 在工作中总结出的构建命令、调试经验、架构笔记、代码风格偏好等内容保存到本地文件系统，供后续会话继续使用。

一句话理解：**Auto Memory 不是聊天历史，也不是项目源码的一部分，而是 Claude Code 在本机为某个仓库维护的 Markdown 记忆目录。**

------

## 一、真实存储路径

真实 Claude Code 的 Auto Memory 默认存储在：

```text
~/.claude/projects/<project>/memory/
```

这里的 `<project>` 由 Git 仓库路径派生。同一个 Git 仓库下的 worktree（工作树）和子目录会共享同一个 auto memory 目录；如果不在 Git 仓库中，则使用项目根目录派生路径。

以当前项目为例，项目根目录是：

```text
/home/white/Desktop/2-github/learn-claude-code
```

对应的 Claude Code 项目状态目录是：

```text
~/.claude/projects/-home-white-Desktop-2-github-learn-claude-code/
```

如果该项目已经生成 Auto Memory，真实路径通常是：

```text
~/.claude/projects/-home-white-Desktop-2-github-learn-claude-code/memory/
```

我检查了当前机器上的这个项目目录：项目状态目录存在，但目前没有 `memory/` 目录。这说明当前项目还没有生成 Auto Memory，或者 auto memory 没有触发、没有开启、没有提取到值得保存的内容。

这也解释了为什么你在项目根目录找不到 `.memory/`。`.memory/` 是当前学习项目 s09 demo 的教学版路径，不是真实 Claude Code 默认路径。

------

## 二、真实文件形式

官方文档描述的真实 Auto Memory 目录包含一个入口文件和若干 topic 文件：

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md
├── debugging.md
├── api-conventions.md
└── ...
```

**MEMORY.md** 是入口和索引。Claude Code 每次会话开始时会加载 `MEMORY.md` 的前 200 行或前 25KB，取两者中较小者。超过这个范围的内容不会在会话启动时加载。

**topic 文件** 是更详细的主题笔记，例如 `debugging.md`、`api-conventions.md`、`build.md`。这些文件不会在启动时全部加载，而是在 Claude 需要时用普通文件读取能力按需读取。

所以真实格式的关键不是"每条记忆一个固定 schema 文件"，而是：

- `MEMORY.md` 保持简洁，作为入口和索引。
- 详细内容拆到独立 Markdown topic 文件。
- 所有文件都是本机 plain markdown，可以直接阅读、编辑、删除。

s09 学习项目里使用 `.memory/MEMORY.md + .memory/*.md + YAML frontmatter` 是教学实现，用来解释"索引 + 记忆文件 + 元数据"的工程思想。真实 Claude Code 当前官方文档更强调 `MEMORY.md` 入口和 topic markdown 文件，不要求你手写 YAML frontmatter。

------

## 三、真实示例

假设当前仓库已经生成了 Auto Memory，目录可能长这样：

```text
~/.claude/projects/-home-white-Desktop-2-github-learn-claude-code/memory/
├── MEMORY.md
├── debugging.md
├── build-and-test.md
└── code-style.md
```

`MEMORY.md` 可能是一个很短的索引：

```markdown
# Memory

## Project overview

- This repository is a Claude Code learning project with staged examples from agent loop to memory, prompt assembly, recovery, and comprehensive agents.

## Useful topic files

- See debugging.md for recurring debugging patterns.
- See build-and-test.md for local run commands and environment notes.
- See code-style.md for user and project formatting preferences.
```

`debugging.md` 可能保存具体调试经验：

```markdown
# Debugging Notes

When investigating context compact behavior, start from `s08_context_compact/README.md` and `s08_context_compact/code.py`.

The teaching implementation uses character-count approximation for token pressure. Real Claude Code has a more precise context budgeting path.

For memory behavior, compare `s09_memory/README.md` with the official Claude Code memory docs because the teaching version intentionally uses a simplified `.memory/` directory.
```

`code-style.md` 可能保存偏好：

```markdown
# Code Style Preferences

Prefer concise Chinese technical notes for learning documents.

When writing Markdown notes in `_pre_docs`, keep the structure similar to existing files: title, short explanation, focused sections, examples, and a final summary.
```

这就是"真实示例"的重点：**Auto Memory 是一个本地 Markdown 目录，`MEMORY.md` 负责入口，详细笔记拆成 topic 文件。**

------

## 四、Memory 会不会写入 system prompt

要分清"存储"和"注入"。

Auto Memory 存在磁盘上，不是永久写死在某个 system prompt 文件里。每次会话开始时，Claude Code 会加载 `MEMORY.md` 的前 200 行或 25KB，并把它作为上下文提供给 Claude。topic 文件不会启动时全量加载，而是在需要时读取。

可以理解成：

```text
磁盘:
  ~/.claude/projects/<project>/memory/MEMORY.md
  ~/.claude/projects/<project>/memory/debugging.md
  ~/.claude/projects/<project>/memory/api-conventions.md

会话启动:
  加载 MEMORY.md 的前 200 行或 25KB

任务过程中:
  需要时读取 topic 文件
```

这和"每轮把所有 memory 全塞进 system prompt"不是一回事。真实机制更像是：**启动时给 Claude 一个简洁入口，细节按需读取。**

------

## 五、Memory 如何生成和维护

Auto Memory 默认开启。你可以在 `/memory` 中切换，也可以通过项目设置里的 `autoMemoryEnabled` 控制；也可以用环境变量 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` 禁用。

Claude 不会每个会话都保存记忆。它会判断某条信息是否对未来会话有用，例如：

- 构建命令和测试命令。
- 调试过程中的稳定发现。
- 项目架构和关键模块说明。
- 代码风格偏好。
- 用户反复纠正过的工作方式。

当你看到 Claude Code 界面出现 "Writing memory" 或 "Recalled memory" 时，说明它正在写入或读取 `~/.claude/projects/<project>/memory/` 下的文件。

你也可以运行 `/memory` 查看和编辑。Auto Memory 文件是普通 Markdown，可以直接打开、修改或删除。

------

## 六、和 CLAUDE.md 的区别

`CLAUDE.md` 和 Auto Memory 都会跨会话提供上下文，但职责不同。

| 机制 | 谁写 | 存什么 | 作用范围 | 加载方式 |
| --- | --- | --- | --- | --- |
| **CLAUDE.md** | 用户或团队 | 明确规则、工作流、项目约定 | 项目、用户、组织 | 每个会话加载 |
| **Auto Memory** | Claude Code | Claude 总结出的经验、偏好、调试线索 | 每个仓库，worktree 共享 | `MEMORY.md` 启动加载，topic 文件按需读取 |

如果你希望 Claude 必须长期遵守某条规则，比如"提交前必须运行某命令"，更适合写进 `CLAUDE.md` 或 hook。Auto Memory 更适合保存 Claude 在工作中逐渐学到的事实和模式。

------

## 七、为什么本地没有 `.memory/`

你在项目根目录没看到 `.memory/`，原因是：

- 真实 Claude Code 的 Auto Memory 默认不写在项目根目录。
- 默认路径是 `~/.claude/projects/<project>/memory/`。
- 当前学习项目的 `.memory/` 是 s09 demo 的教学路径。
- 只有运行 `python s09_memory/code.py`，教学版才会在项目根目录创建 `.memory/`。
- 真实 Claude Code 也不是每次对话都会生成 memory；只有它判断内容值得未来复用时才写入。

所以 `.memory/` 不存在不是异常。要看真实 Claude Code memory，应优先检查：

```text
~/.claude/projects/<project>/memory/
```

或者在 Claude Code 会话里运行：

```text
/memory
```

------

## 八、最终理解

真实 Claude Code Auto Memory 的核心是三句话：

- **存储路径**：`~/.claude/projects/<project>/memory/`
- **存储形式**：`MEMORY.md` 入口文件 + 若干 Markdown topic 文件
- **加载方式**：会话启动加载 `MEMORY.md` 前 200 行或 25KB，详细 topic 文件按需读取

当前学习项目的 `.memory/` 是 s09 为了教学做的简化实现。理解它有助于掌握 memory 的工程思想，但排查真实 Claude Code 时，要以 `~/.claude/projects/<project>/memory/` 和 `/memory` 命令为准。

------

参考资料：Claude Code 官方文档《How Claude remembers your project》：https://docs.anthropic.com/en/docs/claude-code/memory