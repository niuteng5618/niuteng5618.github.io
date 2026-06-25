---
layout: post
title: "MoE vs Dense 部署对比 & 大模型量化选型指南"
display_title: "MoE vs Dense 部署对比 & 大模型量化选型指南"
display_filename: "MoE vs Dense 部署对比 & 大模型量化选型指南.md"
date: 2026-06-25
primary_category: "大模型技术"
secondary_category: "推理与部署"
series: "量化"
primary_category_order: 2
secondary_category_order: 5
series_order: 7
post_order: 80
categories:
  - 大模型技术
  - 推理与部署
  - 量化
tags:
  - MoE
  - 量化
  - AWQ
  - GGUF
  - 部署
toc: true
comments: false
author: niuteng5618
---

部署一套大模型服务，工程同学最常被问的两个问题是：

1. 同等规模下，到底是上 **Dense 稠密模型**还是 **MoE 混合专家模型**？
2. 同一张卡的预算，是塞一个**大模型 + 重度量化**，还是塞一个**小模型 + 满血/轻量化**？

本文围绕 **Qwen3-32B（Dense）** 与 **Qwen3-30B-A3B（MoE）** 这对真实可下载的开源模型展开，把显存、速度、量化方案、选型边界一次讲清。

## 一、对照模型选定

阿里通义千问 Qwen3 系列开源型号如下：

| 型号 | 类型 | 总参数 | 激活参数 | 层数 | 专家数（总/激活） | 上下文 |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-0.6B / 1.7B / 4B / 8B / 14B / 32B | Dense | 0.6B–32B | 同总参数 | 28–64 | — | 32K–128K |
| **Qwen3-30B-A3B** | MoE | 30.5B | 3.3B | 48 | 128 / 8 | 128K |
| Qwen3-235B-A22B | MoE | 235B | 22B | 94 | 128 / 8 | 128K |

> 几个容易被写错的命名：阿里目前**没有** `Qwen3-35B-A3B` 这个型号；30B-A3B 才是开源的小 MoE。"A3B" 表示「激活约 3B」，与总参之间用短横线连接（`30B-A3B`）。

后文一律以 **Qwen3-32B vs Qwen3-30B-A3B** 作为对照——这是两个真实开源、可以拉下来直接跑的型号。

参考：[Qwen3 官方博客](https://qwenlm.github.io/blog/qwen3/)、[Qwen3 技术报告 arXiv:2505.09388](https://arxiv.org/abs/2505.09388)。

## 二、MoE vs Dense：显存底线由「总参数量」决定

一个常见的直觉陷阱：**既然 MoE 每次只激活 3B，是不是用 3B 的卡就能部署？答案是不行。**

原因：

- **专家权重必须全部常驻显存**。MoE 的路由（router / gating）在每个 token 上根据当前 hidden state 动态挑选 Top-K 个专家。如果专家不在显存里，临时从 CPU 内存或磁盘加载，延迟会高到不可接受（PCIe 拷贝比 HBM 访问慢 1–2 个数量级）。
- **KV Cache 也是按总隐藏维度算的**，不会因为 MoE 而变小。Qwen3-30B-A3B 的 hidden size 与 32B 相当，KV 占用相近。

正确的显存估算（**仅权重**，不含 KV Cache、激活、运行时开销）：

| 量化精度 | 字节/参数 | Qwen3-32B（32B） | Qwen3-30B-A3B（30.5B） |
| --- | --- | --- | --- |
| FP16 / BF16 | 2 | ≈ 64 GB | ≈ 61 GB |
| FP8 | 1 | ≈ 32 GB | ≈ 31 GB |
| INT8 / W8A8 | 1 | ≈ 32 GB | ≈ 31 GB |
| INT4（AWQ / GPTQ / GGUF Q4） | 0.5 | ≈ 16 GB | ≈ 15 GB |

加上 KV Cache（与上下文长度 & batch 相关，128K 上下文几 GB 起步）、激活临时缓冲与 CUDA 上下文，单卡跑 **INT4 32B 实际需要 18–22 GB 显存**，跑 **INT4 30B-A3B 实际 18–24 GB 显存**——两者都正好落在 RTX 3090 / 4090（24 GB）单卡的极限工作量上，**部署成本基本一致**。

## 三、MoE vs Dense：推理速度

LLM 解码阶段（decode）的瓶颈在**显存带宽**，因为生成每一个 token 都要把所有参与计算的权重从显存读到 SM。直觉上：

- Dense 32B 每个 token 要读 ≈ 32B × 0.5B（INT4）= 16 GB 权重
- MoE 30B-A3B 每个 token **理论上**读 ≈ 3.3B × 0.5B ≈ 1.7 GB 权重

但实务里**不会真的快 ~10×**，因为：

1. **共享部分仍要全读**：注意力层、router、Embedding、LM head 不参与稀疏化，每 token 都要全部读取——这部分通常占总参数 10–30%。
2. **专家分散读取的内存局部性较差**：8 个被选中的专家分布在 128 个专家里，访问模式更随机，HBM 利用率下降。
3. **路由开销**：每个 token 都要计算 Top-K gating，多一次小矩阵乘 + softmax。
4. **batch 调度损失**：batch 中不同 token 选不同专家，无法像 Dense 那样把整个 batch 整齐做矩阵乘，除非 vLLM / SGLang 等推理引擎做了 expert grouping。

vLLM、SGLang 0.4+ 在 H100 / A100 上的实测，decode 加速比通常是 **2–4×**，并发越高加速越明显。要给业务方报数时，建议按 **2–4×** 表述，而不是按理论上限的 ~10×。

**对比小结：**

| 维度 | Qwen3-32B (Dense) | Qwen3-30B-A3B (MoE) | 说明 |
| --- | --- | --- | --- |
| 总参数量 | 32 B | 30.5 B | 决定静态显存底线 |
| 单 token 激活参数 | 32 B | 3.3 B | 决定 decode 带宽压力 |
| FP16 权重显存 | ≈ 64 GB | ≈ 61 GB | 按 `参数量 × 2 bytes` 估算 |
| INT4 权重显存 | ≈ 16 GB | ≈ 15 GB | + KV Cache 后约 18–22 GB |
| Decode 速度（实测，相对 Dense） | 基线 1× | **2–4×** | 越大 batch 优势越明显 |
| Prefill / TTFT | 计算密集 | 也快，但不如 decode 提速明显 | prefill 受 FLOPs 主导 |
| 高 batch 吞吐 | 受算力瓶颈 | 显著更高（激活小） | 单卡 batch 上限更高 |
| 训练 / 微调难度 | 简单 | 更难（负载均衡 loss、router stability） | 推理选 MoE，微调团队要做好预期 |

一句话：**MoE 是「用显存空间换 decode 速度和吞吐」的设计**，部署成本仍按**总参数量**计。

> Prefill 与 Decode 的区别：prefill 是把整段 prompt 一次喂进去算出 KV Cache，受**算力（FLOPs）**主导；decode 是逐 token 自回归生成，每生成一个 token 都要把权重从显存里读一遍，受**带宽**主导。MoE 在 decode 阶段优势更突出。

## 四、同等显存下：大模型量化 vs 小模型满血

### 4.1 学术结论：4-bit 是甜点

Dettmers & Zettlemoyer 在 [《The case for 4-bit precision: k-bit Inference Scaling Laws》(arXiv:2212.09720)](https://arxiv.org/abs/2212.09720) 中跑了 **35,000+ 组实验**，得出广为引用的结论：

> "4-bit precision is almost universally optimal for total model bits and zero-shot accuracy."

翻译过来：**在显存预算固定的前提下，把最大塞得下的模型量化到 4-bit，是「zero-shot 准确率 / 总比特数」比值的最优解。** 低于 3-bit 性能急剧崩塌，高于 4-bit（如 6 / 8-bit）相对收益递减。

直观原理：

- 大模型在预训练阶段建立了复杂的高维逻辑网络（脑容量、知识图谱）；
- 量化只是抹除了「数值精度的细节」，宏观逻辑结构基本保留；
- 小模型即便满血，受限于参数规模，多步推理、复杂指令遵循能力本就不足。

### 4.2 实操对照（24 GB 单卡）

> 下表「性能保留率」是社区评测与官方 [Qwen Quantization Benchmark](https://qwen.readthedocs.io/en/latest/benchmark/quantization_benchmark.html) 的均值印象，不代表所有 benchmark 都是同一比例；上线前请以业务自己的 eval 集为准。

| 方案 | 实际显存 | 推理质量经验 | 适用场景 |
| --- | --- | --- | --- |
| **Qwen3-32B + INT4 (AWQ/GPTQ)** | 18–22 GB | 保留 FP16 的 **96–98%** | 24GB 单卡的最佳通用选择 |
| Qwen3-14B + FP16 | 28 GB（**单卡 OOM**） | 100% | 需要双卡或换 FP8 |
| Qwen3-14B + FP8 | ≈ 14 GB | ≈ 99–100% | TPS 高、24GB 卡有富余 |
| Qwen3-30B-A3B + INT4 | 18–22 GB | 保留 FP16 的 ~95% | 想要快 + 长上下文 |
| Qwen3-8B + FP16 | 16 GB | 100% | 任务简单、需极低延迟 |

经验法则：

- **复杂推理 / 长文档 / 代码**：32B-INT4 > 14B-FP16，结构（参数规模）赢过精度。
- **客服 FAQ / 分类 / 信息抽取**：14B-FP16 ≈ 32B-INT4，前者延迟更低更划算。
- **想要超长上下文 + 高并发**：30B-A3B INT4 是 24 GB 卡上的黑马。

### 4.3 进入 40+ GB 显存档位

- **Qwen3-235B-A22B（MoE，235B 总参 / 22B 激活）**：INT4 后 ≈ 118 GB（仅权重），需要 2×80GB 或 4×48GB 卡，是开源里能逼近 GPT-5 / Claude Sonnet 4.6 推理体感的最便宜方案。
- **Qwen2.5-72B-INT4**：≈ 36 GB，单张 A6000 48GB 或 2×24GB 即可起服务，在 LiveCodeBench 这种代码题上明显强于 32B。
- **Qwen3-32B FP16 / FP8**：≈ 64 GB / 32 GB；FP8 在 H100 / RTX 5090 等原生支持 FP8 指令的卡上几乎无损，但 24GB 卡跑不动。

### 4.4 反例：什么时候小模型满血更好

1. **极致延迟敏感**：14B-FP16 的 TPS 始终高于 32B-INT4（FLOPs 少一倍多）。客服首屏、IDE 行内补全等场景应选小模型。
2. **极端量化（< 3-bit）灾难**：Q2_K、IQ2、1.58-bit 等在 < 7B 模型上灾难性损失（专门训练的 BitNet 另说）；与其塞 INT2 的 70B，不如选 INT4 的 14B。
3. **专精任务 + 充分微调**：有高质量微调数据时，14B 全量微调通常打过 32B-INT4 零样本。
4. **多 Agent 路由系统**：把简单任务分发到合适尺寸的小模型，比一律走大模型更快更便宜。

## 五、四种主流量化方案怎么选

| 方案 | 核心原理 | 适用硬件 | 推荐推理引擎 |
| --- | --- | --- | --- |
| **AWQ** | **Activation-aware Weight Quantization**：先用校准集统计激活分布，找出对输出影响最大的「显著权重通道」（约 1%），通过**等价的 per-channel 缩放**把它们放大再量化，量化误差被压到最小。**所有权重最终都是 INT4，不存在混合精度**。| NVIDIA GPU | vLLM、SGLang、TGI、TensorRT-LLM |
| **GPTQ** | 基于 Hessian 二阶近似的逐层贪心量化，老牌方案，生态最广，与 AWQ 是 4-bit 量化里的两大主流。| NVIDIA GPU | vLLM、TGI、ExLlamaV2 |
| **GGUF**（Q4_K_M 最常用） | llama.cpp 的容器格式，支持 K-quant、IQ-quant 等多种比特配置，可 **CPU + GPU 混合 offload**。| CPU、Mac M 系列、消费级 GPU | llama.cpp、Ollama、LM Studio |
| **FP8 (E4M3 / E5M2)** | 8-bit 浮点，硬件原生指令支持，**权重 + 激活**都能量化，是「轻量化」而非「重量化」。| H100 / H200 / GB200 / RTX 4090+ | TensorRT-LLM、vLLM、SGLang |

几点容易被混淆的细节：

- **AWQ 的关键是「等价变换」，不是「保留 1% 高精度」**。AWQ 论文（[arXiv:2306.00978](https://arxiv.org/abs/2306.00978)）明确写道："To avoid the hardware-inefficient mix-precision quantization, AWQ employs an equivalent transformation to scale the salient weight channels to protect them." 它通过 per-channel scaling 在量化前放大显著通道、在反量化时除回去，**所有权重统一是 INT4**，硬件友好。
- **GPTQ 与 AWQ 并非取代关系**。多数主流推理引擎两者都支持，按业务 eval 结果选；GPTQ 在某些任务和工具链兼容性上仍有优势。
- **GGUF 的 Q4_K_M** 是社区最被推崇的「性价比挡位」，平均 PPL 损失 < 1%；新版本里 IQ4_XS 在 PPL 与体积上表现更好，值得 A/B。
- **FP8 是不同维度的方案**：它压缩 2×（vs 4-bit 压缩 4×），追求的是「质量优先 + 硬件原生指令」。在 H100 / GB200 上跑 FP8 比 INT4 更适合追求质量的场景；在 4090 / 消费级卡上 FP8 内核还不够成熟。

## 六、选型决策树

```
预算 = 单卡 24 GB
├── 业务复杂（推理/代码/长文档）→ Qwen3-32B-INT4 (AWQ)
├── 业务高并发 + 长上下文     → Qwen3-30B-A3B-INT4
├── 业务简单 + 极低延迟       → Qwen3-8B / 14B (FP16 或 FP8)
└── Mac / 纯 CPU             → Qwen3-32B GGUF Q4_K_M

预算 = 单卡 48 GB / 双卡 24 GB
├── 想要最强开源体感         → Qwen2.5-72B-INT4
├── 长上下文 + 高并发         → Qwen3-30B-A3B FP8
└── 在线训练 / RLHF          → 32B FP16

预算 = 多卡 80 GB+
├── 接近闭源旗舰             → Qwen3-235B-A22B INT4
└── 完整精度服务             → 32B / 72B FP16
```

## 七、参考资料

- Qwen3 官方博客：<https://qwenlm.github.io/blog/qwen3/>
- Qwen3 技术报告：<https://arxiv.org/abs/2505.09388>
- Qwen 官方 Speed Benchmark：<https://qwen.readthedocs.io/en/latest/benchmark/speed_benchmark.html>
- Qwen 官方 Quantization Benchmark：<https://qwen.readthedocs.io/en/latest/benchmark/quantization_benchmark.html>
- 4-bit Scaling Laws（Dettmers & Zettlemoyer, UW, 2023）：<https://arxiv.org/abs/2212.09720>
- AWQ 原论文（Lin et al., MIT, 2023）：<https://arxiv.org/abs/2306.00978>
- GPTQ 原论文：<https://arxiv.org/abs/2210.17323>
- llama.cpp K-quant 说明：<https://github.com/ggerganov/llama.cpp/pull/1684>
- BitNet b1.58（Microsoft, 2024）：<https://arxiv.org/abs/2402.17764>

## 八、小结

1. **同总参 MoE 与 Dense，部署显存基本持平**——别被「激活 3B」误导，硬件成本按总参算。
2. **MoE 在 decode 速度和并发吞吐上有 2–4× 的真实优势**，不会有 10×；首字延迟也快不到「接近 3B」。
3. **24 GB 单卡场景，Qwen3-32B INT4 是当前甜点**；想要更快 / 更长上下文，可换 Qwen3-30B-A3B INT4。
4. **大模型 + 4-bit 量化 > 小模型 + FP16**，这是 Dettmers Scaling Laws 给出的结论，至今未被推翻；但低于 3-bit 会触发智力崩塌（专门训练的 BitNet 另说）。
5. **AWQ 的核心是 per-channel scaling，所有权重都是 INT4**——并非混合精度保留。
