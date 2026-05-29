#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"


PRIMARY_ORDER = {
    "人工智能技术": 1,
    "计算机基础": 2,
    "博客建设": 3,
    "未分类": 99,
}

SECONDARY_ORDER = {
    "人工智能技术": {
        "学习路线": 1,
        "大模型基础": 2,
        "深度学习基础": 3,
        "训练基础设施": 4,
        "大模型推理": 5,
        "RAG系统": 6,
        "强化学习": 7,
        "智能体应用开发": 8,
        "算法与面试": 9,
        "多模态模型": 10,
    },
    "计算机基础": {
        "Linux": 1,
        "数据库": 2,
        "计算机网络": 3,
    },
    "博客建设": {
        "GitHub Pages": 1,
    },
    "未分类": {
        "待整理": 99,
    },
}

SERIES_ORDER = {
    ("人工智能技术", "学习路线"): {"LLM 知识库": 1, "大语言模型速成": 2},
    ("人工智能技术", "大模型基础"): {"Transformer 架构": 1, "Attention": 2, "LLaMA": 3, "预训练": 4, "MoE": 5, "Embedding": 6, "参数高效微调": 7, "量化": 8},
    ("人工智能技术", "深度学习基础"): {"训练基础": 1, "模型训练流程": 2, "激活函数": 3, "正则化": 4, "知识蒸馏": 5, "序列模型": 6, "PyTorch": 7, "xLSTM": 8},
    ("人工智能技术", "训练基础设施"): {"GPU 通信": 1, "并行策略": 2},
    ("人工智能技术", "大模型推理"): {"确定性推理": 1, "不确定性": 2, "解码策略": 3, "KV Cache": 4, "推理压测": 5, "显存估算": 6},
    ("人工智能技术", "RAG系统"): {"基础概念": 1, "系统流程": 2, "Query 改写": 3, "检索排序": 4, "混合检索": 5, "GraphRAG": 6, "LangChain": 7, "LightRAG": 8, "Prompt": 9, "评测": 10, "先进方法": 11},
    ("人工智能技术", "强化学习"): {"偏好优化": 1, "策略优化": 2, "价值学习": 3},
    ("人工智能技术", "智能体应用开发"): {"Skill": 1, "MCP": 2, "MetaGPT": 3, "Claude Code / Codex": 4},
    ("人工智能技术", "算法与面试"): {"算法面试": 1},
    ("人工智能技术", "多模态模型"): {"输出异常分析": 1},
    ("计算机基础", "Linux"): {"文件管理": 1, "磁盘管理": 2},
    ("计算机基础", "数据库"): {"MySQL": 1},
    ("计算机基础", "计算机网络"): {"面试基础": 1, "网络协议": 2},
    ("博客建设", "GitHub Pages"): {"站点维护": 1},
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
    ("Linux", ["linux"]),
    ("文件管理", ["文件管理"]),
    ("磁盘管理", ["磁盘管理"]),
    ("MySQL", ["mysql", "sql", "索引", "事务"]),
    ("计算机网络", ["tcp", "udp", "osi", "ssh", "telnet", "ospf", "计网", "数通"]),
    ("GitHub Pages", ["github pages", "github.io"]),
    ("Jekyll", ["jekyll"]),
])

EXACT = {
    "2026-03-19-001-attention.md": ("人工智能技术", "大模型基础", "Attention", ["Attention", "MHA", "GQA", "MQA", "MLA"]),
    "2026-03-20-002-flashattention.md": ("人工智能技术", "大模型基础", "Attention", ["Flash Attention", "Tiling", "SRAM", "HBM"]),
    "2026-03-21-003-encoder-only.md": ("人工智能技术", "大模型基础", "Transformer 架构", ["Encoder-only", "Decoder-only", "低秩退化", "注意力矩阵"]),
    "2026-03-22-004-llama.md": ("人工智能技术", "大模型基础", "LLaMA", ["LLaMA", "Tokenization", "Embedding", "Transformer"]),
    "2026-03-23-005-query.md": ("人工智能技术", "RAG系统", "Query 改写", ["Query 改写", "Query 扩展", "HyDE", "检索增强"]),
    "2026-03-24-006-pretrain.md": ("人工智能技术", "大模型基础", "预训练", ["预训练", "Tokenization", "数据清洗", "训练流程"]),
    "2026-03-25-007-yuque-007.md": ("人工智能技术", "算法与面试", "算法面试", ["算法", "面试", "复杂度", "数据结构"]),
    "2026-03-26-008-loss.md": ("人工智能技术", "深度学习基础", "训练基础", ["Loss", "梯度", "参数", "优化器"]),
    "2026-03-27-009-yuque-009.md": ("人工智能技术", "深度学习基础", "正则化", ["正则化", "Dropout", "过拟合", "泛化"]),
    "2026-03-28-010-yuque-010.md": ("人工智能技术", "深度学习基础", "模型训练流程", ["深度学习", "训练流程", "前向传播", "反向传播"]),
    "2026-03-29-011-yuque-011.md": ("人工智能技术", "深度学习基础", "激活函数", ["激活函数", "ReLU", "Sigmoid", "非线性"]),
    "2026-03-30-012-3-nvlink.md": ("人工智能技术", "训练基础设施", "GPU 通信", ["NVLink", "GPU", "显存", "并行训练"]),
    "2026-03-31-013-yuque-013.md": ("人工智能技术", "深度学习基础", "知识蒸馏", ["知识蒸馏", "黑盒蒸馏", "白盒蒸馏", "Teacher-Student"]),
    "2026-04-01-014-yuque-014.md": ("人工智能技术", "大模型基础", "Attention", ["Attention", "多头注意力", "交叉注意力", "线性注意力"]),
    "2026-04-02-015-rnnlstm.md": ("人工智能技术", "深度学习基础", "序列模型", ["RNN", "LSTM", "门控机制", "序列建模"]),
    "2026-04-03-016-1-1-fsdp-todo.md": ("人工智能技术", "训练基础设施", "并行策略", ["FSDP", "并行训练", "参数分片", "分布式训练"]),
    "2026-04-04-017-1-zerodptp.md": ("人工智能技术", "训练基础设施", "并行策略", ["ZeRO", "数据并行", "张量并行", "流水线并行"]),
    "2026-04-05-018-10-moe.md": ("人工智能技术", "大模型基础", "MoE", ["MoE", "专家混合", "门控网络", "稀疏激活"]),
    "2026-04-06-019-bgeflagembedding.md": ("人工智能技术", "大模型基础", "Embedding", ["BGE", "FlagEmbedding", "稀疏向量", "Embedding"]),
    "2026-04-07-020-yuque-020.md": ("人工智能技术", "大模型基础", "Embedding", ["Embedding", "微调", "对比学习", "向量模型"]),
    "2026-04-08-021-sglang.md": ("人工智能技术", "大模型推理", "确定性推理", ["SGLang", "确定性推理", "推理稳定性", "采样"]),
    "2026-04-09-022-sglang-2.md": ("人工智能技术", "大模型推理", "确定性推理", ["SGLang", "启动参数", "确定性推理", "推理部署"]),
    "2026-04-10-023-llm.md": ("人工智能技术", "大模型推理", "不确定性", ["LLM", "不确定性", "采样", "推理稳定性"]),
    "2026-04-11-024-yuque-024.md": ("人工智能技术", "大模型推理", "解码策略", ["解码策略", "采样", "推理加速", "生成质量"]),
    "2026-04-12-025-embeddingrerank.md": ("人工智能技术", "RAG系统", "检索排序", ["Embedding", "Rerank", "召回", "重排序"]),
    "2026-04-13-026-19-mm.md": ("人工智能技术", "多模态模型", "输出异常分析", ["多模态", "LLM", "Token", "输出异常"]),
    "2026-04-14-027-flash-attention-paged-attention.md": ("人工智能技术", "大模型基础", "Attention", ["Flash Attention", "Paged Attention", "KV Cache", "推理优化"]),
    "2026-04-15-028-kvcache-1-cache.md": ("人工智能技术", "大模型推理", "KV Cache", ["KV Cache", "Key", "Value", "显存优化"]),
    "2026-04-16-029-kvcache-2-pd.md": ("人工智能技术", "大模型推理", "KV Cache", ["KV Cache", "PD 分离", "缓存命中", "推理优化"]),
    "2026-04-17-030-kvcache-3-kvcache.md": ("人工智能技术", "大模型推理", "KV Cache", ["KV Cache", "请求示例", "推理流程", "缓存"]),
    "2026-04-18-031-kvcache-4-2-prefilldecode.md": ("人工智能技术", "大模型推理", "KV Cache", ["KV Cache", "Prefill", "Decode", "推理阶段"]),
    "2026-04-19-032-5-bpelora.md": ("人工智能技术", "大模型基础", "参数高效微调", ["BPE", "LoRA", "Tokenization", "微调"]),
    "2026-04-20-033-6-vllm.md": ("人工智能技术", "大模型推理", "推理压测", ["vLLM", "压测", "吞吐量", "推理部署"]),
    "2026-04-21-034-yuque-034.md": ("人工智能技术", "大模型推理", "显存估算", ["显存", "参数量", "推理部署", "容量规划"]),
    "2026-04-22-035-graphrag.md": ("人工智能技术", "RAG系统", "GraphRAG", ["GraphRAG", "知识图谱", "实体关系", "检索增强"]),
    "2026-04-23-036-langchain.md": ("人工智能技术", "RAG系统", "LangChain", ["LangChain", "RAG", "Chain", "应用开发"]),
    "2026-04-24-037-lightrag.md": ("人工智能技术", "RAG系统", "LightRAG", ["LightRAG", "检索增强", "知识图谱", "流程分析"]),
    "2026-04-25-038-prompt-cn.md": ("人工智能技术", "RAG系统", "Prompt", ["Prompt", "LightRAG", "中文提示词", "检索增强"]),
    "2026-04-26-039-rag.md": ("人工智能技术", "RAG系统", "基础概念", ["RAG", "检索", "知识库", "术语"]),
    "2026-04-27-040-rag-2.md": ("人工智能技术", "RAG系统", "系统流程", ["RAG", "系统设计", "检索流程", "知识库"]),
    "2026-04-28-041-qmdhydebm25vector.md": ("人工智能技术", "RAG系统", "混合检索", ["HyDE", "BM25", "向量检索", "混合检索"]),
    "2026-04-29-042-ragas-rag.md": ("人工智能技术", "RAG系统", "评测", ["RAGAS", "RAG 评测", "指标", "问答质量"]),
    "2026-04-30-043-yuque-043.md": ("人工智能技术", "RAG系统", "先进方法", ["RAG", "检索策略", "重排序", "先进方法"]),
    "2026-05-01-044-rrf.md": ("人工智能技术", "RAG系统", "混合检索", ["RRF", "线性加权", "BM25", "向量检索"]),
    "2026-05-02-045-yuque-045.md": ("人工智能技术", "大模型基础", "量化", ["量化", "BF16", "FP16", "INT8"]),
    "2026-05-03-046-yuque-046.md": ("人工智能技术", "大模型基础", "量化", ["量化", "GPTQ", "AWQ", "推理优化"]),
    "2026-05-04-047-qa.md": ("人工智能技术", "大模型基础", "量化", ["量化", "QA", "INT4", "显存优化"]),
    "2026-05-05-048-dpo-todo.md": ("人工智能技术", "强化学习", "偏好优化", ["DPO", "偏好学习", "RLHF", "对齐"]),
    "2026-05-06-049-grpo-todo.md": ("人工智能技术", "强化学习", "策略优化", ["GRPO", "强化学习", "策略优化", "奖励模型"]),
    "2026-05-07-050-llm-2.md": ("人工智能技术", "学习路线", "LLM 知识库", ["LLM", "全栈知识库", "学习路线", "博客"]),
    "2026-05-08-051-ppo.md": ("人工智能技术", "强化学习", "策略优化", ["PPO", "策略梯度", "强化学习", "RLHF"]),
    "2026-05-09-052-q-learning.md": ("人工智能技术", "强化学习", "价值学习", ["Q-learning", "强化学习", "价值函数", "Bellman 方程"]),
    "2026-05-10-053-skill.md": ("人工智能技术", "智能体应用开发", "Skill", ["Skill", "Agent", "工具调用", "自动化"]),
    "2026-05-11-054-skill-q-a.md": ("人工智能技术", "智能体应用开发", "Skill", ["Skill", "Q&A", "Agent", "工具链"]),
    "2026-05-12-055-skill-mcp.md": ("人工智能技术", "智能体应用开发", "MCP", ["Skill", "MCP", "Agent", "工具调用"]),
    "2026-05-13-056-metagpt-prd.md": ("人工智能技术", "智能体应用开发", "MetaGPT", ["MetaGPT", "PRD", "多智能体", "需求生成"]),
    "2026-05-14-057-metagpt.md": ("人工智能技术", "智能体应用开发", "MetaGPT", ["MetaGPT", "辩论", "多智能体", "自定义流程"]),
    "2026-05-15-058-claudecode.md": ("人工智能技术", "智能体应用开发", "Claude Code / Codex", ["Claude Code", "上下文压缩", "Agent", "开发工具"]),
    "2026-05-16-059-codex-compact.md": ("人工智能技术", "智能体应用开发", "Claude Code / Codex", ["Codex", "上下文压缩", "Compact", "开发工具"]),
    "2026-05-17-060-hook.md": ("人工智能技术", "智能体应用开发", "Claude Code / Codex", ["Hook", "钩子", "自动化", "开发工具"]),
    "2026-05-18-061-todowritelist.md": ("人工智能技术", "智能体应用开发", "Claude Code / Codex", ["TodoWrite", "任务管理", "Agent", "开发工具"]),
    "2026-05-19-062-llm-3.md": ("人工智能技术", "学习路线", "LLM 知识库", ["LLM", "全栈知识库", "学习路线", "博客"]),
    "2026-05-20-063-yuque-063.md": ("人工智能技术", "学习路线", "大语言模型速成", ["大语言模型", "学习路线", "LLM", "入门指南"]),
    "2026-05-21-064-ppo-2.md": ("人工智能技术", "强化学习", "策略优化", ["PPO", "策略梯度", "强化学习", "RLHF"]),
    "2026-05-22-065-q-learning-2.md": ("人工智能技术", "强化学习", "价值学习", ["Q-learning", "强化学习", "价值函数", "Bellman 方程"]),
    "2026-05-23-066-pytorch.md": ("人工智能技术", "深度学习基础", "PyTorch", ["PyTorch", "张量维度", "维度转换", "深度学习"]),
    "2026-05-24-067-xlstm-mlstm.md": ("人工智能技术", "深度学习基础", "xLSTM", ["xLSTM", "mLSTM", "序列模型", "LSTM"]),
    "2026-05-25-068-xlstm.md": ("人工智能技术", "深度学习基础", "xLSTM", ["xLSTM", "LSTM", "序列模型", "算法"]),
    "2026-05-26-069-linux.md": ("计算机基础", "Linux", "文件管理", ["Linux", "文件管理", "命令行", "权限"]),
    "2026-05-27-070-linux-2.md": ("计算机基础", "Linux", "磁盘管理", ["Linux", "磁盘管理", "分区", "文件系统"]),
    "2026-05-28-071-mysql.md": ("计算机基础", "数据库", "MySQL", ["MySQL", "SQL", "索引", "事务"]),
    "2026-05-29-072-yuque-072.md": ("计算机基础", "计算机网络", "面试基础", ["计算机网络", "TCP", "UDP", "OSI"]),
    "2026-05-29-welcome.md": ("博客建设", "GitHub Pages", "站点维护", ["GitHub Pages", "Jekyll", "博客搭建"]),
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

def detect_from_content(title: str, body: str):
    content = strip_html(title + "\n" + body[:12000]).lower()
    found = []
    for tag, keys in ALIASES.items():
        if any(k.lower() in content for k in keys):
            found.append(tag)
    if any(t in found for t in ["RAG", "GraphRAG", "LightRAG", "BM25", "HyDE", "RRF", "RAGAS"]):
        return "人工智能技术", "RAG系统", next((t for t in ["GraphRAG", "LightRAG", "混合检索", "评测", "Query 改写"] if t in title), "检索增强生成"), found[:6] or ["RAG"]
    if any(t in found for t in ["PPO", "DPO", "GRPO", "Q-learning"]):
        return "人工智能技术", "强化学习", "策略与价值学习", found[:6]
    if any(t in found for t in ["Agent", "MCP", "Skill", "Claude Code", "Codex", "MetaGPT", "Hook", "TodoWrite"]):
        return "人工智能技术", "智能体应用开发", "Agent 工具链", found[:6]
    if any(t in found for t in ["Linux", "文件管理", "磁盘管理"]):
        series = "磁盘管理" if "磁盘" in title else "文件管理"
        return "计算机基础", "Linux", series, found[:6]
    if "MySQL" in found:
        return "计算机基础", "数据库", "MySQL", found[:6]
    if "计算机网络" in found:
        return "计算机基础", "计算机网络", "网络协议", found[:6]
    if any(t in found for t in ["RNN", "LSTM", "xLSTM", "激活函数", "正则化", "知识蒸馏", "PyTorch"]):
        return "人工智能技术", "深度学习基础", found[0], found[:6]
    if found:
        return "人工智能技术", "大模型基础", found[0], found[:6]
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

def post_order_from_filename(filename: str) -> int:
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(\d{3})-", filename)
    return int(match.group(1)) if match else 999

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
        f"display_filename: {yaml_scalar(clean_display_filename(data.get('title', 'Untitled'), filename))}",
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
        taxonomy = EXACT.get(post.name) or detect_from_content(data.get("title", post.stem), body)
        new_text = front_matter(data, taxonomy, post.name) + body.lstrip("\n")
        post.write_text(new_text, encoding="utf-8")
        report.append((post.name, clean_display_title(data.get("title", post.stem)), clean_display_filename(data.get("title", post.stem), post.name), taxonomy, order_values(*taxonomy[:3])))
    print(f"updated={len(report)}")
    for name, display_title, display_filename, taxonomy, orders in report:
        print(f"{orders[0]}.{orders[1]}.{orders[2]} {name} -> {display_title} ({display_filename})")

if __name__ == "__main__":
    main()
