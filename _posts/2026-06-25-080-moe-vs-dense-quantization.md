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

> 本文整理自一段关于「同等规格的 MoE 与 Dense 部署成本对比」+「同等显存下大模型量化 vs 小模型满血如何选」的学习问答。原对话方向大致正确，但**型号命名、显存数字、MoE 加速比、AWQ 工作原理**等关键细节有多处偏差，本文先给出更准确的结论，再附「易错点澄清」表逐条修正。

## 一、先把名字纠正过来：不存在 `Qwen3-35B-A3B`

阿里通义千问 Qwen3 系列实际开源的型号是：

| 型号 | 类型 | 总参数 | 激活参数 | 层数 | 专家数（总/激活） | 上下文 |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-0.6B / 1.7B / 4B / 8B / 14B / 32B | Dense | 0.6B–32B | 同总参数 | 28–64 | — | 32K–128K |
| **Qwen3-30B-A3B** | MoE | 30.5B | 3.3B | 48 | 128 / 8 | 128K |
| Qwen3-235B-A22B | MoE | 235B | 22B | 94 | 128 / 8 | 128K |

所以后文一律以 **Qwen3-32B（Dense）vs Qwen3-30B-A3B（MoE）** 作为对照——这是真实开源、可以直接拉下来跑的两个型号。原 QA 里的 `Qwen-32B` / `Qwen-35B-A3B` 写法都不规范：前者缺版本号，后者是不存在的型号。

> 参考：[Qwen3 官方博客](https://qwenlm.github.io/blog/qwen3/)、[Qwen3 技术报告 arXiv:2505.09388](https://arxiv.org/abs/2505.09388)。

## 二、MoE vs Dense 部署对比

### 2.1 部署成本：显存底线由「总参数量」决定

> 易错点：很多人以为 MoE 每次只激活 3B 就能用 3B 的卡部署——**完全行不通**。

原因：

- **专家权重必须全部常驻显存**。MoE 的路由（router/gating）在每个 token 上根据 hidden state 动态挑选 Top-K 个专家。如果不在显存里，临时从内存/磁盘加载延迟会高到不可接受（PCIe 拷贝 ≫ HBM 访问 1-2 个数量级）。
- **KV Cache 也是按总隐藏维度算的**，不会因为 MoE 而变小，相反 Qwen3-30B-A3B 的 hidden size 与 32B 接近，KV 占用相当。

正确的显存估算（仅权重，不含 KV Cache、激活、运行时开销）：

| 量化精度 | 字节/参数 | Qwen3-32B（32B） | Qwen3-30B-A3B（30.5B） |
| --- | --- | --- | --- |
| FP16 / BF16 | 2 | ≈ 64 GB | ≈ 61 GB |
| FP8 | 1 | ≈ 32 GB | ≈ 31 GB |
| INT8 / W8A8 | 1 | ≈ 32 GB | ≈ 31 GB |
| INT4（AWQ / GPTQ / GGUF Q4） | 0.5 | ≈ 16 GB | ≈ 15 GB |

加上 KV Cache（与上下文长度 & batch 相关，128K 上下文几 GB 起步）、激活临时缓冲、CUDA 上下文，单卡跑 INT4 32B 实际需要 **18–22 GB 显存**，跑 INT4 30B-A3B 实际 **18–24 GB 显存**——所以两者都是 RTX 3090 / 4090（24GB）单卡的极限工作量。

> 原 QA 里的 `FP16 32B ≈ 76 GB`、`FP16 35B-A3B ≈ 84 GB` 数字**严重偏高**且型号本身就不存在；正确数量级是 **64 GB / 61 GB**，76GB 大概是有人误把 KV Cache + 优化器状态算了进去。

### 2.2 推理速度：MoE 显著快，但**没有快 10 倍**

LLM 解码阶段（decode）的瓶颈在**显存带宽**，因为生成每一个 token 都要把所有参与计算的权重从显存读到 SM。直觉上：

- Dense 32B 每个 token 要读 ≈ 32B × 0.5B（INT4）= 16 GB 权重
- MoE 30B-A3B 每个 token **理论上**读 ≈ 3.3B × 0.5B ≈ 1.7 GB 权重

但实务里不会真的快 ~10×，原因：

1. **共享部分仍要全读**：MoE 的注意力层、router、Embedding、LM head 不参与稀疏化，每 token 都要全部读取——这部分 share 通常占总参数 10–30%。
2. **专家分散读取的内存局部性较差**：8 个被选中的专家分布在 128 个专家里，导致访问模式更随机，HBM 利用率下降。
3. **路由开销**：每个 token 都要计算 Top-K gating，多一次小矩阵乘 + softmax。
4. **batch 中不同 token 选不同专家**，无法像 Dense 那样把整个 batch 整齐做矩阵乘——除非 vLLM/SGLang 等做了 expert grouping。

真实测得的 decode 加速比通常是 **2–4×**（vLLM、SGLang 0.4+ 在 H100 / A100 上的常见数据），并发越高加速越明显。**不要按 10× 宣传给业务方**。

| 维度 | Qwen3-32B (Dense) | Qwen3-30B-A3B (MoE) | 说明 |
| --- | --- | --- | --- |
| 总参数量 | 32 B | 30.5 B | 决定静态显存底线 |
| 单 token 激活参数 | 32 B | 3.3 B | 决定 decode 带宽压力 |
| FP16 权重显存 | ≈ 64 GB | ≈ 61 GB | 与原 QA 数字差异较大，请以此为准 |
| INT4 权重显存 | ≈ 16 GB | ≈ 15 GB | + KV Cache 后约 18–22 GB |
| Decode 速度（实测，相对 Dense） | 基线 1× | **2–4×** | 而非"接近 3B 速度" |
| Prefill / TTFT | 计算密集 | 也快，但不如 decode 提速明显 | prefill 受 FLOPs 主导，激活参数小确实占便宜 |
| 高 batch 吞吐 | 受算力瓶颈 | 显著更高（激活小） | 单卡 batch 上限更高 |
| 训练 / 微调难度 | 简单 | 更难（负载均衡 loss、router stability） | 推理选 MoE，但微调团队要做好预期 |

一句话：**MoE 是「用显存空间换 decode 速度和吞吐」的设计**。

## 三、同等显存下：大模型量化 vs 小模型满血

### 3.1 学术结论：4-bit 是最优甜点

Dettmers & Zettlemoyer 在 [《The case for 4-bit precision: k-bit Inference Scaling Laws》(arXiv:2212.09720)](https://arxiv.org/abs/2212.09720) 中跑了 **35,000+ 组实验**，得出广为引用的结论：

> "4-bit precision is almost universally optimal for total model bits and zero-shot accuracy."

翻译过来——**在显存预算固定的前提下，把最大塞得下的模型量化到 4-bit，是 zero-shot 准确率/比特数比值的最优解**。低于 3-bit 性能急剧崩塌，高于 4-bit（如 6/8-bit）相对收益递减。

### 3.2 实操对照（24 GB 单卡）

> 注：以下表格里的"性能保留率"是常见经验值（多次社区测评、Qwen 官方 quantization benchmark 的均值印象），不代表所有 benchmark 都是同一比例；真实数字请以你自己的业务 eval 集为准。

| 方案 | 实际显存 | 推理质量经验 | 适用场景 |
| --- | --- | --- | --- |
| **Qwen3-32B + INT4 (AWQ/GPTQ)** | 18–22 GB | 保留 FP16 的 **96–98%** | 24GB 单卡的最佳通用选择 |
| Qwen3-14B + FP16 | 28 GB（**单卡 OOM**） | 100% | 需要双卡或换 FP8 |
| Qwen3-14B + FP8 | ≈ 14 GB | ≈ 99–100% | TPS 高、24GB 卡有富余 |
| Qwen3-30B-A3B + INT4 | 18–22 GB | 保留 FP16 的 ~95% | 想要快 + 长上下文 |
| Qwen3-8B + FP16 | 16 GB | 100% | 任务简单、需极低延迟 |

经验总结：

- **复杂推理 / 长文档 / 代码**：32B-INT4 > 14B-FP16，结构（参数规模）赢过精度。
- **客服 FAQ / 分类 / 提取**：14B-FP16 ≈ 32B-INT4，前者延迟更低更合算。
- **想要超长上下文 + 高并发**：30B-A3B INT4 是当前 24GB 卡上的黑马。

### 3.3 进入 40+ GB 显存档位

- **Qwen3-235B-A22B（MoE，235B 总参 / 22B 激活）**：INT4 后 ≈ 118 GB（仅权重），需要 2×80GB 或 4×48GB 卡，是开源里能逼近 GPT-5 / Claude Sonnet 4.6 推理体感的最便宜方案。
- **Qwen2.5-72B-INT4**：≈ 36 GB，单张 A6000 48GB 或 2×24GB 即可起服务，且在 LiveCodeBench 这种代码题上明显强于 32B。
- **Qwen3-32B FP16 / FP8**：≈ 64 GB / 32 GB；FP8 在 H100 / RTX 5090 原生支持 FP8 指令时几乎无损，但 24GB 卡跑不动。

## 四、四种主流 4-bit 量化方案怎么选

| 方案 | 原理（一句话讲清） | 适用硬件 | 推荐推理引擎 |
| --- | --- | --- | --- |
| **AWQ** | **Activation-aware Weight Quantization**：找出"显著权重通道"（约 1%，对输出影响最大的那批），通过**等价缩放**变换在量化前放大它们，量化误差被压到最小，**但所有权重最终都还是 4-bit**（重要：见易错点 6） | NVIDIA GPU | vLLM、SGLang、TGI、TensorRT-LLM |
| **GPTQ** | 基于 Hessian 二阶近似的逐层贪心量化，老牌方案，生态最广 | NVIDIA GPU | vLLM、TGI、ExLlamaV2 |
| **GGUF**（Q4_K_M 最常用） | llama.cpp 的容器格式，支持 K-quant、IQ-quant 等多种比特配置，可 **CPU + GPU 混合 offload** | CPU、Mac M 系、消费级 GPU | llama.cpp、Ollama、LM Studio |
| **FP8 (E4M3 / E5M2)** | 8-bit 浮点，硬件原生指令支持，**权重 + 激活**都能量化 | H100 / H200 / GB200 / RTX 4090+ | TensorRT-LLM、vLLM、SGLang |

延伸说明：

- **AWQ ≠ "保留 1% FP16"**。AWQ 论文（[arXiv:2306.00978](https://arxiv.org/abs/2306.00978)）明确反对混合精度："To avoid the hardware-inefficient mix-precision quantization, AWQ employs an equivalent transformation to scale the salient weight channels to protect them." 也就是说，AWQ 是用 per-channel scaling **均匀缩放**那 1% 显著通道，量化后再除回去，全部权重都是 INT4——这点原 QA 讲错了。
- **GPTQ 不是被 AWQ "淘汰"**，只是在多数 benchmark 上 AWQ 略胜。生产线很多团队（包括 vLLM 默认）两者都支持，按业务 eval 结果选。
- **GGUF 的 Q4_K_M** 仍是 llama.cpp 生态最被推崇的"性价比挡位"，平均 PPL 损失 < 1%。
- **FP8 是不同维度**：它是"轻量化"（压缩 2×），不与 4-bit 直接对比。在 H100 上跑 FP8 比 INT4 更适合追求质量；在 4090/消费级卡上 FP8 内核还不够成熟。

## 五、什么时候反例——小模型满血更优

1. **极致延迟敏感**：14B-FP16 的 TPS 始终高于 32B-INT4（FLOPs 少一倍多）。客服首屏、IDE 行内补全等场景应选小模型。
2. **极端量化（< 3-bit）灾难**：Q2_K、IQ2、1.58-bit 等在 < 7B 的模型上灾难性损失（BitNet 等专门训练的另说）；与其塞 INT2 的 70B，不如选 INT4 的 14B。
3. **专精任务 + 微调充分**：如果你有高质量微调数据，14B + 全量微调 通常打过 32B-INT4 零样本。
4. **专家模型 / 小模型路由**：在多 Agent 系统里，路由分发到合适尺寸的小模型，比一律走大模型更快更便宜。

## 六、易错点澄清（针对原 QA 对话）

| # | 原说法 | 问题 | 修正 |
| --- | --- | --- | --- |
| 1 | `qwen-32b`, `qwen3-35b-a3b` | 命名错误，35B-A3B 型号不存在 | 实际是 **Qwen3-32B**（Dense）vs **Qwen3-30B-A3B**（MoE，30.5B/3.3B，128 专家激活 8 个） |
| 2 | FP16 32B 显存 ≈ 76 GB | 数字偏高，与公式 `参数量 × 2 bytes` 不符 | FP16 32B 权重 ≈ **64 GB**；FP16 30B-A3B ≈ 61 GB |
| 3 | INT4 35B-A3B 显存 ≈ 20–22 GB | 型号不存在 | INT4 30B-A3B 权重 ≈ 15 GB；加 KV/激活后实际 18–22 GB |
| 4 | "MoE 显存读取压力只有 Dense 的不到十分之一" | 没考虑共享层、路由开销、batch 调度损失 | 实测 **2–4× decode 加速**，不会到 10× |
| 5 | "MoE 速度接近纯 3B 模型" | 过度承诺 | 实际比 Qwen3-32B 快 2–4×，但比 Qwen3-4B 慢 |
| 6 | "AWQ 把 1% 关键权重保持高精度" | **完全讲错** | AWQ 用**等价 per-channel scaling** 缩放显著通道再量化；**所有权重都是 INT4**，论文明确反对混合精度 |
| 7 | "GPTQ 正逐渐被 AWQ 超越" | 表述偏激 | 两者各有场景；vLLM/TGI 均默认支持，按 business eval 选 |
| 8 | "FP8 ≈ 100% 无损" | 略夸张 | E4M3 在权重+激活全量化时通常 99.x% 保留，长尾 benchmark 仍可能掉 0.5–1 pp |
| 9 | "Qwen2.5-72B-INT4 占 38 GB" | 数字略高 | 4-bit 72B 权重 = 36 GB，加 KV 后 38–44 GB |
| 10 | "1-bit 智力崩塌" 一棍打死 | 漏掉 BitNet b1.58 | 普通 PTQ 到 1-bit 确实崩塌；专门训练的 **BitNet b1.58**（Microsoft, 2024）可以做到接近 FP16 |
| 11 | 把 Dettmers 论文写成 "华盛顿大学 Tim Dettmers 等人" | 单作者表述不严谨 | 实际是 **Dettmers & Zettlemoyer (UW, 2023)**，题为 *The case for 4-bit precision: k-bit Inference Scaling Laws* |
| 12 | 没区分 prefill / decode | 把"显存带宽 bound" 当成全部 | **decode 是带宽 bound**；**prefill 是算力 bound**，长 prompt 时 prefill 占主要延迟，MoE 的 prefill 优势没 decode 那么夸张 |
| 13 | "Q4_K_M 是公认最佳" | 缺少出处 | 是 llama.cpp 社区共识，但 IQ4_XS 在新版本上 PPL 更优、体积更小，值得对比 |

## 七、官方与社区测评链接

- Qwen3 官方博客（含 30B-A3B vs QwQ-32B 等图表）：<https://qwenlm.github.io/blog/qwen3/>
- Qwen3 技术报告：<https://arxiv.org/abs/2505.09388>
- Qwen 官方 Speed Benchmark：<https://qwen.readthedocs.io/en/latest/benchmark/speed_benchmark.html>
- Qwen 官方 Quantization Benchmark：<https://qwen.readthedocs.io/en/latest/benchmark/quantization_benchmark.html>
- 4-bit Scaling Laws（Dettmers & Zettlemoyer）：<https://arxiv.org/abs/2212.09720>
- AWQ 原论文（Lin et al., MIT）：<https://arxiv.org/abs/2306.00978>
- GPTQ 原论文：<https://arxiv.org/abs/2210.17323>
- llama.cpp K-quant 说明：<https://github.com/ggerganov/llama.cpp/pull/1684>
- BitNet b1.58（Microsoft, 2024）：<https://arxiv.org/abs/2402.17764>

## 八、小结

1. **同总参 MoE 与 Dense，部署显存基本持平**——但「成本相近」不等于「便宜」，MoE 仍需要总参那么大的卡。
2. **MoE 在 decode 速度和并发吞吐上有 2–4× 的真实优势**，但不会有 10×；首字延迟也不会"接近 3B"。
3. **24 GB 单卡场景，Qwen3-32B INT4 是当前甜点**；想要更快/更长上下文，可换 Qwen3-30B-A3B INT4。
4. **大模型量化到 4-bit > 小模型 FP16**，这是 Dettmers Scaling Laws 给出的结论，至今未被推翻。
5. **AWQ 的核心是 per-channel scaling，不是混合精度保留**——请别再传错了。
