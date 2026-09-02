---
layout: post
title: "embedding和rerank区别"
display_title: "embedding和rerank区别"
display_filename: "embedding和rerank区别.md"
date: 2026-05-30
primary_category: "RAG"
secondary_category: "检索与排序"
series: "检索排序"
primary_category_order: 3
secondary_category_order: 2
series_order: 2
post_order: 25
categories:
  - RAG
  - 检索与排序
  - 检索排序
tags:
  - 检索排序
  - Embedding
  - Rerank
  - 召回
  - 重排序
toc: true
word_count: 2275
reading_time: 6
comments: false
author: niuteng5618
---
### 一、 底层原理区别
这两者在底层最核心的区别在于**注意力机制（Attention）的作用时机**。

#### 1. Embedding：双塔模型（Bi-Encoder）
+ **工作原理：** Embedding 模型会**独立地**将用户的查询（Query）和文档资料（Document）分别压缩成高维向量（比如 768 维的浮点数数组）。
+ **底层交互：** Query 和 Document 在变成向量之前，**没有任何信息交互**。模型只是各自提取它们的语义特征。
+ **相似度计算：** 当需要匹配时，只需在向量空间中计算两个向量的距离（例如余弦相似度或内积）。
+ **性能特点：** 极快。因为所有企业文档或知识库内容都可以**提前（离线）向量化**并存入向量数据库中。查询时，只需要对简短的 Query 进行一次向量化，然后在数据库中做简单的数学距离比对即可。

#### 2. Rerank：交叉编码器（Cross-Encoder）
+ **工作原理：** Reranker 模型不生成单独的向量。它将用户的查询（Query）和单篇文档（Document）**拼接在一起**（例如 `[CLS] Query [SEP] Document [SEP]`），同时输入到 Transformer 模型中。
+ **底层交互：** 由于 Query 和 Document 是同时输入的，模型底层的自注意力机制（Self-Attention）会让 Query 中的每一个词和 Document 中的每一个词**产生深度的交叉计算**。它能极其精准地捕捉到词与词之间的细微上下文关系。
+ **相似度计算：** 模型最终直接输出一个 0 到 1 之间的相关性打分，而不是输出向量。
+ **性能特点：** 极慢且昂贵。计算复杂度极高，因为无法提前计算文档的特征（文档得分严重依赖于当前的 Query 是什么），必须在用户提问的瞬间，进行实时的深度神经网络推理。

---

### 二、 用途与应用场景区别
由于底层计算成本的巨大差异，它们在实际工程中扮演着完全不同的角色。

#### 1. Embedding：用于“初筛”（召回阶段 / Retrieval）
+ **核心任务：** 在海量数据（几万到几百万篇文档）中，用最快的速度找出**可能相关**的 Top 100 篇文档。
+ **优势：** 速度极快，支持大规模并发，天然契合企业级 IT 基础设施中的向量数据库（Vector DB）。
+ **劣势：** 是一种“粗粒度”的匹配。比如它可能无法精确区分“我不喜欢苹果”和“我喜欢苹果”在特定语境下的差别，因为大部分词汇相同，向量距离会很近。

#### 2. Rerank：用于“精挑细选”（精排阶段 / Reranking）
+ **核心任务：** 接收 Embedding 阶段找出的那 100 篇“粗筛”文档，对它们进行极其严苛的重新打分和排序，选出**最核心、最准确**的 Top 3 到 Top 5，然后喂给 LLM 生成最终答案。
+ **优势：** 极高的语义准确度，能够识别复杂的逻辑、否定句以及特定的业务术语关联。
+ **劣势：** 无法用于全库检索。如果你试图用 Reranker 去直接扫描几十万篇文档，哪怕服务器算力再强，也会导致系统延迟爆炸（Latency 会高到无法接受）。

---

### 三、 总结对比表
为了更直观地理解，我们可以通过以下表格进行对比：

| **比较维度** | **Embedding (向量检索 / 双塔模型)** | **Rerank (重排 / 交叉编码模型)** |
| --- | --- | --- |
| **比喻** | **图书馆的图书管理员**：根据类别快速帮你锁定相关的几个书架。 | **深度阅读的学者**：把你找来的100本书逐字阅读，选出最能回答你问题的3页。 |
| **计算时机** | 文档侧**离线预计算**；Query侧实时计算。 | Query 和 文档必须**实时联合计算**。 |
| **交互深度** | 浅（无交叉注意力，独立表示） | 深（全词级别的交叉注意力匹配） |
| **速度与延迟** | **毫秒级** (极快，适合海量数据计算) | **百毫秒至秒级** (较慢，受限于 GPU 推理性能) |
| **在架构中的位置** | 第一阶段（Stage 1）：粗排/召回 | 第二阶段（Stage 2）：精排 |
| **召回数量级** | 从几百上千万文档中 -> 筛选出 Top 100 | 从 Top 100 中 -> 筛选出 Top 5 |


---

### **一、 底层模型结构拆解（Layer-by-Layer）**
现代的 Embedding 模型（双塔架构 Bi-encoder）和 Rerank 模型（交叉编码器 Cross-encoder）通常底层使用的都是 Transformer 结构，但它们在输入层拼接方式和输出层结构上截然不同。

以下是两者的底层层级剖析及可配置参数：

---

+ **Embedding 的分数确实是在模型外部通过计算两个特征向量的数学距离（通常是余弦相似度 Cosine Similarity 或内积 Dot Product）得出的。**
+ **Rerank 的分数是由模型内部的网络结构（通常是一个线性分类层加上 Sigmoid 或 Softmax 激活函数）直接计算并输出的概率值或相关性得分。**

#### **1. Embedding 模型（Bi-Encoder 双塔架构）运行机制：**Query 和 Document 分别、独立地通过同一个模型（权重共享）。

| **层级顺序** | **层名称 (Layer Name)** | **核心定义与作用** | **典型可配置参数 (Parameters)** |
| :--- | :--- | :--- | :--- |
| Layer 1 | Tokenizer Layer   (分词层) | 将文本切分成 Token。Query 和 Doc 独立切分。   格式: `[CLS] Text [SEP]` | `vocab_size` (词表大小，如 30522) |
| Layer 2 | Input Embedding Layer   (输入嵌入层) | 将 Token 转换为初始稠密向量。包含：   Token Embedding + Position Embedding。 | `max_position_embeddings` (如 512)   `hidden_size` ![image](/images/yuque/025-embeddingrerank/image-1-852c7144.svg) (如 768) |
| Layer 3 | Transformer Blocks   (多层堆叠) | 核心特征提取。    仅在 Query 内部词之间，或 Doc 内部词之间进行 Self-Attention。 | `num_hidden_layers` ![image](/images/yuque/025-embeddingrerank/image-2-9a53d6ae.svg) (如 12层)   `num_attention_heads` ![image](/images/yuque/025-embeddingrerank/image-3-4f90808f.svg) (如 12头)   `intermediate_size` (如 3072) |
| Layer 4 | Pooling Layer   (池化层) | 将变长的序列向量压缩成一个固定长度的全局句向量（Sentence Vector）。通常取 `[CLS]` token 的输出，或进行 Mean Pooling。 | `pooling_mode` (CLS, Mean, Max) |
| 输出外 | Similarity Calculation   (外部相似度计算) | 模型运行结束。在向量数据库中计算 Query 向量 ![image](/images/yuque/025-embeddingrerank/image-4-5a6c7cb6.svg) 和 Doc 向量 ![image](/images/yuque/025-embeddingrerank/image-5-c5fbaf60.svg) 的余弦相似度：   ![image](/images/yuque/025-embeddingrerank/image-6-d0b4cb27.svg) | 无 (纯数学运算) |


#### **2. Rerank 模型（Cross-Encoder 交叉编码架构）运行机制：Query 和 Document 拼接成一段长文本，一起输入到模型中。**

| **层级顺序** | **层名称 (Layer Name)** | **核心定义与作用** | **典型可配置参数 (Parameters)** |
| :--- | :--- | :--- | :--- |
| Layer 1 | Tokenizer Layer   (分词层) | 将 Query 和 Doc 拼接后切分。   格式: `[CLS] Query [SEP] Document [SEP]` | `vocab_size` (如 30522) |
| Layer 2 | Input Embedding Layer   (输入嵌入层) | 与上面类似，但多了一个 Segment Type Embedding，用于告诉模型哪些词属于 Query，哪些属于 Doc。 | `type_vocab_size` (通常为 2：0和1)   `hidden_size` ![image](/images/yuque/025-embeddingrerank/image-1-852c7144.svg) (如 768) |
| Layer 3 | Transformer Blocks   (多层堆叠) | 核心交叉匹配。   Query 中的词与 Doc 中的词在每一层都进行深度的交互和注意力计算。 | `num_hidden_layers` ![image](/images/yuque/025-embeddingrerank/image-2-9a53d6ae.svg) (如 12层)   `num_attention_heads` ![image](/images/yuque/025-embeddingrerank/image-3-4f90808f.svg) (如 12头) |
| Layer 4 | Classification Head   (分类头层) | 获取拼接文本的 `[CLS]` token 的最终输出向量 ![image](/images/yuque/025-embeddingrerank/image-10-e2a7a0e9.svg)，接入一个全连接层（Linear Layer）。 | `out_features` (通常为 1，即单一得分) |
| Layer 5 | Activation Layer   (激活层) | 通过激活函数将分类头的输出映射到 0~1 之间，直接作为相关性得分 ![image](/images/yuque/025-embeddingrerank/image-11-056163a9.svg)：   ![image](/images/yuque/025-embeddingrerank/image-12-0fa5297a.svg) | 激活函数类型 (Sigmoid) |


---

### **二、 速度差异的底层原因：卡在哪一层？**
Embedding 快，Rerank 慢，根本原因在于 Layer 3 (Transformer Blocks) 中的 多头自注意力机制（Multi-Head Self-Attention, MHSA） 的数学计算复杂度。

在 Self-Attention 层中，计算复杂度和输入序列的长度 ![image](/images/yuque/025-embeddingrerank/image-13-1f7566e8.svg) 呈平方级关系 (![image](/images/yuque/025-embeddingrerank/image-14-dfc1f880.svg))。

#### **1. 为什么 Rerank 慢在底层？（算力灾难）**
在 Rerank（Cross-encoder）中，Query 和 Document 是拼接在一起的。  
假设 Query 长度为 ![image](/images/yuque/025-embeddingrerank/image-15-2e591019.svg) (比如 20 tokens)，Document 长度为 ![image](/images/yuque/025-embeddingrerank/image-16-8f8e5897.svg) (比如 500 tokens)。拼接后的总长度 ![image](/images/yuque/025-embeddingrerank/image-17-00e929e0.svg) (520 tokens)。

+ 在 Rerank 的每一层 Transformer Block 中，计算量正比于：

![image](/images/yuque/025-embeddingrerank/image-18-c71134db.svg)

+ 这 ![image](/images/yuque/025-embeddingrerank/image-19-93484f75.svg) 次基本注意力运算需要穿过 12 层（甚至 24 层）网络。
+ 最致命的是： 对于初筛召回的 100 篇候选文档，你必须在用户提问的瞬间，把这个庞大的矩阵运算实时执行 100 次。这使得 Rerank 的推理极度消耗 GPU 算力和时间。

#### **2. 为什么 Embedding 快在底层？（降维打击与预计算）**
在 Embedding（Bi-encoder）中，Query 和 Document 是分离的。

+ Document 侧（离线预计算）： Document 的向量提取（![image](/images/yuque/025-embeddingrerank/image-20-3949e2e6.svg) 的计算量）在构建知识库时就已经提前算好并存成浮点数数组了，查询时不需要模型参与任何计算。
+ Query 侧（实时计算）： 用户提问时，模型只需要对极短的 Query 运行一遍 Transformer：

![image](/images/yuque/025-embeddingrerank/image-21-c6afbade.svg)

+ 匹配侧（极速）： 模型生成 Query 向量后，后续的 100 次比较不再经过复杂的 Transformer 层，而是直接在向量数据库中进行一次简单的点乘运算（时间复杂度仅为 ![image](/images/yuque/025-embeddingrerank/image-22-8cc67886.svg)，例如只做 768 次乘法和加法）。

**总结：**  
Embedding 快是因为它巧妙地避开了实时的 ![image](/images/yuque/025-embeddingrerank/image-14-dfc1f880.svg) 注意力计算，将最重的运算转移到了离线阶段，把实时的匹配简化成了 ![image](/images/yuque/025-embeddingrerank/image-22-8cc67886.svg) 的向量点乘；而 Rerank 慢是因为它强行在实时阶段，将 Query 和 Doc 绑在一起，承受了完整的 ![image](/images/yuque/025-embeddingrerank/image-25-fcef38a5.svg) 深度特征交叉计算。这就如同“看摘要找书（Embedding）”和“逐字精读对比（Rerank）”的时间差异。
