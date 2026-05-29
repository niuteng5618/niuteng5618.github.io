---
layout: post
title: "Codex上下文压缩-compact"
date: 2026-05-16
primary_category: "人工智能技术"
secondary_category: "智能体应用开发"
series: "Claude Code / Codex"
categories:
  - 人工智能技术
  - 智能体应用开发
  - Claude Code / Codex
tags:
  - Claude Code / Codex
  - Codex
  - 上下文压缩
  - Compact
  - 开发工具
toc: true
comments: false
author: niuteng5618
---
## <font style="color:rgb(51, 51, 51);">1. 上下文压缩是什么</font>
<font style="color:rgb(51, 51, 51);">Codex 是长会话 agent。随着轮次增加，消息、工具调用、文件片段、推理摘要等都会占用上下文 token。接近阈值时，Codex 会触发 compaction：把旧历史总结成一个更短的摘要，并保留近期关键消息和工具结果。</font>

<font style="color:rgb(51, 51, 51);">这个过程不是无损压缩。它会尽量保留目标、约束、已完成操作、未完成事项、重要文件和命令结果，但细节一定会被裁剪。因此阈值太低会导致记忆过早丢细节，阈值太高会导致压缩来不及执行而触发上下文超限。</font>

## <font style="color:rgb(51, 51, 51);">2. 压缩方法</font>
> 这里本地压缩指的是，达到config.toml阈值后，调用本地模型进行总结，摘要；
>
> 远端压缩指的是，调用官方模型(gpt-5.5-openai-compact)进行压缩，个别中转站也提供官方的compact模型，需要单独设置。
>

### <font style="color:rgb(51, 51, 51);">2.1 本地 compaction</font>
<font style="color:rgb(51, 51, 51);">“本地”指 compaction 的编排发生在本机 Codex CLI 内：CLI 估算 token，构造压缩 prompt，然后通过当前配置的模型 provider 发起一次普通模型请求，拿到摘要后写回本地会话历史。</font>

<font style="color:rgb(51, 51, 51);">特点：</font>

+ <font style="color:rgb(51, 51, 51);">适合 API key 模式和自定义 OpenAI-compatible 网关。</font>
+ <font style="color:rgb(51, 51, 51);">使用当前 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">model_provider</font>`<font style="color:rgb(51, 51, 51);">、</font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">base_url</font>`<font style="color:rgb(51, 51, 51);">、</font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">wire_api</font>`<font style="color:rgb(51, 51, 51);">、</font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">model</font>`<font style="color:rgb(51, 51, 51);">。</font>
+ <font style="color:rgb(51, 51, 51);">依赖当前后端能正常处理 Responses API 请求。</font>
+ <font style="color:rgb(51, 51, 51);">token 和费用通常按一次额外模型调用计算。</font>
+ <font style="color:rgb(51, 51, 51);">不要求 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">auth.json</font>`<font style="color:rgb(51, 51, 51);"> 里有 ChatGPT token，API key 即可。</font>

<font style="color:rgb(51, 51, 51);">关键配置：</font>

```plain
model_context_window = 272000
model_auto_compact_token_limit = 220000
```

<font style="color:rgb(51, 51, 51);">含义：</font>

+ `<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">model_context_window</font>`<font style="color:rgb(51, 51, 51);">：告诉 Codex 当前模型可用上下文窗口。</font>
+ `<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">model_auto_compact_token_limit</font>`<font style="color:rgb(51, 51, 51);">：达到该估算 token 数后自动触发 compaction。</font>

<font style="color:rgb(51, 51, 51);">经验上，自动压缩阈值不要等于上下文窗口，建议放在 75% 到 85% 左右，给工具结果、系统消息、压缩请求本身留余量。</font>

### <font style="color:rgb(51, 51, 51);">2.2 远端 compaction</font>
<font style="color:rgb(51, 51, 51);">“远端”指 compaction 能力由 OpenAI/ChatGPT 侧服务或 Codex 远端协议完成，CLI 主要负责发起远端压缩请求和接收压缩结果，调用模型id一般为gpt-5.5-openai-compact.</font>

<font style="color:rgb(51, 51, 51);">特点：</font>

+ <font style="color:rgb(51, 51, 51);">更依赖官方 Codex/ChatGPT 服务端能力。</font>
+ <font style="color:rgb(51, 51, 51);">价格昂贵：</font>输入 **$112.5**/1M输出 **$675**/1M
+ <font style="color:rgb(51, 51, 51);">通常更适合 ChatGPT 登录态，而不是只有 API key 的自定义网关。</font>
+ <font style="color:rgb(51, 51, 51);">对自定义 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">base_url</font>`<font style="color:rgb(51, 51, 51);"> 的兼容性不如本地 compaction 可控。</font>
+ <font style="color:rgb(51, 51, 51);">可能受 Codex CLI 版本和 feature flag 影响。</font>

<font style="color:rgb(51, 51, 51);">当前 Codex CLI 0.131.0 中存在 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">remote_compaction_v2</font>`<font style="color:rgb(51, 51, 51);"> feature flag，但状态是 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">under development</font>`<font style="color:rgb(51, 51, 51);">，本机有效状态为 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">false</font>`<font style="color:rgb(51, 51, 51);">。因此本机当前没有启用远端 compaction v2。</font>

<font style="color:rgb(51, 51, 51);">可尝试配置：</font>

```plain
[features]
remote_compaction_v2 = true
```

<font style="color:rgb(51, 51, 51);">不建议在当前 API-key + 自定义 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">base_url</font>`<font style="color:rgb(51, 51, 51);"> 环境中优先启用它。若要验证远端 compaction v2，建议先升级 Codex CLI，并使用官方登录方式确认服务端支持。</font>

## <font style="color:rgb(51, 51, 51);">3. 本地压缩与远端压缩的区别</font>
| **<font style="color:rgb(51, 51, 51);">项目</font>** | **<font style="color:rgb(51, 51, 51);">本地 compaction</font>** | **<font style="color:rgb(51, 51, 51);">远端 compaction</font>** |
| :--- | :--- | :--- |
| <font style="color:rgb(51, 51, 51);">编排位置</font> | <font style="color:rgb(51, 51, 51);">本机 Codex CLI</font> | <font style="color:rgb(51, 51, 51);">OpenAI/ChatGPT 侧服务或远端协议</font> |
| <font style="color:rgb(51, 51, 51);">认证依赖</font> | <font style="color:rgb(51, 51, 51);">API key 即可</font> | <font style="color:rgb(51, 51, 51);">更依赖 ChatGPT/官方服务登录态</font> |
| <font style="color:rgb(51, 51, 51);">自定义网关兼容性</font> | <font style="color:rgb(51, 51, 51);">较好</font> | <font style="color:rgb(51, 51, 51);">不确定，取决于远端协议支持</font> |
| <font style="color:rgb(51, 51, 51);">可控性</font> | <font style="color:rgb(51, 51, 51);">高，可通过上下文窗口和阈值控制</font> | <font style="color:rgb(51, 51, 51);">低，受服务端和 feature flag 影响</font> |
| <font style="color:rgb(51, 51, 51);">成本模型</font> | <font style="color:rgb(51, 51, 51);">通常是一次额外模型请求</font> | <font style="color:rgb(51, 51, 51);">取决于远端服务实现和账户计划</font> |
| <font style="color:rgb(51, 51, 51);">当前本机状态</font> | <font style="color:rgb(51, 51, 51);">可用，走当前 provider</font> | `<font style="color:rgb(51, 51, 51);background-color:rgb(243, 244, 244);">remote_compaction_v2 = false</font>`<font style="color:rgb(51, 51, 51);">，未启用</font> |
