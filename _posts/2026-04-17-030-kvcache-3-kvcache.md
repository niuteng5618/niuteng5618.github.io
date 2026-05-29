---
layout: post
title: "KVcache（3）——包含KVcache完整请求示例"
display_title: "KVcache（3）——包含KVcache完整请求示例"
display_filename: "KVcache（3）——包含KVcache完整请求示例.md"
date: 2026-04-17
primary_category: "人工智能技术"
secondary_category: "大模型推理"
series: "KV Cache"
primary_category_order: 1
secondary_category_order: 5
series_order: 4
post_order: 30
categories:
  - 人工智能技术
  - 大模型推理
  - KV Cache
tags:
  - KV Cache
  - 请求示例
  - 推理流程
  - 缓存
toc: true
comments: false
author: niuteng5618
---
# 🔹完整请求模拟（带模拟数据）


**<font style="color:#DF2A3F;">logits</font>**一般指的是，神经网络**最后一层的输出。**

### 用户输入
```plain
prompt = "写诗"
```

### Tokenizer 编码（模拟）
```plain
"写诗" → [101, 3056, 7405, 102]  
(101 = CLS, 3056 = "写", 7405 = "诗", 102 = SEP)
```

---

## 阶段 1：请求路由
**输入 → 输出格式**

```plain
{
  "request_id": "req_001",
  "prompt": "写诗",
  "input_tokens": [101, 3056, 7405, 102]
}
```

---

## 阶段 2：Prefill 阶段
### 处理内容
1. 通过 Embedding + Transformer 层，计算所有 token 的 hidden states。
2. 为每个 Attention 层保存 KV Cache。  
KV Cache 结构：

```plain
kv_cache[layer][head]["K" or "V"][seq_len, head_dim]
```

### 模拟 KV Cache（假设2层，2头，每个 head_dim=4）
```plain
{
  "request_id": "req_001",
  "kv_cache": {
    "layer_0": {
      "head_0": {
        "K": [[0.1, 0.2, 0.3, 0.4], /token1
              [0.5, 0.6, 0.7, 0.8], /token2
              [0.9, 1.0, 1.1, 1.2], /token3
              [1.3, 1.4, 1.5, 1.6]], /token4
              
        "V": [[0.2, 0.1, 0.0, -0.1],  /token1
              [0.3, 0.2, 0.1, 0.0],   /token2
              [0.4, 0.3, 0.2, 0.1],   /token3
              [0.5, 0.4, 0.3, 0.2]]   /token4
      },
      "head_1": {
        "K": [[-0.1, -0.2, -0.3, -0.4],
              [0.1, 0.2, 0.3, 0.4],
              [0.5, 0.6, 0.7, 0.8],
              [0.9, 1.0, 1.1, 1.2]],
        "V": [[0.0, -0.1, -0.2, -0.3],
              [0.1, 0.0, -0.1, -0.2],
              [0.2, 0.1, 0.0, -0.1],
              [0.3, 0.2, 0.1, 0.0]]
      }
    },
    "layer_1": {
      "head_0": {
        "K": [[0.01, 0.02, 0.03, 0.04],
              [0.05, 0.06, 0.07, 0.08],
              [0.09, 0.10, 0.11, 0.12],
              [0.13, 0.14, 0.15, 0.16]],
        "V": [[0.1, 0.0, -0.1, -0.2],
              [0.2, 0.1, 0.0, -0.1],
              [0.3, 0.2, 0.1, 0.0],
              [0.4, 0.3, 0.2, 0.1]]
      },
      "head_1": {
        "K": [[-0.01, -0.02, -0.03, -0.04],
              [0.01, 0.02, 0.03, 0.04],
              [0.05, 0.06, 0.07, 0.08],
              [0.09, 0.10, 0.11, 0.12]],
        "V": [[0.0, -0.01, -0.02, -0.03],
              [0.01, 0.0, -0.01, -0.02],
              [0.02, 0.01, 0.0, -0.01],
              [0.03, 0.02, 0.01, 0.0]]
      }
    }
  },
  "first_token_logits": [0.05, 0.10, 0.80, 0.05]
}
```

说明：

+ `first_token_logits` → Softmax 后概率最高的是 index=2，对应 "秋"。

---

## 阶段 3：KV Cache 传输
**发送给 Decode 集群**

```plain
{
  "request_id": "req_001",
  "kv_cache": "<完整kvcache上面那个大对象>",
  "generated_tokens": [],
  "next_token": "秋"
}
```

---

## 阶段 4：Decode 阶段（自回归生成）
### Step 1（生成第1个 token）
+ **输入**：KV cache + token="秋"
+ **更新**：KV Cache 添加 "秋" 的 K/V
+ **输出**：

```plain
{
  "request_id": "req_001",
  "generated_tokens": ["秋"],
  "kv_cache": {
    "layer_0": {
      "head_0": {
        "K": [..., [1.7, 1.8, 1.9, 2.0]],
        "V": [..., [0.6, 0.5, 0.4, 0.3]]
      },
      "head_1": {
        "K": [..., [1.3, 1.4, 1.5, 1.6]],
        "V": [..., [0.4, 0.3, 0.2, 0.1]]
      }
    },
    "layer_1": {
      "head_0": {
        "K": [..., [0.17, 0.18, 0.19, 0.20]],
        "V": [..., [0.5, 0.4, 0.3, 0.2]]
      },
      "head_1": {
        "K": [..., [0.13, 0.14, 0.15, 0.16]],
        "V": [..., [0.04, 0.03, 0.02, 0.01]]
      }
    }
  }
}
```

---

### Step 2（生成第2个 token）
+ Decode 输出下一个 token → "天"
+ KV Cache 再追加一列 K/V

```plain
{
  "request_id": "req_001",
  "generated_tokens": ["秋", "天"],
  "kv_cache": { ... 更新后的完整cache ... }
}
```

---

### Step 3（生成第3个 token）
+ 输出 token → "的"

```plain
{
  "request_id": "req_001",
  "generated_tokens": ["秋", "天", "的"],
  "kv_cache": { ... }
}
```

---

### Step 4（生成第4个 token）
+ 输出 token → "诗"

```plain
{
  "request_id": "req_001",
  "generated_tokens": ["秋", "天", "的", "诗"],
  "kv_cache": { ... }
}
```

---

## 阶段 5：结果返回用户
```plain
{
  "request_id": "req_001",
  "final_output": "秋天的诗"
}
```
