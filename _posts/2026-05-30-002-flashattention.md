---
layout: post
title: "FlashAttention"
display_title: "FlashAttention"
display_filename: "FlashAttention.md"
date: 2026-05-30
primary_category: "大模型技术"
secondary_category: "模型架构与基础"
series: "Attention"
primary_category_order: 2
secondary_category_order: 2
series_order: 2
post_order: 2
categories:
  - 大模型技术
  - 模型架构与基础
  - Attention
tags:
  - Attention
  - Flash Attention
  - Tiling
  - SRAM
  - HBM
toc: true
comments: false
author: niuteng5618
---
![](/images/yuque/002-flashattention/image-1-18516ce2.png)

SRAM(静态随机存取存储器)

HBM(显存)

**FlashAttention算法核心思想**：减少HBM(显存)的访问，将QKV切分为小块后放入SRAM中，计算完毕后_**(矩阵乘法、mask、softmax、dropout)**_，将计算结果从SRAM中写入到HBM中

**核心方法**：tiling, recomputation

**1. tiling(平铺): 分块计算**

因为Attention计算中涉及Softmax，所以不能简单的分块后直接计算。softmax操作是row-wise的，即每行都算一次softmax，所以需要用到

[平铺算法](https://zhida.zhihu.com/search?content_id=238498031&content_type=Article&match_order=1&q=%E5%B9%B3%E9%93%BA%E7%AE%97%E6%B3%95&zhida_source=entity)来分块计算softmax。

【**safe softmax**】 原始softmax数值不稳定，为了数值稳定性，FlashAttention采用safe softmax。(也就是减去一个最大值再softmax)

**2 recomputation（重新计算）**

FlashAttention算法的目标：在计算中减少显存占用，从O(N²) 大小降低到线性，这样就可以把数据加载到SRAM中，提高IO速度。

**解决方案**：传统Attention在计算中需要用到Q，K，V去计算S，P两个矩阵，FlashAttention引入softmax中的统计量(_m, l_)，结合output O和在SRAM中的Q，K，V块进行计算。
