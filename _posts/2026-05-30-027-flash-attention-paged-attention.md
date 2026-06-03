---
layout: post
title: "Flash Attention & Paged Attention"
display_title: "Flash Attention & Paged Attention"
display_filename: "Flash Attention & Paged Attention.md"
date: 2026-05-30
primary_category: "大模型技术"
secondary_category: "模型架构与基础"
series: "Attention"
primary_category_order: 2
secondary_category_order: 2
series_order: 2
post_order: 27
categories:
  - 大模型技术
  - 模型架构与基础
  - Attention
tags:
  - Attention
  - Flash Attention
  - Paged Attention
  - KV Cache
  - 推理优化
toc: true
comments: false
author: niuteng5618
---
看这个人的博客，详细原理：[https://agijuejin.feishu.cn/wiki/FG7Jwvc3bitHQUkUrJvcVTBcnfe](https://agijuejin.feishu.cn/wiki/FG7Jwvc3bitHQUkUrJvcVTBcnfe)

以下由AI生成：

## 内容
FlashAttention 和 PagedAttention 是两种针对 Transformer 注意力机制的**显存优化技术**，分别解决不同维度的性能瓶颈。这里用技术对比的方式帮你快速理解：

---

### **1. FlashAttention（计算优化）核心目标**：**减少注意力计算时的显存访问次数适用场景**：训练/推理中的注意力计算优化

FlashAttention 通过以下两种核心技术解决了这个问题：

1. **分块计算（Tiling）：** 将输入的 Query、Key、Value 矩阵切分成多个小块（Blocks），分批次加载到极快的 SRAM 中。在 SRAM 内直接完成计算和 softmax 更新，最后只将最终结果写回 HBM。
2. **重计算（Recomputation）：** 在反向传播时，不保存庞大的 $N \times N$ 矩阵，而是利用前向传递时保存的少量统计数据在 SRAM 中重新快速计算注意力梯度。

将计算的内存复杂度从 $O(N^2)$ 降低到了 $O(N)$，在保证计算结果绝对精确（无损）的前提下，极大地提升了处理长序列的效率。

  
**关键技术**：

```python
# 传统注意力计算 (伪代码)
QK = Q @ K.T            # O(N²) 显存占用
softmax_QK = softmax(QK) 
Attention = softmax_QK @ V  # 两次显存密集型矩阵乘法

# FlashAttention 改进
将计算拆分为分块(tiling)处理：
1. 分块加载Q/K/V到SRAM（片上高速缓存）
2. 局部计算QK^T + softmax + 与V相乘
3. 通过重计算(recompute)避免存储中间矩阵
```

**优化效果**：

+ 训练速度提升 15-30% (A100实测)
+ 显存占用降低 5-20 倍  
**典型应用**：LLaMA、GPT-3 等大模型的训练加速

#### 关闭 FlashAttention 对模型推理的影响
在模型推理（特别是 LLM 推理）过程中关闭 FlashAttention，会对性能指标产生灾难性的影响，尤其是在处理高并发或长上下文时：

+ **显存占用呈指数级爆炸 (OOM 风险剧增) **不使用 FlashAttention 时，注意力矩阵的显存分配将退化回 $O(N^2)$ 的复杂度。如果处理的 Prompt 较长（例如超过 8K 或 32K），计算中间态会瞬间吃满 GPU 显存，极易触发 Out of Memory (OOM) 错误，导致推理任务直接崩溃。
+ **首字延迟 (TTFT) 大幅延长 **推理的 Prefill（预填充）阶段需要对用户输入的整个 Prompt 并行计算注意力。关闭该功能后，GPU 会被海量的 HBM 读写操作卡住。由于计算单元处于等待数据的闲置状态，处理输入所需的时间会显著增加，导致 TTFT (Time To First Token) 严重恶化。
+ **整体吞吐量 (Throughput) 骤降 **在大规模并发推理场景下，系统性能极度依赖硬件资源的利用率。关闭 FlashAttention 会导致严重的访存瓶颈，GPU 的 Tensor Cores 无法满载运行。这会直接拖慢每秒可处理的请求数或 Token 数，导致整体服务吞吐量断崖式下降。
+ **每次输出延迟 (TPOT) 受到波及 **虽然在 Decode（解码）阶段（每次只生成一个 Token）计算注意力时，瓶颈更多在于加载 KV Cache 的显存带宽，但缺少了底层算子的显存访问优化，加上潜在的系统内存压力，TPOT (Time Per Output Token) 和整体的 ITL (Inter-Token Latency) 依然会出现一定程度的波动和性能降级。
+ **丧失长文本处理能力 **现代模型动辄支持 128K 甚至 1M 的上下文窗口，这在标准注意力机制下是物理上无法实现的。关闭它意味着模型基本只能处理极短的对话，失去了阅读长文档或进行复杂代码库分析的能力。

#### FA对Prefill阶段的影响
在处理用户输入的长 Prompt 时，模型需要一次性计算整个序列的自注意力，并生成初始的 KV Cache。

+ **此时的计算特征：** 计算密集型（Compute-bound），涉及庞大的矩阵乘法（Query 矩阵与 Key/Value 矩阵都是 $N \times d$ 的维度）。
+ **它们的关系：** 此时 **FlashAttention 是绝对的主力**。如果没有 FlashAttention，计算这个初始的 $N \times N$ 注意力分数矩阵会直接导致 OOM 或者极长的处理时间。FlashAttention 能够在极低的显存占用下，飞速完成长序列的注意力计算，**并顺便将计算得到的 Key 和 Value 状态输出，存入 GPU 显存，这就是初始的 KV Cache。**
+ **性能影响：** 极大地优化了 **TTFT（Time To First Token，首字延迟）**。

#### FA对decode阶段的影响
标准版本的 FlashAttention（FA1 和 FA2）在纯粹的 Decode（解码）阶段，几乎起不到加速作用，甚至在某些极端情况下可能不如高度优化的基础 CUDA Kernel。

为了解决这个问题，业界衍生出了 **Flash-Decoding** 技术。

为了拯救长上下文场景下的 Decode 性能（尤其是降低不断攀升的 ITL 字间延迟），FlashAttention 的作者在后续提出了 **Flash-Decoding**。它本质上是 FA 思想在 Decode 阶段的特化版本。

Flash-Decoding 改变了并行切分的策略，它的核心作用可以归纳为以下几步：

+ **维度转换（沿着上下文长度并行）：** 既然 $Q$ 的长度只有 1 无法拆分，Flash-Decoding 就选择去**拆分历史的 KV Cache 序列（Sequence Length 维度）**。
+ **多 SM 并发读取：** 它将冗长的历史 KV Cache 切分成多个小块（Blocks），然后把这些块分配给 GPU 上**不同的、闲置的流处理器（SM）**同时去加载和计算。
+ **局部注意力与全局规约（Reduction）：** 每个 SM 拿着全局唯一的 $Q$ 向量和自己分到的那一小块 $K$ 和 $V$，在 SRAM 内独立计算出一个局部的“残缺版”注意力结果和 LogSumExp 统计量。
+ **最终合并：** 最后，启动一个极其轻量的计算 Kernel，将各个 SM 算出的局部结果进行 Reduce（规约合并），得到最终正确的一步注意力输出。

---

### **2. PagedAttention（显存管理优化）核心目标**：**高效管理 KV Cache 显存碎片提出方**：UC Berkeley (vLLM框架)  
**适用场景**：大模型推理时的显存管理  
**关键技术**：

```python
# 传统KV Cache问题：
每个请求的KV缓存分配连续显存 -> 导致内存碎片化

# PagedAttention 改进：
1. 将KV缓存划分为固定大小的"页"(类似OS内存分页)
2. 非连续物理显存 + 逻辑页表映射
3. 支持动态分配/释放显存页
```

**优化效果**：

+ 吞吐量提升 2-4 倍 (实测)
+ 支持比原有显存大 5 倍的上下文长度  
**典型应用**：vLLM、ChatGPT 等推理服务

---

### **对比表格**
| 维度 | FlashAttention | PagedAttention |
| :--- | :--- | :--- |
| **优化方向** | 计算模式优化 | 显存分配优化 |
| **主要阶段** | 训练/推理中的注意力计算 | 推理时的KV缓存管理 |
| **关键技术** | 分块计算 + 重计算 | 显存分页 + 虚拟映射 |
| **显存节省原理** | 减少中间矩阵存储 | 消除内存碎片 |
| **典型受益场景** | 长文本训练 | 高并发推理服务 |


---

### **组合使用示例**
当部署一个大语言模型时：

1. **训练阶段**：使用 FlashAttention 加速注意力计算
2. **推理阶段**：使用 PagedAttention 管理 KV Cache

```bash
# 实际技术栈示例
训练框架：PyTorch + FlashAttention-2
推理框架：vLLM (内置PagedAttention)
```

两者的优化维度相互正交，实际应用中常配合使用以获得最大性能收益。如果想更深入理解，推荐通过具体代码案例实践（如用 FlashAttention 实现一个注意力层，或用 vLLM 部署模型观察显存变化）。
