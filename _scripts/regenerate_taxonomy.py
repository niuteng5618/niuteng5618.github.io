#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"


PRIMARY_ORDER = {
    "传统深度学习": 1,
    "大模型技术": 2,
    "RAG": 3,
    "强化学习与对齐": 4,
    "智能体应用开发": 5,
    "热点问题分析": 6,
    "算法与面试": 7,
    "未分类": 99,
}

SECONDARY_ORDER = {
    "传统深度学习": {
        "基础概念": 1,
        "序列模型": 2,
        "工程实践": 3,
    },
    "大模型技术": {
        "学习路线": 1,
        "模型架构与基础": 2,
        "训练与微调": 3,
        "训练基础设施": 4,
        "推理与部署": 5,
    },
    "RAG": {
        "基础与流程": 1,
        "检索与排序": 2,
        "图谱与框架": 3,
        "Prompt与评测": 4,
        "先进方法": 5,
    },
    "强化学习与对齐": {
        "偏好优化": 1,
        "策略优化": 2,
        "价值学习": 3,
    },
    "智能体应用开发": {
        "Agent 工具链": 1,
        "多智能体框架": 2,
        "AI 编程工具": 3,
    },
    "热点问题分析": {
        "模型输出异常": 1,
    },
    "算法与面试": {
        "算法面试": 1,
    },
    "未分类": {
        "待整理": 99,
    },
}

SERIES_ORDER = {
    ("传统深度学习", "基础概念"): {
        "训练基础": 1,
        "模型训练流程": 2,
        "激活函数": 3,
        "正则化": 4,
        "知识蒸馏": 5,
    },
    ("传统深度学习", "序列模型"): {"RNN / LSTM": 1, "xLSTM": 2},
    ("传统深度学习", "工程实践"): {"PyTorch": 1},
    ("大模型技术", "学习路线"): {"LLM 知识库": 1, "大语言模型速成": 2},
    ("大模型技术", "模型架构与基础"): {
        "Transformer 架构": 1,
        "Attention": 2,
        "LLaMA": 3,
        "MoE": 4,
        "Embedding": 5,
    },
    ("大模型技术", "训练与微调"): {"预训练": 1, "参数高效微调": 2},
    ("大模型技术", "训练基础设施"): {"GPU 通信": 1, "并行策略": 2},
    ("大模型技术", "推理与部署"): {
        "确定性推理": 1,
        "不确定性": 2,
        "解码策略": 3,
        "KV Cache": 4,
        "推理压测": 5,
        "显存估算": 6,
        "量化": 7,
    },
    ("RAG", "基础与流程"): {"基础概念": 1, "系统流程": 2},
    ("RAG", "检索与排序"): {"Query 改写": 1, "检索排序": 2, "混合检索": 3},
    ("RAG", "图谱与框架"): {"GraphRAG": 1, "LangChain": 2, "LightRAG": 3},
    ("RAG", "Prompt与评测"): {"Prompt": 1, "评测": 2},
    ("RAG", "先进方法"): {"先进方法": 1},
    ("强化学习与对齐", "偏好优化"): {"DPO": 1},
    ("强化学习与对齐", "策略优化"): {"GRPO": 1, "PPO": 2},
    ("强化学习与对齐", "价值学习"): {"Q-learning": 1},
    ("智能体应用开发", "Agent 工具链"): {"Skill": 1, "MCP": 2},
    ("智能体应用开发", "多智能体框架"): {"MetaGPT": 1},
    ("智能体应用开发", "AI 编程工具"): {"Claude Code / Codex": 1},
    ("热点问题分析", "模型输出异常"): {"输出异常分析": 1},
    ("算法与面试", "算法面试"): {"算法面试": 1},
}

ALIASES = OrderedDict([
    ("KV Cache", ["kvcache", "kv cache", "kv缓存", "prefill", "decode", "pd分离", "缓存命中"]),
    ("Attention", ["attention", "注意力", "mha", "mqa", "gqa", "mla", "multi-head", "多头", "交叉注意力", "线性注意力"]),
    ("Flash Attention", ["flashattention", "flash attention"]),
    ("Paged Attention", ["paged attention", "pageattention", "pagedattention"]),
    ("MoE", ["moe", "mixture of experts", "专家混合", "稀疏激活", "门控网络"]),
    ("Embedding", ["embedding", "嵌入", "向量模型", "flagembedding", "bge"]),
    ("Rerank", ["rerank", "重排序"]),
    ("RAG", ["rag", "retrieval", "检索增强", "检索", "知识库"]),
    ("GraphRAG", ["graphrag"]),
    ("LightRAG", ["lightrag"]),
    ("BM25", ["bm25"]),
    ("HyDE", ["hyde", "假设性文档"]),
    ("RRF", ["rrf", "reciprocal rank fusion", "线性加权"]),
    ("RAGAS", ["ragas"]),
    ("量化", ["量化", "int8", "int4", "bf16", "fp16", "gptq", "awq"]),
    ("LoRA", ["lora"]),
    ("BPE", ["bpe", "tokenization", "分词"]),
    ("vLLM", ["vllm", "压测"]),
    ("SGLang", ["sglang", "确定性推理"]),
    ("FSDP", ["fsdp"]),
    ("ZeRO", ["zero", "deepspeed"]),
    ("数据并行", ["数据并行", "dp"]),
    ("张量并行", ["张量并行", "tp"]),
    ("PPO", ["ppo", "proximal policy"]),
    ("DPO", ["dpo"]),
    ("GRPO", ["grpo"]),
    ("Q-learning", ["q-learning", "q learning"]),
    ("Agent", ["agent", "智能体"]),
    ("MCP", ["mcp"]),
    ("Skill", ["skill"]),
    ("Claude Code", ["claudecode", "claude code"]),
    ("Codex", ["codex"]),
    ("MetaGPT", ["metagpt"]),
    ("Hook", ["hook", "钩子"]),
    ("TodoWrite", ["todowritelist", "todowrite"]),
    ("RNN", ["rnn"]),
    ("LSTM", ["lstm"]),
    ("xLSTM", ["xlstm"]),
    ("激活函数", ["激活函数", "activation"]),
    ("正则化", ["正则化", "regularization"]),
    ("知识蒸馏", ["知识蒸馏", "蒸馏"]),
    ("PyTorch", ["pytorch", "维度转换"]),
])

EXACT_BY_ORDER = {
    1: ("大模型技术", "模型架构与基础", "Attention", ["Attention", "MHA", "GQA", "MQA", "MLA"]),
    2: ("大模型技术", "模型架构与基础", "Attention", ["Flash Attention", "Tiling", "SRAM", "HBM"]),
    3: ("大模型技术", "模型架构与基础", "Transformer 架构", ["Encoder-only", "Decoder-only", "低秩退化", "注意力矩阵"]),
    4: ("大模型技术", "模型架构与基础", "LLaMA", ["LLaMA", "Tokenization", "Embedding", "Transformer"]),
    5: ("RAG", "检索与排序", "Query 改写", ["Query 改写", "Query 扩展", "HyDE", "检索增强"]),
    6: ("大模型技术", "训练与微调", "预训练", ["预训练", "Tokenization", "数据清洗", "训练流程"]),
    7: ("算法与面试", "算法面试", "算法面试", ["算法", "面试", "复杂度", "数据结构"]),
    8: ("传统深度学习", "基础概念", "训练基础", ["Loss", "梯度", "参数", "优化器"]),
    9: ("传统深度学习", "基础概念", "正则化", ["正则化", "Dropout", "过拟合", "泛化"]),
    10: ("传统深度学习", "基础概念", "模型训练流程", ["深度学习", "训练流程", "前向传播", "反向传播"]),
    11: ("传统深度学习", "基础概念", "激活函数", ["激活函数", "ReLU", "Sigmoid", "非线性"]),
    12: ("大模型技术", "训练基础设施", "GPU 通信", ["NVLink", "GPU", "显存", "并行训练"]),
    13: ("传统深度学习", "基础概念", "知识蒸馏", ["知识蒸馏", "黑盒蒸馏", "白盒蒸馏", "Teacher-Student"]),
    14: ("大模型技术", "模型架构与基础", "Attention", ["Attention", "多头注意力", "交叉注意力", "线性注意力"]),
    15: ("传统深度学习", "序列模型", "RNN / LSTM", ["RNN", "LSTM", "门控机制", "序列建模"]),
    16: ("大模型技术", "训练基础设施", "并行策略", ["FSDP", "并行训练", "参数分片", "分布式训练"]),
    17: ("大模型技术", "训练基础设施", "并行策略", ["ZeRO", "数据并行", "张量并行", "流水线并行"]),
    18: ("大模型技术", "模型架构与基础", "MoE", ["MoE", "专家混合", "门控网络", "稀疏激活"]),
    19: ("大模型技术", "模型架构与基础", "Embedding", ["BGE", "FlagEmbedding", "稀疏向量", "Embedding"]),
    20: ("大模型技术", "模型架构与基础", "Embedding", ["Embedding", "微调", "对比学习", "向量模型"]),
    21: ("大模型技术", "推理与部署", "确定性推理", ["SGLang", "确定性推理", "推理稳定性", "采样"]),
    22: ("大模型技术", "推理与部署", "确定性推理", ["SGLang", "启动参数", "确定性推理", "推理部署"]),
    23: ("大模型技术", "推理与部署", "不确定性", ["LLM", "不确定性", "采样", "推理稳定性"]),
    24: ("大模型技术", "推理与部署", "解码策略", ["解码策略", "采样", "推理加速", "生成质量"]),
    25: ("RAG", "检索与排序", "检索排序", ["Embedding", "Rerank", "召回", "重排序"]),
    26: ("热点问题分析", "模型输出异常", "输出异常分析", ["输出异常分析", "LLM", "Token", "热点问题"]),
    27: ("大模型技术", "模型架构与基础", "Attention", ["Flash Attention", "Paged Attention", "KV Cache", "推理优化"]),
    28: ("大模型技术", "推理与部署", "KV Cache", ["KV Cache", "Key", "Value", "显存优化"]),
    29: ("大模型技术", "推理与部署", "KV Cache", ["KV Cache", "PD 分离", "缓存命中", "推理优化"]),
    30: ("大模型技术", "推理与部署", "KV Cache", ["KV Cache", "请求示例", "推理流程", "缓存"]),
    31: ("大模型技术", "推理与部署", "KV Cache", ["KV Cache", "Prefill", "Decode", "推理阶段"]),
    32: ("大模型技术", "训练与微调", "参数高效微调", ["BPE", "LoRA", "Tokenization", "微调"]),
    33: ("大模型技术", "推理与部署", "推理压测", ["vLLM", "压测", "吞吐量", "推理部署"]),
    34: ("大模型技术", "推理与部署", "显存估算", ["显存", "参数量", "推理部署", "容量规划"]),
    35: ("RAG", "图谱与框架", "GraphRAG", ["GraphRAG", "知识图谱", "实体关系", "检索增强"]),
    36: ("RAG", "图谱与框架", "LangChain", ["LangChain", "RAG", "Chain", "应用开发"]),
    37: ("RAG", "图谱与框架", "LightRAG", ["LightRAG", "检索增强", "知识图谱", "流程分析"]),
    38: ("RAG", "Prompt与评测", "Prompt", ["Prompt", "LightRAG", "中文提示词", "检索增强"]),
    39: ("RAG", "基础与流程", "基础概念", ["RAG", "检索", "知识库", "术语"]),
    40: ("RAG", "基础与流程", "系统流程", ["RAG", "系统设计", "检索流程", "知识库"]),
    41: ("RAG", "检索与排序", "混合检索", ["HyDE", "BM25", "向量检索", "混合检索"]),
    42: ("RAG", "Prompt与评测", "评测", ["RAGAS", "RAG 评测", "指标", "问答质量"]),
    43: ("RAG", "先进方法", "先进方法", ["RAG", "检索策略", "重排序", "先进方法"]),
    44: ("RAG", "检索与排序", "混合检索", ["RRF", "线性加权", "BM25", "向量检索"]),
    45: ("大模型技术", "推理与部署", "量化", ["量化", "BF16", "FP16", "INT8"]),
    46: ("大模型技术", "推理与部署", "量化", ["量化", "GPTQ", "AWQ", "推理优化"]),
    47: ("大模型技术", "推理与部署", "量化", ["量化", "QA", "INT4", "显存优化"]),
    48: ("强化学习与对齐", "偏好优化", "DPO", ["DPO", "偏好学习", "RLHF", "对齐"]),
    49: ("强化学习与对齐", "策略优化", "GRPO", ["GRPO", "强化学习", "策略优化", "奖励模型"]),
    50: ("大模型技术", "学习路线", "LLM 知识库", ["LLM", "全栈知识库", "学习路线", "博客"]),
    51: ("强化学习与对齐", "策略优化", "PPO", ["PPO", "策略梯度", "强化学习", "RLHF"]),
    52: ("强化学习与对齐", "价值学习", "Q-learning", ["Q-learning", "强化学习", "价值函数", "Bellman 方程"]),
    53: ("智能体应用开发", "Agent 工具链", "Skill", ["Skill", "Agent", "工具调用", "自动化"]),
    54: ("智能体应用开发", "Agent 工具链", "Skill", ["Skill", "Q&A", "Agent", "工具链"]),
    55: ("智能体应用开发", "Agent 工具链", "MCP", ["Skill", "MCP", "Agent", "工具调用"]),
    56: ("智能体应用开发", "多智能体框架", "MetaGPT", ["MetaGPT", "PRD", "多智能体", "需求生成"]),
    57: ("智能体应用开发", "多智能体框架", "MetaGPT", ["MetaGPT", "辩论", "多智能体", "自定义流程"]),
    58: ("智能体应用开发", "AI 编程工具", "Claude Code / Codex", ["Claude Code", "上下文压缩", "Agent", "开发工具"]),
    59: ("智能体应用开发", "AI 编程工具", "Claude Code / Codex", ["Codex", "上下文压缩", "Compact", "开发工具"]),
    60: ("智能体应用开发", "AI 编程工具", "Claude Code / Codex", ["Hook", "钩子", "自动化", "开发工具"]),
    61: ("智能体应用开发", "AI 编程工具", "Claude Code / Codex", ["TodoWrite", "任务管理", "Agent", "开发工具"]),
    62: ("大模型技术", "学习路线", "LLM 知识库", ["LLM", "全栈知识库", "学习路线", "博客"]),
    63: ("大模型技术", "学习路线", "大语言模型速成", ["大语言模型", "学习路线", "LLM", "入门指南"]),
    64: ("强化学习与对齐", "策略优化", "PPO", ["PPO", "策略梯度", "强化学习", "RLHF"]),
    65: ("强化学习与对齐", "价值学习", "Q-learning", ["Q-learning", "强化学习", "价值函数", "Bellman 方程"]),
    66: ("传统深度学习", "工程实践", "PyTorch", ["PyTorch", "张量维度", "维度转换", "深度学习"]),
    67: ("传统深度学习", "序列模型", "xLSTM", ["xLSTM", "mLSTM", "序列模型", "LSTM"]),
    68: ("传统深度学习", "序列模型", "xLSTM", ["xLSTM", "LSTM", "序列模型", "算法"]),
    73: ("智能体应用开发", "AI 编程工具", "Claude Code / Codex", ["Claude Code", "System Prompt", "Prompt Cache", "Agent"]),
    74: ("智能体应用开发", "Agent 工具链", "MCP", ["MCP", "Streamable HTTP", "SSE", "stdio", "JSON-RPC"]),
    75: ("RAG", "检索与排序", "混合检索", ["混合检索", "BM25", "Embedding", "RRF", "Rerank"]),
}


def split_front_matter(text: str):
    if text.startswith("---\n"):
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if match:
            return match.group(1), text[match.end():]
    raise ValueError("missing front matter")


def parse_simple_front_matter(fm: str):
    data = OrderedDict()
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*", line):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                arr = []
                i += 1
                while i < len(lines) and re.match(r"^\s+-\s+", lines[i]):
                    arr.append(lines[i].split("-", 1)[1].strip().strip('"'))
                    i += 1
                data[key] = arr
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if inner:
                    data[key] = [v.strip().strip('"') for v in inner.split(",")]
                else:
                    data[key] = []
            else:
                data[key] = value.strip('"')
        i += 1
    return data


def yaml_scalar(value: str) -> str:
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def yaml_list(values):
    return "\n".join(f"  - {v}" for v in values)


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def post_order_from_filename(filename: str) -> int:
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(\d{3})-", filename)
    return int(match.group(1)) if match else 999


def detect_from_content(title: str, body: str):
    content = strip_html(title + "\n" + body[:12000]).lower()
    found = []
    for tag, keys in ALIASES.items():
        if any(k.lower() in content for k in keys):
            found.append(tag)
    if any(t in found for t in ["RAG", "GraphRAG", "LightRAG", "BM25", "HyDE", "RRF", "RAGAS", "Rerank"]):
        if "GraphRAG" in found:
            return "RAG", "图谱与框架", "GraphRAG", found[:6] or ["RAG"]
        if "LightRAG" in found:
            return "RAG", "图谱与框架", "LightRAG", found[:6] or ["RAG"]
        if "RAGAS" in found:
            return "RAG", "Prompt与评测", "评测", found[:6] or ["RAG"]
        if any(t in found for t in ["BM25", "HyDE", "RRF", "Rerank"]):
            return "RAG", "检索与排序", "混合检索", found[:6] or ["RAG"]
        return "RAG", "基础与流程", "基础概念", found[:6] or ["RAG"]
    if any(t in found for t in ["PPO", "DPO", "GRPO", "Q-learning"]):
        if "DPO" in found:
            return "强化学习与对齐", "偏好优化", "DPO", found[:6]
        if "Q-learning" in found:
            return "强化学习与对齐", "价值学习", "Q-learning", found[:6]
        return "强化学习与对齐", "策略优化", next((t for t in ["GRPO", "PPO"] if t in found), "PPO"), found[:6]
    if any(t in found for t in ["Agent", "MCP", "Skill", "Claude Code", "Codex", "MetaGPT", "Hook", "TodoWrite"]):
        if "MetaGPT" in found:
            return "智能体应用开发", "多智能体框架", "MetaGPT", found[:6]
        if any(t in found for t in ["Claude Code", "Codex", "Hook", "TodoWrite"]):
            return "智能体应用开发", "AI 编程工具", "Claude Code / Codex", found[:6]
        return "智能体应用开发", "Agent 工具链", next((t for t in ["MCP", "Skill"] if t in found), "Skill"), found[:6]
    if any(t in found for t in ["RNN", "LSTM", "xLSTM", "激活函数", "正则化", "知识蒸馏", "PyTorch"]):
        if "PyTorch" in found:
            return "传统深度学习", "工程实践", "PyTorch", found[:6]
        if any(t in found for t in ["RNN", "LSTM", "xLSTM"]):
            return "传统深度学习", "序列模型", "xLSTM" if "xLSTM" in found else "RNN / LSTM", found[:6]
        return "传统深度学习", "基础概念", next((t for t in ["激活函数", "正则化", "知识蒸馏"] if t in found), "训练基础"), found[:6]
    if found:
        if any(t in found for t in ["KV Cache", "SGLang", "vLLM", "量化"]):
            if "SGLang" in found:
                series = "确定性推理"
            elif "vLLM" in found:
                series = "推理压测"
            elif "量化" in found:
                series = "量化"
            else:
                series = "KV Cache"
            return "大模型技术", "推理与部署", series, found[:6]
        if any(t in found for t in ["FSDP", "ZeRO", "数据并行", "张量并行"]):
            return "大模型技术", "训练基础设施", "并行策略", found[:6]
        if any(t in found for t in ["LoRA", "BPE"]):
            return "大模型技术", "训练与微调", "参数高效微调", found[:6]
        return "大模型技术", "模型架构与基础", next((t for t in ["Attention", "MoE", "Embedding"] if t in found), found[0]), found[:6]
    return "未分类", "待整理", "其他", ["待整理"]


def clean_display_title(title: str) -> str:
    cleaned = re.sub(r"^\s*\d+(?:[-_.、]\d+)*\s*[-_.、]?\s*", "", str(title)).strip()
    return cleaned or str(title)


def clean_display_filename(title: str, filename: str) -> str:
    display = clean_display_title(title)
    display = re.sub(r"[\\/:*?\"<>|]", "-", display).strip(" .-")
    if not display:
        display = re.sub(r"^\d{4}-\d{2}-\d{2}-\d{3}-", "", filename).removesuffix(".md")
        display = re.sub(r"^\d+(?:[-_.]\d+)*[-_.]?", "", display).strip("-_.") or "post"
    return f"{display}.md"


def order_values(primary: str, secondary: str, series: str):
    primary_order = PRIMARY_ORDER.get(primary, 99)
    secondary_order = SECONDARY_ORDER.get(primary, {}).get(secondary, 99)
    series_order = SERIES_ORDER.get((primary, secondary), {}).get(series, 99)
    return primary_order, secondary_order, series_order


def front_matter(data, taxonomy, filename: str):
    primary, secondary, series, tags = taxonomy
    primary_order, secondary_order, series_order = order_values(primary, secondary, series)
    post_order = post_order_from_filename(filename)
    cleaned = []
    for tag in tags:
        tag = str(tag).strip()
        if not tag or tag in [primary, secondary, series] or tag.lower().startswith("yuque-"):
            continue
        if tag not in cleaned:
            cleaned.append(tag)
    if series and series not in [primary, secondary] and series not in cleaned:
        cleaned.insert(0, series)
    cleaned = cleaned[:8] or [series or secondary or primary]
    categories = [x for x in [primary, secondary, series] if x]
    lines = [
        "---",
        "layout: post",
        f"title: {yaml_scalar(data.get('title', 'Untitled'))}",
        f"display_title: {yaml_scalar(clean_display_title(data.get('title', 'Untitled')))}",
        f"display_filename: {yaml_scalar(data.get('display_filename') or clean_display_filename(data.get('title', 'Untitled'), filename))}",
        f"date: {data.get('date', '')}",
        f"primary_category: {yaml_scalar(primary)}",
        f"secondary_category: {yaml_scalar(secondary)}",
        f"series: {yaml_scalar(series)}",
        f"primary_category_order: {primary_order}",
        f"secondary_category_order: {secondary_order}",
        f"series_order: {series_order}",
        f"post_order: {post_order}",
        "categories:",
        yaml_list(categories),
        "tags:",
        yaml_list(cleaned),
        f"toc: {str(data.get('toc', 'true')).lower()}",
        f"comments: {str(data.get('comments', 'false')).lower()}",
        f"author: {data.get('author', 'niuteng5618')}",
        "---",
        "",
    ]
    return "\n".join(lines)


def main():
    report = []
    for post in sorted(POSTS_DIR.glob("*.md")):
        text = post.read_text(encoding="utf-8", errors="replace")
        fm, body = split_front_matter(text)
        data = parse_simple_front_matter(fm)
        order = post_order_from_filename(post.name)
        taxonomy = EXACT_BY_ORDER.get(order) or detect_from_content(data.get("title", post.stem), body)
        new_text = front_matter(data, taxonomy, post.name) + body.lstrip("\n")
        post.write_text(new_text, encoding="utf-8")
        report.append((post.name, clean_display_title(data.get("title", post.stem)), clean_display_filename(data.get("title", post.stem), post.name), taxonomy, order_values(*taxonomy[:3])))
    print(f"updated={len(report)}")
    for name, display_title, display_filename, taxonomy, orders in report:
        print(f"{orders[0]}.{orders[1]}.{orders[2]} {name} -> {display_title} ({display_filename})")


if __name__ == "__main__":
    main()
