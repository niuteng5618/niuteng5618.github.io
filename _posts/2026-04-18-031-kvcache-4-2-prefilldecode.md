---
layout: post
title: "KVcache（4）——模型推理的2个阶段：Prefill、decode"
date: 2026-04-18
tags: ["人工智能技术", "大模型基础", "KVcache", "KVcache（4）——模型推理的2个阶段：Prefill、decode"]
toc: true
comments: false
author: niuteng5618
---
<font style="color:rgb(31, 35, 40);">完整的KVcache包含 Prefill + decode。</font>

```plain
# 带 KV Cache 的生成
kv_cache = {}  # 每一层缓存 K, V
for step in range(max_new_tokens):
    if step == 0:
        # 第一步：处理所有 input tokens，填充 cache
        logits, kv_cache = model(input_tokens, kv_cache=None)
    else:
        # 后续步：只送入上一步生成的 1 个 token
        logits, kv_cache = model([last_token], kv_cache=kv_cache)
    next_token = sample(logits[-1])
    last_token = next_token
```

<font style="color:rgb(31, 35, 40);">理解了 KV Cache 之后，我们可以把 LLM 推理过程清晰地分成两个阶段：</font>**<font style="color:rgb(31, 35, 40);">Prefill</font>**<font style="color:rgb(31, 35, 40);"> 和 </font>**<font style="color:rgb(31, 35, 40);">Decode</font>**<font style="color:rgb(31, 35, 40);">。这两个阶段的计算特性截然不同，理解它们的区别对后面理解 Prompt Cache 非常关键。</font>

![](/images/yuque/031-kvcache-4-2-prefilldecode/image-1-6233c074.png)

> **<font style="color:rgb(31, 35, 40);">causal attention的mask机制，仅在Prefill阶段生效，在decode阶段无效。</font>**
>
> <font style="color:rgb(31, 35, 40);">直觉：</font>
>
> <font style="color:rgb(31, 35, 40);">用户输入都是一长串query："白日依山"</font>
>
> <font style="color:rgb(31, 35, 40);">Prefill阶段，因为query是 整体、一次性输入进模型中，需要设置 mask机制，让 "白"看不到"日依山"，"日"看不到"依山"...</font>
>
> <font style="color:rgb(31, 35, 40);">但是decode阶段是逐个token生成，无需mask机制 挡住后面的内容（因为还没生成...）</font>
>

### Prefill 阶段（并行处理 input tokens）
<font style="color:rgb(31, 35, 40);">Prefill 阶段就是上面伪代码中 </font>`<font style="color:rgb(31, 35, 40);">step == 0</font>`<font style="color:rgb(31, 35, 40);"> 的那一步：模型一次性处理所有输入 token（system prompt + user message），为每一层、每个 token 计算出 K 和 V 并存入 cache。</font>

**用户输入 (Prompt)：**`“白日依山”`

1. **Prefill 阶段（并行）：**<font style="color:rgb(31, 35, 40);"> GPU 瞬间拿到了 </font>`<font style="color:rgb(31, 35, 40);">["白", "日", "依", "山"]</font>`<font style="color:rgb(31, 35, 40);"> 这 4 个 token。 它不需要先看“白”，再看“日”。GPU 会开足马力，同时计算：</font>
    - <font style="color:rgb(31, 35, 40);">“白”的特征（K, V）</font>
    - <font style="color:rgb(31, 35, 40);">“日”在这个语境下的特征（K, V）</font>
    - <font style="color:rgb(31, 35, 40);">“依”的特征（K, V）</font>
    - <font style="color:rgb(31, 35, 40);">“山”的特征（K, V） 这 4 个 token 的计算是</font>**在同一瞬间、同一个矩阵乘法中并行完成的**<font style="color:rgb(31, 35, 40);">。算完后，把这 4 个字的 KV Cache 存进显存。</font>

<font style="color:rgb(31, 35, 40);">关键特点：</font>

+ **<font style="color:rgb(31, 35, 40);">所有输入 token 可以并行处理</font>**
+ <font style="color:rgb(31, 35, 40);">属于已知全部输入序列</font>
+ <font style="color:rgb(31, 35, 40);">Prefill阶段 input tokens之间的 Attention mask 是 causal 的，但计算可以用矩阵乘法一次完成</font>
+ <font style="color:rgb(31, 35, 40);">计算量大：</font>_<font style="color:rgb(31, 35, 40);">n</font>_<font style="color:rgb(31, 35, 40);"> 个 token × 所有层 × Q/K/V 矩阵运算</font>
+ **<font style="color:#DF2A3F;">Compute Bound</font>**<font style="color:#DF2A3F;">：GPU 的算力是瓶颈，决定了首token时间 </font>**<font style="color:#DF2A3F;">TTFT（Time To First Token）</font>**

:::info
**问题：**为什么Prefill阶段“已知输入”就可以不逐个执行？可以直接并行？

Prefill阶段的输入是整个input序列。假设你的输入 Prompt 有N 个 Token。在送入 Attention 层之前，它们会被转换成一个巨大的输入矩阵X（维度是 N * d，其中d 是隐藏层维度）。

![](/images/yuque/031-kvcache-4-2-prefilldecode/image-2-8a32746c.png)

随后，在进行attention分数计算时引入mask机制。

**个人理解：**

prefill阶段主要是针对input tokens进行预处理，预处理的流程就是计算得到每个token的QKV（用于后续decode生成）。因此，需要进行一个巨大的矩阵乘法计算。因为gpu的并行特性，可以快速进行矩阵计算，得到计算结果。

随后，通过掩码矩阵mask掉未来信息，使得每个token在计算attention时只使用过去token的qkv信息。

 Mask 并不是直接作用在 QKV 上，而是作用在** **Q 和 K 相乘之后得到的“注意力分数”上。  

![](/images/yuque/031-kvcache-4-2-prefilldecode/image-3-51d2a215.png)

**问题：**既然后续decode只用kv值，为什么还要有q和attention 分数？

个人理解：以"白日依山尽"为例，模型是逐个token进行处理的，当token "山"在计算前，都会得到Q_山、K山、V山，随后将K山、V山存储到之前的KVcache中，再使用Q山进行计算。

使用Q山 分别对 K白、K日、K依、K山进行点积计算，得到一个attention分数 List。[0,1,2,1]。

随后对attention分数List进行softmax得到[0, 0.25, 0.5, 0.25]，随后与V矩阵相乘。

:::

### Decode 阶段（逐 token 生成 ）
<font style="color:rgb(31, 35, 40);">Decode 阶段就是后续的</font><font style="color:rgb(31, 35, 40);"> </font>`<font style="color:rgb(31, 35, 40);">step > 0</font>`<font style="color:rgb(31, 35, 40);">：每一步只输入 1 个 token，利用 KV Cache 做 Attention，生成下一个 token。</font>

**Decode 阶段（串行/自回归）：**

+ **第 1 步：**<font style="color:rgb(31, 35, 40);"> 模型看着前面存好的 Cache，经过计算，输出了第一个生成的字：</font>`<font style="color:rgb(31, 35, 40);">“尽”</font>`<font style="color:rgb(31, 35, 40);">。</font>
+ **第 2 步：**<font style="color:rgb(31, 35, 40);"> 现在要把 </font>`<font style="color:rgb(31, 35, 40);">“尽”</font>`<font style="color:rgb(31, 35, 40);"> 喂给模型。模型结合前面的 Cache 和新来的 </font>`<font style="color:rgb(31, 35, 40);">“尽”</font>`<font style="color:rgb(31, 35, 40);">，输出下一个标点：</font>`<font style="color:rgb(31, 35, 40);">“，”</font>`<font style="color:rgb(31, 35, 40);">。</font>
+ **第 3 步：**<font style="color:rgb(31, 35, 40);"> 把 </font>`<font style="color:rgb(31, 35, 40);">“，”</font>`<font style="color:rgb(31, 35, 40);"> 喂给模型，输出下一个字：</font>`<font style="color:rgb(31, 35, 40);">“黄”</font>`<font style="color:rgb(31, 35, 40);">。 在 Decode 阶段，你永远无法在算出 </font>`<font style="color:rgb(31, 35, 40);">“尽”</font>`<font style="color:rgb(31, 35, 40);"> 之前提前算出 </font>`<font style="color:rgb(31, 35, 40);">“黄”</font>`<font style="color:rgb(31, 35, 40);">，这就导致了它只能逐个处理。</font>

<font style="color:rgb(31, 35, 40);">关键特点：</font>

+ **<font style="color:rgb(31, 35, 40);">每步只处理 1 个 token</font>**<font style="color:rgb(31, 35, 40);">（无法并行，因为下一个 token 依赖上一个的输出）</font>
+ <font style="color:rgb(31, 35, 40);">decode阶段无causal attention的mask机制。</font>
+ <font style="color:rgb(31, 35, 40);">每步的计算量其实不大——1 个 token 的 Q 乘以 cache 中所有 K/V</font>
+ <font style="color:rgb(31, 35, 40);">但每步都要从显存</font>**<font style="color:rgb(31, 35, 40);">读取整个 KV Cache</font>**
+ **<font style="color:#DF2A3F;">Memory Bound</font>**<font style="color:#DF2A3F;">：GPU 的显存带宽是瓶颈，决定了生成每个后续 token 的平均时间 </font>**<font style="color:#DF2A3F;">TPOT（Time Per Output Token</font>**
