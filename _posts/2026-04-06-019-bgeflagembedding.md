---
layout: post
title: "BGE的FlagEmbedding库——使用嵌入模型提取稀疏向量"
date: 2026-04-06
tags: ["人工智能技术", "大模型基础", "Embedding模型", "BGE的FlagEmbedding库——使用嵌入模型提取稀疏向量"]
toc: true
comments: false
author: niuteng5618
---
### 学习背景：
在调研向量化方法时，学习到可以将chunk进行稀疏向量和稠密向量（Dense vec）提取。

其中，**稠密向量**就是常规的**embedding**方法。**稀疏向量**则一般采用TFIDF、**bm25**等词袋模型，对出现过的词语进行统计分析。

但是，在了解bge-m3模型后，了解到BGE推出过专门用于BGE模型的embedding库——**FlagEmbedding**，这个库可以使用**bge系列模型**进行**稀疏向量的提取**。 这基本是 FlagEmbedding 独有的功能之一。  

### 代码
```python
from FlagEmbedding import BGEM3FlagModel
import json

# 模型的加载和定义可以放在外面
model = BGEM3FlagModel('/home/worker/models/bge-m3', device=1)
string = "What is BGE M3?"
sentences_1 = [string]

# 关键修复：将运行逻辑放入 if __name__ == '__main__':
if __name__ == '__main__':
    output_1 = model.encode(sentences_1, return_dense=True, return_sparse=True, return_colbert_vecs=False)
    
    # 后续的数据处理逻辑
    dense_vecs = output_1['dense_vecs'].tolist()
    lexical_weights = output_1['lexical_weights'][0]
    
    # 处理稀疏向量的权重，确保可以被 JSON 序列化
    regular_dict = {}
    for key, value in lexical_weights.items():
        regular_dict[key] = float(value)
    
    # 构建最终的响应字典
    response_dict = {}
    response_dict['dense_vecs'] = dense_vecs
    response_dict['lexical_weights'] = regular_dict
    
    # 打印 JSON 字符串
    print(json.dumps(response_dict))
```

**运行结果：**![](/images/yuque/019-bgeflagembedding/image-1-40052b7f.png)

### 与传统稀疏向量提取方法对比（BM25）
于中文而言，基于bge的**tokenizer**会将词切的**更细**。例如：

**example**: 已经腊月二十九了，嘉靖三十九年入冬以来京师地面和邻近数省便没有下过一场雪

**result** : '已经' **'腊' '月' **'二十' '九' '了' ',' '嘉' '靖' '三' '十九' '年' '入' '冬' '以来' '京' '师' '地面' '和'** '邻' '近' **'数' '省' '便' '没有' '下' '过' '一场' '雪'

可以明显看出，很多词语在中文语境中并不该拆分，例如"**腊月**"、"**邻近**"...

**结论：**这种切词方法在稠密向量提取中，能带来较好的效果，但不适用基于词频统计的稀疏向量中。**<font style="color:rgb(37, 41, 51);">这种操作可能造成语义的丢失</font>**<font style="color:rgb(37, 41, 51);">。</font>
