---
layout: post
title: "MCP 支持哪些传输协议？通俗讲解"
display_title: "MCP 支持哪些传输协议？通俗讲解"
display_filename: "MCP传输协议区别联系？.md"
date: 2026-06-03
primary_category: "智能体应用开发"
secondary_category: "Agent 工具链"
series: "MCP"
primary_category_order: 5
secondary_category_order: 1
series_order: 2
post_order: 74
categories:
  - 智能体应用开发
  - Agent 工具链
  - MCP
tags:
  - MCP
  - Streamable HTTP
  - SSE
  - stdio
  - JSON-RPC
toc: true
word_count: 1932
reading_time: 5
comments: false
author: niuteng5618
---
## 🗂️ MCP 支持哪些传输协议？——通俗讲解

### 一、先理解一个比喻：快递是怎么送的？

MCP（Model Context Protocol）是 AI 和工具之间通信的"规则"，但光有规则还不够，还需要选择**运输方式**，就像快递可以用摩托车、货车、飞机来运，这在 MCP 里叫 **Transport（传输层）**。

目前 MCP 官方支持两种正式传输方式，另有一种已被弃用：

------

### 二、三种传输方式逐一解释

#### 🟢 1. stdio（标准输入输出）

**生活比喻：** 就像两个人面对面用纸条传话。

客户端把 MCP Server 当作一个**子进程**启动，Server 从 `stdin`（标准输入）读取消息，从 `stdout`（标准输出）发送消息，消息格式是 JSON-RPC，每行一条。

- ✅ 适合：**本地运行**，比如你在自己电脑上用 Claude Desktop 调用本地工具
- ✅ 简单、零网络开销
- ❌ 缺点：只能本地用，无法跨网络

------

#### 🔴 2. HTTP+SSE（旧版，已弃用）

**生活比喻：** 你打了两部手机——一部专门接电话（收服务器消息），一部专门打出去（发请求给服务器），这很麻烦。

MCP 最初需要远程传输时（2024-11-05 规范），采用了 SSE 方案，使用**两个端点**：客户端通过 GET 连接到 `/sse` 端点来接收服务器的流式响应，然后通过 POST 发送请求到单独的 `/messages` 端点。

**为什么被弃用？** 需要管理两个端点，服务器还要维护 SSE 连接 ID 和 POST 请求之间的映射关系，加重了有状态的复杂性，水平扩展很麻烦。另外很多负载均衡器、API 网关对长连接 SSE 的兼容性不好。

------

#### 🟡 3. Streamable HTTP（新版，当前推荐）

**生活比喻：** 只用一个手机号，既能接电话又能打电话，服务器还可以选择"发短信"（普通 JSON 回复）或"打语音电话"（SSE 流式响应）。

Streamable HTTP 使用**单一端点**（如 `/mcp`），支持 POST 和 GET。客户端通过 POST 发送 JSON-RPC 消息；服务器可以选择回一个普通 JSON 响应，也可以升级为 SSE 流来处理耗时操作，不需要独立的"事件端点"。

> **关键理解：** SSE 这项技术本身并没有消失，它作为**可选的流式响应方式**被内嵌在 Streamable HTTP 里面了。被弃用的是"旧版双端点 HTTP+SSE 传输方案"，而不是 SSE 技术本身。

------

### 三、SSE 被弃用？怎么理解？

这是很多文章容易让人误解的地方，要区分两个层次：

| 层次                                                         | 状态                           |
| ------------------------------------------------------------ | ------------------------------ |
| **SSE 技术本身**（Server-Sent Events，服务器推送事件）       | ✅ 没有弃用，仍在使用           |
| **旧版 HTTP+SSE 传输方案**（MCP 2024-11-05 规范里的那个双端点设计） | ❌ 在 2025-03-26 规范中正式弃用 |

旧版 HTTP+SSE 传输在 2025-03-26 规范中被正式弃用，新实现应使用 Streamable HTTP。但服务器为了兼容老客户端，可以继续保留旧端点。

**时间线：**

2024-11-05，MCP 初始规范，定义了 stdio 和 SSE 作为两种标准传输；2025-03-26，Streamable HTTP 引入，SSE 正式弃用；2025-11-25 最新规范中，正式的两种标准传输为 stdio 和 Streamable HTTP，SSE 仅保留用于向后兼容。

#### **一句话理解`旧版HTTP+SSE`和StreamableHTTP的差异**

- 旧版 `HTTP + SSE` 采用尴尬的**双端点架构**，AI 必须在一个端点通过 HTTP POST 发送指令，再从另一个独立的 SSE 端点接收流式响应，导致服务器必须依靠 Session ID 维持死板的“有状态”连接。
- 新版 `Streamable HTTP` 彻底优化为**单一标准 HTTP 端点**，让 AI 的每一次工具调用都变成“同一个请求进去，流式响应直接出来”的**无状态交互**。这不仅斩断了 Session 的包袱，更彻底解决了旧版无法部署在云端 Serverless（无服务器）架构上、网络抖动易断线解绑的致命痛点。

------

### 四、它们和 WebSocket 的关系

#### SSE 和 WebSocket 的核心区别

SSE 是基于 HTTP 标准的**单向通信**技术，服务器可以向客户端推送数据，但客户端无法通过 SSE 反向发送数据；WebSocket 则是**全双工**协议，客户端和服务器可以同时互相发送接收消息，连接一旦建立就保持打开状态。

用生活比喻：

- **SSE** = 广播电台，只有电台（服务器）发声，听众（客户端）只能听
- **WebSocket** = 对讲机，双方都可以随时说话

#### MCP 支持 WebSocket 吗？

**不支持**。WebSocket 不在当前 MCP 传输规范中。Streamable HTTP 结合 SSE 已经能覆盖流式场景，而且不需要 WebSocket 基础设施——后者在负载均衡和安全方面比普通 HTTP 更复杂。

#### 它们是包含关系吗？

**不是包含关系，而是同层竞争关系。** 三者都是解决"实时通信"问题的不同方案：

```
实时通信技术
├── WebSocket（全双工，独立协议 ws://）
├── SSE（服务端单向推送，基于 HTTP）
└── 普通 HTTP 轮询（客户端主动查询）

MCP 传输层（选择上面其中一种或组合）
├── stdio（不涉及网络）
├── Streamable HTTP（= HTTP POST + 可选 SSE 流）
└── ~~HTTP+SSE~~（已弃用）
```

Streamable HTTP **包含了 SSE 的使用**，但它本身不等于 SSE，更不等于 WebSocket。

### 四、 核心通信协议：JSON-RPC

#### 1. 通俗理解：跨语言的“普通话八股文”

- **RPC（Remote Procedure Call）** 的核心思想是：让调用远程电脑上的一个函数，写起来就像调用自己电脑本地的函数一样简单。
- **JSON-RPC** 是用 **JSON 语法** 包装的通信协议。它规定了大家说话必须带上固定的暗号字段（如版本号、函数名、参数、ID），解决了 AI（如 Python 编写）与工具（如 Go 编写）之间的语言壁垒。

#### 2. 普通 JSON vs JSON-RPC

- **普通 JSON** 是 **数据交换格式（原材料）**。它只管语法正确，里面写什么字段完全随心所欲。
- **JSON-RPC** 是 **行为协议（标准公文）**。它借用了 JSON 的语法，但强制规定了内部字段。

##### 格式对比

```json
JSON
{
  "yonghu_ming": "张三",
  "nianling": 25
}

```

```json
JSON-RPC 请求
{
    "jsonrpc": "2.0",
    "method": "add",
    "params": [1, 2],
    "id": "msg-001"
}
```

*(注：`jsonrpc` 版本、`method` 函数名、`params` 参数、`id` 消息编号，每个字段都雷打不动)*

### 五、 传输方式的实际交互模拟（以“查询北京天气”为例）

#### 1. stdio 模式交互（本地进程间通信）

- **步骤 ①：LLM 进程向工具进程的 `stdin`（输入口）写入一行 JSON 字符串**

  ```json
  {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Beijing"}}, "id": 1}
  ```

* **步骤 ②：工具进程本地查完天气，立刻向 `stdout`（输出口）吐出一行 JSON 字符串**
  ```json
  {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": "北京今天晴，25°C。"}]}, "id": 1}

#### 2. 旧版 HTTP + SSE 模式交互（云端连接）

- **步骤 ①：建立 SSE 长连接通道** LLM 客户端请求：`GET /sse`。服务器响应并保持连接不断开，发回专属通道 ID：

  ```http
  event: endpoint
  data: /message?sessionId=abc123xyz
  ```

* **步骤 ②：LLM 发送调用指令（普通 HTTP POST）**
  LLM 发送：`POST /message?sessionId=abc123xyz`，包体为：
  ```json
  {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Beijing"}}, "id": 1}

服务器收到后回应 `202 Accepted`（表示正在处理）。

- **步骤 ③：工具通过步骤 ① 建立的 SSE 专线把结果“推”回来**

  ```http
  event: message
  data: {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": "北京今天晴，25°C。"}]}, "id": 1}
  ```

#### 3. 新版 Streamable HTTP 模式交互（云端连接）
* **步骤 ①：LLM 直接发起标准的 HTTP POST 请求**
  直接发送到端点，无需提前握手建立长连接：
  ```json
  {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Beijing"}}, "id": 1}

- **步骤 ②：工具直接流式返回响应** 服务器响应头部设置为流式（如 `Transfer-Encoding: chunked`），在当前请求的响应中直接把 JSON 数据一段段吐出来：

  ```http
  HTTP/1.1 200 OK
  Transfer-Encoding: chunked
  Content-Type: application/json-rpc+stream

  [第1段] {"jsonrpc": "2.0", "result": {"content": [{"type": "text",
  [第2段] "text": "北京今天晴，25°C。"}]}, "id": 1}
  ```

  *(特点：一次请求，直接搞定，既不常驻连接，又能实现流式传输)*

---

### 六、 关键思考：既然 AI 需要完整结果，流式的目的是什么？

> 💡 **核心疑问**：对于工具调用来说，必须等到完整结果才能进行 LLM 下一轮思考和响应，为什么协议还要设计流式回复？

#### 1. 澄清一个误解：stdio 也可以是流式的
`stdio`、`Streamable HTTP` 只是**修路的方式（通道）**，而“流式还是阻塞”是**车里装的货**。`stdio` 通道完全可以通过连续写入多段 JSON-RPC Chunk 来实现流式传输。

#### 2. 工具调用需要“流式”的核心原因
1. **进度条与用户体验**：某些工具（如执行复杂代码、大数据分析、检索长篇文档）可能需要执行 30 秒。阻塞式会导致前端死卡，而流式可以允许工具实时吐出中间日志（如 *“正在扫描第 3 个数据库...”*），向用户展示任务进度。
2. **海量数据传输（防止内存撑爆）**：当 MCP 传输大文件资源（如 2GB 的日志文件或大型知识库内容）时，**阻塞式会一次性把大字符串读入内存导致崩溃（OOM）**。流式可以像“抽水机”一样读一行、发一行。
3. **工具本身是子智能体（Sub-Agent）**：在复杂 AI 工作流中，主 AI 调用的 MCP 工具本身可能就是另一个大模型（子智能体）。子智能体自身的思考过程就是一字一字蹦出来的（流式），主 AI 和用户需要实时看到它的思考链。

---

### 七、 WebSocket 深度对比与交互模拟（MCP里没有websocket）

>MCP里没有websocket,这里是扩展，与http和sse对比学习

#### 1. 核心通信特征对比

| 协议/方式        | 传输特点                 | 形象比喻                         | 适合场景                   |
| :--------------- | :----------------------- | :------------------------------- | :------------------------- |
| **HTTP（普通）** | 一问一答，用完就挂       | 戳一下，回一下，随后假装不认识   | 网页静态数据获取           |
| **SSE**          | 一次订阅，服务端单向推流 | 听收音机广播，只能听不能说       | 实时大屏、AI 文本流式回复  |
| **WebSocket**    | 全双工（双向同时）长连接 | 打双向网络电话，随时互相大喊大叫 | 多人联机游戏、实时聊天客服 |

#### 2. WebSocket 完整交互模拟
* **步骤 ①：握手升级（HTTP Handshake）**
  客户端发一个带有升级标记的 HTTP 请求：

  ```http
  GET /chat-ws HTTP/1.1
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==

- **步骤 ②：服务器同意升级** 服务器回应 101 状态码，传统 HTTP 宣告结束，正式接通 WebSocket 电话线：

  HTTP

  ```http
  HTTP/1.1 101 Switching Protocols
  Upgrade: websocket
  Connection: Upgrade
  ```

* **步骤 ③：LLM 顺着电话线发送 JSON-RPC 数据帧**

  ```json
  {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Beijing"}}, "id": 1}

- **步骤 ④：工具顺着同一根线立刻丢回结果**

  ```json
  {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": "北京今天晴，25°C。"}]}, "id": 1}
  ```

* **步骤 ⑤：服务端主动推流（WebSocket 的独特威力）**
  连接未断开。2分钟后北京突然发布暴雨预警，工具**无需等待 LLM 提问**，直接主动把消息拍在 LLM 脸上：
  ```json
  {"jsonrpc": "2.0", "method": "notifications/weather_alert", "params": {"alert": "北京发布暴雨蓝

#### 3. 为什么 MCP 偏爱 Streamable HTTP 胜过 WebSocket？

 在 MCP 场景下，AI 调用工具往往是“AI 问（Method Call） -> 工具答（Result Stream）”。

- **WebSocket** 的“双方随时可以主动说话”的超级能力，**在 MCP 里大部分时间是浪费的。**
- 相反，WebSocket 为了维持那根随时可以双向说话的“电话线”，需要耗费极高的服务器资源（无法轻易使用 Serverless 云函数），且更容易因为网络波动而断线。所以 MCP 最终选择走向了更轻量、更现代的 **Streamable HTTP**。
