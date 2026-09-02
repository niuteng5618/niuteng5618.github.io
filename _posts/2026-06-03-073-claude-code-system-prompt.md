---
layout: post
title: "Claude Code System Prompt 的运行时组装逻辑"
display_title: "Claude Code System Prompt 的运行时组装逻辑"
display_filename: "Claude Code System Prompt 的运行时组装逻辑.md"
date: 2026-06-03
primary_category: "智能体应用开发"
secondary_category: "AI 编程工具"
series: "Claude Code / Codex"
primary_category_order: 5
secondary_category_order: 3
series_order: 1
post_order: 73
categories:
  - 智能体应用开发
  - AI 编程工具
  - Claude Code / Codex
tags:
  - Claude Code / Codex
  - Claude Code
  - System Prompt
  - Prompt Cache
  - Agent
toc: true
word_count: 2572
reading_time: 7
comments: false
author: niuteng5618
---
# Claude Code System Prompt 的运行时组装逻辑

Claude Code 的 system prompt 不应理解为一段写死的大字符串，而应理解为**运行时由多个 section 组合出来的执行契约**。它的目标不是“把所有说明都塞给模型”，而是在每一轮请求中，精确提供当前 Agent 需要的身份、能力、约束和上下文。

## 核心思想

System prompt 的工程化原则是：

1. **分段维护**：不同职责进入不同 section，避免一处修改影响全局。
2. **按状态加载**：是否注入某段内容，取决于真实运行态，而不是关键词猜测。
3. **稳定优先**：稳定内容尽量保持顺序和文本不变，利于 prompt cache 命中。
4. **动态隔离**：易变内容放在动态边界之后，避免污染静态缓存。
5. **上下文最小化**：只加载当前任务必要的信息，减少噪声和 token 成本。


## Claude Code System Prompt 的主要 Section

Claude Code 中 section 数量不是固定值，会受模式、功能开关、工具集、MCP、用户配置、项目状态等影响，一些section静态插入，一些动态插入。可以按职责划分为以下几类。

### 1. Identity / Role

定义模型当前扮演的角色：它不是普通聊天助手，而是运行在开发环境中的 coding agent。

典型内容包括：

- 当前身份是什么
- 面向软件工程任务工作
- 可以读取、修改、运行、验证代码
- 需要主动完成任务，而不是只给建议

这一段通常属于稳定 section，几乎每轮都存在。

### 2. Core Behavior / Agent Contract

定义 Agent 的基本行为契约。

关注点包括：

- 任务未完成时继续推进
- 不要在可以行动时只解释
- 根据工具结果更新判断
- 失败后调整策略
- 完成后给出明确结果

这部分决定 Agent 的“工作方式”，不是某个具体工具的说明。

### 3. Tool Use

说明工具使用原则，而不是复制所有工具 schema。

工具 schema 通常通过 API 的 `tools` 参数传入；system prompt 中更关注高层规则：

- 什么时候应该用工具
- 工具结果如何进入下一轮判断
- 不要臆测文件内容、命令结果或环境状态
- 对破坏性操作保持谨慎
- 并行工具、后台任务、子 Agent 等能力的使用边界

换句话说，`tools` 参数告诉模型“有哪些工具”；tool-use section 告诉模型“应该如何使用工具”。

### 4. Workspace / Environment

描述当前工作环境。

常见内容包括：

- 当前工作目录
- 操作系统、shell、平台信息
- git 仓库状态
- 默认分支和当前分支
- 近期提交或工作区改动
- 运行环境限制

这类信息来自真实环境探测，不应由模型从用户话语中猜测。

### 5. Project Instructions

项目级指令通常来自 `CLAUDE.md`、项目配置、仓库约定或用户持久偏好。

它解决的问题是：

- 当前项目如何构建、测试、发布
- 代码风格和命名约定
- 哪些目录不能动
- 哪些命令危险或需要确认
- 团队偏好的工作流程

这部分属于“项目知识”，不是模型通用能力。它应独立于核心身份 section，便于按项目切换和缓存管理。

### 6. Memory

Memory section 注入跨会话保留的信息。

它通常不是完整记忆库，而是经过选择后的相关记忆，例如：

- 用户长期偏好
- 项目长期约束
- 已确认的工作方式
- 外部资源入口

关键点：memory 应该**选择性注入**。把所有记忆全部放入 system prompt 会降低精度，并增加冲突风险。

### 7. Skills / Commands

Skill 不会在启动时把所有 `SKILL.md` 全文注入。更专业的方式是两级加载：

1. 启动时只注入技能目录：`name + description`
2. 需要时再加载完整 skill 内容

因此 system prompt 里通常只出现“有哪些 skill 可用、何时使用”的目录信息。完整技能说明进入上下文，应由模型显式触发加载。

这避免了把大量低频专业知识长期占据上下文。

### 8. MCP Instructions

MCP server 会带来外部工具、资源和提示。由于 MCP 连接可能在会话中变化，MCP 相关 section 通常更动态。

其内容可能包括：

- 当前连接了哪些 MCP server
- 暴露了哪些外部能力
- 资源访问方式
- 特定 server 的使用约束

这类 section 易变，不适合和稳定核心 prompt 绑定在同一缓存块中。

### 9. Output Style / Response Policy

控制输出形式。

常见约束包括：

- 回答简洁还是详细
- 是否使用 Markdown
- 是否引用文件路径和行号
- 代码修改后的汇报格式
- 是否避免无意义总结
- 是否优先给 CLI 命令

Output style 不是模型身份，而是当前交互界面的表达协议。

### 10. Context Management

Claude Code 需要处理长会话，所以 system prompt 还会包含上下文管理相关指令。

典型逻辑包括：

- 何时压缩上下文
- 如何处理大工具输出
- 哪些信息应保留
- 哪些历史可以摘要
- 如何避免把无关日志长期留在上下文中

这部分让 Agent 在长任务中保持可控，而不是被历史噪声淹没。

### 11. Safety / Permission Model

安全和权限不会只依赖 prompt，但 prompt 会描述模型应如何配合 harness 的权限系统。

例如：

- 修改文件前理解上下文
- 删除、覆盖、发布、推送等操作需要谨慎
- 外部服务调用具有副作用
- 不绕过用户确认
- 不把 hook 或配置当成绝对授权

真正的权限判断应由 harness 执行；system prompt 负责让模型形成正确行为倾向。

## Static Section 与 Dynamic Section

Claude Code 的专业点在于：它不是简单拼接字符串，而是区分稳定内容和易变内容。

### 顺序有意义：静态在前，动态在后

静态 prompt 和动态 prompt 不是随意拼接，顺序有工程意义。更合理的结构是：

```text
静态 section
  ↓
动态边界
  ↓
动态 section
```

静态 section 放在前面，主要有三层作用：

1. **提高 prompt cache 命中率**：API 级 prompt cache 通常更容易复用稳定前缀。身份、行为契约、工具使用原则等内容如果长期保持在前缀位置，就能在不同轮次、不同任务中复用。动态内容如果放在前面，每次 git 状态、memory、MCP 状态变化都会污染前缀，降低缓存收益。
2. **隔离易变信息**：动态 section 放在边界之后，当前目录、项目状态、memory、MCP instructions、token budget 等变化不会影响静态核心块。
3. **建立解释优先级**：模型先看到稳定的角色、边界和行为契约，再看到当前环境信息。这样动态上下文是在核心规则下被解释，而不是反过来让临时状态改写 Agent 的基本行为。

因此，静态在前不只是为了省 token，也是在维护 system prompt 的稳定语义结构：**先定义 Agent 是什么，再描述 Agent 当前身处什么环境。**

### Static Section

静态 section 通常包括：

- identity
- core behavior
- tool-use general policy
- tone / output efficiency
- 基础 agent contract

这些内容变化少，适合放入稳定缓存块。

### Dynamic Section

动态 section 通常包括：

- 当前目录和环境
- git 状态
- memory 选择结果
- CLAUDE.md / 项目指令
- MCP 连接信息
- output style
- token budget
- 当前模式或 feature flag

这些内容可能随会话、项目、工具状态变化，因此应和静态 prompt 分离。

核心收益：**动态内容变化时，不让整个 system prompt 的缓存全部失效。**

## System Context 与 User Context 的区别

Claude Code 中并非所有“系统提醒”都直接属于 system prompt。

可以粗略分为：

| 类型 | 作用 | 注入方式 |
|---|---|---|
| System Context | 描述运行环境、工具契约、核心行为 | system prompt sections |
| User Context | 当前日期、项目提醒、CLAUDE.md、git 状态等上下文提示 | 常以 system-reminder 形式进入消息流 |

这种区分很重要：

- system prompt 更像稳定协议
- user-context reminder 更像当前轮的环境观测

不要把所有信息都塞进 system prompt；不同生命周期的信息应进入不同通道。

## 运行时组装流程

专业实现可以抽象为：

```text
读取基础配置
  ↓
探测当前环境和项目状态
  ↓
加载用户 / 项目指令
  ↓
扫描可用工具、skills、MCP
  ↓
选择需要的 section
  ↓
按稳定顺序组装
  ↓
在静态 / 动态边界处分块
  ↓
发送给模型
```

这里最重要的是“选择 section 的依据”。

好的逻辑应基于真实状态：

- 工具是否实际注册
- MCP 是否实际连接
- memory 是否被选中
- 项目指令文件是否存在
- 当前模式是否启用
- token 预算是否变化

而不是基于用户消息里是否出现某个关键词。

## 为什么不能硬编码

硬编码 system prompt 的问题不在于“字符串长”，而在于它破坏了可维护性：

1. **职责混杂**：身份、工具、记忆、项目规则混在一起。
2. **冲突难定位**：新增一段指令可能影响远处行为。
3. **缓存不稳定**：动态内容变化导致整体缓存失效。
4. **项目不可迁移**：换仓库后难以判断哪些内容该保留。
5. **上下文噪声大**：低频能力长期污染高频任务。

所以 system prompt 应该被看作配置产物，而不是手写常量。

## 设计准则

构建 Agent harness 时，可以遵循以下准则：

- 核心身份稳定，项目上下文动态
- 工具能力由真实注册表生成
- skill 只先暴露目录，按需加载全文
- memory 必须筛选后注入
- MCP section 单独处理，避免污染静态缓存
- section 顺序保持确定性
- 高风险规则交给权限系统兜底，不只依赖 prompt
- prompt 只描述行为契约，不承载所有业务知识

## 总结

Claude Code 的 system prompt 不是“提示词技巧”，而是 harness 的运行时配置层。

它把 Agent 的身份、工具原则、工作环境、项目规则、记忆、技能、MCP、输出风格和安全约束拆成独立 section，再根据当前状态组装。

这就是“system prompt 运行时组装，而不是硬编码”的核心。
